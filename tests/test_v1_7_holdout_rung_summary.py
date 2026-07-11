from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest

from zerogate_sim.v1_7_holdout_rung_summary import (
    CURRENT_VERSION,
    NATIVE_WITNESS,
    build_v1_7_holdout_rung_summary,
    main,
)


def write_matrix(
    path: Path,
    *,
    runs: int = 10,
    role: str = "expresser",
    earned: int = 1,
    raw: int = 5,
    latent: int = 1,
    relation: int = 1,
    return_debt: int = 1,
    false_pressure: int = 1,
    final_symbol: str = "+1",
    candidate_id: str = "C0",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "truth_role",
        "candidate_id",
        "final_trinary_symbol",
        "final_trinary_value",
        "runs",
        "raw_expression_pressure",
        "final_earned_one_count",
        "raw_false_one_pressure",
        "false_one_demoted_count",
        "latent_overcrown_pressure",
        "latent_overcrown_demoted_count",
        "relation_debt_count",
        "return_debt_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "truth_role": role,
                "candidate_id": candidate_id,
                "final_trinary_symbol": final_symbol,
                "final_trinary_value": "1" if final_symbol == "+1" else "-1",
                "runs": runs,
                "raw_expression_pressure": raw,
                "final_earned_one_count": earned,
                "raw_false_one_pressure": false_pressure,
                "false_one_demoted_count": false_pressure,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": relation,
                "return_debt_count": return_debt,
            }
        )
    return path


def _read_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        return next(csv.DictReader(f))


def test_holdout_rung_summary_is_denominated_and_fail_closed(tmp_path: Path) -> None:
    matrices = [
        write_matrix(
            tmp_path / f"matrix_{i}" / "matrix_final_output_summary.csv",
            runs=10,
            earned=1,
            raw=5,
            latent=1,
            relation=1,
            return_debt=1,
            false_pressure=1,
            candidate_id=f"C{i}",
        )
        for i in range(5)
    ]
    paths = build_v1_7_holdout_rung_summary(
        tmp_path / "out",
        rung="triad27",
        start_seed=18,
        count=9,
        matrix_final_outputs=matrices,
    )
    for key in ["row", "read", "top_card", "full_report", "matrix_totals", "html_card", "summary_json", "decision", "bundle"]:
        assert paths[key].exists(), key

    row = _read_row(paths["row"])
    assert row["opportunities"] == "50"
    assert float(row["earned_one_rate"]) == pytest.approx(5 / 50)
    assert float(row["raw_expression_rate"]) == pytest.approx(25 / 50)
    assert row["candidate_names_masked"] == "not_verified"
    assert row["expected_manifest_frozen"] == "not_verified"
    assert row["reference_profile_reused"] == "not_verified"
    assert row["lane_pattern_matches_expected"] == "not_a_pass_condition"

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["native_witness"] == NATIVE_WITNESS
    assert decision["core_question_closed"] is False
    assert decision["provenance_verified"] is False
    assert decision["lane_pattern_matches_expected"] is False
    assert decision["scientific_status"] == "HOLD_CONSTRUCTION_BOUND"
    assert "A false handoff is a false crown" in paths["read"].read_text(encoding="utf-8")


def test_duplicate_matrix_artifacts_do_not_inflate_counts(tmp_path: Path) -> None:
    original = write_matrix(tmp_path / "one" / "matrix_final_output_summary.csv", runs=10, earned=2, raw=6)
    duplicate = tmp_path / "copy" / "matrix_final_output_summary.csv"
    duplicate.parent.mkdir(parents=True)
    shutil.copyfile(original, duplicate)

    base = build_v1_7_holdout_rung_summary(
        tmp_path / "base",
        rung="deep81",
        start_seed=18,
        count=9,
        matrix_final_outputs=[original],
    )
    copied = build_v1_7_holdout_rung_summary(
        tmp_path / "copied",
        rung="deep81",
        start_seed=18,
        count=9,
        matrix_final_outputs=[original, original, duplicate],
    )
    base_row = _read_row(base["row"])
    copied_row = _read_row(copied["row"])
    for field in ("opportunities", "final_earned_one_events", "raw_expression_pressure", "earned_one_rate"):
        assert copied_row[field] == base_row[field]
    assert copied_row["input_artifact_count"] == "3"
    assert copied_row["unique_input_artifact_count"] == "1"
    assert copied_row["duplicate_input_artifact_count"] == "2"
    decision = json.loads(copied["decision"].read_text(encoding="utf-8"))
    assert decision["accounting_status"] == "invalid_duplicate_inputs"


