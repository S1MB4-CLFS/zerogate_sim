from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_anti_tautology_role_dependence_check import (
    AUDIT_CONDITION_ROWS,
    CURRENT_VERSION,
    DECISION,
    GATE_KIND,
    KNOWN_ROUTINE_ROWS,
    NEXT_GATE,
    NATIVE_WITNESS,
    ROLE_DEPENDENCE_CHECK_ROWS,
    build_v1_7_anti_tautology_role_dependence_check,
    classify_audit_row,
    collapse_audit_decision,
    evaluate_audit_rows,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _sample_rows() -> list[dict[str, object]]:
    base = {
        "fresh_seed_block": "18-26",
        "provenance_status": "verified",
        "scoring_label_firewall": "verified",
        "candidate_names_masked": "true",
        "expected_manifest_frozen": "true",
        "reference_profile_reused": "false",
        "earned_controls_present": "true",
        "lane_pattern_matches_expected": "true",
        "role_labels_masked": "true",
        "role_leakage_score": "0.03",
        "label_only_lane_assignment": "false",
    }
    return [
        {
            **base,
            "holdout_run_id": "triad27_18_26",
            "weather_rung": "triad27",
            "final_earned_one_events": 839,
            "raw_expression_pressure": 1283,
            "latent_overcrown": 9,
            "relation_debt": 39,
            "return_debt": 75,
            "false_one_pressure": 321,
            "final_false_one_crowns": 0,
        },
        {
            **base,
            "holdout_run_id": "deep81_18_26",
            "weather_rung": "deep81",
            "final_earned_one_events": 1950,
            "raw_expression_pressure": 3012,
            "latent_overcrown": 9,
            "relation_debt": 120,
            "return_debt": 126,
            "false_one_pressure": 807,
            "final_false_one_crowns": 0,
        },
        {
            **base,
            "holdout_run_id": "wide243_18_26",
            "weather_rung": "wide243",
            "final_earned_one_events": 9417,
            "raw_expression_pressure": 14058,
            "latent_overcrown": 21,
            "relation_debt": 465,
            "return_debt": 612,
            "false_one_pressure": 3543,
            "final_false_one_crowns": 0,
        },
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_v1_7_anti_tautology_outputs_without_evaluation(tmp_path: Path) -> None:
    paths = build_v1_7_anti_tautology_role_dependence_check(tmp_path / "out")
    for key in [
        "read",
        "decision",
        "routine",
        "conditions",
        "role_dependence",
        "input_schema",
        "evaluation",
        "audit",
        "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["evaluation_decision"] == "anti_tautology_role_dependence_check_locked_evaluation_not_run"
    assert decision["gate_kind"] == GATE_KIND
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["core_question_closed"] is False
    assert decision["next_gate"] == NEXT_GATE

    readme = paths["read"].read_text(encoding="utf-8")
    assert "No holdout summary CSV was supplied" in readme
    assert "not role-blind discovery" in readme
    assert "pre-register expected outputs" in readme
    assert NEXT_GATE in readme


def test_v1_7_anti_tautology_known_routine_rows_are_complete() -> None:
    assert {row["routine_step"] for row in KNOWN_ROUTINE_ROWS} >= {
        "pre_registration_trace",
        "holdout_split_trace",
        "negative_control_false_crown_stop",
        "positive_control_dead_safe_guard",
        "label_leakage_and_role_dependence_check",
        "ablation_and_alternative_explanation_pressure",
        "mechanism_self_explanation",
    }
    assert {row["condition"] for row in AUDIT_CONDITION_ROWS} >= {
        "all_weather_rungs_present",
        "not_vacuous_no_false_crowns",
        "not_dead_safe",
        "structured_zero_not_generic_failure",
        "manifest_before_result",
        "candidate_name_masking",
    }
    assert {row["check"] for row in ROLE_DEPENDENCE_CHECK_ROWS} >= {
        "designed_profile_boundary",
        "label_leakage_pressure",
        "witness_count_dependence",
        "tautology_pressure",
        "bounded_claim_translation",
    }


def test_v1_7_anti_tautology_evaluation_decisions() -> None:
    rows = _sample_rows()
    evaluation = evaluate_audit_rows(rows)
    assert collapse_audit_decision(evaluation) == "invalid_evidence_legacy_self_attested_or_role_aware"
    assert all(row["row_status"] == "invalid_legacy_audit_superseded" for row in evaluation)

    missing = evaluate_audit_rows(rows[:2])
    assert collapse_audit_decision(missing) == "invalid_evidence_legacy_self_attested_or_role_aware"

    false_crown = dict(rows[0])
    false_crown["final_false_one_crowns"] = 1
    assert classify_audit_row(false_crown) == "resist_false_crown_stop"
    assert collapse_audit_decision(evaluate_audit_rows([false_crown])) == "resist_audit_false_crown_stop"

    dead_safe = dict(rows[0])
    dead_safe["final_earned_one_events"] = 0
    assert classify_audit_row(dead_safe) == "resist_dead_safe_no_earned_one"

    vacuous = dict(rows[0])
    vacuous["false_one_pressure"] = 0
    assert classify_audit_row(vacuous) == "hold_vacuous_no_false_pressure"

    leakage = dict(rows[0])
    leakage["candidate_names_masked"] = "false"
    assert classify_audit_row(leakage) == "resist_candidate_name_leakage"

    label_only = dict(rows[0])
    label_only["label_only_lane_assignment"] = "true"
    assert classify_audit_row(label_only) == "resist_label_only_lane_assignment"


def test_v1_7_anti_tautology_with_holdout_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "holdout.csv"
    _write_csv(csv_path, _sample_rows())
    paths = build_v1_7_anti_tautology_role_dependence_check(tmp_path / "out", holdout_summary_csvs=[csv_path])
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    readme = paths["read"].read_text(encoding="utf-8")
    evaluation = paths["evaluation"].read_text(encoding="utf-8")

    assert decision["evaluation_decision"] == "invalid_evidence_legacy_self_attested_or_role_aware"
    assert decision["current_claim_authority"] is False
    assert decision["summary"]["total_final_earned_one_events"] == 12206
    assert decision["summary"]["total_false_one_pressure"] == 4671
    assert decision["summary"]["total_final_false_one_crowns"] == 0
    assert "triad27" in readme and "wide243" in readme
    assert "invalid_legacy_audit_superseded" in evaluation


def test_v1_7_anti_tautology_rejects_self_attested_provenance() -> None:
    rows = _sample_rows()
    for row in rows:
        row.pop("provenance_status")
        row.pop("scoring_label_firewall")
    evaluation = evaluate_audit_rows(rows)
    assert {row["row_status"] for row in evaluation} == {"invalid_self_attested_provenance"}
    assert collapse_audit_decision(evaluation) == "invalid_evidence_legacy_self_attested_or_role_aware"


def test_v1_7_anti_tautology_duplicate_inputs_do_not_inflate_totals(tmp_path: Path) -> None:
    csv_path = tmp_path / "holdout.csv"
    _write_csv(csv_path, _sample_rows())
    single = build_v1_7_anti_tautology_role_dependence_check(
        tmp_path / "single",
        holdout_summary_csvs=[csv_path],
    )
    duplicate = build_v1_7_anti_tautology_role_dependence_check(
        tmp_path / "duplicate",
        holdout_summary_csvs=[csv_path, csv_path],
    )
    single_decision = json.loads(single["decision"].read_text(encoding="utf-8"))
    duplicate_decision = json.loads(duplicate["decision"].read_text(encoding="utf-8"))
    assert single_decision["summary"] == duplicate_decision["summary"]


def test_v1_7_anti_tautology_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_anti_tautology_role_dependence_check_read.md").exists()
    assert (out / "v1_7_anti_tautology_role_dependence_check_bundle.zip").exists()


def test_v1_7_7_public_surfaces_and_version_truth() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    audit_doc = read("docs/v1_7_anti_tautology_role_dependence_check.md")
    routine_doc = read("docs/v1_7_anti_tautology_known_routine.md")
    schema_doc = read("docs/v1_7_post_holdout_audit_schema.md")
    release = read("docs/release_notes/v1_7_7_alpha.md")

    assert "zerogate-v1-7-anti-tautology-role-audit" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, audit_doc, routine_doc, schema_doc, release]:
        assert "v1.7.7-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Anti-Tautology Audit / Role-Dependence Check" in readme
    assert "Anti-Tautology Audit / Role-Dependence Check" in roadmap
    assert "pre-register expectations" in audit_doc
    assert "positive controls" in routine_doc
    assert "role_leakage_score" in schema_doc
    assert "no role-blind discovery claim" in release
    assert "v1.7.9-alpha" in readme
    assert "v1.7.9-alpha" in roadmap
    assert "v1.7.9-alpha" in roadmap
