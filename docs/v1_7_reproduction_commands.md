# v1.7.9 Reproduction Commands

**Version:** `v1.7.9-alpha`

This file records the safe reproduction rhythm for the v1.7 reviewer package.

Native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Law

```text
smoke first
triad27 first weather rung
inspect
then deep81
inspect
then wide243
inspect
only then combined index
```

No all-weather one-shot belongs in the reviewer path until the separate rungs prove the plumbing.

## Build the reviewer package smoke

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { $P = "python" }
& $P -m zerogate_sim.v1_7_reviewer_reproduction_package --out runs\v1_7_9_reviewer_reproduction_package
```

This writes the package readme, manifest, expected-output map, command map, and generated helper scripts.

## Run the generated scripts

After the package smoke succeeds, inspect the generated PowerShell files in:

```text
runs/v1_7_9_reviewer_reproduction_package/
```

Run order:

```powershell
powershell -ExecutionPolicy Bypass -File runs\v1_7_9_reviewer_reproduction_package\run_v1_7_9_reviewer_smoke.ps1
powershell -ExecutionPolicy Bypass -File runs\v1_7_9_reviewer_reproduction_package\run_v1_7_9_triad27_reproduction.ps1
# inspect triad27
powershell -ExecutionPolicy Bypass -File runs\v1_7_9_reviewer_reproduction_package\run_v1_7_9_deep81_reproduction.ps1
# inspect deep81
powershell -ExecutionPolicy Bypass -File runs\v1_7_9_reviewer_reproduction_package\run_v1_7_9_wide243_reproduction.ps1
# inspect wide243
```

The rung scripts are separated by design. They do not close the core question.

## What to upload for review

Upload strict handoff ZIPs only after each rung completes and prints the exact ZIP path. A missing required include invalidates the handoff.

## Boundary

This command package is a reproduction and inspection package. It does not claim role-blind discovery, independent generator validation, external empirical validation, or physical dimensional genesis.
