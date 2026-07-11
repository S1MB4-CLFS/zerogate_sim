from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.v1_7_core_question_closeout import (
    ANSWER_STATUS,
    ANSWER_SYMBOL,
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION,
    HISTORICAL_VERSION,
    NEXT_GATE,
    NATIVE_WITNESS,
    build_v1_7_core_question_closeout,
    main,
)
from zerogate_sim.v1_7_evidence_integrity_correction import (
    CANONICAL_CONTRACT_ID,
    canonical_contract_sha256,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _integrity_decision(path: Path) -> Path:
    value = {
        "version": CURRENT_VERSION,
        "decision": "evidence_integrity_correction_hold",
        "answer_symbol": "0/HOLD",
        "scientific_status": "HOLD_CONSTRUCTION_BOUND",
        "evidence_status": "INVALID_FOR_BLIND_EMPIRICAL_DISCRIMINATION",
        "core_question_closed": False,
        "accounting_integrity_passed": True,
        "canonical_contract_id": CANONICAL_CONTRACT_ID,
        "canonical_contract_sha256": canonical_contract_sha256(),
        "canonical_contract_passed": True,
        "legacy_pooled_totals_valid": False,
        "reason_codes": [
            "CONSTRUCTION_BOUND_FALSE_CROWNS",
            "NESTED_RUNG_POOLING_CORRECTED",
            "ROLE_FREE_WITNESS_NOT_IMPLEMENTED",
            "LINEAGE_NOT_IN_FINAL_PATH",
        ],
        "manuscript_v2_go": False,
        "dta_transfer_go": False,
        "release_go": False,
        "unique_union_counts": {
            "opportunities": 260253,
            "raw_expression_pressure": 14058,
            "earned_one": 9417,
            "false_one_pressure": 3543,
            "false_one_demoted": 3543,
            "latent_overcrown": 21,
            "latent_overcrown_demoted": 21,
            "relation_debt": 465,
            "return_debt": 612,
            "final_false_one_crowns": 0,
        },
        "legacy_non_independent_pooled_counts": {
            "opportunities": 375921,
            "raw_expression_pressure": 18353,
            "earned_one": 12206,
            "false_one_pressure": 4671,
            "false_one_demoted": 4671,
            "latent_overcrown": 39,
            "latent_overcrown_demoted": 39,
            "relation_debt": 624,
            "return_debt": 813,
            "final_false_one_crowns": 0,
        },
    }
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return path


def test_closeout_without_integrity_artifact_fails_closed(tmp_path: Path) -> None:
    paths = build_v1_7_core_question_closeout(tmp_path / "out")
    for key in ["read", "decision", "answer_status", "condition_status", "boundary", "go_no_go", "evidence", "bundle"]:
        assert paths[key].exists(), key

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["historical_version"] == HISTORICAL_VERSION
    assert decision["historical_status"] == "superseded_as_construction_bound"
    assert decision["decision"] == DECISION
    assert decision["answer_symbol"] == ANSWER_SYMBOL
    assert decision["answer_status"] == ANSWER_STATUS
    assert decision["core_question"] == CORE_QUESTION
    assert decision["core_question_closed"] is False
    assert decision["native_witness_unchanged"] == NATIVE_WITNESS
    assert decision["full_answer_conditions_passed"] is False
    assert decision["evidence_integrity_artifact_supplied"] is False
    assert decision["manuscript_v2_go"] == "hold"
    assert decision["dta_transfer_go"] == "hold"
    assert decision["next_gate"] == NEXT_GATE


def test_closeout_consumes_integrity_artifact_without_recrowning(tmp_path: Path) -> None:
    integrity = _integrity_decision(tmp_path / "integrity.json")
    paths = build_v1_7_core_question_closeout(
        tmp_path / "out",
        evidence_integrity_decision=integrity,
    )
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["evidence_integrity_artifact_supplied"] is True
    assert decision["accounting_integrity_passed"] is True
    assert decision["core_question_closed"] is False
    assert decision["unique_union_counts"]["opportunities"] == 260253
    assert decision["unique_union_counts"]["earned_one"] == 9417
    assert decision["legacy_non_independent_pooled_counts"]["opportunities"] == 375921
    assert decision["legacy_non_independent_pooled_counts"]["earned_one"] == 12206

    with paths["evidence"].open(newline="", encoding="utf-8") as f:
        evidence = list(csv.DictReader(f))
    assert evidence[0]["aggregation"] == "unique_atomic_union_descriptive"
    assert evidence[0]["valid_as_unique_evidence"] == "true"
    assert evidence[1]["aggregation"] == "legacy_nested_arithmetic_sum"
    assert evidence[1]["valid_as_unique_evidence"] == "false"

    conditions = paths["condition_status"].read_text(encoding="utf-8")
    assert "role_free_scoring,fail" in conditions
    assert "lineage_in_final_path,hold" in conditions


def test_closeout_rejects_forged_or_impossible_integrity_artifact(tmp_path: Path) -> None:
    integrity = _integrity_decision(tmp_path / "integrity.json")
    value = json.loads(integrity.read_text(encoding="utf-8"))
    value["core_question_closed"] = True
    integrity.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="core_question_closed"):
        build_v1_7_core_question_closeout(
            tmp_path / "forged",
            evidence_integrity_decision=integrity,
        )

    integrity = _integrity_decision(tmp_path / "impossible.json")
    value = json.loads(integrity.read_text(encoding="utf-8"))
    value["unique_union_counts"]["earned_one"] = 999999
    integrity.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="earned_one"):
        build_v1_7_core_question_closeout(
            tmp_path / "impossible",
            evidence_integrity_decision=integrity,
        )

    integrity = _integrity_decision(tmp_path / "wrong_contract.json")
    value = json.loads(integrity.read_text(encoding="utf-8"))
    value["canonical_contract_id"] = "caller-selected-contract"
    integrity.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="canonical_contract_id"):
        build_v1_7_core_question_closeout(
            tmp_path / "wrong_contract",
            evidence_integrity_decision=integrity,
        )

    integrity = _integrity_decision(tmp_path / "field_override.json")
    value = json.loads(integrity.read_text(encoding="utf-8"))
    value["unique_union_counts"]["aggregation"] = "forged"
    integrity.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="authorized count fields"):
        build_v1_7_core_question_closeout(
            tmp_path / "field_override",
            evidence_integrity_decision=integrity,
        )


