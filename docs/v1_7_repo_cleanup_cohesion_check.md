# v1.7.8-alpha — Repo Cleanup / Cohesion Check

**Version:** `v1.7.8-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`  
**Status:** documentation / cohesion gate; no new science crown.

`v1.7.8-alpha` exists because the v1.7 answer line now has enough gates, results, and process scars that the repo needs a coherent public surface before reviewer packaging.

This gate does three things:

```text
restore the math spine
preserve the newest 27/81/243 evidence as visual cards
keep every detailed markdown path visible without turning the README into a ledger wall
```

It also fixes the human reading order: readers should meet the theory and witness mechanism before they see the latest test cards.

## Current route shift

```text
v1.7.7-alpha — Anti-Tautology Audit / Role-Dependence Check
v1.7.8-alpha — Repo Cleanup / Cohesion Check
v1.7.9-alpha — Reviewer Start Here / Reproduction Package
v1.7.10-alpha — Core Question Closeout
```

## README flow locked here

```text
identity
-> how to read this README
-> why this exists
-> core theory
-> first visual spine
-> native math witness
-> how it works
-> current route
-> latest evidence snapshot visual cards
-> inspection map
-> quickstart / reviewers / boundary / lineage
```

Latest evidence cards belong on the front page, but not before the reader knows what they are looking at.

## Linked homes kept in sight

- [`current_evidence_state.md`](current_evidence_state.md)
- [`v1_7_latest_holdout_snapshot.md`](v1_7_latest_holdout_snapshot.md)
- [`v1_7_holdout_weather_ladder.md`](v1_7_holdout_weather_ladder.md)
- [`v1_7_holdout_output_structure.md`](v1_7_holdout_output_structure.md)
- [`v1_7_anti_tautology_role_dependence_check.md`](v1_7_anti_tautology_role_dependence_check.md)
- [`v1_7_anti_tautology_known_routine.md`](v1_7_anti_tautology_known_routine.md)
- [`v1_7_post_holdout_audit_schema.md`](v1_7_post_holdout_audit_schema.md)
- [`recent_native_evidence_history.md`](recent_native_evidence_history.md)
- [`version_truth.md`](version_truth.md)

## README math preservation repair

A cohesion cleanup is allowed to move long ledgers into dedicated docs. It is not allowed to remove the math witness from the README. The native math block is part of the project's public identity and review trace:

```text
E0, T3, Li, Gamma, CZ, chi_raw, chi_earned
```

The latest holdout result should be displayed as visual cards, with a compact text read below it. Tables may exist in machine-readable reports, but the front page should not reduce the witness result to spreadsheet posture.

## Line-ending note

SVG evidence cards are text assets and should stay LF-normalized. The repo attributes include an SVG rule so future card commits do not produce LF/CRLF warning noise.

## Boundary

This gate does not:

- close the core question;
- start manuscript v2;
- claim role-blind discovery;
- claim independent generator validation;
- claim physics, cosmology, or observed-universe proof;
- mutate native math.

It makes the repo coherent enough for `v1.7.9-alpha` to package reviewer-facing reproduction logic without asking readers to decode a release-history haystack with a flashlight and a prayer.
