# Shadow Weather Hardening

**Version:** `v1.6.7-alpha`  
**Status:** harder judge for triad27 / deep81 / wide243 shadow evidence  
**Native witness:** `C_Z = min(D, P, R, B)`

## Purpose

`v1.6.7-alpha` adds a hardening report for the shadow line after the actual `triad27` preflight showed the right wound: the transparent shadow score could rank the family rows, but simple baselines could rank them just as well.

This version does not tune the score. It makes the judge harder before any deeper weather result is trusted.

The weather ladder remains:

```text
triad27 = 3^3 local expression weather
deep81  = 3^4 perturbation / late-shock bridge
wide243 = 3^5 temporal-depth / time-axis stress
```

The report can read one or more evidence bases that follow the standard local run shape:

```text
<base>/seed_block/seed_block_four_gate_summary.csv
<base>/role_stripped/role_stripped_profile_features.csv
<base>/role_stripped/role_stripped_family_features.csv
<base>/role_stripped/role_stripped_evaluation_targets.csv
<base>/shadow_score/shadow_score_profile_scores.csv
<base>/shadow_score/shadow_score_family_scores.csv
```

## Claim boundary

This report is not role-blind discovery. It is not detector closeout. It does not crown or demote candidates. It does not mutate the native witness.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

The report reads already-written shadow scores and compares them with targets only after scoring. It does not retune weights after seeing the target file.

## What became harder

The report makes the shadow lane stricter in five ways:

1. It evaluates the supplied weather rungs together instead of letting separate green-looking reports hide ladder gaps.
2. It evaluates every available target field, not only `target_raw_false_one_rate`.
3. It records when the shadow score is right but trivial because a dumb baseline ties or beats it.
4. It reports native gate pressure and native breach status beside shadow diagnostics.
5. It refuses discovery language even if a local comparison looks good.

## Expanded target surface

`v1.6.7-alpha` expands the separated evaluation target file produced by role-stripped feature extraction. New targets remain evaluation-only and must not appear in feature or score inputs.

Available target surface now includes:

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

The purpose is to prevent the shadow line from pretending a single easy target proves general false-one risk understanding.

## Decision language

Possible hardening decisions include:

```text
resist_native_breach
witness_weather_ladder_incomplete
resist_shadow_under_hardened_weather
witness_shadow_trivial_under_hardened_weather
witness_shadow_not_closed_under_hardened_weather
expand_shadow_nontrivial_hardened_weather_not_detector
```

The strongest state still means only that the score survived this hardened role-stripped weather comparison. It does not mean role-blind false-one detection has been solved.

## Command

Example after an actual triad27 evidence chain has been generated under `runs\shadow_triad27_actual_v1_6_6`:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_weather_hardening_report `
  --source triad27=runs\shadow_triad27_actual_v1_6_6 `
  --required-rung triad27 `
  --out runs\shadow_weather_hardening_v1_6_7_triad27
```

Example once `deep81` and `wide243` evidence bases exist in the same standard shape:

```powershell
& $P -m zerogate_sim.shadow_weather_hardening_report `
  --source triad27=runs\shadow_triad27_actual_v1_6_6 `
  --source deep81=runs\shadow_deep81_actual_v1_6_7 `
  --source wide243=runs\shadow_wide243_actual_v1_6_7 `
  --out runs\shadow_weather_hardening_v1_6_7_full_ladder
```

## Outputs

```text
weather_hardening_baseline_comparison.csv
weather_hardening_target_diagnostics.csv
weather_hardening_native_gate_metrics.csv
weather_hardening_decision.json
weather_hardening_audit.json
weather_hardening_read.md
weather_hardening_bundle.zip
```

## Handoff rule

After local tests and this report run green, build the assistant test handoff under `runs/` and include the read, decision JSON, audit JSON, diagnostics CSV, native gate CSV, and bundle. The handoff ZIP is local continuation evidence, not Git truth.

## Next gate

Only after this hardening report shows a non-trivial result should deeper `deep81` / `wide243` shadow holdout evidence be treated as a candidate next gate. If it says the shadow is trivial, the next work is discrimination repair, not larger weather.
