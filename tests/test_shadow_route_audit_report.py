from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.shadow_route_audit_report import write_shadow_route_audit_report

ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_shadow_route_audit_writes_expected_files(tmp_path: Path) -> None:
    paths = write_shadow_route_audit_report(output_dir=tmp_path / "audit")
    for key in ["read", "decision", "steps", "feature_design", "audit", "bundle"]:
        assert paths[key].exists()


def test_shadow_route_audit_boundary_and_decision(tmp_path: Path) -> None:
    paths = write_shadow_route_audit_report(output_dir=tmp_path / "audit")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    assert decision["version"] == "v1.6.11-alpha"
    assert decision["global_decision"] == "hold_map_repaired_feature_design_ready_not_implemented"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["role_blind_discovery_claim"] is False
    assert "not role-blind discovery" in read
    assert "Do not move to deep81 / wide243 while triad27 specificity is unearned." in read


def test_shadow_route_feature_design_names_specific_lanes(tmp_path: Path) -> None:
    paths = write_shadow_route_audit_report(output_dir=tmp_path / "audit")
    rows = _read_csv(paths["feature_design"])
    lanes = {row["lane"] for row in rows}
    assert "relation_specific" in lanes
    assert "return_specific" in lanes
    assert "demotion" in lanes
    assert "density_residual" in lanes
    for row in rows:
        assert "truth_role" not in row["candidate_observables"]
        assert row["forbidden_shortcut"]


def test_roadmap_readme_version_truth_for_v1_6_11() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_11_alpha.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_route_audit_and_feature_design.md").read_text(encoding="utf-8")
    for text in [readme, roadmap, release, doc]:
        assert "v1.6.11-alpha" in text
    assert "v1.6.10-alpha" in roadmap
    assert "v1.6.11-alpha" in roadmap
    assert readme.index("## Core theory") < readme.index("## Why this exists")
    assert "deep81 / wide243" in roadmap
    assert "triad27 specificity" in roadmap
