# ZeroGateSim Seed-Block Four-Gate Report

**Introduced:** `v1.5.0-alpha`  
**Status:** stronger controlled synthetic-field evidence reader

The seed-block four-gate report reads completed matrix runs for the native gate adversary set:

```text
distinction
polarity
relation
return
```

It is a report reader. It does not run a new proof harness by itself, mutate the native gate law, or claim physical dimensional genesis.

## Purpose

The report answers one bounded question:

> Across completed distinction, polarity, relation, and return adversary matrix runs, does the final witness continue to separate earned-one from raw expression pressure, latent pressure, relation/return debt, and false-one pressure without final false-one crowns?

The report belongs after `v1.4.4-alpha`, which aligned adversary presets with the full native four-gate cycle.

## Command

After a completed four-gate adversary preset exists, run:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.seed_block_report `
  --preset-dir runs\cross_logic_presets\adversary_triad27 `
  --out runs\seed_block_four_gate_report
```

Equivalent console script:

```powershell
zerogate-seed-block-report --preset-dir runs\cross_logic_presets\adversary_triad27 --out runs\seed_block_four_gate_report
```

## Outputs

```text
seed_block_four_gate_summary.csv
seed_block_four_gate_mirror_summary.csv
seed_block_four_gate_read.md
seed_block_report_bundle.zip
```

The summary table contains one row per native gate block. The mirror table aggregates known-logic mirror pressure across the four completed matrix runs.

## Readiness criteria

A strong pass requires:

- all four native gate adversary blocks are present;
- raw false-one pressure remains visible when it occurs;
- latent pressure and relation/return debt remain visible when they occur;
- final false-one crowns remain zero;
- mirror safety breach total remains zero;
- evidence files are preserved in one reviewable bundle.

A breach is any final false-one crown or mirror safety breach. A quiet run is not a breach, but it is weaker evidence than a pressure-visible run.

## Boundary

This report supports stronger controlled synthetic-field testing. It does not prove cosmology, physical dimensional genesis, role-blind discovery, or equivalence with any external logic system.
