# v1.6.19-alpha — Four Gates debt candidate generator

`v1.6.19-alpha` implements the near-success debt candidate generator designed in `v1.6.18-alpha`.

## Added

- `four_gates_debt` candidate profile;
- `zerogate-four-gates-debt-generator` console script;
- `src/zerogate_sim/four_gates_debt_candidate_generator_report.py`;
- `docs/four_gates_debt_candidate_generator.md`;
- debt-shaped signal kinds for relation, return, closure, dual-return, perturbation-survival, and global relation holds;
- tests protecting candidate profile registration, route boundary, and no native witness mutation.

## Boundary

This version does not run the heavy evidence gate. It only makes the generator available.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

No Zenodo route, no shadow revival, no observed-universe bridge, and no spacetime metric claim.

## Next

`v1.6.20-alpha` should run four-corpus `triad27` debt evidence using the new `four_gates_debt` profile.
