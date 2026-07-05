from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.comparison_preset import NATIVE_GATE_NAMES
from zerogate_sim.native_ablation_baselines_report import (
    build_definition_rows,
    build_native_ablation_rows,
)
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.seed_block_report import build_seed_block_rows, read_matrix

CURRENT_VERSION = "v1.6.16-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

OUTPUT_FILES = {
    "read": "native_triad27_evidence_read.md",
    "decision": "native_triad27_evidence_decision.json",
    "seed_block": "native_triad27_seed_block_summary.csv",
    "ablation_summary": "native_triad27_ablation_summary.csv",
    "ablation_gate_summary": "native_triad27_ablation_gate_summary.csv",
    "baseline_definitions": "native_triad27_ablation_definitions.csv",
    "state_lanes": "native_triad27_state_lanes.csv",
    "audit": "native_triad27_evidence_audit.json",
    "bundle": "native_triad27_evidence_bundle.zip",
}


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _require_four_triad27_matrix_dirs(matrix_dirs: Iterable[Path]) -> list[Path]:
    dirs = [Path(path) for path in matrix_dirs]
    if not dirs:
        raise ValueError("No matrix directories supplied for native triad27 evidence.")
    by_gate: dict[str, Path] = {}
    profiles: dict[str, str] = {}
    for matrix_dir in dirs:
        ident = read_matrix(matrix_dir)
        if ident.gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if ident.gate in by_gate:
            raise ValueError(f"Duplicate native gate matrix coverage: {ident.gate}")
        by_gate[ident.gate] = matrix_dir
        profiles[ident.gate] = ident.profile
    missing = [gate for gate in NATIVE_GATE_NAMES if gate not in by_gate]
    if missing:
        raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))
    non_triad = {gate: profile for gate, profile in profiles.items() if profile != "triad27"}
    if non_triad:
        details = ", ".join(f"{gate}={profile}" for gate, profile in sorted(non_triad.items()))
        raise ValueError("Native triad27 evidence requires profile `triad27`; found " + details)
    return [by_gate[gate] for gate in NATIVE_GATE_NAMES]


def _summary_by_baseline(summary_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("baseline", "")): row for row in summary_rows}


def _state_lanes(native_row: dict[str, object]) -> list[dict[str, object]]:
    lanes = [
        (
            "+1 earned-one",
            _int(native_row, "final_earned_one_events"),
            "expression preserved by final witness",
            "visible" if _int(native_row, "final_earned_one_events") else "not_visible_in_this_rung",
        ),
        (
            "0 latent overcrown",
            _int(native_row, "latent_overcrown_pressure"),
            "raw pressure held in zero rather than crowned",
            "visible" if _int(native_row, "latent_overcrown_pressure") else "not_visible_in_this_rung",
        ),
        (
            "0 relation debt",
            _int(native_row, "relation_debt_count"),
            "borrowed / insufficient relation held as structured zero",
            "visible" if _int(native_row, "relation_debt_count") else "not_visible_in_this_rung",
        ),
        (
            "0 return debt",
            _int(native_row, "return_debt_count"),
            "return pressure held when return is not coherent enough to crown",
            "visible" if _int(native_row, "return_debt_count") else "not_visible_in_this_rung",
        ),
        (
            "-1 false-one pressure",
            _int(native_row, "raw_false_one_pressure"),
            "trap / false-one pressure seen and demoted",
            "visible" if _int(native_row, "raw_false_one_pressure") else "not_visible_in_this_rung",
        ),
        (
            "-1 final false-one crowns",
            _int(native_row, "final_false_one_crowns"),
            "final false crown breach count",
            "breach" if _int(native_row, "final_false_one_crowns") else "clean_zero",
        ),
    ]
    return [
        {"lane": lane, "count": count, "meaning": meaning, "lane_status": status}
        for lane, count, meaning, status in lanes
    ]


