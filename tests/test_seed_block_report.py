from __future__ import annotations

import csv
from pathlib import Path

import pytest

from zerogate_sim.seed_block_report import build_seed_block_rows, write_seed_block_report


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _matrix_dir(root: Path, run_id: str, *, profile: str, candidate_profile: str, earned: int = 0, false_pressure: int = 0, latent: int = 0, relation_debt: int = 0, breach: int = 0) -> Path:
    path = root / run_id
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("matrix_summary.md").write_text(
        "\n".join(
            [
                "# ZeroGateSim Trinary Matrix Summary",
                f"Profile: `{profile}`",
                f"Candidate profile: `{candidate_profile}`",
                "Seeds per scenario: `0` through `2`",
                "Total runs: `81`",
            ]
        ),
        encoding="utf-8",
    )
    _write_csv(
        path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F00",
                "kind": "stable_core",
                "truth_role": "expresser",
                "final_trinary_value": 1 if earned else 0,
                "final_trinary_symbol": "+1" if earned else "0",
                "final_earned_one_count": earned,
                "raw_expression_pressure": earned + false_pressure,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": relation_debt,
            },
            {
                "candidate_id": "F26",
                "kind": "trap",
                "truth_role": "trap",
                "final_trinary_value": -1,
                "final_trinary_symbol": "-1",
                "final_earned_one_count": 0,
                "raw_expression_pressure": false_pressure,
                "raw_false_one_pressure": false_pressure,
                "false_one_demoted_count": false_pressure,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": 0,
            },
        ],
    )
    _write_csv(
        path / "matrix_known_logic_closeout_summary.csv",
        [
            {
                "mirror": "fuzzy_many_valued",
                "primary_pressure_count": false_pressure + latent,
                "secondary_pressure_count": relation_debt,
                "safety_breach_count": breach,
                "closeout_status": "breach" if breach else "pressure_visible",
                "loss_report": "continuous pressure is not final earned-one",
            },
            {
                "mirror": "paraconsistent_conflict_locality",
                "primary_pressure_count": 0,
                "secondary_pressure_count": 0,
                "safety_breach_count": 0,
                "closeout_status": "localized_or_quiet",
                "loss_report": "conflict locality only",
            },
        ],
    )
    return path


def _four_gate_fixture(root: Path) -> list[Path]:
    return [
        _matrix_dir(root, "distinction_triad27", profile="triad27", candidate_profile="adversary_distinction", earned=0, false_pressure=0),
        _matrix_dir(root, "polarity_triad27", profile="triad27", candidate_profile="adversary_polarity", earned=2, false_pressure=138),
        _matrix_dir(root, "relation_triad27", profile="triad27", candidate_profile="adversary_relation", earned=2, false_pressure=30),
        _matrix_dir(root, "return_triad27", profile="triad27", candidate_profile="adversary_return", earned=2, false_pressure=60, relation_debt=3),
    ]


def test_build_seed_block_rows_requires_four_native_gates(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    rows = build_seed_block_rows(dirs)
    assert [row["gate"] for row in rows] == ["distinction", "polarity", "relation", "return"]
    assert rows[-1]["candidate_profile"] == "adversary_return"
    assert rows[-1]["raw_false_one_pressure"] == 60
    assert rows[-1]["seed_block_status"] == "pressure_visible_no_breach"


def test_build_seed_block_rows_fails_when_return_gate_missing(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")[:3]
    with pytest.raises(ValueError, match="return"):
        build_seed_block_rows(dirs)


def test_write_seed_block_report_outputs_read_and_bundle(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    out = tmp_path / "report"
    paths = write_seed_block_report(output_dir=out, matrix_dirs=dirs)
    read = paths["seed_block_four_gate_read"].read_text(encoding="utf-8")
    assert "Seed-Block Four-Gate Adversary Report" in read
    assert "return" in read
    assert "Final false-one crowns: `0`" in read
    assert "pass_pressure_visible" in read
    assert paths["seed_block_report_bundle"].exists()
