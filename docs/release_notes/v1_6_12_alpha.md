# ZeroGateSim v1.6.12-alpha Release Notes

`v1.6.12-alpha` implements observable shadow feature candidates after the `v1.6.11-alpha` route audit.

## Purpose

The shadow line had one earned candidate signal:

```text
pressure density
```

It had not earned specific discrimination for:

```text
raw false-one pressure
demotion pressure
hold-or-demote pressure
relation-specific pressure
return-specific pressure
```

This release adds role-stripped engineered feature columns so the next hardened triad27 rerun can test whether pressure kind can be separated from pressure amount.

## Added

- `src/zerogate_sim/shadow_feature_design.py`
- `docs/shadow_feature_implementation.md`
- `tests/test_shadow_feature_implementation.py`

## Updated

- `role_stripped_feature_report.py` now emits engineered feature candidates on role-stripped feature rows.
- `shadow_triad27_hardened_evidence_report.py` emits engineered features in cell-level hardened triad27 evidence.
- `shadow_score_report.py` emits fixed feature-aware candidate score columns while preserving the historical shadow score.
- `shadow_lane_discrimination_report.py` points the active lane judge at the v1.6.12 feature-aware candidate score columns.
- README and ROADMAP now point to `v1.6.12-alpha` and preserve the bounded route.

## Boundary

This is not role-blind discovery, not detector closeout, and not a native witness mutation.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

The next evidence gate is `v1.6.13-alpha`: hardened triad27 rerun using the new feature-aware scores. deep81 / wide243 remain blocked until hardened triad27 specificity is earned.
