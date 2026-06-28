from zerogate_sim.earned_one import build_earned_one_rows
from zerogate_sim.gates import GateScores


def _row(candidate_id: str, *, role: str, expressed: bool, kind: str = "k") -> GateScores:
    return GateScores(
        candidate_id=candidate_id,
        kind=kind,
        description="",
        designed_stable=role == "expresser",
        truth_role=role,
        expected_trinary={"trap": -1, "latent": 0, "expresser": 1}[role],
        strength=0.7 if expressed else 0.2,
        distinction=0.8,
        polarity=0.8,
        relation=0.8,
        return_observed=0.8,
        return_potential=0.8,
        echo_mimic_score=0.0,
        echo_mimic_band="low_echo_pressure",
        zero_coherence=0.8,
        zero_depth=4,
        expressed=expressed,
        trinary_value=1 if expressed else -1,
        trinary_outcome="expressed" if expressed else "rejected",
        outcome_reason="",
        latent_score=0.0,
        zero_band_value=1 if expressed else -1,
        zero_band="expressed" if expressed else "rejected",
        zero_band_symbol="+1" if expressed else "-1",
        zero_band_reason="",
        limiting_gate="return",
        observed_stability_score=0.0,
        observed_stable=False,
    )


def test_earned_one_separates_expresser_and_trap_expression():
    rows = [
        (0, _row("s_rM_eZ:F00", role="expresser", expressed=True, kind="stable_core")),
        (0, _row("s_rP_eZ:F26", role="trap", expressed=True, kind="field_echo")),
        (0, _row("s_rP_eZ:F16", role="latent", expressed=True, kind="deep_bridge")),
    ]
    out = {row["candidate_id"]: row for row in build_earned_one_rows(rows)}
    assert out["F00"]["earned_one_count"] == 1
    assert out["F26"]["false_one_count"] == 1
    assert out["F16"]["latent_overcrown_count"] == 1
