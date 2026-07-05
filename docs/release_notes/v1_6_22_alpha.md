# v1.6.22-alpha — Four Gates fresh-seed debt reproduction

`v1.6.22-alpha` adds the fresh-seed reproduction gate for the Four Gates debt evidence line.

## Added

- `zerogate-four-gates-fresh-seed-debt-reproduction`
- `src/zerogate_sim/four_gates_fresh_seed_debt_reproduction_report.py`
- `tests/test_four_gates_fresh_seed_debt_reproduction_report.py`
- `docs/four_gates_fresh_seed_debt_reproduction.md`

## Purpose

This version compares a reference `deep81` / `wide243` debt evidence bundle against a fresh-seed reproduction bundle.

It asks whether the repaired state pattern survives new seeds:

```text
+1 earned-one
 0 latent overcrown
 0 relation debt
 0 return debt
-1 false-one pressure
0 final false-one crowns
```

## Boundary

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

No Zenodo route.  
No shadow route revival.  
No observed-universe bridge.  
No spacetime metric claim.  
No physical proof claim.

## Next gate

If fresh seeds reproduce the qualitative pattern, the next gate is `v1.6.23-alpha` evidence consolidation / runs hygiene.
