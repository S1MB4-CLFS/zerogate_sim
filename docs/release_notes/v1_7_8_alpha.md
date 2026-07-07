# v1.7.8-alpha — Repo Cleanup / Cohesion Check

`v1.7.8-alpha` inserts a cleanup/cohesion gate before reviewer packaging.

## Why this exists

The v1.7 line added the core question contract, return trace, lane taxonomy, falsifier matrix, perturbation spectrum, masked role-dependence audit, fresh holdout challenge, and anti-tautology / role-dependence check. The README had become too long and mixed current evidence, old native history, and release notes in one surface.

This version repairs that public surface.

## Main changes

- Current public line moves to `v1.7.8-alpha`.
- Reviewer package moves to `v1.7.9-alpha`.
- Core question closeout moves to `v1.7.10-alpha`.
- The README now shows a compact current route, latest holdout snapshot, and inspection paths.
- Detailed current evidence moves to `docs/current_evidence_state.md`.
- Recent native evidence history moves to `docs/recent_native_evidence_history.md`.
- Front-page routing rules move to `docs/v1_7_front_page_map.md`.
- The anti-tautology / role-dependence path is linked directly from the README.
- The bottom release-note clutter is replaced by named release-reference links.

## Boundary

This version preserves:

```text
C_Z = min(D, P, R, B)
```

It does not close the core question, start manuscript v2, upload to Zenodo, claim role-blind discovery, claim independent generator validation, or claim physics/cosmology/observed-universe proof.

## Next gate

`v1.7.9-alpha — Reviewer Start Here / Reproduction Package`.
