# Minimal Run Example

A tiny run is for onboarding only. It is not the v1.0-alpha proof harness.

From the repo root:

```powershell
$P = ".\.venv\Scripts\python.exe"
& $P -m zerogate_sim.demo --seed 42 --out runs\example_seed_42
notepad runs\example_seed_42\summary.md
```

For proof records, use `zerogate-proof`, `zerogate-record`, and `zerogate-release` as documented in the README.
