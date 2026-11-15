"""Analyse a results.jsonl run and write the tables used in the paper.

Outputs (in <run>/tables/):
    pass_at_1.csv      pass@1 per model x condition with cluster-bootstrap 95% CI
    comparisons.csv    each condition vs code_only: paired difference, CI, exact McNemar, Holm p
    calibration.csv    mean confidence, accuracy, over-confidence gap, Brier score, ECE
    by_category.csv    pass@1 per model x condition x bug category
    results.json       all of the above plus the run manifest

Unit of analysis: the bug INSTANCE. Seeds are repeated draws for the same instance and
are averaged first, so they are not treated as independent observations.

Usage: PYTHONPATH=src python -m explainbench.analyze --run outputs/run_YYYYMMDD_HHMM
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from . import stats

BASELINE = "code_only"


def load(run: Path, allow_mock: bool):
    recs = [json.loads(l) for l in (run / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    if any(r.get("mock") for r in recs) and not allow_mock:
        raise SystemExit("run contains MOCK records; refusing to analyse (use --allow-mock for plumbing tests only)")
    return recs


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def analyse(recs):
    by = defaultdict(list)
    for r in recs:
        by[(r["model"], r["condition"])].append(r)
    models = sorted({m for m, _ in by})
    conds = sorted({c for _, c in by})

    def inst_rates(model, cond, cat=None):
        d = defaultdict(list)
        for r in by[(model, cond)]:
            if cat is None or r["category"] == cat:
                d[r["instance"]].append(1.0 if r["passed"] else 0.0)
        return {i: stats.mean(v) for i, v in d.items()}

    pass_rows, comp_rows, cal_rows, cat_rows = [], [], [], []
    for m in models:
        for c in conds:
            rates = inst_rates(m, c)
            mu, lo, hi = stats.bootstrap_mean_ci(list(rates.values()), seed=1)
            pass_rows.append({"model": m, "condition": c, "n_instances": len(rates),
                              "n_runs": len(by[(m, c)]), "pass_at_1": round(mu, 4),
                              "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)})
            recs_c = [r for r in by[(m, c)] if r["confidence"] is not None]
            conf = [r["confidence"] for r in recs_c]
            out = [1.0 if r["passed"] else 0.0 for r in recs_c]
            acc = stats.mean(out)
            cal_rows.append({"model": m, "condition": c, "n_with_confidence": len(recs_c),
                             "n_runs": len(by[(m, c)]),
                             "mean_confidence": round(stats.mean(conf), 4) if conf else "",
                             "accuracy": round(acc, 4) if conf else "",
                             "overconfidence_gap": round(stats.mean(conf) - acc, 4) if conf else "",
                             "brier": round(stats.brier(conf, out), 4) if conf else "",
                             "ece": round(stats.ece(conf, out), 4) if conf else ""})
            cats = sorted({r["category"] for r in by[(m, c)]})
            for cat in cats:
                rr = inst_rates(m, c, cat)
                cat_rows.append({"model": m, "condition": c, "category": cat,
                                 "n_instances": len(rr),
                                 "pass_at_1": round(stats.mean(rr.values()), 4)})

    # paired comparisons against the baseline condition, one family for Holm
    raw = []
    for m in models:
        if BASELINE not in conds:
            break
        base = inst_rates(m, BASELINE)
        for c in conds:
            if c == BASELINE:
                continue
            cur = inst_rates(m, c)
            ids = sorted(set(base) & set(cur))
            a = [cur[i] for i in ids]
            b = [base[i] for i in ids]
            d, lo, hi = stats.paired_bootstrap_diff(a, b, seed=2)
            succ_c = [x >= 0.5 for x in a]
            succ_b = [x >= 0.5 for x in b]
            n01 = sum(1 for x, y in zip(succ_c, succ_b) if x and not y)  # better than baseline
            n10 = sum(1 for x, y in zip(succ_c, succ_b) if y and not x)  # worse than baseline
            p = stats.mcnemar_exact(n01, n10)
            raw.append(p)
            comp_rows.append({"model": m, "condition": c, "vs": BASELINE, "n_pairs": len(ids),
                              "mean_diff": round(d, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                              "better_than_baseline": n01, "worse_than_baseline": n10,
                              "p_mcnemar_exact": round(p, 6)})
    for row, adj in zip(comp_rows, stats.holm(raw)):
        row["p_holm"] = round(adj, 6)
    return pass_rows, comp_rows, cal_rows, cat_rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--allow-mock", action="store_true")
    args = ap.parse_args(argv)
    run = Path(args.run)
    recs = load(run, args.allow_mock)
    pass_rows, comp_rows, cal_rows, cat_rows = analyse(recs)
    tdir = run / "tables"
    tdir.mkdir(exist_ok=True)
    write_csv(tdir / "pass_at_1.csv", pass_rows)
    write_csv(tdir / "comparisons.csv", comp_rows)
    write_csv(tdir / "calibration.csv", cal_rows)
    write_csv(tdir / "by_category.csv", cat_rows)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8")) \
        if (run / "manifest.json").exists() else {}
    (tdir / "results.json").write_text(json.dumps(
        {"manifest": manifest, "pass_at_1": pass_rows, "comparisons": comp_rows,
         "calibration": cal_rows, "by_category": cat_rows}, indent=2), encoding="utf-8")
    print(f"tables written to {tdir}")


if __name__ == "__main__":
    main()
