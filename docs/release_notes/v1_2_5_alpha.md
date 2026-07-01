# ZeroGateSim v1.2.5-alpha Release Note

## Purpose

Roadmap repair and surgical scope recovery after the premature v1.2.4 Power-Up / Fail harness.

This release removes the overbuilt acceptance-reporting module from the active package and restores the active line to native math fidelity followed by known-logic comparison.

## Changed

- Updated package version to `1.2.5a0`.
- Updated `__version__` to `1.2.5-alpha`.
- Removed the `zerogate-power-check` console script.
- Removed `src/zerogate_sim/power_check.py` from the active package.
- Removed `tests/test_power_check.py` from the active test suite.
- Rewrote `ROADMAP.md` around the real build sequence:
  - native math;
  - code fidelity;
  - invariant tests;
  - formal logic mirrors;
  - stronger experiments;
  - observed-universe bridge only after those survive.
- Updated `README.md` to remove active Power-Up / Fail instructions.
- Added `docs/simulation_win_conditions.md` as documentation-only acceptance criteria.
- Added `docs/local_tooling_repair.md` for the broken-pip editable-install failure.
- Marked v1.2.4 as superseded, not as a current architecture direction.

## Boundary

This release does not add a new gate, does not add known-logic comparison, does not solve role-blind false-one detection, and does not claim physical dimensional genesis.

## Operating sentence

Native math first. Formal mirrors second. Stronger reality bridge later.
