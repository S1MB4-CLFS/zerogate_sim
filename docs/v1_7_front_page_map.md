# v1.7 Front Page Map

**Introduced:** `v1.7.8-alpha`; reviewer path added in `v1.7.9-alpha`  
**Purpose:** explain what belongs on the README front page and what belongs behind links.

The README is not the evidence vault. It is the door.

## Human reading order

README should teach before it displays evidence. A cold reader should meet the project before they meet the results:

```text
identity -> core theory -> why this exists -> software mechanism -> visual spine -> native math -> current route -> latest evidence cards -> reviewer package -> inspection paths
```

The latest 27/81/243 cards are front-page material, but they must not appear before the reader understands what `earned-one`, `raw expression pressure`, relation debt, return debt, and false-one pressure mean.

## README should contain

- the current public line;
- the core question;
- a short reading order;
- why the project exists;
- the core theory;
- the native math witness spine;
- the software witness mechanism;
- the current route;
- the latest holdout visual cards;
- the anti-tautology / role-dependence inspection path;
- the markdown inspection map;
- quickstart and reviewer links;
- claim boundary.

## README should not contain

- the full recent native version ledger;
- every historical evidence table;
- long release-note blocks under the license;
- local run artifact paths;
- shadow-route history except as a history-vault link;
- speculative physics or external analogy lanes;
- latest test results before the mechanism has been explained.

## Linked homes

| subject | home |
|---|---|
| detailed current evidence state | [`current_evidence_state.md`](current_evidence_state.md) |
| latest holdout snapshot | [`v1_7_latest_holdout_snapshot.md`](v1_7_latest_holdout_snapshot.md) |
| holdout weather ladder | [`v1_7_holdout_weather_ladder.md`](v1_7_holdout_weather_ladder.md) |
| holdout output structure | [`v1_7_holdout_output_structure.md`](v1_7_holdout_output_structure.md) |
| recent native evidence history | [`recent_native_evidence_history.md`](recent_native_evidence_history.md) |
| anti-tautology audit path | [`v1_7_anti_tautology_role_dependence_check.md`](v1_7_anti_tautology_role_dependence_check.md) |
| known audit routine | [`v1_7_anti_tautology_known_routine.md`](v1_7_anti_tautology_known_routine.md) |
| post-holdout audit schema | [`v1_7_post_holdout_audit_schema.md`](v1_7_post_holdout_audit_schema.md) |
| release spine | [`version_truth.md`](version_truth.md) |
| detailed release notes | [`release_notes/`](release_notes/) |

## Rule

A future README addition should either help a cold reader enter the project or point them to the right deeper file. If it is only bookkeeping, it belongs behind a link.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Non-negotiable front-page preservation

The README must preserve the native math witness block. Cleanup may move long ledgers out of the README, but it must not strip the math spine.

The latest holdout evidence should be shown as visual cards after the mechanism has been introduced, not as an Excel-style table and not before the reader understands the witness grammar. The compact machine-readable counts can live below the card and in dedicated docs.

Required front-page visual cards:

- `docs/assets/v1_7_6_triad27_holdout_card.svg`
- `docs/assets/v1_7_6_deep81_holdout_card.svg`
- `docs/assets/v1_7_6_wide243_holdout_card.svg`
- `docs/assets/v1_7_6_holdout_total_card.svg`

## v1.7.9 reviewer path addition

The README now links `REVIEWER_START_HERE.md`, `docs/v1_7_minimal_reproduction.md`, `docs/v1_7_expected_outputs.md`, `docs/v1_7_claim_boundary_card.md`, and `docs/v1_7_evidence_manifest.md` after the current route and before the latest evidence snapshot. The route remains human-first: mechanism before results, package before closeout.
