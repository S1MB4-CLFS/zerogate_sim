from pathlib import Path

from zerogate_sim.matrix import run_matrix
from zerogate_sim.visual_witness import scenario_glyph


def test_scenario_glyph_trinary_zero_bands():
    assert scenario_glyph({"false_positive_runs": 0, "designed_fertile_hold_runs": 0, "designed_witness_hold_runs": 0, "designed_quarantine_hold_runs": 0, "designed_rejected_runs": 0, "mean_designed_accuracy": 1.0, "runs": 9}) == "●"
    assert scenario_glyph({"false_positive_runs": 0, "designed_fertile_hold_runs": 3, "designed_witness_hold_runs": 0, "designed_quarantine_hold_runs": 0, "designed_rejected_runs": 0, "mean_designed_accuracy": 0.99, "runs": 9}) == "◎"
    assert scenario_glyph({"false_positive_runs": 0, "designed_fertile_hold_runs": 0, "designed_witness_hold_runs": 3, "designed_quarantine_hold_runs": 0, "designed_rejected_runs": 0, "mean_designed_accuracy": 0.99, "runs": 9}) == "◌"
    assert scenario_glyph({"false_positive_runs": 0, "designed_fertile_hold_runs": 0, "designed_witness_hold_runs": 0, "designed_quarantine_hold_runs": 3, "designed_rejected_runs": 0, "mean_designed_accuracy": 0.99, "runs": 9}) == "◍"
    assert scenario_glyph({"false_positive_runs": 0, "designed_fertile_hold_runs": 0, "designed_witness_hold_runs": 0, "designed_quarantine_hold_runs": 0, "designed_rejected_runs": 2, "mean_designed_accuracy": 0.91, "runs": 9}) == "△"
    assert scenario_glyph({"false_positive_runs": 1, "designed_fertile_hold_runs": 0, "designed_witness_hold_runs": 0, "designed_quarantine_hold_runs": 0, "designed_rejected_runs": 0, "mean_designed_accuracy": 0.99, "runs": 9}) == "✕"


def test_matrix_writes_glyph_map_and_heatmaps(tmp_path: Path):
    out = tmp_path / "matrix_visual"
    paths = run_matrix(profile="triad27", start_seed=0, count=1, steps=160, output_dir=out, make_plots=False)
    assert paths["matrix_glyph_map"].exists()
    assert paths["matrix_glyph_csv"].exists()
    assert paths["matrix_shape_read"].exists()
    assert paths["matrix_field_atlas"].exists()
    assert (out / "matrix_bundle.zip").exists()
    heatmaps = sorted(out.glob("matrix_glyph_heatmap_*.png"))
    assert len(heatmaps) == 3
    text = paths["matrix_glyph_map"].read_text(encoding="utf-8")
    assert "Glyph legend" in text
    assert "0+ fertile hold" in text
    assert "Noise `minus`" in text
    shape = paths["matrix_shape_read"].read_text(encoding="utf-8")
    assert "Shape verdict" in shape
    assert "Expand" in shape
