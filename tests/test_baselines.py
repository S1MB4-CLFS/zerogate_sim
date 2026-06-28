from __future__ import annotations

from zerogate_sim.baselines import compare_models
from zerogate_sim.gates import evaluate_run
from zerogate_sim.signals import generate_pressure_field


def test_zero_gate_expression_model_uses_strength_boundary() -> None:
    run = generate_pressure_field(seed=0, n_steps=600, dt=0.05)
    rows = evaluate_run(run)
    comparisons = {row.model: row for row in compare_models(rows, truth_field="designed_stable", seed=0)}

    # F10 often reaches Z^4, but should be held back by strength. The expression
    # model represents the full current operator; raw zero_gate_min is kept visible
    # as diagnostic pressure.
    assert "zero_gate_expression" in comparisons
    assert comparisons["zero_gate_expression"].accuracy >= comparisons["zero_gate_min"].accuracy
