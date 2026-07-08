from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.v1_7_reviewer_reproduction_package import (
    CLAIM_BOUNDARY_ROWS,
    CURRENT_VERSION,
    DECISION,
    EVIDENCE_MANIFEST_ROWS,
    EXPECTED_OUTPUT_ROWS,
    NEXT_GATE,
    NATIVE_WITNESS,
    REPRODUCTION_COMMAND_ROWS,
    REVIEWER_PATH_ROWS,
    build_v1_7_reviewer_reproduction_package,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_9_package_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_reviewer_reproduction_package(tmp_path / "out")
    for key in ["read", "decision", "reviewer_path", "reproduction_commands", "expected_outputs", "claim_boundary", "evidence_manifest", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["core_question_closed"] is False
    assert decision["reviewer_package_started"] is True
    assert decision["reviewer_package_complete"] is True
    assert decision["manuscript_v2_started"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["physics_or_cosmology_claimed"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert "handoff" in decision["output_layers"]

    readme = paths["read"].read_text(encoding="utf-8")
    assert "Reviewer Start Here / Reproduction Package" in readme
    assert "No all-weather one-shot" in readme
    assert "does not answer the core question" in readme


def test_v1_7_9_constants_are_complete() -> None:
    assert [row["step"] for row in REVIEWER_PATH_ROWS] == ["1", "2", "3", "4", "5", "6"]
    assert {row["command_id"] for row in REPRODUCTION_COMMAND_ROWS} >= {
        "small_package_smoke",
        "target_test",
        "full_tests",
        "triad27_heavy_rung",
        "deep81_heavy_rung",
        "wide243_heavy_rung",
    }
    assert {row["layer"] for row in EXPECTED_OUTPUT_ROWS} == {
        "full_output",
        "compressed_summary",
        "visuals",
        "machine",
        "handoff",
    }
    assert {row["claim_lane"] for row in CLAIM_BOUNDARY_ROWS} >= {"allowed", "forbidden"}
    assert any(row["artifact"] == "REVIEWER_START_HERE.md" for row in EVIDENCE_MANIFEST_ROWS)


def test_v1_7_9_public_surfaces_and_paths() -> None:
    readme = read("README.md")
    reviewer = read("REVIEWER_START_HERE.md")
    minimal = read("docs/v1_7_minimal_reproduction.md")
    expected = read("docs/v1_7_expected_outputs.md")
    boundary = read("docs/v1_7_claim_boundary_card.md")
    manifest = read("docs/v1_7_evidence_manifest.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    current_state = read("docs/current_evidence_state.md")
    release = read("docs/release_notes/v1_7_9_alpha.md")
    script = read("scripts/run_v1_7_small_reproduction.ps1")

    assert "1.7.10-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.10a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-reviewer-package" in read("pyproject.toml")

    assert "Current public line:** `v1.7.10-alpha` — Core Question Closeout" in readme
    assert "## How to read this README" in readme
    assert "## Reviewer start here / reproduction package" in readme
    assert "REVIEWER_START_HERE.md" in readme
    assert "docs/v1_7_minimal_reproduction.md" in readme
    assert "docs/v1_7_expected_outputs.md" in readme
    assert "docs/v1_7_claim_boundary_card.md" in readme
    assert "docs/v1_7_evidence_manifest.md" in readme
    assert "scripts\\run_v1_7_small_reproduction.ps1" in readme
    assert "manuscript v2 bounded upgrade next before v1.8" in readme
    assert readme.index("## Native math witness") < readme.index("## Latest evidence snapshot")
    assert readme.index("## Latest evidence snapshot") < readme.index("## Reviewer start here / reproduction package") < readme.index("## Inspection map")
    assert "docs/assets/v1_7_6_triad27_holdout_card.svg" in readme

    for text in [reviewer, minimal, expected, boundary, manifest, roadmap, version_truth, current_state, release]:
        assert "v1.7.9-alpha" in text
    assert "C_Z = min(D, P, R, B)" in reviewer
    assert "triad27 -> inspect -> deep81 -> inspect -> wide243 -> inspect" in reviewer
    assert "full_output/" in expected
    assert "A false handoff is a false crown" in expected
    assert "core v1.7 question is formally closed" in boundary
    assert "v1.7.10-alpha" in boundary
    assert "REVIEWER_START_HERE.md" in manifest
    assert "Reviewer Start Here / Reproduction Package" in roadmap
    assert "v1.7.10-alpha" in roadmap
    assert "Reviewer Start Here / Reproduction Package" in version_truth
    assert "Reviewer Start Here / Reproduction Package" in current_state
    assert "reviewer package" in release.lower()
    assert "$Args" not in script
    assert "v1.7.10-alpha" in script
    assert "test_v1_7_reviewer_path.py" in script
    for name, text in {"reviewer": reviewer, "minimal": minimal, "expected": expected, "boundary": boundary, "manifest": manifest}.items():
        bad = [ch for ch in text if ord(ch) < 32 and ch not in "\n\t"]
        assert not bad, name


def test_v1_7_9_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_reviewer_reproduction_package_read.md").exists()
    assert (out / "v1_7_reviewer_reproduction_package_bundle.zip").exists()
