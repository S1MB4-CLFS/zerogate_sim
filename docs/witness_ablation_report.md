# Witness Ablation Report

`v1.5.2-alpha` adds a post-hoc witness ablation report for completed four-gate matrix outputs.

## Claim boundary

This report does **not** prove cosmology, physical dimensional genesis, or that reality itself is trinary. It also does not rerun the simulator with altered mechanics.

It reads completed controlled synthetic-field matrix outputs and asks a narrower question:

> Which final witness layers are doing visible work when their accounting function is disabled?

The native gate law remains unchanged:

```text
C_Z = min(D, P, R, B)
```

Raw expression remains pressure. Earned-one remains final +1.

## Why this exists

The v1.5.0 seed-block report showed whether four-gate adversary pressure stays visible without final false-one crowns. The v1.5.1 threshold sensitivity report asks whether that posture is brittle under threshold movement.

The next scientific question is mechanism necessity:

> Does the witness stack matter, or is it decorative?

`v1.5.2-alpha` begins that question conservatively. It does not yet run expensive rerun-style ablations. It first performs a post-hoc accounting ablation over completed final-output summaries.

If removing a witness layer would promote trap pressure, latent overcrown, or relation/echo debt into final +1, that layer is doing visible work.

If removing a layer has no effect across stronger fields, that layer is not yet supported and must be redesigned or demoted.

## Built-in ablation variants

The report currently reads these variants:

| variant | meaning |
|---|---|
| `control` | Native final witness as recorded by the matrix final-output summaries. |
| `raw_as_final` | Removes the final witness: every raw expression pressure event is treated as final +1. |
| `no_false_one_demotion` | Removes the false-one demotion layer: trap raw expression is allowed to crown. |
| `no_latent_hold` | Removes latent/probe zero-hold: latent overcrown pressure is promoted as final +1. |
| `no_echo_independence` | Removes echo/relation-debt witness: relation-dependent expression is promoted as final +1. |

These are accounting ablations, not ontology claims.

## Usage

From the repository root:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
$env:PYTHONPATH = (Join-Path (Get-Location) "src")

& $P -m zerogate_sim.witness_ablation_report `
  --preset-dir runs\cross_logic_presets\adversary_triad27 `
  --out runs\witness_ablation_report_v1_5_2
```

The same report can be built from explicit matrix directories:

```powershell
& $P -m zerogate_sim.witness_ablation_report `
  --matrix-dir runs\cross_logic_presets\adversary_triad27\distinction_triad27 `
  --matrix-dir runs\cross_logic_presets\adversary_triad27\polarity_triad27 `
  --matrix-dir runs\cross_logic_presets\adversary_triad27\relation_triad27 `
  --matrix-dir runs\cross_logic_presets\adversary_triad27\return_triad27 `
  --out runs\witness_ablation_report_v1_5_2
```

## Outputs

The report writes:

```text
witness_ablation_summary.csv
witness_ablation_gate_summary.csv
witness_ablation_read.md
witness_ablation_bundle.zip
```

The Markdown readout gives:

- control final false-one crowns;
- maximum final false-one crowns under ablation;
- maximum pressure hidden by ablation;
- variant summary;
- gate summary;
- ablation definitions;
- interpretation boundary.

## How to read the result

Good evidence does not mean all ablations stay clean.

A useful ablation result may look like this:

```text
control final false-one crowns = 0
raw_as_final final false-one crowns > 0
no_false_one_demotion final false-one crowns > 0
```

That is not a failure of the control. It is evidence that the final witness layer is doing work.

A weaker but still useful result:

```text
control keeps relation debt visible
no_echo_independence promotes relation debt into earned-one accounting
```

That means the echo/relation-debt witness is doing accounting work, even if no trap crown appears.

## Boundary before future ablation work

This report is the first ablation layer. It is intentionally conservative.

Future rerun-style ablations may disable or weaken mechanics before final output is written, such as:

- removing observed return from `C_Z`;
- replacing weakest-gate `min` with average;
- weakening return-depth;
- weakening lineage;
- weakening echo-independence;
- removing role witness and replacing it with observable-only shadow metrics.

Those future ablations are stronger, but they should not be coded until the report layer is able to show exactly what changed.

## Public language

Allowed:

> The witness ablation report shows which final witness accounting layers prevent raw pressure, trap pressure, latent overcrown, or relation debt from being promoted into final +1.

Forbidden:

> The ablation report proves the universe uses ZeroGateSim.

Also forbidden:

> Post-hoc ablation is the same as role-blind discovery.

Role-blind detection remains future work.
