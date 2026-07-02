# ZeroGateSim Known-Logic Comparison Report

**Line:** `v1.4.0-alpha`  
**Status:** cross-run projection mirror aggregation

This document describes the first v1.4 report layer.

The v1.3 line created four projection mirrors:

- fuzzy / many-valued gate-pressure mirror;
- Belnap evidence-state mirror;
- paraconsistent conflict-locality mirror;
- Kleene / Lukasiewicz compression-loss mirror.

`v1.4.0-alpha` does not add a new native gate and does not add a new proof harness. It reads completed matrix runs that already contain `matrix_known_logic_closeout_summary.csv` and aggregates their mirror-pressure results into one comparison report.

## Why this exists

A single matrix run can show one posture. A cross-logic comparison report can show whether the same mirror pressure repeats across multiple matrix runs, candidate profiles, or adversarial corpora.

This is the bridge from "the mirrors exist" to "the mirrors can be compared across stronger toy-field weather."

## Command

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.cross_logic_report `
  --matrix-dir runs\matrix_triad27_0_0_closeout_smoke `
  --matrix-dir runsnother_completed_matrix `
  --out runs\cross_logic_comparison_v1_4_0
```

The console script is also available after installation:

```powershell
zerogate-cross-logic --matrix-dir runs\matrix_a --matrix-dir runs\matrix_b --out runs\comparison
```

## Outputs

```text
cross_logic_comparison_summary.csv
cross_logic_comparison_matrix_summary.csv
cross_logic_comparison_mirror_summary.csv
cross_logic_comparison_read.md
cross_logic_report_bundle.zip
```

## Claim boundary

This report aggregates completed toy-field matrix evidence.

It does not:

- prove cosmology;
- prove physical dimensional genesis;
- prove that reality is trinary;
- claim identity with fuzzy, Belnap, paraconsistent, Kleene, or Lukasiewicz logic;
- replace native ZeroGateSim final-output witness.

It does:

- show which mirror pressures are visible across completed runs;
- report whether any mirror-level safety breach appears;
- keep each mirror's loss report visible;
- help decide which stronger toy-field experiment should be run next.

## Reading rule

A mirror is useful when it makes a native wound easier to see.

A mirror is dangerous when it hides return, lineage, independence, zero-depth, or false-one demotion and then pretends to authorize a crown.

## Operating sentence

Cross-logic comparison is an evidence organizer, not borrowed authority.
