# Four Gates fresh-seed debt reproduction

**Version:** `v1.6.22-alpha`  
**Status:** fresh-seed reproduction report gate  
**Native witness:** `C_Z = min(D, P, R, B)`

This gate asks whether the repaired Four Gates debt pattern from `v1.6.20-alpha` and `v1.6.21-alpha` reproduces on fresh seeds.

It does not start Zenodo correction, revive the shadow route, open the observed-universe bridge, or claim physical proof.

## Purpose

`v1.6.21-alpha` showed that relation debt and return debt remained visible under deeper weather on the first seed range.

`v1.6.22-alpha` adds the reproduction judge that compares:

```text
reference evidence: seed range 0-8
fresh evidence:     seed range 9-17
```

The comparison is qualitative, not exact-count worship. A fresh run earns expansion only if it preserves the same state structure:

```text
+1 earned-one remains visible
 0 latent overcrown remains visible
 0 relation debt remains visible
 0 return debt remains visible
-1 false-one pressure remains visible and demoted
final false-one crowns remain 0
ablation enemies remain wounded
```

## Required inputs

The report consumes two completed `v1.6.21`-style evidence directories:

```text
four_gates_deepwide_debt_evidence_decision.json
four_gates_deepwide_debt_rung_summary.csv
four_gates_deepwide_state_lanes.csv
```

Both inputs must contain:

```text
deep81
wide243
```

and both must preserve:

```text
C_Z = min(D, P, R, B)
```

## Decisions

Possible global decisions:

```text
expand_four_gates_fresh_seed_debt_reproduction
witness_four_gates_fresh_seed_debt_partial
hold_four_gates_fresh_seed_debt_incomplete
resist_four_gates_fresh_seed_debt_breach
```

A passing reproduction is still controlled synthetic-field evidence only.

It does not prove physical dimensional genesis, quantum gravity, an observed-universe bridge, or that reality itself uses the Four Gates operator.

## Command shape

```powershell
python -m zerogate_sim.four_gates_fresh_seed_debt_reproduction_report `
  --reference-evidence-dir runs\four_gates_deepwide_debt_v1_6_21\four_gates_deepwide_debt_evidence `
  --fresh-evidence-dir runs\four_gates_fresh_seed_debt_v1_6_22\four_gates_deepwide_debt_evidence `
  --reference-label seed-range-0-8 `
  --fresh-label fresh-seed-range-9-17 `
  --out runs\four_gates_fresh_seed_reproduction_v1_6_22
```

## Boundary

No Zenodo route yet.  
No shadow revival.  
No observed-universe bridge.  
No spacetime metric claim.  
No mutation of the native witness.
