# v1.8.1-alpha — Lineage-Bearing Predictor Package (Prior-Touch Semantics)

**Development decision:** `LOCAL_GREEN_LINEAGE_PACKAGE_ONLY`

**Scientific status:** `HOLD_LINEAGE_PACKAGE_DEVELOPMENT_ONLY`

**Scientific authority:** `v1.7.11-alpha`, `0 / HOLD`

## Exact implemented scope

One flat v1.8.0 snapshot cannot express an ordered temporal path. v1.8.1
therefore defines one predictor case as exactly three frames:

```text
early -> witness -> late
```

Every frame derives its exact seven numeric fields from the v1.8.0 observable
schema. The v1.8.1 schema document records both the base schema ID and its
SHA-256, so the frame firewall cannot silently drift away from the merged
v1.8.0 boundary. Row IDs, join IDs, labels, generator identity, seeds,
scenarios, semantic names, and legacy verdict fields remain outside the
predictor callback.

This version implements **prior-touch temporal support**. It does not implement
or claim continuous persistence.

## Threshold-free score

For frame `t`:

```text
Q_t = min(
  strength,
  distinction,
  polarity,
  relation,
  return_observed,
  observed_stability_score,
  1 - echo_mimic_score
)
```

The predictor computes:

```text
prior_touch_support = max(Q_early, Q_witness)
lineage_score       = min(Q_late, prior_touch_support)
no_lineage_score    = Q_late
lineage_delta       = no_lineage_score - lineage_score
```

The stable machine names retain `lineage` for version compatibility, but the
scientific meaning is narrower. A late score needs owned pressure at either
earlier touch. A path such as `.9 -> 0 -> .9` is deliberately treated as
dormant reappearance and may retain the early support; it is not evidence of
unbroken continuity.

No trinary threshold is selected in v1.8.1. The output is a continuous score
table, not a scientific prediction result.

## Executable formula canaries

| path | frame pressure | support score | no-support score | meaning |
|---|---|---:|---:|---|
| sustained | `.8 -> .8 -> .8` | `.8` | `.8` | prior touch and late pressure agree |
| late spike | `.2 -> .2 -> .9` | `.2` | `.9` | late pressure lacks an earlier touch |
| matured | `.2 -> .8 -> .9` | `.8` | `.9` | witness touch can support late pressure |
| collapsed | `.9 -> .8 -> .2` | `.2` | `.2` | late pressure remains limiting |
| dormant reappearance | `.9 -> 0 -> .9` | `.9` | `.9` | allowed; continuity is not claimed |

One-at-a-time input canaries also force every positive observable to become the
minimum and force `echo_mimic_score = .83` to contribute its `.17` complement.
They prevent the descriptive contract from passing if an implemented operand
is silently omitted.

## Executed package binding

The package contract hashes an exact allowlist containing the base v1.8.0
schema, the three-frame schema, predictor, package coordinator, and both JSON
contracts. Scoring does not call mutable already-imported predictor functions.
The coordinator compiles and executes the predictor runtime from the exact
verified source-byte snapshot and then rechecks the package bytes.

This is local code/configuration binding. It is not an operating-system sandbox
or an external timestamp proof, and the coordinator remains trusted as invoked.

## Source manifest and allowed-root boundary

Every score freeze requires:

- a caller-supplied allowed input root;
- an input file that resolves inside that root without symlink traversal;
- a canonical source manifest bound to the input bytes and expected purpose;
- an expected source-manifest SHA-256 supplied by the caller;
- explicit `false` declarations for label-informed observable construction and
  holdout material.

Those declarations are content-hash-bound statements, not independent proof of
the input's entire history. The generic freezer therefore does not infer that
holdout access never happened. v1.8.2 must provide its own generator and
development-fingerprint evidence.

## Strict post-freeze verification

The post-freeze verifier requires caller-retained expected hashes for the
predictor contract, source manifest, and freeze receipt. It reloads the verified
runtime, recomputes scores from the bound observable input, reconstructs the
manifest and receipt, compares exact bytes, and rechecks the input and package.
Reading hashes from the artifacts being checked would not create an independent
integrity boundary.

## Complete v1.8.2 method lock

v1.8.1 locks the development method without selecting a threshold:

- `selected_threshold_option: null` and
  `scientific_thresholds_selected: false`;
- exact threshold semantics: `score <= resist_max` is resist,
  `resist_max < score < crown_min` is hold, and `score >= crown_min` is crown;
- three candidate options: `.2/.8`, `.3/.7`, and `.4/.6`;
- four named controlled-synthetic generator lineages, each with expresser,
  latent, and trap cases; legacy triad27 variants do not count as independent
  lineages;
- nested leave-one-generator-lineage-out folds, with random row splits
  forbidden;
- a deterministic lexicographic objective beginning with worst-fold guardrail
  performance, followed by safety, macro recall, non-latent hold rate, boundary
  margin, and stable option ID;
- always-HOLD/CROWN/RESIST plus strength, gate-minimum, gate-mean, return,
  stability, and echo-guarded baselines;
- an exact score registry defining every baseline's per-frame formula and
  prior-touch aggregation, rather than leaving those names to interpretation;
- no-prior-touch and no-echo ablations evaluated both at frozen primary
  thresholds and with development-only retuning;
- exact class denominators, generator-lineage macro rates, deterministic
  lineage-cluster bootstrap uncertainty, duplicate de-inflation, conflicting
  label alias rejection, and permutation invariance;
- exact model-comparison tuples with zero equivalence tolerance, six executable
  failure-capability fixtures, and a SHA-256-indexed 2,000-resample percentile
  cluster bootstrap with fixed inclusive interval indices;
- fail-closed invalid/HOLD statuses; success means only
  `READY_FOR_V1_8_3_CONTRACT_ONLY`.

Development labels may enter only after raw scores and threshold options are
frozen. v1.8.3 and later holdout material is forbidden in v1.8.2.

## Adversarial review repairs

Before local closeout, independent review exposed and the implementation
repaired:

- disk bytes were hashed while mutable imported functions could execute;
- source/holdout provenance was asserted without an allowed-root manifest;
- the broad word `lineage` hid the narrower prior-touch semantics;
- equal-valued canaries could miss an omitted formula input;
- the development plan did not fully lock the future selector;
- cleanup could remove a file not proven to belong to the current writer;
- the three-frame schema duplicated rather than hash-bound the v1.8.0 schema;
- score artifacts had no strict consuming verifier.

## What this version does not earn

- It does not show that prior-touch support improves empirical discrimination.
- It does not select crown, resist, or hold thresholds.
- It does not treat source declarations as proof of external history.
- It does not create or reveal the unseen-generator holdout.
- It does not authorize DTA transfer, manuscript v2 prose, Zenodo, a tag, or a
  release.

The user has separately authorized full-agent execution of the planned
v1.8.2-through-v1.8.4 sequence, including scientific threshold selection,
holdout mechanics, GitHub CI, PRs, and merges. That operational authority does
not predetermine an evidence result: any locked invalid or HOLD condition still
stops scientific advancement. Scientific authority remains v1.7.11 `0 / HOLD`.
