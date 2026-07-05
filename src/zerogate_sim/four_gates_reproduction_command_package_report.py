from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.26-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
NEXT_GATE = "v1.6.27-alpha — Manuscript Correction Package"
CLAIM_CANDIDATE = (
    "In controlled synthetic adversarial fields, the Four Gates witness operationalizes "
    "a synthetic zero-zone gating principle: it delays premature expression, preserves "
    "earned expression, holds unresolved relation/return debt as structured zero, and "
    "demotes false-one pressure better than raw, binary, dead-safe, and ablated witnesses."
)

OUTPUT_FILES = {
    "read": "four_gates_reproduction_command_package_read.md",
    "decision": "four_gates_reproduction_command_package_decision.json",
    "quick_ps1": "four_gates_small_reproduction_smoke.ps1",
    "full_ps1": "four_gates_full_reproduction_reference_and_fresh.ps1",
    "manifest": "four_gates_reproduction_manifest.csv",
    "expected": "four_gates_reproduction_expected_outputs.csv",
    "audit": "four_gates_reproduction_command_package_audit.json",
    "bundle": "four_gates_reproduction_command_package_bundle.zip",
}

CANONICAL_EVIDENCE_ROWS = [
    {
        "evidence_gate": "triad27 debt evidence",
        "version": "v1.6.20-alpha",
        "canonical_folder": "runs/four_gates_triad27_debt_v1_6_20/four_gates_triad27_debt_evidence",
        "decision_file": "four_gates_triad27_debt_evidence_decision.json",
        "expected_decision": "expand_four_gates_triad27_debt_evidence",
        "role": "small-weather repaired debt evidence",
        "caveat": "small-weather only",
    },
    {
        "evidence_gate": "deep81 / wide243 debt evidence",
        "version": "v1.6.21-alpha",
        "canonical_folder": "runs/four_gates_deepwide_debt_v1_6_21/four_gates_deepwide_debt_evidence",
        "decision_file": "four_gates_deepwide_debt_evidence_decision.json",
        "expected_decision": "expand_four_gates_deepwide_debt_evidence",
        "role": "deeper-weather debt evidence",
        "caveat": "some debt candidate families inactive",
    },
    {
        "evidence_gate": "fresh-seed debt reproduction",
        "version": "v1.6.22-alpha",
        "canonical_folder": "runs/four_gates_fresh_seed_reproduction_v1_6_22",
        "decision_file": "four_gates_fresh_seed_debt_reproduction_decision.json",
        "expected_decision": "expand_four_gates_fresh_seed_debt_reproduction",
        "role": "qualitative reproduction on fresh seeds 9-17",
        "caveat": "latent overcrown did not reproduce; relation/return debt did",
    },
    {
        "evidence_gate": "anti-tautology audit",
        "version": "v1.6.25-alpha",
        "canonical_folder": "runs/four_gates_anti_tautology_audit_v1_6_25",
        "decision_file": "four_gates_anti_tautology_audit_decision.json",
        "expected_decision": "witness_bounded_role_shaped_but_witness_computed",
        "role": "role-dependence and witness-count dependence check",
        "caveat": "bounded designed-profile evidence, not independent role-blind discovery",
    },
]

EXPECTED_OUTPUT_ROWS = [
    {
        "package_part": "small smoke reproduction",
        "path": "runs/four_gates_small_reproduction_v1_6_26/four_gates_triad27_debt_evidence/four_gates_triad27_debt_evidence_decision.json",
        "must_exist": True,
        "meaning": "small triad27 pipeline smoke; not canonical heavy evidence",
    },
    {
        "package_part": "small smoke reproduction",
        "path": "runs/four_gates_small_reproduction_v1_6_26/four_gates_triad27_debt_evidence/four_gates_triad27_debt_evidence_read.md",
        "must_exist": True,
        "meaning": "human-readable smoke report",
    },
    {
        "package_part": "full reference evidence",
        "path": "runs/four_gates_repro_reference_v1_6_26/four_gates_deepwide_debt_evidence/four_gates_deepwide_debt_evidence_decision.json",
        "must_exist": True,
        "meaning": "reference seeds 0-8 deep81/wide243 debt evidence",
    },
    {
        "package_part": "full fresh evidence",
        "path": "runs/four_gates_repro_fresh_v1_6_26/four_gates_deepwide_debt_evidence/four_gates_deepwide_debt_evidence_decision.json",
        "must_exist": True,
        "meaning": "fresh seeds 9-17 deep81/wide243 debt evidence",
    },
    {
        "package_part": "full reproduction comparison",
        "path": "runs/four_gates_repro_comparison_v1_6_26/four_gates_fresh_seed_debt_reproduction_decision.json",
        "must_exist": True,
        "meaning": "reference-vs-fresh qualitative reproduction decision",
    },
]


