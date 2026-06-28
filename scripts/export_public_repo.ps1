# ============================================================
# ZeroGateSim public source export helper
# Target local repo folder: C:\dev\zerogate_sim
# Purpose: create clean public repo ZIP excluding runs/.venv/caches
# ============================================================

Set-Location C:\dev\zerogate_sim

$P = ".\.venv\Scripts\python.exe"

if (!(Test-Path $P)) {
    throw "Virtual environment not found at: $P"
}

& $P -m zerogate_sim.export_public_repo --repo . --out exports\zerogate_sim_public_repo_v1_0_2_alpha.zip
