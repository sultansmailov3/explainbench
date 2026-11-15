"""Run the repair experiment: instances x models x conditions x seeds.

Writes one JSON line per model call to <out>/results.jsonl (resumable) and a run
manifest to <out>/manifest.json. Mock runs go to outputs/mock by default and are
flagged "mock": true; analysis refuses them unless --allow-mock is given.

Usage:
  PYTHONPATH=src python -m explainbench.run_experiment --models qwen2.5-coder:7b llama3.1:8b --seeds 5
  PYTHONPATH=src python -m explainbench.run_experiment --mock          # plumbing test only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import sys
from pathlib import Path

from .llm import MockClient, OllamaClient
from .prompts import CONDITIONS, build_prompt, parse_response
from .sandbox import all_passed, run_tests
from .tasks import bug_instances, load_tasks, sha256


def load_explanation(expl_dir: Path, instance_id: str, kind: str):
    p = expl_dir / f"{instance_id}__{kind}.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing: run make_explanations first")
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("contains_code_block"):
        raise ValueError(f"{p}: explanation contains a code block; regenerate or edit it")
    return d["text"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks")
    ap.add_argument("--explanations", default="explanations")
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--conditions", nargs="*", default=CONDITIONS)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true", help="plumbing test only; not research data")
    args = ap.parse_args(argv)

    tasks = {t.id: t for t in load_tasks(args.tasks)}
    instances = bug_instances(list(tasks.values()))
    out = Path(args.out or ("outputs/mock" if args.mock else
                            "outputs/run_" + dt.datetime.now().strftime("%Y%m%d_%H%M")))
    out.mkdir(parents=True, exist_ok=True)

    if args.mock:
        oracle = {i.code: tasks[i.task_id].reference for i in instances}
        clients = [MockClient(oracle=oracle)]
    else:
        if not args.models:
            ap.error("--models is required unless --mock")
        clients = [OllamaClient(m) for m in args.models]

    results_path = out / "results.jsonl"
    done = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["instance"], r["model"], r["condition"], r["seed"]))

    manifest = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(), "platform": platform.platform(),
        "models": {c.model: c.digest for c in clients}, "conditions": args.conditions,
        "seeds": list(range(args.seeds)), "temperature": args.temperature,
        "max_tokens": args.max_tokens, "n_instances": len(instances), "mock": args.mock,
        "tasks_sha256": {t.id: sha256(json.dumps(t.tests, sort_keys=True) + t.reference)
                         for t in tasks.values()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    expl_dir = Path(args.explanations)

    n_new = 0
    with open(results_path, "a", encoding="utf-8") as log:
        for client in clients:
            for inst in instances:
                task = tasks[inst.task_id]
                for cond in args.conditions:
                    expl = None
                    if cond == "correct_expl":
                        expl = load_explanation(expl_dir, inst.id, "correct")
                    elif cond == "misleading_expl":
                        expl = load_explanation(expl_dir, inst.id, "misleading")
                    prompt = build_prompt(task, inst.code, cond, expl)
                    for seed in range(args.seeds):
                        key = (inst.id, client.model, cond, seed)
                        if key in done:
                            continue
                        res = client.generate(prompt, seed=seed, temperature=args.temperature,
                                              max_tokens=args.max_tokens)
                        parsed = parse_response(res["text"])
                        if parsed["code"] is None:
                            outcome = {"results": [], "load_error": "no code block", "timeout": False}
                            passed = False
                        else:
                            outcome = run_tests(parsed["code"], task.entry, task.tests)
                            passed = all_passed(outcome)
                        log.write(json.dumps({
                            "instance": inst.id, "task": inst.task_id, "category": inst.category,
                            "model": client.model, "model_digest": client.digest,
                            "condition": cond, "seed": seed, "mock": client.mock,
                            "prompt_sha256": sha256(prompt), "response": res["text"],
                            "parsed_ok": parsed["code"] is not None,
                            "confidence": parsed["confidence"], "passed": passed,
                            "n_cases_passed": sum(r["ok"] for r in outcome["results"]),
                            "n_cases": len(task.tests), "load_error": outcome["load_error"],
                            "timeout": outcome["timeout"], "latency_s": res["latency_s"],
                        }, ensure_ascii=False) + "\n")
                        log.flush()
                        n_new += 1
    print(f"wrote {n_new} new records to {results_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
