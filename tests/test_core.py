import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from explainbench import analyze, make_explanations, run_experiment, stats, validate
from explainbench.mutate import generate_mutants
from explainbench.prompts import CONDITIONS, build_prompt, parse_response
from explainbench.sandbox import all_passed, run_tests
from explainbench.tasks import CATEGORIES, bug_instances, load_tasks


class SandboxTests(unittest.TestCase):
    def test_pass_fail_type_and_errors(self):
        tests = [{"args": [1], "expected": True}, {"args": [2], "expected": True}]
        out = run_tests("def f(x):\n    return 1 if x == 1 else True\n", "f", tests)
        self.assertFalse(out["results"][0]["ok"])  # 1 != True by type rule
        self.assertTrue(out["results"][1]["ok"])
        out = run_tests("def f(x):\n    raise ValueError('boom')\n", "f", tests)
        self.assertIn("ValueError", out["results"][0]["error"])

    def test_syntax_error_and_missing_entry(self):
        t = [{"args": [1], "expected": 1}]
        self.assertTrue(run_tests("def f(:\n", "f", t)["load_error"])
        self.assertTrue(run_tests("x = 1\n", "f", t)["load_error"])

    def test_infinite_loop_times_out(self):
        t = [{"args": [1], "expected": 1}]
        out = run_tests("def f(x):\n    while True:\n        pass\n", "f", t, timeout=10, per_test_timeout=0.5)
        self.assertFalse(all_passed(out))
        self.assertIn("TimeoutError", out["results"][0]["error"])

    def test_print_does_not_corrupt_result(self):
        t = [{"args": [1], "expected": 1}]
        out = run_tests("print('@@EXPLAINBENCH_RESULT@@{}')\ndef f(x):\n    print('hi')\n    return x\n", "f", t)
        self.assertTrue(all_passed(out))


class TaskSuiteTests(unittest.TestCase):
    def test_validation_of_example_tasks(self):
        with tempfile.TemporaryDirectory() as d:
            rc = validate.main(["--tasks", str(ROOT / "tasks"), "--out", d, "--generated"])
            self.assertEqual(rc, 0)
            s = json.loads((Path(d) / "summary.json").read_text())
            self.assertTrue(s["reference_all_pass"])
            self.assertEqual(s["by_origin"]["handwritten"]["full"]["score"], 1.0)
            # the weak demo suite must miss at least one handwritten fault (e.g. t04 at age 18)
            self.assertLess(s["by_origin"]["handwritten"]["demo"]["score"], 1.0)

    def test_cheat_passes_demo_fails_full(self):
        t = [x for x in load_tasks(ROOT / "tasks") if x.id == "t01_sum_to_n"][0]
        code = t.cheats["cheat_hardcoded"]
        self.assertTrue(all_passed(run_tests(code, t.entry, t.demo_tests)))
        self.assertFalse(all_passed(run_tests(code, t.entry, t.tests)))


class BenchmarkShapeTests(unittest.TestCase):
    def test_structure_and_size(self):
        tasks = load_tasks(ROOT / "tasks")
        self.assertGreaterEqual(len(bug_instances(tasks)), 40)
        for t in tasks:
            self.assertGreaterEqual(len(t.tests), 7, t.id)
            self.assertEqual(t.demo_count, 4, t.id)
            self.assertTrue(t.alternatives, f"{t.id} needs a valid alternative solution")
            for m in t.mutants:
                self.assertIn(m.category, CATEGORIES)
                self.assertNotEqual(m.code.strip(), t.reference.strip(), f"{t.id}/{m.id} equals reference")
        cats = {c: sum(1 for i in bug_instances(tasks) if i.category == c) for c in CATEGORIES}
        self.assertTrue(all(v >= 5 for v in cats.values()), cats)


class MutateTests(unittest.TestCase):
    def test_generates_changed_unique_mutants(self):
        ms = generate_mutants("def f(a):\n    return a >= 18\n")
        codes = [m["code"] for m in ms]
        self.assertTrue(any(">= 18" not in c and "> 18" in c for c in codes))
        self.assertEqual(len(codes), len(set(codes)))
        for c in codes:
            compile(c, "<m>", "exec")


class PromptTests(unittest.TestCase):
    def test_conditions_and_parsing(self):
        t = load_tasks(ROOT / "tasks")[0]
        base = build_prompt(t, "def f():\n    pass\n", "code_only")
        self.assertNotIn("explanation", base.lower())
        self.assertIn("Reference notes", build_prompt(t, "x", "docs"))
        a = build_prompt(t, "x", "correct_expl", "E")
        b = build_prompt(t, "x", "misleading_expl", "E")
        self.assertEqual(a, b)  # identical framing, only the explanation text differs
        with self.assertRaises(ValueError):
            build_prompt(t, "x", "correct_expl")
        p = parse_response("text\n```python\nA\n```\nmore\n```python\nB\n```\nCONFIDENCE: 0.8")
        self.assertEqual(p["code"].strip(), "B")
        self.assertEqual(p["confidence"], 0.8)
        self.assertEqual(parse_response("```python\nx\n```\nCONFIDENCE: 90%")["confidence"], 0.9)
        self.assertIsNone(parse_response("no code")["code"])


class StatsTests(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(stats.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(stats.mcnemar_exact(5, 0), 0.0625)
        lo, hi = stats.wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.7634, places=3)
        self.assertEqual(stats.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertAlmostEqual(stats.brier([1.0, 0.0], [1, 0]), 0.0)
        self.assertAlmostEqual(stats.ece([0.9, 0.9], [1, 0]), 0.4)
        m, lo, hi = stats.bootstrap_mean_ci([1, 1, 1, 1], n_boot=200)
        self.assertEqual((m, lo, hi), (1.0, 1.0, 1.0))


class PipelineMockTests(unittest.TestCase):
    def test_end_to_end_with_mock(self):
        with tempfile.TemporaryDirectory() as d:
            ex = str(Path(d) / "expl")
            make_explanations.main(["--tasks", str(ROOT / "tasks"), "--out", ex, "--mock"])
            run = str(Path(d) / "run")
            run_experiment.main(["--tasks", str(ROOT / "tasks"), "--explanations", ex,
                                 "--mock", "--seeds", "2", "--out", run])
            n1 = len((Path(run) / "results.jsonl").read_text().splitlines())
            n_inst = len(bug_instances(load_tasks(ROOT / "tasks")))
            self.assertEqual(n1, n_inst * 4 * 2)  # instances x 4 conditions x 2 seeds
            run_experiment.main(["--tasks", str(ROOT / "tasks"), "--explanations", ex,
                                 "--mock", "--seeds", "2", "--out", run])  # resume: no duplicates
            self.assertEqual(len((Path(run) / "results.jsonl").read_text().splitlines()), n1)
            with self.assertRaises(SystemExit):
                analyze.main(["--run", run])  # refuses mock data
            analyze.main(["--run", run, "--allow-mock"])
            self.assertTrue((Path(run) / "tables" / "pass_at_1.csv").exists())


if __name__ == "__main__":
    unittest.main()
