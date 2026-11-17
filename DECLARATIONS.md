# Declarations (text for the manuscript; adapt wording to the target journal's policy)

## Data and code availability
Code, benchmark tasks, generated explanations, the explanation audit, raw model outputs, per-case
logs, analysis scripts and figures are available at https://github.com/sultansmailov3/explainbench
(release tag `final`; protocol tag `protocol-v1`). Code is released under the MIT licence; task
data, explanations and logs under CC BY 4.0 (TO CONFIRM by the author). Model weights are not
redistributed; model names and digests are listed in `outputs/run_20261117/manifest.json`. No
personal data are used.

## Ethics statement
No human participants were involved; all data were produced by software and language models.

## AI-use declaration
Language models are the object of study (`qwen2.5-coder:7b`, `qwen2.5-coder:1.5b`, `llama3.1:8b`,
run locally; `llama3.1:8b` also generated the explanations used as experimental material). In
addition, an AI assistant (Claude, Anthropic) was used between 15 and 17 November 2026 to write
most of the benchmark and analysis code, to draft tasks and seeded bugs, to launch the experiment
on the author's computer, to make the first-pass audit of the generated explanations and the
classification of surviving mutants, to search for literature, and to draft the manuscript text.
The author reviewed the materials, is responsible for confirming the audit, the cited sources and
every reported number against the logs, and takes full responsibility for the content. AI tools
are not listed as authors.

## CRediT author contributions
Sultan Kalzhigit: Conceptualization, Methodology, Investigation, Validation, Data curation,
Writing - review & editing, Project administration. (Software, Formal analysis, Visualization and
Writing - original draft were carried out with substantial AI assistance, as declared above.)

## Conflict of interest
The author declares no conflict of interest.

## Funding
This research received no external funding. (TO CONFIRM by the author.)
