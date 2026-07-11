# Four Gates Reproduction Command Package

> **Historical package:** this v1.6.26 route is preserved for reproducibility.
> Its former evidence claim is superseded by the v1.7.11 `0 / HOLD` correction.

**Introduced:** `v1.6.26-alpha`  
**Status:** reproduction packaging gate, not new science  
**Native witness:** `C_Z = min(D, P, R, B)`

`v1.6.26-alpha` packaged the reproduction route for the Four Gates evidence line
as it was understood at that version.

It does not add a new gate, new candidate family, new physics claim, Zenodo route, or shadow-route revival.

## Why this version exists

At that time the evidence looked promising, but a research claim did not become useful just because internal reports looked good. A skeptical reader needed a clear path:

```text
clone / open repo
set PYTHONPATH
run a small smoke reproduction
know where the canonical heavy evidence lives
know what outputs to expect
know what the results prove and do not prove
```

This version provides that path.

## What the command package contains

The report tool writes:

```text
four_gates_reproduction_command_package_read.md
four_gates_small_reproduction_smoke.ps1
four_gates_full_reproduction_reference_and_fresh.ps1
four_gates_reproduction_manifest.csv
four_gates_reproduction_expected_outputs.csv
four_gates_reproduction_command_package_decision.json
four_gates_reproduction_command_package_bundle.zip
```

## Small smoke vs heavy evidence

The small script is intentionally not the final proof. It exists so a reviewer can test the pipeline shape without running the full heavy ladder.

The canonical evidence remains the completed line:

```text
v1.6.20 triad27 debt evidence
v1.6.21 deep81 / wide243 debt evidence
v1.6.22 fresh-seed reproduction
v1.6.25 anti-tautology audit
```

The full script regenerates reference and fresh seed evidence, then compares them. That is heavier and may take time.

## Expected qualitative pattern

The historical evidence route was expected to preserve this pattern:

```text
+1 earned-one visible
 0 relation debt visible
 0 return debt visible
-1 false-one pressure visible and demoted
final false-one crowns = 0
```

## Boundary

The historical v1.6.26 claim was bounded as follows; it has no current claim authority:

> In controlled synthetic adversarial fields, the Four Gates witness operationalizes a synthetic zero-zone gating principle.

This does not mean independent role-blind discovery, physical dimensional proof, quantum gravity, cosmology, or observed-universe bridge.

## CLI

```powershell
$P = ".\.venv\Scripts\python.exe"
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.four_gates_reproduction_command_package_report `
  --out runs\four_gates_reproduction_command_package_v1_6_26
```

Next locked gate:

```text
v1.6.27-alpha — Manuscript Correction Package
```
