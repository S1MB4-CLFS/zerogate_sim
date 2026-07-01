# ZeroGateSim v1.3.0-alpha — Fuzzy Mirror Foundation

## Purpose

Begin the known-logic mirror line without claiming identity with any external logic system.

This release adds the first formal projection mirror: fuzzy / many-valued scoring comparison.

## Added

- `src/zerogate_sim/fuzzy_mirror.py`
- `tests/test_fuzzy_mirror.py`
- `docs/known_logic_boundary.md`
- `docs/fuzzy_mirror.md`
- matrix integration for fuzzy mirror outputs

## Matrix outputs

Matrix runs now include:

```text
matrix_fuzzy_mirror_trace.csv
matrix_fuzzy_mirror_candidate_summary.csv
matrix_fuzzy_mirror_read.md
```

These outputs compare native weakest-gate coherence against product, average, and Lukasiewicz-style conjunction mirrors.

## Claim boundary

This release does not claim ZeroGateSim is fuzzy logic.

It claims only:

> ZeroGateSim can compare its native weakest-gate coherence against fuzzy / many-valued scoring mirrors and report where softer or stricter aggregations preserve, distort, or hide native gate wounds.

## Key diagnostic

`average_overcrown_pressure` identifies cases where the average gate would pass threshold while the native weakest gate does not.

This protects the native rule:

```text
C_Z = min(D, P, R, B)
```

## Not included

- no Belnap mirror yet;
- no paraconsistent mirror yet;
- no Kleene / Lukasiewicz compression mirror yet;
- no role-blind false-one detector;
- no new core gate.

## Test posture

Expected local gate:

```powershell
python -m pytest tests\test_fuzzy_mirror.py -q
python -m pytest tests\test_native_math_invariants.py tests\test_fuzzy_mirror.py -q
python -m pytest -q
```
