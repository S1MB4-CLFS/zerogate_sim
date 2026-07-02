from __future__ import annotations

import csv
import zipfile

from zerogate_sim.matrix import build_scenarios, run_matrix


def test_trinary_scenario_counts() -> None:
    assert len(build_scenarios("triad27")) == 27
    assert len(build_scenarios("deep81")) == 81
    assert len(build_scenarios("wide243")) == 243


def test_matrix_bundle_creation(tmp_path) -> None:
    paths = run_matrix(
        profile="triad27",
        start_seed=0,
        count=1,
        steps=90,
        dt=0.05,
        output_dir=tmp_path / "matrix",
        make_plots=False,
    )
    bundle = paths["matrix_bundle"]
    assert bundle.exists()
    assert paths["matrix_summary"].exists()
    assert paths["matrix_axis_summary"].exists()
    assert paths["matrix_fuzzy_mirror_read"].exists()
    assert paths["matrix_belnap_mirror_read"].exists()
    assert paths["matrix_paraconsistent_mirror_read"].exists()
    assert paths["matrix_three_valued_mirror_read"].exists()
    assert paths["matrix_known_logic_closeout_read"].exists()

    with open(paths["matrix_scenario_summary"], newline="", encoding="utf-8") as f:
        scenario_rows = list(csv.DictReader(f))
    assert len(scenario_rows) == 27

    with open(paths["matrix_axis_summary"], newline="", encoding="utf-8") as f:
        axis_rows = list(csv.DictReader(f))
    # triad profile has three axes, each with three levels.
    assert len(axis_rows) == 9

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert "matrix_summary.md" in names
    assert "matrix_axis_summary.csv" in names
    assert "matrix_seed_summary.csv" in names
    assert "matrix_lineage_read.md" in names
    assert "matrix_final_output_read.md" in names
    assert "matrix_theory_confirmation_read.md" in names
    assert "matrix_fuzzy_mirror_read.md" in names
    assert "matrix_fuzzy_mirror_candidate_summary.csv" in names
    assert "matrix_belnap_mirror_read.md" in names
    assert "matrix_belnap_mirror_summary.csv" in names
    assert "matrix_paraconsistent_mirror_read.md" in names
    assert "matrix_paraconsistent_mirror_summary.csv" in names
    assert "matrix_three_valued_mirror_read.md" in names
    assert "matrix_three_valued_mirror_summary.csv" in names
    assert "matrix_known_logic_closeout_read.md" in names
    assert "matrix_known_logic_closeout_summary.csv" in names
