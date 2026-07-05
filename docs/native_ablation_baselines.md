# Native Ablation Baselines

**Version:** `v1.6.15-alpha`  
**Status:** native ablation baselines enemy definitions / optional evaluation tool  
**Native witness:** `C_Z = min(D, P, R, B)`

This gate exists because `0 final false-one crowns` is not enough by itself. A witness can avoid false crowns by refusing everything, flattening zero, or hiding pressure. That is not ZeroGate intelligence. That is a very cautious brick with a clipboard.

The active scientific question is:

> Does the final trinary witness preserve earned-one, hold structured zero pressure, and demote false-one pressure better than raw, binary, and ablated alternatives?

## Baseline enemies

`v1.6.15-alpha` defines and tests the baseline enemies that the native witness must beat before the repaired native route can advance to four-corpus `triad27` evidence.

Required baseline families:

- `native_final_trinary_witness` — the current control witness.
- `dead_safe_no_crown` — refuses every crown; proves why safety without earned-one is not enough.
- `raw_expression_only` — treats raw expression pressure as final `+1`.
- `binary_raw_or_fail` — collapses trinary output into raw yes / generic failure.
- `no_zero_hold` — removes structured zero and promotes latent / relation / return debt pressure.
- `no_false_one_demotion` — removes trap / false-one demotion.
- `no_echo_independence` — removes relation-debt / borrowed-coherence witness.
- `no_return_debt_witness` — removes return-debt holding where visible or proxied.
- `no_relation_gate_raw` — removes relation as a raw expression gate.
- `no_return_gate_raw` — removes observed return as a raw expression gate.
- `average_gate_raw` — replaces weakest-gate `C_Z` with average-gate scoring.

## Pass condition

The native witness must win on all three trinary movements:

```text
+1 earned-one preservation
 0 structured zero hold: latent, relation debt, return debt, not-yet / quarantine
-1 false-one demotion without final false crowns
```

A witness that avoids false crowns only by refusing expression fails. A witness that preserves expression by crowning raw pressure fails. A witness that hides latent / relation / return debt in a generic failure bucket fails.

## Boundary

This is still controlled synthetic-field research software. It is not Zenodo correction yet, not a physics claim, not observed-universe bridge work, and not role-blind discovery.

The next route gate is `v1.6.16-alpha`: four-corpus `triad27` native evidence using these ablation enemies.
