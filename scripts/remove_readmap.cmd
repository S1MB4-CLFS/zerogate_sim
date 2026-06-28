@echo off
REM ZeroGateSim v0.2.14-alpha hygiene helper
REM Removes accidental READMAP.md if present.
cd /d "%~dp0\.."
if exist READMAP.md (
  del READMAP.md
  echo Removed READMAP.md. Strategic read now lives in ROADMAP.md.
) else (
  echo READMAP.md not present. Nothing to remove.
)
