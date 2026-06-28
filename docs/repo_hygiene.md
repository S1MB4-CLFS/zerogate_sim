# ZeroGateSim Repo Hygiene

ZeroGateSim is local-first. Generated evidence belongs in `runs/`, and cache/build crumbs should not be confused with source code.

## Preferred cleanup command

PowerShell may block `.ps1` scripts on Windows. To avoid execution-policy noise, use the Python cleanup module or the `.cmd` wrapper.

From `C:\dev\zerogate_sim`:

```powershell
$P = ".\.venv\Scripts\python.exe"
& $P -m zerogate_sim.clean --dry-run --remove-runs
& $P -m zerogate_sim.clean --yes --remove-runs
```

Or use Command Prompt / PowerShell with the `.cmd` wrapper:

```powershell
.\scripts\clean_repo.cmd --dry-run --remove-runs
.\scripts\clean_repo.cmd --yes --remove-runs
```

## What cleanup removes

- `runs/` when `--remove-runs` is supplied
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `build/`
- `dist/`
- `*.egg-info/`
- `*.pyc`, `*.pyo`
- `.coverage`

It refuses to run unless the target folder looks like the ZeroGateSim repo root.

## What cleanup does not remove

- `.venv/`
- source files
- docs
- tests
- README / ROADMAP
- downloaded update ZIPs in Downloads

## Evidence rule

Every single demo run creates a `run_bundle.zip` inside its run folder.

Every batch sweep creates a `batch_bundle.zip` inside its batch output folder.

Upload the bundle ZIP when asking for review. The witness should receive one clean package, not a breadcrumb salad.
