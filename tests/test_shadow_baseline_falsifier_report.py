from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.shadow_baseline_falsifier_report import write_shadow_baseline_falsifier_report
from zerogate_sim.shadow_score_report import write_shadow_score_report

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _feature_values() -> list[tuple[str, dict[str, str], float]]:
    # The target ordering follows the fixed transparent combination better than
    # any single feature-only baseline. This keeps the test about comparison
    # mechanics without pretending the fixture is scientific evidence.
    rows: list[tuple[str, dict[str, str], float]] = [
        (
            "quiet",
            {
                "feature_raw_pressure_rate": "0.050000",
                "feature_latent_hold_rate": "0.020000",
                "feature_relation_debt_rate": "0.000000",
                "feature_mirror_primary_rate": "0.020000",
                "feature_mirror_secondary_rate": "0.000000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
                "feature_ablation_demotion_dependence_rate": "0.000000",
                "feature_ablation_latent_hold_dependence_rate": "0.000000",
                "feature_ablation_echo_independence_rate": "0.000000",
            },
            0.050000,
        ),
        (
            "raw_loud",
            {
                "feature_raw_pressure_rate": "0.950000",
                "feature_latent_hold_rate": "0.010000",
                "feature_relation_debt_rate": "0.000000",
                "feature_mirror_primary_rate": "0.020000",
                "feature_mirror_secondary_rate": "0.000000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
                "feature_ablation_demotion_dependence_rate": "0.000000",
                "feature_ablation_latent_hold_dependence_rate": "0.000000",
                "feature_ablation_echo_independence_rate": "0.000000",
            },
            0.200000,
        ),
        (
            "latent_only",
            {
                "feature_raw_pressure_rate": "0.200000",
                "feature_latent_hold_rate": "0.900000",
                "feature_relation_debt_rate": "0.010000",
                "feature_mirror_primary_rate": "0.020000",
                "feature_mirror_secondary_rate": "0.020000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
                "feature_ablation_demotion_dependence_rate": "0.000000",
                "feature_ablation_latent_hold_dependence_rate": "0.000000",
                "feature_ablation_echo_independence_rate": "0.000000",
            },
            0.300000,
        ),
        (
            "ablation_only",
            {
                "feature_raw_pressure_rate": "0.200000",
                "feature_latent_hold_rate": "0.100000",
                "feature_relation_debt_rate": "0.000000",
                "feature_mirror_primary_rate": "0.100000",
                "feature_mirror_secondary_rate": "0.050000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.900000",
                "feature_ablation_demotion_dependence_rate": "0.900000",
                "feature_ablation_latent_hold_dependence_rate": "0.200000",
                "feature_ablation_echo_independence_rate": "0.000000",
            },
            0.700000,
        ),
        (
            "combo",
            {
                "feature_raw_pressure_rate": "0.550000",
                "feature_latent_hold_rate": "0.500000",
                "feature_relation_debt_rate": "0.050000",
                "feature_mirror_primary_rate": "1.000000",
                "feature_mirror_secondary_rate": "0.400000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.650000",
                "feature_ablation_demotion_dependence_rate": "0.650000",
                "feature_ablation_latent_hold_dependence_rate": "0.400000",
                "feature_ablation_echo_independence_rate": "0.020000",
            },
            0.900000,
        ),
    ]
    return rows


