from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.10-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
DECISION = "reviewer_reproduction_package_locked_not_closeout"
GATE_KIND = "reviewer_start_here_reproduction_package_not_closeout"
NEXT_GATE = "v1.7.10-alpha — Core Question Closeout"

OUTPUT_FILES = {
    "read": "v1_7_reviewer_reproduction_package_read.md",
    "decision": "v1_7_reviewer_reproduction_package_decision.json",
    "reviewer_path": "v1_7_reviewer_path.csv",
    "reproduction_commands": "v1_7_reproduction_commands.csv",
    "expected_outputs": "v1_7_expected_outputs.csv",
    "handoff_manifest": "v1_7_handoff_manifest.csv",
    "claim_boundary": "v1_7_claim_boundary_card.csv",
    "evidence_manifest": "v1_7_evidence_manifest.csv",
    "triad_script": "run_v1_7_9_triad27_reproduction.ps1",
    "deep_script": "run_v1_7_9_deep81_reproduction.ps1",
    "wide_script": "run_v1_7_9_wide243_reproduction.ps1",
    "combined_script": "run_v1_7_9_combined_index.ps1",
    "bundle": "v1_7_reviewer_reproduction_package_bundle.zip",
}

REVIEWER_PATH_ROWS = [
    {"step": "1", "artifact": "README.md", "role": "project face", "reason": "mechanism and math before evidence cards"},
    {"step": "2", "artifact": "REVIEWER_START_HERE.md", "role": "narrow reviewer door", "reason": "one clear path before full repo exploration"},
    {"step": "3", "artifact": "docs/v1_7_reviewer_reproduction_package.md", "role": "package contract", "reason": "bounds the package before commands"},
    {"step": "4", "artifact": "docs/v1_7_reproduction_commands.md", "role": "command map", "reason": "keeps triad27, deep81, and wide243 separate"},
    {"step": "5", "artifact": "docs/v1_7_expected_outputs.md", "role": "expected outputs", "reason": "full/compressed/visual/evaluator/handoff layers"},
    {"step": "6", "artifact": "docs/v1_7_evidence_manifest.md", "role": "evidence manifest", "reason": "current snapshot without closeout overclaim"},
]

REPRODUCTION_COMMAND_ROWS = [
    {"command_id": "small_package_smoke", "step": "1", "command": "powershell -ExecutionPolicy Bypass -File .\\scripts\\run_v1_7_small_reproduction.ps1", "purpose": "build reviewer package report and run target tests"},
    {"command_id": "target_test", "step": "2", "command": "python -m pytest tests/test_v1_7_reviewer_path.py -q", "purpose": "verify reviewer package contract"},
    {"command_id": "full_tests", "step": "3", "command": "python -m pytest -q", "purpose": "full suite before commit/tag"},
    {"command_id": "triad27_heavy_rung", "step": "4", "command": "run triad27 only, inspect report/evaluator/handoff", "purpose": "local expression weather"},
    {"command_id": "deep81_heavy_rung", "step": "5", "command": "run deep81 only after triad27 inspection", "purpose": "perturbation / late-shock bridge"},
    {"command_id": "wide243_heavy_rung", "step": "6", "command": "run wide243 only after deep81 inspection", "purpose": "temporal-depth stress"},
]

EXPECTED_OUTPUT_ROWS = [
    {"layer": "full_output", "required_file": "*_full_output_report.md or evidence read.md", "why_required": "detailed system output"},
    {"layer": "compressed_summary", "required_file": "*_summary_read.md / *_row.csv / *_top_card.md", "why_required": "human reviewer state"},
    {"layer": "visuals", "required_file": "*_top_card.html / matrix_field_atlas.png / docs/assets/*_card.svg", "why_required": "orientation without replacing evidence"},
    {"layer": "machine", "required_file": "*_decision.json / *_evaluation.csv", "why_required": "machine-checkable decision path"},
    {"layer": "handoff", "required_file": "assistant_test_handoff_*.zip", "why_required": "strict include bundle; A false handoff is a false crown"},
]

HANDOFF_MANIFEST_ROWS = [
    {"handoff_layer": "full-output-report", "purpose": "complete system output report and machine-readable matrix/evaluator files"},
    {"handoff_layer": "compressed-summary", "purpose": "small reviewer summary, row, top-card, and JSON"},
    {"handoff_layer": "visual-output", "purpose": "human-friendly visual card and field-atlas artifacts"},
    {"handoff_layer": "report-label-note", "purpose": "make historical internal report labels explicit without changing active package boundary"},
]


OUTPUT_LAYERS = [
    {"layer": "full_output", "meaning": "machine and human-readable full evidence from each rung"},
    {"layer": "compressed_summary", "meaning": "small row and top-card text for fast inspection"},
    {"layer": "visuals", "meaning": "human-facing cards and field atlases"},
    {"layer": "handoff", "meaning": "strict ZIP carrying the reviewable state"},
]

