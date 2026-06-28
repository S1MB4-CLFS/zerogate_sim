from __future__ import annotations

import csv
import zipfile

from zerogate_sim.finalize import finalize_matrix_dir


def test_finalize_existing_matrix_dir_from_earned_summary(tmp_path):
    earned_csv = tmp_path / "matrix_earned_one_summary.csv"
    rows = [
        {
            "candidate_id": "F00",
            "kind": "stable_core",
            "truth_role": "expresser",
            "runs": "3",
            "raw_expressed_count": "3",
            "earned_one_count": "3",
            "false_one_count": "0",
            "latent_overcrown_count": "0",
            "relation_debt_count": "0",
            "relation_minus_raw_expression": "1",
            "relation_zero_raw_expression": "1",
            "relation_plus_raw_expression": "1",
            "echo_independence_band": "independent_expression",
            "relation_dependency_score": "0.0",
            "echo_independence_score": "1.0",
            "mean_strength": "0.7",
            "mean_zero_coherence": "0.8",
            "mean_return_potential": "0.8",
            "mean_return_observed": "0.8",
        },
        {
            "candidate_id": "F26",
            "kind": "field_echo",
            "truth_role": "trap",
            "runs": "3",
            "raw_expressed_count": "1",
            "earned_one_count": "0",
            "false_one_count": "1",
            "latent_overcrown_count": "0",
            "relation_debt_count": "0",
            "relation_minus_raw_expression": "0",
            "relation_zero_raw_expression": "0",
            "relation_plus_raw_expression": "1",
            "echo_independence_band": "echo_breach",
            "relation_dependency_score": "0.6",
            "echo_independence_score": "0.4",
            "mean_strength": "0.5",
            "mean_zero_coherence": "0.6",
            "mean_return_potential": "0.7",
            "mean_return_observed": "0.6",
        },
    ]
    with earned_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    paths = finalize_matrix_dir(tmp_path)
    assert paths["matrix_final_output_read"].exists()
    assert paths["matrix_theory_confirmation_read"].exists()
    text = paths["matrix_final_output_read"].read_text(encoding="utf-8")
    assert "final false-one crowns: `0`" in text
    assert "F26" in text
    with zipfile.ZipFile(paths["matrix_bundle"]) as zf:
        names = set(zf.namelist())
    assert "matrix_final_output_read.md" in names
    assert "matrix_theory_confirmation_read.md" in names
