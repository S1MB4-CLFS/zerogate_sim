from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_fresh_holdout_challenge import (
    CURRENT_VERSION,
    CORE_QUESTION,
    DECISION,
    GATE_KIND,
    NEXT_GATE,
    NATIVE_WITNESS,
    OUTPUT_STRUCTURE_ROWS,
    REQUIRED_WEATHER_RUNGS,
    RUN_ORDER_ANSWER,
    RUN_ORDER_FORBIDDEN,
    WEATHER_LADDER_ROWS,
    build_v1_7_fresh_holdout_challenge,
    classify_holdout_row,
    collapse_holdout_evaluation_decision,
    evaluate_holdout_rows,
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
    base = {
        "fresh_seed_block": "18-26",
        "heldout_profile_variant": "closure_gap_variant_B",
        "candidate_names_masked": "true",
        "expected_manifest_frozen": "true",
        "reference_profile_reused": "false",
        "earned_controls_present": "true",
        "lane_pattern_matches_expected": "true",
        "final_earned_one_events": 64,
        "raw_expression_pressure": 102,
        "latent_overcrown": 0,
        "relation_debt": 8,
        "return_debt": 5,
        "false_one_pressure": 11,
        "final_false_one_crowns": 0,
    }
    return [
        {**base, "holdout_run_id": "fresh_triad27_A", "weather_rung": "triad27", "latent_overcrown": 3},
        {**base, "holdout_run_id": "fresh_deep81_A", "weather_rung": "deep81", "final_earned_one_events": 71, "raw_expression_pressure": 144, "relation_debt": 13, "return_debt": 9, "false_one_pressure": 19},
        {**base, "holdout_run_id": "fresh_wide243_A", "weather_rung": "wide243", "final_earned_one_events": 88, "raw_expression_pressure": 211, "relation_debt": 21, "return_debt": 14, "false_one_pressure": 27},
    ]


def test_v1_7_fresh_holdout_outputs_without_evaluation(tmp_path: Path) -> None:
    paths = build_v1_7_fresh_holdout_challenge(tmp_path / "out")
    for key in [
        "read",
        "decision",
        "holdout_design",
        "expected_outputs",
        "weather_ladder",
        "run_order",
        "candidate_masking",
        "input_schema",
        "output_structure",
        "evaluation",
        "audit",
        "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["evaluation_decision"] == "fresh_holdout_challenge_locked_evaluation_not_run"
    assert decision["gate_kind"] == GATE_KIND
    assert decision["core_question"] == CORE_QUESTION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["new_heavy_evidence_added"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["independent_generator_claimed"] is False
    assert decision["core_question_closed"] is False
    assert decision["required_weather_rungs"] == REQUIRED_WEATHER_RUNGS
    assert decision["run_order_answer"] == RUN_ORDER_ANSWER
    assert decision["run_order_forbidden"] == RUN_ORDER_FORBIDDEN
    assert decision["output_structure_layers"] == [row["output_layer"] for row in OUTPUT_STRUCTURE_ROWS]
    assert "historical internal report-version labels" in decision["historical_report_label_note"]
    assert decision["next_gate"] == NEXT_GATE

    readme = paths["read"].read_text(encoding="utf-8")
    assert "No fresh holdout summary CSV was supplied" in readme
    assert "triad27" in readme and "deep81" in readme and "wide243" in readme
    assert "not role-blind discovery" in readme
    assert "run triad27 first" in readme
    assert "historical modules" in readme
    assert NEXT_GATE in readme


def test_v1_7_fresh_holdout_weather_ladder_rows_are_complete() -> None:
    assert [row["weather_rung"] for row in WEATHER_LADDER_ROWS] == ["triad27", "deep81", "wide243"]
    assert {int(row["cells"]) for row in WEATHER_LADDER_ROWS} == {27, 81, 243}
    assert all("before v1.7.7" in row["run_timing"] for row in WEATHER_LADDER_ROWS)
    assert "one-shot runner" in RUN_ORDER_FORBIDDEN[0]


def test_v1_7_fresh_holdout_output_structure_rows_are_complete() -> None:
    layers = [row["output_layer"] for row in OUTPUT_STRUCTURE_ROWS]
    assert layers == [
        "full_output_report",
        "compressed_summary",
        "visual_outputs",
        "historical_report_label_note",
    ]
    assert {row["handoff_role"] for row in OUTPUT_STRUCTURE_ROWS} == {
        "--full-output-report",
        "--compressed-summary",
        "--visual-output",
        "--report-label-note",
    }


def test_v1_7_fresh_holdout_classifies_and_collapses_rows() -> None:
    rows = _sample_rows()
    evaluation = evaluate_holdout_rows(rows)
    assert collapse_holdout_evaluation_decision(evaluation) == "expand_fresh_holdout_all_weather_rungs_safe_for_reviewer_package"
    assert {row["weather_rung"] for row in evaluation} == set(REQUIRED_WEATHER_RUNGS)
    assert any(row["latent_overcrown_visible"] for row in evaluation)

    missing_rung = rows[:2]
    assert collapse_holdout_evaluation_decision(evaluate_holdout_rows(missing_rung)) == "hold_fresh_holdout_weather_ladder_incomplete"

    stop = dict(rows[0])
    stop["final_false_one_crowns"] = 1
    assert classify_holdout_row(stop) == "resist_false_crown_stop"
    assert collapse_holdout_evaluation_decision(evaluate_holdout_rows([stop])) == "resist_fresh_holdout_false_crown_stop"

    no_manifest = dict(rows[0])
    no_manifest["expected_manifest_frozen"] = "false"
    assert classify_holdout_row(no_manifest) == "hold_expected_manifest_not_frozen"
    assert collapse_holdout_evaluation_decision(evaluate_holdout_rows([no_manifest])) == "hold_fresh_holdout_protocol_incomplete"

    dead_safe = dict(rows[0])
    dead_safe["final_earned_one_events"] = 0
    assert classify_holdout_row(dead_safe) == "resist_dead_safe_earned_lost"


def test_v1_7_fresh_holdout_with_evaluation_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "summary.csv"
    _write_summary(csv_path, _sample_rows())
    paths = build_v1_7_fresh_holdout_challenge(tmp_path / "out", holdout_summary_csv=csv_path)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    readme = paths["read"].read_text(encoding="utf-8")
    evaluation = paths["evaluation"].read_text(encoding="utf-8")

    assert decision["evaluation_decision"] == "expand_fresh_holdout_all_weather_rungs_safe_for_reviewer_package"
    assert decision["evaluation_rows"] == 3
    assert "witness_holdout_core_lanes_visible_with_latent" in readme
    assert "fresh_wide243_A" in evaluation
    assert "final_false_one_crowns" in evaluation


def test_v1_7_fresh_holdout_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_fresh_holdout_challenge_read.md").exists()
    assert (out / "v1_7_fresh_holdout_challenge_bundle.zip").exists()


def test_v1_7_6_public_surfaces_and_version_truth() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    holdout_doc = read("docs/v1_7_holdout_design.md")
    expected_doc = read("docs/v1_7_holdout_expected_outputs.md")
    weather_doc = read("docs/v1_7_holdout_weather_ladder.md")
    masking_doc = read("docs/v1_7_candidate_name_masking.md")
    release = read("docs/release_notes/v1_7_6_alpha.md")
    output_doc = read("docs/v1_7_holdout_output_structure.md")
    process_note = read("docs/release_notes/v1_7_6_holdout_output_process_note.md")

    assert "1.7.11-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.11a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-fresh-holdout-challenge" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, holdout_doc, expected_doc, weather_doc, masking_doc, release, output_doc, process_note]:
        assert "v1.7.7-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Fresh Holdout Synthetic-Field Challenge" in readme
    assert "Fresh Holdout Synthetic-Field Challenge" in roadmap
    assert "triad27" in weather_doc and "deep81" in weather_doc and "wide243" in weather_doc
    assert "before `v1.7.7-alpha`" in weather_doc
    assert "Run `triad27` first" in weather_doc
    assert "all-weather one-shot" in weather_doc
    assert "candidate-name masking" in holdout_doc
    assert "Any final false-one crown" in expected_doc
    assert "Candidate-name masking is not role-blind discovery" in masking_doc
    assert "no new heavy evidence crown" in release
    assert "full output report" in output_doc
    assert "compressed summary" in output_doc
    assert "historical internal report-version labels" in output_doc
    assert "No run result is promoted" in process_note
    assert "v1.7.7-alpha" in readme
    assert "v1.7.7-alpha" in roadmap
