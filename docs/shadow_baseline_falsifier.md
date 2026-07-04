# Shadow Baseline/Falsifier Report

**Version:** `v1.6.3-alpha`  
**Status:** baseline comparison / falsifier gate / no role-blind discovery  
**Line:** role-blind shadow support after `v1.6.2-alpha` transparent scoring

## Purpose

`v1.6.3-alpha` adds the first baseline/falsifier report for the role-blind shadow line.

The report reads:

```text
role_stripped_profile_features.csv
role_stripped_family_features.csv
shadow_score_profile_scores.csv
shadow_score_family_scores.csv
role_stripped_evaluation_targets.csv
```

The important ordering is:

```text
role-stripped features -> transparent scores -> separated targets -> baseline comparison
```

The target file is loaded only after scoring has already happened. It is not a score input.

## Native boundary

No native gate changes. No new crown rule. No demotion authority. No replacement of the role-aware witness.

The native coherence witness remains:

```text
C_Z = min(D, P, R, B)
```

This is not role-blind discovery. It is not a detector closeout. It is an evaluation report asking whether the transparent shadow score ranks known false-one-like pressure better than simple role-stripped baselines.

## Primary target

The primary evaluation target is:

```text
target_raw_false_one_rate
```

Secondary target columns may be carried through the comparison output for audit:

```text
target_false_one_demotion_rate
target_final_false_crown_rate
target_relation_false_pressure_share
```

These are evaluation fields, not scoring features.

## Baselines

The report always includes:

```text
shadow_score
random_deterministic
```

It also includes any baseline whose source feature is present:

| baseline | feature field |
|---|---|
| `raw_pressure_only` | `feature_raw_pressure_rate` |
| `earned_rate_only` | `feature_earned_rate` |
| `latent_hold_only` | `feature_latent_hold_rate` |
| `relation_debt_only` | `feature_relation_debt_rate` |
| `mirror_primary_only` | `feature_mirror_primary_rate` |
| `mirror_secondary_only` | `feature_mirror_secondary_rate` |
| `ablation_raw_as_final_only` | `feature_ablation_raw_as_final_crown_risk_rate` |
| `demotion_dependence_only` | `feature_ablation_demotion_dependence_rate` |
| `latent_hold_dependence_only` | `feature_ablation_latent_hold_dependence_rate` |
| `echo_independence_dependence_only` | `feature_ablation_echo_independence_rate` |
| `raw_strength_only` | `feature_raw_strength_pressure_rate` |
| `weakest_gate_only` | `feature_weakest_gate_pressure_rate` |
| `relation_gate_only` | `feature_relation_gate_rate` |

The v1.6.0 design names random, raw-strength-only, weakest-gate-only, and relation-gate-only as minimum baselines. This report does not fake missing baselines. If exact fields are absent from the current role-stripped feature schema, the metrics file records the gap and the result stays in witness.

## Metrics

For each model and scope, the report writes:

```text
pairwise_order_accuracy
spearman_rank_correlation
top_bucket_target_lift
mean_target_top_bucket
mean_target_all
```

The primary falsifier metric is `pairwise_order_accuracy`: among row pairs with different target values, does the model rank the higher false-pressure row higher?

## Falsifier decision

The report can return several states:

```text
resist_shadow_not_better_than_available_baselines
witness_shadow_beats_available_baselines_exact_minimum_incomplete
expand_shadow_beats_exact_baselines_not_detector
witness_insufficient_target_variation
witness_no_available_baselines
```

The strongest `expand` state still does not mean role-blind discovery. It only means the report survived this baseline comparison. Holdout remains separate.

## Command

Example using the `v1.6.1-alpha` and `v1.6.2-alpha` local reports:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_baseline_falsifier_report `
  --profile-features runs\role_stripped_feature_report_v1_6_1\role_stripped_profile_features.csv `
  --family-features runs\role_stripped_feature_report_v1_6_1\role_stripped_family_features.csv `
  --profile-scores runs\shadow_score_report_v1_6_2\shadow_score_profile_scores.csv `
  --family-scores runs\shadow_score_report_v1_6_2\shadow_score_family_scores.csv `
  --evaluation-targets runs\role_stripped_feature_report_v1_6_1\role_stripped_evaluation_targets.csv `
  --out runs\shadow_baseline_falsifier_report_v1_6_3
```

## Outputs

```text
shadow_baseline_profile_comparison.csv
shadow_baseline_family_comparison.csv
shadow_baseline_model_metrics.csv
shadow_baseline_falsifier_read.md
shadow_baseline_falsifier_metrics.json
shadow_baseline_falsifier_audit.json
shadow_baseline_falsifier_bundle.zip
```

## Next gate

`v1.6.4-alpha` repairs the four-gate / first-alpha claim lane before holdout. `v1.6.5-alpha` adds a held-out `deep81` / `wide243` role-stripped evaluation. If exact gate baseline fields are absent, the result must stay in witness instead of pretending the missing baselines exist.

## v1.6.7 weather-hardening note

`v1.6.7-alpha` does not change the baseline/falsifier principle. It extends the later weather-hardening judge so target comparison can evaluate multiple separated target fields, not only `target_raw_false_one_rate`.

The rule remains unchanged: target fields are evaluation-only and must not appear in feature or score inputs.
