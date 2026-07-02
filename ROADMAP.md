# ZeroGateSim Roadmap

**Current line:** `v1.4.4-alpha` four-gate adversary coverage lock  
**Release posture:** public research-alpha / speculative toy-field proof-of-concept

**CI support boundary:** Python 3.12 is the required release/test runtime. v1.3.5 deliberately tried to re-expand Python 3.10 / 3.11 / 3.12, but GitHub Actions showed 3.10 / 3.11 are still red. v1.3.6 keeps the release gate green on 3.12 and moves older interpreters into manual compatibility probes so unresolved legacy drift does not block the main research line.

ZeroGateSim already has a first-research-alpha toy-field proof record. The next work is not to make bigger claims or add shiny machinery. The next work is to make the native math testable, then compare that native math against nearby formal logic families without pretending they are the same thing.

## North Star

ZeroGateSim tests whether dimensional expression can be modeled as candidate freedoms passing through a zero-gate cycle of distinction, polarity, relation, and return, then earning final +1 through a trinary witness stack.

Current supported claim:

> Inside generated toy fields, final trinary witness separated earned-one from raw expression, latent overcrown, and false-one pressure across original and fresh-seed adversarial proof records.

Current unsupported claims:

- not proof of cosmology;
- not proof of physical dimensional genesis;
- not proof that reality itself is trinary;
- not role-blind false-one discovery;
- not equivalence with Kleene, Lukasiewicz, Priest, Belnap, fuzzy, or other known logic systems.

## Current proof record

Combined original proof and fresh-seed reproduction:

- `1458` scenario cells;
- `13122` seeded toy-field runs;
- `22131` final earned-one events;
- `2388` raw false-one pressures detected and demoted;
- `0` final false-one crowns.

This is the proof-of-concept floor. It is not the roof.

## Operating law

The build order is:

> native geometry -> native math -> code fidelity -> invariant tests -> formal mirrors -> stronger experiments.

Any version that skips this order is a HOLD or RESIST event.

## v1.0-alpha to v1.0.2-alpha — First proof floor

Completed:

- first-research-alpha proof record;
- public source foundation;
- generated run exclusion;
- release notes and proof boundary;
- MIT license and citation metadata.

Purpose:

Show that the toy-field engine can generate adversarial pressure, name false-one pressure, and refuse final false-one crowns inside the controlled harness.

## v1.1-alpha — Public witness pack

Completed or preserved:

- README / quickstart / public sharing path;
- claim boundary;
- reviewer guide;
- visual guide and visual assets;
- proof record summary;
- simulation-supported manuscript scaffold.

Purpose:

Let a skeptical reader understand what was tested, what was not tested, and where the proof record belongs.

## v1.2-alpha — Native math and scope discipline

Purpose:

Make the native ZeroGateSim math explicit and testable before comparing it against known logic systems.

Native anchors:

- `E0 = (Z0, tau)` — zero-zone under generative ordering;
- `T3[X](tau)` — becoming / witness-invariance / inheritance posture;
- `Li = (-ei, 0, +ei)` — polarity around zero;
- `Gamma_i = D_i P_i R_i` — return-potential / relational-gravity coherence;
- `C_Z = min(D, P, R, B)` — weakest-gate coherence;
- `chi_raw` — local expression pressure;
- `Z(0)..Z(4)` — return-depth grammar;
- `chi_earned` — raw expression plus return-depth, lineage, independence, and role witness.

### v1.2.1-alpha — Version truth repair

Repair README, ROADMAP, package metadata, and public docs so the repo tells one version story.

Success condition:

- no active file falsely calls the current line `v1.0.2-alpha` or `v1.1-alpha`;
- release history remains visible instead of being rewritten.

### v1.2.2-alpha — Native math witness map

Add `docs/math_witness_map.md`.

Each native object must show:

- geometry;
- manuscript equation;
- code trace;
- invariant;
- external-logic relevance;
- overclaim boundary.

Success condition:

A reader can trace:

> geometry -> math -> code -> test -> claim boundary.

### v1.2.3-alpha — Native invariant tests

Add `tests/test_native_math_invariants.py`.

Protected commitments:

- `C_Z = min(D, P, R, B)`;
- return-potential behaves as `D * P * R`;
- raw expression requires strength and zero-gate coherence threshold passage;
- zero-depth is ordered and bounded;
- `0+`, `0`, and `0-` remain distinct;
- final +1 is not raw +1 automatically.

Success condition:

The tests catch broken gates, broken witness grammar, and accidental overcrown.

### v1.2.4-alpha — Superseded overbuild

Status: superseded by `v1.2.5-alpha`.

A Power-Up / Fail reporting module was added too early. The idea was useful as a human acceptance question, but not ready as engine machinery. It blurred future validation language with current capability.

What was wrong:

- informal operator language became code too soon;
- future role-blind and later-pressure validation appeared as a ladder before the tests were designed;
- the roadmap drifted from native math / known-logic comparison into acceptance-reporting machinery.

Boundary:

- do not treat `POWER` or “holy-shit detector” language as active product architecture;
- keep that language only as documentation-level acceptance criteria until tests exist.

### v1.2.5-alpha — Roadmap repair and surgical scope recovery

Purpose:

Restore the active line to native math fidelity and release-safe simulation criteria.

Changes:

- remove `src/zerogate_sim/power_check.py` from the active package;
- remove `tests/test_power_check.py`;
- remove the `zerogate-power-check` console script;
- add `docs/simulation_win_conditions.md` as a documentation-only translation of “power up or fail”;
- add `docs/local_tooling_repair.md` for the corrupted-pip / editable-install failure;
- rewrite ROADMAP so the next steps point toward formal comparison, not accidental machinery.

Success condition:

The active package is back to:

> toy-field proof floor -> native math fidelity -> known logic mirror preparation.

No new gate. No fake detector. No external-logic claim yet.

### v1.2.6-alpha — Local tooling repair note only

Purpose:

Make the editable-install / broken-pip repair path explicit in docs and quickstart if needed.

Allowed:

- docs-only repair instructions;
- workflow clarification.

Forbidden:

- engine changes;
- roadmap expansion;
- workaround code for a local pip corruption.

### v1.2.7-alpha — Zero-band prediction design, not code yet

Purpose:

Design how to test whether `0+`, `0`, and `0-` predict later maturation, ambiguity, or collapse.

Required before code:

- define later-pressure scenarios;
- define expected behavior per zero band;
- define what counts as prediction success;
- define what falsifies the claim.

Success condition:

The test design exists before any prediction module exists.

## v1.3-alpha — Known logic mirror foundation

Purpose:

Compare ZeroGateSim's native math against known non-binary logic families as projection mirrors, not identity claims.

Forbidden claim:

> ZeroGateSim is Kleene logic, Lukasiewicz logic, Priest logic, Belnap logic, or fuzzy logic.

Allowed claim:

> ZeroGateSim can project its native states and scores into known logic mirrors to see what is preserved, collapsed, or distorted.

### v1.3.0-alpha — Fuzzy / many-valued mirror foundation

Purpose:

Begin the formal mirror line with the closest native mathematical neighbor: continuous fuzzy / many-valued scoring.

Why first:

ZeroGateSim already computes continuous gate scores and native weakest-gate coherence:

```text
C_Z = min(D, P, R, B)
```

This can be compared safely against other continuous conjunction mirrors without claiming equivalence.

Delivered:

- `docs/known_logic_boundary.md`;
- `docs/fuzzy_mirror.md`;
- `src/zerogate_sim/fuzzy_mirror.py`;
- `tests/test_fuzzy_mirror.py`;
- matrix outputs:
  - `matrix_fuzzy_mirror_trace.csv`;
  - `matrix_fuzzy_mirror_candidate_summary.csv`;
  - `matrix_fuzzy_mirror_read.md`.

Comparison mirrors:

- native min gate;
- product gate;
- average gate;
- Lukasiewicz-style conjunction;
- strength-min-native pressure.

Key diagnostic:

- `average_overcrown_pressure`: average gate passes threshold while native min gate fails.

Success condition:

A matrix run can show where ZeroGateSim behaves like fuzzy scoring, where average aggregation hides a wounded gate, and why a high fuzzy score remains pressure rather than final earned-one.

Boundary:

No new core gate. No final truth claim. No identity with fuzzy logic.

### v1.3.1-alpha — Belnap evidence-state mirror

Purpose:

Compare ZeroGateSim's raw-expression / earned-one / false-one / hold grammar with evidence-state logic.

Delivered:

- `docs/belnap_mirror.md`;
- `src/zerogate_sim/belnap_mirror.py`;
- `tests/test_belnap_mirror.py`;
- matrix outputs:
  - `matrix_belnap_mirror_summary.csv`;
  - `matrix_belnap_mirror_read.md`.

Projection target:

- `T` / true-only: evidence for final +1 without contrary witness;
- `F` / false-only: evidence against final +1 without positive expression pressure;
- `B` / both: raw expression or positive-looking pressure plus false-one / latent / relation-debt witness;
- `N` / neither: clean hold / insufficient evidence.

Key diagnostic:

- Belnap `B` conflict-pressure: positive-looking pressure and contrary witness coexist locally.

Success condition:

The projection exposes whether ZeroGateSim preserves local conflict instead of flattening it or crowning it.

Boundary:

A Belnap `B` state is not a native final +1. It is pressure under conflict. The native earned-one witness still decides final output.

### v1.3.1-alpha companion — Assistant test handoff bundle

Purpose:

Create one uploadable bundle after local test gates so future continuation can read test status, git state, notes, and optional result files.

Delivered:

- `docs/assistant_test_handoff.md`;
- `src/zerogate_sim/test_handoff.py`;
- `tests/test_assistant_test_handoff.py`.

