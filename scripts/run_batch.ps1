# ZeroGateSim local batch runner
# Target repo: C:\dev\zerogate_sim
# GitHub: not used

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Repo = "C:\dev\zerogate_sim"
if (!(Test-Path $Repo)) {
    throw "Repo folder not found: $Repo"
}

Set-Location $Repo

$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) {
    throw "Virtual environment not found. Run scripts\run_demo.ps1 first."
}

& $P -m zerogate_sim.batch --start-seed 0 --count 10 --out runs\sweep_0_9

Write-Host ""
Write-Host "Open:   C:\dev\zerogate_sim\runs\sweep_0_9\batch_summary.md"
Write-Host "Upload: C:\dev\zerogate_sim\runs\sweep_0_9\batch_bundle.zip"
