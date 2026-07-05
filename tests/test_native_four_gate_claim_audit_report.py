from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.native_four_gate_claim_audit_report import write_native_four_gate_claim_audit_report

ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_native_claim_audit_writes_expected_files(tmp_path: Path) -> None:
    paths = write_native_four_gate_claim_audit_report(output_dir=tmp_path / "audit")
    for key in ["read", "decision", "readiness", "route", "claim_lanes", "audit", "bundle"]:
        assert paths[key].exists()


def test_native_claim_audit_decision_and_boundaries(tmp_path: Path) -> None:
    paths = write_native_four_gate_claim_audit_report(output_dir=tmp_path / "audit")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    assert decision["version"] == "v1.6.14-alpha"
    assert decision["global_decision"] == "hold_native_claim_not_closed_yet"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["zenodo_route_allowed"] is False
    assert decision["observed_universe_bridge_allowed"] is False
    assert decision["role_blind_discovery_claim"] is False
    assert "not Zenodo yet" in read
    assert "not shadow revival" in read


def test_native_claim_lanes_include_structured_zero(tmp_path: Path) -> None:
    paths = write_native_four_gate_claim_audit_report(output_dir=tmp_path / "audit")
    rows = _read_csv(paths["claim_lanes"])
    lanes = {row["lane"] for row in rows}
    assert "+1 earned-one" in lanes
    assert "0 latent overcrown" in lanes
    assert "0 relation debt" in lanes
    assert "0 return debt" in lanes
    assert "-1 false-one pressure" in lanes


def test_readiness_route_names_ablation_and_weather_order(tmp_path: Path) -> None:
    paths = write_native_four_gate_claim_audit_report(output_dir=tmp_path / "audit")
    criteria = _read_csv(paths["readiness"])
    route = _read_csv(paths["route"])
    joined_criteria = "\n".join(row["criterion"] + " " + row["pass_condition"] for row in criteria)
    joined_route = "\n".join(row["version"] + " " + row["gate"] for row in route)
    assert "native ablation enemies" in joined_criteria
    assert "triad27" in joined_criteria
    assert "deep81" in joined_criteria
    assert "wide243" in joined_criteria
    assert "v1.6.15-alpha native ablation baselines" in joined_route
    assert "v1.6.16-alpha four-corpus triad27 native evidence" in joined_route


def test_public_version_truth_surfaces_preserve_v1_6_14_and_route_to_v1_6_15() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_14_alpha.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/native_four_gate_claim_audit.md").read_text(encoding="utf-8")
    assert "1.6.28-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.6.28a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [version_truth, release, doc]:
        assert "v1.6.14-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text
    for text in [readme, roadmap, version_truth]:
        assert "v1.6.15-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text
    assert "v1.6.15-alpha" in roadmap
    assert "native ablation baselines" in roadmap
    assert "Observed-universe bridge rule" in roadmap
    assert "not proof that the universe uses ZeroGateSim" in roadmap
