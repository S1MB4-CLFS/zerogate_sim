# v1.6.8-alpha — Shadow triad27 hardened evidence

## Purpose

`v1.6.8-alpha` adds a harder triad27 evidence generator for the role-blind shadow line.

The previous triad27 audit showed the important wound: the shadow score could rank the four families correctly while being tied by trivial baselines. This version does not repair or retune the score. It makes the triad27 battlefield more informative first.

## Added

- `src/zerogate_sim/shadow_triad27_hardened_evidence_report.py`
- `tests/test_shadow_triad27_hardened_evidence_report.py`
- `docs/shadow_triad27_hardened_evidence.md`
- console script: `zerogate-shadow-triad27-hardened-evidence`

## What changed

The new report reads completed four-gate triad27 matrix directories and writes a standard evidence base:

```text
seed_block/
role_stripped/
shadow_score/
weather_hardening/
cell_evidence/
```

It converts the evidence into cell-level role-stripped family rows and adds exact baseline fields:

- `feature_raw_strength_pressure_rate`
- `feature_weakest_gate_pressure_rate`
- `feature_relation_gate_rate`
- `feature_return_gate_rate`

The native gate label and truth-role labels remain out of the feature inputs. Evaluation labels are kept only in the target file and joined after scoring.

## Boundary

This version is not role-blind discovery, not detector closeout, not a shadow-score repair, and not a native witness mutation.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Next

Run fresh harder triad27 matrix evidence, then run this report. Only if the hardened result is non-trivial should the project proceed to deep81 / wide243 shadow evidence.
