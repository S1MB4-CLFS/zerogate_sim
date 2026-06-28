from __future__ import annotations

import zipfile
from pathlib import Path

from zerogate_sim.config import SimulationConfig
from zerogate_sim.demo import run_demo


def test_run_demo_writes_evidence_bundle(tmp_path: Path) -> None:
    out = tmp_path / "demo"
    paths = run_demo(
        SimulationConfig(seed=3, n_steps=120, dt=0.05, output_dir=out),
        make_plots=False,
        make_bundle=True,
    )

    bundle = paths["evidence_bundle"]
    assert bundle.exists()
    assert bundle.name == "run_bundle.zip"

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert "summary.md" in names
    assert "gate_scores.csv" in names
    assert "metadata.json" in names
    assert "bundle_manifest.json" in names
