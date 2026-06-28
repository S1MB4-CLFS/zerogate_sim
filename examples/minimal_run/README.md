# Minimal Run Example

This folder is intentionally light. Generated run outputs belong under local `runs/`, not in the source repository.

Try:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m zerogate_sim.demo --seed 42 --out runs\demo_seed_42
notepad runs\demo_seed_42\summary.md
```

Upload `runs\demo_seed_42\run_bundle.zip` only when asking for review.
