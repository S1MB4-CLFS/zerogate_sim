from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.shadow_holdout_evaluation_report import write_shadow_holdout_evaluation_report
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


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    profile_features = tmp_path / "role_stripped_profile_features.csv"
    family_features = tmp_path / "role_stripped_family_features.csv"
    targets = tmp_path / "role_stripped_evaluation_targets.csv"

    # Raw pressure alone ranks the profile rows the wrong way. The fixed
    # transparent score ranks the ablation-heavy holdout pressure higher.
    profile_rows = [
        {
            "source_label": "deep81_holdout",
            "source_profile": "deep81",
            "family_count": 2,
            "total_runs": 100,
            "feature_earned_rate": "0.300000",
            "feature_raw_pressure_rate": "0.900000",
            "feature_latent_hold_rate": "0.010000",
            "feature_relation_debt_rate": "0.000000",
            "feature_mirror_primary_rate": "0.020000",
            "feature_mirror_secondary_rate": "0.000000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
            "feature_ablation_demotion_dependence_rate": "0.000000",
            "feature_ablation_latent_hold_dependence_rate": "0.000000",
            "feature_ablation_echo_independence_rate": "0.000000",
            "boundary": "role_stripped_features_only_no_truth_role_labels",
        },
        {
            "source_label": "wide243_holdout",
            "source_profile": "wide243",
            "family_count": 2,
            "total_runs": 100,
            "feature_earned_rate": "0.200000",
            "feature_raw_pressure_rate": "0.350000",
            "feature_latent_hold_rate": "0.500000",
            "feature_relation_debt_rate": "0.100000",
            "feature_mirror_primary_rate": "0.800000",
            "feature_mirror_secondary_rate": "0.200000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.900000",
            "feature_ablation_demotion_dependence_rate": "0.900000",
            "feature_ablation_latent_hold_dependence_rate": "0.300000",
            "feature_ablation_echo_independence_rate": "0.050000",
            "boundary": "role_stripped_features_only_no_truth_role_labels",
        },
    ]
    family_rows = [
        {
            "source_label": "deep81_holdout",
            "source_profile": "deep81",
            "family_id": "opaque_d_low",
            "seed_range": "27-35",
            "total_runs": 100,
            "feature_earned_rate": "0.300000",
            "feature_raw_pressure_rate": "0.800000",
            "feature_latent_hold_rate": "0.020000",
            "feature_relation_debt_rate": "0.000000",
            "feature_mirror_primary_rate": "0.010000",
            "feature_mirror_secondary_rate": "0.000000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
            "feature_ablation_demotion_dependence_rate": "0.000000",
            "feature_ablation_latent_hold_dependence_rate": "0.000000",
            "feature_ablation_echo_independence_rate": "0.000000",
            "boundary": "opaque_family_row_role_stripped",
        },
        {
            "source_label": "wide243_holdout",
            "source_profile": "wide243",
            "family_id": "opaque_w_high",
            "seed_range": "27-35",
            "total_runs": 100,
            "feature_earned_rate": "0.200000",
            "feature_raw_pressure_rate": "0.300000",
            "feature_latent_hold_rate": "0.600000",
            "feature_relation_debt_rate": "0.100000",
            "feature_mirror_primary_rate": "0.800000",
            "feature_mirror_secondary_rate": "0.300000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.900000",
            "feature_ablation_demotion_dependence_rate": "0.800000",
            "feature_ablation_latent_hold_dependence_rate": "0.300000",
            "feature_ablation_echo_independence_rate": "0.050000",
            "boundary": "opaque_family_row_role_stripped",
        },
    ]
    target_rows = [
        {
            "source_label": "deep81_holdout",
            "source_profile": "deep81",
            "total_runs": 100,
            "target_raw_false_one_rate": "0.100000",
            "target_false_one_demotion_rate": "0.100000",
            "target_final_false_crown_rate": "0.000000",
            "target_relation_false_pressure_share": "0.500000",
            "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
        },
        {
            "source_label": "wide243_holdout",
            "source_profile": "wide243",
            "total_runs": 100,
            "target_raw_false_one_rate": "0.800000",
            "target_false_one_demotion_rate": "0.800000",
            "target_final_false_crown_rate": "0.000000",
            "target_relation_false_pressure_share": "0.500000",
            "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
        },
        {
            "source_label": "deep81_holdout",
            "family_id": "opaque_d_low",
            "evaluation_family_label": "held_out_family_a",
            "target_raw_false_one_rate": "0.100000",
            "target_false_one_demotion_rate": "0.100000",
            "target_final_false_crown_rate": "0.000000",
            "boundary": "evaluation_target_separate_from_role_stripped_features",
        },
        {
            "source_label": "wide243_holdout",
            "family_id": "opaque_w_high",
            "evaluation_family_label": "held_out_family_b",
            "target_raw_false_one_rate": "0.800000",
            "target_false_one_demotion_rate": "0.800000",
            "target_final_false_crown_rate": "0.000000",
            "boundary": "evaluation_target_separate_from_role_stripped_features",
        },
    ]
    _write_csv(profile_features, profile_rows)
    _write_csv(family_features, family_rows)
    _write_csv(targets, target_rows)
    score_paths = write_shadow_score_report(output_dir=tmp_path / "score", profile_features=profile_features, family_features=family_features)
    return profile_features, family_features, score_paths["shadow_score_profile_scores"], score_paths["shadow_score_family_scores"], targets


