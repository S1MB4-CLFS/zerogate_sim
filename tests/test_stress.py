from __future__ import annotations

import csv
import zipfile

from zerogate_sim.stress import run_stress


def test_stress_writes_bundle(tmp_path):
    out = tmp_path / "stress"
    paths = run_stress(
        start_seed=0,
        count=2,
        steps=160,
        output_dir=out,
        scenario_names=["baseline", "noisy"],
        make_plots=False,
    )

    assert paths["stress_bundle"].exists()
    assert paths["stress_summary"].exists()
    assert paths["stress_seed_summary"].exists()
    assert paths["stress_scenario_summary"].exists()
    assert paths["stress_candidate_summary"].exists()

    with paths["stress_scenario_summary"].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {row["scenario"] for row in rows} == {"baseline", "noisy"}

    with zipfile.ZipFile(paths["stress_bundle"]) as zf:
        names = set(zf.namelist())
    assert "stress_summary.md" in names
    assert "stress_scenario_summary.csv" in names
    assert "baseline/seed_0/summary.md" in names
    assert "noisy/seed_1/gate_scores.csv" in names
