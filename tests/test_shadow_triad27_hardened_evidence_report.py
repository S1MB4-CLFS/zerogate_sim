from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.gates import GateScores
from zerogate_sim.shadow_triad27_hardened_evidence_report import write_shadow_triad27_hardened_evidence_report

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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _gate_row(candidate_id: str, *, truth_role: str, expressed: bool, strength: float, relation: float, ret: float) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "kind": f"{truth_role}_kind",
        "description": "fixture candidate",
        "designed_stable": truth_role == "expresser",
        "truth_role": truth_role,
        "expected_trinary": 1 if truth_role == "expresser" else 0 if truth_role == "latent" else -1,
        "strength": strength,
        "distinction": 0.8,
        "polarity": 0.7,
        "relation": relation,
        "return_observed": ret,
        "return_potential": 0.5,
        "echo_mimic_score": 0.1,
        "echo_mimic_band": "low_echo_pressure",
        "zero_coherence": min(0.8, 0.7, relation, ret),
        "zero_depth": 4 if expressed else 1,
        "expressed": expressed,
        "trinary_value": 1 if expressed else 0,
        "trinary_outcome": "expressed" if expressed else "held",
        "outcome_reason": "fixture",
        "latent_score": 0.2,
        "zero_band_value": 1 if expressed else 0,
        "zero_band": "expressed" if expressed else "witness_hold",
        "zero_band_symbol": "+1" if expressed else "0",
        "zero_band_reason": "fixture",
        "limiting_gate": "return" if ret < relation else "relation",
        "observed_stability_score": 0.6,
        "observed_stable": expressed,
    }


def _matrix_dir(base: Path, *, gate: str, candidate_profile: str, trap_expressed: bool) -> Path:
    matrix = base / f"{gate}_triad27"
    matrix.mkdir(parents=True)
    (matrix / "matrix_summary.md").write_text(
        "# Matrix\n\n"
        "Profile: `triad27`\n"
        f"Candidate profile: `{candidate_profile}`\n"
        "Seeds per scenario: `0` through `0`\n"
        "Total runs: `1`\n",
        encoding="utf-8",
    )
    scenario = "nM_rP_eZ" if gate in {"relation", "return"} else "nM_rM_eZ"
    _write_csv(
        matrix / "matrix_scenario_summary.csv",
        [
            {
                "scenario": scenario,
                "runs": 1,
                "noise_axis": -1,
                "relation_axis": 1 if gate in {"relation", "return"} else -1,
                "expansion_axis": 0,
                "perturbation_axis": "",
                "time_axis": "",
                "mean_designed_accuracy": 0.8,
                "mean_signal_health_accuracy": 0.8,
            }
        ],
    )
    _write_csv(
        matrix / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "T00",
                "kind": "trap_kind",
                "truth_role": "trap",
                "runs": 1,
                "raw_expression_pressure": 1 if trap_expressed else 0,
                "final_earned_one_count": 0,
                "raw_false_one_pressure": 1 if trap_expressed else 0,
                "false_one_demoted_count": 1 if trap_expressed else 0,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": 0,
                "final_trinary_value": -1,
                "final_trinary_symbol": "-1",
            }
        ],
    )
    _write_csv(
        matrix / "matrix_known_logic_closeout_summary.csv",
        [
            {
                "mirror": "fuzzy",
                "primary_pressure_count": 1 if trap_expressed else 0,
                "secondary_pressure_count": 0,
                "safety_breach_count": 0,
                "closeout_status": "pressure_visible_no_breach",
                "loss_report": "fixture",
            }
        ],
    )
    seed_dir = matrix / scenario / "seed_0"
    rows = [
        _gate_row("E00", truth_role="expresser", expressed=not trap_expressed, strength=0.7, relation=0.6, ret=0.6),
        _gate_row("T00", truth_role="trap", expressed=trap_expressed, strength=0.95 if trap_expressed else 0.2, relation=0.9 if trap_expressed else 0.2, ret=0.8 if trap_expressed else 0.1),
        _gate_row("L00", truth_role="latent", expressed=False, strength=0.3, relation=0.4, ret=0.3),
    ]
    _write_csv(seed_dir / "gate_scores.csv", rows)
    return matrix


def _matrix_dirs(tmp_path: Path) -> list[Path]:
    return [
        _matrix_dir(tmp_path, gate="distinction", candidate_profile="adversary_distinction", trap_expressed=False),
        _matrix_dir(tmp_path, gate="polarity", candidate_profile="adversary_polarity", trap_expressed=False),
        _matrix_dir(tmp_path, gate="relation", candidate_profile="adversary_relation", trap_expressed=True),
        _matrix_dir(tmp_path, gate="return", candidate_profile="adversary_return", trap_expressed=True),
    ]


def test_triad27_hardened_evidence_writes_standard_base_and_hardening(tmp_path: Path) -> None:
    paths = write_shadow_triad27_hardened_evidence_report(output_dir=tmp_path / "out", matrix_dirs=_matrix_dirs(tmp_path / "matrix"))
    for key in [
        "triad27_hardened_evidence_read",
        "triad27_hardened_evidence_audit",
        "triad27_hardened_evidence_bundle",
        "role_stripped_profile_features",
        "role_stripped_family_features",
        "role_stripped_evaluation_targets",
        "shadow_score_family_scores",
        "weather_hardening_decision",
    ]:
        assert paths[key].exists()

    decision = json.loads(paths["weather_hardening_decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] in {
        "resist_shadow_under_hardened_weather",
        "witness_shadow_trivial_under_hardened_weather",
        "witness_shadow_not_closed_under_hardened_weather",
        "expand_shadow_nontrivial_hardened_weather_not_detector",
    }
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"


def test_triad27_hardened_family_rows_are_cell_level_and_role_stripped(tmp_path: Path) -> None:
    paths = write_shadow_triad27_hardened_evidence_report(output_dir=tmp_path / "out", matrix_dirs=_matrix_dirs(tmp_path / "matrix"))
    features = _read_csv(paths["role_stripped_family_features"])
    targets = _read_csv(paths["role_stripped_evaluation_targets"])
    assert len(features) == 4
    header = set(features[0])
    assert "gate" not in header
    assert "truth_role" not in header
    assert "candidate_profile" not in header
    assert "feature_raw_strength_pressure_rate" in header
    assert "feature_weakest_gate_pressure_rate" in header
    assert "feature_relation_gate_rate" in header
    assert "feature_return_gate_rate" in header
    assert any(row.get("evaluation_family_label", "").startswith("return:") for row in targets)


def test_triad27_hardened_refuses_missing_four_gate_coverage(tmp_path: Path) -> None:
    dirs = _matrix_dirs(tmp_path / "matrix")[:-1]
    with pytest.raises(ValueError, match="Missing native gate matrix coverage"):
        write_shadow_triad27_hardened_evidence_report(output_dir=tmp_path / "out", matrix_dirs=dirs)


def test_triad27_hardened_docs_and_readme_name_v1_6_8_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/shadow_triad27_hardened_evidence.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_8_alpha.md").read_text(encoding="utf-8")
    for text in [readme, roadmap, doc, release]:
        assert "v1.6.8-alpha" in text
    assert "triad27 = 3^3 local expression weather" in doc
    assert "C_Z = min(D, P, R, B)" in doc
    assert "not role-blind discovery" in doc
