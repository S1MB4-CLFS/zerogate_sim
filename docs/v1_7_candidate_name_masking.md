# v1.7.6-alpha — Candidate Name Masking

**Version:** `v1.7.6-alpha`  
**Native witness:** `C_Z = min(D, P, R, B)`

Candidate names can leak design intent. In a fresh holdout challenge, names must not carry lane assignment.

## Rule

```text
candidate semantic name -> stable masked id
```

The masked id must preserve trace without revealing whether the candidate is expected to earn, hold, create relation debt, create return debt, or expose false-one pressure.

## Allowed claim

Candidate-name masking reduces one leakage path inside a controlled synthetic-field holdout.

## Forbidden claim

Candidate-name masking does not solve role-blind discovery.

## Stop condition

If the lane can only be interpreted because the candidate name tells the story, the holdout remains `0` or `-1`, not `+1`.

Candidate-name masking is not role-blind discovery. It is a controlled holdout hygiene gate that removes obvious name/role hints while preserving numeric witness surfaces.


Post-holdout audit note: `v1.7.7-alpha` checks these holdout expectations for anti-tautology and role-dependence pressure before reviewer packaging.
