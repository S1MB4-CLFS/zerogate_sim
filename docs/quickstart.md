# ZeroGateSim Quickstart

This guide gives three entry paths:

1. install and test;
2. run a small demo;
3. run proof-scale commands only when ready.

The full proof harness is intentionally heavy. Do not start there unless you want your computer to wrestle the weather.

## Install/update locally

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m pip install -e ".[dev]"
& $P -m pytest
```

Expected result: all tests pass.

## Small demo

```powershell
& $P -m zerogate_sim.demo --seed 42 --out runs\demo_seed_42
notepad runs\demo_seed_42\summary.md
explorer runs\demo_seed_42
```

The demo creates one toy field and one run bundle.

## Small proof smoke test

```powershell
& $P -m zerogate_sim.proof --profile triad27 --start-seed 0 --count 1 --out runs\proof_smoke
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_smoke
notepad runs\proof_smoke\proof_record.md
explorer runs\proof_smoke
```

This is not the full proof record. It is a small sanity check.

## Full proof harness

The full proof harness used for the first-research-alpha record is:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 0 --count 9 --out runs\proof_wide243_0_8_v033
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_0_8_v033
```

Fresh-seed reproduction:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 9 --count 9 --out runs\proof_wide243_9_17_repro
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_9_17_repro
```

Combined first-research-alpha record:

```powershell
& $P -m zerogate_sim.release_record `
    --proof-dir runs\proof_wide243_0_8_v033 `
    --proof-dir runs\proof_wide243_9_17_repro `
    --out runs\first_research_alpha_v1_0_alpha
```

## Evidence rule

Generated `runs/` are evidence, not source. They are intentionally excluded from Git.

Use bundles for review. Do not commit heavy weather into the repo.
