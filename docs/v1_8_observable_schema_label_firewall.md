# v1.8.0-alpha — Observable Schema and Label Firewall

**Development decision:** `LOCAL_GREEN_FIREWALL_ONLY`

**Scientific authority:** `v1.7.11-alpha`, `0 / HOLD`

**Native witness:** `C_Z = min(D, P, R, B)`

**Evidence class:** synthetic infrastructure canaries only

## What this version earns

`v1.8.0-alpha` implements the callback-argument/schema and hash-integrity
boundary that v1.7 lacked. It does not implement or validate a scientific
scorer, operating-system sandbox, encryption boundary, or access-control
boundary.

The predictor callback receives exactly seven finite values in `[0, 1]`:

| field | status |
|---|---|
| `strength` | permitted pre-verdict observable |
| `distinction` | permitted pre-verdict observable |
| `polarity` | permitted pre-verdict observable |
| `relation` | permitted pre-verdict observable |
| `return_observed` | permitted pre-verdict observable |
| `echo_mimic_score` | permitted pre-verdict observable |
| `observed_stability_score` | permitted pre-verdict observable |

Missing, extra, malformed, non-finite, boolean, or out-of-range values fail
closed. Negative zero is normalized. Labels, semantic names, source/profile
identifiers, scenario controls, expected outcomes, legacy role-derived
aggregates, and derived verdict fields are forbidden.

## Structural separation

The path is split across three modules:

```text
observable split
  -> transport row: row_index + seven observables
  -> callback argument: seven observables only; row_index excluded
  -> hash-bound join keys: row_index <-> blind_case_id
  -> separately serialized, hash-bound labels: blind_case_id <-> evaluation_role

prediction freeze
  -> callback receives immutable observables only
  -> canonical predictions
  -> freeze manifest
  -> pre-label receipt

label join / evaluation
  -> verify expected receipt and frozen artifacts from one byte snapshot
  -> verify expected split-manifest hash
  -> verify join-key hash
  -> only then read and verify the label-vault bytes
  -> require exact ID-set equality and evaluate
```

The freeze hashes the exact observable bytes parsed for scoring. It rejects an
observable file changed during callbacks. Verification reads each artifact
once, hashes and parses that same snapshot, and refuses any mismatch.

The split manifest hash-binds observable inputs, join keys, and the separately
serialized label artifact. A
caller must provide the expected split-manifest SHA-256, just as it must provide
the expected pre-label receipt SHA-256.

## Leakage and determinism controls

- Source and blind identifiers are not callback arguments.
- Labels and expected outcomes are not callback arguments.
- Identical observable vectors must yield identical proposals.
- Every predictor is repeated in reverse row order; disagreement fails closed.
- A row-permutation canary compares predictions by observable hash.
- Label permutation leaves observable and prediction bytes unchanged.
- Identifier renaming leaves observable and prediction bytes unchanged while
  changing the hash-bound join-key artifact.

These controls establish the callback argument boundary and reject ordinary
position/state/randomness leakage. They do not prove safety against malicious
code with filesystem or global-state access.

## Failure capability

The evaluator uses explicit synthetic canaries:

| canary | required result |
|---|---|
| perfect three-class control | evaluator operable, science still HOLD |
| injected trap crown | false crown counted |
| injected latent crown | HOLD overcrown counted |
| always HOLD | invalid constant refusal |
| always CROWN | invalid constant overcrown |
| always RESIST | invalid constant rejection |

Generated local-green status also depends on executable negative canaries for
forbidden fields, prediction tampering, and label-artifact hash tampering. These are
not unconditional success flags.

## Commands

Run the focused adversarial suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_v1_8_observable_schema_label_firewall.py
```

Build the synthetic infrastructure record:

```powershell
.\.venv\Scripts\python.exe -m zerogate_sim.v1_8_observable_schema_label_firewall `
  --out runs\v1_8_observable_schema_label_firewall_local
```

## Honest limits

- The bundled predictor is a lookup canary, not a scientific scorer.
- No scientific threshold, abstention rule, or optimization target is selected.
- No frozen empirical holdout is read or revealed.
- The predictor-contract hash is caller-declared; v1.8.0 does not bind it to a
  packaged code/config artifact.
- An in-process Python callback is not an operating-system sandbox.
- A local hash proves artifact integrity, not external timestamped chronology.
- Synthetic evaluator operability is not evidence of real discrimination.
- The native witness and legacy simulator logic are unchanged.
- Manuscript v2 and DTA transfer remain on HOLD.

## Checkpoint

Stop before scientific scorer thresholds, frozen holdout reveal, DTA transfer,
manuscript prose, merge, tag, push, PR, or release.

The next proposed coded gate is `v1.8.1-alpha — Lineage-Bearing Predictor
Package and Development-Only Preregistration`. It requires new authorization
because threshold choices begin to shape the empirical claim.
