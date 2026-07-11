# v1.8.2-alpha — Failure-Capable Development Evaluation

**Decision:** `INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR`

**Progression authorized:** `false`

**Selected threshold option:** `null`

**Scientific authority:** `v1.7.11-alpha`, `0 / HOLD`

## Result first

The v1.8.2 development evaluator worked as designed and refused to select a
scientific threshold. Its exact reason is:

```text
no valid locked threshold option; piecewise_hysteresis_v1:INVALID_DEAD_SAFE_NO_CROWNS
```

The primary prior-touch scorer produced 144 distinct scores across the 144
effective development cases, spanning
`0.029125411853012872` through `0.8196793296679462`. It was therefore not a
globally constant scorer. The failure was lineage-specific: the maximum primary
score in `piecewise_hysteresis_v1` was `0.58779880167953524`. That lineage
produced zero crowns under every preregistered crown boundary:

```text
wide_hold    crown >= 0.8
medium_hold  crown >= 0.7
narrow_hold  crown >= 0.6
```

Each option consequently became dead-safe for that complete lineage. The
nested selector had no valid locked option and stopped before full threshold
selection. `READY_FOR_V1_8_3_CONTRACT_ONLY` was not earned.

## Development material and joins

The corpus is explicitly **class-conditioned controlled synthetic** development
material. It is not label-free source data, independent empirical data, or an
unseen-family holdout.

The executed data contract contained:

- four generator lineages: `ar_recovery_v1`, `impulse_response_v1`,
  `coupled_oscillator_v1`, and `piecewise_hysteresis_v1`;
- 12 cases for each of `expresser`, `latent`, and `trap` in every lineage;
- 144 raw cases and 144 effective cases;
- 144 unique blind IDs and 144 unique atomic case IDs;
- exact prediction-to-vault joins;
- zero exact observable duplicates and zero cross-lineage overlap.

Labels and generator groups were read only after the observable source,
development fingerprint, pre-label artifacts, retained hashes, and evaluator
package were verified. No v1.8.3 or later holdout material was accessed.

## Failure capability

All six locked evaluator fixtures passed:

1. balanced operable fixture;
2. one injected trap crown detected exactly;
3. always-HOLD rejected;
4. always-CROWN rejected;
5. always-RESIST rejected;
6. constant primary score rejected.

This establishes evaluator operability and explains why the real dead-safe
lineage could not be hidden. It does not turn the invalid development result
into scientific support.

## What did not execute

Because valid nested threshold selection was impossible:

- the selected option remained `null`;
- out-of-fold and full-development scientific selection did not execute;
- primary-versus-baseline comparisons did not execute;
- frozen and retuned ablation comparisons did not execute;
- lineage-cluster uncertainty did not execute.

Those artifacts correctly record `NOT_EXECUTED_INVALID_INPUT`. They must not be
described as missing report polish or silently replaced with partial metrics.

## Retained local evidence

The canonical evidence remains local under
`runs/v1_8_2_development_evaluation/`. The `runs/` tree is ignored and is not
repository truth by itself. The retained SHA-256 values are:

| artifact | SHA-256 |
|---|---|
| development split receipt | `c9dc6890d6ae9a1a865c8d433878a79536bd8ae7357db257c0f06482df8bf461` |
| observable source | `bcc3cad731a8fac78cb256fd9c15d24161df7c50c6c24a8f173471dacbc8d59c` |
| extraction source manifest | `1cb70ba191328bc2aca97906fb7247cd2e42408acf6b21cd7cdeef6e697fe782` |
| development fingerprint | `571f3f2ce1a9b777957eea0a6854d23bc56dc339a1fff578138d860bd6a506cf` |
| pre-label receipt | `9c77254645e7cbc814e01ff62e07ac0cff478e35ea64278881030457dc890daf` |
| evaluator package contract | `5f3cd3a086cc42c5f2f06804b4f9d9bff6d35dbfefc7cb06016c6a8ff8d7a82b` |
| development result | `27a934de013f56f47b3f929d781c7c6fe1e461bb50b0007cf45685fe19e28866` |
| evaluation manifest | `54fac47bd6ef598545ba9528acce19993d23895f10252982df6021852ce3eaf2` |
| evaluation receipt | `00935943039930113e732ea8f794adce0087458f2fc94d234285b089c440a205` |

These hashes establish local artifact identity. They are not external timestamp
proof and do not independently establish the unrestricted history of the data.

## Scientific and workflow boundary

The current scientific authority remains the v1.7.11 evidence-integrity
correction at `0 / HOLD`. v1.8.2 selected no threshold and authorizes no
v1.8.3 holdout contract, v1.8.4 label join, manuscript v2 prose, DTA transfer,
tag, release, Zenodo upload, or external sharing.

The next scientific action must be a separately preregistered repair version
using a new untouched development set. It may investigate why the frozen
prior-touch scorer and `piecewise_hysteresis_v1` do not support crowns, but it
must not retune the three locked thresholds against the already revealed
v1.8.2 labels. The failed development set remains evidence about the mechanism.
