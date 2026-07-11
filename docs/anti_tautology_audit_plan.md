# Anti-Tautology Audit Plan

> **Historical plan:** preserved to show the original audit design. v1.7.11
> found that this audit did not execute a role-free scorer and therefore did not
> detect the construction-bound final path.

**Target version:** `v1.6.25-alpha`  
**Created:** `v1.6.24-alpha`

At v1.6.24 the evidence line looked promising, and the next gate was meant to ask the hard question:

> Did the Four Gates witness derive structured zero/debt states from gate and return dynamics, or did the reports mostly count labels we designed into the candidate profile?

## Audit principle

A result is stronger when the output state is earned by witness dynamics.
A result is weaker when the output state is mainly a role/profile label wearing evidence clothing.

## Required checks

`v1.6.25-alpha` should inspect:

1. **Role dependence** — which outputs depend on explicit `candidate_profile`, role labels, or family names?
2. **Witness dependence** — which outputs depend on `D`, `P`, `R`, `B`, return depth, lineage, echo independence, relation debt, or return debt diagnostics?
3. **Masked evaluation** — what remains if labels are masked and only numeric witness diagnostics are considered?
4. **Ablation contrast** — do raw, binary, dead-safe, no-relation, no-return, and average-gate witnesses still fail for the right reasons?
5. **Debt specificity** — are relation debt and return debt different states, or only two names for generic hold pressure?

## Possible outcomes

```text
+1 earned audit:
  Debt states are witness-derived enough to support synthetic zero-zone gating language.

0 bounded audit:
  Debt states are represented and reproduced, but too role-shaped for stronger language.

-1 demoted audit:
  Debt states are mostly label-counting or tautological; core claim must shrink.
```

## Boundary

This audit does not mutate native witness math.
Native witness remains:

```text
C_Z = min(D, P, R, B)
```

No Zenodo route, no observed-universe bridge, no shadow revival.
