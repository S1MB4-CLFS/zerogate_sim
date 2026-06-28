from zerogate_sim.gates import zero_band_from_scores


def _band(**overrides):
    data = dict(
        trinary_value=0,
        trinary_outcome="held_latent",
        outcome_reason="test",
        strength=0.36,
        distinction=0.9,
        polarity=0.9,
        relation=0.9,
        return_observed=0.50,
        return_potential=0.73,
        zero_coherence=0.50,
        zero_depth=3,
        gate_threshold=0.55,
        strength_threshold=0.40,
    )
    data.update(overrides)
    return zero_band_from_scores(**data)


def test_zero_band_expressed_is_plus_one():
    value, band, symbol, reason = _band(trinary_value=1, trinary_outcome="expressed")
    assert value == 1
    assert band == "expressed"
    assert symbol == "+1"
    assert reason == "earned_one"


def test_zero_band_fertile_z4_near_expression():
    value, band, symbol, reason = _band(
        zero_depth=4,
        zero_coherence=0.58,
        strength=0.36,
        return_observed=0.50,
    )
    assert value == 1
    assert band == "fertile_hold"
    assert symbol == "0+"
    assert reason == "near_expression_z4"


def test_zero_band_witness_hold_for_weak_but_coherent_z4():
    value, band, symbol, reason = _band(
        zero_depth=4,
        zero_coherence=0.58,
        strength=0.24,
        return_observed=0.56,
    )
    assert value == 0
    assert band == "witness_hold"
    assert symbol == "0"
    assert reason == "needs_more_return_pressure"


def test_zero_band_quarantine_for_return_gap():
    value, band, symbol, reason = _band(
        return_potential=0.90,
        zero_depth=0,
        return_observed=0.28,
        strength=0.40,
    )
    assert value == -1
    assert band == "quarantine_hold"
    assert symbol == "0-"
    assert reason == "return_gap_quarantine"
