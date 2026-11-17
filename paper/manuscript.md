# Explanation Context and Bug-Repair Calibration in Open-Weight Code LLMs on Novice Python Tasks

Sultan Kalzhigit, Astana IT University (SE-2416)

> DRAFT v0.2 (2026-11-17). All numbers come from `outputs/validation/` and
> `outputs/run_20261117/tables/`. Citations (name year) refer to `paper/references.md`; the author reports having read the cited sources.
> Still to do by the author: move the text into the journal template and reference style.

## Abstract
**Background.** Explanations of code written by large language models (LLMs) are read by novices
and fed back to models as context in tutoring and repair tools. An explanation can be accurate,
or can confidently present faulty code as correct. **Aim.** We test
how the presence and accuracy of an explanation in the prompt change the repair accuracy and stated
confidence of open-weight LLMs on novice-level Python bugs. **Method.** We built a benchmark of 20
tasks with 40 hand-seeded bugs in five categories and 144 hidden test cases, and validated it with
seeded faults, alternative solutions and generated mutants. Three locally run models repaired each
bug under four conditions (code only, reference notes, accuracy-seeking explanation, misleading
explanation) with three seeds (1,440 runs). **Results.** The full suite detected 40/40 seeded bugs;
a four-case suite detected 29/40. Only 12 of 40 accuracy-seeking explanations were fully accurate.
Two 7-8B models were at ceiling in every condition (pass@1 0.98-1.00). For a 1.5B model, pass@1 was 0.55 with code only, 0.73 with an audited explanation
(difference +0.09, 95% CI 0.01 to 0.19) and 0.51 with a misleading one (-0.04, CI -0.13 to 0.04);
no comparison was significant after Holm adjustment. That model reported a mean confidence of at
least 0.99 in every condition, and in 44-49% of runs returned the buggy code unchanged except when
given an accuracy-seeking explanation (24%). **Conclusion.** On this benchmark the hypothesised harm
of misleading explanations was not demonstrated; the clearest result is severe over-confidence of
the small model regardless of context.

**Keywords:** automated program repair; confidence estimation; computing education; mutation
analysis; prompt context; test adequacy

## 1. Introduction
Generative language models are now part of how beginners learn to program. Controlled and
observational studies describe both benefits and risks: learners supported by a code generator
completed authoring tasks more successfully without a measured loss on later manual tasks (Kazemitabaar et al. 2023),
students rated model-written code explanations as more accurate and easier to understand than
explanations written by peers (Leinonen et al. 2023), and observations of novices working with a code assistant
documented cognitive and metacognitive difficulties (Prather et al. 2023). Explanations of code are among the most
common kinds of support, and their properties are known to shift with the prompt, the code, the
language and the model version (Oli et al. 2023). Recent tools for novice debugging try to keep the learner
active rather than hand over a fix, because over-reliance is a recurring concern (Kurniawan et al. 2025).

An explanation is not always right. A model asked to describe a buggy function may describe the
intended behaviour instead of the actual one, and the result reads as a fluent endorsement of
faulty code. Studies of AI-assisted decision making show that incorrect explanations can mislead
people even when the underlying advice is sound (Spitzer et al. 2024; Cabitza et al. 2024). Much less is known about the
machine side of the same situation. Explanations are routinely passed back to models as context -
in tutoring pipelines, in repair tools that add feedback to the prompt (Koutcheme et al. 2024; Campos et al. 2025), and in agent
loops - and language models are known to be sensitive to context that should not change the answer
(Shi et al. 2023). If a misleading explanation lowers repair accuracy while leaving stated confidence
unchanged, any system that chains explanation and repair inherits that failure. Calibration of
code models is itself an open problem: generated code is frequently accompanied by confidence that
does not track correctness (Spiess et al. 2025; Singh et al. 2025).

This paper grew out of a planned classroom study on whether LLM explanations affect novices'
independent debugging. That study requires human participants and prior ethical approval and is
left as future work. Here we ask the corresponding question about the models themselves:

