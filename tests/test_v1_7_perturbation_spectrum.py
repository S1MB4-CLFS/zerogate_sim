from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_perturbation_spectrum import (
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION,
    GATE_KIND,
    NEXT_GATE,
    NATIVE_WITNESS,
    REQUIRED_SPECTRUM_LANES,
    WITNESS_SPECTRUM_ROWS,
    WEATHER_RUNG_ROWS,
    build_v1_7_perturbation_spectrum,
    classify_spectrum_row,
    collapse_spectrum_evaluation_decision,
    evaluate_perturbation_spectrum_rows,
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
            "weather_rung": "triad27",
            "pressure_level": "local",
            "final_earned_one_events": 12,
            "earned_lost": 0,
            "raw_expression_pressure": 15,
            "latent_overcrown": 0,
            "relation_debt": 3,
            "return_debt": 2,
            "echo_dependence": 1,
            "lineage_instability": 0,
            "false_one_pressure": 2,
            "final_false_one_crowns": 0,
        },
        {
            "weather_rung": "deep81",
            "pressure_level": "perturbation",
            "final_earned_one_events": 10,
            "earned_lost": 1,
            "raw_expression_pressure": 18,
            "latent_overcrown": 1,
            "relation_debt": 4,
            "return_debt": 5,
            "echo_dependence": 2,
            "lineage_instability": 1,
            "false_one_pressure": 4,
            "final_false_one_crowns": 0,
        },
        {
            "weather_rung": "wide243",
            "pressure_level": "temporal_depth",
            "final_earned_one_events": 8,
            "earned_lost": 2,
            "raw_expression_pressure": 21,
            "latent_overcrown": 0,
            "relation_debt": 6,
            "return_debt": 7,
            "echo_dependence": 4,
            "lineage_instability": 3,
            "false_one_pressure": 8,
            "final_false_one_crowns": 0,
        },
    ]


def test_v1_7_perturbation_spectrum_outputs_without_evaluation(tmp_path: Path) -> None:
    paths = build_v1_7_perturbation_spectrum(tmp_path / "out")
    for key in [
        "read",
        "decision",
        "witness_spectrum",
        "perturbation_curve",
        "weather_curve",
        "quiet_lane_activation",
        "input_schema",
        "evaluation",
        "audit",
        "bundle",
    ]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["evaluation_decision"] == "perturbation_spectrum_locked_evaluation_not_run"
    assert decision["gate_kind"] == GATE_KIND
    assert decision["core_question"] == CORE_QUESTION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["new_heavy_evidence_added"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["core_question_closed"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert set(REQUIRED_SPECTRUM_LANES) <= set(decision["required_spectrum_lanes"])

    readme = paths["read"].read_text(encoding="utf-8")
    assert "No perturbation summary CSV was supplied" in readme
    assert "Do not rely on one scalar" in readme
    assert NEXT_GATE in readme

    spectrum = paths["witness_spectrum"].read_text(encoding="utf-8")
    for lane in REQUIRED_SPECTRUM_LANES:
        assert lane in spectrum
    assert "never a false crown" in readme


def test_v1_7_perturbation_spectrum_rows_are_complete() -> None:
    lanes = {row["lane"] for row in WITNESS_SPECTRUM_ROWS}
    assert set(REQUIRED_SPECTRUM_LANES) <= lanes
    for row in WITNESS_SPECTRUM_ROWS:
        assert row["expected_curve_behavior"]
        assert row["safe_failure_state"]
        assert row["must_not_do"]
        assert row["primary_countermetric"]

    rungs = {row["weather_rung"] for row in WEATHER_RUNG_ROWS}
    assert rungs == {"triad27", "deep81", "wide243"}


def test_v1_7_perturbation_evaluation_classifies_rows() -> None:
    rows = _sample_rows()
    evaluation = evaluate_perturbation_spectrum_rows(rows)
    assert collapse_spectrum_evaluation_decision(evaluation) == "expand_perturbation_spectrum_safe_failure_visible"
    assert any(row["row_status"] == "expand_spectrum_lanes_visible_safe" for row in evaluation)
    assert all(row["final_false_one_crowns"] == 0 for row in evaluation)

    stop = dict(rows[0])
    stop["final_false_one_crowns"] = 1
    assert classify_spectrum_row(stop) == "resist_false_crown_stop"
    assert collapse_spectrum_evaluation_decision(evaluate_perturbation_spectrum_rows([stop])) == "resist_perturbation_false_crown_stop"


def test_v1_7_perturbation_spectrum_with_evaluation_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "summary.csv"
    _write_summary(csv_path, _sample_rows())
    paths = build_v1_7_perturbation_spectrum(tmp_path / "out", spectrum_summary_csv=csv_path)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    readme = paths["read"].read_text(encoding="utf-8")
    evaluation = paths["evaluation"].read_text(encoding="utf-8")

    assert decision["evaluation_decision"] == "expand_perturbation_spectrum_safe_failure_visible"
    assert decision["evaluation_rows"] == 3
    assert "expand_spectrum_lanes_visible_safe" in readme
    assert "wide243" in evaluation
    assert "final_false_one_crowns" in evaluation


def test_v1_7_perturbation_spectrum_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_perturbation_spectrum_read.md").exists()
    assert (out / "v1_7_perturbation_spectrum_bundle.zip").exists()


def test_v1_7_4_public_surfaces_and_version_truth() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    spectrum_doc = read("docs/v1_7_witness_spectrum.md")
    curve_doc = read("docs/v1_7_perturbation_curve.md")
    weather_doc = read("docs/v1_7_weather_curve_summary.md")
    quiet_doc = read("docs/v1_7_expected_quiet_lane_activation.md")
    release = read("docs/release_notes/v1_7_4_alpha.md")

    assert "1.7.4-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.4a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-perturbation-spectrum" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, spectrum_doc, curve_doc, weather_doc, quiet_doc, release]:
        assert "v1.7.4-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    assert "Perturbation Spectrum Witness" in readme
    assert "Perturbation Spectrum Witness" in roadmap
    assert "spectrum, not scalar" in curve_doc
    assert "triad27" in weather_doc and "deep81" in weather_doc and "wide243" in weather_doc
    assert "final false-one crowns" in quiet_doc
    assert "no new heavy evidence crown" in release
    assert "v1.7.5-alpha" in readme
    assert "v1.7.5-alpha" in roadmap
