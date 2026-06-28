from zerogate_sim.gates import evaluate_run, polarity_score, return_score
from zerogate_sim.signals import generate_pressure_field


def test_gate_evaluation_returns_all_candidates() -> None:
    run = generate_pressure_field(seed=42, n_steps=200, dt=0.05)
    rows = evaluate_run(run)
    assert len(rows) == len(run.specs)
    assert all(0.0 <= row.zero_coherence <= 1.0 for row in rows)
    assert all(0 <= row.zero_depth <= 4 for row in rows)


def test_polarity_score_balanced_signal_high() -> None:
    run = generate_pressure_field(seed=42, n_steps=200, dt=0.05)
    stable = run.signals[0]
    assert polarity_score(stable) > 0.5


def test_return_score_not_only_any_signal() -> None:
    run = generate_pressure_field(seed=42, n_steps=200, dt=0.05)
    no_return = run.signals[2]
    assert return_score(no_return) < 0.7
