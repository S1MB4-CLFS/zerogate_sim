# v1.7.7-alpha — Anti-Tautology Audit / Role-Dependence Check

`v1.7.7-alpha` adds the post-holdout audit gate before reviewer / reproduction packaging.

## Purpose

After `v1.7.6-alpha` fresh holdout runs, the project must check whether the result is non-tautological, non-vacuous, non-dead-safe, and not carried by role/name leakage before it is packaged for reviewers.

## Adds

```text
docs/v1_7_anti_tautology_role_dependence_check.md
docs/v1_7_anti_tautology_known_routine.md
docs/v1_7_post_holdout_audit_schema.md
src/zerogate_sim/v1_7_anti_tautology_role_dependence_check.py
tests/test_v1_7_anti_tautology_role_dependence_check.py
zerogate-v1-7-anti-tautology-role-audit
```

## Preserves

```text
C_Z = min(D, P, R, B)
```

No native math mutation. no role-blind discovery claim. No observed-universe bridge. No manuscript v2. No core question closeout.

## Next gate

`v1.7.8-alpha — Reviewer Start Here / Reproduction Package`.

The old reviewer package step moved up one point because the audit must happen first. `v1.7.9-alpha` becomes the Core Question Closeout gate.