def _ablation_enemy_status(summary_rows: list[dict[str, object]]) -> dict[str, object]:
    by_baseline = _summary_by_baseline(summary_rows)
    enemy_names = [name for name in by_baseline if name != "native_final_trinary_witness"]
    rows = [by_baseline[name] for name in enemy_names]
    breach_or_wound = [
        str(row.get("baseline", ""))
        for row in rows
        if any(
            needle in str(row.get("baseline_status", ""))
            for needle in [
                "breach_introduced",
                "structured_zero_overcrowned",
                "dead_safe_fails_earned_preservation",
                "earned_expression_lost",
                "witness_pressure_hidden",
            ]
        )
    ]
    return {
        "enemy_count": len(rows),
        "wounding_enemy_count": len(breach_or_wound),
        "wounding_enemies": breach_or_wound,
        "raw_expression_only_wounds": "raw_expression_only" in breach_or_wound,
        "dead_safe_no_crown_wounds": "dead_safe_no_crown" in breach_or_wound,
        "gate_ablation_wounds": any(name in breach_or_wound for name in ["no_relation_gate_raw", "no_return_gate_raw", "average_gate_raw"]),
        "zero_state_ablation_wounds": any(name in breach_or_wound for name in ["no_zero_hold", "no_echo_independence", "no_return_debt_witness"]),
    }


def _decision(summary_rows: list[dict[str, object]], state_rows: list[dict[str, object]]) -> str:
    by_baseline = _summary_by_baseline(summary_rows)
    native = by_baseline.get("native_final_trinary_witness")
    if native is None:
        return "hold_native_triad27_missing_native_control"
    if _int(native, "final_false_one_crowns"):
        return "resist_native_triad27_false_crown_breach"
    earned_visible = _int(native, "final_earned_one_events") > 0
    false_pressure_visible = _int(native, "raw_false_one_pressure") > 0 and _int(native, "false_one_demoted_count") >= _int(native, "raw_false_one_pressure")
    zero_visible = _int(native, "structured_zero_pressure") > 0
    ablation = _ablation_enemy_status(summary_rows)
    if earned_visible and false_pressure_visible and zero_visible and ablation["wounding_enemy_count"] >= 3:
        return "expand_native_triad27_four_gate_ablation_evidence"
    if earned_visible and false_pressure_visible and ablation["wounding_enemy_count"] >= 3:
        return "witness_native_triad27_false_pressure_strong_zero_lanes_partial"
    if earned_visible and ablation["wounding_enemy_count"] >= 3:
        return "witness_native_triad27_earned_preserved_but_pressure_incomplete"
    visible_lanes = sum(1 for row in state_rows if str(row.get("lane_status")) == "visible")
    if visible_lanes < 3:
        return "hold_native_triad27_insufficient_trinary_lane_visibility"
    return "witness_native_triad27_needs_stronger_or_clearer_pressure"


