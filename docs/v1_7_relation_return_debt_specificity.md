# v1.7.2-alpha — Relation Debt vs Return Debt Specificity

**Version:** `v1.7.2-alpha`  
**Status:** lane boundary lock  
**Native witness:** `C_Z = min(D, P, R, B)`

## Why this exists

`v1.7.1-alpha` separated return-potential from observed return. `v1.7.2-alpha` now uses that distinction to keep relation debt and return debt from collapsing into one polite non-crown bucket.

## Relation debt

Relation debt asks:

> Does the candidate own the relation enough to deserve one?

Relation debt is about binding and ownership. It includes incomplete, unstable, borrowed, under-owned, or global-only relation.

Typical surfaces:

```text
relation_debt_local
relation_debt_global_a
relation_debt_global_b
echo / relation-dependence bands when applicable
```

## Return debt

Return debt asks:

> Did the candidate return with preserved structure?

Return debt is about `Gamma` being meaningful while observed `B`, memory, closure, continuity, or return-depth remains incomplete.

Typical surfaces:

```text
return_debt_local
closure_gap_candidate
dual_return_gap_candidate
perturbation_survival_candidate
return_debt_dpr_hold
return_debt_near_expression
return_gap_quarantine
```

## Boundary

```text
relation debt = binding/ownership wound
return debt   = observed-return / closure / depth wound
```

Both are `0` structured zero. Neither is final `+1`. Neither is generic failure.

## Stop condition

If a future report cannot say whether the wound is relation ownership or return completion, the lane taxonomy is not ready for baseline claims.
