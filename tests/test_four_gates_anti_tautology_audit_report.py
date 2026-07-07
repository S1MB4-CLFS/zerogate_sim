from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.four_gates_anti_tautology_audit_report import write_four_gates_anti_tautology_audit_report

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fake_evidence(root: Path, *, final_false: int = 0, relation_debt: int = 72, return_debt: int = 75) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    decision = {
        "global_decision": "expand_four_gates_deepwide_debt_evidence" if not final_false else "resist_four_gates_deepwide_debt_breach_or_regression",
        "loaded_rungs": ["deep81", "wide243"],
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    (root / "four_gates_deepwide_debt_evidence_decision.json").write_text(json.dumps(decision), encoding="utf-8")
    rung_rows = []
    state_rows = []
    candidate_rows = []
    for rung, factor in [("deep81", 1), ("wide243", 3)]:
        rd = relation_debt * factor
        ret = return_debt * factor
        row = {
            "weather_rung": rung,
            "decision": f"expand_four_gates_{rung}_debt_evidence" if not final_false else f"resist_four_gates_{rung}_debt_false_crown_breach",
            "native_total_matrix_runs": 2916 * factor,
            "debt_matrix_runs": 729 * factor,
            "final_earned_one_events": 1900 * factor,
            "native_final_earned_one_events": 1500 * factor,
            "debt_earned_one_events": 400 * factor,
            "raw_false_one_pressure": 900 * factor,
            "false_one_demoted_count": 900 * factor,
            "latent_overcrown_pressure": 0,
            "relation_debt_count": rd,
            "return_debt_count": ret,
            "final_false_one_crowns": final_false,
            "ablation_wounding_enemy_count": 7,
            "relation_debt_visible": rd > 0,
            "return_debt_visible": ret > 0,
        }
        rung_rows.append(row)
        state_rows.extend(
            [
                {"weather_rung": rung, "lane": "+1 earned-one", "count": row["final_earned_one_events"], "meaning": "earned", "lane_status": "visible"},
                {"weather_rung": rung, "lane": "0 relation debt", "count": rd, "meaning": "relation", "lane_status": "visible" if rd else "not_visible"},
                {"weather_rung": rung, "lane": "0 return debt", "count": ret, "meaning": "return", "lane_status": "visible" if ret else "not_visible"},
                {"weather_rung": rung, "lane": "-1 false-one pressure", "count": row["raw_false_one_pressure"], "meaning": "false", "lane_status": "visible"},
                {"weather_rung": rung, "lane": "-1 final false-one crowns", "count": final_false, "meaning": "breach", "lane_status": "clean_zero" if not final_false else "breach"},
            ]
        )
        candidate_rows.extend(
            [
                {
                    "weather_rung": rung,
                    "matrix_label": f"four_gates_debt_{rung}",
                    "profile": rung,
                    "candidate_profile": "four_gates_debt",
                    "candidate_id": "D00",
                    "kind": "earned_return_control",
                    "truth_role": "expresser",
                    "assigned_lane": "+1 earned-one",
                    "raw_expression_pressure": 200 * factor,
                    "final_earned_one_count": 200 * factor,
                    "latent_overcrown_pressure": 0,
                    "relation_debt_count": 0,
                    "return_debt_count": 0,
                    "raw_false_one_pressure": 0,
                    "false_one_demoted_count": 0,
                    "final_false_one_crowns": 0,
                    "final_band": "earned_one",
                    "final_trinary_symbol": "+1",
                },
                {
                    "weather_rung": rung,
                    "matrix_label": f"four_gates_debt_{rung}",
                    "profile": rung,
                    "candidate_profile": "four_gates_debt",
                    "candidate_id": "D03",
                    "kind": "relation_debt_global_a",
                    "truth_role": "latent",
                    "assigned_lane": "0 relation debt",
                    "raw_expression_pressure": 100 * factor,
                    "final_earned_one_count": 0,
                    "latent_overcrown_pressure": 0,
                    "relation_debt_count": rd,
                    "return_debt_count": 0,
                    "raw_false_one_pressure": 0,
                    "false_one_demoted_count": 0,
                    "final_false_one_crowns": 0,
                    "final_band": "relation_debt",
                    "final_trinary_symbol": "0",
                },
                {
                    "weather_rung": rung,
                    "matrix_label": f"four_gates_debt_{rung}",
                    "profile": rung,
                    "candidate_profile": "four_gates_debt",
                    "candidate_id": "D05",
                    "kind": "return_debt_local",
                    "truth_role": "latent",
                    "assigned_lane": "0 return debt",
                    "raw_expression_pressure": 150 * factor,
                    "final_earned_one_count": 0,
                    "latent_overcrown_pressure": 0,
                    "relation_debt_count": 0,
                    "return_debt_count": ret,
                    "raw_false_one_pressure": 0,
                    "false_one_demoted_count": 0,
                    "final_false_one_crowns": 0,
                    "final_band": "return_debt",
                    "final_trinary_symbol": "0",
                },
            ]
        )
    _write_csv(root / "four_gates_deepwide_debt_rung_summary.csv", rung_rows)
    _write_csv(root / "four_gates_deepwide_state_lanes.csv", state_rows)
    _write_csv(root / "four_gates_deepwide_debt_candidate_lanes.csv", candidate_rows)
    return root


def _fake_reproduction(root: Path, *, relation_debt: int = 72, return_debt: int = 75, final_false: int = 0) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    decision = {
        "global_decision": "expand_four_gates_fresh_seed_debt_reproduction" if not final_false and relation_debt and return_debt else "witness_four_gates_fresh_seed_debt_partial",
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "reference_label": "seed-range-0-8",
        "fresh_label": "fresh-seed-range-9-17",
    }
    (root / "four_gates_fresh_seed_debt_reproduction_decision.json").write_text(json.dumps(decision), encoding="utf-8")
    rung_rows = []
    state_rows = []
    for rung, factor in [("deep81", 1), ("wide243", 3)]:
        rd = relation_debt * factor
        ret = return_debt * factor
        rung_rows.append(
            {
                "weather_rung": rung,
                "reproduction_status": "expand_fresh_seed_pattern_reproduced" if not final_false and rd and ret else "witness_fresh_seed_core_reproduced_debt_partial",
                "reference_decision": f"expand_four_gates_{rung}_debt_evidence",
                "fresh_decision": f"expand_four_gates_{rung}_debt_evidence",
                "reference_native_runs": 2916 * factor,
                "fresh_native_runs": 2916 * factor,
                "reference_debt_runs": 729 * factor,
                "fresh_debt_runs": 729 * factor,
                "reference_earned": 2000 * factor,
                "fresh_earned": 1900 * factor,
                "reference_latent": 9 * factor,
                "fresh_latent": 0,
                "reference_relation_debt": 54 * factor,
                "fresh_relation_debt": rd,
                "reference_return_debt": 123 * factor,
                "fresh_return_debt": ret,
                "reference_raw_false": 924 * factor,
                "fresh_raw_false": 900 * factor,
                "reference_demoted": 924 * factor,
                "fresh_demoted": 900 * factor,
                "reference_final_false_crowns": 0,
                "fresh_final_false_crowns": final_false,
                "reference_ablation_wounds": 8,
                "fresh_ablation_wounds": 7,
                "reference_quality_passed": True,
                "fresh_quality_passed": not bool(final_false) and bool(rd) and bool(ret),
            }
        )
        for lane, count in [("+1 earned-one", 1900 * factor), ("0 relation debt", rd), ("0 return debt", ret), ("-1 false-one pressure", 900 * factor), ("-1 final false-one crowns", final_false)]:
            state_rows.append(
                {
                    "weather_rung": rung,
                    "lane": lane,
                    "reference_count": count,
                    "fresh_count": count,
                    "reference_status": "visible" if count else "clean_zero",
                    "fresh_status": "visible" if count else "clean_zero",
                    "lane_reproduced": not (lane in {"0 relation debt", "0 return debt"} and count == 0),
                }
            )
    _write_csv(root / "four_gates_fresh_seed_rung_comparison.csv", rung_rows)
    _write_csv(root / "four_gates_fresh_seed_state_lane_comparison.csv", state_rows)
    return root


def test_anti_tautology_audit_bounds_role_shaped_but_witness_computed(tmp_path: Path) -> None:
    reproduction = _fake_reproduction(tmp_path / "reproduction")
    evidence = _fake_evidence(tmp_path / "evidence")
    paths = write_four_gates_anti_tautology_audit_report(
        output_dir=tmp_path / "out",
        fresh_reproduction_dir=reproduction,
        fresh_evidence_dir=evidence,
    )
    for key in ["read", "decision", "role_dependence", "witness_dependence", "masked_evaluation", "debt_specificity", "audit", "bundle"]:
        assert paths[key].exists()
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    role_rows = _read_csv(paths["role_dependence"])
    masked = _read_csv(paths["masked_evaluation"])
    assert decision["version"] == "v1.6.25-alpha"
    assert decision["global_decision"] == "witness_bounded_role_shaped_but_witness_computed"
    assert decision["claim_status"].startswith("0 bounded audit")
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["stronger_claim_not_earned"] == "independent role-blind discovery of debt states"
    assert any(row["role_dependence_status"] == "high_designed_candidate_profile_dependence" for row in role_rows)
    assert {row["masked_pattern_status"] for row in masked} == {"masked_numeric_pattern_visible"}


def test_anti_tautology_audit_holds_missing_debt_lanes(tmp_path: Path) -> None:
    reproduction = _fake_reproduction(tmp_path / "reproduction", relation_debt=0, return_debt=0)
    evidence = _fake_evidence(tmp_path / "evidence", relation_debt=0, return_debt=0)
    paths = write_four_gates_anti_tautology_audit_report(
        output_dir=tmp_path / "out",
        fresh_reproduction_dir=reproduction,
        fresh_evidence_dir=evidence,
    )
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] == "hold_anti_tautology_audit_incomplete"


