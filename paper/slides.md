# Slides (10) - content outline; every number is from outputs/

1. **Title.** Explanation Context and Bug-Repair Calibration in Open-Weight Code LLMs on Novice Python Tasks. Name, group, target journal.
2. **Problem.** LLM explanations of code are read by novices and re-used as model context; an explanation can endorse buggy code. RQ.
3. **Gap.** Repair studies vary amount of context, not its truth; calibration studies fix context; misleading-explanation studies are about humans. (Table 1)
4. **Benchmark.** 20 tasks, 40 seeded bugs, 5 categories, 144 hidden tests. Validation: full suite 40/40, short suite 29/40; boundary bugs 2/9. (Fig. 1)
5. **Design.** 4 conditions x 3 local models x 3 seeds = 1,440 runs. Protocol tagged before the run. Outcomes: pass@1, confidence.
6. **Manipulation check.** 40/40 misleading as intended; accuracy-seeking explanations: 12 accurate, 21 partial, 7 inaccurate -> primary analysis on 33.
7. **Result 1: accuracy.** 7-8B models at ceiling (0.98-1.00). 1.5B: 0.55 code only; 0.73 with explanation (+0.09, CI 0.01-0.19); 0.51 misleading (-0.04); Holm p = 1.0 everywhere. (Fig. 2)
8. **Result 2: confidence.** 1.5B model: confidence >= 0.995 in all conditions, accuracy 0.51-0.65, gap 0.34-0.49. Unchanged buggy code in 44-49% of runs (24% with explanation). (Fig. 3)
9. **Limits.** Ceiling for 2 of 3 models; 40 small hand-seeded bugs; AI-made audit, single rater; verbal confidence; post hoc analysis; models, not students.
10. **Conclusion and reproducibility.** H1-H3 not supported; validate oracles, do not trust small-model confidence, check explanations. Repo, tags, one-command run; what I would do next.

Defence questions to prepare: why is code-only a fair baseline; why McNemar and Holm; what a
bootstrap CI over instances means; why 33 not 40; what would change the conclusion; which paper is
closest and how this differs.
