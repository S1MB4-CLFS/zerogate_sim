from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.shadow_discrimination_report import write_shadow_discrimination_report

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _comparison_fixture(path: Path) -> Path:
    rows: list[dict[str, object]] = []
    target_values = {
        "target_raw_false_one_rate": [0.0, 0.5, 1.0, 1.5],
        "target_false_pressure_density_rate": [0.2, 0.1, 1.2, 0.9],
        "target_relation_false_pressure_share": [0.0, 0.8, 0.1, 0.7],
    }
    model_scores = {
        "target_raw_false_one_rate": {
            "shadow_score": [0.0, 0.4, 0.7, 0.9],
            "raw_pressure_only": [0.0, 0.5, 1.0, 1.5],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
        "target_false_pressure_density_rate": {
            "shadow_score": [0.2, 0.1, 1.2, 0.9],
            "raw_pressure_only": [0.0, 0.5, 1.0, 1.5],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
        "target_relation_false_pressure_share": {
            "shadow_score": [0.1, 0.4, 0.2, 0.5],
            "raw_strength_only": [0.0, 0.8, 0.1, 0.7],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
    }
    for target_name, targets in target_values.items():
        for index, target in enumerate(targets):
            for model_name, scores in model_scores[target_name].items():
                rows.append(
                    {
                        "rung": "triad27",
                        "scope": "family",
                        "row_key": f"triad27::family_{index}",
                        "source_label": "triad27",
                        "source_profile": "triad27_hardened_cell",
                        "family_id": f"family_{index}",
                        "model_name": model_name,
                        "model_score": scores[index],
                        "target_name": target_name,
                        "target_value": target,
                        "evaluation_family_label": f"gate:{index}",
                        "evaluation_boundary": "targets_compared_after_scores_no_role_labels_loaded_as_features",
                    }
                )
    _write_csv(path, rows)
    return path


def test_shadow_discrimination_report_writes_expected_files(tmp_path: Path) -> None:
    comparison = _comparison_fixture(tmp_path / "weather_hardening_baseline_comparison.csv")
    paths = write_shadow_discrimination_report(output_dir=tmp_path / "out", hardening_comparison=comparison)
    for key in [
        "shadow_discrimination_target_metrics",
        "shadow_discrimination_residual_metrics",
        "shadow_discrimination_lane_summary",
        "shadow_discrimination_decision",
        "shadow_discrimination_audit",
        "shadow_discrimination_read",
        "shadow_discrimination_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_discrimination_names_density_only_and_specific_resist(tmp_path: Path) -> None:
    comparison = _comparison_fixture(tmp_path / "weather_hardening_baseline_comparison.csv")
    paths = write_shadow_discrimination_report(output_dir=tmp_path / "out", hardening_comparison=comparison)
    decision = json.loads(paths["shadow_discrimination_decision"].read_text(encoding="utf-8"))
    lanes = _read_rows(paths["shadow_discrimination_lane_summary"])
    residuals = _read_rows(paths["shadow_discrimination_residual_metrics"])
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["global_decision"] == "witness_shadow_density_only_specific_discrimination_not_earned"
    by_lane = {row["lane"]: row["lane_state"] for row in lanes}
    assert by_lane["density_pressure"] == "expand_lane_has_candidate_signal"
    assert by_lane["raw_false_one"] == "witness_lane_trivial_tie"
    assert by_lane["relation_specific"] == "resist_lane_under_baseline"
    relation = next(row for row in residuals if row["target_name"] == "target_relation_false_pressure_share")
    assert relation["best_baseline_model"] == "raw_strength_only"


def test_shadow_discrimination_read_keeps_boundary(tmp_path: Path) -> None:
    comparison = _comparison_fixture(tmp_path / "weather_hardening_baseline_comparison.csv")
    paths = write_shadow_discrimination_report(output_dir=tmp_path / "out", hardening_comparison=comparison)
    read = paths["shadow_discrimination_read"].read_text(encoding="utf-8")
    assert "does not retune the shadow score" in read
    assert "does not claim role-blind discovery" in read
    assert "C_Z = min(D, P, R, B)" in read
    assert "z(target)-z(best_available_baseline_score)" in read


def test_shadow_discrimination_docs_and_readme_name_v1_6_9_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    history = (ROOT / "docs/history_vault/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_discrimination_repair.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_9_alpha.md").read_text(encoding="utf-8")
    for text in [history, doc, release]:
        assert "v1.6.9-alpha" in text
    assert "does not retune" in doc
    assert "not role-blind discovery" in doc
    assert "docs/version_truth.md" in readme
    assert "docs/test_truth_and_handoff_boundary.md" in readme
