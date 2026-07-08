from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.four_gates_debt_candidate_design_report import write_four_gates_debt_candidate_design_report

ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_four_gates_debt_design_writes_expected_files(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_design_report(output_dir=tmp_path / "design")
    for key in ["read", "decision", "candidate_families", "diagnostics", "claim_lanes", "route", "forbidden_claims", "audit", "bundle"]:
        assert paths[key].exists()


def test_four_gates_debt_design_decision_boundaries(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_design_report(output_dir=tmp_path / "design")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    assert decision["version"] == "v1.6.18-alpha"
    assert decision["global_decision"] == "hold_debt_candidate_design_ready_for_generator_implementation"
    assert decision["framework_name"] == "Four Gates of Becoming"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["physics_topology_analogy_hold"] is True
    assert decision["spacetime_metric_claim_allowed"] is False
    assert ("D" + "QRT") not in read
    assert "Four Gates of Becoming" in read
    assert "no spacetime metric claim" in read.lower()


def test_debt_candidate_families_include_relation_return_and_global_debt(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_design_report(output_dir=tmp_path / "design")
    families = {row["family"]: row for row in _read_csv(paths["candidate_families"])}
    assert families["relation_debt_local"]["expected_primary_state"] == "0 relation debt"
    assert families["return_debt_local"]["expected_primary_state"] == "0 return debt"
    assert families["relation_debt_global"]["expected_primary_state"] == "0 relation debt"
    assert families["false_one_trap_control"]["expected_primary_state"] == "-1 false-one demotion"
    assert families["earned_return_control"]["expected_primary_state"] == "+1 earned-one"


def test_debt_diagnostics_and_claim_lanes_are_bounded(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_design_report(output_dir=tmp_path / "design")
    diagnostics = {row["diagnostic"] for row in _read_csv(paths["diagnostics"])}
    lanes = {row["lane"]: row for row in _read_csv(paths["claim_lanes"])}
    forbidden = "\n".join(row["forbidden_claim"] for row in _read_csv(paths["forbidden_claims"]))
    assert "relation_ownership_gap" in diagnostics
    assert "dual_return_gap" in diagnostics
    assert "closure_gap" in diagnostics
    assert lanes["formal_computational"]["claim_status"] == "active"
    assert lanes["physics_topology_hold"]["claim_status"] == "hold"
    assert "spacetime metric" in forbidden
    assert "universe" in forbidden


def test_public_surfaces_current_route_and_no_dqrt_label() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_18_alpha.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/four_gates_debt_candidate_design.md").read_text(encoding="utf-8")
    assert "1.7.10-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.7.10a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, release, doc]:
        assert "v1.6.18-alpha" in text
        assert "Four Gates" in text
        assert "C_Z = min(D, P, R, B)" in text
        assert ("D" + "QRT") not in text
    assert "v1.6.19-alpha" in roadmap
    assert "debt candidate generator" in roadmap