**RQ.** How do the presence and the accuracy of a natural-language explanation of buggy code in
the prompt affect the repair accuracy and the stated confidence of open-weight code LLMs on seeded
novice Python bugs?

Our contributions are:
1. **A validated benchmark** of 20 novice-level Python tasks with 40 hand-seeded bugs in five
   categories and hidden tests, together with evidence that the tests detect all seeded bugs,
   accept alternative correct solutions and reject a hard-coded solution that a short suite accepts.
2. **A controlled comparison** of four prompt contexts - code only, reference notes, an
   accuracy-seeking explanation and a misleading explanation - on the same bugs, models and seeds.
3. **A calibration analysis** of self-reported confidence under these contexts (over-confidence
   gap, Brier score, expected calibration error).
4. **A reproducibility package** in which every reported number is regenerated from logs.

Section 2 reviews related work, Section 3 describes materials and methods, Section 4 reports
results, Section 5 discusses them and their limits, and Section 6 concludes.

## 2. Related Work
**LLM explanations for novices.** Work on model-written explanations has mostly evaluated their
quality or their reception by learners. Explanations were judged favourably against student-written
ones (Leinonen et al. 2023), and their correctness is typically high while completeness, conciseness and specificity lag
(Oli et al. 2023). These studies treat the
explanation as an output for a human reader. We treat it as an input to a model.

**LLM-based repair of novice programs.** Repair of student programs with language models is now
evaluated on shared benchmarks with
functional-correctness metrics such as pass@k, in which the prompt may also carry extra context
such as grader feedback (Koutcheme et al. 2024). Evaluations across languages report that adding failing-test
information to the prompt improves repair (Campos et al. 2025). Small single-function benchmarks with one-line
defects (Lin et al. 2017) and hand-written function-level benchmarks scored by unit tests (Chen et al. 2021) established the
evaluation style we follow. Recent empirical studies in software engineering likewise evaluate language models on repair
beyond conventional code (Alhanahnah et al. 2025) and examine how prompt design changes the quality of generated
tests (Ouédraogo et al. 2026), and LLM-based detection and repair of vulnerabilities in real
developer code has been assessed with re-scanning and manual review (Belozerov et al. 2026). None of these studies varies the *truthfulness* of the added context.

**Confidence and calibration.** Modern neural networks are often miscalibrated (Guo et al. 2017). Language
models can be asked to assess their own answers, with encouraging but task-dependent results (Kadavath et al. 2022).
For code, studies find that confidence is not well aligned with correctness without correction
(Spiess et al. 2025)
and that weaker models overestimate themselves most (Singh et al. 2025). We add one factor these studies hold
fixed: what the prompt says about the code.

**Context sensitivity and misleading explanations.** Irrelevant sentences in a problem statement
reduce model accuracy on arithmetic reasoning (Shi et al. 2023). In human-AI decision making, incorrect
explanations impair performance and later reasoning (Spitzer et al. 2024), and persuasive but wrong explanations
can stop people from checking correct advice (Cabitza et al. 2024). Our misleading-explanation condition is the
model-side analogue.

**Test adequacy.** A repair counts as correct only relative to its tests. Patches that pass a weak
suite yet remain wrong are a known problem in test-based repair (Yu et al. 2019; Xin and Reiss 2017). Mutation analysis measures
a suite by the seeded faults it detects (Jia and Harman 2011); mutant detection correlates with real-fault detection
(Just et al. 2014).
Benchmark problems that appear in training data are a further threat to evaluation (Riddell et al. 2024). We
therefore validate our suite before using it and write the tasks and bugs ourselves.

**Table 1. Closest studies.** (complete after reading the full papers)

