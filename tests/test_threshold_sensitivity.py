from __future__ import annotations

import csv
from pathlib import Path

import argparse

import pytest

from zerogate_sim.threshold_sensitivity import (
    ThresholdVariant,
    build_threshold_gate_rows,
    build_threshold_summary_rows,
    parse_variant_arg,
    write_threshold_sensitivity_report,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _seed_block_report_dir(root: Path, label: str, *, earned: int, raw_false: int, final_false: int = 0, mirror_breach: int = 0) -> Path:
    path = root / label
    summary_rows = []
    for gate in ["distinction", "polarity", "relation", "return"]:
        gate_false = raw_false if gate == "return" else 0
        gate_earned = earned if gate == "return" else 0
        summary_rows.append(
            {
                "gate": gate,
                "matrix_label": f"{gate}_triad27",
                "candidate_profile": f"adversary_{gate}",
                "seed_range": "0-2",
                "total_runs": 81,
                "final_earned_one_events": gate_earned,
                "raw_false_one_pressure": gate_false,
                "false_one_demoted_count": gate_false,
                "latent_overcrown_pressure": 0,
                "relation_debt_count": 0,
                "final_false_one_crowns": final_false if gate == "return" else 0,
                "trap_final_crowns": final_false if gate == "return" else 0,
                "mirror_primary_pressure": gate_false + 10,
                "mirror_secondary_pressure": 3,
                "mirror_safety_breach_total": mirror_breach if gate == "return" else 0,
                "seed_block_status": "breach" if final_false or mirror_breach else "pressure_visible_no_breach",
            }
        )
    mirror_rows = [
        {
            "mirror": "fuzzy_many_valued",
            "gates_read": 4,
            "primary_pressure_total": raw_false + 40,
            "secondary_pressure_total": 12,
            "safety_breach_total": mirror_breach,
            "gate_pressure_summary": f"return:{raw_false}",
            "dominant_status": "breach" if mirror_breach else "pressure_visible",
            "loss_report": "fuzzy score is pressure not final one",
        }
    ]
    _write_csv(path / "seed_block_four_gate_summary.csv", summary_rows)
    _write_csv(path / "seed_block_four_gate_mirror_summary.csv", mirror_rows)
    (path / "seed_block_four_gate_read.md").write_text(f"# report {label}\n", encoding="utf-8")
    return path


def test_parse_variant_arg_requires_label_path() -> None:
    parsed = parse_variant_arg("baseline=runs/baseline")
    assert parsed.label == "baseline"
    assert str(parsed.report_dir).endswith("baseline")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_variant_arg("broken")


def test_build_threshold_summary_rows_tracks_deltas(tmp_path: Path) -> None:
    baseline = _seed_block_report_dir(tmp_path, "baseline", earned=2, raw_false=60)
    loose = _seed_block_report_dir(tmp_path, "loose", earned=3, raw_false=72)
    rows = build_threshold_summary_rows([
        ThresholdVariant("baseline", baseline),
        ThresholdVariant("loose", loose),
    ])
    assert rows[0]["earned_delta_from_baseline"] == 0
    assert rows[1]["earned_delta_from_baseline"] == 1
    assert rows[1]["raw_false_delta_from_baseline"] == 12
    assert rows[1]["threshold_status"] == "pressure_visible_no_breach"


def test_build_threshold_gate_rows_preserves_gate_variant_rows(tmp_path: Path) -> None:
    baseline = _seed_block_report_dir(tmp_path, "baseline", earned=2, raw_false=60)
    rows = build_threshold_gate_rows([ThresholdVariant("baseline", baseline)])
    assert len(rows) == 4
    assert {row["gate"] for row in rows} == {"distinction", "polarity", "relation", "return"}
    assert [row for row in rows if row["gate"] == "return"][0]["raw_false_one_pressure"] == 60


def test_write_threshold_sensitivity_report_outputs_read_and_bundle(tmp_path: Path) -> None:
    low = _seed_block_report_dir(tmp_path, "gate_050", earned=3, raw_false=72)
    mid = _seed_block_report_dir(tmp_path, "gate_055", earned=2, raw_false=60)
    high = _seed_block_report_dir(tmp_path, "gate_060", earned=1, raw_false=44)
    out = tmp_path / "threshold_report"
    paths = write_threshold_sensitivity_report(
        output_dir=out,
        variants=[
            ThresholdVariant("gate_050", low),
            ThresholdVariant("gate_055", mid),
            ThresholdVariant("gate_060", high),
        ],
    )
    read = paths["threshold_sensitivity_read"].read_text(encoding="utf-8")
    assert "Threshold Sensitivity Report" in read
    assert "gate_050" in read
    assert "gate_060" in read
    assert "Final false-one crowns across variants: `0`" in read
    assert paths["threshold_sensitivity_bundle"].exists()


def test_matrix_records_threshold_overrides(tmp_path: Path) -> None:
    from zerogate_sim.matrix import run_matrix

    out = tmp_path / "matrix_threshold_override"
    paths = run_matrix(
        profile="triad27",
        candidate_profile="alpha12",
        start_seed=0,
        count=1,
        steps=40,
        output_dir=out,
        gate_threshold=0.50,
        strength_threshold=0.25,
    )
    text = paths["matrix_summary"].read_text(encoding="utf-8")
    assert "Gate threshold override: `0.500`" in text
    assert "Strength threshold override: `0.250`" in text
