# ============================================================
# ZeroGateSim trinary matrix runner
# Target local repo folder: C:\dev\zerogate_sim
# GitHub: not used
# ============================================================

Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) {
    throw "Virtual environment not found. Run the setup/update block first."
}

& $P -m zerogate_sim.matrix --profile triad27 --start-seed 0 --count 9 --out runs\matrix_triad27_0_8_v026

Write-Host ""
Write-Host "Upload this file for review:"
Write-Host "C:\dev\zerogate_sim\runs\matrix_triad27_0_8_v026\matrix_bundle.zip"
