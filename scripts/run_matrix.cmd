@echo off
REM ============================================================
REM ZeroGateSim trinary matrix runner
REM Target local repo folder: C:\dev\zerogate_sim
REM GitHub: not used
REM ============================================================
cd /d C:\dev\zerogate_sim
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run the setup/update block first.
  exit /b 1
)
.venv\Scripts\python.exe -m zerogate_sim.matrix --profile triad27 --start-seed 0 --count 9 --out runs\matrix_triad27_0_8_v026

echo.
echo Upload this file for review:
echo C:\dev\zerogate_sim\runs\matrix_triad27_0_8_v026\matrix_bundle.zip
