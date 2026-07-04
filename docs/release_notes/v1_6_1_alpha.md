# v1.6.1-alpha — Role-Stripped Feature Extraction Report

`v1.6.1-alpha` adds the first report reader for the role-blind shadow line.

## Added

- `src/zerogate_sim/role_stripped_feature_report.py`;
- console script `zerogate-role-stripped-features`;
- `docs/role_stripped_feature_extraction.md`;
- `docs/assets/role_stripped_feature_extraction_card.svg`;
- README and ROADMAP pointers;
- tests for feature/target separation and forbidden-field boundaries.

## What it does

The report reads completed seed-block and witness-ablation summaries and writes:

```text
role_stripped_profile_features.csv
role_stripped_family_features.csv
role_stripped_evaluation_targets.csv
role_stripped_feature_read.md
role_stripped_forbidden_field_audit.json
role_stripped_feature_bundle.zip
```

Feature files are stripped of designed truth-role shortcut fields. Evaluation targets are deliberately separate and must not be loaded by any future role-blind scorer.

## Boundary

No native gate changed. No engine crown behavior changed. No role-blind discovery is claimed.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

`v1.6.1-alpha` prepares clean inputs for `v1.6.2-alpha`, where a transparent shadow score may be prototyped as report-only.
