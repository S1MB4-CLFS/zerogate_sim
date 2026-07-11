# v1.7.11-alpha — Evidence Integrity Correction

**Decision:** `0 / HOLD`

**Scientific status:** `HOLD_CONSTRUCTION_BOUND`

**Native witness:** `C_Z = min(D, P, R, B)`

**Historical release preserved:** `v1.7.10-alpha`

**Current authority:** the v1.7.10 `+1` closeout is superseded.

## Why this correction exists

The v1.7.10 software and evidence artifacts are reproducible, but the inference
drawn from them is not strong enough.

Two failures reopen the core question:

1. The earned-one/final path consumes `truth_role`. A trap is demoted because the
   system already knows that it is a trap. Consequently, zero final false crowns
   are construction-bound; they are not evidence that a blind witness discovered
   false-one structure.
2. `triad27`, `deep81`, and `wide243` are nested views. Their absolute counts were
   added as though the rungs were independent evidence, which double- and
   triple-counted atomic cases.

The previous Anti-Tautology Audit inspected summary states and supplied booleans.
It did not execute a role-free scorer, prove label invariance, or demonstrate
that a false crown could occur and be counted.

## Surviving evidence

The legacy controlled harness reproducibly partitions its designed role-aware
lanes. That remains useful software behavior and historical evidence.

It does not establish:

- blind empirical discrimination;
- role-free false-one detection;
- exact lineage authority in the final path;
- independent generator validation;
- transfer value for Deep Temporal Affect;
- physical, cosmological, clinical, or observed-world truth.

## Atomic overlap correction

The v1.7.11 audit normalizes the operational defaults already implemented in the
matrix engine:

```text
absent perturbation axis = -1 / calm
absent time axis         =  0 / baseline
```

It then identifies a candidate-run case from the generator, canonical candidate
corpus, observable candidate specification, seed, simulation configuration, and
effective five-axis scenario. Rung and filesystem path are excluded from the
identity so nested copies can match.

Authority is bound to the frozen canonical contract, not caller-selected
expectations:

```text
contract id       = zerogate-v1.7.11-evidence-integrity-canonical-v1
contract SHA-256  = ecaddfc43bd276b58bba0fd9914f8e62e3652a639c750f619b15b13493f74a34
candidate corpora = 5 exact profiles
scenario grids    = 27 / 81 / 243 exact cells
seed set          = 18 through 26 inclusive
```

A custom or incomplete contract may exercise structural test mechanics, but it
cannot issue authoritative unique-union counts and the audit CLI exits nonzero.

Verified local holdout structure:

| view | gate-score files | candidate opportunities | relation to wider view |
|---|---:|---:|---|
| triad27 | 1,215 | 28,917 | exact subset of deep81 |
| deep81 | 3,645 | 86,751 | exact subset of wide243 |
| wide243 | 10,935 | 260,253 | unique union |
| naive arithmetic sum | 15,795 | 375,921 | invalid as independent evidence |

```text
unique atomic cases             = 260,253
duplicate atomic representations = 115,668
payload conflicts                = 0
```

The old pooled totals remain historical arithmetic only:

```text
earned-one             12,206
raw expression         18,353
false-one pressure      4,671
```

They are not valid unique evidence totals.

## Denominated rung view

| rung | opportunities | earned | earned rate | raw expression | raw rate | false pressure | false-pressure rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| triad27 | 28,917 | 839 | 2.9014% | 1,283 | 4.4368% | 321 | 1.1101% |
| deep81 | 86,751 | 1,950 | 2.2478% | 3,012 | 3.4720% | 807 | 0.9302% |
| wide243 | 260,253 | 9,417 | 3.6184% | 14,058 | 5.4017% | 3,543 | 1.3614% |

Absolute counts are expected to grow with opportunity exposure. They must not be
forced to become non-monotonic. Future comparisons use rates, matched cases,
per-seed/per-family summaries, and uncertainty.

## Unique-union descriptive counts

Because wide243 contains the two narrower operational slices, the nested-safe
descriptive union is:

```text
opportunities           260,253
earned-one                9,417
raw expression           14,058
latent overcrown             21
relation debt               465
return debt                 612
false-one pressure         3,543
final false crowns             0
```

These counts remain outputs of the role-aware construction. Correct accounting
does not turn them into blind evidence.

## Lineage status

Manuscript lineage is not part of final earned-one. The current pipeline writes
lineage artifacts beside earned-one/final artifacts; the verdict does not consume
them. Until lineage is a required input and its ablation changes controlled and
held-out predictions, its exact status is:

```text
lineage_report_only_not_implemented_in_final_path
```

## Fail-closed changes

- Final-output counts are rebuilt from normalized gate rows and must match every
  supplied summary before accounting can pass.
- The evidence bundle records canonical case identities and typed gate payloads
  for replay, with root-relative source identifiers rather than machine-local
  absolute paths.
- Numeric formatting differences such as `1` versus `1.0` do not create false
  payload conflicts.
- The canonical contract ID and hash are required by corrected closeout.
- Aggregate rung summaries report `not_verified` for masking, frozen-manifest,
  and reference-independence claims.
- Missing or malformed denominators and duplicate candidate rows fail instead
  of becoming zero or inflating totals.
- Semantically duplicate matrix artifacts are diagnosed even if CSV byte order
  or numeric formatting differs.
- The historical anti-tautology CSV reader cannot produce current claim
  authority from supplied booleans.
- The closeout consumes a v1.7.11 integrity decision artifact and remains HOLD.
- The closeout no longer embeds static passing conditions or active pooled totals.

## Active version contract

```text
objective:
  correct provenance and nested-rung accounting; withdraw unsupported closeout

hypothesis:
  the existing raw artifacts remain reproducible, but their strongest inference
  becomes 0/HOLD after executable integrity checks

falsifier:
  atomic cases do not nest as diagnosed, payloads conflict, denominators do not
  match raw gate records, or generated closeout still reaches +1

forbidden expansion:
  no native witness rewrite, no scientific thresholds, no manuscript promotion,
  no DTA integration, no release action

rollback target:
  commit 718ca61 / tag v1.7.10-alpha
```

## Holds

```text
manuscript v2       HOLD
DTA transfer        HOLD
scientific thresholds HOLD
frozen blind holdout HOLD
Zenodo / release    HOLD without separate authority
```

## Next coded boundary

`v1.8.0-alpha — Observable Schema and Label Firewall`.

That version must separate observable inputs, blind predictions, and later
evaluation labels before any mechanism repair is allowed to seek a new result.
