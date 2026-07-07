from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.four_gates_reproduction_command_package_report import (
    CURRENT_VERSION,
    NATIVE_WITNESS,
    build_reproduction_command_package,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_reproduction_command_package_writes_command_bundle(tmp_path: Path) -> None:
    paths = build_reproduction_command_package(tmp_path / "out")
    for key in ["read", "decision", "quick_ps1", "full_ps1", "manifest", "expected", "audit", "bundle"]:
        assert paths[key].exists(), key
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["decision"] == "expand_reproduction_command_package_ready_for_manuscript_correction"
    assert decision["allowed_next_gate"].startswith("v1.6.28-alpha")
    assert decision["stronger_claim_not_earned"] == "independent role-blind discovery"

    quick = paths["quick_ps1"].read_text(encoding="utf-8")
    assert "SMALL PIPELINE SMOKE" in quick
    assert "--candidate-profile four_gates_debt" in quick
    assert "four_gates_triad27_debt_evidence_report" in quick
    assert "--count 1" in quick

    full = paths["full_ps1"].read_text(encoding="utf-8")
    assert "New-DeepWideEvidence $ReferenceBase 0" in full
    assert "New-DeepWideEvidence $FreshBase 9" in full
    assert "four_gates_deepwide_debt_evidence_report" in full
    assert "four_gates_fresh_seed_debt_reproduction_report" in full

    manifest = paths["manifest"].read_text(encoding="utf-8")
    assert "v1.6.20-alpha" in manifest
    assert "v1.6.21-alpha" in manifest
    assert "v1.6.22-alpha" in manifest
    assert "v1.6.25-alpha" in manifest


def test_reproduction_command_package_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "four_gates_reproduction_command_package_read.md").exists()
    assert (out / "four_gates_reproduction_command_package_bundle.zip").exists()


def test_v1_6_27_public_surfaces_and_route() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    doc = read("docs/manuscript_correction_package.md")
    release = read("docs/release_notes/v1_6_28_alpha.md")
    assert "1.7.0-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.0a0"' in read("pyproject.toml")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.28-alpha" in text
        assert "Manuscript Correction Package" in text or "manuscript correction package" in text
        assert "C_Z = min(D, P, R, B)" in text
    assert "v1.6.28-alpha" in roadmap
    assert "Manuscript Correction Package" in roadmap
    assert "observed-universe bridge" in roadmap
