"""Count failed repairs that return the buggy code unchanged (ignoring blank lines,
comments and a CONFIDENCE line placed inside the code block).
Usage: PYTHONPATH=src python scripts/unchanged_analysis.py outputs/run_20261117
Writes <run>/tables/unchanged.csv
"""
import csv, json, sys
from pathlib import Path
from explainbench.prompts import CONDITIONS, parse_response
from explainbench.tasks import bug_instances, load_tasks

def norm(s):
    out = []
    for l in (s or "").splitlines():
        l = l.split("#")[0].rstrip()
        if l.strip() and not l.strip().upper().startswith("CONFIDENCE"):
            out.append(l)
    return "\n".join(out)

run = Path(sys.argv[1])
inst = {i.id: i for i in bug_instances(load_tasks("tasks"))}
recs = [json.loads(l) for l in (run / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
rows = []
for m in sorted({r["model"] for r in recs}):
    for c in CONDITIONS:
        sel = [r for r in recs if r["model"] == m and r["condition"] == c]
        fails = [r for r in sel if not r["passed"]]
        same = sum(norm(parse_response(r["response"])["code"]) == norm(inst[r["instance"]].code) for r in fails)
        rows.append({"model": m, "condition": c, "n_runs": len(sel), "n_failed": len(fails),
                     "failed_unchanged": same,
                     "share_of_runs_unchanged": round(same / len(sel), 4)})
with open(run / "tables" / "unchanged.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
