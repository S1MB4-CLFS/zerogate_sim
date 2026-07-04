from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_role_blind_design_states_boundary_and_native_witness() -> None:
    text = _read("docs/role_blind_shadow_design.md")

    for needle in [
        "design-only",
        "report-only",
        "without reading designed truth-role labels",
        "not enough to trust the shadow",
        "C_Z = min(D, P, R, B)",
        "W_role",
        "does not replace the current role-aware witness",
        "not role-blind discovery",
    ]:
        assert needle in text


def test_role_blind_schema_separates_allowed_and_forbidden_fields() -> None:
    data = json.loads(_read("docs/role_blind_shadow_schema.json"))

    allowed = set(data["allowed_input_fields"])
    forbidden = set(data["forbidden_input_fields"])

    for field in [
        "gate_distinction",
        "gate_polarity",
        "gate_relation",
        "gate_return",
        "weakest_gate",
        "time_axis",
        "ablation_variant_outputs",
    ]:
        assert field in allowed

    for field in [
        "trap",
        "expresser",
        "latent_probe",
        "truth_role",
        "role_label",
        "candidate_profile",
        "designed_truth_role",
        "answer_key",
    ]:
        assert field in forbidden
        assert field not in allowed

    assert "Score first without forbidden fields" in data["evaluation_rule"]
    assert "raw-strength-only" in data["falsifier"]


def test_readme_and_roadmap_point_to_role_blind_design() -> None:
    readme = _read("README.md")
    roadmap = _read("ROADMAP.md")

    for needle in [
        "`v1.6.0-alpha`",
        "docs/role_blind_shadow_design.md",
        "docs/role_blind_shadow_schema.json",
        "docs/assets/role_blind_shadow_design_card.svg",
        "Role-blind shadow design card",
    ]:
        assert needle in readme

    assert "### v1.6.0-alpha — Role-blind shadow design" in roadmap
    assert "role-blind shadow is design-only" in roadmap
    assert "score prototype, report-only" in roadmap


def test_role_blind_design_card_matches_visual_boundary() -> None:
    text = _read("docs/assets/role_blind_shadow_design_card.svg")

    for needle in [
        "ZeroGateSim Role-Blind Shadow Design Card",
        "ALLOW",
        "FORBID",
        "REPORT-ONLY",
        "S_shadow",
        "Native C_Z = min(D, P, R, B) remains unchanged",
    ]:
        assert needle in text


def test_v1_6_release_note_preserves_falsifier() -> None:
    text = _read("docs/release_notes/v1_6_0_alpha.md")
    assert "Role-Blind Shadow Design" in text
    assert "No native gate changed" in text
    assert "role-stripped shadow report" in text
    assert "not earned" in text