def _write_read(
    path: Path,
    *,
    seed_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    state_rows: list[dict[str, object]],
    decision: str,
) -> None:
    by_baseline = _summary_by_baseline(summary_rows)
    native = by_baseline.get("native_final_trinary_witness", {})
    ablation = _ablation_enemy_status(summary_rows)
    lines = [
        "# Native Four-Corpus Triad27 Evidence",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** controlled synthetic-field native evidence gate",
        "**Boundary:** no Zenodo route, no observed-universe bridge, no shadow revival, no native witness mutation",
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
        decision,
        "```",
        "",
        "## Native control summary",
        "",
        f"- Gates represented: `{len({row['gate'] for row in seed_rows})}`",
        f"- Matrix runs represented: `{sum(_int(row, 'total_runs') for row in seed_rows)}`",
        f"- Final earned-one events: `{_int(native, 'final_earned_one_events')}`",
        f"- Raw false-one pressure: `{_int(native, 'raw_false_one_pressure')}`",
        f"- False-one demotions: `{_int(native, 'false_one_demoted_count')}`",
        f"- Structured zero pressure: `{_int(native, 'structured_zero_pressure')}`",
        f"- Final false-one crowns: `{_int(native, 'final_false_one_crowns')}`",
        "",
        "## Trinary lane visibility",
        "",
        "| lane | count | status | meaning |",
        "|---|---:|---|---|",
    ]
    for row in state_rows:
        lines.append(f"| {row['lane']} | {row['count']} | {row['lane_status']} | {row['meaning']} |")
    lines.extend(
        [
            "",
            "## Four adversarial corpora",
            "",
            "| gate | matrix | runs | earned | raw false | demoted | latent | relation debt | final false | status |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in seed_rows:
        lines.append(
            f"| {row['gate']} | {row['matrix_label']} | {row['total_runs']} | {row['final_earned_one_events']} | "
            f"{row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | {row['latent_overcrown_pressure']} | "
            f"{row['relation_debt_count']} | {row['final_false_one_crowns']} | {row['seed_block_status']} |"
        )
    lines.extend(
        [
            "",
            "## Ablation enemy summary",
            "",
            f"Wounding enemies: `{ablation['wounding_enemy_count']}` of `{ablation['enemy_count']}`",
            "",
            "| baseline | family | earned | lost earned | raw false | zero pressure | zero promoted | final false | status |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in summary_rows:
        lines.append(
            f"| {row['baseline']} | {row['baseline_family']} | {row['final_earned_one_events']} | {row['earned_lost']} | "
            f"{row['raw_false_one_pressure']} | {row['structured_zero_pressure']} | {row['structured_zero_promoted']} | "
            f"{row['final_false_one_crowns']} | {row['baseline_status']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This report supports only controlled synthetic-field native witness evaluation. It does not prove cosmology, physical dimensional genesis, or that the observed universe uses ZeroGateSim. A clean result here only earns permission to continue the native evidence ladder toward deep81 / wide243.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_native_triad27_evidence_report(*, output_dir: Path, matrix_dirs: Iterable[Path]) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    ordered_dirs = _require_four_triad27_matrix_dirs(matrix_dirs)
    seed_rows = build_seed_block_rows(ordered_dirs, require_four_gates=True)
    ablation_gate_rows, ablation_summary_rows = build_native_ablation_rows(ordered_dirs, require_four_gates=True)
    by_baseline = _summary_by_baseline(ablation_summary_rows)
    state_rows = _state_lanes(by_baseline.get("native_final_trinary_witness", {}))
    decision = _decision(ablation_summary_rows, state_rows)

    seed_csv = output_dir / OUTPUT_FILES["seed_block"]
    ablation_summary_csv = output_dir / OUTPUT_FILES["ablation_summary"]
    ablation_gate_csv = output_dir / OUTPUT_FILES["ablation_gate_summary"]
    definitions_csv = output_dir / OUTPUT_FILES["baseline_definitions"]
    lanes_csv = output_dir / OUTPUT_FILES["state_lanes"]
    read_md = output_dir / OUTPUT_FILES["read"]
    decision_json = output_dir / OUTPUT_FILES["decision"]
    audit_json = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(seed_csv, seed_rows)
    write_dict_rows_csv(ablation_summary_csv, ablation_summary_rows)
    write_dict_rows_csv(ablation_gate_csv, ablation_gate_rows)
    write_dict_rows_csv(definitions_csv, build_definition_rows())
    write_dict_rows_csv(lanes_csv, state_rows)
    _write_read(read_md, seed_rows=seed_rows, summary_rows=ablation_summary_rows, state_rows=state_rows, decision=decision)

    ablation = _ablation_enemy_status(ablation_summary_rows)
    decision_payload = {
        "version": CURRENT_VERSION,
        "global_decision": decision,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "weather_rung": "triad27",
        "required_gates": list(NATIVE_GATE_NAMES),
        "loaded_gates": [str(row["gate"]) for row in seed_rows],
        "total_matrix_runs": sum(_int(row, "total_runs") for row in seed_rows),
        "trinary_lane_visibility": state_rows,
        "ablation_enemy_status": ablation,
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "shadow_route_status": "historical_hold",
        "next_gate_if_earned": "v1.6.17-alpha deep81 / wide243 native evidence",
    }
    decision_json.write_text(json.dumps(decision_payload, indent=2), encoding="utf-8")
    audit = {
        "output_files": OUTPUT_FILES,
        "matrix_dirs": [str(path) for path in ordered_dirs],
        "profile_required": "triad27",
        "require_four_gates": True,
        "baseline_rows": len(ablation_summary_rows),
        "gate_rows": len(ablation_gate_rows),
        "state_lane_rows": len(state_rows),
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(output_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="zerogate_native_triad27_evidence_bundle")
    return {
        "read": read_md,
        "decision": decision_json,
        "seed_block": seed_csv,
        "ablation_summary": ablation_summary_csv,
        "ablation_gate_summary": ablation_gate_csv,
        "baseline_definitions": definitions_csv,
        "state_lanes": lanes_csv,
        "audit": audit_json,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate four-corpus triad27 native evidence against ablation baselines.")
    parser.add_argument("--matrix-dir", type=Path, action="append", required=True, help="Completed triad27 matrix directory. Supply distinction, polarity, relation, and return.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_native_triad27_evidence_report(output_dir=args.out, matrix_dirs=args.matrix_dir)
    print(f"[native-triad27] wrote {paths['read']}")
    print(f"[native-triad27] bundle {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
