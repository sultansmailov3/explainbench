# One-command run of the whole experiment on Windows (PowerShell).
# Usage:  .\run_all.ps1 -Models "qwen2.5-coder:7b","llama3.1:8b" -Seeds 3
# Requires: Python >= 3.10, Ollama running, models pulled (ollama pull <name>).
# The first model is also used as the explainer.
param(
    [Parameter(Mandatory = $true)][string[]]$Models,
    [int]$Seeds = 3,
    [string]$Run = ("outputs/run_" + (Get-Date -Format "yyyyMMdd_HHmm"))
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

python -m explainbench.validate --generated
python -m explainbench.make_explanations --model $Models[0]

$audit = (Get-Content explanations/AUDIT.csv | Measure-Object -Line).Lines
if ($audit -lt 2) {
    Write-Host "STOP: read the files in explanations/ and fill explanations/AUDIT.csv (manipulation check)," -ForegroundColor Yellow
    Write-Host "then run this script again. Explanations are cached, so nothing is regenerated." -ForegroundColor Yellow
    exit 1
}

python -m explainbench.run_experiment --models @Models --seeds $Seeds --out $Run
python -m explainbench.analyze --run $Run
python -m explainbench.figures --validation outputs/validation --run $Run --out figures
Write-Host "Done. Commit $Run, figures/ and explanations/ and push." -ForegroundColor Green