| Study | Subjects | Task | Context varied | Misleading context | Confidence measured |
|---|---|---|---|---|---|
| Koutcheme et al. (2024) | LLMs | repair of student programs | optional feedback | no | no |
| Campos et al. (2025) | LLMs | repair, several languages | failing-test information | no | no |
| Spiess et al. (2025) | LLMs | completion, synthesis, repair | - | no | yes |
| Shi et al. (2023) | LLMs | arithmetic word problems | irrelevant sentences | irrelevant, not false | no |
| Spitzer et al. (2024) | humans | AI-assisted decisions | explanation correctness | yes | (verify) |
| **This work** | open-weight LLMs | repair of seeded novice bugs | none / docs / accurate / misleading explanation | **yes** | **yes** |

**Gap.** Repair studies vary how much context a model receives but not whether it is true;
calibration studies fix the context; studies of misleading explanations concern human readers. No
study we found measures repair accuracy and confidence of code models when an explanation of the
buggy code is accurate versus misleading.

## 3. Materials and Methods
### 3.1 Design
A within-instance factorial design: every bug instance is presented to every model under each of
four context conditions with the same seeds. The analysis plan was fixed in `PROTOCOL.md` and
tagged in the repository (`protocol-v1`) before the first model run; one amendment (v1.1, below)
was committed after the manipulation check and before any repair run.

### 3.2 Benchmark
The benchmark contains 20 Python tasks of the kind set in a first programming course (accumulation
loops, searching, string and list processing, simple recursion, dictionaries and sets, boundary
conditions). Each task has a natural-language description, a reference implementation, at least one
alternative correct implementation written differently, short documentation notes on the relevant
language feature, and 7-8 test cases (144 in total). The first four cases of each task are typical,
easily guessed inputs and form the *short suite*; the remaining cases target boundaries and
general behaviour. A candidate passes a task only if every case returns the expected value and type.

Forty bug instances were seeded by hand, two per task, in five categories taken from the earlier
course assignments: off-by-one (7), loop condition (10), base case (8), boundary/operator (9) and
data-structure update (6). Each instance differs from its reference by a small edit. Tasks and
bugs were written for this study rather than taken from a public benchmark, to limit the chance
that they appear verbatim in model training data (Riddell et al. 2024); the task types themselves are common.

### 3.3 Suite validation
Before any model was run, the suite was validated (`explainbench.validate`): (i) every reference
and every alternative solution must pass the full suite; (ii) every seeded bug must fail at least
one case; (iii) a hard-coded solution that returns memorised answers for the short-suite inputs
must pass the short suite and fail the full one; (iv) mutants generated from each reference by
three operator families (comparison swap, integer constant +/-1, +/- swap) are executed against
both suites. The short suite serves as the baseline against which the full suite is compared.

### 3.4 Conditions
| Condition | Text added to the prompt |
|---|---|
| code only (baseline) | none |
| notes | short author-written reference notes on the relevant language feature (true, not specific to the bug) |
| accuracy-seeking explanation | LLM-written description produced with a prompt asking what the buggy code actually does |
| misleading explanation | LLM-written description presenting the buggy code as correct |

Explanations were generated once per instance by `llama3.1:8b` at temperature 0 with a fixed seed
and cached. The two explanation conditions use an identical prompt wrapper, so only the explanation
text differs. No explanation contained a code block.

**Manipulation check.** All 80 explanations were read and labelled (`explanations/AUDIT.csv`). The
first pass was made by an AI assistant (Claude) and was then reviewed and confirmed by the author. All 40
misleading explanations presented the buggy code as correct without mentioning a fault. Of the 40
accuracy-seeking explanations, 12 were labelled accurate, 21 partial (the seeded fault is
identified, but at least one other statement about the code is false) and 7 inaccurate (the fault
is not identified, or is called correct). Following the protocol amendment made before the repair
run, explanations were not edited; the primary analysis of this condition uses the 33 instances
labelled accurate or partial, and the analysis of all 40 is reported as a sensitivity analysis.

