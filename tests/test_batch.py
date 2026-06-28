from __future__ import annotations

import zipfile
from pathlib import Path

from zerogate_sim.batch import run_batch


def test_batch_writes_uploadable_bundle(tmp_path: Path) -> None:
    out = tmp_path / "sweep"
    paths = run_batch(start_seed=0, count=2, steps=120, output_dir=out, make_plots=False)

    bundle = paths["batch_bundle"]
    assert bundle.exists()
    assert bundle.name == "batch_bundle.zip"

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert "batch_summary.md" in names
    assert "batch_seed_summary.csv" in names
    assert "batch_candidate_summary.csv" in names
    assert "seed_0/summary.md" in names
    assert "seed_1/gate_scores.csv" in names
    assert "bundle_manifest.json" in names
