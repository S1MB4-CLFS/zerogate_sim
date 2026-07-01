# ZeroGateSim v1.2.4-alpha Release Note

## Status

Superseded by `v1.2.5-alpha`.

## What happened

v1.2.4 added a Power-Up / Fail witness harness:

- `src/zerogate_sim/power_check.py`
- `tests/test_power_check.py`
- `zerogate-power-check` console script

The module read existing matrix/proof artifacts and reported a power/fail ladder. The intent was to translate the operator question “power up or fail?” into a report.

## Why it was superseded

The idea was useful, but implementation was too early. It turned future validation language into active package machinery before the native math / known-logic comparison line was ready.

The correct posture is documentation first:

- define simulation win/fail criteria;
- keep the engine unchanged;
- compare native math against known formal mirrors only after the native math line is stable.

## Boundary

v1.2.4 should be treated as a visible scar in the release history, not as the active architecture direction.

v1.2.5 removes the module and preserves the useful idea only as release-safe documentation.
