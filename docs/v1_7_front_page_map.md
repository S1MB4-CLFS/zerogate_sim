# v1.7 Front Page Map

**Introduced:** `v1.7.8-alpha`  
**Purpose:** explain what belongs on the README front page and what belongs behind links.

The README is not the evidence vault. It is the door.

## README should contain

- the current public line;
- the core question;
- the native witness spine;
- the latest compact holdout snapshot;
- the anti-tautology / role-dependence inspection path;
- the clean current route;
- quickstart and reviewer links;
- claim boundary.

## README should not contain

- the full recent native version ledger;
- every historical evidence table;
- long release-note blocks under the license;
- local run artifact paths;
- shadow-route history except as a history-vault link;
- speculative physics or external analogy lanes.

## Linked homes

| subject | home |
|---|---|
| detailed current evidence state | [`current_evidence_state.md`](current_evidence_state.md) |
| latest holdout snapshot | [`v1_7_latest_holdout_snapshot.md`](v1_7_latest_holdout_snapshot.md) |
| recent native evidence history | [`recent_native_evidence_history.md`](recent_native_evidence_history.md) |
| anti-tautology audit path | [`v1_7_anti_tautology_role_dependence_check.md`](v1_7_anti_tautology_role_dependence_check.md) |
| known audit routine | [`v1_7_anti_tautology_known_routine.md`](v1_7_anti_tautology_known_routine.md) |
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

The latest holdout evidence should be shown as visual cards first, not as an Excel-style table. The compact machine-readable counts can live below the card and in dedicated docs.

Required front-page visual cards:

- `docs/assets/v1_7_6_triad27_holdout_card.svg`
- `docs/assets/v1_7_6_deep81_holdout_card.svg`
- `docs/assets/v1_7_6_wide243_holdout_card.svg`
- `docs/assets/v1_7_6_holdout_total_card.svg`
