@echo off
setlocal
cd /d C:\dev\zerogate_sim
set P=.venv\Scripts\python.exe
if not exist "%P%" (
  echo Virtual environment not found: %P%
  exit /b 1
)
"%P%" -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_0_8_v033
