from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.v1_7_reviewer_reproduction_package import (
    COMMAND_MAP,
    CURRENT_VERSION,
    DECISION,
    EVIDENCE_MANIFEST_ROWS,
    EXPECTED_OUTPUT_ROWS,
    HANDOFF_MANIFEST_ROWS,
    NATIVE_WITNESS,
    OUTPUT_LAYERS,
    REVIEWER_PATH_ROWS,
    build_v1_7_reviewer_reproduction_package,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_9_reviewer_package_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_reviewer_reproduction_package(tmp_path / "pkg")
    for key in [
        "read", "decision", "reviewer_path", "reproduction_commands", "expected_outputs",
        "handoff_manifest", "claim_boundary", "evidence_manifest", "triad_script", "deep_script",
        "wide_script", "combined_script", "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["core_question_closed"] is False
    assert decision["combined_index_replaces_rungs"] is False
    assert decision["separate_rung_records_required"] is True
    assert decision["all_weather_one_shot_allowed"] is False
    assert decision["next_gate"] == "v1.7.10-alpha — Core Question Closeout"

    triad_script = paths["triad_script"].read_text(encoding="utf-8")
    assert "$Args" not in triad_script
    assert "$HandoffArgs" not in triad_script
    assert "all-weather one-shot" in triad_script
    assert "triad27 reproduction helper reached safe start" in triad_script


def test_v1_7_9_constants_keep_review_layers_visible() -> None:
    assert {row["artifact"] for row in REVIEWER_PATH_ROWS} >= {
        "README.md",
        "REVIEWER_START_HERE.md",
        "docs/v1_7_reviewer_reproduction_package.md",
        "docs/v1_7_reproduction_commands.md",
        "docs/v1_7_expected_outputs.md",
        "docs/v1_7_evidence_manifest.md",
    }
    assert {row["layer"] for row in OUTPUT_LAYERS} >= {
        "full_output",
        "compressed_summary",
        "visuals",
        "handoff",
    }
    assert [row["rung"] for row in EVIDENCE_MANIFEST_ROWS if row["rung"] != "package"] == ["triad27", "deep81", "wide243"]
    evidence_rows = [row for row in EVIDENCE_MANIFEST_ROWS if row["rung"] != "package"]
    assert sum(int(row["final_false_one_crowns"]) for row in evidence_rows) == 0
    assert {row["command_level"] for row in COMMAND_MAP} == {"smoke", "triad27", "deep81", "wide243"}
    assert {row["layer"] for row in EXPECTED_OUTPUT_ROWS} >= {"full_output", "compressed_summary", "visuals", "machine", "handoff"}
    assert {row["handoff_layer"] for row in HANDOFF_MANIFEST_ROWS} >= {"full-output-report", "compressed-summary", "visual-output", "report-label-note"}


def test_v1_7_9_public_surfaces_and_paths() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    reviewer = read("REVIEWER_START_HERE.md")
    package = read("docs/v1_7_reviewer_reproduction_package.md")
    commands = read("docs/v1_7_reproduction_commands.md")
    manifest = read("docs/v1_7_evidence_manifest.md")
    expected = read("docs/v1_7_expected_outputs.md")
    boundary_card = read("docs/v1_7_claim_boundary_card.md")
    release = read("docs/release_notes/v1_7_9_alpha.md")

    assert "1.7.9-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.9a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-reviewer-package" in read("pyproject.toml")

    assert "Current public line:** `v1.7.9-alpha` — Reviewer Start Here / Reproduction Package" in readme
    assert readme.index("## Core theory") < readme.index("## Latest evidence snapshot") < readme.index("## Reviewer start here / reproduction package") < readme.index("## Inspection map")
    assert "REVIEWER_START_HERE.md" in readme
    assert "docs/v1_7_reproduction_commands.md" in readme
    assert "v1.7.10-alpha core question closeout next" in readme
    assert "v1.7.9-alpha -> v1.7.9-alpha" not in readme
    assert roadmap.count("| `v1.7.9-alpha` | Reviewer Start Here / Reproduction Package |") == 1
    assert "```math" in readme
    assert r"\Gamma_i(t)=D_i(t)P_i(t)R_i(t)" in readme

    assert "v1.7.9-alpha" in roadmap
    assert "Reviewer Start Here / Reproduction Package" in roadmap
    assert "v1.7.10-alpha" in roadmap
    assert "Core Question Closeout" in roadmap

    for text in [version_truth, reviewer, package, commands, manifest, expected, boundary_card, release]:
        assert "C_Z = min(D, P, R, B)" in text
        assert "role-blind" in text or "role-blind" in readme

    assert "triad27 -> inspect -> deep81 -> inspect -> wide243" in reviewer
    assert "A false handoff is a false crown" in expected
    assert "final false-one crowns = 0" in manifest
    assert "Forbidden claims" in boundary_card


def test_v1_7_9_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_reviewer_reproduction_package_read.md").exists()
    assert (out / "v1_7_reviewer_reproduction_package_bundle.zip").exists()