def _small_reproduction_script() -> str:
    return r'''$ErrorActionPreference = "Stop"

function Run($Name, [scriptblock]$Command) {
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$Repo = "C:\dev\zerogate_sim"
Set-Location $Repo
Remove-Module PSReadLine -ErrorAction SilentlyContinue

$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { $P = "python" }

$env:PYTHONPATH = (Join-Path (Get-Location) "src")
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

Run "confirm v1.6.26 or later" {
    & $P -c "import zerogate_sim; print(zerogate_sim.__version__)"
}

$Base = "runs\four_gates_small_reproduction_v1_6_26"
if (Test-Path $Base) { Remove-Item $Base -Recurse -Force }

# This is a SMALL PIPELINE SMOKE, not the canonical heavy evidence.
# It uses one seed per matrix so a reviewer can see the command shape and output structure.
# The canonical heavy evidence remains the v1.6.20-v1.6.25 evidence line.

Run "small matrix distinction triad27" {
    & $P -m zerogate_sim.matrix --profile triad27 --candidate-profile adversary_distinction --start-seed 0 --count 1 --steps 120 --out "$Base\matrix\native\distinction_triad27"
}
Run "small matrix polarity triad27" {
    & $P -m zerogate_sim.matrix --profile triad27 --candidate-profile adversary_polarity --start-seed 0 --count 1 --steps 120 --out "$Base\matrix\native\polarity_triad27"
}
Run "small matrix relation triad27" {
    & $P -m zerogate_sim.matrix --profile triad27 --candidate-profile adversary_relation --start-seed 0 --count 1 --steps 120 --out "$Base\matrix\native\relation_triad27"
}
Run "small matrix return triad27" {
    & $P -m zerogate_sim.matrix --profile triad27 --candidate-profile adversary_return --start-seed 0 --count 1 --steps 120 --out "$Base\matrix\native\return_triad27"
}
Run "small matrix Four Gates debt triad27" {
    & $P -m zerogate_sim.matrix --profile triad27 --candidate-profile four_gates_debt --start-seed 0 --count 1 --steps 120 --out "$Base\matrix\debt\four_gates_debt_triad27"
}
Run "small Four Gates triad27 debt report" {
    & $P -m zerogate_sim.four_gates_triad27_debt_evidence_report `
      --matrix-dir "$Base\matrix\native\distinction_triad27" `
      --matrix-dir "$Base\matrix\native\polarity_triad27" `
      --matrix-dir "$Base\matrix\native\relation_triad27" `
      --matrix-dir "$Base\matrix\native\return_triad27" `
      --debt-matrix-dir "$Base\matrix\debt\four_gates_debt_triad27" `
      --out "$Base\four_gates_triad27_debt_evidence"
}

Write-Host "`n=== SMALL REPRODUCTION SMOKE COMPLETE ===" -ForegroundColor Green
Write-Host "Read: C:\dev\zerogate_sim\$Base\four_gates_triad27_debt_evidence\four_gates_triad27_debt_evidence_read.md"
'''


