# ZeroGateSim Shadow Lane Discrimination

**Version:** `v1.6.12-alpha`  
**Status:** report-side candidate scoring / discrimination audit  
**Boundary:** not a detector, not role-blind discovery, not native witness mutation

## Why this exists

The hardened triad27 evidence showed a specific wound: the frozen transparent `shadow_score` could see pressure density, but it did not earn relation-, return-, demotion-, or raw-false-one-specific discrimination beyond dumb baselines.

The repair is not to retune the old score until it passes. The repair is to split the shadow surface into fixed candidate lanes and then test each lane against the relevant target.

## Native witness boundary

The native witness remains unchanged:

```text
C_Z = min(D, P, R, B)
```

The lane scores do not crown, demote, override, or replace the native witness.

## Historical score remains frozen

The original `shadow_score` remains the v1.6.2 transparent report-side score. It stays available as historical pressure evidence and as a baseline for comparison.

`v1.6.10-alpha` added legacy lane columns. `v1.6.12-alpha` adds feature-aware candidate columns and the active lane judge now reads those feature-aware columns:

```text
shadow_feature_density_residual_score
shadow_feature_raw_false_one_pressure_score
shadow_feature_demotion_pressure_score
shadow_feature_hold_or_demote_pressure_score
shadow_feature_relation_specific_pressure_score
shadow_feature_return_specific_pressure_score
shadow_feature_native_breach_proxy_score
```

These scores are fixed formulas over role-stripped engineered features. They are not learned from targets.

## Lane-to-target map

| lane | candidate score | evaluation target |
|---|---|---|
| density pressure | `shadow_feature_density_residual_score` | `target_false_pressure_density_rate` |
| raw false-one | `shadow_feature_raw_false_one_pressure_score` | `target_raw_false_one_rate` |
| demotion | `shadow_feature_demotion_pressure_score` | `target_false_one_demotion_rate` |
| hold / demote | `shadow_feature_hold_or_demote_pressure_score` | `target_hold_or_demote_rate` |
| relation-specific | `shadow_feature_relation_specific_pressure_score` | `target_relation_false_pressure_share` |
| return-specific | `shadow_feature_return_specific_pressure_score` | `target_return_false_pressure_share` |
| native breach proxy | `shadow_feature_native_breach_proxy_score` | `target_native_breach_rate` |

## What earns movement

A lane does not pass because it is higher on hard cases. It must beat the best available dumb baseline and show residual structure after that baseline explains the easy pressure.

The report state may be:

```text
expand_lane_above_baseline_with_residual_signal_not_detector
witness_lane_above_baseline_but_residual_weak
witness_lane_trivial_tie
resist_lane_under_baseline
hold_insufficient_variation
```

`expand` here still means candidate evidence only. It is not detector closeout.

## How to run

After a hardened evidence base exists and the v1.6.12 score report has been regenerated:

```powershell
$P = ".\.venv\Scripts\python.exe"
$Base = "runs\shadow_triad27_harder_v1_6_8\triad27_hardened_evidence"

& $P -m zerogate_sim.shadow_lane_discrimination_report `
  --evidence-base $Base `
  --out runs\shadow_lane_discrimination_v1_6_12_triad27
```

## Interpretation discipline

If only density expands, the system sees pressure amount but not pressure kind. That is witness, not failure. It means the next repair must improve observable features or lane formulas before deeper `deep81` / `wide243` trust.

## v1.6.12 boundary

The v1.6.12 lane judge is still a candidate audit. If relation, return, demotion, or hold/demote lanes remain under dumb baselines after the hardened triad27 rerun, shadow stays diagnostic-only and does not advance to deep81 / wide243 trust.
