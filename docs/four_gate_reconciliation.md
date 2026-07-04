# Four-Gate Reconciliation / Return-Adversary Audit

**Version:** `v1.6.4-alpha`  
**Status:** correction and reconciliation gate  
**Native witness:** `C_Z = min(D, P, R, B)`

This version resolves a foundation-language wound before the role-blind shadow line moves into holdout evaluation.

## What is being reconciled

ZeroGateSim's native mechanism has four gates:

```text
D = distinction
P = polarity
R = relation
B = observed return
```

The historical first-alpha proof record used three dedicated adversarial corpora:

```text
distinction
polarity
relation
```

Return was still present in the native witness as `B` and in the final earned-one stack, but it was not independently adversarialized as a fourth first-alpha corpus.

The corrected public sentence is:

> The historical first-alpha proof is a three-corpus pre-return adversarial proof with return measured as a native gate and final witness requirement; later controlled evidence adds dedicated return-adversary coverage.

## What must not be said

Do not say the historical first-alpha proof independently adversarialized all four gates.

Do not call the historical `wide243` record a role-blind discovery result.

Do not backdate the later `adversary_return` profile into the original first-alpha proof record.

## What later repo work adds

`v1.4.4-alpha` added four-gate adversary coverage planning:

```text
adversary_distinction
adversary_polarity
adversary_relation
adversary_return
```

`v1.5.5-alpha` preserved fresh controlled `deep81` and `wide243` four-gate evidence reports across dedicated distinction, polarity, relation, and return adversary corpora.

## Report command

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
.\.venv\Scripts\python.exe -m zerogate_sim.four_gate_reconciliation_report `
  --out runs\four_gate_reconciliation_v1_6_4 `
  --repo-root C:\dev\zerogate_sim
```

Expected outputs:

```text
four_gate_native_witness.csv
first_alpha_historical_corpora.csv
four_gate_followup_coverage.csv
four_gate_claim_language_audit.csv
four_gate_reconciliation_read.md
zenodo_version_correction_note.md
four_gate_reconciliation_audit.json
four_gate_reconciliation_bundle.zip
```

## Handoff rule

After local tests and this report are green, build the assistant test handoff under `runs/` and include the reconciliation read plus Zenodo correction note. The handoff ZIP is local continuation evidence, not Git truth.

## Boundary

This version does not run a new proof harness, change the simulator engine, mutate native math, or prove cosmology. It repairs the public claim lane before the next shadow-validation gate.
