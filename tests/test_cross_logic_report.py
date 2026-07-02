from __future__ import annotations

import csv
import zipfile
from pathlib import Path

import pytest

from zerogate_sim.cross_logic_report import (
    build_cross_logic_rows,
    build_matrix_summary_rows,
    build_mirror_summary_rows,
    read_matrix_identity,
    write_cross_logic_report_outputs,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fake_matrix(path: Path, *, profile: str = "triad27", candidate_profile: str = "alpha12", fuzzy_pressure: int = 3, breach: int = 0) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("matrix_summary.md").write_text(
        f"# Matrix\n\nProfile: `{profile}`\nCandidate profile: `{candidate_profile}`\n",
        encoding="utf-8",
    )
    _write_csv(
        path / "matrix_known_logic_closeout_summary.csv",
        [
            {
                "mirror": "fuzzy_many_valued",
                "native_question": "gate pressure",
                "primary_pressure_count": fuzzy_pressure,
                "secondary_pressure_count": 1,
                "safety_breach_count": 0,
                "closeout_status": "average_overcrown_visible" if fuzzy_pressure else "quiet",
                "useful_when": "continuous gate comparison",
                "loss_report": "cannot crown earned-one alone",
            },
            {
                "mirror": "paraconsistent_conflict_locality",
                "native_question": "conflict locality",
                "primary_pressure_count": 2,
                "secondary_pressure_count": breach,
                "safety_breach_count": breach,
                "closeout_status": "breach" if breach else "localized_or_quiet",
                "useful_when": "conflict stays local",
                "loss_report": "not metaphysical proof",
            },
        ],
    )
    _write_csv(
        path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F00",
                "truth_role": "expresser",
                "final_earned_one_count": 4,
                "raw_false_one_pressure": 0,
                "latent_overcrown_pressure": 1,
                "final_trinary_value": 1,
                "final_trinary_symbol": "+1",
            },
            {
                "candidate_id": "F26",
                "truth_role": "trap",
                "final_earned_one_count": 0,
                "raw_false_one_pressure": 2,
                "latent_overcrown_pressure": 0,
                "final_trinary_value": -1,
                "final_trinary_symbol": "-1",
            },
        ],
    )
    return path


def test_read_matrix_identity_from_summary(tmp_path: Path) -> None:
    matrix = _fake_matrix(tmp_path / "matrix_a", profile="wide243", candidate_profile="adversary_relation")
    identity = read_matrix_identity(matrix)
    assert identity.matrix_label == "matrix_a"
    assert identity.profile == "wide243"
    assert identity.candidate_profile == "adversary_relation"


def test_build_cross_logic_rows_and_summaries(tmp_path: Path) -> None:
    a = _fake_matrix(tmp_path / "matrix_a", fuzzy_pressure=5)
    b = _fake_matrix(tmp_path / "matrix_b", fuzzy_pressure=0, breach=1)

    rows = build_cross_logic_rows([a, b])
    assert len(rows) == 4
    assert {row["matrix_label"] for row in rows} == {"matrix_a", "matrix_b"}

    matrix_rows = build_matrix_summary_rows(rows)
    assert len(matrix_rows) == 2
    matrix_b = [row for row in matrix_rows if row["matrix_label"] == "matrix_b"][0]
    assert matrix_b["comparison_status"] == "breach"
    assert matrix_b["final_false_one_crowns"] == 0

    mirror_rows = build_mirror_summary_rows(rows)
    fuzzy = [row for row in mirror_rows if row["mirror"] == "fuzzy_many_valued"][0]
    assert fuzzy["primary_pressure_total"] == 5
    assert fuzzy["matrices_read"] == 2


def test_write_cross_logic_report_outputs(tmp_path: Path) -> None:
    a = _fake_matrix(tmp_path / "matrix_a", fuzzy_pressure=5)
    out_dir = tmp_path / "comparison"
    paths = write_cross_logic_report_outputs([a], out_dir)

    assert paths["cross_logic_comparison_summary"].exists()
    assert paths["cross_logic_comparison_matrix_summary"].exists()
    assert paths["cross_logic_comparison_mirror_summary"].exists()
    assert paths["cross_logic_comparison_read"].exists()
    assert "projection mirrors" in paths["cross_logic_comparison_read"].read_text(encoding="utf-8")

    bundle = paths["cross_logic_report_bundle"]
    assert bundle.exists()
    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert "cross_logic_comparison_read.md" in names
    assert "cross_logic_comparison_matrix_summary.csv" in names


def test_missing_closeout_csv_is_explicit(tmp_path: Path) -> None:
    missing = tmp_path / "missing_matrix"
    missing.mkdir()
    with pytest.raises(FileNotFoundError, match="matrix_known_logic_closeout_summary.csv"):
        build_cross_logic_rows([missing])
