# ZeroGateSim v1.6.10-alpha Release Notes

## Purpose

`v1.6.10-alpha` adds shadow lane splitting and local runs hygiene scaffolding.

The hardened triad27 result showed the frozen transparent `shadow_score` could see pressure density but did not yet earn relation/return/demotion-specific discrimination. This release keeps the historical score frozen and adds fixed lane-specific candidate scores for sharper testing.

## Added

- `zerogate-shadow-lane-discrimination`
- `zerogate-runs-inventory`
- `docs/shadow_lane_discrimination.md`
- `docs/runs_cleanup_policy.md`
- `tests/test_shadow_lane_discrimination_report.py`
- `tests/test_runs_inventory_report.py`

## Changed

- `shadow_score_report` now emits fixed lane-specific candidate score columns while preserving the historical `shadow_score`.
- README moves Core theory near the front, between identity and motivation.
- README active route names shadow lane discrimination instead of treating the global shadow score as enough.

## Boundaries

```text
no score retuning
no role-blind discovery
no detector closeout
no native witness mutation
C_Z = min(D, P, R, B)
```

## Next evidence move

After CI is green, rerun the score and lane discrimination on the hardened triad27 evidence base. If only density expands, do not move to deep81 / wide243 yet.
