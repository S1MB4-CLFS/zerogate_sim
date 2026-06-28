from zerogate_sim.gates import trinary_outcome_from_scores


def test_trinary_outcome_expressed():
    value, outcome, reason, latent = trinary_outcome_from_scores(
        expressed=True,
        strength=0.8,
        distinction=0.9,
        polarity=0.9,
        relation=0.9,
        return_observed=0.9,
        return_potential=0.8,
        zero_coherence=0.9,
        zero_depth=4,
        gate_threshold=0.55,
        strength_threshold=0.40,
    )
    assert value == 1
    assert outcome == "expressed"
    assert reason == "earned_expression"
    assert latent == 1.0


def test_trinary_outcome_strength_hold_z4():
    value, outcome, reason, latent = trinary_outcome_from_scores(
        expressed=False,
        strength=0.22,
        distinction=0.9,
        polarity=0.9,
        relation=0.9,
        return_observed=0.9,
        return_potential=0.8,
        zero_coherence=0.9,
        zero_depth=4,
        gate_threshold=0.55,
        strength_threshold=0.40,
    )
    assert value == 0
    assert outcome == "held_latent"
    assert reason == "strength_hold_z4"
    assert 0.0 < latent < 1.0


def test_trinary_outcome_return_debt_hold():
    value, outcome, reason, latent = trinary_outcome_from_scores(
        expressed=False,
        strength=0.45,
        distinction=1.0,
        polarity=0.9,
        relation=0.9,
        return_observed=0.12,
        return_potential=0.81,
        zero_coherence=0.12,
        zero_depth=0,
        gate_threshold=0.55,
        strength_threshold=0.40,
    )
    assert value == 0
    assert outcome == "held_latent"
    assert reason == "return_debt_dpr_hold"


def test_trinary_outcome_rejected():
    value, outcome, reason, latent = trinary_outcome_from_scores(
        expressed=False,
        strength=0.2,
        distinction=0.4,
        polarity=0.2,
        relation=0.1,
        return_observed=0.0,
        return_potential=0.008,
        zero_coherence=0.0,
        zero_depth=0,
        gate_threshold=0.55,
        strength_threshold=0.40,
    )
    assert value == -1
    assert outcome == "rejected"
    assert reason == "insufficient_zero_gate_coherence"
