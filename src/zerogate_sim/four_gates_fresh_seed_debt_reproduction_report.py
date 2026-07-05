from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.22-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
REQUIRED_RUNGS = ("deep81", "wide243")
EVIDENCE_DECISION_FILE = "four_gates_deepwide_debt_evidence_decision.json"
EVIDENCE_RUNG_SUMMARY_FILE = "four_gates_deepwide_debt_rung_summary.csv"
EVIDENCE_STATE_LANES_FILE = "four_gates_deepwide_state_lanes.csv"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

OUTPUT_FILES = {
    "read": "four_gates_fresh_seed_debt_reproduction_read.md",
    "decision": "four_gates_fresh_seed_debt_reproduction_decision.json",
    "rung_comparison": "four_gates_fresh_seed_rung_comparison.csv",
    "state_lane_comparison": "four_gates_fresh_seed_state_lane_comparison.csv",
    "audit": "four_gates_fresh_seed_debt_reproduction_audit.json",
    "bundle": "four_gates_fresh_seed_debt_reproduction_bundle.zip",
}


def _int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "visible"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_evidence_dir(evidence_dir: Path, *, label: str) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir)
    decision = _read_json(evidence_dir / EVIDENCE_DECISION_FILE)
    rung_rows = _read_csv(evidence_dir / EVIDENCE_RUNG_SUMMARY_FILE)
    state_rows = _read_csv(evidence_dir / EVIDENCE_STATE_LANES_FILE)
    loaded = decision.get("loaded_rungs", [])
    missing = [rung for rung in REQUIRED_RUNGS if rung not in loaded]
    if missing:
        raise ValueError(f"{label} evidence is missing required weather rung(s): " + ", ".join(missing))
    native = decision.get("native_witness_unchanged")
    if native != NATIVE_WITNESS:
        raise ValueError(f"{label} evidence native witness mismatch: {native!r}")
    by_rung = {str(row.get("weather_rung", "")): row for row in rung_rows}
    missing_rows = [rung for rung in REQUIRED_RUNGS if rung not in by_rung]
    if missing_rows:
        raise ValueError(f"{label} rung summary is missing required row(s): " + ", ".join(missing_rows))
    return {
        "label": label,
        "dir": evidence_dir,
        "decision": decision,
        "rung_rows": rung_rows,
        "state_rows": state_rows,
        "by_rung": by_rung,
    }


def _rung_quality(row: dict[str, Any]) -> dict[str, bool]:
    raw_false = _int(row, "raw_false_one_pressure")
    demoted = _int(row, "false_one_demoted_count")
    return {
        "earned_visible": _int(row, "final_earned_one_events") > 0,
        "latent_visible": _int(row, "latent_overcrown_pressure") > 0,
        "relation_debt_visible": _boolish(row.get("relation_debt_visible")) or _int(row, "relation_debt_count") > 0,
        "return_debt_visible": _boolish(row.get("return_debt_visible")) or _int(row, "return_debt_count") > 0,
        "false_pressure_visible": raw_false > 0,
        "false_pressure_demoted": demoted >= raw_false and raw_false > 0,
        "final_false_clean": _int(row, "final_false_one_crowns") == 0,
        "ablation_wounds_visible": _int(row, "ablation_wounding_enemy_count") >= 3,
    }


def _quality_passes(quality: dict[str, bool]) -> bool:
    required = [
        "earned_visible",
        "relation_debt_visible",
        "return_debt_visible",
        "false_pressure_visible",
        "false_pressure_demoted",
        "final_false_clean",
        "ablation_wounds_visible",
    ]
    return all(quality[key] for key in required)


def _rung_status(reference_row: dict[str, Any], fresh_row: dict[str, Any]) -> tuple[str, dict[str, bool], dict[str, bool]]:
    ref_quality = _rung_quality(reference_row)
    fresh_quality = _rung_quality(fresh_row)
    if not fresh_quality["final_false_clean"]:
        status = "resist_fresh_seed_false_crown_breach"
    elif _quality_passes(ref_quality) and _quality_passes(fresh_quality):
        status = "expand_fresh_seed_pattern_reproduced"
    elif fresh_quality["earned_visible"] and fresh_quality["false_pressure_demoted"] and fresh_quality["final_false_clean"]:
        status = "witness_fresh_seed_core_reproduced_debt_partial"
    else:
        status = "hold_fresh_seed_pattern_incomplete"
    return status, ref_quality, fresh_quality


