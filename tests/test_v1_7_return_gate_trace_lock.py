from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from zerogate_sim.gates import return_score, trinary_outcome_from_scores, zero_depth_from_gates
from zerogate_sim.v1_7_return_gate_trace import (
    CORE_QUESTION,
    CURRENT_VERSION,
    DECISION_STATE,
    NATIVE_WITNESS,
    build_v1_7_return_gate_trace,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_return_gate_trace_outputs(tmp_path: Path) -> None:
    paths = build_v1_7_return_gate_trace(tmp_path / "out")
    for key in ["read", "trace", "terms", "math_to_code", "debt_taxonomy", "false_return", "forbidden", "audit", "bundle"]:
        assert paths[key].exists(), key

    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))
    assert trace["version"] == CURRENT_VERSION
    assert trace["decision_state"] == DECISION_STATE
    assert trace["core_question"] == CORE_QUESTION
    assert trace["native_witness"] == NATIVE_WITNESS
    assert trace["evidence_added"] is False
    assert trace["native_math_mutated"] is False
    assert trace["manuscript_v2_started"] is False
    assert trace["return_trace_locked"] is True
    assert "Gamma is return-potential, not observed return" in trace["trace_spine"]
    assert "observed_return_B" in trace["required_distinctions"]
    assert "zero crossing equals return" in trace["forbidden_readings"]

    terms = paths["terms"].read_text(encoding="utf-8")
    for needle in ["return_potential_Gamma", "observed_return_B", "zero_gate_coherence_C_Z", "return_debt", "false_return_theater"]:
        assert needle in terms

    math_to_code = paths["math_to_code"].read_text(encoding="utf-8")
    assert "return_potential = clamp01(distinction * polarity * relation)" in math_to_code
    assert "return_score" in math_to_code
    assert "zero_coherence = min" in math_to_code

    debt = paths["debt_taxonomy"].read_text(encoding="utf-8")
    assert "return_debt_dpr_hold" in debt
    assert "closure_gap_candidate" in debt
    assert "structured zero" in debt

    forbidden = paths["forbidden"].read_text(encoding="utf-8")
    assert "Gamma is observed return" in forbidden
    assert "return-potential is physical gravity" in forbidden
    assert "C_Z can average over missing return" in forbidden

    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    assert audit["checks"]["gamma_separated_from_b"] is True
    assert audit["checks"]["b_separated_from_zero_crossing_only"] is True
    assert audit["checks"]["c_z_preserved_as_weakest_gate"] is True
    assert audit["checks"]["next_gate_is_lane_taxonomy"] is True


def test_v1_7_return_gate_trace_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / "v1_7_return_gate_trace_read.md").exists()
    assert (out / "v1_7_return_gate_trace_bundle.zip").exists()


def test_return_score_rejects_zero_crossing_theater() -> None:
    t = np.linspace(0.0, 12.0 * np.pi, 600)
    smooth_returner = np.sin(t)
    zero_crossing_theater = np.sign(np.sin(t)) * (1.0 + 0.03 * np.sin(7.0 * t))
    collapse_return = np.exp(-np.linspace(0.0, 5.0, 600)) * np.sin(t)

    smooth_score = return_score(smooth_returner)
    theater_score = return_score(zero_crossing_theater)
    collapse_score = return_score(collapse_return)

    assert smooth_score > 0.75
    assert theater_score < 0.25
    assert collapse_score < smooth_score / 3.0


def test_return_potential_does_not_crown_without_observed_return() -> None:
    depth = zero_depth_from_gates(
        distinction=0.90,
        polarity=0.90,
        relation=0.90,
        return_observed=0.20,
        threshold=0.55,
    )
    assert depth == 0

    trinary_value, trinary_outcome, outcome_reason, latent_score = trinary_outcome_from_scores(
        expressed=False,
        strength=0.80,
        distinction=0.90,
        polarity=0.90,
        relation=0.90,
        return_observed=0.20,
        return_potential=0.729,
        zero_coherence=0.20,
        zero_depth=0,
        gate_threshold=0.55,
        strength_threshold=0.30,
    )
    assert trinary_value == 0
    assert trinary_outcome == "held_latent"
    assert outcome_reason == "return_debt_dpr_hold"
    assert latent_score > 0.0


def test_v1_7_1_public_surfaces() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    version_truth = read("docs/version_truth.md")
    evidence_index = read("docs/current_evidence_index.md")
    release = read("docs/release_notes/v1_7_1_alpha.md")

    assert "1.7.11-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.11a0"' in read("pyproject.toml")
    assert "zerogate-v1-7-return-gate-trace" in read("pyproject.toml")

    for text in [readme, roadmap, version_truth, evidence_index, release]:
        assert "v1.7.1-alpha" in text
        assert "C_Z = min(D, P, R, B)" in text

    for doc_path in [
        "docs/v1_7_return_gate_trace.md",
        "docs/v1_7_return_potential_vs_observed_return.md",
        "docs/v1_7_return_debt_taxonomy.md",
        "docs/v1_7_return_gate_forbidden_readings.md",
    ]:
        doc = read(doc_path)
        assert "return" in doc.lower()
        assert "structured zero" in doc or "C_Z = min(D, P, R, B)" in doc

    assert "Gamma = D * P * R" in read("docs/v1_7_return_gate_trace.md")
    assert "zero crossing" in read("docs/v1_7_return_gate_forbidden_readings.md")
    assert "v1.7.2-alpha" in roadmap
