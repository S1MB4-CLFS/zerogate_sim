from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.shadow_lane_discrimination_report import write_shadow_lane_discrimination_report
from zerogate_sim.shadow_score_report import write_shadow_score_report

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


def _evidence_base(tmp_path: Path) -> Path:
    base = tmp_path / "evidence"
    feature_rows = []
    target_rows = []
    targets = {
        "f0": {"density": 0.2, "raw": 0.0, "relation": 0.0, "return": 0.0},
        "f1": {"density": 0.1, "raw": 0.4, "relation": 0.8, "return": 0.0},
        "f2": {"density": 1.2, "raw": 0.8, "relation": 0.1, "return": 0.9},
        "f3": {"density": 0.9, "raw": 1.2, "relation": 0.7, "return": 0.2},
    }
    for key, values in targets.items():
        feature_rows.append(
            {
                "source_label": "triad27",
                "source_profile": "triad27_hardened_cell",
                "family_id": key,
                "total_runs": 9,
                "feature_earned_rate": "0.0",
                "feature_raw_pressure_rate": values["density"],
                "feature_latent_hold_rate": values["density"] / 2,
                "feature_relation_debt_rate": values["relation"],
                "feature_mirror_primary_rate": "0.0",
                "feature_mirror_secondary_rate": "0.0",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.0",
                "feature_ablation_demotion_dependence_rate": values["raw"] / 2,
                "feature_ablation_latent_hold_dependence_rate": "0.0",
                "feature_ablation_echo_independence_rate": values["relation"] / 3,
                "feature_raw_strength_pressure_rate": values["raw"],
                "feature_weakest_gate_pressure_rate": values["density"],
                "feature_relation_gate_rate": values["relation"],
                "feature_return_gate_rate": 1.0 - values["return"],
                "feature_relation_limiting_rate": values["relation"],
                "feature_return_limiting_rate": values["return"],
                "boundary": "role_stripped",
            }
        )
        target_rows.append(
            {
                "source_label": "triad27",
                "family_id": key,
                "evaluation_family_label": key,
                "target_false_pressure_density_rate": values["density"],
                "target_raw_false_one_rate": values["raw"],
                "target_false_one_demotion_rate": values["raw"],
                "target_hold_or_demote_rate": values["density"],
                "target_relation_false_pressure_share": values["relation"],
                "target_return_false_pressure_share": values["return"],
                "target_native_breach_rate": "0.0",
                "boundary": "targets_after_scoring",
            }
        )
    _write_csv(base / "role_stripped" / "role_stripped_profile_features.csv", [feature_rows[0] | {"family_count": 4, "family_id": ""}])
    _write_csv(base / "role_stripped" / "role_stripped_family_features.csv", feature_rows)
    _write_csv(base / "role_stripped" / "role_stripped_evaluation_targets.csv", target_rows)
    write_shadow_score_report(
        output_dir=base / "shadow_score",
        profile_features=base / "role_stripped" / "role_stripped_profile_features.csv",
        family_features=base / "role_stripped" / "role_stripped_family_features.csv",
    )
    comparison_rows = []
    target_map = {
        "target_false_pressure_density_rate": [0.2, 0.1, 1.2, 0.9],
        "target_raw_false_one_rate": [0.0, 0.4, 0.8, 1.2],
        "target_relation_false_pressure_share": [0.0, 0.8, 0.1, 0.7],
        "target_return_false_pressure_share": [0.0, 0.0, 0.9, 0.2],
    }
    baselines = {
        "target_false_pressure_density_rate": {
            "raw_pressure_only": [0.0, 0.4, 0.9, 1.4],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
        "target_raw_false_one_rate": {
            "raw_pressure_only": [0.0, 0.4, 0.8, 1.2],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
        "target_relation_false_pressure_share": {
            "raw_strength_only": [0.0, 0.8, 0.1, 0.7],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
        "target_return_false_pressure_share": {
            "raw_strength_only": [0.0, 0.1, 0.9, 0.2],
            "random_deterministic": [0.7, 0.1, 0.9, 0.2],
        },
    }
    for target_name, target_values in target_map.items():
        for index, target_value in enumerate(target_values):
            for model_name, scores in baselines[target_name].items():
                comparison_rows.append(
                    {
                        "rung": "triad27",
                        "scope": "family",
                        "row_key": f"triad27::f{index}",
                        "source_label": "triad27",
                        "source_profile": "triad27_hardened_cell",
                        "family_id": f"f{index}",
                        "model_name": model_name,
                        "model_score": scores[index],
                        "target_name": target_name,
                        "target_value": target_value,
                        "evaluation_family_label": f"gate:{index}",
                    }
                )
    _write_csv(base / "weather_hardening" / "weather_hardening_baseline_comparison.csv", comparison_rows)
    return base


def test_lane_score_columns_are_emitted(tmp_path: Path) -> None:
    base = _evidence_base(tmp_path)
    rows = _read_rows(base / "shadow_score" / "shadow_score_family_scores.csv")
    header = set(rows[0])
    assert "shadow_density_pressure_score" in header
    assert "shadow_relation_specific_pressure_score" in header
    assert "shadow_return_specific_pressure_score" in header
    assert "shadow_score" in header


def test_shadow_lane_discrimination_writes_expected_files(tmp_path: Path) -> None:
    base = _evidence_base(tmp_path)
    paths = write_shadow_lane_discrimination_report(output_dir=tmp_path / "out", evidence_base=base)
    for key in [
        "shadow_lane_discrimination_metrics",
        "shadow_lane_discrimination_summary",
        "shadow_lane_discrimination_decision",
        "shadow_lane_discrimination_audit",
        "shadow_lane_discrimination_read",
        "shadow_lane_discrimination_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_lane_discrimination_keeps_boundary(tmp_path: Path) -> None:
    base = _evidence_base(tmp_path)
    paths = write_shadow_lane_discrimination_report(output_dir=tmp_path / "out", evidence_base=base)
    decision = json.loads(paths["shadow_lane_discrimination_decision"].read_text(encoding="utf-8"))
    read = paths["shadow_lane_discrimination_read"].read_text(encoding="utf-8")
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert "not role-blind discovery" in read
    assert "does not retune" in read
    assert "C_Z = min(D, P, R, B)" in read


def test_docs_and_readme_name_v1_6_10_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    history = (ROOT / "docs/history_vault/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_lane_discrimination.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_10_alpha.md").read_text(encoding="utf-8")
    for text in [history, doc, release]:
        assert "v1.6.10-alpha" in text
    assert readme.index("## Core theory") < readme.index("## Why this exists")
    assert "docs/runs_cleanup_policy.md" in history or "runs cleanup" in history.lower()
