from zerogate_sim.lineage import classify_lineage, write_lineage_outputs


def _row(candidate_id="F00", designed=True, early="witness_hold", witness="fertile_hold", late="expressed"):
    return {
        "scenario": "s",
        "seed": 0,
        "candidate_id": candidate_id,
        "kind": "stable_core",
        "designed_stable": designed,
        "early_band": early,
        "witness_band": witness,
        "late_band": late,
        "transition_signature": "0>0+>+1",
        "temporal_band": "temporal_expression",
        "endurance_score": 0.75,
    }


def test_lineage_classifies_maturation():
    assert classify_lineage(_row()) == "matured_to_expression"


def test_lineage_outputs_are_written(tmp_path):
    rows = [_row(), _row(candidate_id="F02", designed=False, early="rejected", witness="rejected", late="rejected")]
    paths = write_lineage_outputs(tmp_path, rows)
    assert paths["matrix_lineage_read"].exists()
    assert paths["matrix_lineage_transitions"].exists()
    assert paths["matrix_lineage_candidate_summary"].exists()
