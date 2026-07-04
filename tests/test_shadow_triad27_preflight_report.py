from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.shadow_score_report import write_shadow_score_report
from zerogate_sim.shadow_triad27_preflight_report import write_shadow_triad27_preflight_report


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


def _fixture(tmp_path: Path, *, source_profile: str = "triad27", label_prefix: str = "triad27") -> tuple[Path, Path, Path, Path, Path]:
    profile_features = tmp_path / "role_stripped_profile_features.csv"
    family_features = tmp_path / "role_stripped_family_features.csv"
    targets = tmp_path / "role_stripped_evaluation_targets.csv"

    profile_rows = [
        {
            "source_label": f"{label_prefix}_shadow_low",
            "source_profile": source_profile,
            "family_count": 1,
            "total_runs": 27,
            "feature_earned_rate": "0.400000",
            "feature_raw_pressure_rate": "0.800000",
            "feature_latent_hold_rate": "0.010000",
            "feature_relation_debt_rate": "0.000000",
            "feature_mirror_primary_rate": "0.000000",
            "feature_mirror_secondary_rate": "0.000000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
            "feature_ablation_demotion_dependence_rate": "0.000000",
            "feature_ablation_latent_hold_dependence_rate": "0.000000",
            "feature_ablation_echo_independence_rate": "0.000000",
            "feature_raw_strength_pressure_rate": "0.700000",
            "feature_weakest_gate_pressure_rate": "0.050000",
            "feature_relation_gate_rate": "0.000000",
            "boundary": "role_stripped_features_only_no_truth_role_labels",
        },
        {
            "source_label": f"{label_prefix}_shadow_high",
            "source_profile": source_profile,
            "family_count": 1,
            "total_runs": 27,
            "feature_earned_rate": "0.100000",
            "feature_raw_pressure_rate": "0.250000",
            "feature_latent_hold_rate": "0.550000",
            "feature_relation_debt_rate": "0.100000",
            "feature_mirror_primary_rate": "0.900000",
            "feature_mirror_secondary_rate": "0.200000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.900000",
            "feature_ablation_demotion_dependence_rate": "0.900000",
            "feature_ablation_latent_hold_dependence_rate": "0.350000",
            "feature_ablation_echo_independence_rate": "0.100000",
            "feature_raw_strength_pressure_rate": "0.150000",
            "feature_weakest_gate_pressure_rate": "0.700000",
            "feature_relation_gate_rate": "0.500000",
            "boundary": "role_stripped_features_only_no_truth_role_labels",
        },
    ]
    family_rows = [
        {
            "source_label": f"{label_prefix}_shadow_low",
            "source_profile": source_profile,
            "family_id": "triad27_opaque_low",
            "seed_range": "18-26",
            "total_runs": 27,
            "feature_earned_rate": "0.400000",
            "feature_raw_pressure_rate": "0.750000",
            "feature_latent_hold_rate": "0.010000",
            "feature_relation_debt_rate": "0.000000",
            "feature_mirror_primary_rate": "0.000000",
            "feature_mirror_secondary_rate": "0.000000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
            "feature_ablation_demotion_dependence_rate": "0.000000",
            "feature_ablation_latent_hold_dependence_rate": "0.000000",
            "feature_ablation_echo_independence_rate": "0.000000",
            "feature_raw_strength_pressure_rate": "0.700000",
            "feature_weakest_gate_pressure_rate": "0.050000",
            "feature_relation_gate_rate": "0.000000",
            "boundary": "opaque_family_row_role_stripped",
        },
        {
            "source_label": f"{label_prefix}_shadow_high",
            "source_profile": source_profile,
            "family_id": "triad27_opaque_high",
            "seed_range": "18-26",
            "total_runs": 27,
            "feature_earned_rate": "0.100000",
            "feature_raw_pressure_rate": "0.250000",
            "feature_latent_hold_rate": "0.600000",
            "feature_relation_debt_rate": "0.150000",
            "feature_mirror_primary_rate": "0.800000",
            "feature_mirror_secondary_rate": "0.250000",
            "feature_ablation_raw_as_final_crown_risk_rate": "0.900000",
            "feature_ablation_demotion_dependence_rate": "0.800000",
            "feature_ablation_latent_hold_dependence_rate": "0.300000",
            "feature_ablation_echo_independence_rate": "0.100000",
            "feature_raw_strength_pressure_rate": "0.150000",
            "feature_weakest_gate_pressure_rate": "0.700000",
            "feature_relation_gate_rate": "0.500000",
            "boundary": "opaque_family_row_role_stripped",
        },
    ]
    target_rows = [
        {
            "source_label": f"{label_prefix}_shadow_low",
            "source_profile": source_profile,
            "total_runs": 27,
            "target_raw_false_one_rate": "0.100000",
            "target_false_one_demotion_rate": "0.100000",
            "target_final_false_crown_rate": "0.000000",
            "target_relation_false_pressure_share": "0.200000",
            "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
        },
        {
            "source_label": f"{label_prefix}_shadow_high",
            "source_profile": source_profile,
            "total_runs": 27,
            "target_raw_false_one_rate": "0.800000",
            "target_false_one_demotion_rate": "0.800000",
            "target_final_false_crown_rate": "0.000000",
            "target_relation_false_pressure_share": "0.700000",
            "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
        },
        {
            "source_label": f"{label_prefix}_shadow_low",
            "family_id": "triad27_opaque_low",
            "evaluation_family_label": "triad27_family_low",
            "target_raw_false_one_rate": "0.100000",
            "target_false_one_demotion_rate": "0.100000",
            "target_final_false_crown_rate": "0.000000",
            "boundary": "evaluation_target_separate_from_role_stripped_features",
        },
        {
            "source_label": f"{label_prefix}_shadow_high",
            "family_id": "triad27_opaque_high",
            "evaluation_family_label": "triad27_family_high",
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


def test_shadow_triad27_preflight_writes_expected_files(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    paths = write_shadow_triad27_preflight_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    for key in [
        "shadow_triad27_profile_comparison",
        "shadow_triad27_family_comparison",
        "shadow_triad27_model_metrics",
        "shadow_triad27_preflight_read",
        "shadow_triad27_preflight_metrics",
        "shadow_triad27_preflight_audit",
        "shadow_triad27_preflight_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_triad27_preflight_declares_first_weather_rung_not_discovery(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    paths = write_shadow_triad27_preflight_report(
        output_dir=tmp_path / "out",
        profile_features=profile_features,
        family_features=family_features,
        profile_scores=profile_scores,
        family_scores=family_scores,
        evaluation_targets=targets,
    )
    metrics = json.loads(paths["shadow_triad27_preflight_metrics"].read_text(encoding="utf-8"))
    assert metrics["version"] == "v1.6.6-alpha"
    assert metrics["weather_rung"] == "triad27"
    assert metrics["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert "deep81/wide243 holdout still separate" in metrics["role_blind_boundary"]
    assert metrics["decisions"]["profile"]["triad27_result"] in {
        "resist_triad27_shadow_not_better_than_available_baselines",
        "witness_triad27_shadow_beats_available_baselines_exact_minimum_incomplete",
        "expand_triad27_shadow_beats_exact_baselines_not_detector",
    }
    read = paths["shadow_triad27_preflight_read"].read_text(encoding="utf-8")
    assert "triad27 = 3^3 local expression weather" in read
    assert "not role-blind discovery" in read
    assert "Score first. Compare later." in read


def test_shadow_triad27_preflight_refuses_missing_triad27_source(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path, source_profile="deep81", label_prefix="deep81")
    with pytest.raises(ValueError, match="Missing required triad27 source"):
        write_shadow_triad27_preflight_report(
            output_dir=tmp_path / "out",
            profile_features=profile_features,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
        )


def test_shadow_triad27_preflight_refuses_target_leak_in_features(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    rows = _read_rows(profile_features)
    rows[0]["target_raw_false_one_rate"] = "0.900000"
    bad_profile = tmp_path / "bad_profile_features.csv"
    _write_csv(bad_profile, rows)
    with pytest.raises(ValueError, match="Forbidden role/target fields"):
        write_shadow_triad27_preflight_report(
            output_dir=tmp_path / "out",
            profile_features=bad_profile,
            family_features=family_features,
            profile_scores=profile_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
        )


def test_shadow_triad27_preflight_refuses_role_leak_in_scores(tmp_path: Path) -> None:
    profile_features, family_features, profile_scores, family_scores, targets = _fixture(tmp_path)
    rows = _read_rows(profile_scores)
    rows[0]["truth_role"] = "trap"
    bad_scores = tmp_path / "bad_profile_scores.csv"
    _write_csv(bad_scores, rows)
    with pytest.raises(ValueError, match="Forbidden role/target fields"):
        write_shadow_triad27_preflight_report(
            output_dir=tmp_path / "out",
            profile_features=profile_features,
            family_features=family_features,
            profile_scores=bad_scores,
            family_scores=family_scores,
            evaluation_targets=targets,
        )
