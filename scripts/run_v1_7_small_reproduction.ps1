$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# v1.7.10-alpha small reviewer reproduction / closeout-support runner

function Run($Name, [scriptblock]$Command) {
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function RequireFile($Path, $Label) {
    if (!(Test-Path $Path)) {
        throw "Missing expected $Label`: $Path"
    }
}

Set-Location (Split-Path -Parent $PSScriptRoot)
Remove-Module PSReadLine -ErrorAction SilentlyContinue

$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { $P = "python" }

$env:PYTHONPATH = (Join-Path (Get-Location) "src")
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

Run "version check" {
    $Version = (& $P -c "import zerogate_sim; print(zerogate_sim.__version__)").Trim()
    Write-Host "ZeroGateSim version: $Version"
    if ($Version -ne "1.7.10-alpha") {
        throw "Expected 1.7.10-alpha. Found: $Version"
    }
}

Run "v1.7.10 reviewer path target test" {
    & $P -m pytest tests\test_v1_7_reviewer_path.py -q
}

$Out = "runs\v1_7_10_reviewer_reproduction_package"
if (Test-Path $Out) {
    Remove-Item $Out -Recurse -Force
}

Run "build reviewer reproduction package" {
    & $P -m zerogate_sim.v1_7_reviewer_reproduction_package --out $Out
}

Run "verify reviewer package outputs" {
    RequireFile (Join-Path $Out "v1_7_reviewer_reproduction_package_read.md") "reviewer package read"
    RequireFile (Join-Path $Out "v1_7_reviewer_reproduction_package_decision.json") "reviewer package decision"
    RequireFile (Join-Path $Out "v1_7_reviewer_path.csv") "reviewer path CSV"
    RequireFile (Join-Path $Out "v1_7_reproduction_commands.csv") "reproduction commands CSV"
    RequireFile (Join-Path $Out "v1_7_expected_outputs.csv") "expected outputs CSV"
    RequireFile (Join-Path $Out "v1_7_claim_boundary_card.csv") "claim boundary CSV"
    RequireFile (Join-Path $Out "v1_7_evidence_manifest.csv") "evidence manifest CSV"
    RequireFile (Join-Path $Out "v1_7_reviewer_reproduction_package_bundle.zip") "reviewer package bundle"
}

Write-Host "`n=== V1.7.10 SMALL REPRODUCTION COMPLETE ===" -ForegroundColor Green
Write-Host "Read:" -ForegroundColor Green
Write-Host "$((Resolve-Path (Join-Path $Out 'v1_7_reviewer_reproduction_package_read.md')).Path)"
Write-Host "`nBundle:" -ForegroundColor Green
Write-Host "$((Resolve-Path (Join-Path $Out 'v1_7_reviewer_reproduction_package_bundle.zip')).Path)"
