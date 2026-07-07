from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_baseline_falsifier_matrix import (
    BASELINE_MATRIX_ROWS,
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION,
    FAILURE_MODE_ROWS,
    GATE_KIND,
    NATIVE_WITNESS,
    NEXT_GATE,
    REQUIRED_BASELINE_ENEMIES,
    build_v1_7_baseline_falsifier_matrix,
    collapse_evaluation_decision,
    evaluate_baseline_summary_rows,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "baseline": "native_final_trinary_witness",
            "final_earned_one_events": 6,
            "earned_lost": 0,
            "raw_expression_pressure": 22,
            "raw_false_one_pressure": 13,
            "structured_zero_pressure": 16,
            "structured_zero_promoted": 0,
            "final_false_one_crowns": 0,
            "baseline_status": "native_witness_visible_work",
        },
        {
            "baseline": "dead_safe_no_crown",
            "final_earned_one_events": 0,
            "earned_lost": 6,
            "raw_expression_pressure": 22,
            "raw_false_one_pressure": 13,
            "structured_zero_pressure": 16,
            "structured_zero_promoted": 0,
            "final_false_one_crowns": 0,
            "baseline_status": "dead_safe_fails_earned_preservation",
        },
        {
            "baseline": "raw_expression_only",
            "final_earned_one_events": 22,
            "earned_lost": 0,
            "raw_expression_pressure": 22,
            "raw_false_one_pressure": 13,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 16,
            "final_false_one_crowns": 13,
            "baseline_status": "breach_introduced",
        },
        {
            "baseline": "binary_raw_or_fail",
            "final_earned_one_events": 22,
            "earned_lost": 0,
            "raw_expression_pressure": 22,
            "raw_false_one_pressure": 13,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 16,
            "final_false_one_crowns": 13,
            "baseline_status": "breach_introduced",
        },
        {
            "baseline": "average_gate_raw",
            "final_earned_one_events": 10,
            "earned_lost": 0,
            "raw_expression_pressure": 26,
            "raw_false_one_pressure": 4,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 3,
            "final_false_one_crowns": 4,
            "baseline_status": "breach_introduced",
        },
        {
            "baseline": "no_return_gate_raw",
            "final_earned_one_events": 13,
            "earned_lost": 0,
            "raw_expression_pressure": 18,
            "raw_false_one_pressure": 4,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 7,
            "final_false_one_crowns": 4,
            "baseline_status": "breach_introduced",
        },
        {
            "baseline": "no_relation_gate_raw",
            "final_earned_one_events": 10,
            "earned_lost": 0,
            "raw_expression_pressure": 12,
            "raw_false_one_pressure": 0,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 4,
            "final_false_one_crowns": 0,
            "baseline_status": "structured_zero_overcrowned",
        },
        {
            "baseline": "no_lineage_or_return_depth_witness",
            "final_earned_one_events": 11,
            "earned_lost": 0,
            "raw_expression_pressure": 15,
            "raw_false_one_pressure": 2,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 5,
            "final_false_one_crowns": 2,
            "baseline_status": "breach_introduced",
        },
        {
            "baseline": "no_echo_independence_witness",
            "final_earned_one_events": 10,
            "earned_lost": 0,
            "raw_expression_pressure": 16,
            "raw_false_one_pressure": 0,
            "structured_zero_pressure": 12,
            "structured_zero_promoted": 4,
            "final_false_one_crowns": 0,
            "baseline_status": "structured_zero_overcrowned",
        },
        {
            "baseline": "no_zero_hold_witness",
            "final_earned_one_events": 22,
            "earned_lost": 0,
            "raw_expression_pressure": 22,
            "raw_false_one_pressure": 0,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": 16,
            "final_false_one_crowns": 0,
            "baseline_status": "structured_zero_overcrowned",
        },
    ]


