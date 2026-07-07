# v1.7.6-alpha — Fresh Holdout Synthetic-Field Challenge

`v1.7.6-alpha` locks the fresh holdout synthetic-field challenge required before reviewer reproduction packaging.

## Added

- `docs/v1_7_holdout_design.md`
- `docs/v1_7_holdout_expected_outputs.md`
- `docs/v1_7_holdout_weather_ladder.md`
- `docs/v1_7_candidate_name_masking.md`
- `src/zerogate_sim/v1_7_fresh_holdout_challenge.py`
- `tests/test_v1_7_fresh_holdout_challenge.py`
- CLI entry: `zerogate-v1-7-fresh-holdout-challenge`

## Locked

```text
fresh seeds not used in the reference run
held-out profile variants
controlled weather shifts
candidate-name masking
lane-level expected-output manifest written before run
triad27 / deep81 / wide243 weather rung timing
```

## Not claimed

This release adds no new heavy evidence crown, does not answer the v1.7 core question, does not start manuscript v2, does not claim role-blind discovery, does not claim independent generator validation, and does not mutate `C_Z = min(D, P, R, B)`.

## Timing

`v1.7.6-alpha` defines and optionally evaluates the holdout ladder. After `v1.7.6-alpha` is CI green, the full `triad27` / `deep81` / `wide243` holdout summaries should be run before `v1.7.7-alpha` packages reviewer-facing small / medium / full reproduction commands. `v1.7.8-alpha` is the only v1.7 gate allowed to close the core question.

The next gate is `v1.7.7-alpha — Reviewer Start Here / Reproduction Package`.
