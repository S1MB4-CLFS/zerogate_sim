# v1.6.2-alpha — Transparent Shadow Score Prototype

## Status

Report-side score prototype. No role-blind verdict. No native math change.

## Delivered

- `src/zerogate_sim/shadow_score_report.py`;
- console script `zerogate-shadow-score`;
- `docs/transparent_shadow_score.md`;
- `docs/assets/transparent_shadow_score_card.svg`;
- `docs/release_notes/v1_6_2_alpha.md`;
- tests for score output, forbidden-field refusal, monotonic pressure fixture, and README/ROADMAP documentation.

## What this does

`v1.6.2-alpha` reads role-stripped feature files from `v1.6.1-alpha` and writes a transparent fixed-weight score.

It does not read `role_stripped_evaluation_targets.csv`. Targets are reserved for the next baseline/falsifier report.

## Boundary

This is not role-blind discovery. It does not crown, demote, or replace the current role-aware witness.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Next

`v1.6.3-alpha` should compare the transparent score against trivial baselines and separated evaluation targets. If it cannot beat simple baselines on held-out evidence, role-blind shadow is not earned.
