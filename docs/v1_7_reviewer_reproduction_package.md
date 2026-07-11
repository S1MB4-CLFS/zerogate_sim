# v1.7.9-alpha — Reviewer Start Here / Reproduction Package

> **Historical package:** this records the pre-closeout reviewer route. Current
> authority starts at the v1.7.11 evidence-integrity correction and `0 / HOLD`.

**Version:** `v1.7.9-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`  
**Purpose at v1.7.9:** make the then-current evidence path readable and reproducible before core-question closeout.

This gate packages a reviewer-facing path. It is not a new science crown and not the core-question closeout.

## What it packages

- root `REVIEWER_START_HERE.md`;
- three-rung run order: `triad27 -> deep81 -> wide243`;
- a reusable rung-summary CLI: `zerogate-v1-7-holdout-rung-summary`;
- a reviewer package CLI: `zerogate-v1-7-reviewer-package`;
- expected output rules for full report, compressed summary, visual card, evaluator/bundle output;
- explicit boundaries against role-blind discovery, physics, cosmology, and manuscript-v2 overreach.

## Known routine

```text
pre-register expectations
-> run smallest holdout rung
-> inspect full and compressed outputs
-> preserve positive controls
-> preserve negative controls
-> prevent label/name leakage
-> compare against simpler explanations
-> move to larger rung only after the smaller rung is clean
-> close the question only after reproduction packaging is coherent
```

## Reviewer package command

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { $P = "python" }
& $P -m zerogate_sim.v1_7_reviewer_reproduction_package --out runs\v1_7_9_reviewer_reproduction_package
```

The generated package includes separate PowerShell scripts for `triad27`, `deep81`, and `wide243`. Those scripts should be run one at a time, never as a first-pass all-weather block.
