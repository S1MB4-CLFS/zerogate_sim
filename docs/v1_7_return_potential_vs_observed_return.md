# v1.7.1 — Return-Potential vs Observed Return

**Boundary:** controlled synthetic-field trace discipline only.

## Return-potential

```text
Gamma = D * P * R
```

`Gamma` means distinction, polarity, and relation have combined into a structural pressure that makes return possible. It is not the return gate.

A candidate may have high `Gamma` and still fail to return coherently.

## Observed return

`B` is observed return. In the current code, `B` is produced by `return_score`, which combines:

```text
zero crossing pressure
half-cycle memory
continuity
persistence
```

This means a signal that merely crosses zero is not automatically returning. Noise crosses zero. Phase resets cross zero. Collapse may approach zero. None of those earn final +1 without memory, continuity, and persistence.

## Native witness consequence

```text
C_Z = min(D, P, R, B)
```

If `B` is weak, the witness stays weak. The model is not allowed to average away the missing return gate.

## v1.7 claim consequence

Return debt belongs in `0` structured zero:

```text
D/P/R meaningful
Gamma meaningful
B incomplete
therefore: hold, do not crown
```
