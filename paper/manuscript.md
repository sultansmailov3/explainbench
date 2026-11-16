# Explanation Context and Bug-Repair Calibration in Open-Weight Code LLMs on Novice Python Tasks

Sultan Kalzhigit, Astana IT University (SE-2416)

> DRAFT v0.1. Sections 1-3 and 4.1 are written; 4.2-4.4, 5, 6 and the abstract numbers depend on
> the experiment and are marked **[RESULT ...]**. Do not fill them from anything except
> `outputs/run_*/tables/`. Citations [n] refer to `paper/references.md`; statements about sources
> were drafted from abstracts and must be checked against the full papers by the author.
> Move the text into the target journal's template once the journal is fixed.

## Abstract (to finalise, 200-250 words)
**Background.** Novice programmers increasingly read explanations of code produced by large
language models (LLMs), and the same explanations are fed back to models as context in tutoring
and repair tools. An explanation can be accurate, or it can confidently present faulty code as
correct. **Aim.** We test how the presence and the accuracy of an explanation in the prompt change
the repair accuracy and the stated confidence of open-weight code LLMs on novice-level Python bugs.
**Method.** We built a benchmark of 20 tasks with 40 hand-seeded bugs in five categories and 144
hidden test cases, validated with seeded faults, alternative correct solutions and generated
mutants. [RESULT: k] locally run models repaired each bug under four conditions (code only,
documentation notes, accurate explanation, misleading explanation) with [RESULT: s] seeds.
**Results.** The full suite detected 40/40 seeded bugs, whereas a four-case suite detected 29/40
(72.5%). [RESULT: pass@1 by condition, differences with 95% CIs, Holm-adjusted p; over-confidence
gap by condition]. **Conclusion.** [RESULT-dependent].

**Keywords:** automated program repair; confidence estimation; computing education; mutation
analysis; prompt context; test adequacy

## 1. Introduction
Generative language models are now part of how beginners learn to program. Controlled and
observational studies describe both benefits and risks: learners supported by a code generator
completed authoring tasks more successfully without a measured loss on later manual tasks [1],
students rated model-written code explanations as more accurate and easier to understand than
explanations written by peers [2], and observations of novices working with a code assistant
documented cognitive and metacognitive difficulties [3]. Explanations of code are among the most
common kinds of support, and their properties are known to shift with the prompt, the code, the
language and the model version [4]. Recent tools for novice debugging try to keep the learner
active rather than hand over a fix, because over-reliance is a recurring concern [7, 8].

An explanation is not always right. A model asked to describe a buggy function may describe the
intended behaviour instead of the actual one, and the result reads as a fluent endorsement of
faulty code. Studies of AI-assisted decision making show that incorrect explanations can mislead
people even when the underlying advice is sound [20, 21, 22]. Much less is known about the
machine side of the same situation. Explanations are routinely passed back to models as context -
in tutoring pipelines, in repair tools that add feedback to the prompt [9, 11], and in agent
loops - and language models are known to be sensitive to context that should not change the answer
[19]. If a misleading explanation lowers repair accuracy while leaving stated confidence
unchanged, any system that chains explanation and repair inherits that failure. Calibration of
code models is itself an open problem: generated code is frequently accompanied by confidence that
does not track correctness [14, 17, 18].

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
2. **A controlled comparison** of four prompt contexts - code only, documentation notes, an
   accurate explanation and a misleading explanation - on the same bugs, models and seeds.
3. **A calibration analysis** of self-reported confidence under these contexts (over-confidence
   gap, Brier score, expected calibration error).
4. **A reproducibility package** in which every reported number is regenerated from logs.

Section 2 reviews related work, Section 3 describes materials and methods, Section 4 reports
results, Section 5 discusses them and their limits, and Section 6 concludes.

