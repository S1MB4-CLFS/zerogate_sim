# ZeroGateSim v1.3.2-alpha Release Note

## Purpose

Add the paraconsistent conflict-locality mirror.

This release continues the `v1.3-alpha` known-logic mirror line. It follows fuzzy / many-valued scoring and Belnap evidence-state projection with a narrower conflict-locality witness.

## Added

- `src/zerogate_sim/paraconsistent_mirror.py`
- `tests/test_paraconsistent_mirror.py`
- `docs/paraconsistent_mirror.md`
- matrix outputs:
  - `matrix_paraconsistent_mirror_summary.csv`
  - `matrix_paraconsistent_mirror_read.md`

## Core rule

```text
raw +1 plus debt must not explode into arbitrary final +1
```

## Boundary

This is a projection mirror only.

ZeroGateSim is not Priest logic and not a complete paraconsistent logic system. The mirror reads conflict-locality pressure after the native final-output witness. It does not change the four-gate engine and does not authorize final +1.

## Success condition

A matrix run can report local conflict pressure without crowning it or letting it inflate the whole run into a stronger claim.

## Next

`v1.3.3-alpha` should add the Kleene / Lukasiewicz compression and loss mirror.