def _full_reproduction_script() -> str:
    return r'''$ErrorActionPreference = "Stop"

function Run($Name, [scriptblock]$Command) {
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$Repo = "C:\dev\zerogate_sim"
Set-Location $Repo
Remove-Module PSReadLine -ErrorAction SilentlyContinue

$P = ".\.venv\Scripts\python.exe"
if (!(Test-Path $P)) { $P = "python" }

$env:PYTHONPATH = (Join-Path (Get-Location) "src")
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

Run "confirm v1.6.26 or later" {
    & $P -c "import zerogate_sim; print(zerogate_sim.__version__)"
}

function New-DeepWideEvidence($Base, $StartSeed, $Label) {
    if (Test-Path $Base) { Remove-Item $Base -Recurse -Force }

    Run "$Label matrix distinction deep81" { & $P -m zerogate_sim.matrix --profile deep81 --candidate-profile adversary_distinction --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\deep81\native\distinction_deep81" }
    Run "$Label matrix polarity deep81" { & $P -m zerogate_sim.matrix --profile deep81 --candidate-profile adversary_polarity --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\deep81\native\polarity_deep81" }
    Run "$Label matrix relation deep81" { & $P -m zerogate_sim.matrix --profile deep81 --candidate-profile adversary_relation --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\deep81\native\relation_deep81" }
    Run "$Label matrix return deep81" { & $P -m zerogate_sim.matrix --profile deep81 --candidate-profile adversary_return --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\deep81\native\return_deep81" }
    Run "$Label matrix debt deep81" { & $P -m zerogate_sim.matrix --profile deep81 --candidate-profile four_gates_debt --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\deep81\debt\four_gates_debt_deep81" }

    Run "$Label matrix distinction wide243" { & $P -m zerogate_sim.matrix --profile wide243 --candidate-profile adversary_distinction --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\wide243\native\distinction_wide243" }
    Run "$Label matrix polarity wide243" { & $P -m zerogate_sim.matrix --profile wide243 --candidate-profile adversary_polarity --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\wide243\native\polarity_wide243" }
    Run "$Label matrix relation wide243" { & $P -m zerogate_sim.matrix --profile wide243 --candidate-profile adversary_relation --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\wide243\native\relation_wide243" }
    Run "$Label matrix return wide243" { & $P -m zerogate_sim.matrix --profile wide243 --candidate-profile adversary_return --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\wide243\native\return_wide243" }
    Run "$Label matrix debt wide243" { & $P -m zerogate_sim.matrix --profile wide243 --candidate-profile four_gates_debt --start-seed $StartSeed --count 9 --steps 240 --out "$Base\matrix\wide243\debt\four_gates_debt_wide243" }

    Run "$Label deepwide debt evidence report" {
        & $P -m zerogate_sim.four_gates_deepwide_debt_evidence_report `
          --deep81-matrix-dir "$Base\matrix\deep81\native\distinction_deep81" `
          --deep81-matrix-dir "$Base\matrix\deep81\native\polarity_deep81" `
          --deep81-matrix-dir "$Base\matrix\deep81\native\relation_deep81" `
          --deep81-matrix-dir "$Base\matrix\deep81\native\return_deep81" `
          --deep81-debt-matrix-dir "$Base\matrix\deep81\debt\four_gates_debt_deep81" `
          --wide243-matrix-dir "$Base\matrix\wide243\native\distinction_wide243" `
          --wide243-matrix-dir "$Base\matrix\wide243\native\polarity_wide243" `
          --wide243-matrix-dir "$Base\matrix\wide243\native\relation_wide243" `
          --wide243-matrix-dir "$Base\matrix\wide243\native\return_wide243" `
          --wide243-debt-matrix-dir "$Base\matrix\wide243\debt\four_gates_debt_wide243" `
          --out "$Base\four_gates_deepwide_debt_evidence"
    }
}

$ReferenceBase = "runs\four_gates_repro_reference_v1_6_26"
$FreshBase = "runs\four_gates_repro_fresh_v1_6_26"
$CompareOut = "runs\four_gates_repro_comparison_v1_6_26"
if (Test-Path $CompareOut) { Remove-Item $CompareOut -Recurse -Force }

New-DeepWideEvidence $ReferenceBase 0 "reference seeds 0-8"
New-DeepWideEvidence $FreshBase 9 "fresh seeds 9-17"

Run "compare reference and fresh reproduction" {
    & $P -m zerogate_sim.four_gates_fresh_seed_debt_reproduction_report `
      --reference-evidence-dir "$ReferenceBase\four_gates_deepwide_debt_evidence" `
      --fresh-evidence-dir "$FreshBase\four_gates_deepwide_debt_evidence" `
      --reference-label seed-range-0-8 `
      --fresh-label fresh-seed-range-9-17 `
      --out $CompareOut
}

Write-Host "`n=== FULL REPRODUCTION COMPLETE ===" -ForegroundColor Green
Write-Host "Comparison: C:\dev\zerogate_sim\$CompareOut\four_gates_fresh_seed_debt_reproduction_read.md"
'''


