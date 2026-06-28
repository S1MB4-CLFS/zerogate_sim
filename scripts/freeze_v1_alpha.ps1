# ============================================================
# ZeroGateSim v1.0-alpha first research-alpha release record
# Target local repo folder: C:\dev\zerogate_sim
# Requires two proof records: initial and fresh-seed reproduction
# ============================================================

Set-Location C:\dev\zerogate_sim

$P = ".\.venv\Scripts\python.exe"

if (!(Test-Path $P)) {
    throw "Virtual environment not found. Run setup first."
}

& $P -m zerogate_sim.release_record `
    --proof-dir runs\proof_wide243_0_8_v033 `
    --proof-dir runs\proof_wide243_9_17_repro `
    --out runs\first_research_alpha_v1_0_alpha

notepad runs\first_research_alpha_v1_0_alpha\first_research_alpha_record.md
explorer runs\first_research_alpha_v1_0_alpha
