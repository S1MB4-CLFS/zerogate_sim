# Four Gates Debt Candidate Generator

**Version:** `v1.6.19-alpha`  
**Status:** generator implementation gate  
**Boundary:** no Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim

## Purpose

`v1.6.19-alpha` implements the debt-shaped candidate profile designed in `v1.6.18-alpha`.

The goal is not to run heavy proof yet. The goal is to create near-success candidates that can make structured zero visible:

```text
not earned
not false
not random
not safe to crown
wrong to demote
structured enough to hold
```

The active candidate profile is:

```text
four_gates_debt
```

Matrix runs can call it with:

```powershell
& $P -m zerogate_sim.matrix --profile triad27 --candidate-profile four_gates_debt --start-seed 0 --count 9 --steps 240 --out runs\...
```

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Candidate lanes

The generator includes controls and debt candidates:

| lane | role |
|---|---|
| `+1 earned-one` | earned controls prove the witness is not dead-safe |
| `-1 false-one demotion` | trap controls prove false pressure still demotes |
| `0 relation debt` | relation is meaningful but incomplete, unstable, borrowed, or global-only |
| `0 return debt` | return occurs but returns altered, weakened, or closure-incomplete |
| `0 latent overcrown` | perturbation-survival candidates may deserve hold instead of crown/demotion |

## Candidate families

Implemented debt families:

- `relation_debt_local`;
- `return_debt_local`;
- `relation_debt_global_a` / `relation_debt_global_b`;
- `closure_gap_candidate`;
- `dual_return_gap_candidate`;
- `perturbation_survival_candidate`.

Implemented controls:

- `earned_return_control`;
- `false_one_trap_control`.

## Evidence boundary

This version only makes the generator available and writes a small preview report. The preview is a sanity check, not evidence that debt lanes passed.

`v1.6.20-alpha` is the first actual evidence gate: four-corpus `triad27` debt evidence with ablation comparison and positive zero-state visibility.
