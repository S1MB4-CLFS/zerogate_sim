# Four Gates Anti-Tautology Audit / Role-Dependence Check

> **Historical / insufficient audit:** preserved as a record of v1.6.25. Its
> summary-state checks did not establish label isolation or a frozen role-free
> scorer. It has no current claim authority after v1.7.11.

**Introduced:** `v1.6.25-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

This gate asked whether the then-current Four Gates debt evidence was doing real witness work or merely re-counting labels designed into the `four_gates_debt` candidate profile.

## Why this audit exists

The evidence line looked promising at that historical gate:

```text
+1 earned-one visible
 0 relation debt visible
 0 return debt visible
-1 false-one pressure visible and demoted
final false-one crowns = 0
```

But the debt candidates are deliberately designed near-success states. That is valid for a controlled synthetic-field experiment, but it creates a tautology risk.

The audit therefore separates four questions:

1. **Role dependence** — do debt lanes depend on explicit candidate profile, candidate kind, or truth-role names?
2. **Witness dependence** — are debt lanes assigned by witness outputs such as `relation_debt_count` and `return_debt_count`?
3. **Masked numeric visibility** — if candidate labels are ignored, does the numeric pattern still show earned-one, relation debt, return debt, false-one demotion, and zero final false crowns?
4. **Debt specificity** — are relation debt and return debt distinct states, or only generic hold pressure with two names?

## Expected bounded outcome

The anticipated result was not independent role-blind discovery. The evidence used a designed `four_gates_debt` profile. At that time, a passing audit would have supported only this historical bounded claim:

> Historical v1.6.25 wording: the Four Gates witness appeared to represent and
> reproduce structured zero/debt states in designed controlled scenarios. That
> wording is not a current empirical-discrimination claim.

The stronger claim is **not** earned yet:

> The witness independently discovers debt states from unlabeled role-blind dynamics.

That stronger lane belongs after the v1.6 closeout only if a future route deliberately earns it.

## Decision states

```text
+1 expand_anti_tautology_audit_witness_derived_enough
  Debt states are witness-derived enough for stronger bounded language.

0 witness_bounded_role_shaped_but_witness_computed
  Debt states reproduce and are witness-counted, but the current evidence remains designed-profile / role-shaped.

0 hold_anti_tautology_audit_incomplete
  The audit cannot yet support a claim upgrade.

-1 resist_anti_tautology_audit_breach_or_regression
  Breach or regression blocks the route.
```

## Tool

```powershell
python -m zerogate_sim.four_gates_anti_tautology_audit_report `
  --fresh-reproduction-dir runs\four_gates_fresh_seed_reproduction_v1_6_22 `
  --fresh-evidence-dir runs\four_gates_fresh_seed_debt_v1_6_22\four_gates_deepwide_debt_evidence `
  --out runs\four_gates_anti_tautology_audit_v1_6_25
```

## Boundary

This audit does not mutate native witness math.

```text
C_Z = min(D, P, R, B)
```

No Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim.
