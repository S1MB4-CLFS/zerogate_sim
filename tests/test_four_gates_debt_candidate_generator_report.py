from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.four_gates_debt_candidate_generator_report import write_four_gates_debt_candidate_generator_report
from zerogate_sim.signals import CANDIDATE_PROFILES, candidate_specs

ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_four_gates_debt_profile_is_registered_and_bounded() -> None:
    assert "four_gates_debt" in CANDIDATE_PROFILES
    specs = candidate_specs("four_gates_debt")
    kinds = {spec.kind for spec in specs}
    roles = {spec.truth_role for spec in specs}
    assert {"expresser", "latent", "trap"}.issubset(roles)
    assert "relation_debt_local" in kinds
    assert "return_debt_local" in kinds
    assert "relation_debt_global_a" in kinds
    assert "relation_debt_global_b" in kinds
    assert "closure_gap_candidate" in kinds
    assert "dual_return_gap_candidate" in kinds
    assert "perturbation_survival_candidate" in kinds
    assert "earned_return_control" in kinds
    assert "false_one_trap_control" in kinds


def test_debt_candidate_generator_writes_expected_files(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_generator_report(output_dir=tmp_path / "generator")
    for key in ["read", "decision", "candidate_specs", "lane_targets", "preview_scores", "audit", "bundle"]:
        assert paths[key].exists()


def test_debt_candidate_generator_decision_and_lanes(tmp_path: Path) -> None:
    paths = write_four_gates_debt_candidate_generator_report(output_dir=tmp_path / "generator")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    lanes = {row["expected_lane"]: row for row in _read_csv(paths["lane_targets"])}
    specs = _read_csv(paths["candidate_specs"])
    preview = _read_csv(paths["preview_scores"])
    assert decision["version"] == "v1.6.19-alpha"
    assert decision["global_decision"] == "hold_debt_candidate_generator_ready_for_triad27_debt_evidence"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["candidate_profile"] == "four_gates_debt"
    assert decision["heavy_evidence_run_completed"] is False
    assert "+1 earned-one" in lanes
    assert "-1 false-one demotion" in lanes
    assert "0 relation debt" in lanes
    assert "0 return debt" in lanes
    assert any(row["kind"] == "relation_debt_local" and row["truth_role"] == "latent" for row in specs)
    assert len(preview) == len(specs)


def test_generator_public_surfaces_and_route_are_current() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/four_gates_debt_candidate_generator.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_19_alpha.md").read_text(encoding="utf-8")
    assert "1.6.24-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.6.24a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.19-alpha" in text
        assert "Four Gates" in text
        assert "C_Z = min(D, P, R, B)" in text
        assert ("D" + "QRT") not in text
    assert "v1.6.20-alpha" in roadmap
    assert "triad27 debt evidence" in roadmap
