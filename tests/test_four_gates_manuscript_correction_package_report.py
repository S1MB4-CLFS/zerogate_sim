from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.four_gates_manuscript_correction_package_report import (
    CLAIM_CANDIDATE,
    CURRENT_VERSION,
    NATIVE_WITNESS,
    build_manuscript_correction_package,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_manuscript_correction_package_outputs(tmp_path: Path) -> None:
    paths = build_manuscript_correction_package(tmp_path / "out")
    for key in ["read", "decision", "outline", "patch_map", "claim_lanes", "evidence_table", "zenodo_plan", "audit", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["decision"] == "expand_manuscript_correction_package_ready_for_closeout"
    assert decision["zenodo_action_now"] == "no_upload_yet_prepare_new_version_later"
    assert decision["full_v2_paper_ready"] is False
    assert decision["requires_v1_7_success_for_v2"] is True
    assert decision["old_manuscript_status"] == "preserve_as_historical_first_research_alpha_artifact"

    read_text = paths["read"].read_text(encoding="utf-8")
    assert CLAIM_CANDIDATE in read_text
    assert "not the full v2 manuscript" in read_text
    assert "No Zenodo route starts here" in read_text

    patch_map = paths["patch_map"].read_text(encoding="utf-8")
    assert "three-corpus / four-gate distinction" in patch_map
    assert "relation debt and return debt" in patch_map

    lanes = paths["claim_lanes"].read_text(encoding="utf-8")
    assert "simulation_supported" in lanes
    assert "physics_topology_hold" in lanes
    assert "role_blind_shadow" in lanes

    outline = paths["outline"].read_text(encoding="utf-8")
    assert "v1.7 succeeds" in outline
    assert "designed-profile shaped but witness-counted" in outline

    zenodo = paths["zenodo_plan"].read_text(encoding="utf-8")
    assert "no Zenodo upload" in zenodo
    assert "historical first-research-alpha artifact" in zenodo


def test_manuscript_correction_package_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "four_gates_manuscript_correction_package_read.md").exists()
    assert (out / "four_gates_manuscript_correction_package_bundle.zip").exists()


def test_v1_6_27_public_surfaces_and_route() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    doc = read("docs/manuscript_correction_package.md")
    release = read("docs/release_notes/v1_6_28_alpha.md")

    assert "1.7.2-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.2a0"' in read("pyproject.toml")
    assert "zerogate-four-gates-manuscript-correction-package" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, doc, release]:
        assert "v1.6.28-alpha" in text
        assert "Manuscript Correction Package" in text or "manuscript correction package" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "no upload yet" in roadmap.lower()
    assert "v1.6 closeout" in roadmap
    assert "v1.7" in roadmap
    assert "full v2 paper" in doc
    assert "no observed-universe bridge" in release