def _fixtures(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    profile_features = tmp_path / "role_stripped_profile_features.csv"
    family_features = tmp_path / "role_stripped_family_features.csv"
    targets = tmp_path / "role_stripped_evaluation_targets.csv"

    profile_rows: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []
    for idx, (label, features, target) in enumerate(_feature_values(), start=1):
        profile_rows.append(
            {
                "source_label": label,
                "source_profile": "fixture243",
                "family_count": 1,
                "total_runs": 100,
                "feature_earned_rate": "0.200000",
                **features,
                "boundary": "role_stripped_features_only_no_truth_role_labels",
            }
        )
        target_rows.append(
            {
                "source_label": label,
                "source_profile": "fixture243",
                "total_runs": 100,
                "target_raw_false_one_rate": f"{target:.6f}",
                "target_false_one_demotion_rate": f"{target:.6f}",
                "target_final_false_crown_rate": "0.000000",
                "target_relation_false_pressure_share": "0.500000",
                "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
            }
        )
        family_id = f"fixture_family_{idx:03d}"
        family_rows.append(
            {
                "source_label": "fixture",
                "source_profile": "fixture243",
                "family_id": family_id,
                "seed_range": "0-0",
                "total_runs": 100,
                "feature_earned_rate": "0.200000",
                **features,
                "boundary": "opaque_family_row_role_stripped",
            }
        )
        target_rows.append(
            {
                "source_label": "fixture",
                "family_id": family_id,
                "evaluation_family_label": f"family_{idx}",
                "target_raw_false_one_rate": f"{target:.6f}",
                "target_false_one_demotion_rate": f"{target:.6f}",
                "target_final_false_crown_rate": "0.000000",
                "boundary": "evaluation_target_separate_from_role_stripped_features",
            }
        )

    _write_csv(profile_features, profile_rows)
    _write_csv(family_features, family_rows)
    _write_csv(targets, target_rows)
    score_paths = write_shadow_score_report(output_dir=tmp_path / "score", profile_features=profile_features, family_features=family_features)
    return (
        profile_features,
        family_features,
        score_paths["shadow_score_profile_scores"],
        score_paths["shadow_score_family_scores"],
        targets,
    )


def test_shadow_baseline_falsifier_report_writes_expected_files(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixtures(tmp_path)
    paths = write_shadow_baseline_falsifier_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    for key in [
        "shadow_baseline_profile_comparison",
        "shadow_baseline_family_comparison",
        "shadow_baseline_model_metrics",
        "shadow_baseline_falsifier_read",
        "shadow_baseline_falsifier_metrics",
        "shadow_baseline_falsifier_audit",
        "shadow_baseline_falsifier_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_baseline_falsifier_compares_shadow_to_baselines(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixtures(tmp_path)
    paths = write_shadow_baseline_falsifier_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    metrics_rows = _read_rows(paths["shadow_baseline_model_metrics"])
    profile_metrics = {row["model_name"]: row for row in metrics_rows if row["scope"] == "profile"}
    assert "shadow_score" in profile_metrics
    assert "raw_pressure_only" in profile_metrics
    assert "random_deterministic" in profile_metrics
    assert float(profile_metrics["shadow_score"]["pairwise_order_accuracy"]) > float(profile_metrics["raw_pressure_only"]["pairwise_order_accuracy"])

    metrics = json.loads(paths["shadow_baseline_falsifier_metrics"].read_text(encoding="utf-8"))
    assert metrics["version"] == "v1.6.3-alpha"
    assert metrics["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert metrics["decisions"]["profile"]["falsifier_result"] == "witness_shadow_beats_available_baselines_exact_minimum_incomplete"


def test_shadow_baseline_falsifier_refuses_target_leak_in_feature_input(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixtures(tmp_path)
    rows = _read_rows(profile_features)
    rows[0]["target_raw_false_one_rate"] = "0.900000"
    bad_profile = tmp_path / "bad_profile_features.csv"
    _write_csv(bad_profile, rows)
    with pytest.raises(ValueError, match="Forbidden role/target fields"):
        write_shadow_baseline_falsifier_report(
            output_dir=tmp_path / "out",
            profile_features=bad_profile,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
        )


def test_shadow_baseline_falsifier_refuses_role_field_in_targets(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixtures(tmp_path)
    rows = _read_rows(targets)
    rows[0]["truth_role"] = "trap"
    bad_targets = tmp_path / "bad_targets.csv"
    _write_csv(bad_targets, rows)
    with pytest.raises(ValueError, match="Forbidden role/answer-key fields"):
        write_shadow_baseline_falsifier_report(
            output_dir=tmp_path / "out",
            profile_features=profile_features,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=bad_targets,
        )


def test_shadow_baseline_docs_and_readme_name_v1_6_3_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_baseline_falsifier.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_3_alpha.md").read_text(encoding="utf-8")
    card = (ROOT / "docs/assets/shadow_baseline_falsifier_card.svg").read_text(encoding="utf-8")
    for text in [readme, roadmap, doc, release, card]:
        assert "v1.6.3-alpha" in text
    assert "baseline/falsifier" in readme
    assert "docs/assets/shadow_baseline_falsifier_card.svg" not in readme
    assert "shadow_route_history_and_closeout.md" in readme
    assert "C_Z = min(D, P, R, B)" in doc
    assert "not role-blind discovery" in doc
