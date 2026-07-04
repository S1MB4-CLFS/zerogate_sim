# v1.6.0-alpha — Role-Blind Shadow Design

`v1.6.0-alpha` starts the role-blind shadow line as a design checkpoint.

## Added

- `docs/role_blind_shadow_design.md`;
- `docs/role_blind_shadow_schema.json`;
- `docs/assets/role_blind_shadow_design_card.svg`;
- README and ROADMAP pointers;
- text tests for role-blind boundary, schema, and native witness preservation.

## Design boundary

The shadow is report-only. It may read observable behavior and derived pressure metrics, but it must not read designed truth-role labels such as `trap`, `expresser`, `latent/probe`, `truth_role`, `role_label`, or `candidate_profile` as a shortcut.

## Native math boundary

No native gate changed. No engine changed. The coherence witness remains:

```text
C_Z = min(D, P, R, B)
```

The role-aware witness remains the current final-output floor. Role-blind shadow may only become useful after role-stripped reports beat trivial baselines.

## Falsifier

If a future role-stripped shadow report cannot separate known false-pressure-heavy cases from clean earned-one cases better than random, raw-strength-only, weakest-gate-only, and relation-gate-only baselines, the shadow is not earned.