def test_shadow_holdout_evaluation_writes_expected_files(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    paths = write_shadow_holdout_evaluation_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    for key in [
        "shadow_holdout_profile_comparison",
        "shadow_holdout_family_comparison",
        "shadow_holdout_model_metrics",
        "shadow_holdout_evaluation_read",
        "shadow_holdout_evaluation_metrics",
        "shadow_holdout_evaluation_audit",
        "shadow_holdout_evaluation_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_holdout_evaluation_declares_holdout_not_discovery(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    paths = write_shadow_holdout_evaluation_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    metrics = json.loads(paths["shadow_holdout_evaluation_metrics"].read_text(encoding="utf-8"))
    assert metrics["version"] == "v1.6.5-alpha"
    assert metrics["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert metrics["decisions"]["profile"]["holdout_result"] in {
        "resist_holdout_shadow_not_better_than_available_baselines",
        "witness_holdout_shadow_beats_available_baselines_exact_minimum_incomplete",
        "expand_holdout_shadow_beats_exact_baselines_not_detector",
    }
    read = paths["shadow_holdout_evaluation_read"].read_text(encoding="utf-8")
    assert "not role-blind discovery" in read
    assert "Score first. Compare later." in read


def test_shadow_holdout_evaluation_refuses_missing_required_source(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    with pytest.raises(ValueError, match="Missing required holdout source"):
        write_shadow_holdout_evaluation_report(
            output_dir=tmp_path / "out",
            profile_features=profile_features,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
            required_sources=("deep81", "wide243", "missing243"),
        )


def test_shadow_holdout_evaluation_refuses_target_leak_in_features(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    rows = _read_rows(profile_features)
    rows[0]["target_raw_false_one_rate"] = "0.900000"
    bad_profile = tmp_path / "bad_profile_features.csv"
    _write_csv(bad_profile, rows)
    with pytest.raises(ValueError, match="Forbidden role/target fields"):
        write_shadow_holdout_evaluation_report(
            output_dir=tmp_path / "out",
            profile_features=bad_profile,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
        )


def test_shadow_holdout_docs_and_readme_name_v1_6_5_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    history = (ROOT / "docs/history_vault/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_holdout_evaluation.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_5_alpha.md").read_text(encoding="utf-8")
    for text in [history, doc, release]:
        assert "v1.6.5-alpha" in text
    assert "not role-blind discovery" in doc
    assert "C_Z = min(D, P, R, B)" in doc
