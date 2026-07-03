# ZeroGateSim Threshold Sensitivity Report

**Line:** `v1.5.1-alpha`  
**Status:** controlled synthetic-field sensitivity reader

The threshold sensitivity report compares completed seed-block four-gate reports across threshold variants.

It does not prove cosmology, physical dimensional genesis, or that reality itself is trinary. It asks a narrower question:

> Does the four-gate earned-one witness remain bounded when gate and/or strength thresholds move inside a controlled band?

## Why this exists

A single passing seed-block report is useful, but it can still be brittle. If a small threshold movement creates final false-one crowns, the witness is not yet robust enough for stronger claims.

The threshold report turns that concern into a repeatable artifact.

## Input shape

The report reads one or more completed `seed_block_four_gate_report` directories. Each directory must contain:

```text
seed_block_four_gate_summary.csv
seed_block_four_gate_mirror_summary.csv
seed_block_four_gate_read.md
```

Use variant labels to identify each threshold condition:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.threshold_sensitivity `
  --variant gate_050=runs\seed_block_gate_050 `
  --variant gate_055=runs\seed_block_gate_055 `
  --variant gate_060=runs\seed_block_gate_060 `
  --out runs\threshold_sensitivity_report
```

## Output files

```text
threshold_sensitivity_summary.csv
threshold_sensitivity_gate_summary.csv
threshold_sensitivity_mirror_summary.csv
threshold_sensitivity_read.md
threshold_sensitivity_bundle.zip
```

## How to read it

The key indicators are:

- `final_false_one_crowns` — any nonzero value is a breach;
- `mirror_safety_breach_total` — any nonzero value requires inspection;
- earned-one range across variants;
- raw false-one pressure range across variants;
- gate-specific sensitivity, especially return pressure and relation/return debt.

## Boundary

A clean threshold sweep strengthens the controlled synthetic-field result only inside the tested threshold band. It does not remove the need for ablation, role-blind shadow design, independent generator families, or external comparison.
