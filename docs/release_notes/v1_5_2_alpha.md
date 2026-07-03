# v1.5.2-alpha — Witness Ablation Report

## Purpose

Add a post-hoc witness ablation report for completed four-gate matrix outputs.

This begins mechanism-necessity testing without pretending the simulator has already solved full rerun-style ablation or role-blind discovery.

## Delivered

- `src/zerogate_sim/witness_ablation_report.py`
- `tests/test_witness_ablation_report.py`
- `docs/witness_ablation_report.md`
- console script: `zerogate-witness-ablation`
- report outputs:
  - `witness_ablation_summary.csv`
  - `witness_ablation_gate_summary.csv`
  - `witness_ablation_read.md`
  - `witness_ablation_bundle.zip`

## Ablation variants

- `control` — recorded native final witness.
- `raw_as_final` — every raw expression pressure event becomes final +1.
- `no_false_one_demotion` — trap raw expression is allowed to crown.
- `no_latent_hold` — latent/probe overcrown is promoted.
- `no_echo_independence` — relation/echo debt is promoted.

## Boundary

This is an accounting ablation over completed controlled synthetic-field outputs. It does not mutate the native gate law, rerun the simulator with altered mechanics, solve role-blind detection, or claim physical dimensional genesis.

The native law remains:

```text
C_Z = min(D, P, R, B)
```

Raw expression remains pressure. Earned-one remains final +1.

## Success condition

The report must expose whether disabling a witness accounting layer would promote hidden pressure or false-one crowns. If removing a layer has no effect across stronger fields, that layer remains unsupported until stronger rerun-style ablation is designed.
