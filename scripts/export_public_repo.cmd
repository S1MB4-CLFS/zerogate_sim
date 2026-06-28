@echo off
REM ZeroGateSim public source export helper.
cd /d C:\dev\zerogate_sim
set P=.\.venv\Scripts\python.exe
if not exist %P% (
  echo Virtual environment not found at %P%
  exit /b 1
)
%P% -m zerogate_sim.export_public_repo --repo . --out exports\zerogate_sim_public_repo_v1_0_2_alpha.zip
