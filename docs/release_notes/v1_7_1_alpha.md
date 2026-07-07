# v1.7.1-alpha — Return Gate Trace Lock

`v1.7.1-alpha` locks the return-gate trace before heavier v1.7 evidence work.

## Added

- `docs/v1_7_return_gate_trace.md`
- `docs/v1_7_return_potential_vs_observed_return.md`
- `docs/v1_7_return_debt_taxonomy.md`
- `docs/v1_7_return_gate_forbidden_readings.md`
- `src/zerogate_sim/v1_7_return_gate_trace.py`
- `zerogate-v1-7-return-gate-trace`
- `tests/test_v1_7_return_gate_trace_lock.py`

## Locked trace

```text
Gamma = D * P * R
Gamma is return-potential
B is observed return
B is not zero crossing alone
C_Z = min(D, P, R, B)
return debt is structured zero
```

## Claim boundary

This release adds no new science evidence crown, does not start manuscript v2, does not revive shadow, does not claim role-blind discovery, and does not claim physical gravity, cosmology, or observed-universe proof.

## Next

`v1.7.2-alpha` should handle lane taxonomy and latent-overcrown repair or demotion.
