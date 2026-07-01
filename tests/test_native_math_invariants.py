from __future__ import annotations

import math

from zerogate_sim.final_output import build_final_output_rows_from_earned_rows
from zerogate_sim.gates import (
    evaluate_run,
    zero_band_from_scores,
    zero_depth_from_gates,
)
from zerogate_sim.signals import generate_pressure_field


def test_zero_coherence_is_weakest_gate_and_limiting_gate_names_it() -> None:
    run = generate_pressure_field(seed=42, n_steps=240, dt=0.05)
    rows = evaluate_run(run, gate_threshold=0.55, strength_threshold=0.30)

    for row in rows:
        gate_values = {
            "distinction": row.distinction,
            "polarity": row.polarity,
            "relation": row.relation,
            "return": row.return_observed,
        }
        expected_min = min(gate_values.values())
        assert math.isclose(row.zero_coherence, expected_min, rel_tol=0.0, abs_tol=1e-12)
        assert row.limiting_gate == min(gate_values.items(), key=lambda item: item[1])[0]


def test_return_potential_is_dpr_product_pressure_not_final_truth() -> None:
    run = generate_pressure_field(seed=7, n_steps=240, dt=0.05)
    rows = evaluate_run(run, gate_threshold=0.55, strength_threshold=0.30)

    for row in rows:
        expected = row.distinction * row.polarity * row.relation
        assert math.isclose(row.return_potential, expected, rel_tol=0.0, abs_tol=1e-12)
        assert 0.0 <= row.return_potential <= 1.0


def test_raw_expression_requires_strength_and_zero_gate_thresholds() -> None:
    gate_threshold = 0.55
    strength_threshold = 0.30
    run = generate_pressure_field(seed=9, n_steps=300, dt=0.05)
    rows = evaluate_run(run, gate_threshold=gate_threshold, strength_threshold=strength_threshold)

    for row in rows:
        expected_expression = bool(
            row.strength >= strength_threshold and row.zero_coherence >= gate_threshold
        )
        assert row.expressed is expected_expression


def test_zero_depth_is_ordered_not_flat() -> None:
    threshold = 0.55

    assert zero_depth_from_gates(
        distinction=0.90,
        polarity=0.90,
        relation=0.90,
        return_observed=0.40,
        threshold=threshold,
    ) == 0

    assert zero_depth_from_gates(
        distinction=0.90,
        polarity=0.40,
        relation=0.90,
        return_observed=0.90,
        threshold=threshold,
    ) == 1

    assert zero_depth_from_gates(
        distinction=0.90,
        polarity=0.90,
        relation=0.40,
        return_observed=0.90,
        threshold=threshold,
    ) == 2

    assert zero_depth_from_gates(
        distinction=0.90,
        polarity=0.90,
        relation=0.90,
        return_observed=0.90,
        threshold=threshold,
    ) == 4


def _zero_band_case(**overrides: float | int | str) -> tuple[int, str, str, str]:
    args = {
        "trinary_value": 0,
        "trinary_outcome": "held_latent",
        "outcome_reason": "test_case",
        "strength": 0.30,
        "distinction": 0.55,
        "polarity": 0.55,
        "relation": 0.55,
        "return_observed": 0.45,
        "return_potential": 0.45,
        "zero_coherence": 0.45,
        "zero_depth": 2,
        "gate_threshold": 0.55,
        "strength_threshold": 0.40,
    }
    args.update(overrides)
    return zero_band_from_scores(**args)  # type: ignore[arg-type]


def test_zero_bands_remain_distinct() -> None:
    expressed = _zero_band_case(trinary_value=1)
    rejected = _zero_band_case(trinary_value=-1)
    fertile = _zero_band_case(
        strength=0.36,
        return_observed=0.50,
        zero_coherence=0.56,
        zero_depth=4,
    )
    witness = _zero_band_case(
        strength=0.26,
        relation=0.50,
        return_observed=0.40,
        return_potential=0.45,
        zero_coherence=0.45,
        zero_depth=2,
    )
    quarantine = _zero_band_case(strength=0.10)

    assert expressed[1:] == ("expressed", "+1", "earned_one")
    assert rejected[1:] == ("rejected", "-1", "active_rejection")
    assert fertile[1] == "fertile_hold"
    assert witness[1] == "witness_hold"
    assert quarantine[1] == "quarantine_hold"
    assert {fertile[2], witness[2], quarantine[2]} == {"0+", "0", "0-"}


def _earned_row(
    *,
    candidate_id: str,
    truth_role: str,
    raw: int,
    earned: int,
    false_one: int,
    latent: int,
    relation_debt: int,
    echo_band: str = "contained",
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "kind": "test_candidate",
        "truth_role": truth_role,
        "runs": 3,
        "raw_expressed_count": raw,
        "earned_one_count": earned,
        "false_one_count": false_one,
        "latent_overcrown_count": latent,
        "relation_debt_count": relation_debt,
        "echo_independence_band": echo_band,
        "relation_dependency_score": 0.0,
        "echo_independence_score": 1.0,
        "relation_minus_raw_expression": 0,
        "relation_zero_raw_expression": raw,
        "relation_plus_raw_expression": 0,
        "mean_strength": 0.80,
        "mean_zero_coherence": 0.80,
        "mean_return_potential": 0.80,
        "mean_return_observed": 0.80,
    }


def test_final_output_does_not_crown_raw_expression_automatically() -> None:
    rows = build_final_output_rows_from_earned_rows(
        [
            _earned_row(
                candidate_id="E00",
                truth_role="expresser",
                raw=3,
                earned=3,
                false_one=0,
                latent=0,
                relation_debt=0,
            ),
            _earned_row(
                candidate_id="T00",
                truth_role="trap",
                raw=2,
                earned=0,
                false_one=2,
                latent=0,
                relation_debt=0,
            ),
            _earned_row(
                candidate_id="L00",
                truth_role="latent",
                raw=1,
                earned=0,
                false_one=0,
                latent=1,
                relation_debt=0,
            ),
            _earned_row(
                candidate_id="D00",
                truth_role="expresser",
                raw=1,
                earned=0,
                false_one=0,
                latent=0,
                relation_debt=1,
                echo_band="relation_debt",
            ),
        ]
    )
    by_id = {str(row["candidate_id"]): row for row in rows}

    assert by_id["E00"]["final_trinary_symbol"] == "+1"
    assert by_id["E00"]["final_band"] == "earned_one"

    assert by_id["T00"]["raw_expression_pressure"] == 2
    assert by_id["T00"]["final_trinary_symbol"] == "-1"
    assert by_id["T00"]["final_band"] == "false_one_demoted"

    assert by_id["L00"]["final_trinary_symbol"] == "0+"
    assert by_id["L00"]["final_band"] == "latent_overcrown_demoted"

    assert by_id["D00"]["final_trinary_symbol"] == "0"
    assert by_id["D00"]["final_band"] == "relation_debt_hold"
