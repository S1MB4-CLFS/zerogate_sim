from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.role_stripped_feature_report import write_role_stripped_feature_report
from zerogate_sim.shadow_score_report import write_shadow_score_report
from zerogate_sim.shadow_weather_hardening_report import (
    parse_source,
    write_shadow_weather_hardening_report,
)

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


def _seed_summary(base: Path, *, rung: str) -> Path:
    path = base / "seed_block" / "seed_block_four_gate_summary.csv"
    _write_csv(
        path,
        [
            {
                "gate": "distinction",
                "matrix_label": f"distinction_{rung}",
                "matrix_dir": f"runs/{rung}/distinction",
                "profile": rung,
                "candidate_profile": "adversary_distinction",
                "seed_range": "0-2",
                "total_runs": 27,
                "final_earned_one_events": 0,
                "raw_expression_pressure": 0,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": 0,
                "final_false_one_crowns": 0,
                "trap_final_crowns": 0,
                "mirror_primary_pressure": 10,
                "mirror_secondary_pressure": 3,
                "mirror_safety_breach_total": 0,
                "seed_block_status": "pressure_visible_no_breach",
            },
            {
                "gate": "relation",
                "matrix_label": f"relation_{rung}",
                "matrix_dir": f"runs/{rung}/relation",
                "profile": rung,
                "candidate_profile": "adversary_relation",
                "seed_range": "0-2",
                "total_runs": 27,
                "final_earned_one_events": 1,
                "raw_expression_pressure": 3,
                "raw_false_one_pressure": 2,
                "false_one_demoted_count": 2,
                "latent_overcrown_pressure": 1,
                "latent_overcrown_demoted_count": 1,
                "relation_debt_count": 1,
                "final_false_one_crowns": 0,
                "trap_final_crowns": 0,
                "mirror_primary_pressure": 12,
                "mirror_secondary_pressure": 4,
                "mirror_safety_breach_total": 0,
                "seed_block_status": "pressure_visible_no_breach",
            },
            {
                "gate": "return",
                "matrix_label": f"return_{rung}",
                "matrix_dir": f"runs/{rung}/return",
                "profile": rung,
                "candidate_profile": "adversary_return",
                "seed_range": "0-2",
                "total_runs": 27,
                "final_earned_one_events": 1,
                "raw_expression_pressure": 6,
                "raw_false_one_pressure": 4,
                "false_one_demoted_count": 4,
                "latent_overcrown_pressure": 2,
                "latent_overcrown_demoted_count": 2,
                "relation_debt_count": 0,
                "final_false_one_crowns": 0,
                "trap_final_crowns": 0,
                "mirror_primary_pressure": 14,
                "mirror_secondary_pressure": 8,
                "mirror_safety_breach_total": 0,
                "seed_block_status": "pressure_visible_no_breach",
            },
        ],
    )
    return path


def _evidence_base(tmp_path: Path, *, rung: str) -> Path:
    base = tmp_path / rung
    seed = _seed_summary(base, rung=rung)
    role_paths = write_role_stripped_feature_report(
        output_dir=base / "role_stripped",
        seed_summaries={rung: seed},
    )
    write_shadow_score_report(
        output_dir=base / "shadow_score",
        profile_features=role_paths["role_stripped_profile_features"],
        family_features=role_paths["role_stripped_family_features"],
    )
    return base


def test_parse_source() -> None:
    label, path = parse_source("triad27=runs/example")
    assert label == "triad27"
    assert path == Path("runs/example")


def test_weather_hardening_report_writes_expected_files(tmp_path: Path) -> None:
    triad = _evidence_base(tmp_path, rung="triad27")
    paths = write_shadow_weather_hardening_report(
        output_dir=tmp_path / "out",
        sources={"triad27": triad},
        required_rungs=("triad27",),
    )
    for key in [
        "weather_hardening_baseline_comparison",
        "weather_hardening_target_diagnostics",
        "weather_hardening_native_gate_metrics",
        "weather_hardening_decision",
        "weather_hardening_audit",
        "weather_hardening_read",
        "weather_hardening_bundle",
    ]:
        assert paths[key].exists()


def test_weather_hardening_expands_target_variety_and_no_discovery(tmp_path: Path) -> None:
    triad = _evidence_base(tmp_path, rung="triad27")
    paths = write_shadow_weather_hardening_report(
        output_dir=tmp_path / "out",
        sources={"triad27": triad},
        required_rungs=("triad27",),
    )
    decision = json.loads(paths["weather_hardening_decision"].read_text(encoding="utf-8"))
    assert decision["version"] == "v1.6.7-alpha"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert "no role-blind discovery" in decision["role_blind_boundary"]
    assert "target_false_pressure_density_rate" in decision["per_rung"]["triad27"]["target_fields"]
    assert "target_hold_or_demote_rate" in decision["per_rung"]["triad27"]["target_fields"]
    assert decision["global_decision"] in {
        "resist_shadow_under_hardened_weather",
        "witness_shadow_trivial_under_hardened_weather",
        "witness_shadow_not_closed_under_hardened_weather",
        "expand_shadow_nontrivial_hardened_weather_not_detector",
    }
    read = paths["weather_hardening_read"].read_text(encoding="utf-8")
    assert "triad27 = 3^3 local expression weather" in read
    assert "does not tune the shadow score" in read
    assert "right but trivial" in read


def test_weather_hardening_reports_missing_ladder_when_only_triad_required_all(tmp_path: Path) -> None:
    triad = _evidence_base(tmp_path, rung="triad27")
    paths = write_shadow_weather_hardening_report(
        output_dir=tmp_path / "out",
        sources={"triad27": triad},
    )
    decision = json.loads(paths["weather_hardening_decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] == "witness_weather_ladder_incomplete"
    assert decision["required_rungs"] == ["triad27", "deep81", "wide243"]
    assert decision["loaded_rungs"] == ["triad27"]


def test_weather_hardening_refuses_target_leak_in_features(tmp_path: Path) -> None:
    triad = _evidence_base(tmp_path, rung="triad27")
    profile = triad / "role_stripped" / "role_stripped_profile_features.csv"
    rows = _read_rows(profile)
    rows[0]["target_false_pressure_density_rate"] = "0.9"
    _write_csv(profile, rows)
    with pytest.raises(ValueError, match="Forbidden role/target fields"):
        write_shadow_weather_hardening_report(
            output_dir=tmp_path / "out",
            sources={"triad27": triad},
            required_rungs=("triad27",),
        )


def test_role_stripped_targets_include_v1_6_7_harder_targets(tmp_path: Path) -> None:
    triad = _evidence_base(tmp_path, rung="triad27")
    targets = _read_rows(triad / "role_stripped" / "role_stripped_evaluation_targets.csv")
    header = set(targets[0])
    assert "target_false_pressure_density_rate" in header
    assert "target_hold_or_demote_rate" in header
    assert "target_return_false_pressure_share" in header
    assert "target_native_breach_rate" in header
    features = _read_rows(triad / "role_stripped" / "role_stripped_profile_features.csv")
    assert "target_false_pressure_density_rate" not in set(features[0])


def test_weather_hardening_docs_and_readme_name_v1_6_7_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    history = (ROOT / "docs/history_vault/shadow_route_history_and_closeout.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_weather_hardening.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_7_alpha.md").read_text(encoding="utf-8")
    for text in [history, doc, release]:
        assert "v1.6.7-alpha" in text
    assert "C_Z = min(D, P, R, B)" in doc
    assert "not role-blind discovery" in doc
    assert "weather hardening" in history.lower()
