from __future__ import annotations

import csv
from pathlib import Path

from zerogate_sim.role_stripped_feature_report import (
    FORBIDDEN_SHADOW_INPUT_FIELDS,
    parse_labeled_path,
    write_role_stripped_feature_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    seed = tmp_path / "seed_block_four_gate_summary.csv"
    ablation = tmp_path / "witness_ablation_summary.csv"
    _write_csv(
        seed,
        [
            {
                "gate": "relation",
                "matrix_label": "relation_deep81",
                "matrix_dir": "runs/secret/relation_deep81",
                "profile": "deep81",
                "candidate_profile": "adversary_relation",
                "seed_range": "18-26",
                "total_runs": 100,
                "final_earned_one_events": 20,
                "raw_expression_pressure": 40,
                "raw_false_one_pressure": 12,
                "false_one_demoted_count": 12,
                "latent_overcrown_pressure": 7,
                "latent_overcrown_demoted_count": 7,
                "relation_debt_count": 0,
                "final_false_one_crowns": 0,
                "trap_final_crowns": 0,
                "mirror_primary_pressure": 30,
                "mirror_secondary_pressure": 10,
                "mirror_safety_breach_total": 0,
                "seed_block_status": "pressure_visible_no_breach",
            },
            {
                "gate": "return",
                "matrix_label": "return_deep81",
                "matrix_dir": "runs/secret/return_deep81",
                "profile": "deep81",
                "candidate_profile": "adversary_return",
                "seed_range": "18-26",
                "total_runs": 100,
                "final_earned_one_events": 30,
                "raw_expression_pressure": 35,
                "raw_false_one_pressure": 1,
                "false_one_demoted_count": 1,
                "latent_overcrown_pressure": 7,
                "latent_overcrown_demoted_count": 7,
                "relation_debt_count": 0,
                "final_false_one_crowns": 0,
                "trap_final_crowns": 0,
                "mirror_primary_pressure": 25,
                "mirror_secondary_pressure": 8,
                "mirror_safety_breach_total": 0,
                "seed_block_status": "pressure_visible_no_breach",
            },
        ],
    )
    _write_csv(
        ablation,
        [
            {"variant": "control", "total_matrix_runs": 200, "final_false_one_crowns": 0, "promoted_latent_pressure": 0, "promoted_relation_debt": 0},
            {"variant": "raw_as_final", "total_matrix_runs": 200, "final_false_one_crowns": 13, "promoted_latent_pressure": 14, "promoted_relation_debt": 0},
            {"variant": "no_false_one_demotion", "total_matrix_runs": 200, "final_false_one_crowns": 13, "promoted_latent_pressure": 0, "promoted_relation_debt": 0},
            {"variant": "no_latent_hold", "total_matrix_runs": 200, "final_false_one_crowns": 0, "promoted_latent_pressure": 14, "promoted_relation_debt": 0},
            {"variant": "no_echo_independence", "total_matrix_runs": 200, "final_false_one_crowns": 0, "promoted_latent_pressure": 0, "promoted_relation_debt": 0},
        ],
    )
    return seed, ablation


def test_parse_labeled_path() -> None:
    label, path = parse_labeled_path("deep81=runs/example.csv")
    assert label == "deep81"
    assert path == Path("runs/example.csv")


def test_role_stripped_feature_report_writes_expected_files(tmp_path: Path) -> None:
    seed, ablation = _fixture(tmp_path)
    out = tmp_path / "out"
    paths = write_role_stripped_feature_report(
        output_dir=out,
        seed_summaries={"deep81": seed},
        ablation_summaries={"deep81": ablation},
    )
    for key in [
        "role_stripped_profile_features",
        "role_stripped_family_features",
        "role_stripped_evaluation_targets",
        "role_stripped_feature_read",
        "role_stripped_forbidden_field_audit",
        "role_stripped_feature_bundle",
    ]:
        assert paths[key].exists()


def test_feature_outputs_do_not_leak_forbidden_fields(tmp_path: Path) -> None:
    seed, ablation = _fixture(tmp_path)
    paths = write_role_stripped_feature_report(
        output_dir=tmp_path / "out",
        seed_summaries={"deep81": seed},
        ablation_summaries={"deep81": ablation},
    )
    for key in ["role_stripped_profile_features", "role_stripped_family_features"]:
        header = set(_read_header(paths[key]))
        assert not (header & FORBIDDEN_SHADOW_INPUT_FIELDS)
        assert "candidate_profile" not in header
        assert "truth_role" not in header


def test_targets_are_separate_from_features(tmp_path: Path) -> None:
    seed, ablation = _fixture(tmp_path)
    paths = write_role_stripped_feature_report(
        output_dir=tmp_path / "out",
        seed_summaries={"deep81": seed},
        ablation_summaries={"deep81": ablation},
    )
    target_text = paths["role_stripped_evaluation_targets"].read_text(encoding="utf-8")
    feature_text = paths["role_stripped_family_features"].read_text(encoding="utf-8")
    assert "evaluation_family_label" in target_text
    assert "target_raw_false_one_rate" in target_text
    assert "evaluation_family_label" not in feature_text
    assert "target_raw_false_one_rate" not in feature_text


def test_docs_and_readme_name_v1_6_1_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/role_stripped_feature_extraction.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_1_alpha.md").read_text(encoding="utf-8")
    card = (ROOT / "docs/assets/role_stripped_feature_extraction_card.svg").read_text(encoding="utf-8")
    for text in [readme, roadmap, doc, release, card]:
        assert "v1.6.1-alpha" in text
    assert "C_Z = min(D, P, R, B)" in doc
    assert "Role-stripped feature extraction" in readme
    assert "docs/assets/role_stripped_feature_extraction_card.svg" in readme
