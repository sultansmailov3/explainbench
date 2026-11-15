"""Validate the test suite: reference must pass, seeded faults must be caught.

Reproduces the technical-validation tables of the paper:
    outputs/validation/validation.csv     one row per (task, variant)
    outputs/validation/case_logs.jsonl    every executed (variant, test) pair
    outputs/validation/summary.json       counts, mutation scores, environment

Usage:  PYTHONPATH=src python -m explainbench.validate [--tasks tasks] [--out outputs/validation] [--generated]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import platform
import sys
from pathlib import Path

from .mutate import generate_mutants
from .sandbox import all_passed, run_tests
from .tasks import load_tasks, sha256


def _evaluate(task, code, tests, suite, variant_id, kind, log):
    outcome = run_tests(code, task.entry, tests)
    for i, (t, r) in enumerate(zip(tests, outcome["results"])):
        log.write(json.dumps({
            "task": task.id, "variant": variant_id, "kind": kind, "suite": suite,
            "case": i, "args": t["args"], "expected": t["expected"],
            "observed": r["observed"], "ok": r["ok"], "error": r["error"],
        }) + "\n")
    return outcome


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks")
    ap.add_argument("--out", default="outputs/validation")
    ap.add_argument("--generated", action="store_true",
                    help="also run AST-generated mutants of each reference")
    args = ap.parse_args(argv)

    tasks = load_tasks(args.tasks)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, problems = [], []

    with open(out / "case_logs.jsonl", "w", encoding="utf-8") as log:
        for t in tasks:
            full, demo = t.tests, t.demo_tests

            ref = _evaluate(t, t.reference, full, "full", "reference", "reference", log)
            ref_ok = all_passed(ref)
            rows.append(dict(task=t.id, variant="reference", kind="reference", origin="",
                             category="", operator="", sha256=sha256(t.reference),
                             killed_demo="", killed_full="", n_failed_full=sum(not r["ok"] for r in ref["results"]),
                             n_full=len(full), expected_status="pass", status_ok=ref_ok))
            if not ref_ok:
                problems.append(f"{t.id}: reference fails the full suite")

            for name, code in t.alternatives.items():
                o = _evaluate(t, code, full, "full", name, "alternative", log)
                ok = all_passed(o)
                rows.append(dict(task=t.id, variant=name, kind="alternative", origin="",
                                 category="", operator="", sha256=sha256(code),
                                 killed_demo="", killed_full=not ok,
                                 n_failed_full=sum(not r["ok"] for r in o["results"]),
                                 n_full=len(full), expected_status="pass", status_ok=ok))
                if not ok:
                    problems.append(f"{t.id}/{name}: valid alternative rejected")

            for name, code in t.cheats.items():
                od = _evaluate(t, code, demo, "demo", name, "cheat", log)
                of = _evaluate(t, code, full, "full", name, "cheat", log)
                ok = all_passed(od) and not all_passed(of)
                rows.append(dict(task=t.id, variant=name, kind="cheat", origin="",
                                 category="", operator="", sha256=sha256(code),
                                 killed_demo=not all_passed(od), killed_full=not all_passed(of),
                                 n_failed_full=sum(not r["ok"] for r in of["results"]),
                                 n_full=len(full), expected_status="demo_pass_full_fail", status_ok=ok))
                if not ok:
                    problems.append(f"{t.id}/{name}: cheat did not behave as designed")

            variants = [(m.id, m.code, "handwritten", m.category, "") for m in t.mutants]
            if args.generated:
                for k, g in enumerate(generate_mutants(t.reference)):
                    variants.append((f"gen{k:03d}", g["code"], "generated", "", g["operator"]))
            for vid, code, origin, cat, op in variants:
                od = _evaluate(t, code, demo, "demo", vid, "mutant", log)
                of = _evaluate(t, code, full, "full", vid, "mutant", log)
                rows.append(dict(task=t.id, variant=vid, kind="mutant", origin=origin,
                                 category=cat, operator=op, sha256=sha256(code),
                                 killed_demo=not all_passed(od), killed_full=not all_passed(of),
                                 n_failed_full=sum(not r["ok"] for r in of["results"]),
                                 n_full=len(full), expected_status="fail_full",
                                 status_ok=not all_passed(of)))
                if origin == "handwritten" and all_passed(of):
                    problems.append(f"{t.id}/{vid}: handwritten mutant survives the full suite")

    fields = list(rows[0].keys())
    with open(out / "validation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    def score(sel, key):
        sel = list(sel)
        return {"n": len(sel), "killed": sum(1 for r in sel if r[key]),
                "score": (sum(1 for r in sel if r[key]) / len(sel)) if sel else None}

    mutants = [r for r in rows if r["kind"] == "mutant"]
    summary = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(), "platform": platform.platform(),
        "n_tasks": len(tasks),
        "n_full_cases": sum(len(t.tests) for t in tasks),
        "reference_all_pass": all(r["status_ok"] for r in rows if r["kind"] == "reference"),
        "mutation_score_demo": score(mutants, "killed_demo"),
        "mutation_score_full": score(mutants, "killed_full"),
        "by_origin": {o: {"demo": score([r for r in mutants if r["origin"] == o], "killed_demo"),
                          "full": score([r for r in mutants if r["origin"] == o], "killed_full")}
                      for o in sorted({r["origin"] for r in mutants})},
        "problems": problems,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
