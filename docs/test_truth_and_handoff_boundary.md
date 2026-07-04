# Test Truth and Handoff Boundary

**Status:** README overflow moved here in `v1.6.9-alpha`  
**Purpose:** preserve the exact evidence-chain and assistant-handoff rules without making the README begin with release bookkeeping.

A handoff is evidence only after the gates it reports have actually run. `runs/` bundles are local continuation evidence, not Git truth.

`v1.4.2-alpha` makes handoff includes strict by default. If a command requests a report file for the assistant handoff and that file is missing, the handoff fails instead of silently creating a partial bundle that looks green. Optional missing includes must be explicitly requested with `--allow-missing-include`.

`v1.4.3-alpha` preserves source-relative include paths inside the handoff ZIP. Three matrix reports can all be named `matrix_known_logic_closeout_read.md`; they now bundle as separate files under their run folders instead of overwriting each other by basename.

`v1.4.4-alpha` aligns adversary presets with the native four-gate cycle. Dedicated adversary presets now cover distinction, polarity, relation, and observed return, and tests lock that coverage before evidence runs are treated as complete.

`v1.4.5-alpha` adds a professional learning report for the v1.2-to-v1.4.4 line. It records what the line established, what remains bounded, and what evidence is needed before the language can move from toy-field proof-of-concept toward controlled synthetic-field benchmark.

`v1.5.0-alpha` adds a seed-block four-gate adversary report. It reads completed distinction, polarity, relation, and return matrix runs and reports earned-one, raw false-one pressure, latent pressure, relation/return debt, final false-one crowns, and mirror safety breaches in one evidence table.

`v1.5.1-alpha` adds a threshold sensitivity report. Matrix runs can now record gate/strength threshold overrides, and completed seed-block reports can be compared across threshold variants to expose stable, sensitive, or breached operating regions.

`v1.5.2-alpha` adds a witness ablation report. It reads completed four-gate matrix outputs and performs post-hoc accounting ablations over raw-as-final, false-one demotion, latent hold, and echo/relation-debt witness layers. This exposes which witness layers are doing visible work before heavier rerun-style ablations are attempted.

`v1.5.3-alpha` creates the controlled synthetic-field language boundary. It keeps `toy field` for the historical first-research-alpha proof record while allowing `controlled synthetic field` for the v1.5 experimental layer. It also moves runtime-history detail out of README/ROADMAP and into the runtime support note.

`v1.5.4-alpha` adds a historical `wide243` evidence-intake report. It records the uploaded original and fresh-seed `wide243` proof archives, explains `triad27` / `deep81` / `wide243`, and states when fresh controlled `deep81` / `wide243` four-gate reruns should happen.

`v1.5.5-alpha` preserves the fresh controlled `deep81` and `wide243` four-gate evidence runs as repo reports, README visual cards, and later paper-source material. It adds derived evidence metrics only; the native math witness is unchanged.

`v1.6.0-alpha` adds the role-blind shadow design. It is a report-only design checkpoint: the shadow may read observable behavior, but it must not read designed truth-role labels, and it does not replace the current role-aware witness.

`v1.6.1-alpha` adds role-stripped feature extraction. It reads completed seed-block and witness-ablation reports, writes feature files without designed truth-role shortcut fields, and keeps evaluation targets separate for later falsifier tests.

`v1.6.2-alpha` adds a transparent shadow score prototype. It reads only role-stripped feature files, writes fixed-weight report-side scores, refuses role/answer-key fields, and leaves target comparison for the next falsifier report.

`v1.6.3-alpha` adds a baseline/falsifier report. It compares already-written transparent scores against separated evaluation targets and trivial role-stripped baselines, records missing exact-baseline schema gaps, and still refuses role-blind discovery language.

`v1.6.4-alpha` adds a four-gate reconciliation / return-adversary audit. It states that the historical first-alpha proof used three dedicated adversarial corpora while return was measured as the native `B` gate, points to later dedicated return-adversary coverage, and writes Zenodo correction-note source text without backdating evidence.

`v1.6.5-alpha` adds a shadow holdout evaluation report. It evaluates already-written transparent shadow scores on declared held-out `deep81` / `wide243` role-stripped evidence, hardens opaque family IDs, and still refuses role-blind discovery language.

`v1.6.6-alpha` adds a triad27 preflight report. It forces the shadow line through the first trinary weather cube, `triad27 = 3^3`, before deeper `deep81` / `wide243` evidence is treated as the next rightful gate.

`v1.6.7-alpha` adds a shadow weather hardening report. It treats the actual triad27 wound seriously: the shadow score can be right and still scientifically trivial if raw-pressure or mirror baselines tie it. The new report evaluates triad27 / deep81 / wide243 evidence with expanded target variety, native-gate pressure diagnostics, baseline-tie reporting, and no score retuning.

`v1.6.8-alpha` adds a hardened triad27 evidence generator. It converts four native triad27 matrix runs into cell-level role-stripped evidence, exposes exact raw-strength / weakest-gate / relation-gate / return-gate baselines, and immediately runs weather hardening without retuning the score.

Generated comparison preset scripts now check the expected cross-logic report path before building the handoff and print the exact `assistant_test_handoff.zip` path to upload.

## v1.6.9-alpha placement repair

`v1.6.9-alpha` keeps these rules intact but moves this long ledger out of the README top card. The README now links here from the boundary/reference section near the end.

Practical rule:

```text
patch ZIP in Downloads = delivery shell
runs/.../assistant_test_handoff_*.zip = local evidence / continuation shell
repo commit = tracked source truth
```
