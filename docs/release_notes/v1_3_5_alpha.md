# ZeroGateSim v1.3.5-alpha — CI Compatibility Re-expansion

## Purpose

Repair the temporary runtime support narrowing from the v1.3.3 CI boundary.

The project should not leave Python 3.10 / 3.11 behind as vague future debt. This release deliberately re-expands interpreter support and lets GitHub Actions witness the declared range again.

## Changed

- `pyproject.toml`
  - version -> `1.3.5a0`;
  - `requires-python` -> `>=3.10`;
  - classifiers include Python 3.10 / 3.11 / 3.12;
  - dependency bounds added below future major versions.
- `.github/workflows/tests.yml`
  - restores matrix: Python 3.10 / 3.11 / 3.12;
  - keeps an explicit import check before pytest.
- `docs/runtime_ci_support.md`
  - documents runtime support and failure protocol.
- README / ROADMAP
  - removes the stale 3.12-only HOLD posture and states the active support target.

## Boundary

This release does not add a new logic mirror and does not change the four-gate engine.

It repairs the engineering witness layer so future known-logic and stronger-experiment work is not held back by unresolved interpreter support.

## Success condition

GitHub Actions is green on Python 3.10, 3.11, and 3.12.

If any lane fails, stop feature work and repair that exact lane before advancing.