## 2. Related Work
**LLM explanations for novices.** Work on model-written explanations has mostly evaluated their
quality or their reception by learners. Explanations were judged favourably against student-written
ones [2]; their correctness is typically high while completeness, conciseness and specificity lag
[4]; and a large randomised classroom comparison examined whether explanations that stress
different aspects of a program help more than generic ones [5]. Qualitative work on novices solving
tracing problems with a chatbot available shows varied patterns of use [6]. These studies treat the
explanation as an output for a human reader. We treat it as an input to a model.

**LLM-based repair of novice programs.** Repair of student programs with language models has
moved from single systems evaluated on a few hundred submissions [10] to shared benchmarks with
functional-correctness metrics such as pass@k, in which the prompt may also carry extra context
such as grader feedback [9]. Evaluations across languages report that adding failing-test
information to the prompt improves repair [11]. Small single-function benchmarks with one-line
defects [12] and hand-written function-level benchmarks scored by unit tests [13] established the
evaluation style we follow. None of these studies varies the *truthfulness* of the added context.

**Confidence and calibration.** Modern neural networks are often miscalibrated [15]. Language
models can be asked to assess their own answers, with encouraging but task-dependent results [16].
For code, studies find that confidence is not well aligned with correctness without correction
[14], that calibration of code reasoning can be improved with prompting and post-hoc scaling [17],
and that weaker models overestimate themselves most [18]. We add one factor these studies hold
fixed: what the prompt says about the code.

**Context sensitivity and misleading explanations.** Irrelevant sentences in a problem statement
reduce model accuracy on arithmetic reasoning [19]. In human-AI decision making, incorrect
explanations impair performance and later reasoning [20, 21], and persuasive but wrong explanations
can stop people from checking correct advice [22]. Our misleading-explanation condition is the
model-side analogue.

**Test adequacy.** A repair counts as correct only relative to its tests. Patches that pass a weak
suite yet remain wrong are a known problem in test-based repair [26, 27]. Mutation analysis measures
a suite by the seeded faults it detects [23]; mutant detection correlates with real-fault detection
[24], and the technique has been applied to the test suites of programming-assignment graders [25].
Benchmark problems that appear in training data are a further threat to evaluation [28, 29]. We
therefore validate our suite before using it and write the tasks and bugs ourselves.

**Table 1. Closest studies.** (complete after reading the full papers)

| Study | Subjects | Task | Context varied | Misleading context | Confidence measured |
|---|---|---|---|---|---|
| Koutcheme et al. [9] | LLMs | repair of student programs | optional feedback | no | no |
| Campos et al. [11] | LLMs | repair, several languages | failing-test information | no | no |
| Spiess et al. [14] | LLMs | completion, synthesis, repair | - | no | yes |
| Shi et al. [19] | LLMs | arithmetic word problems | irrelevant sentences | irrelevant, not false | no |
| Spitzer et al. [21] | humans | AI-assisted decisions | explanation correctness | yes | (verify) |
| **This work** | open-weight LLMs | repair of seeded novice bugs | none / docs / accurate / misleading explanation | **yes** | **yes** |

**Gap.** Repair studies vary how much context a model receives but not whether it is true;
calibration studies fix the context; studies of misleading explanations concern human readers. No
study we found measures repair accuracy and confidence of code models when an explanation of the
buggy code is accurate versus misleading.

## 3. Materials and Methods
### 3.1 Design
A within-instance factorial design: every bug instance is presented to every model under each of
four context conditions with the same seeds. The analysis plan was fixed in `PROTOCOL.md` and
tagged in the repository before the first model run [RESULT: tag and commit hash].

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
that they appear verbatim in model training data [28, 29]; the task types themselves are common.

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
| docs | documentation notes on the relevant feature [RESULT: source and Python version of excerpts] |
| accurate explanation | LLM-written description of what the buggy code actually does |
| misleading explanation | LLM-written description presenting the buggy code as correct |

Explanations were generated once per instance by a fixed explainer model at temperature 0 and
cached. The two explanation conditions use an identical prompt wrapper, so only the explanation
text differs. Explanations may not contain code. **Manipulation check:** the author read all 80
explanations and recorded whether each was accurate or misleading as intended
(`explanations/AUDIT.csv`); [RESULT: n passed, n regenerated/excluded and why].

