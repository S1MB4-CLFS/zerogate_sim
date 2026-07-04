# Release Notes — v1.6.7-alpha

## Name

Shadow Weather Hardening Foundation

## Why this exists

The actual `triad27` shadow preflight showed an honest wound: the shadow score ranked the family rows correctly, but raw-pressure / mirror-style baselines could rank them just as well. That means the shadow line cannot advance by simply scaling to `deep81` / `wide243` and hoping the larger weather makes the claim stronger.

`v1.6.7-alpha` makes the judge harder before score repair or deeper holdout trust.

## Added

- `src/zerogate_sim/shadow_weather_hardening_report.py`
- `tests/test_shadow_weather_hardening_report.py`
- `docs/shadow_weather_hardening.md`
- `docs/release_notes/v1_6_7_alpha.md`
- console script: `zerogate-shadow-weather-hardening`

## Changed

- Version bumped to `1.6.7-alpha` / `1.6.7a0`.
- Role-stripped evaluation targets now include additional target variety:
  - `target_false_pressure_density_rate`
  - `target_hold_or_demote_rate`
  - `target_return_false_pressure_share`
  - `target_native_breach_rate`
- Target-field blocking was updated so the new target fields are still forbidden in feature and score inputs.
- README, ROADMAP, triad27, and holdout docs now route through weather hardening before deeper trust.

## Boundary

This is not role-blind discovery, not detector closeout, not score retuning, and not a native witness change.

```text
C_Z = min(D, P, R, B)
```

The report reads already-written scores, joins targets only after scoring, evaluates multiple target fields, names baseline ties, and records native gate pressure beside shadow diagnostics.

## Correct next step

Run the hardening report first on the actual triad27 evidence. If it still says the shadow is trivial, repair discrimination before deeper weather. If triad27 becomes non-trivial, then run the same hardening judge across `triad27`, `deep81`, and `wide243` evidence before any closeout language.