COMMAND_MAP = [
    {"command_level": "smoke", "script": "run_v1_7_9_reviewer_smoke.ps1", "run_order": "first", "purpose": "package smoke before weather rungs"},
    {"command_level": "triad27", "script": "run_v1_7_9_triad27_reproduction.ps1", "run_order": "second", "purpose": "smallest weather rung"},
    {"command_level": "deep81", "script": "run_v1_7_9_deep81_reproduction.ps1", "run_order": "third", "purpose": "perturbation bridge rung"},
    {"command_level": "wide243", "script": "run_v1_7_9_wide243_reproduction.ps1", "run_order": "fourth", "purpose": "temporal-depth rung"},
]

CLAIM_BOUNDARY_ROWS = [
    {"claim_lane": "allowed", "wording": "controlled synthetic-field reviewer reproduction package", "why": "v1.7.9 packages inspection and reproduction paths"},
    {"claim_lane": "allowed", "wording": "local triad27/deep81/wide243 holdout snapshot is evidence pressure", "why": "three rungs were inspected separately with zero final false-one crowns"},
    {"claim_lane": "forbidden", "wording": "core question closed", "why": "closeout waits for v1.7.10-alpha"},
    {"claim_lane": "forbidden", "wording": "role-blind discovery solved", "why": "role-dependence remains bounded"},
    {"claim_lane": "forbidden", "wording": "physics, cosmology, observed-universe, or dimensional-origin proof", "why": "evidence remains controlled synthetic-field software evidence"},
]

EVIDENCE_MANIFEST_ROWS = [
    {"artifact": "REVIEWER_START_HERE.md", "evidence": "reviewer start page", "rung": "package", "status": "tracked reviewer door", "earned_one": 0, "raw_expression_pressure": 0, "latent_overcrown": 0, "relation_debt": 0, "return_debt": 0, "false_one_pressure": 0, "final_false_one_crowns": 0, "boundary": "path artifact, not evidence result"},
    {"artifact": "docs/v1_7_minimal_reproduction.md", "evidence": "minimal reproduction guide", "rung": "package", "status": "tracked reproduction path", "earned_one": 0, "raw_expression_pressure": 0, "latent_overcrown": 0, "relation_debt": 0, "return_debt": 0, "false_one_pressure": 0, "final_false_one_crowns": 0, "boundary": "small-path guide, not heavy evidence"},
    {"artifact": "docs/v1_7_expected_outputs.md", "evidence": "expected output layer map", "rung": "package", "status": "tracked output contract", "earned_one": 0, "raw_expression_pressure": 0, "latent_overcrown": 0, "relation_debt": 0, "return_debt": 0, "false_one_pressure": 0, "final_false_one_crowns": 0, "boundary": "full/compressed/visual/machine/handoff map"},
    {"artifact": "docs/v1_7_claim_boundary_card.md", "evidence": "claim boundary card", "rung": "package", "status": "tracked boundary surface", "earned_one": 0, "raw_expression_pressure": 0, "latent_overcrown": 0, "relation_debt": 0, "return_debt": 0, "false_one_pressure": 0, "final_false_one_crowns": 0, "boundary": "core v1.7 question remains unclosed until v1.7.10"},
    {"artifact": "docs/v1_7_evidence_manifest.md", "evidence": "evidence manifest", "rung": "package", "status": "tracked evidence index", "earned_one": 0, "raw_expression_pressure": 0, "latent_overcrown": 0, "relation_debt": 0, "return_debt": 0, "false_one_pressure": 0, "final_false_one_crowns": 0, "boundary": "manifest artifact, not closeout"},
    {"artifact": "docs/v1_7_latest_holdout_snapshot.md", "evidence": "triad27 fresh holdout snapshot", "rung": "triad27", "status": "local assistant-handoff evidence inspected", "earned_one": 839, "raw_expression_pressure": 1283, "latent_overcrown": 9, "relation_debt": 39, "return_debt": 75, "false_one_pressure": 321, "final_false_one_crowns": 0, "boundary": "not packaged reproduction, not closeout"},
    {"artifact": "docs/v1_7_latest_holdout_snapshot.md", "evidence": "deep81 fresh holdout snapshot", "rung": "deep81", "status": "local assistant-handoff evidence inspected", "earned_one": 1950, "raw_expression_pressure": 3012, "latent_overcrown": 9, "relation_debt": 120, "return_debt": 126, "false_one_pressure": 807, "final_false_one_crowns": 0, "boundary": "not packaged reproduction, not closeout"},
    {"artifact": "docs/v1_7_latest_holdout_snapshot.md", "evidence": "wide243 fresh holdout snapshot", "rung": "wide243", "status": "local assistant-handoff evidence inspected", "earned_one": 9417, "raw_expression_pressure": 14058, "latent_overcrown": 21, "relation_debt": 465, "return_debt": 612, "false_one_pressure": 3543, "final_false_one_crowns": 0, "boundary": "not packaged reproduction, not closeout"},
]



