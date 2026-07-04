# v1.6.6-alpha — Shadow Triad27 Preflight

`v1.6.6-alpha` adds the first trinary-weather shadow evaluation rung before deeper holdout evidence.

## Added

- `src/zerogate_sim/shadow_triad27_preflight_report.py`;
- console script `zerogate-shadow-triad27-preflight`;
- `docs/shadow_triad27_preflight.md`;
- `docs/release_notes/v1_6_6_alpha.md`;
- tests for triad27 source enforcement, score-before-target boundary, forbidden-field refusal, output files, and documentation boundaries.

## Why this exists

The shadow line had tooling for `deep81` / `wide243`, but the shadow itself had not been forced through the smaller trinary weather cube first.

The ladder is now explicit:

```text
triad27 = 3^3 local expression weather
deep81  = 3^4 perturbation / late-shock bridge
wide243 = 3^5 temporal-depth / time-axis stress
```

## Boundary

This version does not claim role-blind discovery, detector closeout, or deep/wide holdout success.

A passing triad27 preflight can only support readiness for the deeper `deep81` / `wide243` holdout evidence run.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Next

`v1.6.7-alpha` should run the deeper `deep81` / `wide243` holdout evidence after this triad27 preflight gate is green.
