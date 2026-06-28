# ZeroGateSim proof record freeze helper
# Target local repo folder: C:\dev\zerogate_sim

Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) {
    throw "Virtual environment not found: $P"
}
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_0_8_v033
