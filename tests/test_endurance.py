from zerogate_sim.config import SimulationConfig
from zerogate_sim.endurance import build_temporal_rows, classify_temporal_endurance
from zerogate_sim.gates import evaluate_run
from zerogate_sim.matrix import apply_signal_pressure, apply_spec_pressure, build_scenarios, run_matrix
from zerogate_sim.signals import generate_pressure_field, default_candidate_specs


def test_temporal_rows_use_three_windows():
    scenario = build_scenarios("triad27")[13]
    specs = apply_spec_pressure(default_candidate_specs(), scenario)
    run = generate_pressure_field(seed=0, n_steps=300, dt=0.05, specs=specs)
    rows = build_temporal_rows(
        run=run,
        scenario=scenario.name,
        seed=0,
        noise_axis=scenario.noise_axis,
        relation_axis=scenario.relation_axis,
        expansion_axis=scenario.expansion_axis,
        perturbation_axis=scenario.perturbation_axis,
        noise_floor=scenario.noise_floor,
        gate_threshold=scenario.gate_threshold,
        strength_threshold=scenario.strength_threshold,
    )
    assert len(rows) == len(run.specs)
    first = rows[0]
    assert first["transition_signature"].count(">") == 2
    assert first["return_cycle_trace"].count(">") == 2
    assert "temporal_band" in first
    assert 0.0 <= float(first["endurance_score"]) <= 1.0


def test_temporal_classification_detects_expression():
    run = generate_pressure_field(seed=1, n_steps=600, dt=0.05)
    rows = evaluate_run(run, noise_floor=0.12, gate_threshold=0.55, strength_threshold=0.40)
    stable = next(row for row in rows if row.candidate_id == "F00")
    value, band, symbol, reason, score = classify_temporal_endurance([stable, stable, stable])
    assert value == 1
    assert band == "temporal_expression"
    assert symbol == "+1T"
    assert score > 0.5


def test_matrix_writes_temporal_outputs(tmp_path):
    paths = run_matrix(profile="triad27", start_seed=0, count=1, steps=240, output_dir=tmp_path / "matrix")
    assert paths["matrix_temporal_read"].exists()
    assert paths["matrix_temporal_trace"].exists()
    assert paths["matrix_temporal_candidate_summary"].exists()
    assert "matrix_temporal_read.md" in paths["matrix_bundle"].read_bytes().decode("latin1", errors="ignore")
