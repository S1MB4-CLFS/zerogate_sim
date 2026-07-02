# ZeroGateSim v1.3.3-alpha Release Note

## Purpose

Add the Kleene / Lukasiewicz compression and loss mirror.

This is the fourth known-logic mirror in the v1.3 line:

```text
fuzzy scoring -> Belnap evidence -> paraconsistent locality -> three-valued compression/loss
```

## Added

- `src/zerogate_sim/three_valued_mirror.py`
- `tests/test_three_valued_mirror.py`
- `docs/three_valued_mirror.md`
- matrix output integration:
  - `matrix_three_valued_mirror_summary.csv`
  - `matrix_three_valued_mirror_read.md`

## CI support repair

This release also repairs the GitHub Actions support boundary. The active CI matrix is narrowed to Python 3.12 only because the v1.3.x GitHub emails showed failing pytest jobs on Python 3.10 / 3.11 while local and 3.12 gates were green.

This is not a claim that older Python versions can never work. It is a release-truth decision: do not claim support for interpreters that are not passing.

The workflow now runs tests with explicit `PYTHONPATH=src`, matching the local-source test pattern used in Marek's patch workflow.

## Boundary

This release does not claim that ZeroGateSim is Kleene logic or Lukasiewicz logic.

It performs a value-level compression only:

```text
+1 -> true
0 -> unknown
-1 -> false
```

The loss report is the point. Native ZeroGate zero grammar is richer than this mirror can preserve.

## What to inspect

After a matrix smoke run, read:

```text
matrix_three_valued_mirror_read.md
```

Look for:

- true / unknown / false counts;
- zero-compression loss candidates;
- native final bands that were collapsed into unknown.

## Status

Surgical known-logic mirror. No gate mutation. No cosmology claim.
