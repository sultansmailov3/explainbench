"""Generate the explanation texts for the explanation conditions and cache them.

Each bug instance gets two files in explanations/:
    <instance>__correct.json     accurate explanation of the buggy code
    <instance>__misleading.json  confident explanation that presents the bug as correct

IMPORTANT (manipulation check, see PROTOCOL.md): a person must read every generated
explanation and record in explanations/AUDIT.csv whether the "correct" ones are accurate
and the "misleading" ones are actually misleading. Do not run the experiment before that.

Usage: PYTHONPATH=src python -m explainbench.make_explanations --model <ollama-model> [--mock]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from .llm import MockClient, OllamaClient
from .prompts import explainer_prompt
from .tasks import bug_instances, load_tasks, sha256


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks")
    ap.add_argument("--out", default="explanations")
    ap.add_argument("--model", help="Ollama model used as the explainer")
    ap.add_argument("--seed", type=int, default=2416)
    ap.add_argument("--mock", action="store_true", help="plumbing test only")
    args = ap.parse_args(argv)

    tasks = {t.id: t for t in load_tasks(args.tasks)}
    client = MockClient() if args.mock else OllamaClient(args.model)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for inst in bug_instances(list(tasks.values())):
        for kind in ("correct", "misleading"):
            path = out / f"{inst.id}__{kind}.json"
            if path.exists():
                continue
            prompt = explainer_prompt(tasks[inst.task_id], inst.code, kind)
            res = client.generate(prompt, seed=args.seed, temperature=0.0, max_tokens=400)
            text = res["text"].strip()
            path.write_text(json.dumps({
                "instance": inst.id, "kind": kind, "text": text,
                "contains_code_block": "```" in text,
                "explainer_model": client.model, "explainer_digest": client.digest,
                "prompt_sha256": sha256(prompt), "seed": args.seed, "mock": client.mock,
                "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print("wrote", path)


if __name__ == "__main__":
    main()
