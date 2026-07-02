from __future__ import annotations

import csv

from zerogate_sim.gates import evaluate_run
from zerogate_sim.known_logic_closeout import build_known_logic_closeout_rows, write_known_logic_closeout_outputs
from zerogate_sim.signals import generate_pressure_field


def _gate_rows():
    run = generate_pressure_field(seed=4, n_steps=180, dt=0.05)
    rows = evaluate_run(run)
    return list(enumerate(rows))


def test_known_logic_closeout_has_four_mirror_rows() -> None:
    rows = build_known_logic_closeout_rows(_gate_rows())
    assert {row["mirror"] for row in rows} == {
        "fuzzy_many_valued",
        "belnap_evidence_state",
        "paraconsistent_conflict_locality",
        "kleene_lukasiewicz_compression",
    }
    assert all("loss_report" in row for row in rows)
    assert all("useful_when" in row for row in rows)


def test_known_logic_closeout_writes_summary_and_read(tmp_path) -> None:
    paths = write_known_logic_closeout_outputs(tmp_path, _gate_rows())
    assert paths["matrix_known_logic_closeout_summary"].exists()
    assert paths["matrix_known_logic_closeout_read"].exists()

    with paths["matrix_known_logic_closeout_summary"].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert {row["mirror"] for row in rows} == {
        "fuzzy_many_valued",
        "belnap_evidence_state",
        "paraconsistent_conflict_locality",
        "kleene_lukasiewicz_compression",
    }

    text = paths["matrix_known_logic_closeout_read"].read_text(encoding="utf-8")
    assert "Known-Logic Mirror Closeout" in text
    assert "projection mirrors" in text
    assert "not an identity claim" in text
