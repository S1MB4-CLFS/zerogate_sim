@echo off
setlocal
cd /d C:\dev\zerogate_sim
set P=.venv\Scripts\python.exe
if not exist "%P%" (
  echo Virtual environment not found. Run setup first.
  exit /b 1
)
"%P%" -m zerogate_sim.proof --profile wide243 --start-seed 0 --count 9 --out runs\proof_wide243_0_8_v033
