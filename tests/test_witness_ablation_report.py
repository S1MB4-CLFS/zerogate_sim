from __future__ import annotations

import csv
from pathlib import Path

import pytest

from zerogate_sim.witness_ablation_report import build_ablation_gate_rows, build_ablation_summary_rows, write_witness_ablation_report


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _matrix_dir(
    root: Path,
    run_id: str,
    *,
    profile: str,
    candidate_profile: str,
    earned: int = 0,
    false_pressure: int = 0,
    latent: int = 0,
    relation_debt: int = 0,
) -> Path:
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
                "raw_expression_pressure": earned + relation_debt,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": relation_debt,
            },
            {
                "candidate_id": "F13",
                "kind": "probe",
                "truth_role": "latent",
                "final_trinary_value": 0,
                "final_trinary_symbol": "0+" if latent else "0",
                "final_earned_one_count": 0,
                "raw_expression_pressure": latent,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": 0,
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
    return path


def _four_gate_fixture(root: Path) -> list[Path]:
    return [
        _matrix_dir(root, "distinction_triad27", profile="triad27", candidate_profile="adversary_distinction", earned=0),
        _matrix_dir(root, "polarity_triad27", profile="triad27", candidate_profile="adversary_polarity", earned=2, false_pressure=138),
        _matrix_dir(root, "relation_triad27", profile="triad27", candidate_profile="adversary_relation", earned=2, false_pressure=30, latent=5),
        _matrix_dir(root, "return_triad27", profile="triad27", candidate_profile="adversary_return", earned=2, false_pressure=60, relation_debt=3),
    ]


def test_ablation_requires_four_native_gates(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")[:3]
    with pytest.raises(ValueError, match="return"):
        build_ablation_gate_rows(dirs)


def test_raw_as_final_exposes_false_crown_risk(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    gate_rows = build_ablation_gate_rows(dirs, variants=["control", "raw_as_final"])
    summary = {row["variant"]: row for row in build_ablation_summary_rows(gate_rows)}

    assert summary["control"]["final_false_one_crowns"] == 0
    assert summary["control"]["false_one_demoted_count"] == 228
    assert summary["raw_as_final"]["final_false_one_crowns"] == 228
    assert summary["raw_as_final"]["ablation_status"] == "breach_introduced"


def test_specific_witness_ablations_report_promoted_pressure(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    gate_rows = build_ablation_gate_rows(dirs, variants=["control", "no_latent_hold", "no_echo_independence"])
    summary = {row["variant"]: row for row in build_ablation_summary_rows(gate_rows)}

    assert summary["no_latent_hold"]["promoted_latent_pressure"] == 5
    assert summary["no_latent_hold"]["pressure_hidden_by_ablation"] == 5
    assert summary["no_echo_independence"]["promoted_relation_debt"] == 3
    assert summary["no_echo_independence"]["pressure_hidden_by_ablation"] == 3


def test_write_witness_ablation_report_outputs_read_and_bundle(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    out = tmp_path / "report"
    paths = write_witness_ablation_report(output_dir=out, matrix_dirs=dirs)
    read = paths["witness_ablation_read"].read_text(encoding="utf-8")

    assert "Witness Ablation Report" in read
    assert "raw_as_final" in read
    assert "Control final false-one crowns: `0`" in read
    assert "Maximum final false-one crowns under ablation: `228`" in read
    assert paths["witness_ablation_bundle"].exists()
