# Transparent Shadow Score Prototype

**Version:** `v1.6.2-alpha`  
**Status:** report-side score prototype / no role-blind verdict  
**Line:** role-blind shadow support after `v1.6.1-alpha` feature extraction

## Purpose

`v1.6.2-alpha` adds a transparent shadow-score report reader.

It reads the role-stripped feature files produced by `v1.6.1-alpha` and writes inspectable shadow scores. The score is not learned. It is deliberately simple so the first shadow signal can be challenged before any stronger detector exists.

Correct path:

```text
role-stripped features -> transparent score -> later baseline/falsifier comparison
```

Incorrect path:

```text
targets / role labels -> score
```

## Native boundary

No native gate changes. No new crown rule. No replacement of the role-aware witness.

The native coherence witness remains:

```text
C_Z = min(D, P, R, B)
```

`v1.6.2-alpha` is not a role-blind detector yet. It does not crown, demote, or claim discovery.

## Inputs

Allowed inputs:

```text
role_stripped_profile_features.csv
role_stripped_family_features.csv
```

Forbidden inputs:

```text
role_stripped_evaluation_targets.csv
truth_role
role_label
candidate_profile
trap / expresser / latent_probe
answer_key
```

The target file is reserved for `v1.6.3-alpha`, where the score can be compared against baselines and falsifiers after scoring has already happened.

## Score math

Each feature rate is first normalized with a saturating pressure transform:

```text
N(x) = x / (1 + x)
```

The transparent shadow score is:

```text
S_shadow = sum_j w_j N(x_j)
```

The first fixed weights are:

| feature | weight | interpretation |
|---|---:|---|
| `feature_raw_pressure_rate` | `0.14` | general raw pressure |
| `feature_latent_hold_rate` | `0.16` | latent hold dependence |
| `feature_relation_debt_rate` | `0.06` | observed relation/return debt |
| `feature_mirror_primary_rate` | `0.12` | mirror-visible primary pressure |
| `feature_mirror_secondary_rate` | `0.06` | mirror-visible secondary pressure |
| `feature_ablation_raw_as_final_crown_risk_rate` | `0.18` | raw-as-final crown risk |
| `feature_ablation_demotion_dependence_rate` | `0.18` | false-one demotion dependence |
| `feature_ablation_latent_hold_dependence_rate` | `0.08` | latent-hold dependence |
| `feature_ablation_echo_independence_rate` | `0.02` | echo/relation-debt dependence |

The weights sum to `1.0` and are written to `shadow_score_formula.json`.

## Command

Example using the `v1.6.1-alpha` role-stripped report kept locally:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_score_report `
  --profile-features runs\role_stripped_feature_report_v1_6_1\role_stripped_profile_features.csv `
  --family-features runs\role_stripped_feature_report_v1_6_1\role_stripped_family_features.csv `
  --out runs\shadow_score_report_v1_6_2
```

## Outputs

The report writes:

```text
shadow_score_profile_scores.csv
shadow_score_family_scores.csv
shadow_score_read.md
shadow_score_formula.json
shadow_score_forbidden_field_audit.json
shadow_score_bundle.zip
```

The score outputs are still report evidence, not product verdicts.

## Falsifier discipline

`v1.6.3-alpha` must compare these scores against trivial baselines and the separated target file.

If the transparent shadow score cannot beat raw-pressure-only, weakest-gate-only, random, and simple profile baselines on held-out controlled synthetic-field evidence, role-blind shadow is not earned.

## v1.6.10 lane split

The original `shadow_score` remains frozen as the v1.6.2 transparent score. `v1.6.10-alpha` adds fixed lane-specific candidate score columns to the same score CSVs:

```text
shadow_density_pressure_score
shadow_raw_false_one_pressure_score
shadow_demotion_pressure_score
shadow_hold_or_demote_pressure_score
shadow_relation_specific_pressure_score
shadow_return_specific_pressure_score
shadow_native_breach_proxy_score
```

These lane scores do not retune the historical score and do not claim detector status. They exist so `zerogate-shadow-lane-discrimination` can test whether any lane sees pressure kind beyond dumb baselines.

## v1.6.12 feature-aware candidate scores

`v1.6.12-alpha` preserves the historical `shadow_score` and the `v1.6.10` lane scores, then adds feature-aware candidate score columns built from observable engineered features:

```text
shadow_feature_density_residual_score
shadow_feature_raw_false_one_pressure_score
shadow_feature_demotion_pressure_score
shadow_feature_hold_or_demote_pressure_score
shadow_feature_relation_specific_pressure_score
shadow_feature_return_specific_pressure_score
shadow_feature_native_breach_proxy_score
```

These scores are still report-side candidates. They are not learned, not target-tuned, and not role-blind discovery. Their only purpose is to let the next hardened triad27 rerun test whether relation / return / demotion specificity improves beyond dumb baselines.
