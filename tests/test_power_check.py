from __future__ import annotations

import csv

from zerogate_sim.power_check import build_power_check, main, write_power_check_outputs


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_minimal_witness_artifacts(matrix_dir):
    rows = [{"candidate_id": "F00", "status": "present"}]
    for name in [
        "matrix_earned_one_summary.csv",
        "matrix_echo_independence_summary.csv",
        "matrix_temporal_candidate_summary.csv",
        "matrix_lineage_candidate_summary.csv",
        "matrix_seed_summary.csv",
    ]:
        if name == "matrix_seed_summary.csv":
            _write_csv(matrix_dir / name, [{"scenario": "s0", "seed": "0", "best_designed_model": "zero_gate_expression"}])
        else:
            _write_csv(matrix_dir / name, rows)


def test_power_check_reaches_predictive_zero_ready_floor(tmp_path) -> None:
    _write_csv(
        tmp_path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F00",
                "kind": "stable_core",
                "truth_role": "expresser",
                "runs": "9",
                "raw_expression_pressure": "9",
                "final_earned_one_count": "9",
                "raw_false_one_pressure": "0",
                "false_one_demoted_count": "0",
                "latent_overcrown_pressure": "0",
                "latent_overcrown_demoted_count": "0",
                "relation_debt_count": "0",
                "final_trinary_value": "1",
                "final_trinary_symbol": "+1",
                "final_band": "earned_one",
            },
            {
                "candidate_id": "F10",
                "kind": "weak_stable",
                "truth_role": "latent",
                "runs": "9",
                "raw_expression_pressure": "3",
                "final_earned_one_count": "0",
                "raw_false_one_pressure": "0",
                "false_one_demoted_count": "0",
                "latent_overcrown_pressure": "3",
                "latent_overcrown_demoted_count": "3",
                "relation_debt_count": "0",
                "final_trinary_value": "0",
                "final_trinary_symbol": "0+",
                "final_band": "latent_overcrown_demoted",
            },
            {
                "candidate_id": "F26",
                "kind": "field_echo",
                "truth_role": "trap",
                "runs": "9",
                "raw_expression_pressure": "2",
                "final_earned_one_count": "0",
                "raw_false_one_pressure": "2",
                "false_one_demoted_count": "2",
                "latent_overcrown_pressure": "0",
                "latent_overcrown_demoted_count": "0",
                "relation_debt_count": "0",
                "final_trinary_value": "-1",
                "final_trinary_symbol": "-1",
                "final_band": "false_one_demoted",
            },
        ],
    )
    _write_minimal_witness_artifacts(tmp_path)

    result = build_power_check(tmp_path)

    assert result.posture == "power"
    assert result.reached_power == 3
    assert {row["status"] for row in result.summary_rows[:4]} == {"pass"}
    assert result.summary_rows[4]["status"] == "hold"


def test_power_check_fails_on_final_false_one_crown(tmp_path) -> None:
    _write_csv(
        tmp_path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F26",
                "kind": "field_echo",
                "truth_role": "trap",
                "runs": "9",
                "raw_expression_pressure": "2",
                "final_earned_one_count": "2",
                "raw_false_one_pressure": "2",
                "false_one_demoted_count": "0",
                "latent_overcrown_pressure": "0",
                "latent_overcrown_demoted_count": "0",
                "relation_debt_count": "0",
                "final_trinary_value": "1",
                "final_trinary_symbol": "+1",
                "final_band": "earned_one",
            }
        ],
    )

    result = build_power_check(tmp_path)

    assert result.posture == "fail"
    assert any(row["fail_state"] == "FAIL B" and row["status"] == "fail" for row in result.fail_rows)


def test_write_power_check_outputs_creates_report_files(tmp_path) -> None:
    _write_csv(
        tmp_path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F00",
                "kind": "stable_core",
                "truth_role": "expresser",
                "runs": "1",
                "raw_expression_pressure": "1",
                "final_earned_one_count": "1",
                "raw_false_one_pressure": "0",
                "false_one_demoted_count": "0",
                "latent_overcrown_pressure": "0",
                "latent_overcrown_demoted_count": "0",
                "relation_debt_count": "0",
                "final_trinary_value": "1",
                "final_trinary_symbol": "+1",
                "final_band": "earned_one",
            }
        ],
    )

    paths = write_power_check_outputs(tmp_path)

    assert paths["matrix_power_check_summary"].exists()
    assert paths["matrix_power_check_fail_summary"].exists()
    assert paths["matrix_power_check_read"].exists()
    assert "Power-Up / Fail" in paths["matrix_power_check_read"].read_text(encoding="utf-8")


def test_power_check_cli_returns_nonzero_on_hard_fail(tmp_path) -> None:
    _write_csv(
        tmp_path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F26",
                "kind": "field_echo",
                "truth_role": "trap",
                "runs": "1",
                "raw_expression_pressure": "1",
                "final_earned_one_count": "1",
                "raw_false_one_pressure": "1",
                "false_one_demoted_count": "0",
                "latent_overcrown_pressure": "0",
                "latent_overcrown_demoted_count": "0",
                "relation_debt_count": "0",
                "final_trinary_value": "1",
                "final_trinary_symbol": "+1",
                "final_band": "earned_one",
            }
        ],
    )

    assert main(["--matrix-dir", str(tmp_path)]) == 1
