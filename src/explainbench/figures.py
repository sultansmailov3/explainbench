"""Make the figures of the manuscript from logged results (requires matplotlib).

Figures are written as PNG (300 dpi) and PDF to <out>/:
    fig_validation.png   kill rate of the short (demo) vs full suite, by bug category
    fig_pass_at_1.png    pass@1 per model x condition with 95% bootstrap CIs      (needs --run)
    fig_calibration.png  over-confidence gap per model x condition                (needs --run)
    fig_reliability.png  reliability diagram per condition (pooled over models)   (needs --run)

Usage:
  PYTHONPATH=src python -m explainbench.figures --validation outputs/validation --out figures
  PYTHONPATH=src python -m explainbench.figures --run outputs/run_YYYYMMDD_HHMM --out figures
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from . import stats
from .prompts import CONDITIONS


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:  # pragma: no cover
        raise SystemExit("matplotlib is required for figures: pip install matplotlib") from e
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    return plt


def _save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")


def fig_validation(val_dir: Path, out: Path):
    plt = _plt()
    rows = [r for r in csv.DictReader(open(val_dir / "validation.csv", encoding="utf-8"))
            if r["kind"] == "mutant" and r["origin"] == "handwritten"]
    cats = sorted({r["category"] for r in rows})
    demo, full, n = [], [], []
    for c in cats:
        sel = [r for r in rows if r["category"] == c]
        n.append(len(sel))
        demo.append(sum(r["killed_demo"] == "True" for r in sel) / len(sel))
        full.append(sum(r["killed_full"] == "True" for r in sel) / len(sel))
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    x = range(len(cats))
    w = 0.38
    ax.bar([i - w / 2 for i in x], demo, w, label="Short suite (4 cases)")
    ax.bar([i + w / 2 for i in x], full, w, label="Full suite")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{c.replace('_', chr(10))}\n(n={k})" for c, k in zip(cats, n)], fontsize=8)
    ax.set_ylabel("Share of seeded bugs detected")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8)
    _save(fig, out, "fig_validation")
    plt.close(fig)


def _load_results(run: Path):
    return [json.loads(l) for l in (run / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]


def fig_pass_at_1(run: Path, out: Path):
    plt = _plt()
    rows = list(csv.DictReader(open(run / "tables" / "pass_at_1.csv", encoding="utf-8")))
    models = sorted({r["model"] for r in rows})
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    w = 0.8 / max(1, len(conds))
    for j, c in enumerate(conds):
        xs, ys, lo, hi = [], [], [], []
        for i, m in enumerate(models):
            r = next(r for r in rows if r["model"] == m and r["condition"] == c)
            xs.append(i + (j - (len(conds) - 1) / 2) * w)
            ys.append(float(r["pass_at_1"]))
            lo.append(float(r["pass_at_1"]) - float(r["ci_lo"]))
            hi.append(float(r["ci_hi"]) - float(r["pass_at_1"]))
        ax.bar(xs, ys, w, yerr=[lo, hi], capsize=2, label=c.replace("_", " "))
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, fontsize=8)
    ax.set_ylabel("pass@1 (95% bootstrap CI)")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    _save(fig, out, "fig_pass_at_1")
    plt.close(fig)


def fig_calibration(run: Path, out: Path):
    plt = _plt()
    rows = [r for r in csv.DictReader(open(run / "tables" / "calibration.csv", encoding="utf-8"))
            if r["overconfidence_gap"] != ""]
    models = sorted({r["model"] for r in rows})
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    w = 0.8 / max(1, len(conds))
    for j, c in enumerate(conds):
        xs, ys = [], []
        for i, m in enumerate(models):
            r = next((r for r in rows if r["model"] == m and r["condition"] == c), None)
            if r:
                xs.append(i + (j - (len(conds) - 1) / 2) * w)
                ys.append(float(r["overconfidence_gap"]))
        ax.bar(xs, ys, w, label=c.replace("_", " "))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, fontsize=8)
    ax.set_ylabel("Mean confidence - accuracy")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    _save(fig, out, "fig_calibration")
    plt.close(fig)


def fig_reliability(run: Path, out: Path, bins: int = 10):
    plt = _plt()
    recs = [r for r in _load_results(run) if r["confidence"] is not None]
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in recs)]
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="perfect calibration")
    for c in conds:
        buckets = defaultdict(list)
        for r in recs:
            if r["condition"] == c:
                b = min(int(r["confidence"] * bins), bins - 1)
                buckets[b].append(1.0 if r["passed"] else 0.0)
        pts = sorted((b, stats.mean(v), len(v)) for b, v in buckets.items())
        ax.plot([(b + 0.5) / bins for b, _, _ in pts], [m for _, m, _ in pts], marker="o", ms=3,
                label=c.replace("_", " "))
    ax.set_xlabel("Stated confidence")
    ax.set_ylabel("Observed accuracy")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=7)
    _save(fig, out, "fig_reliability")
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", help="directory with validation.csv")
    ap.add_argument("--run", help="run directory (after `analyze`)")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if args.validation:
        fig_validation(Path(args.validation), out)
    if args.run:
        run = Path(args.run)
        fig_pass_at_1(run, out)
        fig_calibration(run, out)
        fig_reliability(run, out)
    if not (args.validation or args.run):
        ap.error("give --validation and/or --run")
    print("figures written to", out)


if __name__ == "__main__":
    main()
