from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.runs_inventory_report import classify_run_dir, write_runs_inventory_report


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_classify_run_dir_protects_history_and_marks_handoffs() -> None:
    assert classify_run_dir("proof_wide243_0_8_v033")[0] == "keep_history"
    assert classify_run_dir("controlled_deep81_four_gate_v1_5_4")[0] == "keep_history"
    assert classify_run_dir("assistant_test_handoff_v1_6_9_discrimination")[0] == "archive_or_delete_after_confirmation"
    assert classify_run_dir("mystery_folder")[0] == "witness_review_before_action"


def test_runs_inventory_report_writes_no_delete_plan(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    for name in ["proof_wide243_0_8_v033", "assistant_test_handoff_v1_6_9_discrimination", "mystery_folder"]:
        folder = runs / name
        folder.mkdir(parents=True)
        (folder / "note.txt").write_text("x", encoding="utf-8")
    paths = write_runs_inventory_report(output_dir=tmp_path / "out", runs_dir=runs)
    rows = _read_rows(paths["runs_inventory_csv"])
    by_name = {row["name"]: row for row in rows}
    assert by_name["proof_wide243_0_8_v033"]["classification"] == "keep_history"
    assert by_name["assistant_test_handoff_v1_6_9_discrimination"]["classification"] == "archive_or_delete_after_confirmation"
    read = paths["runs_cleanup_plan"].read_text(encoding="utf-8")
    audit = json.loads(paths["runs_inventory_audit"].read_text(encoding="utf-8"))
    assert "does not delete files" in read
    assert audit["deletes_files"] is False
    assert audit["safety"] == "classification_only_no_delete_default"
