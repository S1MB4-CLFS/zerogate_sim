# v1.6.5-alpha — Shadow Holdout Evaluation

## Status

Held-out role-stripped evaluation gate for the role-blind shadow line. No native math change. No role-blind discovery claim.

## Delivered

- `src/zerogate_sim/shadow_holdout_evaluation_report.py`;
- console script `zerogate-shadow-holdout-evaluation`;
- `docs/shadow_holdout_evaluation.md`;
- `docs/release_notes/v1_6_5_alpha.md`;
- tests for holdout source coverage, score-before-target boundary, forbidden-field refusal, output files, and documentation boundaries;
- role-stripped family-id hardening so feature/target family joins use opaque non-sequential IDs instead of ordinal `family_001` style shortcuts.

## What this does

`v1.6.5-alpha` evaluates already-written transparent shadow scores on declared held-out `deep81` / `wide243` role-stripped evidence.

It preserves the order:

```text
role-stripped features
transparent score
holdout target comparison after scoring
```

It does not tune the score, crown candidates, demote candidates, or replace the current witness.

## Boundary

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

A passing holdout result can support only:

```text
the shadow score survived this held-out role-stripped comparison
```

It cannot support:

```text
role-blind false-one detection is solved
```

## Next

`v1.6.6-alpha` may close the v1.6 shadow line with a visual/report closeout only if the holdout report, local tests, and CI are green. If holdout resists, the shadow line stays in HOLD.
