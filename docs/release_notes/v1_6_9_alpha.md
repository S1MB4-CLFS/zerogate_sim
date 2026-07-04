# v1.6.9-alpha — Shadow Discrimination Repair and README Reorganization

`v1.6.9-alpha` responds to the hardened triad27 result: the frozen shadow score saw pressure density but did not yet earn false-one-kind discrimination beyond simple baselines.

## Added

- `src/zerogate_sim/shadow_discrimination_report.py`
- `tests/test_shadow_discrimination_report.py`
- `docs/shadow_discrimination_repair.md`
- `docs/test_truth_and_handoff_boundary.md`
- `docs/version_truth.md`

## Changed

- README reorganized around project identity, why it exists, the first three visual maps, native math witness, active route, evidence state, and then reference material.
- Long README lists for test truth / handoff boundary and version truth moved into dedicated Markdown files.
- Runtime support boundary remains in `docs/runtime_ci_support.md` and is now linked with the other boundary/reference docs near the end of README.
- `shadow_score_read.md` generation no longer says the next step is only `v1.6.3-alpha`; it now points to baseline, weather-hardening, and discrimination reports.
- `docs/shadow_triad27_hardened_evidence.md` command example repaired so `relation_triad27` and `return_triad27` paths do not contain carriage-return corruption.

## Boundary

No native math mutation.

```text
C_Z = min(D, P, R, B)
```

No score retuning. No role-blind discovery claim. No detector closeout. This release adds a sharper witness for what the frozen score still fails to discriminate.
