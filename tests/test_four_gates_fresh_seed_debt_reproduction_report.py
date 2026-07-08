from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.four_gates_fresh_seed_debt_reproduction_report import (
    write_four_gates_fresh_seed_debt_reproduction_report,
)

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


def _evidence_dir(
    root: Path,
    *,
    decision: str = "expand_four_gates_deepwide_debt_evidence",
    final_false: int = 0,
    relation_debt: int = 30,
    return_debt: int = 63,
    earned: int = 900,
    raw_false: int = 400,
    demoted: int = 400,
    ablation_wounds: int = 8,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rung_rows = []
    state_rows = []
    for rung in ["deep81", "wide243"]:
        factor = 3 if rung == "wide243" else 1
        row = {
            "weather_rung": rung,
            "decision": f"expand_four_gates_{rung}_debt_evidence" if final_false == 0 else f"resist_four_gates_{rung}_debt_false_crown_breach",
            "native_total_matrix_runs": 2916 * factor,
            "debt_matrix_runs": 729 * factor,
            "final_earned_one_events": earned * factor,
            "native_final_earned_one_events": (earned - 100) * factor,
            "debt_earned_one_events": 100 * factor,
            "raw_false_one_pressure": raw_false * factor,
            "false_one_demoted_count": demoted * factor,
            "latent_overcrown_pressure": 9 * factor,
            "relation_debt_count": relation_debt * factor,
            "return_debt_count": return_debt * factor,
            "final_false_one_crowns": final_false,
            "ablation_wounding_enemy_count": ablation_wounds,
            "relation_debt_visible": relation_debt > 0,
            "return_debt_visible": return_debt > 0,
        }
        rung_rows.append(row)
        state_rows.extend(
            [
                {"weather_rung": rung, "lane": "+1 earned-one", "count": row["final_earned_one_events"], "meaning": "earned", "lane_status": "visible"},
                {"weather_rung": rung, "lane": "0 latent overcrown", "count": row["latent_overcrown_pressure"], "meaning": "latent", "lane_status": "visible"},
                {"weather_rung": rung, "lane": "0 relation debt", "count": row["relation_debt_count"], "meaning": "relation", "lane_status": "visible" if relation_debt else "not_visible"},
                {"weather_rung": rung, "lane": "0 return debt", "count": row["return_debt_count"], "meaning": "return", "lane_status": "visible" if return_debt else "not_visible"},
                {"weather_rung": rung, "lane": "-1 false-one pressure", "count": row["raw_false_one_pressure"], "meaning": "false", "lane_status": "visible"},
                {"weather_rung": rung, "lane": "-1 final false-one crowns", "count": row["final_false_one_crowns"], "meaning": "breach", "lane_status": "clean_zero" if final_false == 0 else "breach"},
            ]
        )
    (root / "four_gates_deepwide_debt_evidence_decision.json").write_text(
        json.dumps(
            {
                "version": "v1.6.21-alpha",
                "global_decision": decision if final_false == 0 else "resist_four_gates_deepwide_debt_breach_or_regression",
                "native_witness_unchanged": "C_Z = min(D, P, R, B)",
                "loaded_rungs": ["deep81", "wide243"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_csv(root / "four_gates_deepwide_debt_rung_summary.csv", rung_rows)
    _write_csv(root / "four_gates_deepwide_state_lanes.csv", state_rows)
    return root


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_fresh_seed_reproduction_expands_when_pattern_reproduces(tmp_path: Path) -> None:
    reference = _evidence_dir(tmp_path / "reference")
    fresh = _evidence_dir(tmp_path / "fresh", earned=920, raw_false=410, demoted=410, relation_debt=34, return_debt=59)
    paths = write_four_gates_fresh_seed_debt_reproduction_report(
        output_dir=tmp_path / "out",
        reference_evidence_dir=reference,
        fresh_evidence_dir=fresh,
    )
    for key in ["read", "decision", "rung_comparison", "state_lane_comparison", "audit", "bundle"]:
        assert paths[key].exists()
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    rows = _read_csv(paths["rung_comparison"])
    assert decision["version"] == "v1.6.22-alpha"
    assert decision["global_decision"] == "expand_four_gates_fresh_seed_debt_reproduction"
    assert decision["native_witness_unchanged"] == "C_Z = min(D, P, R, B)"
    assert {row["reproduction_status"] for row in rows} == {"expand_fresh_seed_pattern_reproduced"}


def test_fresh_seed_reproduction_resists_false_crown_breach(tmp_path: Path) -> None:
    reference = _evidence_dir(tmp_path / "reference")
    fresh = _evidence_dir(tmp_path / "fresh", final_false=2)
    paths = write_four_gates_fresh_seed_debt_reproduction_report(
        output_dir=tmp_path / "out",
        reference_evidence_dir=reference,
        fresh_evidence_dir=fresh,
    )
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] == "resist_four_gates_fresh_seed_debt_breach"


def test_fresh_seed_reproduction_holds_when_debt_lanes_missing(tmp_path: Path) -> None:
    reference = _evidence_dir(tmp_path / "reference")
    fresh = _evidence_dir(tmp_path / "fresh", relation_debt=0, return_debt=0)
    paths = write_four_gates_fresh_seed_debt_reproduction_report(
        output_dir=tmp_path / "out",
        reference_evidence_dir=reference,
        fresh_evidence_dir=fresh,
    )
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["global_decision"] == "witness_four_gates_fresh_seed_debt_partial"


def test_fresh_seed_reproduction_rejects_missing_required_rung(tmp_path: Path) -> None:
    reference = _evidence_dir(tmp_path / "reference")
    fresh = _evidence_dir(tmp_path / "fresh")
    decision_path = fresh / "four_gates_deepwide_debt_evidence_decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["loaded_rungs"] = ["deep81"]
    decision_path.write_text(json.dumps(decision), encoding="utf-8")
    with pytest.raises(ValueError, match="wide243"):
        write_four_gates_fresh_seed_debt_reproduction_report(
            output_dir=tmp_path / "out",
            reference_evidence_dir=reference,
            fresh_evidence_dir=fresh,
        )


def test_fresh_seed_reproduction_public_surfaces_are_current() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    version_truth = (ROOT / "docs/version_truth.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs/four_gates_fresh_seed_debt_reproduction.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release_notes/v1_6_22_alpha.md").read_text(encoding="utf-8")
    assert "1.7.10-alpha" in (ROOT / "src/zerogate_sim/__init__.py").read_text(encoding="utf-8")
    assert 'version = "1.7.10a0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for text in [readme, roadmap, version_truth, doc, release]:
        assert "v1.6.22-alpha" in text
        assert "fresh-seed debt reproduction" in text
        assert "C_Z = min(D, P, R, B)" in text
        assert "observed-universe bridge" in text
    assert "v1.6.25-alpha" in roadmap
    assert "Evidence consolidation" in roadmap