def test_v1_7_baseline_matrix_outputs_without_evaluation(tmp_path: Path) -> None:
    paths = build_v1_7_baseline_falsifier_matrix(tmp_path / "out")
    for key in ["read", "decision", "baseline_matrix", "failure_modes", "pass_rules", "input_schema", "evaluation", "audit", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["evaluation_decision"] == "baseline_falsifier_matrix_locked_evaluation_not_run"
    assert decision["gate_kind"] == GATE_KIND
    assert decision["core_question"] == CORE_QUESTION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["new_heavy_evidence_added"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["core_question_closed"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert set(REQUIRED_BASELINE_ENEMIES) <= set(decision["required_baseline_enemies"])

    readme = paths["read"].read_text(encoding="utf-8")
    assert "A dead-safe witness gets zero false crowns by refusing real earned-one" in readme
    assert "No baseline summary CSV was supplied" in readme
    assert NEXT_GATE in readme

    matrix = paths["baseline_matrix"].read_text(encoding="utf-8")
    for enemy in REQUIRED_BASELINE_ENEMIES:
        assert enemy in matrix
    assert "native_final_trinary_witness" in matrix


def test_v1_7_baseline_matrix_rows_are_complete() -> None:
    baselines = {row["baseline"] for row in BASELINE_MATRIX_ROWS}
    assert "native_final_trinary_witness" in baselines
    assert set(REQUIRED_BASELINE_ENEMIES) <= baselines
    assert "no_false_one_demotion_witness" in baselines
    for row in BASELINE_MATRIX_ROWS:
        assert row["family"]
        assert row["what_it_removes_or_collapses"]
        assert row["must_show_or_fail_by"]
        assert row["native_counterproof_required"]
        assert row["fatal_if"]

    modes = {row["failure_mode"] for row in FAILURE_MODE_ROWS}
    assert {"dead_safe_equivalence", "raw_pressure_equivalence", "average_gate_compensation", "no_zero_hold_ablation_survives"} <= modes


def test_v1_7_baseline_evaluation_classifies_enemies() -> None:
    evaluation = evaluate_baseline_summary_rows(_sample_rows())
    by_name = {row["baseline"]: row for row in evaluation}

    assert by_name["native_final_trinary_witness"]["matrix_status"] == "native_control_visible"
    assert by_name["dead_safe_no_crown"]["matrix_status"] == "enemy_fails_dead_safe_refusal"
    assert by_name["raw_expression_only"]["matrix_status"] == "enemy_fails_false_crowns"
    assert by_name["no_zero_hold_witness"]["matrix_status"] == "enemy_fails_zero_overcrown"
    assert by_name["no_false_one_demotion_witness"]["matrix_status"] == "hold_not_evaluated"
    assert collapse_evaluation_decision(evaluation) == "expand_baseline_enemies_expose_witness_work"


def test_v1_7_baseline_matrix_with_evaluation_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "summary.csv"
    _write_summary(csv_path, _sample_rows())
    paths = build_v1_7_baseline_falsifier_matrix(tmp_path / "out", baseline_summary_csv=csv_path)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    readme = paths["read"].read_text(encoding="utf-8")
    evaluation = paths["evaluation"].read_text(encoding="utf-8")

    assert decision["evaluation_decision"] == "expand_baseline_enemies_expose_witness_work"
    assert decision["evaluation_rows"] == len(BASELINE_MATRIX_ROWS)
    assert "enemy_fails_dead_safe_refusal" in readme
    assert "enemy_fails_false_crowns" in evaluation
    assert "no_zero_hold_witness" in evaluation


def test_v1_7_baseline_matrix_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_baseline_falsifier_matrix_read.md").exists()
    assert (out / "v1_7_baseline_falsifier_matrix_bundle.zip").exists()


def test_v1_7_3_public_surfaces_remain_historical_under_current_package() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    matrix_doc = read("docs/v1_7_baseline_falsifier_matrix.md")
    summary_doc = read("docs/v1_7_ablation_summary.md")
    failure_doc = read("docs/v1_7_failure_mode_table.md")
    release = read("docs/release_notes/v1_7_3_alpha.md")

    assert "1.7.8-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.8a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-baseline-falsifier" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index]:
        assert "v1.7.7-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    for text in [matrix_doc, summary_doc, failure_doc, release]:
        assert "v1.7.3-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Baseline and Ablation Falsifier Matrix" in readme
    assert "Baseline and Ablation Falsifier Matrix" in roadmap
    assert "dead-safe" in matrix_doc
    assert "native final trinary witness must win three ways" in summary_doc
    assert "dead-safe equivalence" in failure_doc
    assert "no new heavy evidence crown" in release
    assert "v1.7.7-alpha" in readme
    assert "v1.7.7-alpha" in roadmap
