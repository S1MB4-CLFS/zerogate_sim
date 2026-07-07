from __future__ import annotations

import csv
import json
from pathlib import Path

from zerogate_sim.v1_7_repo_cleanup_cohesion_check import (
    CLOSEOUT_GATE,
    COHESION_CHECKS,
    CURRENT_VERSION,
    DECISION,
    FRONT_PAGE_ROUTES,
    HOLDOUT_SNAPSHOT_ROWS,
    NEXT_GATE,
    NATIVE_WITNESS,
    build_v1_7_repo_cleanup_cohesion_check,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_8_cleanup_report_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_repo_cleanup_cohesion_check(tmp_path / "out")
    for key in ["read", "decision", "front_page", "cohesion", "evidence", "release_shift", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["core_question_closed"] is False
    assert decision["reviewer_package_started"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["physics_or_cosmology_claimed"] is False
    assert decision["next_gate"] == NEXT_GATE
    assert decision["closeout_gate"] == CLOSEOUT_GATE
    assert decision["latest_snapshot_totals"]["final_earned_one_events"] == 12206
    assert decision["latest_snapshot_totals"]["false_one_pressure"] == 4671
    assert decision["latest_snapshot_totals"]["final_false_one_crowns"] == 0

    readme = paths["read"].read_text(encoding="utf-8")
    assert "front-page cohesion" in readme or "front-page" in readme
    assert "haunted spreadsheet attic" in readme


def test_v1_7_8_route_and_snapshot_constants_are_complete() -> None:
    assert {row["route"] for row in FRONT_PAGE_ROUTES} >= {
        "current_evidence_state",
        "latest_holdout_snapshot",
        "anti_tautology_path",
        "known_routine",
        "recent_native_history",
        "version_truth",
        "repo_cohesion_check",
    }
    assert {row["check"] for row in COHESION_CHECKS} >= {
        "readme_front_page_math_and_visual_cards_preserved",
        "current_evidence_state_has_home",
        "recent_native_history_has_home",
        "anti_tautology_path_is_inspectable",
        "version_route_shift_is_explicit",
        "forbidden_claims_still_blocked",
    }
    assert [row["weather_rung"] for row in HOLDOUT_SNAPSHOT_ROWS] == ["triad27", "deep81", "wide243"]
    assert sum(int(row["final_false_one_crowns"]) for row in HOLDOUT_SNAPSHOT_ROWS) == 0


def test_v1_7_8_public_surfaces_are_cohesive() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    current_state = read("docs/current_evidence_state.md")
    front_page = read("docs/v1_7_front_page_map.md")
    recent_history = read("docs/recent_native_evidence_history.md")
    snapshot = read("docs/v1_7_latest_holdout_snapshot.md")
    cleanup_doc = read("docs/v1_7_repo_cleanup_cohesion_check.md")
    release = read("docs/release_notes/v1_7_8_alpha.md")

    assert "1.7.8-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.8a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-repo-cohesion-check" in read("pyproject.toml")

    assert "Current public line:** `v1.7.8-alpha` — Repo Cleanup / Cohesion Check" in readme
    assert "Latest evidence snapshot" in readme
    assert "```math" in readme
    assert r"E_0 = (Z_0, \tau)" in readme
    assert r"T_3[X](\tau)" in readme
    assert r"\Gamma_i(t)=D_i(t)P_i(t)R_i(t)" in readme
    assert r"\chi^i_{earned}" in readme
    assert "docs/assets/v1_7_6_triad27_holdout_card.svg" in readme
    assert "docs/assets/v1_7_6_deep81_holdout_card.svg" in readme
    assert "docs/assets/v1_7_6_wide243_holdout_card.svg" in readme
    assert "docs/assets/v1_7_6_holdout_total_card.svg" in readme
    assert "docs/v1_7_latest_holdout_snapshot.md" in readme
    assert "docs/current_evidence_state.md" in readme
    assert "docs/recent_native_evidence_history.md" in readme
    assert "docs/v1_7_anti_tautology_role_dependence_check.md" in readme
    assert "docs/v1_7_anti_tautology_known_routine.md" in readme
    assert "v1.7.9-alpha reviewer start here / reproduction package next" in readme
    assert "v1.7.10-alpha core question closeout later" in readme

    assert "v1.7.8-alpha" in roadmap
    assert "Repo Cleanup / Cohesion Check" in roadmap
    assert "v1.7.9-alpha" in roadmap
    assert "Reviewer Start Here / Reproduction Package" in roadmap
    assert "v1.7.10-alpha" in roadmap
    assert "Core Question Closeout" in roadmap

    for text in [version_truth, current_state, front_page, recent_history, snapshot, cleanup_doc, release]:
        assert "C_Z = min(D, P, R, B)" in text or text is snapshot
        assert "role-blind" in text or "role-blind" in readme

    assert "12,206" in snapshot
    assert "4,671" in snapshot
    assert "final false-one crowns = 0" in snapshot
    assert "v1.7.8-alpha" in version_truth
    assert "v1.7.9-alpha" in version_truth
    assert "v1.7.10-alpha" in version_truth


def test_v1_7_8_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_repo_cleanup_cohesion_check_read.md").exists()
    assert (out / "v1_7_repo_cleanup_cohesion_check_bundle.zip").exists()