def _build_readme() -> str:
    return "\n".join(
        [
            "# Four Gates Reproduction Command Package",
            "",
            f"**Version:** `{CURRENT_VERSION}`",
            f"**Native witness:** `{NATIVE_WITNESS}`",
            "**Purpose:** provide a clean command path for reproduction without adding a new scientific claim.",
            "",
            "## Claim boundary",
            "",
            CLAIM_CANDIDATE,
            "",
            "This package does not prove cosmology, physical dimensional genesis, quantum gravity, or an observed-universe bridge. It packages controlled synthetic-field reproduction commands and expected outputs.",
            "",
            "## Package parts",
            "",
            "- `four_gates_small_reproduction_smoke.ps1` — small triad27 pipeline smoke. It checks that a skeptical reader can run the command shape and receive the expected report structure. It is not canonical heavy evidence.",
            "- `four_gates_full_reproduction_reference_and_fresh.ps1` — full reference/fresh deep81 and wide243 reproduction path using seed ranges `0-8` and `9-17`.",
            "- `four_gates_reproduction_manifest.csv` — canonical current evidence folders and expected decisions.",
            "- `four_gates_reproduction_expected_outputs.csv` — output paths the scripts should produce.",
            "",
            "## Pass/fail standard",
            "",
            "A reproduction command package passes as a package if it is explicit, bounded, and runnable from a clean local repo. The science claim remains bounded by the evidence decisions it points to.",
            "",
            "Expected qualitative pattern:",
            "",
            "```text",
            "+1 earned-one visible",
            " 0 relation debt visible",
            " 0 return debt visible",
            "-1 false-one pressure visible and demoted",
            "final false-one crowns = 0",
            "```",
            "",
            "## Honest caveat",
            "",
            "The anti-tautology audit bounded the claim as designed-profile / role-shaped but witness-counted and reproducible. This is valid controlled synthetic-field evidence; it is not independent role-blind discovery.",
            "",
            f"## Next gate",
            "",
            f"After this package is green, the locked next gate is `{NEXT_GATE}`.",
            "",
        ]
    )


def build_reproduction_command_package(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(Path(out_dir))
    read_path = out_dir / OUTPUT_FILES["read"]
    decision_path = out_dir / OUTPUT_FILES["decision"]
    quick_path = out_dir / OUTPUT_FILES["quick_ps1"]
    full_path = out_dir / OUTPUT_FILES["full_ps1"]
    manifest_path = out_dir / OUTPUT_FILES["manifest"]
    expected_path = out_dir / OUTPUT_FILES["expected"]
    audit_path = out_dir / OUTPUT_FILES["audit"]

    read_path.write_text(_build_readme(), encoding="utf-8", newline="\n")
    quick_path.write_text(_small_reproduction_script(), encoding="utf-8", newline="\n")
    full_path.write_text(_full_reproduction_script(), encoding="utf-8", newline="\n")
    write_dict_rows_csv(manifest_path, CANONICAL_EVIDENCE_ROWS)
    write_dict_rows_csv(expected_path, EXPECTED_OUTPUT_ROWS)

    decision: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "package_kind": "four_gates_reproduction_command_package",
        "native_witness_unchanged": NATIVE_WITNESS,
        "claim_candidate": CLAIM_CANDIDATE,
        "small_reproduction_script": OUTPUT_FILES["quick_ps1"],
        "full_reproduction_script": OUTPUT_FILES["full_ps1"],
        "canonical_evidence_count": len(CANONICAL_EVIDENCE_ROWS),
        "expected_output_count": len(EXPECTED_OUTPUT_ROWS),
        "role_dependence_boundary": "designed_profile_role_shaped_but_witness_counted",
        "stronger_claim_not_earned": "independent role-blind discovery",
        "allowed_next_gate": NEXT_GATE,
        "decision": "expand_reproduction_command_package_ready_for_manuscript_correction",
        "forbidden_claims": [
            "cosmology proof",
            "physical dimensional genesis proof",
            "quantum gravity proof",
            "observed-universe bridge",
            "role-blind discovery",
            "spacetime metric claim",
        ],
    }
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "version": CURRENT_VERSION,
        "files_written": [OUTPUT_FILES[key] for key in ("read", "decision", "quick_ps1", "full_ps1", "manifest", "expected")],
        "native_witness_unchanged": NATIVE_WITNESS,
        "notes": [
            "This package adds commands and expected outputs, not new evidence.",
            "The quick script is a smoke test, not canonical heavy proof.",
            "The full script is the heavy reference/fresh reproduction path.",
        ],
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    bundle_path = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="four_gates_reproduction_command_package_bundle",
    )
    return {
        "read": read_path,
        "decision": decision_path,
        "quick_ps1": quick_path,
        "full_ps1": full_path,
        "manifest": manifest_path,
        "expected": expected_path,
        "audit": audit_path,
        "bundle": bundle_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Four Gates reproduction command package.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for the command package.")
    args = parser.parse_args(argv)
    outputs = build_reproduction_command_package(args.out)
    print("Four Gates reproduction command package written:")
    for key, path in outputs.items():
        print(f"- {key}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
