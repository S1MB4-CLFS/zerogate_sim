@echo off
REM ZeroGateSim v0.2.8-alpha deep81 runner
REM Target local repo folder: C:\dev\zerogate_sim
REM GitHub: not used
cd /d C:\dev\zerogate_sim
set P=.\.venv\Scripts\python.exe
if not exist %P% (
  echo Virtual environment not found at %P%
  exit /b 1
)
%P% -m zerogate_sim.matrix --profile deep81 --start-seed 0 --count 9 --out runs\matrix_deep81_0_8_v028
start notepad runs\matrix_deep81_0_8_v028\matrix_shape_read.md
start explorer runs\matrix_deep81_0_8_v028
