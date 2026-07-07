# v1.7.4-alpha — Perturbation Spectrum Witness

`v1.7.4-alpha` locks the perturbation spectrum witness required by the v1.7 core question.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

This version adds the spectrum-under-perturbation contract:

```text
raw pressure may move;
final witness must fail safely;
+1 when earned;
0 when unresolved;
-1 when false;
final false-one crowns must remain zero for any later +1 closeout candidate.
```

## What changed

- Adds `docs/v1_7_witness_spectrum.md`.
- Adds `docs/v1_7_perturbation_curve.md`.
- Adds `docs/v1_7_weather_curve_summary.md`.
- Adds `docs/v1_7_expected_quiet_lane_activation.md`.
- Adds `zerogate-v1-7-perturbation-spectrum`.
- Adds `tests/test_v1_7_perturbation_spectrum.py`.

## What did not change

- No native math mutation.
- no new heavy evidence crown.
- no new heavy evidence crown.
- No manuscript v2 start.
- No role-blind discovery claim.
- No physics, topology, dimensions, cosmology, or observed-universe claim.

## Why this gate exists

`v1.7.3-alpha` named weaker witnesses and ablation enemies. `v1.7.4-alpha` names the behavior that must be visible under pressure curves before the core question can eventually close: the system must show a spectrum of lane behavior rather than a single victory count.

The next gate is `v1.7.5-alpha — Masked Role-Dependence Audit`.
