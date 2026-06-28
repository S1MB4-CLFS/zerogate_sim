# ZeroGateSim repo cleanup helper
# Target repo: C:\dev\zerogate_sim
# GitHub: not used

param(
    [switch]$RemoveRuns,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Repo = "C:\dev\zerogate_sim"
if (!(Test-Path $Repo)) {
    throw "Repo folder not found: $Repo"
}

Set-Location $Repo

if (!(Test-Path "pyproject.toml") -or !(Test-Path "src\zerogate_sim")) {
    throw "Refusing cleanup: this does not look like the ZeroGateSim repo root: $PWD"
}

$Targets = @()

$Targets += Get-ChildItem -Path . -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Recurse -Force -Filter ".pytest_cache" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Recurse -Force -Filter ".mypy_cache" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Recurse -Force -Filter ".ruff_cache" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Force -Filter "build" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Force -Filter "dist" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -Directory -Recurse -Force -Filter "*.egg-info" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path . -File -Recurse -Force -Include "*.pyc", "*.pyo", ".coverage" -ErrorAction SilentlyContinue

if ($RemoveRuns -and (Test-Path "runs")) {
    $Targets += Get-Item "runs"
}

$UniqueTargets = $Targets | Sort-Object FullName -Unique

if (!$UniqueTargets -or $UniqueTargets.Count -eq 0) {
    Write-Host "Nothing to clean. Source tree already looks tidy."
    exit 0
}

Write-Host "ZeroGateSim cleanup targets:"
foreach ($Target in $UniqueTargets) {
    Write-Host "- $($Target.FullName)"
}

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry run only. Nothing removed."
    exit 0
}

foreach ($Target in $UniqueTargets) {
    Remove-Item $Target.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Cleanup complete."
if ($RemoveRuns) {
    Write-Host "Runs removed. Recreate evidence with scripts\run_demo.ps1 or scripts\run_batch.ps1."
}
