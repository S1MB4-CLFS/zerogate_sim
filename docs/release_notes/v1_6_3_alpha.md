# v1.6.3-alpha — Shadow Baseline/Falsifier Report

## Status

Baseline comparison and falsifier gate. No role-blind discovery. No native math change.

## Delivered

- `src/zerogate_sim/shadow_baseline_falsifier_report.py`;
- console script `zerogate-shadow-baseline-falsifier`;
- `docs/shadow_baseline_falsifier.md`;
- `docs/assets/shadow_baseline_falsifier_card.svg`;
- `docs/release_notes/v1_6_3_alpha.md`;
- tests for baseline comparison output, target/role-field refusal, metrics, and documentation boundary.

## What this does

`v1.6.3-alpha` compares already-written transparent shadow scores from `v1.6.2-alpha` against separated evaluation targets from `v1.6.1-alpha`.

The report evaluates whether `shadow_score` ranks `target_raw_false_one_rate` better than trivial role-stripped baselines. Targets are loaded only after scoring has already happened.

## Boundary

This is not role-blind discovery. It does not crown, demote, or replace the current role-aware witness.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

The report also records schema gaps when exact minimum baselines from the `v1.6.0-alpha` design are not present in the current role-stripped feature files. Missing baselines are held as witness, not silently fabricated.

## Next

`v1.6.4-alpha` should perform a held-out `deep81` / `wide243` role-stripped evaluation and include exact gate baselines if the feature schema provides them.
