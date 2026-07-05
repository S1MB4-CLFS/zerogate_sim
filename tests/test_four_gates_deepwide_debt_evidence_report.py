from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.four_gates_deepwide_debt_evidence_report import write_four_gates_deepwide_debt_evidence_report

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _matrix_dir(
    root: Path,
    name: str,
    *,
    profile: str,
    candidate_profile: str,
    earned: int = 0,
    false_pressure: int = 0,
    latent: int = 0,
    relation_debt: int = 0,
    return_debt: int = 0,
) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("matrix_summary.md").write_text(
        "\n".join(
            [
                "# ZeroGateSim Trinary Matrix Summary",
                f"Profile: `{profile}`",
                f"Candidate profile: `{candidate_profile}`",
                "Seeds per scenario: `0` through `8`",
                "Total runs: `243`",
            ]
        ),
        encoding="utf-8",
    )
    _write_csv(
        path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "E00",
                "kind": "earned_return_control",
                "truth_role": "expresser",
                "final_trinary_value": 1 if earned else 0,
                "final_trinary_symbol": "+1" if earned else "0",
                "final_band": "earned_one" if earned else "contained",
                "final_earned_one_count": earned,
                "raw_expression_pressure": earned + latent + relation_debt + return_debt,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": relation_debt,
                "return_debt_count": return_debt,
                "mean_return_potential": 0.9,
                "mean_return_observed": 0.4 if return_debt else 0.9,
                "echo_independence_band": "independent",
                "relation_dependency_score": 0.0,
                "echo_independence_score": 1.0,
                "relation_minus_raw_expression": 0,
                "relation_zero_raw_expression": 0,
                "relation_plus_raw_expression": earned,
            },
            {
                "candidate_id": "T00",
                "kind": "false_one_trap_control",
                "truth_role": "trap",
                "final_trinary_value": -1,
                "final_trinary_symbol": "-1",
                "final_band": "false_one_demoted" if false_pressure else "trap_contained",
                "final_earned_one_count": 0,
                "raw_expression_pressure": false_pressure,
                "raw_false_one_pressure": false_pressure,
                "false_one_demoted_count": false_pressure,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": 0,
                "return_debt_count": 0,
                "mean_return_potential": 0.9,
                "mean_return_observed": 0.9,
                "echo_independence_band": "independent",
                "relation_dependency_score": 0.0,
                "echo_independence_score": 1.0,
                "relation_minus_raw_expression": 0,
                "relation_zero_raw_expression": 0,
                "relation_plus_raw_expression": false_pressure,
            },
        ],
    )
    _write_csv(
        path / "matrix_known_logic_closeout_summary.csv",
        [
            {
                "mirror": "native_trinary",
                "primary_pressure_count": false_pressure + latent + relation_debt + return_debt,
                "secondary_pressure_count": 0,
                "safety_breach_count": 0,
                "closeout_status": "pressure_visible_no_breach",
                "loss_report": "fixture",
            }
        ],
    )
    _write_csv(
        path / "nZ_rZ_eZ" / "seed_0" / "gate_scores.csv",
        [
            {
                "candidate_id": "E00",
                "kind": "earned_return_control",
                "truth_role": "expresser",
                "strength": 0.9,
                "distinction": 0.9,
                "polarity": 0.9,
                "relation": 0.9,
                "return_observed": 0.9,
                "expressed": "True",
                "trinary_value": 1,
            },
            {
                "candidate_id": "T00",
                "kind": "false_one_trap_control",
                "truth_role": "trap",
                "strength": 0.9,
                "distinction": 0.9,
                "polarity": 0.9,
                "relation": 0.9,
                "return_observed": 0.2,
                "expressed": "True" if false_pressure else "False",
                "trinary_value": 1 if false_pressure else 0,
            },
        ],
    )
    return path


def _native_fixture(root: Path, *, profile: str) -> list[Path]:
    return [
        _matrix_dir(root, f"distinction_{profile}", profile=profile, candidate_profile="adversary_distinction", earned=4),
        _matrix_dir(root, f"polarity_{profile}", profile=profile, candidate_profile="adversary_polarity", earned=5, false_pressure=8, latent=2),
        _matrix_dir(root, f"relation_{profile}", profile=profile, candidate_profile="adversary_relation", earned=5, false_pressure=6),
        _matrix_dir(root, f"return_{profile}", profile=profile, candidate_profile="adversary_return", earned=5, false_pressure=7),
    ]