def test_anti_tautology_audit_resists_false_crown_breach(tmp_path: Path) -> None:
    reproduction = _fake_reproduction(tmp_path / "reproduction", final_false=1)
    evidence = _fake_evidence(tmp_path / "evidence", final_false=1)
    paths = write_four_gates_anti_tautology_audit_report(
        output_dir=tmp_path / "out",
        fresh_reproduction_dir=reproduction,
        fresh_evidence_dir=evidence,
    )
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] == "resist_anti_tautology_audit_breach_or_regression"


def test_anti_tautology_audit_rejects_missing_required_inputs(tmp_path: Path) -> None:
    reproduction = _fake_reproduction(tmp_path / "reproduction")
    evidence = _fake_evidence(tmp_path / "evidence")
    (evidence / "four_gates_deepwide_debt_candidate_lanes.csv").unlink()
    with pytest.raises(FileNotFoundError):
        write_four_gates_anti_tautology_audit_report(
            output_dir=tmp_path / "out",
            fresh_reproduction_dir=reproduction,
            fresh_evidence_dir=evidence,
        )


def test_v1_6_25_public_surfaces_and_route() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/anti_tautology_audit_report.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_25_alpha.md").read_text(encoding="utf-8")
    assert "1.7.4-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.7.4a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.25-alpha" in text
        assert "Anti-Tautology Audit" in text or "anti-tautology" in text
        assert "C_Z = min(D, P, R, B)" in text
    assert "v1.6.28-alpha" in roadmap
    assert "Reproduction Command Package" in roadmap
    assert "independent role-blind discovery" in doc