def _rung_script(rung: str) -> str:
    return f'''$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# v1.7 reviewer reproduction helper — {rung} only.
# No all-weather one-shot. Run, inspect, then decide whether to continue.

function Run($Name, [scriptblock]$Command) {{
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {{ throw "$Name failed with exit code $LASTEXITCODE" }}
}}

Set-Location C:\\dev\\zerogate_sim
Remove-Module PSReadLine -ErrorAction SilentlyContinue
$P = ".\\.venv\\Scripts\\python.exe"
if (!(Test-Path $P)) {{ $P = "python" }}
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

Run "version check" {{
    $Version = (& $P -c "import zerogate_sim; print(zerogate_sim.__version__)").Trim()
    if ($Version -ne "1.7.10-alpha") {{ throw "Expected 1.7.10-alpha. Found: $Version" }}
}}

Write-Host "`n{rung} reproduction helper reached safe start." -ForegroundColor Green
Write-Host "Use docs/v1_7_reproduction_commands.md for the full rung command path and expected outputs." -ForegroundColor Green
'''


def _combined_script() -> str:
    return r'''$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Combined index is navigation only. It must not replace separate rung records.
Set-Location C:\\dev\\zerogate_sim
Write-Host "Build combined reviewer index only after triad27, deep81, and wide243 handoffs exist." -ForegroundColor Green
'''


def _write_read(path: Path) -> None:
    lines = [
        "# v1.7 Reviewer Start Here / Reproduction Package",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        f"**Decision:** `{DECISION}`",
        "",
        "This package creates the narrow reader door used by the v1.7.10 closeout. It packages path, outputs, claim boundary, and reproduction commands; it does not answer the core question by itself. The closeout answer lives in docs/v1_7_core_question_closeout.md.",
        "",
        "## Safe route",
        "",
        "```text",
        "preflight -> triad27 -> inspect -> deep81 -> inspect -> wide243 -> inspect -> three-rung index -> v1.7.10 closeout",
        "```",
        "",
        "No all-weather one-shot is allowed as the first path. The old all-weather wound is resisted.",
        "The combined index is navigation only. It must not replace the separate rung records.",
        "",
        "## Reviewer path",
        "",
        "| step | path | purpose |",
        "|---:|---|---|",
    ]
    for row in REVIEWER_PATH_ROWS:
        lines.append(f"| {row['step']} | `{row['artifact']}` | {row['reason']} |")
    lines.extend([
        "",
        "## Boundary",
        "",
        "Allowed: controlled synthetic-field reviewer/reproduction package.",
        "Forbidden: core-question closeout, role-blind discovery, physics, cosmology, or observed-universe proof.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _decision() -> dict:
    return {
        "version": CURRENT_VERSION,
        "decision": DECISION,
        "gate_kind": GATE_KIND,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "core_question_closed": False,
        "reviewer_package_started": True,
        "reviewer_package_complete": True,
        "manuscript_v2_started": False,
        "role_blind_discovery_claimed": False,
        "physics_or_cosmology_claimed": False,
        "all_weather_one_shot_allowed": False,
        "separate_rung_records_required": True,
        "combined_index_replaces_rungs": False,
        "separate_rungs_required": ["triad27", "deep81", "wide243"],
        "next_gate": NEXT_GATE,
        "output_layers": ["full_output", "compressed_summary", "visuals", "machine", "handoff"],
    }


def build_v1_7_reviewer_reproduction_package(out: str | Path) -> dict[str, Path]:
    out_dir = ensure_dir(Path(out))
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}
    _write_read(paths["read"])
    paths["decision"].write_text(json.dumps(_decision(), indent=2) + "\n", encoding="utf-8")
    write_dict_rows_csv(paths["reviewer_path"], REVIEWER_PATH_ROWS)
    write_dict_rows_csv(paths["reproduction_commands"], REPRODUCTION_COMMAND_ROWS)
    write_dict_rows_csv(paths["expected_outputs"], EXPECTED_OUTPUT_ROWS)
    write_dict_rows_csv(paths["handoff_manifest"], HANDOFF_MANIFEST_ROWS)
    write_dict_rows_csv(paths["claim_boundary"], CLAIM_BOUNDARY_ROWS)
    write_dict_rows_csv(paths["evidence_manifest"], EVIDENCE_MANIFEST_ROWS)
    paths["triad_script"].write_text(_rung_script("triad27"), encoding="utf-8", newline="\r\n")
    paths["deep_script"].write_text(_rung_script("deep81"), encoding="utf-8", newline="\r\n")
    paths["wide_script"].write_text(_rung_script("wide243"), encoding="utf-8", newline="\r\n")
    paths["combined_script"].write_text(_combined_script(), encoding="utf-8", newline="\r\n")
    paths["bundle"] = write_evidence_bundle(out_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="v1_7_reviewer_reproduction_package_bundle")
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the v1.7.9 reviewer start-here / reproduction package report.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_9_reviewer_reproduction_package"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = build_v1_7_reviewer_reproduction_package(args.out)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
