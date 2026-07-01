# ZeroGateSim v1.2.5-alpha Release Note

## Purpose

Restore surgical scope after a premature acceptance-reporting layer was added too early.

This release keeps the native math witness line and removes code that turned informal future validation language into active package machinery before the test design existed.

## Removed

- `src/zerogate_sim/power_check.py`
- `tests/test_power_check.py`
- `zerogate-power-check` console script
- the v1.2.4 release note for the premature acceptance-report layer

## Added

- `docs/simulation_win_conditions.md`

## Changed

- README now describes v1.2.5 as scope restoration and links to release-safe simulation win conditions.
- ROADMAP now marks the premature artifact-reader layer as held/superseded and keeps future validation as design work, not code.
- Package version moved to `1.2.5a0`.

## Boundary

This release does not mutate the four-gate engine. It does not add a new witness layer. It does not claim role-blind detection. It does not claim external logic validation.

The useful idea is preserved as acceptance criteria:

> A future stronger result would be a witness refusal that is later confirmed by fresh pressure.

That remains future work.
