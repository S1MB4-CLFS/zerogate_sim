from __future__ import annotations

import csv
from pathlib import Path

from zerogate_sim.echo_independence import build_echo_independence_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.matrix import run_matrix


def _row(candidate_id: str, *, kind: str = "field_echo", role: str = "trap", expressed: bool = False) -> GateScores:
    return GateScores(
        candidate_id=candidate_id,
        kind=kind,
        description="test row",
        designed_stable=False,
        truth_role=role,
        expected_trinary=-1 if role == "trap" else 0 if role == "latent" else 1,
        strength=0.5,
        distinction=1.0,
        polarity=0.9,
        relation=1.0,
        return_observed=0.7,
        return_potential=0.9,
        echo_mimic_score=0.2,
        echo_mimic_band="low_echo_pressure",
        zero_coherence=0.7,
        zero_depth=4,
        expressed=expressed,
        trinary_value=1 if expressed else -1,
        trinary_outcome="expressed" if expressed else "rejected",
        outcome_reason="test",
        latent_score=0.0,
        zero_band_value=1 if expressed else -1,
        zero_band="expressed" if expressed else "rejected",
        zero_band_symbol="+1" if expressed else "-1",
        zero_band_reason="test",
        limiting_gate="return",
        observed_stability_score=0.0,
        observed_stable=False,
    )


def test_echo_independence_outputs(tmp_path: Path) -> None:
    paths = run_matrix(
        profile="triad27",
        candidate_profile="triad27",
        start_seed=0,
        count=1,
        steps=90,
        output_dir=tmp_path / "matrix_echo",
        make_plots=False,
    )
    assert paths["matrix_echo_independence_summary"].exists()
    assert paths["matrix_echo_independence_read"].exists()
    text = paths["matrix_echo_independence_read"].read_text(encoding="utf-8")
    assert "Echo-Independence" in text
    assert "relation-plus" in text
    with paths["matrix_echo_independence_summary"].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert {"candidate_id", "echo_independence_band", "relation_dependency_score"}.issubset(rows[0])


def test_echo_independence_detects_relation_plus_trap_pressure() -> None:
    gate_rows = []
    for seed in range(3):
        gate_rows.append((seed, _row(f"nZ_rM_eZ:F26", expressed=False)))
        gate_rows.append((seed, _row(f"nZ_rZ_eZ:F26", expressed=False)))
        gate_rows.append((seed, _row(f"nZ_rP_eZ:F26", expressed=True)))
    rows = {row["candidate_id"]: row for row in build_echo_independence_rows(gate_rows)}
    f26 = rows["F26"]
    assert f26["echo_independence_band"] == "echo_breach"
    assert f26["echo_independence_reason"] == "trap_expression_relation_plus_dependent"
    assert float(f26["relation_dependency_score"]) > 0.9
