# ZeroGateSim v1.3.6-alpha — CI Release-Gate Flow Repair

## Purpose

Repair the failed `v1.3.5-alpha` CI re-expansion.

`v1.3.5-alpha` attempted to make Python 3.10 / 3.11 / 3.12 all required release gates again. GitHub Actions showed that Python 3.10 and 3.11 are still red.

This release restores flow without lying:

- Python 3.12 is the required release/test gate;
- package metadata declares `requires-python >=3.12`;
- Python 3.10 / 3.11 are moved to a manual, non-blocking compatibility probe;
- the research roadmap can continue without pretending legacy-interpreter support is solved.

## Changed

- `pyproject.toml`
  - version -> `1.3.6a0`;
  - `requires-python` -> `>=3.12`;
  - classifiers return to Python 3.12 release support.
- `.github/workflows/tests.yml`
  - required release gate is Python 3.12.
- `.github/workflows/compatibility.yml`
  - manual compatibility probe for Python 3.10 / 3.11.
- `docs/runtime_ci_support.md`
  - updated support boundary and failure protocol.
- README / ROADMAP
  - update v1.3.5 as superseded failed re-expansion attempt and v1.3.6 as the active flow repair.

## Boundary

This release does not add a new logic mirror and does not change the four-gate engine.

It repairs the engineering witness layer so the next research line can continue without red CI or false runtime claims.

## Success condition

GitHub Actions required tests are green on Python 3.12.

Manual compatibility probes may still fail; they are explicitly not release gates.
