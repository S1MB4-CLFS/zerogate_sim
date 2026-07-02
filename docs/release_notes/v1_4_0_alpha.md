# ZeroGateSim v1.4.0-alpha — Cross-Logic Comparison Report

## Purpose

Begin the v1.4 line by aggregating known-logic projection mirror results across completed matrix runs.

## Added

- `src/zerogate_sim/cross_logic_report.py`
- `tests/test_cross_logic_report.py`
- `docs/known_logic_comparison_report.md`
- `zerogate-cross-logic` console script

## Outputs

The cross-logic report writes:

```text
cross_logic_comparison_summary.csv
cross_logic_comparison_matrix_summary.csv
cross_logic_comparison_mirror_summary.csv
cross_logic_comparison_read.md
cross_logic_report_bundle.zip
```

## Boundary

This release does not add a native gate and does not run a new proof harness.

It reads completed matrix runs and compares how the v1.3 projection mirrors behave across them.

## Claim boundary

Allowed:

> ZeroGateSim can aggregate projection mirror outputs across completed toy-field matrix runs and report visible pressure, safety breaches, and mirror-specific loss reports.

Forbidden:

> Cross-logic aggregation proves ZeroGateSim is equivalent to a known logic system or proves physical dimensional genesis.
