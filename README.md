# ExplainBench

Seeded-bug benchmark and experiment pipeline for the study  
**"Explanation Context and Bug-Repair Calibration in Open-Weight Code LLMs on Novice Python Tasks"**
(final research project, Astana IT University; author: Sultan Kalzhigit, SE-2416).

Status: **work in progress.** `tasks/` holds 20 tasks with 40 hand-written seeded bugs
(boundary/operator 9, loop condition 10, off-by-one 7, base case 8, data-structure update 6) -
categories are not yet balanced; add tasks for off-by-one and data-structure update. Test cases and
`docs.md` notes are first drafts. Nothing in this repository has been run with a real model yet.
Numbers in the paper must come only from logs in `outputs/run_*/`.

## What it does
1. `validate` - checks the hidden test suite: the reference passes, each seeded bug is caught, valid
   alternative solutions pass, a hard-coded solution passes the short demo suite but fails the full one,
   and (optionally) AST-generated mutants give a mutation score for demo vs full suite.
2. `make_explanations` - an explainer model writes an accurate and a misleading explanation per bug.
3. `run_experiment` - for each bug x model x condition x seed asks a local model (Ollama) to repair the
   code and state its confidence; every response and test outcome is logged to JSONL.
4. `analyze` - pass@1 with CIs, paired comparisons (bootstrap + exact McNemar + Holm), calibration
   (Brier, ECE, over-confidence gap), per-category tables.

Design details and the pre-specified analysis: see [PROTOCOL.md](PROTOCOL.md).

## Quick start
Python >= 3.10, standard library only. For real runs, install [Ollama](https://ollama.com) and pull
the models you will use.

```bash
export PYTHONPATH=src
make test                                   # unit tests (no model needed)
python -m explainbench.validate --generated # technical validation -> outputs/validation/

# real experiment (run inside a container/VM, see Safety)
python -m explainbench.make_explanations --model <explainer-model>
#   -> now read every explanation and fill explanations/AUDIT.csv (manipulation check)
python -m explainbench.run_experiment --models <model-a> <model-b> --seeds 5
python -m explainbench.analyze --run outputs/run_YYYYMMDD_HHMM
```

On Windows the whole pipeline is one command: `.\run_all.ps1 -Models "<model-a>","<model-b>" -Seeds 3`.

`make mock` runs the whole pipeline with a fake model to check the plumbing. Mock output is flagged
`"mock": true`, is git-ignored, and `analyze` refuses it unless `--allow-mock` is passed.

## Reproducing the paper's tables and figures
Fill this table as the manuscript takes shape (every number in the paper must trace to a file here).

| Paper item | Command | Output file |
|---|---|---|
| Table 1 - suite validation | `python -m explainbench.validate --generated` | `outputs/validation/summary.json`, `validation.csv` |
| Table 2 - pass@1 by condition | `python -m explainbench.analyze --run <run>` | `<run>/tables/pass_at_1.csv` |
| Table 3 - paired comparisons | same | `<run>/tables/comparisons.csv` |
| Table 4 - calibration | same | `<run>/tables/calibration.csv` |
| Table 5 - by bug category | same | `<run>/tables/by_category.csv` |
| Fig. 1 - suite validation by category | `python -m explainbench.figures --validation outputs/validation` | `figures/fig_validation.png` |
| Fig. 2-4 - pass@1, over-confidence gap, reliability | `python -m explainbench.figures --run <run>` | `figures/fig_pass_at_1.png`, `fig_calibration.png`, `fig_reliability.png` |

## Layout
```
src/explainbench/   sandbox, tasks, mutate, validate, prompts, llm, make_explanations,
                    run_experiment, stats, analyze
tasks/<id>/         task.json (description + tests), reference.py, docs.md, mutants/, alt_*.py, cheat_*.py
explanations/       cached explanation texts + AUDIT.csv
outputs/            validation/ and run_*/ (raw logs, manifest, tables)
tests/              unit and end-to-end (mock) tests
```

## Adding tasks
Create `tasks/tNN_name/` with `task.json`, `reference.py`, `docs.md`, and one or more files under
`mutants/` (listed in `task.json` with a category from `explainbench.tasks.CATEGORIES`). Put the cheap,
guessable cases first: the first `demo_count` tests form the short baseline suite. Add `alt_*.py`
(valid, different implementation) and, where sensible, `cheat_*.py`. Then run `validate`.
The `docs.md` files currently contain placeholder notes: replace them with short excerpts from the
official Python documentation (cite URL and version) before the experiment.

## Safety
Model-generated code is executed in a child process with a time and memory limit. This is **not** a
security sandbox. Run experiments in a disposable container or VM, without credentials or network
access to anything you care about.

## Licence
MIT (see [LICENSE](LICENSE)). Decide and state the licence for task data and logs before release
(see [DECLARATIONS.md](DECLARATIONS.md)).
