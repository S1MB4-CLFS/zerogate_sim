from __future__ import annotations

from pathlib import Path

from zerogate_sim.three_valued_mirror import (
    THREE_FALSE,
    THREE_TRUE,
    THREE_UNKNOWN,
    build_three_valued_mirror_rows_from_final_rows,
    write_three_valued_mirror_outputs,
)


def test_three_valued_projection_maps_final_symbols() -> None:
    rows = build_three_valued_mirror_rows_from_final_rows(
        [
            {
                "candidate_id": "E",
                "kind": "earned",
                "truth_role": "expresser",
                "final_trinary_symbol": "+1",
                "final_band": "earned_one",
            },
            {
                "candidate_id": "H",
                "kind": "hold",
                "truth_role": "latent",
                "final_trinary_symbol": "0",
                "final_band": "latent_contained",
            },
            {
                "candidate_id": "R",
                "kind": "reject",
                "truth_role": "trap",
                "final_trinary_symbol": "-1",
                "final_band": "trap_contained",
            },
        ]
    )

    by_id = {str(row["candidate_id"]): row for row in rows}
    assert by_id["E"]["kleene_value"] == THREE_TRUE
    assert by_id["H"]["kleene_value"] == THREE_UNKNOWN
    assert by_id["R"]["kleene_value"] == THREE_FALSE
    assert by_id["H"]["zero_compression_loss_flag"] == 1


def test_three_valued_unknown_collapses_specific_zero_bands() -> None:
    rows = build_three_valued_mirror_rows_from_final_rows(
        [
            {
                "candidate_id": "D",
                "kind": "debt",
                "truth_role": "expresser",
                "final_trinary_symbol": "0",
                "final_band": "relation_debt_hold",
                "relation_debt_count": 3,
            },
            {
                "candidate_id": "L",
                "kind": "latent",
                "truth_role": "latent",
                "final_trinary_symbol": "0",
                "final_band": "latent_overcrown_demoted",
                "latent_overcrown_pressure": 2,
            },
        ]
    )

    bands = {str(row["zero_compression_loss_band"]) for row in rows}
    assert "relation_debt_collapsed_to_unknown" in bands
    assert "latent_overcrown_collapsed_to_unknown" in bands


def test_three_valued_write_outputs(tmp_path: Path) -> None:
    paths = write_three_valued_mirror_outputs(
        tmp_path,
        final_rows=[
            {
                "candidate_id": "F10",
                "kind": "weak_stable",
                "truth_role": "latent",
                "runs": 9,
                "final_trinary_symbol": "0",
                "final_band": "latent_contained",
            }
        ],
    )

    assert paths["matrix_three_valued_mirror_summary"].exists()
    read = paths["matrix_three_valued_mirror_read"].read_text(encoding="utf-8")
    assert "Kleene / Lukasiewicz Compression Mirror" in read
    assert "Zero-compression loss candidates" in read
