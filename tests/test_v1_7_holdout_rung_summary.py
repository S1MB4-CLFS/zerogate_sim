from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_holdout_rung_summary import (
    CURRENT_VERSION,
    NATIVE_WITNESS,
    build_v1_7_holdout_rung_summary,
    main,
)


def write_matrix(path: Path, *, earned: int, raw: int, latent: int, relation: int, return_debt: int, false_pressure: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "truth_role",
        "final_trinary_symbol",
        "final_trinary_value",
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
        writer.writerow({
            "truth_role": "expresser",
            "final_trinary_symbol": "+1",
            "final_trinary_value": "1",
            "raw_expression_pressure": raw,
            "final_earned_one_count": earned,
            "raw_false_one_pressure": false_pressure,
            "false_one_demoted_count": false_pressure,
            "latent_overcrown_pressure": latent,
            "latent_overcrown_demoted_count": latent,
            "relation_debt_count": relation,
            "return_debt_count": return_debt,
        })
    return path


def test_holdout_rung_summary_outputs_expected_layers(tmp_path: Path) -> None:
    matrices = [
        write_matrix(tmp_path / f"matrix_{i}" / "matrix_final_output_summary.csv", earned=1, raw=2, latent=1, relation=1, return_debt=1, false_pressure=1)
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
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["native_witness"] == NATIVE_WITNESS
    assert decision["core_question_closed"] is False
    assert decision["lane_pattern_matches_expected"] is True
    assert decision["final_false_one_crowns"] == 0
    assert "A false handoff is a false crown" in paths["read"].read_text(encoding="utf-8")


def test_holdout_rung_summary_cli(tmp_path: Path) -> None:
    matrix = write_matrix(tmp_path / "matrix" / "matrix_final_output_summary.csv", earned=1, raw=1, latent=1, relation=1, return_debt=1, false_pressure=1)
    out = tmp_path / "cli"
    assert main(["--rung", "deep81", "--start-seed", "18", "--count", "9", "--matrix-final-output", str(matrix), "--out", str(out)]) == 0
    assert (out / "v1_7_holdout_rung_summary_read.md").exists()
    assert (out / "v1_7_holdout_rung_summary_bundle.zip").exists()
