# v1.8.2-alpha — Failure-Capable Development Evaluation

v1.8.2 executed the locked development-only data, pre-label freeze, exact join,
duplicate audit, evaluator-failure canaries, and nested threshold-selection
path. The evaluator correctly returned
`INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR`.

## Development result

- decision: `INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR`;
- progression authorized: `false`;
- selected option: `null`;
- exact reason:
  `no valid locked threshold option; piecewise_hysteresis_v1:INVALID_DEAD_SAFE_NO_CROWNS`;
- 144 raw and 144 effective unique cases across four lineages;
- 12 expresser, 12 latent, and 12 trap cases per lineage;
- exact joins and zero observable duplicates;
- all six failure-capability fixtures passed;
- no holdout material accessed.

The primary scorer emitted 144 unique values from
`0.029125411853012872` through `0.8196793296679462`, but the maximum in
`piecewise_hysteresis_v1` was only `0.58779880167953524`. That lineage therefore
had no crowns at the locked `.8`, `.7`, or `.6` crown boundaries.

## Correctly unexecuted analysis

No valid nested selection existed, so scientific threshold selection,
uncertainty, baseline comparisons, and frozen/retuned ablation comparisons did
not execute. Their machine artifacts retain `NOT_EXECUTED_INVALID_INPUT` rather
than presenting partial analysis as a pass.

## Boundary

Scientific authority remains `v1.7.11-alpha`, `0 / HOLD`.
`READY_FOR_V1_8_3_CONTRACT_ONLY` was not earned, so v1.8.3 and v1.8.4 do not
execute. The next action requires a new preregistered repair version and a new
untouched development set; threshold retuning on the revealed v1.8.2 labels is
forbidden.

Canonical evidence is local under `runs/v1_8_2_development_evaluation/` and is
ignored by Git. See
[`../v1_8_2_failure_capable_development_evaluation.md`](../v1_8_2_failure_capable_development_evaluation.md)
for the retained hashes and full interpretation.