Code only is the baseline because it is the standard input of repair benchmarks [9, 12]; the
documentation condition controls for the mere presence of extra, true, non-specific text.

### 3.5 Models and procedure
[RESULT: model names, parameter counts, quantisation, Ollama digests from `manifest.json`], run
locally through Ollama on [RESULT: hardware, OS]. Each call asked for the complete corrected
function and a final line `CONFIDENCE: p` with p in [0, 1], at temperature 0.2 with seeds
0..[RESULT] and at most 1024 new tokens. The last code block of the response was executed against
the full suite in a separate process with time and memory limits. Responses without a code block
count as failures; responses without a parseable confidence are excluded from calibration only and
counted.

### 3.6 Outcomes and analysis
*Primary:* pass@1, the share of runs whose repair passes all hidden cases. *Calibration:*
over-confidence gap (mean stated confidence minus accuracy), Brier score, and expected calibration
error with ten equal-width bins. *Secondary:* pass@1 by bug category.

The unit of analysis is the bug instance; seeds are averaged within instance and are not treated
as independent observations. For each model and each non-baseline condition we report the mean
paired difference to code only with a percentile bootstrap 95% interval (10,000 resamples of
instances), and an exact McNemar test on instance-level success (majority of seeds). P-values are
Holm-adjusted [30] across all model-by-condition comparisons; alpha = .05. Hypotheses: H1,
misleading explanations lower pass@1; H2, accurate explanations change pass@1 (two-sided); H3,
misleading explanations raise the over-confidence gap.

### 3.7 Ethics and reproducibility
No human participants were involved. Code, tasks, explanations, raw responses, per-case logs and
analysis scripts are in the repository; the README maps each table and figure to a command.

## 4. Results
### 4.1 Suite validation
All 20 references and all alternative solutions passed the full suite. The full suite detected
all 40 seeded bugs; the short suite detected 29 (72.5%). Table 2 and Figure 1 show that the
shortfall is concentrated in boundary/operator bugs, of which the short suite caught 2 of 9,
followed by loop-condition bugs (7 of 10). The hard-coded solution passed the short suite and was
rejected by the full one. Of 128 generated mutants the full suite detected 123 (96.1%) and the
short suite 104 (81.3%); the five survivors [RESULT: manual classification - equivalent or not].
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
[RESULT: Table 3 from `tables/pass_at_1.csv`; Table 4 from `tables/comparisons.csv`; Figure 2.]

### 4.3 Calibration
[RESULT: Table 5 from `tables/calibration.csv`; Figures 3-4; number of runs without confidence.]

### 4.4 Additional analysis
[RESULT: pass@1 by bug category from `tables/by_category.csv`; 3-5 inspected failure examples
under the misleading condition, quoted from `results.jsonl`.]

## 5. Discussion
[RESULT-dependent: answer H1-H3 with the adjusted p-values; compare with [9, 11, 14, 19, 21].]

**Threats to validity (apply regardless of outcome).** *Construct:* passing tests is agreement with
expected outputs on selected inputs, not proof of correctness; stated confidence is a verbal report,
not a token probability. *Internal:* explanations were written by a model, so the conditions also
differ in whatever else that model does; the manipulation check was done by one person. *External:*
40 hand-seeded single-edit bugs in 20 small tasks are not real student errors; quantised local
models may not represent larger ones; common task types may still be familiar to the models.
*Conclusion:* with 40 instances only large effects are detectable; non-significant differences are
not evidence of no effect. The findings concern models and say nothing about how students learn.

## 6. Conclusion
[RESULT-dependent, 200-300 words, no new results. Future work: more instances and real student
bugs; token-probability confidence; the approved classroom study.]

## Declarations
See `DECLARATIONS.md` (data and code availability, CRediT, AI use, conflict of interest, funding,
ethics).
