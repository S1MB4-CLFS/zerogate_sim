from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.role_stripped_feature_report import FORBIDDEN_SHADOW_INPUT_FIELDS
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


def _fixtures(tmp_path: Path) -> tuple[Path, Path]:
    profile = tmp_path / "role_stripped_profile_features.csv"
    family = tmp_path / "role_stripped_family_features.csv"
    _write_csv(
        profile,
        [
            {
                "source_label": "quiet",
                "source_profile": "triad27",
                "family_count": 4,
                "total_runs": 100,
                "feature_earned_rate": "0.200000",
                "feature_raw_pressure_rate": "0.010000",
                "feature_latent_hold_rate": "0.010000",
                "feature_relation_debt_rate": "0.000000",
                "feature_mirror_primary_rate": "0.020000",
                "feature_mirror_secondary_rate": "0.010000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
                "feature_ablation_demotion_dependence_rate": "0.000000",
                "feature_ablation_latent_hold_dependence_rate": "0.000000",
                "feature_ablation_echo_independence_rate": "0.000000",
                "boundary": "role_stripped_features_only_no_truth_role_labels",
            },
            {
                "source_label": "pressure",
                "source_profile": "wide243",
                "family_count": 4,
                "total_runs": 100,
                "feature_earned_rate": "0.400000",
                "feature_raw_pressure_rate": "0.900000",
                "feature_latent_hold_rate": "0.500000",
                "feature_relation_debt_rate": "0.020000",
                "feature_mirror_primary_rate": "2.000000",
                "feature_mirror_secondary_rate": "1.000000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.700000",
                "feature_ablation_demotion_dependence_rate": "0.700000",
                "feature_ablation_latent_hold_dependence_rate": "0.300000",
                "feature_ablation_echo_independence_rate": "0.010000",
                "boundary": "role_stripped_features_only_no_truth_role_labels",
            },
        ],
    )
    _write_csv(
        family,
        [
            {
                "source_label": "pressure",
                "source_profile": "wide243",
                "family_id": "opaque_family_001",
                "seed_range": "27-35",
                "total_runs": 100,
                "feature_earned_rate": "0.400000",
                "feature_raw_pressure_rate": "0.900000",
                "feature_latent_hold_rate": "0.500000",
                "feature_relation_debt_rate": "0.000000",
                "feature_mirror_primary_rate": "2.000000",
                "feature_mirror_secondary_rate": "1.000000",
                "boundary": "opaque_family_row_role_stripped",
            }
        ],
    )
    return profile, family


def test_shadow_score_report_writes_expected_files(tmp_path: Path) -> None:
    profile, family = _fixtures(tmp_path)
    paths = write_shadow_score_report(output_dir=tmp_path / "out", profile_features=profile, family_features=family)
    for key in [
        "shadow_score_profile_scores",
        "shadow_score_family_scores",
        "shadow_score_read",
        "shadow_score_formula",
        "shadow_score_forbidden_field_audit",
        "shadow_score_bundle",
    ]:
        assert paths[key].exists()


def test_shadow_score_is_monotonic_for_pressure_fixture(tmp_path: Path) -> None:
    profile, family = _fixtures(tmp_path)
    paths = write_shadow_score_report(output_dir=tmp_path / "out", profile_features=profile, family_features=family)
    rows = _read_rows(paths["shadow_score_profile_scores"])
    by_label = {row["source_label"]: float(row["shadow_score"]) for row in rows}
    assert by_label["pressure"] > by_label["quiet"]
    assert rows[0]["score_status"] == "report_only_no_crown_no_demotion"


def test_shadow_score_outputs_do_not_leak_forbidden_fields(tmp_path: Path) -> None:
    profile, family = _fixtures(tmp_path)
    paths = write_shadow_score_report(output_dir=tmp_path / "out", profile_features=profile, family_features=family)
    for key in ["shadow_score_profile_scores", "shadow_score_family_scores"]:
        header = set(_read_rows(paths[key])[0].keys())
        assert not (header & FORBIDDEN_SHADOW_INPUT_FIELDS)
        assert "target_raw_false_one_rate" not in header
        assert "evaluation_family_label" not in header


def test_shadow_score_refuses_forbidden_feature_input(tmp_path: Path) -> None:
    profile, family = _fixtures(tmp_path)
    rows = _read_rows(profile)
    rows[0]["truth_role"] = "trap"
    bad_profile = tmp_path / "bad_profile.csv"
    _write_csv(bad_profile, rows)
    with pytest.raises(ValueError, match="Forbidden role/answer-key fields"):
        write_shadow_score_report(output_dir=tmp_path / "out", profile_features=bad_profile, family_features=family)


def test_shadow_score_formula_and_docs_keep_boundary(tmp_path: Path) -> None:
    profile, family = _fixtures(tmp_path)
    paths = write_shadow_score_report(output_dir=tmp_path / "out", profile_features=profile, family_features=family)
    formula = json.loads(paths["shadow_score_formula"].read_text(encoding="utf-8"))
    read = paths["shadow_score_read"].read_text(encoding="utf-8")
    assert formula["version"] == "v1.6.2-alpha"
    assert formula["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert "target_file_loaded" not in formula
    assert "It is not a role-blind detector yet" in read
    assert "C_Z = min(D, P, R, B)" in read


def test_docs_and_readme_name_v1_6_2_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/transparent_shadow_score.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_2_alpha.md").read_text(encoding="utf-8")
    card = (ROOT / "docs/assets/transparent_shadow_score_card.svg").read_text(encoding="utf-8")
    closeout = (ROOT / "docs/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    for text in [readme, roadmap, doc, release, card, closeout]:
        assert "v1.6.2-alpha" in text
    assert "transparent shadow score" in readme
    assert "docs/assets/transparent_shadow_score_card.svg" not in readme
    assert "C_Z = min(D, P, R, B)" in doc
    assert "not a role-blind detector yet" in doc