def _build_comparison_rows(reference: dict[str, Any], fresh: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rung in REQUIRED_RUNGS:
        ref = reference["by_rung"][rung]
        fr = fresh["by_rung"][rung]
        status, ref_quality, fresh_quality = _rung_status(ref, fr)
        rows.append(
            {
                "weather_rung": rung,
                "reproduction_status": status,
                "reference_decision": ref.get("decision", ""),
                "fresh_decision": fr.get("decision", ""),
                "reference_native_runs": _int(ref, "native_total_matrix_runs"),
                "fresh_native_runs": _int(fr, "native_total_matrix_runs"),
                "reference_debt_runs": _int(ref, "debt_matrix_runs"),
                "fresh_debt_runs": _int(fr, "debt_matrix_runs"),
                "reference_earned": _int(ref, "final_earned_one_events"),
                "fresh_earned": _int(fr, "final_earned_one_events"),
                "reference_latent": _int(ref, "latent_overcrown_pressure"),
                "fresh_latent": _int(fr, "latent_overcrown_pressure"),
                "reference_relation_debt": _int(ref, "relation_debt_count"),
                "fresh_relation_debt": _int(fr, "relation_debt_count"),
                "reference_return_debt": _int(ref, "return_debt_count"),
                "fresh_return_debt": _int(fr, "return_debt_count"),
                "reference_raw_false": _int(ref, "raw_false_one_pressure"),
                "fresh_raw_false": _int(fr, "raw_false_one_pressure"),
                "reference_demoted": _int(ref, "false_one_demoted_count"),
                "fresh_demoted": _int(fr, "false_one_demoted_count"),
                "reference_final_false_crowns": _int(ref, "final_false_one_crowns"),
                "fresh_final_false_crowns": _int(fr, "final_false_one_crowns"),
                "reference_ablation_wounds": _int(ref, "ablation_wounding_enemy_count"),
                "fresh_ablation_wounds": _int(fr, "ablation_wounding_enemy_count"),
                "reference_quality_passed": _quality_passes(ref_quality),
                "fresh_quality_passed": _quality_passes(fresh_quality),
            }
        )
    return rows


def _build_state_lane_rows(reference: dict[str, Any], fresh: dict[str, Any]) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> tuple[str, str]:
        return str(row.get("weather_rung", "")), str(row.get("lane", ""))

    ref_lanes = {key(row): row for row in reference["state_rows"]}
    fresh_lanes = {key(row): row for row in fresh["state_rows"]}
    keys = sorted(set(ref_lanes) | set(fresh_lanes))
    rows: list[dict[str, Any]] = []
    for weather_rung, lane in keys:
        ref = ref_lanes.get((weather_rung, lane), {})
        fr = fresh_lanes.get((weather_rung, lane), {})
        rows.append(
            {
                "weather_rung": weather_rung,
                "lane": lane,
                "reference_count": _int(ref, "count"),
                "fresh_count": _int(fr, "count"),
                "reference_status": ref.get("lane_status", "missing"),
                "fresh_status": fr.get("lane_status", "missing"),
                "lane_reproduced": (_int(fr, "count") > 0) if not lane.endswith("final false-one crowns") else (_int(fr, "count") == 0),
            }
        )
    return rows


def _global_decision(comparison_rows: list[dict[str, Any]]) -> str:
    statuses = [str(row["reproduction_status"]) for row in comparison_rows]
    if any(status.startswith("resist_") for status in statuses):
        return "resist_four_gates_fresh_seed_debt_breach"
    if all(status.startswith("expand_") for status in statuses):
        return "expand_four_gates_fresh_seed_debt_reproduction"
    if all(status.startswith("expand_") or status.startswith("witness_") for status in statuses):
        return "witness_four_gates_fresh_seed_debt_partial"
    return "hold_four_gates_fresh_seed_debt_incomplete"


def _write_read(path: Path, *, comparison_rows: list[dict[str, Any]], global_decision: str, reference_label: str, fresh_label: str) -> None:
    lines = [
        "# Four Gates Fresh-Seed Debt Reproduction",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** fresh-seed reproduction gate for Four Gates debt evidence",
        "**Boundary:** no Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim, no native witness mutation",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Native witness",
        "",
        "```text",
        NATIVE_WITNESS,
        "```",
        "",
        "## Decision",
        "",
        "```text",
        global_decision,
        "```",
        "",
        "## Evidence labels",
        "",
        f"- reference: `{reference_label}`",
        f"- fresh: `{fresh_label}`",
        "",
        "## Rung comparison",
        "",
        "| rung | status | ref earned | fresh earned | ref relation debt | fresh relation debt | ref return debt | fresh return debt | fresh false crowns | fresh ablation wounds |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison_rows:
        lines.append(
            f"| {row['weather_rung']} | {row['reproduction_status']} | {row['reference_earned']} | {row['fresh_earned']} | "
            f"{row['reference_relation_debt']} | {row['fresh_relation_debt']} | {row['reference_return_debt']} | {row['fresh_return_debt']} | "
            f"{row['fresh_final_false_crowns']} | {row['fresh_ablation_wounds']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "A successful fresh-seed result is still controlled synthetic-field software evidence. It does not prove physical dimensional genesis, observed-universe behavior, or a physics bridge. It only says the repaired Four Gates debt pattern reproduced qualitatively on unseen seeds.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_fresh_seed_debt_reproduction_report(
    *,
    output_dir: Path,
    reference_evidence_dir: Path,
    fresh_evidence_dir: Path,
    reference_label: str = "seed-range-0-8",
    fresh_label: str = "fresh-seed-range-9-17",
) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    reference = _load_evidence_dir(reference_evidence_dir, label="reference")
    fresh = _load_evidence_dir(fresh_evidence_dir, label="fresh")
    comparison_rows = _build_comparison_rows(reference, fresh)
    state_rows = _build_state_lane_rows(reference, fresh)
    global_decision = _global_decision(comparison_rows)

    read_path = output_dir / OUTPUT_FILES["read"]
    decision_path = output_dir / OUTPUT_FILES["decision"]
    rung_path = output_dir / OUTPUT_FILES["rung_comparison"]
    lane_path = output_dir / OUTPUT_FILES["state_lane_comparison"]
    audit_path = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(rung_path, comparison_rows)
    write_dict_rows_csv(lane_path, state_rows)
    _write_read(
        read_path,
        comparison_rows=comparison_rows,
        global_decision=global_decision,
        reference_label=reference_label,
        fresh_label=fresh_label,
    )
    decision_payload = {
        "version": CURRENT_VERSION,
        "global_decision": global_decision,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "reference_label": reference_label,
        "fresh_label": fresh_label,
        "required_weather_rungs": list(REQUIRED_RUNGS),
        "reference_global_decision": reference["decision"].get("global_decision"),
        "fresh_global_decision": fresh["decision"].get("global_decision"),
        "rung_decisions": {str(row["weather_rung"]): str(row["reproduction_status"]) for row in comparison_rows},
        "rung_comparison": comparison_rows,
        "state_lane_comparison": state_rows,
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "shadow_route_status": "historical_hold",
        "next_gate_if_earned": "v1.6.23-alpha evidence consolidation / runs hygiene",
    }
    decision_path.write_text(json.dumps(decision_payload, indent=2, sort_keys=True), encoding="utf-8")
    audit_path.write_text(
        json.dumps(
            {
                "output_files": OUTPUT_FILES,
                "reference_evidence_dir": str(Path(reference_evidence_dir)),
                "fresh_evidence_dir": str(Path(fresh_evidence_dir)),
                "required_weather_rungs": list(REQUIRED_RUNGS),
                "required_evidence_files": [EVIDENCE_DECISION_FILE, EVIDENCE_RUNG_SUMMARY_FILE, EVIDENCE_STATE_LANES_FILE],
                "native_witness_mutated": False,
                "forbidden_claims": [
                    "Zenodo correction/upload",
                    "role-blind discovery",
                    "observed-universe bridge",
                    "spacetime metric claim",
                    "physics proof",
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    bundle = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_four_gates_fresh_seed_debt_reproduction_bundle",
    )
    return {
        "read": read_path,
        "decision": decision_path,
        "rung_comparison": rung_path,
        "state_lane_comparison": lane_path,
        "audit": audit_path,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Four Gates fresh-seed debt reproduction report.")
    parser.add_argument("--reference-evidence-dir", type=Path, required=True, help="Reference v1.6.21-style deepwide debt evidence directory.")
    parser.add_argument("--fresh-evidence-dir", type=Path, required=True, help="Fresh-seed v1.6.21-style deepwide debt evidence directory.")
    parser.add_argument("--reference-label", default="seed-range-0-8", help="Human label for the reference evidence.")
    parser.add_argument("--fresh-label", default="fresh-seed-range-9-17", help="Human label for the fresh-seed evidence.")
    parser.add_argument("--out", type=Path, required=True, help="Output report directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_four_gates_fresh_seed_debt_reproduction_report(
        output_dir=args.out,
        reference_evidence_dir=args.reference_evidence_dir,
        fresh_evidence_dir=args.fresh_evidence_dir,
        reference_label=args.reference_label,
        fresh_label=args.fresh_label,
    )
    print("Four Gates fresh-seed debt reproduction report written:")
    for key in ["read", "decision", "bundle"]:
        print(f"- {key}: {paths[key]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
