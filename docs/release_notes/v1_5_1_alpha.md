# ZeroGateSim v1.5.1-alpha — Threshold Sensitivity Report

## Purpose

Add a controlled threshold sensitivity reader for completed four-gate seed-block reports.

## Added

- `src/zerogate_sim/threshold_sensitivity.py`
- `tests/test_threshold_sensitivity.py`
- `docs/threshold_sensitivity_report.md`
- console script: `zerogate-threshold-sensitivity`

## Matrix support

Matrix runs now accept optional threshold overrides:

```powershell
& $P -m zerogate_sim.matrix --gate-threshold 0.50 --strength-threshold 0.30 ...
```

The matrix summary records threshold overrides when supplied.

## Outputs

```text
threshold_sensitivity_summary.csv
threshold_sensitivity_gate_summary.csv
threshold_sensitivity_mirror_summary.csv
threshold_sensitivity_read.md
threshold_sensitivity_bundle.zip
```

## Claim boundary

This release does not change the native gate law, the final witness, or the proof claim. It adds a way to compare completed reports across threshold variants so brittle operating regions become visible instead of hidden.
