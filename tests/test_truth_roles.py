import csv
import zipfile

from zerogate_sim.gates import evaluate_run
from zerogate_sim.matrix import run_matrix
from zerogate_sim.signals import candidate_specs, generate_pressure_field


def test_candidate_truth_roles_are_trinary() -> None:
    specs = {spec.candidate_id: spec for spec in candidate_specs("triad27")}
    assert specs["F00"].truth_role == "expresser"
    assert specs["F10"].truth_role == "latent"
    assert specs["F26"].truth_role == "trap"
    assert specs["F13"].truth_role == "latent"
    assert specs["F13"].designed_stable is False


def test_gate_rows_include_truth_role_and_echo_diagnostic() -> None:
    run = generate_pressure_field(seed=0, n_steps=180, dt=0.05, specs=candidate_specs("triad27"))
    rows = evaluate_run(run, strength_threshold=0.40)
    by_id = {row.candidate_id: row for row in rows}
    assert by_id["F00"].truth_role == "expresser"
    assert by_id["F10"].expected_trinary == 0
    assert by_id["F26"].expected_trinary == -1
    assert 0.0 <= by_id["F26"].echo_mimic_score <= 1.0
    assert by_id["F26"].echo_mimic_band in {
        "low_echo_pressure",
        "moderate_echo_pressure",
        "high_echo_pressure",
        "echo_breach",
    }


def test_matrix_writes_truth_role_and_echo_outputs(tmp_path) -> None:
    paths = run_matrix(
        profile="triad27",
        candidate_profile="alpha12",
        start_seed=0,
        count=1,
        steps=90,
        dt=0.05,
        output_dir=tmp_path / "matrix_truth",
        make_plots=False,
    )
    assert paths["matrix_truth_role_read"].exists()
    assert paths["matrix_echo_mimic_report"].exists()

    with open(paths["matrix_truth_role_candidate_summary"], newline="", encoding="utf-8") as f:
        candidate_rows = list(csv.DictReader(f))
    by_id = {row["candidate_id"]: row for row in candidate_rows}
    assert by_id["F10"]["truth_role"] == "latent"
    assert by_id["F00"]["truth_role"] == "expresser"

    with zipfile.ZipFile(paths["matrix_bundle"]) as zf:
        names = set(zf.namelist())
    assert "matrix_truth_role_read.md" in names
    assert "matrix_echo_mimic_report.md" in names