def _debt_fixture(root: Path, *, profile: str) -> Path:
    path = _matrix_dir(root, f"debt_{profile}", profile=profile, candidate_profile="four_gates_debt", earned=9, relation_debt=11, return_debt=13)
    rows = list(csv.DictReader((path / "matrix_final_output_summary.csv").open(newline="", encoding="utf-8")))
    rows.extend(
        [
            {
                **rows[0],
                "candidate_id": "D04",
                "kind": "relation_debt_global_a",
                "truth_role": "latent",
                "final_trinary_value": 0,
                "final_trinary_symbol": "0",
                "final_band": "relation_debt_hold",
                "final_earned_one_count": 0,
                "raw_expression_pressure": 11,
                "relation_debt_count": 11,
                "return_debt_count": 0,
            },
            {
                **rows[0],
                "candidate_id": "D03",
                "kind": "return_debt_local",
                "truth_role": "latent",
                "final_trinary_value": 0,
                "final_trinary_symbol": "0",
                "final_band": "return_debt_hold",
                "final_earned_one_count": 0,
                "raw_expression_pressure": 13,
                "relation_debt_count": 0,
                "return_debt_count": 13,
            },
        ]
    )
    _write_csv(path / "matrix_final_output_summary.csv", rows)
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_four_gates_deepwide_debt_requires_both_rungs(tmp_path: Path) -> None:
    deep_native = _native_fixture(tmp_path / "deep_native", profile="deep81")
    deep_debt = _debt_fixture(tmp_path / "deep_debt", profile="deep81")
    wide_debt = _debt_fixture(tmp_path / "wide_debt", profile="wide243")
    with pytest.raises(ValueError, match="wide243"):
        write_four_gates_deepwide_debt_evidence_report(
            output_dir=tmp_path / "out",
            deep81_matrix_dirs=deep_native,
            deep81_debt_matrix_dir=deep_debt,
            wide243_matrix_dirs=[],
            wide243_debt_matrix_dir=wide_debt,
        )


def test_four_gates_deepwide_debt_rejects_wrong_debt_profile(tmp_path: Path) -> None:
    deep_native = _native_fixture(tmp_path / "deep_native", profile="deep81")
    wide_native = _native_fixture(tmp_path / "wide_native", profile="wide243")
    deep_debt = _matrix_dir(tmp_path / "wrong", "debt_deep81", profile="deep81", candidate_profile="adversary_relation")
    wide_debt = _debt_fixture(tmp_path / "wide_debt", profile="wide243")
    with pytest.raises(ValueError, match="four_gates_debt"):
        write_four_gates_deepwide_debt_evidence_report(
            output_dir=tmp_path / "out",
            deep81_matrix_dirs=deep_native,
            deep81_debt_matrix_dir=deep_debt,
            wide243_matrix_dirs=wide_native,
            wide243_debt_matrix_dir=wide_debt,
        )


def test_four_gates_deepwide_debt_report_expands_when_both_rungs_visible(tmp_path: Path) -> None:
    deep_native = _native_fixture(tmp_path / "deep_native", profile="deep81")
    wide_native = _native_fixture(tmp_path / "wide_native", profile="wide243")
    deep_debt = _debt_fixture(tmp_path / "deep_debt", profile="deep81")
    wide_debt = _debt_fixture(tmp_path / "wide_debt", profile="wide243")
    paths = write_four_gates_deepwide_debt_evidence_report(
        output_dir=tmp_path / "out",
        deep81_matrix_dirs=deep_native,
        deep81_debt_matrix_dir=deep_debt,
        wide243_matrix_dirs=wide_native,
        wide243_debt_matrix_dir=wide_debt,
    )
    for key in ["read", "decision", "rung_summary", "native_seed_block", "native_ablation_summary", "debt_candidate_lanes", "state_lanes", "audit", "bundle"]:
        assert paths[key].exists()
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    lanes = _read_csv(paths["state_lanes"])
    debt_rows = _read_csv(paths["debt_candidate_lanes"])
    assert decision["version"] == "v1.6.21-alpha"
    assert decision["global_decision"] == "expand_four_gates_deepwide_debt_evidence"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["loaded_rungs"] == ["deep81", "wide243"]
    assert {row["weather_rung"] for row in lanes} == {"deep81", "wide243"}
    assert any(row["assigned_lane"] == "0 relation debt" for row in debt_rows)
    assert any(row["assigned_lane"] == "0 return debt" for row in debt_rows)
    for rung in ["deep81", "wide243"]:
        assert decision["debt_counts_by_rung"][rung]["relation_debt"] > 0
        assert decision["debt_counts_by_rung"][rung]["return_debt"] > 0


def test_four_gates_deepwide_debt_public_surfaces_are_current() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/four_gates_deepwide_debt_evidence.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_21_alpha.md").read_text(encoding="utf-8")
    assert "1.6.27-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.6.27a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.21-alpha" in text
        assert "deep81 / wide243 debt evidence" in text
        assert "C_Z = min(D, P, R, B)" in text
        assert "observed-universe bridge" in text
    assert "v1.6.22-alpha" in roadmap
    assert "fresh-seed debt reproduction" in roadmap
