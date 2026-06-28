from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.release_record import freeze_release_record, summarize_release


def _write_proof_dir(path: Path, *, seed_range: str, earned: int, raw_false: int) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    data = {
        "profile": "wide243",
        "seed_range": seed_range,
        "corpus_count": 3,
        "scenario_cells": 729,
        "seeded_runs": 6561,
        "final_earned_one_events": earned,
        "raw_expression_pressure": earned + raw_false,
        "raw_false_one_pressure": raw_false,
        "false_one_demoted_count": raw_false,
        "final_false_one_crowns": 0,
        "latent_overcrown_pressure": 9,
        "latent_overcrown_demoted_count": 9,
        "expresser_candidate_count": 12,
        "earned_expresser_candidate_count": 11,
        "trap_candidate_count": 42,
        "trap_final_crown_count": 0,
        "corpora_passed": 3,
        "corpora_hold": 0,
        "corpora_failed": 0,
        "proof_status": "proof_record_candidate",
        "proof_claim": "test claim",
        "next_action": "test next action",
    }
    (path / "proof_record_summary.json").write_text(json.dumps(data), encoding="utf-8")
    return path


def test_summarize_release_passes_with_reproduction(tmp_path: Path) -> None:
    p1 = _write_proof_dir(tmp_path / "proof_a", seed_range="0-8", earned=10, raw_false=3)
    p2 = _write_proof_dir(tmp_path / "proof_b", seed_range="9-17", earned=8, raw_false=4)

    summary, rows = summarize_release([p1, p2])

    assert summary["status"] == "first_research_alpha_passed"
    assert summary["scenario_cells"] == 1458
    assert summary["seeded_runs"] == 13122
    assert summary["final_earned_one_events"] == 18
    assert summary["raw_false_one_pressure"] == 7
    assert summary["false_one_demoted_count"] == 7
    assert summary["final_false_one_crowns"] == 0
    assert len(rows) == 2


def test_freeze_release_record_writes_bundle(tmp_path: Path) -> None:
    p1 = _write_proof_dir(tmp_path / "proof_a", seed_range="0-8", earned=10, raw_false=3)
    p2 = _write_proof_dir(tmp_path / "proof_b", seed_range="9-17", earned=8, raw_false=4)
    out = tmp_path / "release"

    paths = freeze_release_record([p1, p2], out)

    assert paths["first_research_alpha_record"].exists()
    assert paths["first_research_alpha_summary"].exists()
    assert paths["first_research_alpha_csv"].exists()
    assert paths["proof_records_csv"].exists()
    assert paths["release_bundle"].exists()
    text = paths["first_research_alpha_record"].read_text(encoding="utf-8")
    assert "first_research_alpha_passed" in text
    assert "refused the crown" in text
