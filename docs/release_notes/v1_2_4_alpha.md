# ZeroGateSim v1.2.4-alpha Release Note

## Purpose

Add the first Power-Up / Fail witness harness for existing matrix/proof output directories.

This release does not mutate the four-gate engine and does not claim external logic validation. It reads existing matrix artifacts and reports whether a run is merely producing files or has reached a stronger witness posture inside the current toy-field domain.

## Added

- `src/zerogate_sim/power_check.py`
- `tests/test_power_check.py`
- `zerogate-power-check` console script
- README quickstart instructions for power-check runs
- ROADMAP update marking v1.2.4 as the conservative artifact-reader floor

## Outputs

When run against a matrix directory, the power-check writes:

- `matrix_power_check_summary.csv`
- `matrix_power_check_fail_summary.csv`
- `matrix_power_check_read.md`

## Power ladder

- `POWER 0` — runs
- `POWER 1` — witness artifacts present
- `POWER 2` — discriminator
- `POWER 3` — predictive-zero-ready
- `POWER 4` — role-blind shadow
- `POWER 5` — holy-shit detector

`POWER 4` and `POWER 5` are expected to remain HOLD until future role-blind shadow and later-pressure confirmation artifacts exist.

## Boundary

The holy-shit detector is not a large run count. It is only reached when the simulator refuses or holds a tempting candidate before collapse is obvious, names the wound, and later fresh pressure confirms that refusal.

For v1.2.4, the correct achievement is more modest: a matrix can now report where it sits on the power/fail ladder without pretending that future gates already exist.
