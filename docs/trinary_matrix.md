# Trinary Matrix Witness

The trinary matrix runner is the first wider combination pressure test for ZeroGateSim.

It is intentionally not a decimal checklist. It uses trinary axes: minus, zero, plus.

## Triad profile: 3^3 = 27 scenarios

The default matrix varies three pressure axes:

- noise pressure: calmer field, baseline field, noisy field
- relation pressure: weaker binding, baseline binding, stronger binding
- expression pressure: stable-freedom dip, baseline strength, stable-freedom boost

With 9 seeds per scenario, the default run creates 27 x 9 = 243 toy runs.

## Deep profile: 3^4 = 81 scenarios

The deep profile adds perturbation pressure:

- calm late field
- mild late shock
- rough late shock

With 9 seeds per scenario, deep mode creates 81 x 9 = 729 toy runs.

Use deep mode only after the triad profile has been reviewed. The primate does not get to order a banquet before checking if the chair has legs.

## Outputs

The runner writes:

- `matrix_summary.md`
- `matrix_seed_summary.csv`
- `matrix_scenario_summary.csv`
- `matrix_axis_summary.csv`
- `matrix_candidate_summary.csv`
- `matrix_bundle.zip`

Upload `matrix_bundle.zip` for review.

## Claim boundary

This matrix does not prove physics. It asks whether the current zero-gate expression rule survives structured trinary pressure variation.
