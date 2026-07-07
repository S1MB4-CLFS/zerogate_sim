from __future__ import annotations

import json
from pathlib import Path

from zerogate_sim.v1_7_core_question_contract import (
    BOUNDED_CLAIM_UNDER_TEST,
    CORE_QUESTION,
    CURRENT_VERSION,
    NATIVE_WITNESS,
    V1_7_DECISION_STATE,
    build_v1_7_core_question_contract,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_core_question_contract_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_core_question_contract(tmp_path / "out")
    for key in ["read", "contract", "lanes", "answer_states", "falsifiers", "forbidden", "audit", "bundle"]:
        assert paths[key].exists(), key

    contract = json.loads(paths["contract"].read_text(encoding="utf-8"))
    assert contract["version"] == CURRENT_VERSION
    assert contract["decision_state"] == V1_7_DECISION_STATE
    assert contract["core_question"] == CORE_QUESTION
    assert contract["native_witness"] == NATIVE_WITNESS
    assert contract["bounded_claim_under_test"] == BOUNDED_CLAIM_UNDER_TEST
    assert contract["evidence_added"] is False
    assert contract["manuscript_v2_started"] is False
    assert contract["native_math_mutated"] is False
    assert contract["answer_states"] == ["+1", "0", "-1"]
    assert set(contract["required_lanes"]) == {
        "earned_one",
        "raw_expression_pressure",
        "latent_overcrown",
        "relation_debt",
        "return_debt",
        "false_one_pressure",
    }

    lanes = paths["lanes"].read_text(encoding="utf-8")
    for lane in ["earned_one", "raw_expression_pressure", "latent_overcrown", "relation_debt", "return_debt", "false_one_pressure"]:
        assert lane in lanes

    falsifiers = paths["falsifiers"].read_text(encoding="utf-8")
    for needle in ["baseline_equivalence", "role_label_recounting", "return_specificity_collapse", "false_one_final_crown"]:
        assert needle in falsifiers

    forbidden = paths["forbidden"].read_text(encoding="utf-8")
    assert "observed_universe_bridge" in forbidden
    assert "role_blind_discovery_solved" in forbidden
    assert "new_native_gate_or_mutated_native_math" in forbidden

    read_text = paths["read"].read_text(encoding="utf-8")
    assert CORE_QUESTION in read_text
    assert "does not answer the question yet" in read_text
    assert "v1.7.1-alpha" in read_text


def test_v1_7_core_question_contract_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_core_question_contract_read.md").exists()
    assert (out / "v1_7_core_question_contract_bundle.zip").exists()


def test_v1_7_0_public_surfaces_remain_historical_under_current_package() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    release = read("docs/release_notes/v1_7_0_alpha.md")

    assert "1.7.2-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.2a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-core-question-contract" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, release]:
        assert "v1.7.0-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    for doc_path in [
        "docs/v1_7_core_question_contract.md",
        "docs/v1_7_answer_grammar.md",
        "docs/v1_7_forbidden_claims.md",
        "docs/v1_7_falsifier_register.md",
    ]:
        doc = read(doc_path)
        assert CORE_QUESTION in doc
        assert "controlled synthetic-field" in doc

    assert "no new evidence crown" in read("docs/v1_7_core_question_contract.md")
    assert "role-blind discovery" in read("docs/v1_7_forbidden_claims.md")
    assert "return specificity collapse" in read("docs/v1_7_falsifier_register.md")
    assert "v1.7.1-alpha" in roadmap
    assert "v1.7.1-alpha" in read("docs/release_notes/v1_7_1_alpha.md")
