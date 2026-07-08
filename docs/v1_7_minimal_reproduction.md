# v1.7 Minimal Reproduction

**Introduced:** `v1.7.9-alpha`  
**Purpose:** give a cold reviewer a small, non-heavy reproduction path before any 27/81/243 weather run.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Small path

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_v1_7_small_reproduction.ps1
```

This script performs:

```text
version check -> target test -> reviewer package builder -> required-output verification
```

Expected output directory:

```text
runs/v1_7_9_reviewer_reproduction_package
```

Expected key files:

```text
v1_7_reviewer_reproduction_package_read.md
v1_7_reviewer_reproduction_package_decision.json
v1_7_reviewer_path.csv
v1_7_reproduction_commands.csv
v1_7_expected_outputs.csv
v1_7_claim_boundary_card.csv
v1_7_evidence_manifest.csv
v1_7_reviewer_reproduction_package_bundle.zip
```

## Heavy path rule

The heavy holdout weather ladder must remain separated:

```text
triad27 first, inspect, then deep81, inspect, then wide243, inspect.
```

This was learned the hard way. An all-weather one-shot can bury the first wound under later noise. A valid handoff is evidence only if all required includes exist.

## What this does not do

This small reproduction path does not regenerate the full v1.7.6 heavy holdout ladder. It packages and verifies the reviewer route. The full heavy ladder remains optional reviewer pressure and must be run one rung at a time.
