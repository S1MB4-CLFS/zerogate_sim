# ZeroGateSim v1.4.4-alpha — Four-Gate Adversary Coverage Lock

## Purpose

Align adversary comparison presets with the native four-gate witness cycle.

The native gate set is:

```text
distinction
polarity
relation
return
```

## Added

- `adversary_return` candidate profile.
- `return_triad27` in the `adversary_triad27` preset.
- `return_wide243` in the `wide_adversary_probe` preset.
- Preset coverage helpers for native gate coverage.
- Tests that require four-gate adversary presets to cover every native gate.

## Boundary

This release does not change the native gate law, the final-output witness, or the known-logic mirror layer.

It repairs run-plan coverage so future adversary evidence distinguishes complete four-gate evidence from partial evidence.
