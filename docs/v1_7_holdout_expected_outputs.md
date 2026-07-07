# v1.7.6-alpha — Holdout Expected Outputs

**Version:** `v1.7.6-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

The holdout expected-output manifest must be written before the run. Its job is not to predict every count exactly. Its job is to state which lanes must remain visible and which stop conditions block closeout.

## Required manifest columns

```text
challenge_id
weather_rung
fresh_seed_block
heldout_profile_variant
candidate_names_masked
expected_manifest_frozen_before_run
final_earned_one_events
raw_expression_pressure
latent_overcrown
relation_debt
return_debt
false_one_pressure
final_false_one_crowns
```

## Interpretation rule

A successful row is not merely a row with zero false crowns. It must also avoid dead-safe behavior by preserving earned-one and showing the relevant pressure/debt lanes when the held-out profile is designed to activate them.

## Required lane behavior

| lane | required holdout behavior |
|---|---|
| earned-one | final +1 remains possible when return-depth, lineage, and independence are paid |
| raw expression pressure | remains visible as pressure before final witness |
| latent overcrown | stays structured zero / HOLD when activated |
| relation debt | visible when relation is borrowed, unstable, global-only, or under-owned |
| return debt | visible when `Gamma = D * P * R` is high but observed return is incomplete |
| false-one pressure | remains visible enough to demote before final crown |
| final false-one crowns | must remain `0`; Any final false-one crown blocks later `+1` closeout language |

A partial rung result may be useful. It is not the full v1.7 answer.


Post-holdout audit note: `v1.7.7-alpha` checks these holdout expectations for anti-tautology and role-dependence pressure before reviewer packaging.
