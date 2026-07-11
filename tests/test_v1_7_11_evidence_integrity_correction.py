from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.v1_7_evidence_integrity_correction import (
    ANSWER_SYMBOL,
    CANONICAL_CONTRACT_ID,
    CANONICAL_SEEDS,
    CURRENT_VERSION,
    EvidenceIntegrityError,
    OUTPUT_FILES,
    SCIENTIFIC_STATUS,
    _effective_axes,
    build_v1_7_evidence_integrity_correction,
    canonical_contract_payload,
    canonical_contract_sha256,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_case(
    root: Path,
    *,
    rung: str,
    scenario: str,
    seed: int = 18,
    strength: str = "0.75",
) -> None:
    run_dir = root / "family" / f"corpus_{rung}" / scenario / f"seed_{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    axis_map = {"M": -1, "Z": 0, "P": 1}
    parts = {part[0]: axis_map[part[1]] for part in scenario.split("_")}
    metadata = {
        "config": {
            "seed": seed,
            "n_steps": 100,
            "dt": 0.05,
            "noise_floor": 0.1,
            "near_zero_ratio": 0.12,
            "gate_threshold": 0.55,
            "strength_threshold": 0.4,
        },
        "run": {
            "generator": "tests.synthetic_generator",
            "n_candidates": 1,
            "matrix_profile": rung,
            "matrix_scenario": scenario,
            "matrix_candidate_profile": "fixture_corpus",
            "matrix_dt_factor": 1.0,
            "matrix_axes": {
                "noise_axis": parts["n"],
                "relation_axis": parts["r"],
                "expansion_axis": parts["e"],
                "perturbation_axis": parts.get("p"),
                "time_axis": parts.get("t"),
            },
        },
        "candidate_specs": [
            {
                "candidate_id": "C0",
                "amplitude": 1.0,
                "frequency": 0.8,
                "phase": 0.2,
                "noise": 0.03,
                "drift": 0.0,
                "bias": 0.0,
                "coupling_group": None,
                "relation_weight": 0.4,
                "truth_role": "expresser",
                "kind": "semantic_answer_key_not_identity",
            }
        ],
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    gate_row = {
        "candidate_id": "C0",
        "kind": "semantic_answer_key_not_identity",
        "description": "fixture",
        "designed_stable": "true",
        "truth_role": "expresser",
        "expected_trinary": "1",
        "strength": strength,
        "distinction": "0.8",
        "polarity": "0.7",
        "relation": "0.6",
        "return_observed": "0.5",
        "return_potential": "0.6",
        "echo_mimic_score": "0.1",
        "echo_mimic_band": "low_echo_pressure",
        "zero_coherence": "0.5",
        "zero_depth": "1",
        "expressed": "true",
        "trinary_value": "1",
        "trinary_outcome": "expressed",
        "outcome_reason": "fixture",
        "latent_score": "0.0",
        "zero_band_value": "1",
        "zero_band": "expressed",
        "zero_band_symbol": "+1",
        "zero_band_reason": "fixture",
        "limiting_gate": "return",
        "observed_stability_score": "0.7",
        "observed_stable": "true",
    }
    with (run_dir / "gate_scores.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(gate_row))
        writer.writeheader()
        writer.writerow(gate_row)


def _write_final_summary(
    root: Path,
    *,
    rung: str,
    runs: int,
    earned: int,
    raw: int,
    false_pressure: int,
) -> None:
    path = root / "family" / f"corpus_{rung}" / "matrix_final_output_summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "candidate_id": "C0",
        "kind": "semantic_answer_key_not_identity",
        "truth_role": "expresser",
        "runs": runs,
        "raw_expression_pressure": raw,
        "final_earned_one_count": earned,
        "raw_false_one_pressure": false_pressure,
        "false_one_demoted_count": false_pressure,
        "latent_overcrown_pressure": 0,
        "latent_overcrown_demoted_count": 0,
        "relation_debt_count": 0,
        "return_debt_count": 0,
        "final_trinary_value": 1,
        "final_trinary_symbol": "+1",
    }
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def _fixture_roots(tmp_path: Path, *, payload_mismatch: bool = False) -> dict[str, Path]:
    roots = {rung: tmp_path / rung for rung in ("triad27", "deep81", "wide243")}
    _write_case(roots["triad27"], rung="triad27", scenario="nM_rM_eM")
    _write_final_summary(roots["triad27"], rung="triad27", runs=1, earned=1, raw=1, false_pressure=0)

    _write_case(
        roots["deep81"],
        rung="deep81",
        scenario="nM_rM_eM_pM",
        strength="0.76" if payload_mismatch else "0.750",
    )
    _write_case(roots["deep81"], rung="deep81", scenario="nM_rM_eM_pZ")
    _write_final_summary(roots["deep81"], rung="deep81", runs=2, earned=2, raw=2, false_pressure=0)

    _write_case(roots["wide243"], rung="wide243", scenario="nM_rM_eM_pM_tZ")
    _write_case(roots["wide243"], rung="wide243", scenario="nM_rM_eM_pZ_tZ")
    _write_case(roots["wide243"], rung="wide243", scenario="nM_rM_eM_pZ_tP")
    _write_final_summary(roots["wide243"], rung="wide243", runs=3, earned=3, raw=3, false_pressure=0)
    return roots


def _build(tmp_path: Path, roots: dict[str, Path]) -> dict[str, Path]:
    return build_v1_7_evidence_integrity_correction(
        tmp_path / "out",
        triad_root=roots["triad27"],
        deep_root=roots["deep81"],
        wide_root=roots["wide243"],
        expected_candidate_profiles=["fixture_corpus"],
        expected_scenarios={
            "triad27": {"nM_rM_eM"},
            "deep81": {"nM_rM_eM_pM", "nM_rM_eM_pZ"},
            "wide243": {"nM_rM_eM_pM_tZ", "nM_rM_eM_pZ_tZ", "nM_rM_eM_pZ_tP"},
        },
        expected_seeds=[18],
    )


def test_missing_axes_normalize_to_operational_equivalents() -> None:
    assert _effective_axes("nM_rM_eM")["perturbation"] == -1
    assert _effective_axes("nM_rM_eM")["time"] == 0
    assert _effective_axes("nM_rM_eM_pM")["perturbation"] == -1
    assert _effective_axes("nM_rM_eM_pM")["time"] == 0


def test_canonical_contract_is_exact_and_hashable() -> None:
    contract = canonical_contract_payload()
    assert contract["contract_id"] == CANONICAL_CONTRACT_ID
    assert contract["seeds"] == list(CANONICAL_SEEDS) == list(range(18, 27))
    assert len(contract["candidate_profiles"]) == 5
    assert {rung: len(values) for rung, values in contract["scenarios"].items()} == {
        "triad27": 27,
        "deep81": 81,
        "wide243": 243,
    }
    assert len(canonical_contract_sha256()) == 64


def test_nested_cases_deduplicate_and_rates_use_explicit_denominators(tmp_path: Path) -> None:
    roots = _fixture_roots(tmp_path)
    paths = _build(tmp_path, roots)
    for key, name in OUTPUT_FILES.items():
        assert paths[key].exists(), name

    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["answer_symbol"] == ANSWER_SYMBOL
    assert decision["scientific_status"] == SCIENTIFIC_STATUS
    assert decision["structural_accounting_passed"] is True
    assert decision["canonical_contract_passed"] is False
    assert decision["accounting_integrity_passed"] is False
    assert decision["core_question_closed"] is False
    assert decision["declared_atomic_representations"] == 6
    assert decision["unique_atomic_cases"] == 3
    assert decision["duplicate_atomic_representations"] == 3
    assert decision["nested_rungs_consistent"] is True
    assert decision["unique_union_rung"] == "wide243"
    assert decision["legacy_pooled_opportunities"] == 6
    assert decision["unique_union_counts"] is None
    assert decision["candidate_widest_view_counts"]["opportunities"] == 3
    assert decision["candidate_widest_view_counts"]["earned_one"] == 3
    assert decision["legacy_pooled_totals_valid"] is False
    assert decision["manuscript_v2_go"] is False
    assert decision["dta_transfer_go"] is False
    assert decision["release_go"] is False

    with paths["rates"].open(newline="", encoding="utf-8") as f:
        rates = {row["weather_rung"]: row for row in csv.DictReader(f)}
    assert int(rates["wide243"]["opportunities"]) == 3
    assert float(rates["wide243"]["earned_one_rate"]) == pytest.approx(1.0)
    assert float(rates["wide243"]["false_one_pressure_rate"]) == pytest.approx(0.0)


def test_same_case_with_changed_payload_invalidates_accounting(tmp_path: Path) -> None:
    roots = _fixture_roots(tmp_path, payload_mismatch=True)
    paths = _build(tmp_path, roots)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["payload_mismatch_cases"] == 1
    assert decision["accounting_integrity_passed"] is False
    assert decision["evidence_status"] == "INVALID_FOR_BLIND_EMPIRICAL_DISCRIMINATION"
    assert decision["unique_union_counts"] is None
    with paths["nested_safe"].open(newline="", encoding="utf-8") as f:
        first_row = next(csv.DictReader(f))
    assert first_row["valid_as_unique_evidence"] == "false"


def test_tampered_final_summary_cannot_supply_authoritative_counts(tmp_path: Path) -> None:
    roots = _fixture_roots(tmp_path)
    summary = roots["wide243"] / "family" / "corpus_wide243" / "matrix_final_output_summary.csv"
    with summary.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    row["final_earned_one_count"] = "2"
    row["relation_debt_count"] = "1"
    with summary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    paths = _build(tmp_path, roots)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["final_summaries_match_recomputed_gate_rows"] is False
    assert decision["accounting_integrity_passed"] is False
    assert decision["unique_union_counts"] is None


def test_path_and_metadata_rung_mismatch_fails_closed(tmp_path: Path) -> None:
    roots = _fixture_roots(tmp_path)
    metadata = roots["wide243"] / "family" / "corpus_wide243" / "nM_rM_eM_pM_tZ" / "seed_18" / "metadata.json"
    value = json.loads(metadata.read_text(encoding="utf-8"))
    value["run"]["matrix_profile"] = "deep81"
    metadata.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="matrix_profile"):
        _build(tmp_path, roots)


def test_source_order_cannot_change_unique_union(tmp_path: Path) -> None:
    first_roots = _fixture_roots(tmp_path / "first")
    second_roots = {
        "wide243": first_roots["wide243"],
        "triad27": first_roots["triad27"],
        "deep81": first_roots["deep81"],
    }
    first = build_v1_7_evidence_integrity_correction(
        tmp_path / "first_out",
        triad_root=first_roots["triad27"],
        deep_root=first_roots["deep81"],
        wide_root=first_roots["wide243"],
        expected_candidate_profiles=["fixture_corpus"],
        expected_scenarios={
            "triad27": {"nM_rM_eM"},
            "deep81": {"nM_rM_eM_pM", "nM_rM_eM_pZ"},
            "wide243": {"nM_rM_eM_pM_tZ", "nM_rM_eM_pZ_tZ", "nM_rM_eM_pZ_tP"},
        },
        expected_seeds=[18],
    )
    second = build_v1_7_evidence_integrity_correction(
        tmp_path / "second_out",
        triad_root=second_roots["triad27"],
        deep_root=second_roots["deep81"],
        wide_root=second_roots["wide243"],
        expected_candidate_profiles=["fixture_corpus"],
        expected_scenarios={
            "triad27": {"nM_rM_eM"},
            "deep81": {"nM_rM_eM_pM", "nM_rM_eM_pZ"},
            "wide243": {"nM_rM_eM_pM_tZ", "nM_rM_eM_pZ_tZ", "nM_rM_eM_pZ_tP"},
        },
        expected_seeds=[18],
    )
    first_decision = json.loads(first["decision"].read_text(encoding="utf-8"))
    second_decision = json.loads(second["decision"].read_text(encoding="utf-8"))
    assert first_decision["candidate_widest_view_counts"] == second_decision["candidate_widest_view_counts"]
    assert first_decision["scientific_status"] == second_decision["scientific_status"]


def test_v1_7_11_public_contract_and_version_truth() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "HOLD_CONSTRUCTION_BOUND" in agents
    assert "Manuscript v2, DTA transfer" in agents


def test_evidence_integrity_cli(tmp_path: Path) -> None:
    roots = _fixture_roots(tmp_path)
    out = tmp_path / "cli"
    assert (
        main(
            [
                "--triad-root",
                str(roots["triad27"]),
                "--deep-root",
                str(roots["deep81"]),
                "--wide-root",
                str(roots["wide243"]),
                "--out",
                str(out),
            ]
        )
        == 2
    )
    assert (out / OUTPUT_FILES["decision"]).exists()
    assert (out / OUTPUT_FILES["bundle"]).exists()
