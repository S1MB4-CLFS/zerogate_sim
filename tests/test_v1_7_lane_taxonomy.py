from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.v1_7_lane_taxonomy import (
    CANDIDATE_FAMILY_MAP_ROWS,
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION,
    GATE_KIND,
    LANE_BOUNDARY_ROWS,
    LANE_TAXONOMY_ROWS,
    LATENT_OVERCROWN_REPAIR_ROWS,
    NATIVE_WITNESS,
    NEXT_GATE,
    build_v1_7_lane_taxonomy,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_lane_taxonomy_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_lane_taxonomy(tmp_path / "out")
    for key in [
        "read",
        "decision",
        "lane_taxonomy",
        "lane_boundaries",
        "latent_overcrown_repair",
        "relation_return_specificity",
        "candidate_family_map",
        "decision_rules",
        "falsifiers",
        "audit",
        "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["gate_kind"] == GATE_KIND
    assert decision["core_question"] == CORE_QUESTION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["new_heavy_evidence_added"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["latent_overcrown_silently_reproduced"] is False
    assert decision["relation_debt_equals_return_debt"] is False
    assert decision["raw_expression_equals_earned_one"] is False
    assert decision["false_one_pressure_softened_to_latent"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert set(decision["required_lanes"]) == {
        "earned_one",
        "raw_expression_pressure",
        "latent_overcrown",
        "relation_debt",
        "return_debt",
        "false_one_pressure",
    }

    readme = paths["read"].read_text(encoding="utf-8")
    assert "latent overcrown = named lane + historical support + current seed-sensitivity" in readme
    assert "No ghost lane. No fake crown." in readme
    assert "relation debt is not return debt" in readme
    assert NEXT_GATE in readme

    taxonomy = paths["lane_taxonomy"].read_text(encoding="utf-8")
    for lane in ["earned_one", "raw_expression_pressure", "latent_overcrown", "relation_debt", "return_debt", "false_one_pressure"]:
        assert lane in taxonomy
    assert "fragile_historical_pressure_explicit_hold_until_reproduced_or_narrowed" in taxonomy

    boundaries = paths["lane_boundaries"].read_text(encoding="utf-8")
    assert "raw_vs_earned" in boundaries
    assert "relation_vs_return_debt" in boundaries
    assert "trap_as_latent" not in boundaries

    latent = paths["latent_overcrown_repair"].read_text(encoding="utf-8")
    assert "2442/2442" in latent
    assert "18 -> 0" in latent
    assert "fragile_hold_requiring_rewitness_or_claim_narrowing" in latent

    relation_return = paths["relation_return_specificity"].read_text(encoding="utf-8")
    assert "relation_debt_local" in relation_return
    assert "return_debt_local" in relation_return
    assert "Gamma" in relation_return

    family_map = paths["candidate_family_map"].read_text(encoding="utf-8")
    assert "D02" in family_map
    assert "D03" in family_map
    assert "F26" in family_map
    assert "return_debt_or_latent_overcrown_hold" in family_map


def test_v1_7_lane_taxonomy_rows_are_complete() -> None:
    lanes = {row["lane"] for row in LANE_TAXONOMY_ROWS}
    assert lanes == {
        "earned_one",
        "raw_expression_pressure",
        "latent_overcrown",
        "relation_debt",
        "return_debt",
        "false_one_pressure",
    }
    for row in LANE_TAXONOMY_ROWS:
        assert row["definition"]
        assert row["positive_evidence_surface"]
        assert row["primary_code_surface"]
        assert row["closeout_rule"]

    boundaries = {row["boundary"] for row in LANE_BOUNDARY_ROWS}
    assert {"raw_vs_earned", "latent_vs_earned", "relation_vs_return_debt", "false_one_vs_baseline_safety"} <= boundaries

    latent_surfaces = {row["surface"] for row in LATENT_OVERCROWN_REPAIR_ROWS}
    assert "first_research_alpha_archived_record" in latent_surfaces
    assert "v1_6_22_fresh_seed_debt_reproduction" in latent_surfaces
    assert "v1_7_2_repair_decision" in latent_surfaces

    families = {row["candidate_family"] for row in CANDIDATE_FAMILY_MAP_ROWS}
    assert "relation_debt_local" in families
    assert "return_debt_local" in families
    assert "perturbation_survival_candidate" in families


def test_v1_7_lane_taxonomy_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_lane_taxonomy_read.md").exists()
    assert (out / "v1_7_lane_taxonomy_bundle.zip").exists()


def test_v1_7_2_public_surfaces_and_version_truth() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    lane_doc = read("docs/v1_7_lane_taxonomy.md")
    latent_doc = read("docs/v1_7_latent_overcrown_repair.md")
    rr_doc = read("docs/v1_7_relation_return_debt_specificity.md")
    rules_doc = read("docs/v1_7_lane_visibility_decision_rules.md")
    release = read("docs/release_notes/v1_7_2_alpha.md")

    assert "1.7.4-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.4a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-lane-taxonomy" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, lane_doc, latent_doc, rr_doc, rules_doc, release]:
        assert "v1.7.2-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Lane Taxonomy and Latent Overcrown Repair" in readme
    assert "Lane Taxonomy and Latent Overcrown Repair" in roadmap
    assert "latent overcrown" in lane_doc
    assert "fragile" in lane_doc
    assert "explicit HOLD" in latent_doc
    assert "Relation Debt vs Return Debt" in rr_doc
    assert "Lane Visibility Decision Rules" in rules_doc
    assert "no new heavy evidence crown" in release
    assert "v1.7.4-alpha" in readme
    assert "v1.7.4-alpha" in roadmap
