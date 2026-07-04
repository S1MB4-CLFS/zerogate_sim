# Role-Stripped Feature Extraction

**Version:** `v1.6.1-alpha`  
**Status:** report reader / feature extraction / no role-blind verdict  
**Line:** role-blind shadow support after `v1.6.0-alpha` design

## Purpose

`v1.6.1-alpha` adds a small report reader that extracts role-stripped feature tables from completed controlled synthetic-field evidence reports.

The goal is not to score candidates yet. The goal is cleaner separation:

```text
role-stripped feature files -> future shadow scorer -> evaluation targets checked after scoring
```

The feature files must not contain designed truth-role shortcut fields such as `candidate_profile`, `truth_role`, `role_label`, `trap`, `expresser`, `latent_probe`, `designed_truth_role`, or `answer_key`.

## Native boundary

No native gate changes. No new crown rule. No replacement of the role-aware witness.

The native coherence witness remains:

```text
C_Z = min(D, P, R, B)
```

`v1.6.1-alpha` only prepares feature tables for later role-blind shadow tests.

## Command

Example using the fresh controlled `deep81` and `wide243` evidence folders kept locally:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.role_stripped_feature_report `
  --seed-summary deep81=runs\controlled_deep81_four_gate_v1_5_4\reports\seed_block_four_gate_report\seed_block_four_gate_summary.csv `
  --ablation-summary deep81=runs\controlled_deep81_four_gate_v1_5_4\reports\witness_ablation_report\witness_ablation_summary.csv `
  --seed-summary wide243=runs\controlled_wide243_four_gate_v1_5_4\reports\seed_block_four_gate_report\seed_block_four_gate_summary.csv `
  --ablation-summary wide243=runs\controlled_wide243_four_gate_v1_5_4\reports\witness_ablation_report\witness_ablation_summary.csv `
  --out runs\role_stripped_feature_report_v1_6_1
```

## Outputs

The report writes:

```text
role_stripped_profile_features.csv
role_stripped_family_features.csv
role_stripped_evaluation_targets.csv
role_stripped_feature_read.md
role_stripped_forbidden_field_audit.json
role_stripped_feature_bundle.zip
```

The first two are role-stripped feature inputs. The evaluation target file is deliberately separate and must not be loaded by a future role-blind scorer.

## v1.6.5 family-id hardening

`v1.6.5-alpha` keeps this extractor compatible but hardens the family-level join surface. Family IDs are now deterministic opaque hashes over observable non-role fields, not ordinal labels such as `family_001`.

The ID is allowed to preserve feature/target joins. It must not encode `gate`, `candidate_profile`, `truth_role`, `role_label`, `answer_key`, or simple row order.

## Feature witness math

For each source or opaque family row, the report extracts rate features such as:

```text
X_raw = raw_expression_pressure / N_runs
X_L = latent_overcrown_pressure / N_runs
X_M = mirror_primary_pressure / N_runs
X_D = relation_debt_count / N_runs
```

When witness-ablation summaries are supplied, source-level ablation pressure is also read:

```text
X_A = final_false_crowns(raw_as_final) / N_runs
X_H = promoted_latent_pressure(no_latent_hold) / N_runs
```

These are not new native gates. They are report-side features prepared for later falsifier tests.

## Falsifier discipline

A later role-blind shadow score must be produced from the feature files first. Only after that may it be compared against `role_stripped_evaluation_targets.csv`.

If a shadow score cannot beat random, raw-pressure-only, weakest-gate-only, and relation-gate-only baselines on held-out controlled synthetic-field evidence, it is not earned.

## v1.6.7 target hardening

`v1.6.7-alpha` keeps the feature files role-stripped but expands the separate evaluation target file so later weather hardening can judge more than one easy target.

The expanded target surface includes:

```text
target_raw_false_one_rate
target_false_one_demotion_rate
target_final_false_crown_rate
target_relation_false_pressure_share
target_false_pressure_density_rate
target_hold_or_demote_rate
target_return_false_pressure_share
target_native_breach_rate
```

These target fields are evaluation-only. They must never appear in role-stripped feature files or score files.