Code only is the baseline because it is the standard input of repair benchmarks (Koutcheme et al. 2024; Lin et al. 2017); the
notes condition controls for the mere presence of extra, true, non-specific text.

### 3.5 Models and procedure
Three open-weight models were run locally through Ollama 0.40.16 with their default tags:
`qwen2.5-coder:7b`, `llama3.1:8b` and `qwen2.5-coder:1.5b` (digests in
`outputs/run_20261117/manifest.json`), on a laptop with an NVIDIA GeForce RTX 4050 GPU and 16 GB of
RAM under Windows 11 and Python 3.13. Each call asked for the complete corrected
function and a final line `CONFIDENCE: p` with p in [0, 1], at temperature 0.2 with seeds
0-2 and at most 1024 new tokens. The last code block of the response was executed against
the full suite in a separate process with time and memory limits. Responses without a code block
count as failures; responses without a parseable confidence are excluded from calibration only and
counted.

Every prompt had the same structure: a one-line role statement, the task description, the function
name, the buggy code, the condition-specific context (if any), and a fixed instruction stating that
the code contains exactly one bug and asking for the corrected function and the confidence line.
The model was never shown test cases, expected outputs or error messages, so a repair had to come
from the description and the code alone. Model-generated code was executed only inside a child
process with a time limit and a memory limit; on Windows the per-case timer is unavailable and
only the whole-run limit of 20 seconds applied, which no run reached.

### 3.6 Outcomes and analysis
*Primary:* pass@1, the share of runs whose repair passes all hidden cases. *Calibration:*
over-confidence gap (mean stated confidence minus accuracy), Brier score, and expected calibration
error with ten equal-width bins. *Secondary:* pass@1 by bug category.

The unit of analysis is the bug instance; seeds are averaged within instance and are not treated
as independent observations. For each model and each non-baseline condition we report the mean
paired difference to code only with a percentile bootstrap 95% interval (10,000 resamples of
instances), and an exact McNemar test on instance-level success (majority of seeds). P-values are
Holm-adjusted (Holm 1979) across all model-by-condition comparisons; alpha = .05. Hypotheses: H1,
misleading explanations lower pass@1; H2, accurate explanations change pass@1 (two-sided); H3,
misleading explanations raise the over-confidence gap.

### 3.7 Ethics, reproducibility and use of AI tools
No human participants were involved. Code, tasks, explanations, raw responses, per-case logs and
analysis scripts are in the repository; the README maps each table and figure to a command.

In line with the journal's policy on large language models, we document their use here. Apart from
the models under study, an AI assistant (Claude, Anthropic) wrote most of the benchmark and
analysis code, drafted the tasks and seeded bugs, launched the experiment on the author's
computer, made the first-pass audit of explanations and the classification of surviving mutants,
searched for literature and drafted the manuscript text. The author reviewed these materials and
is accountable for the content.

## 4. Results
### 4.1 Suite validation
All 20 references and all alternative solutions passed the full suite. The full suite detected
all 40 seeded bugs; the short suite detected 29 (72.5%). Table 2 and Figure 1 show that the
shortfall is concentrated in boundary/operator bugs, of which the short suite caught 2 of 9,
followed by loop-condition bugs (7 of 10). The hard-coded solution passed the short suite and was
rejected by the full one. Of 128 generated mutants the full suite detected 123 and the short suite 104. The five survivors
were inspected by hand and all are equivalent to their reference (for example, starting a summation
loop at 0 instead of 1; `docs/equivalent_mutants.md`), so the full suite detected 123 of 123
non-equivalent mutants and the short suite 104 of 123 (84.6%).
(Source: `outputs/validation/summary.json`, `validation.csv`; run on Windows 11, Python 3.13.15.)

**Table 2. Seeded bugs detected by suite and category.**

| Category | n | Short suite | Full suite |
|---|---|---|---|
| Off-by-one | 7 | 7 | 7 |
| Loop condition | 10 | 7 | 10 |
| Base case | 8 | 8 | 8 |
| Boundary/operator | 9 | 2 | 9 |
| Data-structure update | 6 | 5 | 6 |
| **Total** | **40** | **29 (72.5%)** | **40 (100%)** |

