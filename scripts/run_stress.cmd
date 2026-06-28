@echo off
REM ============================================================
REM ZeroGateSim stress sweep helper
REM Target local repo folder: C:\dev\zerogate_sim
REM GitHub: not used
REM ============================================================

cd /d C:\dev\zerogate_sim
set P=.venv\Scripts\python.exe
if not exist "%P%" (
  echo Virtual environment not found at %P%
  exit /b 1
)

"%P%" -m zerogate_sim.stress --start-seed 0 --count 10 --out runs\stress_0_9_v025

echo.
echo Upload this file for review: C:\dev\zerogate_sim\runs\stress_0_9_v025\stress_bundle.zip
