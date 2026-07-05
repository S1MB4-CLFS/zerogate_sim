from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.role_stripped_feature_report import write_role_stripped_feature_report
from zerogate_sim.shadow_feature_design import SHADOW_ENGINEERED_FEATURE_COLUMNS, engineered_shadow_feature_values
from zerogate_sim.shadow_lane_discrimination_report import TARGET_TO_LANE_SCORE
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


def test_engineered_features_use_observable_columns_only() -> None:
    values = engineered_shadow_feature_values(
        {
            "feature_raw_pressure_rate": "1.2",
            "feature_raw_strength_pressure_rate": "0.4",
            "feature_weakest_gate_pressure_rate": "0.7",
            "feature_relation_gate_rate": "0.9",
            "feature_return_gate_rate": "0.2",
            "feature_relation_limiting_rate": "0.3",
            "feature_return_limiting_rate": "0.5",
            "feature_earned_rate": "0.1",
            "feature_latent_hold_rate": "0.6",
            "feature_relation_debt_rate": "0.2",
            "feature_mirror_secondary_rate": "0.4",
            "feature_ablation_echo_independence_rate": "0.1",
            "feature_ablation_demotion_dependence_rate": "0.2",
            "truth_role": "trap",
            "target_raw_false_one_rate": "999",
        }
    )
    assert set(values) == set(SHADOW_ENGINEERED_FEATURE_COLUMNS)
    assert "truth_role" not in values
    assert "target_raw_false_one_rate" not in values
    assert float(values["feature_relation_ownership_gap_rate"]) > 0
    assert float(values["feature_return_integrity_gap_rate"]) > 0


def test_role_stripped_report_emits_engineered_features_before_targets(tmp_path: Path) -> None:
    seed = tmp_path / "seed.csv"
    _write_csv(
        seed,
        [
            {
                "profile": "triad27",
                "gate": "relation",
                "seed_range": "0-8",
                "total_runs": 27,
                "final_earned_one_events": 2,
                "raw_expression_pressure": 12,
                "latent_overcrown_pressure": 3,
                "relation_debt_count": 1,
                "mirror_primary_pressure": 0,
                "mirror_secondary_pressure": 1,
                "raw_false_one_pressure": 5,
                "false_one_demoted_count": 5,
                "latent_overcrown_demoted_count": 3,
                "final_false_one_crowns": 0,
                "mirror_safety_breach_total": 0,
            }
        ],
    )
    paths = write_role_stripped_feature_report(output_dir=tmp_path / "out", seed_summaries={"triad27": seed})
    feature_rows = _read_rows(paths["role_stripped_family_features"])
    target_rows = _read_rows(paths["role_stripped_evaluation_targets"])
    feature_header = set(feature_rows[0])
    target_header = set(target_rows[0])
    assert set(SHADOW_ENGINEERED_FEATURE_COLUMNS).issubset(feature_header)
    assert not any(name.startswith("target_") for name in feature_header)
    assert "truth_role" not in feature_header
    assert "feature_relation_ownership_gap_rate" not in target_header
    audit = json.loads(paths["role_stripped_forbidden_field_audit"].read_text(encoding="utf-8"))
    assert "feature_return_integrity_gap_rate" in audit["engineered_shadow_feature_columns"]


def test_shadow_score_emits_v1_6_12_feature_aware_scores(tmp_path: Path) -> None:
    profile = tmp_path / "profile.csv"
    family = tmp_path / "family.csv"
    row = {
        "source_label": "triad27",
        "source_profile": "triad27_hardened_cell",
        "family_id": "opaque_1",
        "family_count": 1,
        "total_runs": 9,
        "feature_earned_rate": "0.0",
        "feature_raw_pressure_rate": "1.0",
        "feature_latent_hold_rate": "0.2",
        "feature_relation_debt_rate": "0.1",
        "feature_mirror_primary_rate": "0.0",
        "feature_mirror_secondary_rate": "0.2",
        "feature_ablation_raw_as_final_crown_risk_rate": "0.0",
        "feature_ablation_demotion_dependence_rate": "0.2",
        "feature_ablation_latent_hold_dependence_rate": "0.0",
        "feature_ablation_echo_independence_rate": "0.1",
        "feature_raw_strength_pressure_rate": "0.4",
        "feature_weakest_gate_pressure_rate": "0.6",
        "feature_relation_gate_rate": "0.9",
        "feature_return_gate_rate": "0.2",
        "feature_relation_limiting_rate": "0.3",
        "feature_return_limiting_rate": "0.5",
        **engineered_shadow_feature_values(
            {
                "feature_earned_rate": "0.0",
                "feature_raw_pressure_rate": "1.0",
                "feature_latent_hold_rate": "0.2",
                "feature_relation_debt_rate": "0.1",
                "feature_mirror_secondary_rate": "0.2",
                "feature_ablation_demotion_dependence_rate": "0.2",
                "feature_ablation_echo_independence_rate": "0.1",
                "feature_raw_strength_pressure_rate": "0.4",
                "feature_weakest_gate_pressure_rate": "0.6",
                "feature_relation_gate_rate": "0.9",
                "feature_return_gate_rate": "0.2",
                "feature_relation_limiting_rate": "0.3",
                "feature_return_limiting_rate": "0.5",
            }
        ),
        "boundary": "role_stripped",
    }
    _write_csv(profile, [row | {"family_id": ""}])
    _write_csv(family, [row])
    paths = write_shadow_score_report(output_dir=tmp_path / "score", profile_features=profile, family_features=family)
    rows = _read_rows(paths["shadow_score_family_scores"])
    header = set(rows[0])
    assert "shadow_feature_relation_specific_pressure_score" in header
    assert "shadow_feature_return_specific_pressure_score" in header
    assert "shadow_feature_demotion_pressure_score" in header
    formula = json.loads(paths["shadow_score_formula"].read_text(encoding="utf-8"))
    assert formula["feature_aware_scores_version"] == "v1.6.12-alpha"
    assert "feature_relation_ownership_gap_rate" in formula["engineered_feature_columns"]


def test_lane_discrimination_uses_v1_6_12_feature_aware_scores() -> None:
    assert TARGET_TO_LANE_SCORE["target_relation_false_pressure_share"] == "shadow_feature_relation_specific_pressure_score"
    assert TARGET_TO_LANE_SCORE["target_return_false_pressure_share"] == "shadow_feature_return_specific_pressure_score"
    assert TARGET_TO_LANE_SCORE["target_false_one_demotion_rate"] == "shadow_feature_demotion_pressure_score"


def test_docs_and_roadmap_name_v1_6_12_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    history = (ROOT / "docs/history_vault/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_feature_implementation.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_12_alpha.md").read_text(encoding="utf-8")
    for text in [history, doc, release]:
        assert "v1.6.12-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text
    assert "v1.6.13-alpha" in history
    assert "v1.6.14-alpha" in (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    assert "deep81 / wide243 remain blocked" in release
