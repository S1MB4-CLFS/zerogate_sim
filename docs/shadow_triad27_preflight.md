# Shadow Triad27 Preflight

**Version:** `v1.6.6-alpha`  
**Status:** first trinary-weather shadow evaluation rung  
**Native witness:** `C_Z = min(D, P, R, B)`

## Purpose

`v1.6.6-alpha` adds a triad27 preflight gate for the role-blind shadow line.

This exists because the shadow route should not jump straight to `deep81` / `wide243` evidence before passing through the smallest full trinary weather cube:

```text
triad27 = 3^3 local expression weather
deep81  = 3^4 perturbation / late-shock bridge
wide243 = 3^5 temporal-depth / time-axis stress
```

The preflight evaluates already-written transparent shadow scores on declared `triad27` role-stripped evidence.

It is not role-blind discovery. It is not a detector closeout. It does not crown, demote, or replace the current role-aware witness.

## Rule

The rule stays the same:

```text
role-stripped features -> transparent score -> target comparison after scoring -> triad27 preflight decision
```

Feature and score inputs must not contain designed role labels, answer keys, or target fields. The target table is used only after the scores already exist.

## Source guard

By default the report requires a source label or source profile containing:

```text
triad27
```

This does not prove the runs were never seen before. It does enforce the operator declaration that the current evaluation is the `triad27` rung and not mislabeled `deep81`, `wide243`, or mixed evidence.

## Metrics

The preflight uses the same primary ranking metrics as the baseline/falsifier and holdout reports:

```text
pairwise_order_accuracy
spearman_rank_correlation
top_bucket_target_lift
mean_target_top_bucket
mean_target_all
```

The primary target remains:

```text
target_raw_false_one_rate
```

## Decision language

Possible triad27 states include:

```text
resist_triad27_shadow_not_better_than_available_baselines
witness_triad27_shadow_beats_available_baselines_exact_minimum_incomplete
expand_triad27_shadow_beats_exact_baselines_not_detector
witness_triad27_insufficient_target_variation
witness_triad27_no_available_baselines
```

Even the strongest state says only that the transparent shadow score survived the `triad27` comparison. It still does not mean role-blind false-one detection has been solved, and it still does not mean `deep81` / `wide243` has passed.

## Command

Example after generating triad27 role-stripped features and scores:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_triad27_preflight_report `
  --profile-features runs\role_stripped_feature_report_v1_6_6_triad27\role_stripped_profile_features.csv `
  --family-features runs\role_stripped_feature_report_v1_6_6_triad27\role_stripped_family_features.csv `
  --profile-scores runs\shadow_score_report_v1_6_6_triad27\shadow_score_profile_scores.csv `
  --family-scores runs\shadow_score_report_v1_6_6_triad27\shadow_score_family_scores.csv `
  --evaluation-targets runs\role_stripped_feature_report_v1_6_6_triad27\role_stripped_evaluation_targets.csv `
  --required-source triad27 `
  --out runs\shadow_triad27_preflight_v1_6_6
```

## Outputs

```text
shadow_triad27_profile_comparison.csv
shadow_triad27_family_comparison.csv
shadow_triad27_model_metrics.csv
shadow_triad27_preflight_read.md
shadow_triad27_preflight_metrics.json
shadow_triad27_preflight_audit.json
shadow_triad27_preflight_bundle.zip
```

## Handoff rule

After local tests and this report are green, build the assistant test handoff under `runs/` and include the triad27 read, metrics JSON, audit JSON, and bundle. The handoff ZIP is local continuation evidence, not Git truth.

## Next gate

`v1.6.7-alpha` should run the deeper `deep81` / `wide243` holdout evidence only after triad27 preflight evidence, local full tests, and CI are green.
