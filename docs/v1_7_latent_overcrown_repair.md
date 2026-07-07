# v1.7.2-alpha — Latent Overcrown Repair

**Version:** `v1.7.2-alpha`  
**Status:** explicit HOLD; no ghost lane, no fake crown  
**Native witness:** `C_Z = min(D, P, R, B)`

## Problem

Latent overcrown has two truths that must not be collapsed.

First, it is historically real inside the archived first-research-alpha proof record. That line held `2,442` of `2,442` latent overcrown pressures in zero.

Second, in the current Four Gates debt line, it became seed-sensitive. The current evidence index records that latent overcrown did not reproduce cleanly in the fresh-seed debt reproduction path.

Both facts matter.

## Repair

`v1.7.2-alpha` does not erase latent overcrown and does not let it pretend to be cleanly reproduced current evidence.

The repaired status is:

```text
latent_overcrown.status = fragile_historical_pressure_explicit_hold_until_reproduced_or_narrowed
```

## Decision rule

```text
If later v1.7 evidence reproduces latent overcrown, keep it in the full closeout sentence.
If later v1.7 evidence does not reproduce it, v1.7.8 must close partial or narrow the full-answer claim.
If any report silently counts latent overcrown as reproduced current evidence, stop and repair the claim surface.
```

## Why this is not a failure

A clean `0` is not a loss. It means the witness is refusing a premature crown. The repair preserves the scar instead of painting it gold and asking the reviewer not to notice the smell.

## Forbidden readings

- Do not say latent overcrown is gone.
- Do not say latent overcrown is fully reproduced in the current evidence line.
- Do not use first-alpha historical support as a substitute for current v1.7 closeout evidence.
- Do not soften false-one pressure into latent overcrown to avoid a resist result.
- Do not make taxonomy cleaner than the evidence.