**Figure 1.** Share of seeded bugs detected by the short and full suites, by category
(`figures/fig_validation.png`).

### 4.2 Repair accuracy by condition
All 1,440 responses contained a code block and a parseable confidence; no run timed out. Table 3
gives pass@1 (`tables/pass_at_1.csv`, `pass_at_1_audited.csv`; Figure 2).

**Table 3. pass@1 by model and condition (95% bootstrap CI over instances).**

| Model | Code only | Notes | Accuracy-seeking expl. (audited, n=33) | same, all 40 | Misleading expl. |
|---|---|---|---|---|---|
| qwen2.5-coder:7b | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| llama3.1:8b | 1.00 | 1.00 | 1.00 | 0.98 [0.95, 1.00] | 0.98 [0.95, 1.00] |
| qwen2.5-coder:1.5b | 0.55 [0.40, 0.70] | 0.55 [0.40, 0.70] | 0.73 [0.58, 0.87] | 0.65 [0.50, 0.79] | 0.51 [0.36, 0.66] |

The two larger models were at ceiling: `qwen2.5-coder:7b` passed all 480 runs and `llama3.1:8b`
failed 4 of 480 (two runs each on one instance, in the two explanation conditions). For these
models the benchmark cannot show a benefit of context, and it shows no harm from misleading
explanations.

For `qwen2.5-coder:1.5b` (Table 4; `tables/comparisons_audited.csv`), the accuracy-seeking
explanation raised pass@1 by 0.09 on the 33 audited instances (95% CI 0.01 to 0.19); three
instances moved from failure to success and none the other way (exact McNemar p = .25). On all 40
instances the difference was 0.10 (CI 0.02 to 0.20; 4 vs 0 instances, p = .125). The misleading
explanation lowered pass@1 by 0.04 (CI -0.13 to 0.04; 1 instance better, 3 worse, p = .625).
Reference notes made no difference (0.00, CI -0.05 to 0.04). After Holm adjustment over the nine
model-by-condition comparisons every adjusted p-value was 1.0. H1 and H2 are therefore not
supported at the pre-specified level; the bootstrap interval for the accuracy-seeking explanation
excludes zero, which we treat as suggestive only.

**Table 4. Differences to code only, qwen2.5-coder:1.5b.**

| Condition | n | Mean diff. | 95% CI | Better / worse | McNemar p | Holm p |
|---|---|---|---|---|---|---|
| Notes | 40 | 0.00 | -0.05, 0.04 | 0 / 1 | 1.00 | 1.00 |
| Accuracy-seeking expl. (audited) | 33 | +0.09 | 0.01, 0.19 | 3 / 0 | .25 | 1.00 |
| Accuracy-seeking expl. (all) | 40 | +0.10 | 0.02, 0.20 | 4 / 0 | .125 | 1.00 |
| Misleading expl. | 40 | -0.04 | -0.13, 0.04 | 1 / 3 | .625 | 1.00 |

### 4.3 Calibration
Stated confidence took only five values (0.8, 0.9, 0.95, 0.99, 1.0), and 603 of 1,440 runs (42%)
reported 1.0. Table 5 (`tables/calibration.csv`; Figures 3-4) shows that the two larger models were
slightly under-confident (gap -0.08 to -0.03), which at ceiling accuracy means only that they did
not say 1.0. The small model reported a mean confidence between 0.995 and 1.000 in every condition
while its accuracy ranged from 0.51 to 0.65, an over-confidence gap of 0.34 to 0.49. The gap was
largest with misleading explanations (0.49) and smallest with accuracy-seeking ones (0.34), but the
change comes entirely from accuracy: confidence did not move. No inferential test of the gap was
pre-specified, so H3 is assessed descriptively: the direction agrees with H3, the size is small
relative to the baseline gap (0.45), and it is not evidence that misleading text raises confidence.

