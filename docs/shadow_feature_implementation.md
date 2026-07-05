# ZeroGateSim Shadow Feature Implementation

**Version:** `v1.6.12-alpha`  
**Status:** observable feature implementation, not detector closeout  
**Boundary:** no role labels, no target leakage, no native witness mutation

## Why this exists

`v1.6.11-alpha` repaired the route and named the shadow wound:

```text
native four-gate witness: standing
shadow density pressure: candidate signal
shadow relation / return / demotion specificity: not earned
```

`v1.6.12-alpha` implements the next allowed step: observable, role-stripped feature columns that try to expose pressure kind instead of pressure amount.

This version does **not** claim those features succeed. It only makes them available for the next hardened triad27 rerun.

## Native witness boundary

The native witness remains unchanged:

```text
C_Z = min(D, P, R, B)
```

The new feature columns do not crown, demote, or alter the simulator witness. They are report-side shadow candidates only.

## Implemented feature families

The new engineered feature columns are computed before targets are loaded:

| column | intended pressure kind |
|---|---|
| `feature_density_residual_proxy_rate` | raw pressure remaining after raw-strength pressure |
| `feature_relation_ownership_gap_rate` | relation pressure not matched by earned expression |
| `feature_relation_echo_pressure_rate` | relation debt / echo-dependence pressure |
| `feature_relation_return_divergence_rate` | relation and return disagreeing |
| `feature_return_integrity_gap_rate` | return weakness relative to relation / weakest-gate pressure |
| `feature_return_strength_mismatch_rate` | raw strength not matched by return coherence |
| `feature_return_memory_pressure_rate` | return-limiting and zero-hold pressure without earned expression |
| `feature_demotion_trajectory_proxy_rate` | observable refusal-pressure trajectory |
| `feature_zero_hold_ambiguity_proxy_rate` | structured zero / not-yet pressure |
| `feature_gate_imbalance_rate` | spread across observable gate-pressure fields |
| `feature_pressure_kind_contrast_rate` | pressure-shape contrast normalized by raw pressure |

## Feature-aware candidate scores

`shadow_score_report.py` still preserves the historical `shadow_score` and the `v1.6.10` lane split. `v1.6.12-alpha` adds feature-aware candidate score columns:

```text
shadow_feature_density_residual_score
shadow_feature_raw_false_one_pressure_score
shadow_feature_demotion_pressure_score
shadow_feature_hold_or_demote_pressure_score
shadow_feature_relation_specific_pressure_score
shadow_feature_return_specific_pressure_score
shadow_feature_native_breach_proxy_score
```

These are fixed, transparent candidate formulas. They are not learned, not target-tuned, and not role-blind discovery.

## Forbidden shortcuts

The feature implementation must not use:

```text
truth_role
role_label
trap / expresser / latent-probe labels
candidate_profile as a classification shortcut
evaluation target fields
family row order
post-score outcomes
```

## Next gate

`v1.6.13-alpha` must rerun hardened triad27 using the new feature-aware score columns.

Pass condition:

```text
at least one specific lane beats the best dumb baseline with residual signal
```

Stop condition:

```text
relation / return / demotion lanes remain under raw-pressure or raw-strength baselines
```

If the stop condition holds after this feature implementation, shadow remains diagnostic-only and should not advance to deep81 / wide243 trust.
