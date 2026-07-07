# v1.7.7-alpha — Known Audit Routine

**Version:** `v1.7.7-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

This note explains why the Anti-Tautology Audit / Role-Dependence Check is placed before reviewer packaging.

A convincing result should not merely say, "the system passed because the system defines pass." It should survive familiar sanity checks used across empirical, computational, and model-evaluation work.

## Routine map

| ordinary sanity routine | ZeroGateSim translation |
|---|---|
| pre-registration | expected-output manifest frozen before result interpretation |
| train/test or reference/holdout split | fresh seeds, held-out profile variants, no reference-profile reuse |
| positive controls | earned-one remains visible; not a dead-safe no-crown system |
| negative controls | false-one pressure appears and is not crowned |
| label leakage check | candidate names and role-like identifiers are masked before lane interpretation |
| ablation / alternative explanation | raw-only, binary, dead-safe, average-gate, no-return, no-relation, no-zero-hold, and no-false-demotion witnesses remain named as enemies |
| mechanism trace | the audit explains each check, what it measures, and what would fail |
| bounded claim translation | controlled synthetic-field claim only |

## Why this belongs before reviewer packaging

Reviewer packaging should not be asked to sell raw output. It should package already-audited output.

So the order is:

```text
v1.7.6 fresh holdout ladder
-> v1.7.7 anti-tautology / role-dependence check
-> v1.7.8 reviewer / reproduction package
-> v1.7.9 core question closeout
```

The audit is not a new theory. It is a pressure gate between evidence and communication.