**Table 5. Calibration (all runs had a confidence; n = 120 per cell).**

| Model | Condition | Mean conf. | Accuracy | Gap | Brier | ECE |
|---|---|---|---|---|---|---|
| qwen2.5-coder:7b | code only | 0.957 | 1.000 | -0.043 | 0.002 | 0.043 |
| | notes | 0.964 | 1.000 | -0.036 | 0.002 | 0.036 |
| | accuracy-seeking | 0.965 | 1.000 | -0.035 | 0.002 | 0.035 |
| | misleading | 0.962 | 1.000 | -0.038 | 0.002 | 0.038 |
| llama3.1:8b | code only | 0.921 | 1.000 | -0.080 | 0.008 | 0.080 |
| | notes | 0.924 | 1.000 | -0.076 | 0.007 | 0.076 |
| | accuracy-seeking | 0.934 | 0.983 | -0.050 | 0.019 | 0.050 |
| | misleading | 0.923 | 0.983 | -0.061 | 0.022 | 0.061 |
| qwen2.5-coder:1.5b | code only | 0.998 | 0.550 | 0.448 | 0.450 | 0.448 |
| | notes | 0.998 | 0.550 | 0.448 | 0.450 | 0.448 |
| | accuracy-seeking | 0.995 | 0.650 | 0.345 | 0.347 | 0.345 |
| | misleading | 1.000 | 0.508 | 0.492 | 0.492 | 0.492 |

### 4.4 Additional analysis
*By category* (`tables/by_category.csv`). With code only, the small model repaired off-by-one bugs
most often (0.86) and loop-condition bugs least often (0.23); boundary/operator 0.78, base case
0.50, data-structure update 0.44. Under misleading explanations boundary/operator fell to 0.56 and
data-structure update rose to 0.67; with 6-10 instances per category these are descriptive only.

*Unchanged code* (exploratory, not pre-specified; `scripts/unchanged_analysis.py`,
`tables/unchanged.csv`). Almost every failure of the small model was a response that returned the
buggy function unchanged: 53 of 54 failures with code only, 54 of 54 with notes and 59 of 59 with
misleading explanations, i.e. 44%, 45% and 49% of all runs. With accuracy-seeking explanations 29
of 42 failures were unchanged code (24% of runs). Eleven of the 40 instances were never repaired by
this model in any condition and 15 were always repaired. The four failures of `llama3.1:8b` were
changed but still incorrect programs.

**Figures 2-4.** pass@1 by model and condition; over-confidence gap; reliability diagram
(`figures/fig_pass_at_1.png`, `fig_calibration.png`, `fig_reliability.png`).

## 5. Discussion
**Answer to the research question.** On this benchmark, adding an explanation to the prompt did not
reliably change repair accuracy. For two 7-8B models the tasks were too easy to reveal any effect.
For the 1.5B model the differences ran in the hypothesised directions - an explanation that names
the fault helped, one that endorses the faulty code hurt slightly - but none survived the planned
correction for multiple comparisons, and the study, with 40 instances, was only able to detect
large effects. We therefore report H1 and H2 as not supported rather than refuted.

**What the small model did.** The most consistent observation is not about context. The small model
declared near-certainty in every run and, in close to half of them, handed back the code it was
asked to fix. An explanation that pointed at the fault roughly halved that behaviour, whereas true
but non-specific notes had no effect at all. This is consistent with reports that code models'
confidence does not track correctness (Spiess et al. 2025) and that weaker models overestimate themselves most
(Singh et al. 2025), and with findings that repair improves when the prompt carries information that localises
the failure (Campos et al. 2025). It does not match the sensitivity to added context reported for arithmetic
problems (Shi et al. 2023): here irrelevant-but-true text changed nothing, and false text changed little. One
reading is that single-edit bugs in ten-line functions leave little for a misleading sentence to
disturb once a model can see the fault at all; this is a conjecture, not something we tested.

