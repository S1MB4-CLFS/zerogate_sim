# ZeroGateSim v0.2.8-alpha deep81 runner
# Target local repo folder: C:\dev\zerogate_sim
# GitHub: not used

Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) {
    throw "Virtual environment not found at: $P"
}
& $P -m zerogate_sim.matrix --profile deep81 --start-seed 0 --count 9 --out runs\matrix_deep81_0_8_v028
notepad runs\matrix_deep81_0_8_v028\matrix_shape_read.md
explorer runs\matrix_deep81_0_8_v028
