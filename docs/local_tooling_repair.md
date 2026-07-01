# Local Tooling Repair

**Scope:** operator note for local Python environment failures.  
**Not project theory. Not engine code.**

## Broken pip symptom

If editable install fails with:

```text
ModuleNotFoundError: No module named 'pip._internal.operations.build'
```

then the local virtual environment's `pip` install is corrupted or mismatched. This is not a ZeroGateSim math failure and not a simulation result.

## Repair existing venv first

```powershell
$ErrorActionPreference = "Stop"
Set-Location C:\dev\zerogate_sim

$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { throw "Python venv not found: $P" }

& $P -m ensurepip --upgrade
& $P -m pip install --upgrade --force-reinstall pip setuptools wheel
& $P -m pip --version
& $P -m pip install -e ".[dev]"
& $P -m pytest -q
```

## Rebuild venv if repair fails

```powershell
$ErrorActionPreference = "Stop"
Set-Location C:\dev\zerogate_sim

deactivate 2>$null
Remove-Item ".venv" -Recurse -Force
py -3.12 -m venv .venv

$P = ".\.venv\Scripts\python.exe"
& $P -m ensurepip --upgrade
& $P -m pip install --upgrade pip setuptools wheel
& $P -m pip install -e ".[dev]"
& $P -m pytest -q
```

## Boundary

Do not commit through a broken install gate. Repair tooling first, then rerun tests.