**The explanations themselves.** Only 12 of 40 explanations produced with an accuracy-seeking prompt
were free of false statements, and 7 missed the fault entirely, although the same model repaired
every one of these bugs when asked to. Fluent explanations of buggy code from an 8B model are thus
frequently wrong in detail. This echoes work that finds model-written explanations mostly correct
but uneven in other respects (Oli et al. 2023), and it matters for tools that show such explanations to novices
(Kurniawan et al. 2025): the explanations were worse than the repairs.

**Suite validation.** A four-case suite of typical inputs missed 11 of 40 seeded bugs and 7 of 9
boundary/operator bugs, and accepted a hard-coded solution. Had we scored repairs with such a suite,
unchanged buggy code would often have counted as a successful repair. This agrees with the
literature on patches that overfit weak tests (Yu et al. 2019; Xin and Reiss 2017) and supports checking a suite with seeded
faults before using it as an oracle (Jia and Harman 2011; Just et al. 2014).

**Implications for benchmark design.** The ceiling reached by two mid-sized local models is itself
informative. Single-edit faults in introductory exercises, the staple of debugging instruction, no
longer discriminate between conditions for models of 7-8B parameters, and any future study of
context effects on repair needs items that such models fail at a meaningful rate under the
baseline. Options that preserve the educational setting include multi-fault programs, faults that
require understanding an ambiguous specification, and authentic incorrect student submissions,
as collected in educational repair benchmarks (Koutcheme et al. 2024). The validation step used here transfers
directly to such items: seeded faults and alternative correct solutions expose a weak oracle
regardless of how hard the underlying task is.

**Threats to validity.** *Construct:* passing tests is agreement with expected outputs on selected
inputs, not proof of correctness; stated confidence is a verbal report with five observed values,
not a probability derived from the model. *Internal:* explanations were written by one of the
evaluated models, so explanation conditions also differ in whatever else that model writes; the
manipulation check was a first pass by an AI assistant confirmed by the single author, with no
independent second rater; the amendment restricting the primary analysis to 33 instances was made after seeing the
explanations (but before any repair run). *External:* 40 hand-seeded single-edit bugs in 20 small
tasks are not real student errors; three quantised local models do not represent larger or hosted
models; common task types may be familiar to the models despite newly written code. *Conclusion:*
ceiling performance removes two of three models from the comparison; with 40 instances and three
seeds, non-significant differences are not evidence of no effect; the unchanged-code analysis is
post hoc; no test was planned for calibration differences. The findings concern models and say
nothing about how students learn.

## 6. Conclusion
We asked whether an explanation placed in the prompt - accurate or misleading - changes how well
open-weight language models repair novice-level Python bugs and how confident they say they are. A
benchmark of 40 seeded bugs was built and its tests validated: the full suite caught every seeded
bug where a short suite of typical cases caught 29 of 40. In 1,440 repair runs, two 7-8B models
were at ceiling in every condition, and for a 1.5B model neither the benefit of an accuracy-seeking
explanation (+0.09) nor the cost of a misleading one (-0.04) was statistically reliable after
correction. The hypothesised harm of misleading explanations was not demonstrated. What the data do
show is that the small model was almost always certain and frequently returned the faulty code
untouched, and that explanations written by an 8B model for buggy code were fully accurate in only
12 of 40 cases. For builders of tutoring and repair pipelines the practical points are to validate
test oracles with seeded faults, not to trust self-reported confidence from small models, and to
check generated explanations before showing or reusing them. Future work should use harder and
real student bugs so that capable models are below ceiling, more instances and a second human
rater, confidence derived from token probabilities, and - with ethical approval - the classroom
study that motivated this project.

## Statements and Declarations
See `DECLARATIONS.md` (data and code availability, CRediT, AI use, conflict of interest, funding,
ethics).
