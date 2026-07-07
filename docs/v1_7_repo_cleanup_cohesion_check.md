# v1.7.8-alpha — Repo Cleanup / Cohesion Check

**Version:** `v1.7.8-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`  
**Status:** documentation / cohesion gate; no new science crown.

`v1.7.8-alpha` exists because the v1.7 answer line now has enough gates, results, and process scars that the repo needs a coherent public surface before reviewer packaging.

This gate moves long lists out of the README, puts the latest holdout result on the front page in compact form, exposes the anti-tautology path, and shifts the roadmap by one more point:

```text
v1.7.7-alpha — Anti-Tautology Audit / Role-Dependence Check
v1.7.8-alpha — Repo Cleanup / Cohesion Check
v1.7.9-alpha — Reviewer Start Here / Reproduction Package
v1.7.10-alpha — Core Question Closeout
```

## What changed conceptually

The repo now separates:

```text
front page = orientation and latest compact state
evidence state docs = detailed evidence ledger
version truth = release spine
anti-tautology docs = audit mechanism and input schema
reviewer package = next version, not this one
```

## Required front-page links

- [`current_evidence_state.md`](current_evidence_state.md)
- [`v1_7_latest_holdout_snapshot.md`](v1_7_latest_holdout_snapshot.md)
- [`v1_7_anti_tautology_role_dependence_check.md`](v1_7_anti_tautology_role_dependence_check.md)
- [`v1_7_anti_tautology_known_routine.md`](v1_7_anti_tautology_known_routine.md)
- [`v1_7_post_holdout_audit_schema.md`](v1_7_post_holdout_audit_schema.md)
- [`recent_native_evidence_history.md`](recent_native_evidence_history.md)
- [`version_truth.md`](version_truth.md)

## Boundary

This gate does not:

- close the core question;
- start manuscript v2;
- claim role-blind discovery;
- claim independent generator validation;
- claim physics, cosmology, or observed-universe proof;
- mutate native math.

It makes the repo coherent enough for `v1.7.9-alpha` to package reviewer-facing reproduction logic without asking readers to decode a release-history haystack with a flashlight and a prayer.
