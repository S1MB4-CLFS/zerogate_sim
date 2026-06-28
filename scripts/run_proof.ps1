# ZeroGateSim proof harness runner
# Target local repo folder: C:\dev\zerogate_sim
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { throw "Virtual environment not found. Run setup first." }
& $P -m zerogate_sim.proof --profile wide243 --start-seed 0 --count 9 --out runs\proof_wide243_0_8_v033