def test_trap_only_input_cannot_self_attest_earned_controls(tmp_path: Path) -> None:
    matrix = write_matrix(
        tmp_path / "trap" / "matrix_final_output_summary.csv",
        role="trap",
        earned=0,
        raw=1,
        latent=0,
        relation=0,
        return_debt=0,
        final_symbol="-1",
    )
    paths = build_v1_7_holdout_rung_summary(
        tmp_path / "out",
        rung="triad27",
        start_seed=18,
        count=1,
        matrix_final_outputs=[matrix],
    )
    row = _read_row(paths["row"])
    assert row["earned_controls_present"] == "not_observed"
    assert row["legacy_lane_presence_observed"] == "false"


def test_holdout_rung_summary_rejects_missing_denominator(tmp_path: Path) -> None:
    matrix = write_matrix(tmp_path / "bad" / "matrix_final_output_summary.csv")
    text = matrix.read_text(encoding="utf-8").replace("runs,", "missing_runs,")
    matrix.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="runs"):
        build_v1_7_holdout_rung_summary(
            tmp_path / "out",
            rung="triad27",
            start_seed=18,
            count=1,
            matrix_final_outputs=[matrix],
        )


def test_holdout_rung_summary_rejects_invalid_contract_and_counts(tmp_path: Path) -> None:
    matrix = write_matrix(tmp_path / "matrix" / "matrix_final_output_summary.csv")
    with pytest.raises(ValueError, match="unsupported rung"):
        build_v1_7_holdout_rung_summary(
            tmp_path / "bad_rung",
            rung="bogus",
            start_seed=18,
            count=1,
            matrix_final_outputs=[matrix],
        )
    with pytest.raises(ValueError, match="count must be positive"):
        build_v1_7_holdout_rung_summary(
            tmp_path / "bad_count",
            rung="triad27",
            start_seed=18,
            count=0,
            matrix_final_outputs=[matrix],
        )

    impossible = write_matrix(
        tmp_path / "impossible" / "matrix_final_output_summary.csv",
        runs=2,
        earned=3,
        raw=7,
    )
    with pytest.raises(ValueError, match="0 <= count <= runs"):
        build_v1_7_holdout_rung_summary(
            tmp_path / "bad_counts",
            rung="triad27",
            start_seed=18,
            count=1,
            matrix_final_outputs=[impossible],
        )


def test_holdout_rung_summary_rejects_duplicate_candidate_rows(tmp_path: Path) -> None:
    matrix = write_matrix(tmp_path / "duplicate" / "matrix_final_output_summary.csv")
    with matrix.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with matrix.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows([rows[0], rows[0]])
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        build_v1_7_holdout_rung_summary(
            tmp_path / "out",
            rung="triad27",
            start_seed=18,
            count=1,
            matrix_final_outputs=[matrix],
        )


def test_holdout_rung_summary_cli(tmp_path: Path) -> None:
    matrix = write_matrix(tmp_path / "matrix" / "matrix_final_output_summary.csv")
    out = tmp_path / "cli"
    assert main(["--rung", "deep81", "--start-seed", "18", "--count", "9", "--matrix-final-output", str(matrix), "--out", str(out)]) == 0
    assert (out / "v1_7_holdout_rung_summary_read.md").exists()
    assert (out / "v1_7_holdout_rung_summary_bundle.zip").exists()
