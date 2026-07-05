from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.native_ablation_baselines_report import (
    build_native_ablation_rows,
    write_native_ablation_baselines_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _matrix_dir(
    root: Path,
    run_id: str,
    *,
    profile: str,
    candidate_profile: str,
    earned: int = 0,
    false_pressure: int = 0,
    latent: int = 0,
    relation_debt: int = 0,
    return_debt: int = 0,
) -> Path:
    path = root / run_id
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("matrix_summary.md").write_text(
        "\n".join(
            [
                "# ZeroGateSim Trinary Matrix Summary",
                f"Profile: `{profile}`",
                f"Candidate profile: `{candidate_profile}`",
                "Seeds per scenario: `0` through `2`",
                "Total runs: `81`",
            ]
        ),
        encoding="utf-8",
    )
    _write_csv(
        path / "matrix_final_output_summary.csv",
        [
            {
                "candidate_id": "F00",
                "kind": "stable_core",
                "truth_role": "expresser",
                "final_trinary_value": 1 if earned else 0,
                "final_trinary_symbol": "+1" if earned else "0",
                "final_earned_one_count": earned,
                "raw_expression_pressure": earned + relation_debt + return_debt,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": relation_debt,
                "return_debt_count": return_debt,
                "mean_return_potential": 0.8,
                "mean_return_observed": 0.3 if return_debt else 0.8,
            },
            {
                "candidate_id": "F13",
                "kind": "probe",
                "truth_role": "latent",
                "final_trinary_value": 0,
                "final_trinary_symbol": "0+" if latent else "0",
                "final_earned_one_count": 0,
                "raw_expression_pressure": latent,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": 0,
                "return_debt_count": 0,
                "mean_return_potential": 0.7,
                "mean_return_observed": 0.7,
            },
            {
                "candidate_id": "F26",
                "kind": "trap",
                "truth_role": "trap",
                "final_trinary_value": -1,
                "final_trinary_symbol": "-1",
                "final_earned_one_count": 0,
                "raw_expression_pressure": false_pressure,
                "raw_false_one_pressure": false_pressure,
                "false_one_demoted_count": false_pressure,
                "latent_overcrown_pressure": 0,
                "latent_overcrown_demoted_count": 0,
                "relation_debt_count": 0,
                "return_debt_count": 0,
                "mean_return_potential": 0.7,
                "mean_return_observed": 0.7,
            },
        ],
    )
    _write_csv(
        path / "nZ_rZ_eZ" / "seed_0" / "gate_scores.csv",
        [
            {
                "candidate_id": "F00",
                "kind": "stable_core",
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
                "candidate_id": "F13",
                "kind": "probe",
                "truth_role": "latent",
                "strength": 0.9,
                "distinction": 0.9,
                "polarity": 0.9,
                "relation": 0.2,
                "return_observed": 0.9,
                "expressed": "False",
                "trinary_value": 0,
            },
            {
                "candidate_id": "F26",
                "kind": "trap",
                "truth_role": "trap",
                "strength": 0.9,
                "distinction": 0.9,
                "polarity": 0.9,
                "relation": 0.9,
                "return_observed": 0.2,
                "expressed": "False",
                "trinary_value": 0,
            },
        ],
    )
    return path


def _four_gate_fixture(root: Path) -> list[Path]:
    return [
        _matrix_dir(root, "distinction_triad27", profile="triad27", candidate_profile="adversary_distinction", earned=0),
        _matrix_dir(root, "polarity_triad27", profile="triad27", candidate_profile="adversary_polarity", earned=2, false_pressure=6),
        _matrix_dir(root, "relation_triad27", profile="triad27", candidate_profile="adversary_relation", earned=2, false_pressure=3, latent=5, relation_debt=4),
        _matrix_dir(root, "return_triad27", profile="triad27", candidate_profile="adversary_return", earned=2, false_pressure=4, return_debt=7),
    ]


def _by_baseline(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row["baseline"]): row for row in rows}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_native_ablation_requires_four_gates(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")[:3]
    with pytest.raises(ValueError, match="return"):
        build_native_ablation_rows(dirs)


def test_native_ablation_summary_exposes_raw_and_dead_safe_failures(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    _gate_rows, summary_rows = build_native_ablation_rows(dirs)
    summary = _by_baseline(summary_rows)

    assert summary["native_final_trinary_witness"]["final_false_one_crowns"] == 0
    assert summary["native_final_trinary_witness"]["final_earned_one_events"] == 6
    assert summary["raw_expression_only"]["final_false_one_crowns"] == 13
    assert "breach_introduced" in str(summary["raw_expression_only"]["baseline_status"])
    assert summary["dead_safe_no_crown"]["earned_lost"] == 6
    assert "dead_safe_fails_earned_preservation" in str(summary["dead_safe_no_crown"]["baseline_status"])


def test_native_ablation_summary_exposes_zero_relation_return_failures(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    _gate_rows, summary_rows = build_native_ablation_rows(dirs)
    summary = _by_baseline(summary_rows)

    assert summary["no_zero_hold"]["structured_zero_promoted"] == 16
    assert summary["no_echo_independence"]["structured_zero_promoted"] == 4
    assert summary["no_return_debt_witness"]["structured_zero_promoted"] == 7


def test_gate_ablation_variants_use_per_seed_gate_scores(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    _gate_rows, summary_rows = build_native_ablation_rows(dirs)
    summary = _by_baseline(summary_rows)

    assert summary["no_relation_gate_raw"]["final_earned_one_events"] >= summary["native_final_trinary_witness"]["final_earned_one_events"]
    assert summary["no_return_gate_raw"]["final_false_one_crowns"] >= 4
    assert summary["average_gate_raw"]["raw_expression_pressure"] > 0


def test_write_native_ablation_baselines_definition_only(tmp_path: Path) -> None:
    paths = write_native_ablation_baselines_report(output_dir=tmp_path / "defs")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    definitions = _read_csv(paths["definitions"])

    assert decision["global_decision"] == "hold_baseline_definitions_only"
    assert decision["matrix_dirs_supplied"] == 0
    assert "No matrix directories were supplied" in read
    assert {row["name"] for row in definitions} >= {"raw_expression_only", "no_return_gate_raw", "dead_safe_no_crown"}
    assert paths["bundle"].exists()


def test_write_native_ablation_baselines_evaluation_outputs(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    paths = write_native_ablation_baselines_report(output_dir=tmp_path / "report", matrix_dirs=dirs)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    summary = _read_csv(paths["summary"])

    assert decision["global_decision"] == "expand_native_ablation_enemies_expose_witness_work"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert "dead_safe_no_crown" in read
    assert len(summary) >= 10
    assert paths["bundle"].exists()


def test_public_version_truth_surfaces_include_v1_6_16_current_and_v1_6_15_history() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_15_alpha.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/native_ablation_baselines.md").read_text(encoding="utf-8")
    assert "1.6.18-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.6.18a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth]:
        assert "v1.6.16-alpha" in text
        assert "four-corpus triad27 native evidence" in text
        assert "C_Z = min(D, P, R, B)" in text
    for text in [release, doc, roadmap, version_truth]:
        assert "v1.6.15-alpha" in text
        assert "native ablation baselines" in text
    assert "v1.6.18-alpha" in roadmap
    assert "deep81 / wide243 native evidence" in roadmap