def test_closeout_preserves_failed_accounting_without_issuing_unique_counts(tmp_path: Path) -> None:
    integrity = _integrity_decision(tmp_path / "failed.json")
    value = json.loads(integrity.read_text(encoding="utf-8"))
    value["accounting_integrity_passed"] = False
    value["unique_union_counts"] = None
    integrity.write_text(json.dumps(value), encoding="utf-8")

    paths = build_v1_7_core_question_closeout(
        tmp_path / "failed",
        evidence_integrity_decision=integrity,
    )
    with paths["evidence"].open(newline="", encoding="utf-8") as f:
        evidence = list(csv.DictReader(f))
    assert evidence[0]["aggregation"] == "unique_atomic_union_not_issued"
    assert evidence[0]["valid_as_unique_evidence"] == "false"
    assert evidence[0]["opportunities"] == ""
    assert evidence[1]["aggregation"] == "legacy_nested_arithmetic_sum"
    assert evidence[1]["opportunities"] == "375921"
    conditions = paths["condition_status"].read_text(encoding="utf-8")
    assert "evidence_integrity_artifact,hold_failed" in conditions


def test_v1_7_11_public_surfaces() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    current_state = read("docs/current_evidence_state.md")
    evidence_index = read("docs/current_evidence_index.md")
    correction = read("docs/v1_7_11_evidence_integrity_correction.md")
    release = read("docs/release_notes/v1_7_11_alpha.md")

    assert "zerogate-v1-7-evidence-integrity-correction" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, current_state, evidence_index, correction, release]:
        assert "v1.7.11-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text
        assert "HOLD" in text

    assert "Evidence Integrity Correction" in readme
    assert "Evidence Integrity Correction" in roadmap
    assert "construction-bound" in correction
    assert "260,253" in correction
    assert "375,921" in correction
    assert "DTA" in correction


def test_v1_7_11_closeout_cli(tmp_path: Path) -> None:
    integrity = _integrity_decision(tmp_path / "integrity.json")
    out = tmp_path / "cli"
    assert main(["--evidence-integrity-decision", str(integrity), "--out", str(out)]) == 0
    assert (out / "v1_7_core_question_closeout_read.md").exists()
    assert (out / "v1_7_core_question_closeout_bundle.zip").exists()
