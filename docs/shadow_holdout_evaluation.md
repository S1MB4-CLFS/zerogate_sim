# Shadow Holdout Evaluation

**Version:** `v1.6.5-alpha`  
**Status:** held-out role-stripped evaluation gate  
**Native witness:** `C_Z = min(D, P, R, B)`

## Purpose

`v1.6.5-alpha` adds the evaluator for declared held-out `deep81` / `wide243` role-stripped evidence. After the v1.6.6/v1.6.7 corrections, the intended evidence order is triad27 preflight first, weather hardening second, then deeper `deep81` / `wide243` holdout only if the hardened judge does not reduce the shadow to a trivial baseline tie.

This is not role-blind discovery. It is not a detector closeout. It does not crown, demote, or replace the current role-aware witness.

The rule is still:

```text
role-stripped features -> transparent score -> target comparison after scoring -> holdout decision
```

## What this report reads

The report reads already-written holdout files:

```text
role_stripped_profile_features.csv
role_stripped_family_features.csv
shadow_score_profile_scores.csv
shadow_score_family_scores.csv
role_stripped_evaluation_targets.csv
```

Feature and score inputs must not contain designed role labels, answer keys, or evaluation target fields. The target table is used only after the scores already exist.

## Holdout source guard

By default the report requires declared held-out `deep81` and `wide243` sources. It checks `source_label` and `source_profile` values and refuses to call the comparison a holdout if the required sources are missing.

This does not independently prove the runs were never seen before. It does enforce a visible operator declaration and prevents accidental single-source or mislabeled score comparison.

## Family-id leakage repair

`v1.6.5-alpha` also hardens the role-stripped feature extractor. Family IDs are now deterministic opaque hashes over observable non-role fields, not ordinal values such as `family_001`.

This preserves feature/target joins while reducing the row-order/gate-family shortcut risk before holdout evaluation.

The family IDs do not use:

```text
gate
candidate_profile
truth_role
role_label
answer_key
ordinal row number
```

## Metrics

The holdout report uses the same primary ranking metrics as the baseline/falsifier gate:

```text
pairwise_order_accuracy
spearman_rank_correlation
top_bucket_target_lift
mean_target_top_bucket
mean_target_all
```

The original primary target remains:

```text
target_raw_false_one_rate
```

The weather hardening report added in v1.6.7 also evaluates expanded target variety before this holdout is treated as stronger evidence.

## Decision language

Possible holdout states include:

```text
resist_holdout_shadow_not_better_than_available_baselines
witness_holdout_shadow_beats_available_baselines_exact_minimum_incomplete
expand_holdout_shadow_beats_exact_baselines_not_detector
witness_holdout_insufficient_target_variation
witness_holdout_no_available_baselines
```

Even the strongest state says only that the score survived this holdout comparison. It still does not mean role-blind false-one detection has been solved.

## Command

Example after generating held-out role-stripped features and scores:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_holdout_evaluation_report `
  --profile-features runs\role_stripped_feature_report_v1_6_5_holdout\role_stripped_profile_features.csv `
  --family-features runs\role_stripped_feature_report_v1_6_5_holdout\role_stripped_family_features.csv `
  --profile-scores runs\shadow_score_report_v1_6_5_holdout\shadow_score_profile_scores.csv `
  --family-scores runs\shadow_score_report_v1_6_5_holdout\shadow_score_family_scores.csv `
  --evaluation-targets runs\role_stripped_feature_report_v1_6_5_holdout\role_stripped_evaluation_targets.csv `
  --required-source deep81 `
  --required-source wide243 `
  --training-metrics runs\shadow_baseline_falsifier_report_v1_6_3\shadow_baseline_falsifier_metrics.json `
  --out runs\shadow_holdout_evaluation_v1_6_5
```

## Outputs

```text
shadow_holdout_profile_comparison.csv
shadow_holdout_family_comparison.csv
shadow_holdout_model_metrics.csv
shadow_holdout_evaluation_read.md
shadow_holdout_evaluation_metrics.json
shadow_holdout_evaluation_audit.json
shadow_holdout_evaluation_bundle.zip
```

## Handoff rule

After local tests and this report are green, build the assistant test handoff under `runs/` and include the holdout read, metrics JSON, audit JSON, and bundle. The handoff ZIP is local continuation evidence, not Git truth.

## Next gate

`v1.6.7-alpha` adds shadow weather hardening before this deeper holdout is trusted. If the hardened report says the shadow is trivial against available baselines, the next work is discrimination repair, not larger weather.
