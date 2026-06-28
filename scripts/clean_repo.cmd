@echo off
REM ZeroGateSim cleanup helper without PowerShell execution policy issues.
REM Target repo: C:\dev\zerogate_sim

set REPO=C:\dev\zerogate_sim
set VENV_PY=%REPO%\.venv\Scripts\python.exe

if not exist "%REPO%" (
  echo Repo folder not found: %REPO%
  exit /b 1
)

cd /d "%REPO%" || exit /b 1

if exist "%VENV_PY%" (
  "%VENV_PY%" -m zerogate_sim.clean %*
) else (
  python -m zerogate_sim.clean %*
)
