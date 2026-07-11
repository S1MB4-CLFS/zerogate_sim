# Codex Workflow Research Ledger

This ledger studies the economics of end-to-end Codex work. Credit cost is one
variable; elapsed time, human attention, defects caught, scientific discipline,
and repair work also count.

Values are factual receipts where available. Credit usage is `not_recorded`
unless supplied by the user or product telemetry. The user's purchase of a
credit allowance is budget context, not evidence that those credits were used.

## v1.8.0-alpha

| item | observation |
|---|---|
| execution mode | Codex local-green implementation, then user-authorized full publish/merge observation |
| local verification | 51 focused tests; 390 full-suite tests |
| independent review | caught observable TOCTOU, unbound label manifest, positional leakage, and overstated provenance before publish |
| first PR | #2 merged immediately because repository checks were not branch-protected |
| post-merge CI | failed on two test-portability assumptions; production firewall was not the failing surface |
| repair | PR #3; direct byte tamper plus optional external-workspace protocol equality |
| repair verification | 2 focused and 390 full local tests; both GitHub Actions runs passed before merge |
| human intervention after authorization | none required |
| credit usage | `not_recorded` |
| workflow lesson | inspect protection state; never assume auto-merge waits for non-required checks |

This is not evidence that full-agent mode is always cheaper. It is one observed
cycle showing both value (independent integrity review and autonomous repair)
and added work (an avoidable early merge caused by an incorrect automation
assumption).

## v1.8.1-alpha — local green, publication pending

| item | observation |
|---|---|
| execution mode | full-agent local implementation with independent adversarial review |
| review finding | disk source was hashed while mutable imported functions could execute |
| repair | predictor runtime is compiled and executed from the exact verified source-byte snapshot |
| review finding | arbitrary input paths and self-asserted holdout fields did not establish development provenance |
| repair | allowed-root source manifest, expected purpose/hash, and declarations-are-not-proof boundary |
| review finding | `lineage` wording overstated a two-touch operator; `.9 -> 0 -> .9` was indistinguishable from sustained support |
| repair | exact prior-touch semantics, no continuous-persistence claim, and explicit dormant-reappearance canary |
| review finding | equal-valued canaries could miss an omitted observable operand |
| repair | one-at-a-time formula-input canaries, including echo complement |
| review finding | the future development selector was not fully locked |
| first repair | threshold boundaries, generator lineages, nested folds, objective names, baselines/ablations, uncertainty, duplicate/permutation rules, and stop statuses were added |
| second review finding | named baselines, metrics, margin, equivalence, failure capability, and bootstrap still admitted result-changing implementation choices |
| final repair | exact baseline formulas/aggregation, denominators, boundary margin, zero-tolerance comparison tuple, six failure fixtures, and SHA-256-indexed percentile bootstrap are byte-locked |
| second review finding | the new prior-touch formula was mislabeled as the historical native witness |
| final repair | decision artifacts now separate `C_Z = min(D,P,R,B)` as the historical native witness from the v1.8.1 predictor formula |
| review finding | race cleanup, base-schema drift, and absent post-freeze consumption could weaken artifact authority |
| repair | file-identity cleanup, v1.8.0 schema ID/hash binding, and strict recomputing freeze verifier |
| scientific result | unchanged: v1.7.11 `0 / HOLD` |
| focused verification | 145 tests passed across v1.8.1, inherited v1.8.0, and version-surface gates |
| first full-suite attempt | 480 passed, 1 documentation-anchor failure; no code-behavior failure |
| full-suite repair | restored the stable `Manuscript v2, DTA transfer` authority phrase |
| final full-suite result | 481 passed |
| canonical local bundle | `LOCAL_GREEN_LINEAGE_PACKAGE_ONLY`; ZIP SHA-256 `3a99c237ad3cb19a98bc989e57f4881c2b01f1a8f906ebd64ae3ec6eb1b3c7f9` |
| human intervention | none required |
| credit usage | `not_recorded` |

## Authorized workflow-research sequence

The user explicitly authorized Codex to continue the planned v1.8 sequence
through v1.8.4 as an experiment in whether full-agent work saves human time.
The user reported purchasing 2,000 additional Codex credits for this test; that
is budget context, not measured consumption.

Authorized through v1.8.4:

- implementation, local tests, adversarial review, and evidence artifacts;
- scientific threshold selection from locked development data in v1.8.2;
- unseen-generator holdout contract and prediction freeze in v1.8.3;
- one-pass holdout label join and empirical closeout in v1.8.4;
- local commits, push, pull requests, CI inspection/repair, and merges for each
  version.

Still forbidden:

- tags and releases;
- DTA transfer or integration;
- manuscript v2 prose;
- Zenodo or other archive publication;
- email or other external communication.

This authority permits the process, not a positive result. `INVALID`, `HOLD`,
or `FALSIFIED` outcomes must remain visible and may stop or redirect the
sequence. Each version still needs its own coherent diff, local green, CI, PR,
merge receipt, and evidence boundary.

## Future version fields

For v1.8.1 onward record:

```text
version
elapsed local cycles
focused/full tests
independent-review findings
CI attempts and outcomes
PR/merge receipts
human interventions
credit usage if supplied
net human-time assessment
```
