# Shadow Discrimination Repair

**Version:** `v1.6.9-alpha`  
**Status:** report-side discrimination audit; no score retuning; not role-blind discovery

## Why this exists

The hardened `triad27` evidence showed the first honest wound in the shadow line: the frozen transparent shadow score could detect pressure density, but simple baselines still beat or tied it on the main false-one targets.

That is not a native witness failure. The native four-gate witness still holds:

```text
C_Z = min(D, P, R, B)
```

The wound belongs to the shadow inference layer:

```text
shadow sees pressure
≠
shadow discriminates false-one kind beyond dumb baselines
```

## What v1.6.9 adds

`v1.6.9-alpha` adds `zerogate-shadow-discrimination`, a report that reads `weather_hardening_baseline_comparison.csv` and asks what remains after the best available baseline already explains the easy part.

It writes:

```text
shadow_discrimination_target_metrics.csv
shadow_discrimination_residual_metrics.csv
shadow_discrimination_lane_summary.csv
shadow_discrimination_decision.json
shadow_discrimination_audit.json
shadow_discrimination_read.md
shadow_discrimination_bundle.zip
```

## Residual rule

For each target, scope, and rung, the report finds the best available non-shadow baseline and computes:

```text
residual_target = z(target) - z(best_available_baseline_score)
```

Then it asks whether the frozen shadow score has signal against that residual. This is the difference between:

```text
being right because raw pressure was obvious
```

and:

```text
seeing structure that raw pressure, raw strength, relation-only, return-only, or mirror-only baselines did not already explain
```

## Lanes

Targets are grouped into pressure lanes:

```text
density_pressure
raw_false_one
demotion
hold_or_demote
relation_specific
return_specific
native_breach_proxy
```

A global result can therefore say the precise wound, for example:

```text
witness_shadow_density_only_specific_discrimination_not_earned
```

That means the score sees pressure density, but has not yet earned relation/return/demotion-specific false-one discrimination.

## Command shape

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.shadow_discrimination_report `
  --hardening-comparison runs\shadow_triad27_harder_v1_6_8\triad27_hardened_evidence\weather_hardening\weather_hardening_baseline_comparison.csv `
  --out runs\shadow_discrimination_v1_6_9_triad27
```

A directory may also be supplied if it contains `weather_hardening_baseline_comparison.csv`:

```powershell
& $P -m zerogate_sim.shadow_discrimination_report `
  --hardening-comparison runs\shadow_triad27_harder_v1_6_8\triad27_hardened_evidence\weather_hardening `
  --out runs\shadow_discrimination_v1_6_9_triad27
```

## Boundary

This report does not retune the score, does not crown or demote candidates, does not mutate native math, and is not role-blind discovery.

If the result remains density-only or under-baseline, the next work is feature/score discrimination design, not `deep81` / `wide243` trust.
