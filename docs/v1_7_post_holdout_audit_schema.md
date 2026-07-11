# v1.7.7-alpha — Post-Holdout Audit Schema

> **Historical schema:** self-declared masking, manifest, reference, control, or pass fields are not proof under `v1.7.11-alpha`. Current evidence integrity must be recomputed from source artifacts and hashes.

**Version:** `v1.7.7-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

The `zerogate-v1-7-anti-tautology-role-audit` CLI may be run with one or more holdout summary CSV files:

```powershell
& $P -m zerogate_sim.v1_7_anti_tautology_role_dependence_check `
  --holdout-summary-csv runs\...\v1_7_6_holdout_triad27_row.csv `
  --holdout-summary-csv runs\...\v1_7_6_holdout_deep81_row.csv `
  --holdout-summary-csv runs\...\v1_7_6_holdout_wide243_row.csv `
  --out runs\v1_7_7_anti_tautology_role_dependence_check
```

## Required row columns

```text
weather_rung
fresh_seed_block
candidate_names_masked
expected_manifest_frozen
reference_profile_reused
earned_controls_present
lane_pattern_matches_expected
final_earned_one_events
raw_expression_pressure
latent_overcrown
relation_debt
return_debt
false_one_pressure
final_false_one_crowns
```

Optional stronger leakage columns:

```text
role_labels_masked
role_leakage_score
label_only_lane_assignment
```

## Output files

```text
v1_7_anti_tautology_role_dependence_check_read.md
v1_7_anti_tautology_role_dependence_check_decision.json
v1_7_anti_tautology_known_routine.csv
v1_7_anti_tautology_audit_conditions.csv
v1_7_role_dependence_post_holdout_checks.csv
v1_7_anti_tautology_role_dependence_input_schema.csv
v1_7_anti_tautology_role_dependence_evaluation.csv
v1_7_anti_tautology_role_dependence_audit.json
v1_7_anti_tautology_role_dependence_check_bundle.zip
```

## Decision grammar

```text
expand_audit_passed_not_tautological_role_bounded
witness_audit_passed_with_latent_hold_no_role_blind_claim
hold_audit_weather_ladder_incomplete
hold_audit_role_dependence_or_tautology_pressure
resist_audit_false_crown_stop
resist_audit_post_hoc_manifest
resist_audit_label_or_name_leakage
resist_audit_dead_safe_or_missing_positive_control
resist_audit_reference_profile_reused
```

Any `resist_*` decision blocks reviewer packaging until repaired.
