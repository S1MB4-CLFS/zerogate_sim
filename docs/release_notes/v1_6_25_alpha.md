# v1.6.25-alpha — Anti-Tautology Audit / Role-Dependence Check

`v1.6.25-alpha` adds the anti-tautology audit tool for the current Four Gates debt evidence line.

## Added

- `zerogate-four-gates-anti-tautology-audit`
- `src/zerogate_sim/four_gates_anti_tautology_audit_report.py`
- `docs/anti_tautology_audit_report.md`
- `tests/test_four_gates_anti_tautology_audit_report.py`

## What it checks

The audit asks whether relation/return debt states are only role labels or whether they are computed by the witness outputs.

It reports:

- role/profile/kind dependence;
- witness-count dependence;
- masked numeric pattern visibility;
- debt specificity between relation debt and return debt.

## Expected boundary

A passing audit may still be a bounded `0` result:

```text
witness_bounded_role_shaped_but_witness_computed
```

That means the current evidence is valid as designed controlled synthetic-field evidence, but it is not independent role-blind discovery.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

No Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim.
