from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_masked_role_dependence_audit import (
    CURRENT_VERSION,
    CORE_QUESTION,
    DECISION,
    GATE_KIND,
    MASKED_AUDIT_RULE_ROWS,
    MASKED_NUMERIC_VISIBILITY_ROWS,
    NEXT_GATE,
    NATIVE_WITNESS,
    REQUIRED_MASKED_LANES,
    ROLE_DEPENDENCE_PRESSURE_ROWS,
    build_v1_7_masked_role_dependence_audit,
    classify_masked_role_row,
    collapse_masked_role_evaluation_decision,
    evaluate_masked_role_rows,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "candidate_set": "triad27_masked_core",
            "role_labels_masked": "true",
            "role_leakage_score": "0.02",
            "label_only_lane_assignment": "false",
            "final_earned_one_events": 64,
            "raw_expression_pressure": 102,
            "latent_overcrown": 3,
            "relation_debt": 8,
            "return_debt": 5,
            "false_one_pressure": 11,
            "final_false_one_crowns": 0,
        },
        {
            "candidate_set": "deep81_masked_core",
            "role_labels_masked": "yes",
            "role_leakage_score": "0.04",
            "label_only_lane_assignment": "no",
            "final_earned_one_events": 71,
            "raw_expression_pressure": 144,
            "latent_overcrown": 0,
            "relation_debt": 13,
            "return_debt": 9,
            "false_one_pressure": 19,
            "final_false_one_crowns": 0,
        },
    ]


def test_v1_7_masked_role_audit_outputs_without_evaluation(tmp_path: Path) -> None:
    paths = build_v1_7_masked_role_dependence_audit(tmp_path / "out")
    for key in [
        "read",
        "decision",
        "audit_rules",
        "masked_numeric_visibility",
        "role_dependence_pressure",
        "input_schema",
        "evaluation",
        "audit",
        "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["evaluation_decision"] == "masked_role_audit_locked_evaluation_not_run"
    assert decision["gate_kind"] == GATE_KIND
    assert decision["core_question"] == CORE_QUESTION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["new_heavy_evidence_added"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["core_question_closed"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert set(REQUIRED_MASKED_LANES) <= set(decision["required_masked_lanes"])

    readme = paths["read"].read_text(encoding="utf-8")
    assert "No masked numeric summary CSV was supplied" in readme
    assert "not role-blind discovery" in readme
    assert NEXT_GATE in readme


def test_v1_7_masked_role_audit_rows_are_complete() -> None:
    assert {row["visible_signal"] for row in MASKED_NUMERIC_VISIBILITY_ROWS} >= {
        "earned_one",
        "relation_debt",
        "return_debt",
        "false_one_pressure",
        "final_false_one_crowns",
    }
    assert {row["audit_rule"] for row in MASKED_AUDIT_RULE_ROWS} >= {
        "mask_role_labels",
        "separate_witness_computed_from_role_shaped",
        "forbid_role_blind_discovery_language",
        "false_crown_stop_survives_masking",
    }
    assert {row["pressure_state"] for row in ROLE_DEPENDENCE_PRESSURE_ROWS} >= {
        "masked_core_lanes_visible",
        "role_leakage_pressure",
        "label_only_lane_failure",
        "false_crown_stop",
    }


def test_v1_7_masked_role_audit_evaluation_classifies_rows() -> None:
    rows = _sample_rows()
    evaluation = evaluate_masked_role_rows(rows)
    assert collapse_masked_role_evaluation_decision(evaluation) == "expand_masked_role_audit_core_lanes_visible_no_role_blind_claim"
    assert any(row["row_status"] == "witness_masked_core_lanes_visible" for row in evaluation)
    assert all(row["final_false_one_crowns"] == 0 for row in evaluation)

    stop = dict(rows[0])
    stop["final_false_one_crowns"] = 1
    assert classify_masked_role_row(stop) == "resist_false_crown_stop"
    assert collapse_masked_role_evaluation_decision(evaluate_masked_role_rows([stop])) == "resist_masked_role_false_crown_stop"

    label_only = dict(rows[0])
    label_only["label_only_lane_assignment"] = "true"
    assert classify_masked_role_row(label_only) == "resist_label_only_lane_assignment"
    assert collapse_masked_role_evaluation_decision(evaluate_masked_role_rows([label_only])) == "resist_role_label_only_lane_failure"

    leakage = dict(rows[0])
    leakage["role_leakage_score"] = "0.90"
    assert classify_masked_role_row(leakage) == "hold_role_leakage_pressure"
    assert collapse_masked_role_evaluation_decision(evaluate_masked_role_rows([leakage])) == "hold_masked_role_audit_leakage_or_unmasked"


def test_v1_7_masked_role_audit_with_evaluation_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "summary.csv"
    _write_summary(csv_path, _sample_rows())
    paths = build_v1_7_masked_role_dependence_audit(tmp_path / "out", masked_summary_csv=csv_path)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    readme = paths["read"].read_text(encoding="utf-8")
    evaluation = paths["evaluation"].read_text(encoding="utf-8")

    assert decision["evaluation_decision"] == "expand_masked_role_audit_core_lanes_visible_no_role_blind_claim"
    assert decision["evaluation_rows"] == 2
    assert "witness_masked_core_lanes_visible" in readme
    assert "triad27_masked_core" in evaluation
    assert "final_false_one_crowns" in evaluation


def test_v1_7_masked_role_audit_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_masked_role_dependence_audit_read.md").exists()
    assert (out / "v1_7_masked_role_dependence_audit_bundle.zip").exists()


def test_v1_7_5_public_surfaces_and_version_truth() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    audit_doc = read("docs/v1_7_masked_role_dependence_audit.md")
    numeric_doc = read("docs/v1_7_masked_numeric_visibility.md")
    pressure_doc = read("docs/v1_7_role_dependence_pressure.md")
    forbidden_doc = read("docs/v1_7_role_blind_forbidden_language.md")
    release = read("docs/release_notes/v1_7_5_alpha.md")

    assert "1.7.6-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.6a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-masked-role-audit" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index]:
        assert "v1.7.6-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    for text in [audit_doc, numeric_doc, pressure_doc, forbidden_doc, release]:
        assert "v1.7.5-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Masked Role-Dependence Audit" in readme
    assert "Masked Role-Dependence Audit" in roadmap
    assert "not role-blind discovery" in audit_doc
    assert "final false-one crowns" in numeric_doc
    assert "label-only lane failure" in pressure_doc
    assert "Role-Blind Forbidden Language" in forbidden_doc
    assert "no new heavy evidence crown" in release
    assert "v1.7.6-alpha" in readme
    assert "v1.7.6-alpha" in roadmap
    assert "v1.7.7-alpha" in readme
    assert "v1.7.7-alpha" in roadmap
