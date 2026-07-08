from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.v1_7_core_question_closeout import (
    ANSWER_STATUS,
    ANSWER_SYMBOL,
    BOUNDARY_ROWS,
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION,
    FULL_ANSWER_CONDITIONS,
    GO_NO_GO_ROWS,
    HOLDOUT_ROWS,
    NATIVE_WITNESS,
    build_v1_7_core_question_closeout,
    closeout_totals,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_10_closeout_report_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_core_question_closeout(tmp_path / "out")
    for key in ["read", "decision", "answer_status", "condition_status", "boundary", "go_no_go", "evidence", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["answer_symbol"] == ANSWER_SYMBOL
    assert decision["answer_status"] == ANSWER_STATUS
    assert decision["core_question"] == CORE_QUESTION
    assert decision["core_question_closed"] is True
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["native_math_mutated"] is False
    assert decision["full_answer_conditions_passed"] is True
    assert decision["final_false_one_crowns"] == 0
    assert decision["earned_one"] == 12206
    assert decision["false_one_pressure"] == 4671
    assert decision["manuscript_v2_go"] == "go_bounded"
    assert decision["v1_8_allowed_now"] is False
    assert decision["role_blind_discovery_claimed"] is False
    assert decision["independent_generator_validation_claimed"] is False
    assert decision["physics_or_cosmology_claimed"] is False


def test_v1_7_10_constants_are_bounded() -> None:
    assert [row["weather_rung"] for row in HOLDOUT_ROWS] == ["triad27", "deep81", "wide243"]
    totals = closeout_totals()
    assert totals == {
        "earned_one": 12206,
        "raw_expression_pressure": 18353,
        "latent_overcrown": 39,
        "relation_debt": 624,
        "return_debt": 813,
        "false_one_pressure": 4671,
        "final_false_one_crowns": 0,
    }
    assert all(row["status"] == "pass" for row in FULL_ANSWER_CONDITIONS)
    assert {row["lane"] for row in BOUNDARY_ROWS} >= {"allowed", "forbidden"}
    assert {row["target"] for row in GO_NO_GO_ROWS} >= {
        "manuscript_v2_upgrade",
        "v1.8_independent_synthetic_challenge",
        "role_blind_discovery_language",
        "physics_or_cosmology_language",
        "zenodo_new_version",
    }


def test_v1_7_10_public_surfaces() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    current_state = read("docs/current_evidence_state.md")
    evidence_index = read("docs/current_evidence_index.md")
    claim_card = read("docs/v1_7_claim_boundary_card.md")
    closeout = read("docs/v1_7_core_question_closeout.md")
    status_card = read("docs/v1_7_answer_status_card.md")
    go_no_go = read("docs/v1_7_go_no_go_for_manuscript_v2.md")
    release = read("docs/release_notes/v1_7_10_alpha.md")

    assert "1.7.10-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.10a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-core-question-closeout" in read("pyproject.toml")

    assert "Current public line:** `v1.7.10-alpha` — Core Question Closeout" in readme
    assert "## Core question closeout" in readme
    assert "docs/assets/v1_7_10_core_question_closeout_card.svg" in readme
    assert "docs/v1_7_core_question_closeout.md" in readme
    assert "manuscript v2 bounded upgrade next before v1.8" in readme
    assert readme.index("## Native math witness") < readme.index("## Latest evidence snapshot") < readme.index("## Reviewer start here / reproduction package") < readme.index("## Core question closeout") < readme.index("## Inspection map")

    assert "v1.7.10-alpha" in roadmap
    assert "Core Question Closeout" in roadmap
    assert "Manuscript v2 upgrade gate" in roadmap
    assert "v1.7.10-alpha current note" in roadmap
    assert "controlled synthetic-field adversarial weather" in roadmap

    for text in [version_truth, current_state, evidence_index, claim_card, closeout, status_card, go_no_go, release]:
        assert "C_Z = min(D, P, R, B)" in text
        assert "role-blind" in text or "role-blind" in readme

    assert "+1" in closeout
    assert "Yes — inside controlled synthetic-field adversarial weather" in closeout
    assert "final false-one crowns" in closeout
    assert "manuscript v2" in go_no_go.lower()
    assert "v1.8" in go_no_go
    assert "v1.7.10-alpha" in release
    assert "physics" in claim_card
    assert "Core Question Closeout" in current_state


def test_v1_7_10_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_core_question_closeout_read.md").exists()
    assert (out / "v1_7_core_question_closeout_bundle.zip").exists()
