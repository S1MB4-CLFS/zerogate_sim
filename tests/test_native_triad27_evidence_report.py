from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.native_triad27_evidence_report import write_native_triad27_evidence_report

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
    profile: str = "triad27",
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
                "mean_return_potential": 0.9,
                "mean_return_observed": 0.35 if return_debt else 0.9,
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
                "mean_return_potential": 0.8,
                "mean_return_observed": 0.8,
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


def _four_gate_fixture(root: Path, *, profile: str = "triad27") -> list[Path]:
    return [
        _matrix_dir(root, "distinction_triad27", profile=profile, candidate_profile="adversary_distinction", earned=1),
        _matrix_dir(root, "polarity_triad27", profile=profile, candidate_profile="adversary_polarity", earned=2, false_pressure=6, latent=3),
        _matrix_dir(root, "relation_triad27", profile=profile, candidate_profile="adversary_relation", earned=2, false_pressure=4, relation_debt=5),
        _matrix_dir(root, "return_triad27", profile=profile, candidate_profile="adversary_return", earned=2, false_pressure=5, return_debt=7),
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_native_triad27_requires_four_gates(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")[:3]
    with pytest.raises(ValueError, match="return"):
        write_native_triad27_evidence_report(output_dir=tmp_path / "out", matrix_dirs=dirs)


def test_native_triad27_rejects_wrong_weather_rung(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset", profile="deep81")
    with pytest.raises(ValueError, match="triad27"):
        write_native_triad27_evidence_report(output_dir=tmp_path / "out", matrix_dirs=dirs)


def test_native_triad27_writes_expected_outputs_and_decision(tmp_path: Path) -> None:
    dirs = _four_gate_fixture(tmp_path / "preset")
    paths = write_native_triad27_evidence_report(output_dir=tmp_path / "out", matrix_dirs=dirs)
    for key in ["read", "decision", "seed_block", "ablation_summary", "ablation_gate_summary", "state_lanes", "audit", "bundle"]:
        assert paths[key].exists()
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    read = paths["read"].read_text(encoding="utf-8")
    lanes = _read_csv(paths["state_lanes"])

    assert decision["version"] == "v1.6.16-alpha"
    assert decision["weather_rung"] == "triad27"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert decision["loaded_gates"] == ["distinction", "polarity", "relation", "return"]
    assert decision["global_decision"] == "expand_native_triad27_four_gate_ablation_evidence"
    assert "Final earned-one events" in read
    assert {row["lane"] for row in lanes} >= {"+1 earned-one", "0 latent overcrown", "0 relation debt", "0 return debt", "-1 false-one pressure"}


def test_native_triad27_public_version_truth_surfaces() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/native_triad27_evidence.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_16_alpha.md").read_text(encoding="utf-8")
    assert "1.7.0-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.7.0a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.16-alpha" in text
        assert "triad27" in text
        assert "C_Z = min(D, P, R, B)" in text
    assert "v1.6.18-alpha" in roadmap
    assert "deep81 / wide243 native evidence" in roadmap
