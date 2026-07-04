from zerogate_sim.final_output import build_final_output_rows
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


def test_final_output_uses_earned_one_as_only_final_crown():
    rows = [
        (0, _row("nZ_rM_eZ:F00", role="expresser", expressed=True, kind="stable_core")),
        (0, _row("nZ_rP_eZ:F26", role="trap", expressed=True, kind="field_echo")),
        (0, _row("nZ_rP_eZ:F16", role="latent", expressed=True, kind="deep_bridge")),
    ]
    out = {row["candidate_id"]: row for row in build_final_output_rows(rows)}

    assert out["F00"]["final_band"] == "earned_one"
    assert out["F00"]["final_trinary_value"] == 1

    assert out["F26"]["final_band"] == "false_one_demoted"
    assert out["F26"]["final_trinary_value"] == -1
    assert out["F26"]["false_one_demoted_count"] == 1
    assert out["F26"]["final_earned_one_count"] == 0

    assert out["F16"]["final_band"] == "latent_overcrown_demoted"
    assert out["F16"]["final_trinary_value"] == 0
    assert out["F16"]["latent_overcrown_demoted_count"] == 1


def test_final_output_read_computes_final_false_crowns_from_rows(tmp_path):
    from zerogate_sim.final_output import write_final_output_rows

    rows = [
        {
            "candidate_id": "F26",
            "kind": "field_echo",
            "truth_role": "trap",
            "runs": 1,
            "raw_expression_pressure": 1,
            "final_earned_one_count": 1,
            "raw_false_one_pressure": 1,
            "false_one_demoted_count": 0,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "relation_debt_count": 0,
            "final_trinary_value": 1,
            "final_trinary_symbol": "+1",
            "final_band": "earned_one",
            "final_reason": "malformed fixture: trap was crowned",
            "echo_independence_band": "low_echo_pressure",
            "relation_dependency_score": 0.0,
            "echo_independence_score": 1.0,
            "relation_minus_raw_expression": 0,
            "relation_zero_raw_expression": 0,
            "relation_plus_raw_expression": 1,
            "mean_strength": 1.0,
            "mean_zero_coherence": 1.0,
            "mean_return_potential": 1.0,
            "mean_return_observed": 1.0,
        }
    ]

    paths = write_final_output_rows(tmp_path, rows)
    final_read = paths["matrix_final_output_read"].read_text(encoding="utf-8")
    confirmation = paths["matrix_theory_confirmation_read"].read_text(encoding="utf-8")

    assert "final false-one crowns: `1`" in final_read
    assert "allows `1` final false-one crowns" in confirmation
    assert "Status: `hold`" in confirmation
