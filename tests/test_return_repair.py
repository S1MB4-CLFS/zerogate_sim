from __future__ import annotations

from zerogate_sim.gates import evaluate_run, return_score
from zerogate_sim.signals import generate_pressure_field


def _row_map(seed: int):
    run = generate_pressure_field(seed=seed, n_steps=600, dt=0.05)
    rows = evaluate_run(run)
    return {row.candidate_id: row for row in rows}


def test_return_repair_keeps_deep_returner_alive_for_known_brittle_seeds() -> None:
    # v0.2.2 sometimes gave F08 return=0 on these seeds because the full-cycle
    # return check was too brittle for slow coherent pulses.
    for seed in (0, 7):
        rows = _row_map(seed)
        assert rows["F08"].return_observed >= 0.55
        assert rows["F08"].expressed


def test_return_repair_rejects_memory_reset_trap_in_seed_sweep() -> None:
    for seed in range(10):
        rows = _row_map(seed)
        assert not rows["F05"].expressed


def test_default_seed_expresses_only_designed_stable_candidates() -> None:
    rows = _row_map(42)
    expressed = {candidate_id for candidate_id, row in rows.items() if row.expressed}
    assert expressed == {"F00", "F01", "F08"}


def test_return_score_penalizes_collapse_after_shock() -> None:
    run = generate_pressure_field(seed=7, n_steps=600, dt=0.05)
    rows = {row.candidate_id: row for row in evaluate_run(run)}
    assert rows["F07"].return_observed < 0.55
