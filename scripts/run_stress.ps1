# ============================================================
# ZeroGateSim stress sweep helper
# Target local repo folder: C:\dev\zerogate_sim
# GitHub: not used
# ============================================================

param(
    [int]$StartSeed = 0,
    [int]$Count = 10,
    [string]$Out = "runs\stress_0_9_v025"
)

Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) {
    throw "Virtual environment not found at $P"
}

& $P -m zerogate_sim.stress --start-seed $StartSeed --count $Count --out $Out
Write-Host ""
Write-Host "Upload this file for review: C:\dev\zerogate_sim\$Out\stress_bundle.zip"
