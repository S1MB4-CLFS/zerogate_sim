# v1.7.2-alpha — Lane Taxonomy and Latent Overcrown Repair

`v1.7.2-alpha` locks the core lane taxonomy before the baseline and ablation falsifier matrix.

## Added

- `docs/v1_7_lane_taxonomy.md`
- `docs/v1_7_latent_overcrown_repair.md`
- `docs/v1_7_relation_return_debt_specificity.md`
- `docs/v1_7_lane_visibility_decision_rules.md`
- `src/zerogate_sim/v1_7_lane_taxonomy.py`
- `tests/test_v1_7_lane_taxonomy.py`
- CLI: `zerogate-v1-7-lane-taxonomy`

## Decision

```text
witness_lane_taxonomy_locked_latent_overcrown_held
```

The lane set is now explicit:

```text
+1 earned-one
raw expression pressure
0 latent overcrown — fragile / historical / HOLD until reproduced or narrowed
0 relation debt
0 return debt
-1 false-one pressure
```

## Boundary

no new heavy evidence crown.  
No native witness mutation.  
No role-blind discovery claim.  
No manuscript v2 start.  
No physics, topology, dimension, or observed-universe claim.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Next

`v1.7.3-alpha — Baseline and Ablation Falsifier Matrix`.
