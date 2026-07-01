from __future__ import annotations

from types import SimpleNamespace

from zerogate_sim.fuzzy_mirror import (
    build_fuzzy_candidate_summary_rows,
    build_fuzzy_mirror_rows,
    fuzzy_average,
    fuzzy_lukasiewicz,
    fuzzy_min,
    fuzzy_product,
    write_fuzzy_mirror_outputs,
)


def _row(**kwargs):
    defaults = {
        "candidate_id": "F_test",
        "kind": "test_kind",
        "truth_role": "expresser",
        "strength": 1.0,
        "distinction": 0.9,
        "polarity": 0.9,
        "relation": 0.9,
        "return_observed": 0.2,
        "zero_coherence": 0.2,
        "limiting_gate": "return",
        "trinary_value": 0,
        "zero_band": "witness_hold",
        "zero_band_symbol": "0",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_fuzzy_conjunction_mirrors_are_bounded() -> None:
    values = (0.9, 0.8, 0.7, 0.6)
    assert fuzzy_min(values) == 0.6
    assert 0.0 <= fuzzy_product(values) <= 1.0
    assert fuzzy_average(values) == sum(values) / len(values)
    assert fuzzy_lukasiewicz((1.0, 1.0, 1.0, 1.0)) == 1.0
    assert fuzzy_lukasiewicz((0.5, 0.5, 0.5, 0.5)) == 0.0


def test_build_fuzzy_mirror_rows_detects_average_overcrown_pressure() -> None:
    rows = build_fuzzy_mirror_rows([(7, _row())], threshold=0.55)
    assert len(rows) == 1
    row = rows[0]
    assert row["native_min_gate"] == 0.2
    assert row["average_gate"] > 0.55
    assert row["average_overcrown_pressure"] == 1
    assert row["native_band"] == "below_threshold"
    assert row["average_band"] == "passes_threshold"


def test_candidate_summary_counts_mirror_pressure() -> None:
    trace = build_fuzzy_mirror_rows(
        [
            (1, _row(candidate_id="F00", return_observed=0.2, zero_coherence=0.2)),
            (2, _row(candidate_id="F00", return_observed=0.9, zero_coherence=0.9, limiting_gate="distinction")),
        ],
        threshold=0.55,
    )
    summary = build_fuzzy_candidate_summary_rows(trace)
    assert summary[0]["candidate_id"] == "F00"
    assert summary[0]["runs"] == 2
    assert summary[0]["average_overcrown_pressure_count"] == 1
    assert summary[0]["native_threshold_pass_count"] == 1


def test_write_fuzzy_mirror_outputs_creates_files(tmp_path) -> None:
    paths = write_fuzzy_mirror_outputs(tmp_path, [(3, _row())], threshold=0.55)
    assert paths["matrix_fuzzy_mirror_trace"].exists()
    assert paths["matrix_fuzzy_mirror_candidate_summary"].exists()
    assert paths["matrix_fuzzy_mirror_read"].exists()
    text = paths["matrix_fuzzy_mirror_read"].read_text(encoding="utf-8")
    assert "projection mirror" in text
    assert "Average-overcrown pressure" in text
