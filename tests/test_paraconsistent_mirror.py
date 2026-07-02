from __future__ import annotations

from zerogate_sim.belnap_mirror import BELNAP_BOTH, BELNAP_FALSE_ONLY, BELNAP_NEITHER, BELNAP_TRUE_ONLY
from zerogate_sim.paraconsistent_mirror import (
    PARA_CONFLICT_LOCALIZED,
    PARA_CONFLICT_OVERCROWNED,
    PARA_FALSE_WITHOUT_CONFLICT,
    PARA_NEITHER_WITHOUT_CONFLICT,
    PARA_TRUE_WITHOUT_CONFLICT,
    build_paraconsistent_mirror_rows_from_belnap_rows,
    build_paraconsistent_mirror_rows_from_final_rows,
    paraconsistent_value_from_belnap_row,
    write_paraconsistent_mirror_outputs,
)


def _belnap_row(**kwargs):
    row = {
        "candidate_id": "F00",
        "kind": "stable_core",
        "truth_role": "expresser",
        "final_trinary_symbol": "0",
        "final_band": "latent_contained",
        "belnap_value": BELNAP_NEITHER,
        "belnap_symbol": "N",
        "evidence_for_final_one": 0,
        "evidence_against_final_one": 0,
    }
    row.update(kwargs)
    return row


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


def test_paraconsistent_projection_localizes_belnap_both_when_not_crowned() -> None:
    value, explosion, reason = paraconsistent_value_from_belnap_row(
        _belnap_row(
            candidate_id="F26",
            truth_role="trap",
            final_trinary_symbol="-1",
            final_band="false_one_demoted",
            belnap_value=BELNAP_BOTH,
            belnap_symbol="B",
            evidence_for_final_one=4,
            evidence_against_final_one=4,
        )
    )
    assert value == PARA_CONFLICT_LOCALIZED
    assert explosion == 0
    assert "localized" in reason or "held" in reason


def test_paraconsistent_projection_flags_conflict_overcrown() -> None:
    value, explosion, reason = paraconsistent_value_from_belnap_row(
        _belnap_row(
            final_trinary_symbol="+1",
            final_band="earned_one",
            belnap_value=BELNAP_BOTH,
            belnap_symbol="B",
            evidence_for_final_one=2,
            evidence_against_final_one=1,
        )
    )
    assert value == PARA_CONFLICT_OVERCROWNED
    assert explosion == 1
    assert "crowned" in reason


def test_paraconsistent_projection_maps_nonconflict_states() -> None:
    true_value, true_explosion, _ = paraconsistent_value_from_belnap_row(
        _belnap_row(belnap_value=BELNAP_TRUE_ONLY, evidence_for_final_one=3, belnap_symbol="T")
    )
    false_value, false_explosion, _ = paraconsistent_value_from_belnap_row(
        _belnap_row(belnap_value=BELNAP_FALSE_ONLY, evidence_against_final_one=2, belnap_symbol="F")
    )
    neither_value, neither_explosion, _ = paraconsistent_value_from_belnap_row(
        _belnap_row(belnap_value=BELNAP_NEITHER, belnap_symbol="N")
    )
    assert (true_value, true_explosion) == (PARA_TRUE_WITHOUT_CONFLICT, 0)
    assert (false_value, false_explosion) == (PARA_FALSE_WITHOUT_CONFLICT, 0)
    assert (neither_value, neither_explosion) == (PARA_NEITHER_WITHOUT_CONFLICT, 0)


def test_build_paraconsistent_rows_from_belnap_rows_preserves_locality_metrics() -> None:
    rows = build_paraconsistent_mirror_rows_from_belnap_rows(
        [
            _belnap_row(candidate_id="F00", belnap_value=BELNAP_TRUE_ONLY, belnap_symbol="T", evidence_for_final_one=5),
            _belnap_row(candidate_id="F26", belnap_value=BELNAP_BOTH, belnap_symbol="B", evidence_for_final_one=2, evidence_against_final_one=4),
        ]
    )
    assert rows[0]["paraconsistent_value"] == PARA_TRUE_WITHOUT_CONFLICT
    assert rows[1]["paraconsistent_value"] == PARA_CONFLICT_LOCALIZED
    assert rows[1]["contradiction_load"] == 2
    assert rows[1]["local_explosion_flag"] == 0


def test_build_paraconsistent_rows_from_final_rows_detects_false_one_conflict() -> None:
    rows = build_paraconsistent_mirror_rows_from_final_rows(
        [
            _final_row(candidate_id="F00", raw_expression_pressure=3, final_earned_one_count=3, final_trinary_symbol="+1", final_band="earned_one"),
            _final_row(
                candidate_id="F26",
                truth_role="trap",
                raw_expression_pressure=2,
                raw_false_one_pressure=2,
                false_one_demoted_count=2,
                final_trinary_symbol="-1",
                final_band="false_one_demoted",
            ),
        ]
    )
    assert rows[0]["paraconsistent_value"] == PARA_TRUE_WITHOUT_CONFLICT
    assert rows[1]["paraconsistent_value"] == PARA_CONFLICT_LOCALIZED
    assert rows[1]["contradiction_load"] == 2


def test_write_paraconsistent_outputs_creates_read_and_csv(tmp_path) -> None:
    final_rows = [
        _final_row(candidate_id="F00", raw_expression_pressure=3, final_earned_one_count=3, final_trinary_symbol="+1", final_band="earned_one"),
        _final_row(
            candidate_id="F26",
            truth_role="trap",
            raw_expression_pressure=2,
            raw_false_one_pressure=2,
            false_one_demoted_count=2,
            final_trinary_symbol="-1",
            final_band="false_one_demoted",
        ),
    ]
    paths = write_paraconsistent_mirror_outputs(tmp_path, final_rows=final_rows)
    assert paths["matrix_paraconsistent_mirror_summary"].exists()
    assert paths["matrix_paraconsistent_mirror_read"].exists()
    text = paths["matrix_paraconsistent_mirror_read"].read_text(encoding="utf-8")
    assert "projection mirror" in text
    assert "conflict-locality" in text
    assert "raw +1 plus debt" in text
