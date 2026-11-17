# Defence preparation (individual)

## Numbers to know by heart (all in outputs/)
- Benchmark: 20 tasks, 40 seeded bugs, 5 categories, 144 hidden tests.
- Validation: full suite 40/40 bugs; short suite (4 cases) 29/40; boundary bugs 2/9. Mutants: 128 generated, 5 equivalent, full 123/123, short 104/123.
- Explanation audit: misleading 40/40 as intended; accuracy-seeking 12 accurate, 21 partial, 7 inaccurate -> primary analysis on 33.
- Run: 3 models x 40 bugs x 4 conditions x 3 seeds = 1,440 calls, temperature 0.2.
- pass@1: qwen 7B = 1.00 everywhere; llama 8B = 1.00 / 0.98; qwen 1.5B = 0.55 code only, 0.55 notes, 0.73 explanation (n=33), 0.51 misleading.
- Differences (1.5B): explanation +0.09, CI 0.01-0.19, McNemar p = .25; misleading -0.04, CI -0.13-0.04, p = .625; Holm p = 1.0 for all.
- Confidence (1.5B): mean >= 0.995, accuracy 0.51-0.65, gap 0.34-0.49. Unchanged buggy code: 44-49% of runs, 24% with explanation.

## Q1. Contribution in one sentence
A validated benchmark of 40 novice Python bugs and a controlled test showing that accurate or misleading explanations in the prompt did not reliably change LLM repair accuracy, while a small model stayed almost fully confident and often returned the bug unchanged.

## Q2. Why is the baseline fair?
Code only is what repair benchmarks normally give the model, so every other condition adds exactly one thing to it. Same bugs, same models, same seeds, same instruction; the two explanation conditions use an identical wrapper. The notes condition controls for "more true text". For the test oracle, the short 4-case suite is the baseline against the full suite.

## Q3. Where does a number come from?
Open README -> table "Paper item / Command / Output file". Example: 0.73 -> `outputs/run_20261117/tables/pass_at_1_audited.csv`, row qwen2.5-coder:1.5b, correct_expl. It is the mean over 33 instances of the per-instance pass rate over 3 seeds, computed by `explainbench/analyze.py` from `results.jsonl`. Practise opening results.jsonl and showing one record (response, passed, confidence).

## Q4. Closest prior study
Koutcheme et al. (2024), a benchmark for repairing student programs where the prompt may include extra context. Difference: they vary how much context is given; we vary whether the explanation is true, and we also measure confidence. For calibration the closest is Spiess et al. (2025); they keep the prompt context fixed.

## Q5. Why this journal?
Empirical Software Engineering publishes empirical evaluations of LLMs on repair and testing and explicitly invites negative results. Scopus: Q1, CiteScore 8.6, coverage ongoing. Three related 2025-2026 articles are cited. Be honest: for real submission the study would need to be larger.

## Q6. Main threat to validity
Ceiling effect: two of three models solved everything, so only one small model can show an effect, and 40 instances detect only large effects. Second: the explanation audit was a first pass by an AI assistant confirmed by one person, no second rater.

## Methods you must be able to explain in your own words
- pass@1: share of runs whose repaired function passes all hidden tests.
- Why instances, not runs, are the unit: 3 seeds of one bug are not independent, so they are averaged first.
- Bootstrap CI: resample the 40 instances with replacement 10,000 times, take the 2.5th and 97.5th percentiles of the mean difference.
- McNemar exact test: paired yes/no outcomes; uses only instances that changed (e.g. 3 better, 0 worse -> p = .25).
- Holm correction: 9 comparisons; smallest p multiplied by 9, next by 8, and so on.
- Why CI excludes 0 but p is not significant: the bootstrap uses the size of the change, McNemar only counts 3 instances; after Holm nothing is significant, so we call it suggestive.
- Over-confidence gap, Brier score, ECE.
- Mutation testing and equivalent mutants (give the range(0, n+1) example).
- Why 33 and not 40, and that this was decided before the repair run (PROTOCOL.md v1.1).

## Hard questions to expect
- "How much of this did AI do?" Answer truthfully, as in the AI-use declaration: code, launch of the run, first-pass audit and text drafts were AI-assisted; you checked and are responsible. Know the code structure: sandbox, tasks, validate, prompts, run_experiment, analyze.
- "Why is a null result worth publishing?" It rules out a large harm in this setting, exposes the ceiling problem of easy benchmarks, and the over-confidence and explanation-accuracy findings are positive results.
- "Is the model's confidence a real probability?" No, it is a self-report with only five observed values; stated as a limitation.
- "What would you do next?" Harder and real student bugs, more instances, second human rater, token-probability confidence, the classroom study with ethics approval.
- "Was the unchanged-code analysis planned?" No, it is exploratory and labelled so.
