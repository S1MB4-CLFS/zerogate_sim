# v1.7.3-alpha — Baseline and Ablation Falsifier Matrix

`v1.7.3-alpha` locks the baseline and ablation enemies required by the v1.7 core question.

## Added

- `docs/v1_7_baseline_falsifier_matrix.md`
- `docs/v1_7_ablation_summary.md`
- `docs/v1_7_failure_mode_table.md`
- `src/zerogate_sim/v1_7_baseline_falsifier_matrix.py`
- `tests/test_v1_7_baseline_falsifier_matrix.py`
- CLI: `zerogate-v1-7-baseline-falsifier`

## Decision

```text
baseline_falsifier_matrix_locked_no_core_closeout
```

This version does not close the main v1.7 question. It defines what would make the native witness fail against raw, binary, dead-safe, average-gate, no-return, no-relation, no-lineage/no-return-depth, no-echo-independence, and no-zero-hold witnesses.

## Boundary

- no native witness mutation;
- no new heavy evidence crown;
- no manuscript v2 start;
- no role-blind discovery claim;
- no physics, topology, dimensions, cosmology, or observed-universe claim.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

Next gate: `v1.7.4-alpha — Perturbation Spectrum Witness`.
