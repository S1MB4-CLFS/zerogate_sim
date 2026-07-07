from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.four_gates_v1_6_closeout_report import (
    CLAIM_FOR_V1_7,
    CLOSEOUT_DECISION,
    CURRENT_VERSION,
    NATIVE_WITNESS,
    build_v1_6_closeout,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_6_closeout_report_outputs(tmp_path: Path) -> None:
    paths = build_v1_6_closeout(tmp_path / "out")
    for key in ["read", "decision", "claim_decision", "evidence_table", "caveats", "v1_7_entry", "audit", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == CLOSEOUT_DECISION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["v1_7_allowed"] is True
    assert decision["zenodo_action_now"] == "no_upload_yet"
    assert "controlled_synthetic_four_gates_witness" in decision["earned_lanes"]
    assert "role_blind_discovery" in decision["demoted_or_blocked_lanes"]
    assert CLAIM_FOR_V1_7 in decision["v1_7_claim_candidate"]

    read_text = paths["read"].read_text(encoding="utf-8")
    assert "bounded `+1`" in read_text
    assert "role-blind discovery" in read_text
    assert "v1.7.0-alpha" in read_text

    claims = paths["claim_decision"].read_text(encoding="utf-8")
    assert "bounded_controlled_synthetic_four_gates_witness" in claims
    assert "synthetic_zero_zone_gating_principle" in claims
    assert "observed_universe_or_physics_bridge" in claims

    evidence = paths["evidence_table"].read_text(encoding="utf-8")
    assert "v1.6.20-alpha" in evidence
    assert "v1.6.21-alpha" in evidence
    assert "v1.6.22-alpha" in evidence
    assert "v1.6.25-alpha" in evidence

    v17 = paths["v1_7_entry"].read_text(encoding="utf-8")
    assert "Operational Claim Definition" in v17
    assert "External Small-Run Reproduction Instructions" in v17


def test_v1_6_closeout_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "four_gates_v1_6_closeout_read.md").exists()
    assert (out / "four_gates_v1_6_closeout_bundle.zip").exists()


def test_v1_6_28_public_surfaces_and_route() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    closeout = read("docs/v1_6_closeout_decision.md")
    release = read("docs/release_notes/v1_6_28_alpha.md")

    assert "1.7.4-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.4a0"' in read("pyproject.toml")
    assert "zerogate-four-gates-v1-6-closeout" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, closeout, release]:
        assert "v1.6.28-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "v1.6 Closeout Decision" in readme
    assert "bounded controlled synthetic-field" in roadmap
    assert "v1.7.0-alpha" in closeout
    assert "no Zenodo" in release
    assert "observed-universe" in release
