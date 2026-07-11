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

## v1.8.1-alpha — merged

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
| checkpoint commit | `b5a9394a63377103c375a2680988713f0030a243` |
| pull request | [#4](https://github.com/S1MB4-CLFS/zerogate_sim/pull/4) |
| remote verification | push and pull-request `pytest (release 3.12)` runs passed in 48s and 52s before merge |
| merge receipt | `f11835e5d63c8f686ae1801793a78d3ce6577705` |
| human intervention | none required |
| credit usage | `not_recorded` |

## v1.8.2-alpha — merged scientific stop

| item | observation |
|---|---|
| baseline | merged v1.8.1 main at `f11835e5d63c8f686ae1801793a78d3ce6577705` |
| execution mode | full-agent implementation with disjoint generator, evaluation-math, and pre-label-firewall ownership |
| locked boundary | class-conditioned development generators are allowed; fixed raw traces must make frames, scores, options, and predictions invariant to labels, identifiers, and groups |
| development data | four distinct backends × three roles × 12 cases = 144 class-conditioned controlled-synthetic cases; generator lineage is the split and uncertainty unit |
| retained pre-label roots | split `c9dc6890…`; observables `bcc3cad7…`; source `1cb70ba1…`; fingerprint `571f3f2c…`; pre-label receipt `9c772546…` |
| data-quality result | 144 raw / 144 effective / 144 unique; exact 12-per-role-per-lineage denominators; 0 duplicate representations; exact blind/atomic joins |
| failure capability | 6/6 canaries passed after repair to route fixtures through shared production guards rather than a fixture-only status oracle |
| review finding | the first failure-capability implementation could certify locally restated expected statuses without exercising production guards |
| repair | constant-control, constant-primary, false-crown, and balanced-operability guards are shared by the real evaluator and the canaries; regression tests count those production calls |
| review finding | source/pre-label/evaluator allowlists, generator semantic root, and raw frame-slice bindings were incomplete |
| repair | exact ordered allowlists, file-byte plus semantic contract roots, exact frame windows/raw slices, evaluator method package, and transitive receipt bindings |
| review finding | simple baselines were given an unregistered frozen-threshold gate, dead-safe baseline exceptions auto-passed, and unexpected ablation math errors could be mislabeled HOLD |
| repair | simple baselines use their own locked nested selection; only ablations use frozen and retuned paths; dead-safe comparisons do not pass; unexpected math errors fail as invalid artifacts |
| review-process wound | a read-only review harness executed two deterministic development joins inside automatically deleted temporary directories; the retained split was later rebuilt without parameter/code changes and reproduced all four captured pre-label roots byte-for-byte |
| protocol repair | a label-opening review is now classified as a scientific run and must use a persistent named evidence root; temporary auto-cleanup is forbidden for real label joins |
| retained scientific result | `INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR`; no selected option; evaluation receipt `00935943039930113e732ea8f794adce0087458f2fc94d234285b089c440a205` |
| exact blocker | primary scores are globally variable (144 unique), but `piecewise_hysteresis_v1` maxes at `0.58779880167953524`, below the narrowest crown boundary `0.6`; all three options have zero crowns on that lineage |
| correctly unexecuted | nested selection never became valid, so baseline/ablation comparison and cluster uncertainty were not run or inferred |
| final local verification | 123 focused v1.8.2/version-surface tests and 601 full-suite tests passed |
| final independent diff review | no P1/P2 blockers; retained hashes and every bound source byte matched, invalid outputs remained unexecuted where required, no holdout implementation/access, and generated evidence stayed ignored |
| checkpoint commit | `528ac55e76cd974be72d0572429963d4c0319d4f` |
| pull request | [#5](https://github.com/S1MB4-CLFS/zerogate_sim/pull/5) |
| remote verification | push and pull-request `pytest (release 3.12)` runs both passed before merge: [push run](https://github.com/S1MB4-CLFS/zerogate_sim/actions/runs/29164269010), [PR run](https://github.com/S1MB4-CLFS/zerogate_sim/actions/runs/29164277666) |
| merge receipt | `14f0abe7a88bf0c11e18d45e0e5e7c2df879e256` |
| holdout boundary | v1.8.3 and v1.8.4 are blocked; no holdout material exists or was accessed |
| human intervention | none required during implementation/evidence execution |
| credit usage | `not_recorded` |
| purchased-credit context | user reported purchasing 2,000 additional Codex credits for the workflow experiment; this is not measured consumption |
| economic observation | parallel ownership and adversarial review caught multiple decision-integrity faults, but also added two invalid ephemeral review runs; end-to-end delegation shifted substantial QA/Git attention away from the human while increasing agent work |

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

The retained v1.8.2 result is `INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR`, so the
scientific sequence stopped before v1.8.3. Full-agent Git/CI publication of the
honest v1.8.2 negative gate remains in scope; holdout construction, freeze, and
reveal do not.

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