Use local-source mode:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.test_handoff --version v1.3.1-alpha --status passed --note "full test suite passed" --out runs\assistant_test_handoff_v1_3_1_alpha
```

Boundary:

This bundle is a continuation aid, not a truth machine and not a release gate by itself.

### v1.3.2-alpha — Paraconsistent conflict-locality mirror

Purpose:

Test whether contradiction pressure stays local.

Delivered:

- `docs/paraconsistent_mirror.md`;
- `src/zerogate_sim/paraconsistent_mirror.py`;
- `tests/test_paraconsistent_mirror.py`;
- matrix outputs:
  - `matrix_paraconsistent_mirror_summary.csv`;
  - `matrix_paraconsistent_mirror_read.md`.

Core rule:

> raw +1 plus debt must not explode into arbitrary final +1.

Projection target:

- `conflict_localized`: Belnap-both conflict pressure is held or demoted instead of crowned;
- `conflict_overcrowned`: Belnap-both conflict pressure becomes final +1 and must be inspected as a breach;
- `true_without_conflict`: positive evidence without contrary witness;
- `false_without_conflict`: contrary witness without positive pressure;
- `neither_without_conflict`: no decisive pressure.

Key diagnostic:

- `local_explosion_flag`: conflict pressure was crowned as final +1.

Success condition:

Conflicting evidence can be reported without crowning unrelated candidates or confirming the whole run.

Boundary:

This is not Priest logic and not a native gate. It is a projection mirror that reads conflict-locality pressure after the native final-output witness.

### v1.3.3-alpha — Kleene / Lukasiewicz compression and loss mirror + CI support boundary

Purpose:

Test what gets lost when native final trinary output compresses to true / unknown / false.

Delivered:

- `docs/three_valued_mirror.md`;
- `src/zerogate_sim/three_valued_mirror.py`;
- `tests/test_three_valued_mirror.py`;
- matrix outputs:
  - `matrix_three_valued_mirror_summary.csv`;
  - `matrix_three_valued_mirror_read.md`.

Projection:

- final `+1` earned-one -> `T` true;
- final `0` witness / hold / debt / wound -> `U` unknown;
- final `-1` resist / rejection / demotion -> `F` false.

Required loss report:

- native zero-state detail collapses into one middle value;
- temporal lineage and echo-debt information are lost;
- raw expression vs earned-one must remain externally explained.

Boundary:

This is not full Kleene K3 or Lukasiewicz L3 semantics. It is a value-level compression mirror that prepares the ground for deeper truth-table comparison only if later needed.

### v1.3.4-alpha — v1.3 mirror closeout

Purpose:

Confirm that the fuzzy, Belnap, paraconsistent, and K3/L3 mirrors are projections with explicit loss reports before moving into wider comparison.

Delivered:

- `src/zerogate_sim/known_logic_closeout.py`;
- `tests/test_known_logic_closeout.py`;
- `docs/known_logic_closeout.md`;
- `matrix_known_logic_closeout_summary.csv`;
- `matrix_known_logic_closeout_read.md`.

Success condition:

A reader can see which mirror is useful for which pressure and where each mirror lies if overused. The closeout report must not turn projection into borrowed authority.


### v1.3.5-alpha — CI compatibility re-expansion

Purpose:

Repair the temporary support narrowing introduced when older-interpreter CI failures appeared during the known-logic mirror line.

Delivered:

- restore `requires-python = >=3.10`;
- restore CI matrix for Python 3.10 / 3.11 / 3.12;
- add `docs/runtime_ci_support.md`;
- bound dependencies below future major versions where practical;
- keep local handoffs on `PYTHONPATH=src` while CI still checks editable install.

Success condition:

GitHub Actions is green on Python 3.10, 3.11, and 3.12.

Boundary:

If one lane fails, feature work stops and that exact interpreter log is repaired. Do not leave older-interpreter failures as vague HOLD language.

## v1.4-alpha — Cross-logic comparison report

Purpose:

Aggregate fuzzy, Belnap, paraconsistent, and K3/L3 projection closeout results across completed matrix runs.

### v1.4.0-alpha — Cross-logic report foundation

Delivered:

- `docs/known_logic_comparison_report.md`;
- `src/zerogate_sim/cross_logic_report.py`;
- `tests/test_cross_logic_report.py`;
- console script: `zerogate-cross-logic`;
- report outputs:
  - `cross_logic_comparison_summary.csv`;
  - `cross_logic_comparison_matrix_summary.csv`;
  - `cross_logic_comparison_mirror_summary.csv`;
  - `cross_logic_comparison_read.md`;
  - `cross_logic_report_bundle.zip`.

Success condition:

A reader can see which external logic mirror is useful for which pressure across completed runs, where safety breaches appear, and what each mirror loses.

Boundary:

This line reads completed toy-field evidence. It does not run a new proof harness, mutate the native gate, or claim equivalence with any external logic system.

### v1.4.1-alpha — Stronger run comparison preset

Purpose:

Define small, repeatable comparison recipes for reading multiple completed matrix runs without turning the preset itself into a proof harness.

Delivered:

- `src/zerogate_sim/comparison_preset.py`;
- `tests/test_comparison_preset.py`;
- `docs/cross_logic_comparison_presets.md`;
- console script: `zerogate-cross-logic-preset`;
- generated local outputs:
  - `comparison_preset_read.md`;
  - `comparison_preset_manifest.csv`;
  - `run_preset.ps1`.

Preset families:

- `quick_smoke` — wiring check;
- `adversary_triad27` — small distinction / polarity / relation / return adversary comparison;
- `wide_adversary_probe` — heavier wide243 four-gate adversary probe.

Success condition:

A reader can generate a repeatable run plan for stronger cross-logic comparison while preserving the boundary: a preset is a plan, not evidence.

Boundary:

This version writes commands. It does not run heavy matrices automatically, does not mutate the native gate, and does not claim stronger proof until generated outputs are actually produced and reviewed.


### v1.4.2-alpha — Truth-safe handoff and preset path repair

Purpose:

Repair the continuation/test handoff layer so it cannot silently omit requested result files or print ambiguous paths.

Delivered:

- strict include checking in `src/zerogate_sim/test_handoff.py`;
- `--allow-missing-include` only for explicit optional missing files;
- include audit and missing-include count in handoff JSON/Markdown;
- generated preset scripts check the exact cross-logic report path before building the handoff;
- generated preset scripts print the exact ZIP path to upload.

Success condition:

A handoff that says tests passed must either contain the requested evidence files or fail loudly. No silent skipped include. No wrong report path hidden behind a green-looking bundle.

Boundary:

This is infrastructure truth repair. No native gate change, no new mirror, no new simulation claim.

### v1.4.3-alpha — Unique handoff include path repair

Purpose:

Repair the second continuation/test handoff wound: different result files with the same basename must not collapse into one bundled file.

Delivered:

- source-relative include paths are preserved under `included/`;
- include audit records `source_relative_path`;
- duplicate basenames from distinction / polarity / relation matrix folders remain separate in the ZIP;
- tests prove same-named closeout files keep distinct contents in the bundle.

Success condition:

A handoff that includes three `matrix_known_logic_closeout_read.md` files from three run folders must preserve all three as distinct evidence files with distinct contents.

Boundary:

This is infrastructure truth repair. No native gate change, no new mirror, no new simulation claim.

### v1.4.4-alpha — Four-gate adversary coverage lock

Purpose:

Align adversary comparison presets with the native four-gate witness cycle: distinction, polarity, relation, and observed return.

Delivered:

- `adversary_return` candidate profile;
- `return_triad27` in the `adversary_triad27` preset;
- `return_wide243` in the `wide_adversary_probe` preset;
- preset coverage helpers and tests that require four-gate adversary presets to cover every native gate.

Success condition:

A four-gate adversary preset cannot be treated as complete unless its dedicated run coverage equals the native gate set: distinction, polarity, relation, and return.

Boundary:

This is coverage repair for run planning. It does not change the native gate law, the mirror layer, or the final-output claim boundary.

## v1.5-alpha — Stronger toy-field experiments

Purpose:

Move from current designed adversarial roles toward stronger tests without pretending role-blind discovery is solved.

Possible work:

- independent oracle signal families;
- stricter adversarial corpora;
- threshold sensitivity;
- ablation: remove return / lineage / independence / role witness;
- seed block confidence summaries.

Success condition:

The engine becomes harder to fool under tests that were not shaped only around its own favorite examples.

## v1.6-alpha — Role-blind shadow design

Purpose:

Design, then only later implement, a shadow detector that estimates false-one pressure from observable metrics without reading designed truth-role labels.

Required before code:

- metric list;
- expected failure modes;
- comparison against current role-aware proof witness;
- clear claim boundary.

## v2.0 direction — External review and observed-universe bridge

Only after v1.3-v1.6 are stable:

- external reproduction of small runs;
- effective dimension comparisons: PCA rank, stable rank, graph diffusion, spectral-style return probabilities;
- comparison against relevant emergence / pregeometry / many-valued logic literature;
- evidence DOI plan;
- manuscript update separating simulation support, mathematical analogy, and physical speculation.

Observed-universe bridge rule:

> A match to known math or observed behavior is support for a modeling analogy, not proof that the universe uses ZeroGateSim.

## HOLD conditions

Stop and repair before advancing if:

- public language implies proof of cosmology or physics;
- final false-one crowns reappear and are hidden;
- raw expression is treated as final earned-one;
- role-aware proof is described as role-blind discovery;
- known-logic projection is described as identity;
- generated runs, bundles, or PDFs enter Git history by accident;
- roadmap turns into a wish list instead of a promise map.

## Operating sentence

Small engine. Native math first. Formal mirrors second. Stronger reality bridge later.

A real one is not the first thing after zero. A real one is what zero can return as without lying.
