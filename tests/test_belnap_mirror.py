from __future__ import annotations

from zerogate_sim.belnap_mirror import (
    BELNAP_BOTH,
    BELNAP_FALSE_ONLY,
    BELNAP_NEITHER,
    BELNAP_TRUE_ONLY,
    belnap_value_from_final_row,
    build_belnap_mirror_rows_from_final_rows,
    write_belnap_mirror_outputs,
)


def _final_row(**kwargs):
    row = {
        "candidate_id": "F00",
        "kind": "stable_core",
        "truth_role": "expresser",
        "runs": 9,
        "raw_expression_pressure": 0,
        "final_earned_one_count": 0,
        "raw_false_one_pressure": 0,
        "false_one_demoted_count": 0,
        "latent_overcrown_pressure": 0,
        "latent_overcrown_demoted_count": 0,
        "relation_debt_count": 0,
        "final_trinary_symbol": "0",
        "final_band": "latent_contained",
    }
    row.update(kwargs)
    return row


def test_belnap_projection_maps_earned_one_to_true_only() -> None:
    value, symbol, reason = belnap_value_from_final_row(
        _final_row(raw_expression_pressure=5, final_earned_one_count=5, final_trinary_symbol="+1", final_band="earned_one")
    )
    assert value == BELNAP_TRUE_ONLY
    assert symbol == "T"
    assert "earned_one" in reason


def test_belnap_projection_maps_false_one_pressure_to_both() -> None:
    value, symbol, reason = belnap_value_from_final_row(
        _final_row(
            candidate_id="F26",
            truth_role="trap",
            raw_expression_pressure=4,
            raw_false_one_pressure=4,
            false_one_demoted_count=4,
            final_trinary_symbol="-1",
            final_band="false_one_demoted",
        )
    )
    assert value == BELNAP_BOTH
    assert symbol == "B"
    assert "raw_expression_pressure" in reason
    assert "false_one_demoted" in reason


def test_belnap_projection_distinguishes_false_only_and_neither() -> None:
    false_value, false_symbol, _ = belnap_value_from_final_row(
        _final_row(candidate_id="F02", truth_role="trap", final_trinary_symbol="-1", final_band="trap_contained")
    )
    neither_value, neither_symbol, _ = belnap_value_from_final_row(
        _final_row(candidate_id="F10", truth_role="latent", final_trinary_symbol="0", final_band="latent_contained")
    )
    assert false_value == BELNAP_FALSE_ONLY
    assert false_symbol == "F"
    assert neither_value == BELNAP_NEITHER
    assert neither_symbol == "N"


def test_build_belnap_rows_and_write_outputs(tmp_path) -> None:
    final_rows = [
        _final_row(candidate_id="F00", raw_expression_pressure=3, final_earned_one_count=3, final_trinary_symbol="+1", final_band="earned_one"),
        _final_row(candidate_id="F26", truth_role="trap", raw_expression_pressure=2, raw_false_one_pressure=2, false_one_demoted_count=2, final_trinary_symbol="-1", final_band="false_one_demoted"),
    ]
    rows = build_belnap_mirror_rows_from_final_rows(final_rows)
    assert [row["belnap_value"] for row in rows] == [BELNAP_TRUE_ONLY, BELNAP_BOTH]

    paths = write_belnap_mirror_outputs(tmp_path, final_rows=final_rows)
    assert paths["matrix_belnap_mirror_summary"].exists()
    assert paths["matrix_belnap_mirror_read"].exists()
    text = paths["matrix_belnap_mirror_read"].read_text(encoding="utf-8")
    assert "projection mirror" in text
    assert "Belnap" in text
