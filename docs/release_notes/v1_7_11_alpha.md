# v1.7.11-alpha — Evidence Integrity Correction

`v1.7.11-alpha` reopens the v1.7 core question at `0 / HOLD`.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Why

`v1.7.10-alpha` remains reproducible history, but its closeout is superseded as
construction-bound:

- the final earned-one path branches on truth role;
- the old anti-tautology audit trusted summary declarations instead of proving a
  role-free scoring path;
- triad27, deep81, and wide243 were pooled even though they are nested views.

## Changes

- Adds the v1.7.11 atomic evidence-integrity audit and CLI.
- Records source hashes, canonical atomic cases, payload conflicts, rung overlap,
  explicit denominators, rates, and nested-safe totals.
- Locks authority to five exact candidate corpora, the 27/81/243 scenario grids,
  and seeds 18-26 under a recorded contract ID and SHA-256.
- Recomputes final summaries from typed gate rows and rejects mismatches.
- Includes replayable canonical identities and normalized gate payloads with
  root-relative source identifiers.
- Makes legacy rung summaries fail closed on provenance claims.
- Prevents duplicate matrix artifacts from inflating rung summaries.
- Replaces the active static closeout with an integrity-artifact-driven HOLD.
- Makes a failed or noncanonical integrity audit return a nonzero CLI status and
  prevents it from issuing unique-union counts.
- Marks the historical anti-tautology reader as having no current claim authority.
- Adds Protocol v3 and repository-local Codex operating instructions.

## Corrected evidence state

```text
naive nested opportunities = 375,921 (invalid pooled evidence)
unique atomic union         = 260,253
duplicate representations  = 115,668
current answer              = 0 / HOLD
```

## Boundary

- No native math mutation.
- No role-free scorer yet.
- No scientific threshold selection.
- No manuscript v2 promotion.
- No DTA transfer or integration.
- No Zenodo, commit, tag, push, or release authority is implied by this note.

## Next

`v1.8.0-alpha — Observable Schema and Label Firewall`.
