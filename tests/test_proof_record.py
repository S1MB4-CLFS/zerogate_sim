from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

from zerogate_sim.proof_record import freeze_proof_record, summarize_proof_dir


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fake_proof_dir(path: Path) -> Path:
    rows = [
        {
            "axis": "distinction",
            "candidate_profile": "adversary_distinction",
            "description": "fake distinction",
            "matrix_dir": str(path / "distinction"),
            "scenario_count": 243,
            "seed_count": 9,
            "seeded_run_count": 2187,
            "candidate_count": 27,
            "final_earned_one_events": 2320,
            "raw_expression_pressure": 2320,
            "raw_false_one_pressure": 0,
            "false_one_demoted_count": 0,
            "final_false_one_crowns": 0,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "expresser_candidate_count": 4,
            "earned_expresser_candidate_count": 3,
            "trap_candidate_count": 14,
            "trap_final_crown_count": 0,
            "status": "pass",
            "reason": "protected crown",
        },
        {
            "axis": "polarity",
            "candidate_profile": "adversary_polarity",
            "description": "fake polarity",
            "matrix_dir": str(path / "polarity"),
            "scenario_count": 243,
            "seed_count": 9,
            "seeded_run_count": 2187,
            "candidate_count": 27,
            "final_earned_one_events": 4539,
            "raw_expression_pressure": 5136,
            "raw_false_one_pressure": 0,
            "false_one_demoted_count": 0,
            "final_false_one_crowns": 0,
            "latent_overcrown_pressure": 597,
            "latent_overcrown_demoted_count": 597,
            "expresser_candidate_count": 4,
            "earned_expresser_candidate_count": 4,
            "trap_candidate_count": 14,
            "trap_final_crown_count": 0,
            "status": "pass",
            "reason": "protected crown",
        },
        {
            "axis": "relation",
            "candidate_profile": "adversary_relation",
            "description": "fake relation",
            "matrix_dir": str(path / "relation"),
            "scenario_count": 243,
            "seed_count": 9,
            "seeded_run_count": 2187,
            "candidate_count": 27,
            "final_earned_one_events": 4512,
            "raw_expression_pressure": 6315,
            "raw_false_one_pressure": 1206,
            "false_one_demoted_count": 1206,
            "final_false_one_crowns": 0,
            "latent_overcrown_pressure": 597,
            "latent_overcrown_demoted_count": 597,
            "expresser_candidate_count": 4,
            "earned_expresser_candidate_count": 4,
            "trap_candidate_count": 14,
            "trap_final_crown_count": 0,
            "status": "pass",
            "reason": "protected crown",
        },
    ]
    _write_csv(path / "proof_harness_summary.csv", rows)
    (path / "proof_harness_read.md").write_text("Profile: `wide243`\nSeed range: `0` to `8`\n", encoding="utf-8")
    relation_rows = [
        {
            "candidate_id": "F26",
            "kind": "field_echo",
            "truth_role": "trap",
            "raw_expression_pressure": 1044,
            "false_one_demoted_count": 1044,
            "final_earned_one_count": 0,
            "raw_false_one_pressure": 1044,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "final_trinary_symbol": "-1",
            "final_band": "false_one_demoted",
            "echo_independence_band": "trap_breach",
        }
    ]
    _write_csv(path / "relation" / "matrix_final_output_summary.csv", relation_rows)
    distinction_rows = [
        {
            "candidate_id": "F12",
            "kind": "late_maturer",
            "truth_role": "expresser",
            "raw_expression_pressure": 0,
            "false_one_demoted_count": 0,
            "final_earned_one_count": 0,
            "raw_false_one_pressure": 0,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "final_trinary_symbol": "0",
            "final_band": "expresser_wound",
            "echo_independence_band": "contained",
        }
    ]
    _write_csv(path / "distinction" / "matrix_final_output_summary.csv", distinction_rows)
    return path


def test_summarize_proof_dir(tmp_path: Path) -> None:
    proof_dir = _fake_proof_dir(tmp_path / "proof")
    totals, rows, false_candidates, conditional = summarize_proof_dir(proof_dir)
    assert totals.seeded_runs == 6561
    assert totals.scenario_cells == 729
    assert totals.raw_false_one_pressure == 1206
    assert totals.false_one_demoted_count == 1206
    assert totals.final_false_one_crowns == 0
    assert totals.proof_status == "proof_record_candidate"
    assert rows[0]["axis"] == "distinction"
    assert false_candidates[0]["candidate_id"] == "F26"
    assert conditional[0]["candidate_id"] == "F12"


def test_freeze_proof_record_outputs(tmp_path: Path) -> None:
    proof_dir = _fake_proof_dir(tmp_path / "proof")
    paths = freeze_proof_record(proof_dir)
    assert paths["proof_record"].exists()
    assert paths["proof_record_summary"].exists()
    assert paths["proof_record_json"].exists()
    assert paths["proof_bundle"].exists()
    text = paths["proof_record"].read_text(encoding="utf-8")
    assert "Proof Record Freeze" in text
    assert "met false one" in text
    summary = json.loads(paths["proof_record_json"].read_text(encoding="utf-8"))
    assert summary["proof_status"] == "proof_record_candidate"
    with zipfile.ZipFile(paths["proof_bundle"]) as zf:
        assert "proof_record.md" in zf.namelist()
        assert "proof_record_summary.json" in zf.namelist()
