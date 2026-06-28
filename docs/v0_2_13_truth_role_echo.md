# v0.2.13-alpha — Truth Roles and Echo-Mimic Witness

This release repairs the candidate truth layer after the wide243 + triad27 run exposed an echo-mimic breach.

## What changed

- Added trinary truth roles: `expresser`, `latent`, `trap`.
- Added expected trinary values for candidates: `+1`, `0`, `-1`.
- Added echo-mimic diagnostic score.
- Added matrix truth-role outputs.
- Added echo-mimic report.
- Added top-level `READMAP.md` to state how far the project can currently see.

## What did not change

The core zero-gate law did not change.

```math
C_Z^i(t)=\min(g_D^i(t),g_P^i(t),g_R^i(t),g_B^i(t))
```

Expression is still earned through strength and zero-gate coherence.

## Why this matters

The earlier binary label `designed_stable` was too crude. A latent candidate held in zero is not the same as a trap correctly rejected. A trap crowned as expression is the dangerous case.

The first real enemy is now visible:

> echo pretending to be earned coherence.

## New outputs

- `matrix_truth_role_read.md`
- `matrix_truth_role_summary.csv`
- `matrix_truth_role_candidate_summary.csv`
- `matrix_echo_mimic_report.md`
