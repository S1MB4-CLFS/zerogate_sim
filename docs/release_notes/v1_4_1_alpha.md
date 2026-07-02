# ZeroGateSim v1.4.1-alpha — Stronger Run Comparison Preset

## Purpose

Make stronger cross-logic comparison runs repeatable without turning the preset itself into evidence.

## Added

- `src/zerogate_sim/comparison_preset.py`
- `tests/test_comparison_preset.py`
- `docs/cross_logic_comparison_presets.md`
- console script: `zerogate-cross-logic-preset`

## Generated local outputs

The preset writer creates:

```text
comparison_preset_read.md
comparison_preset_manifest.csv
run_preset.ps1
```

These outputs are local planning artifacts and should not be committed.

## Presets

- `quick_smoke` — command wiring check.
- `adversary_triad27` — small three-wound adversary comparison.
- `wide_adversary_probe` — heavier wide243 adversary probe.

## Claim boundary

This release does not run a new proof harness automatically. It does not mutate the native gate and does not claim stronger proof by itself.

A preset is a route. Only completed matrix outputs and the cross-logic report are evidence.
