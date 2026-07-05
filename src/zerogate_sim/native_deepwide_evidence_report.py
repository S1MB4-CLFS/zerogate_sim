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

CURRENT_VERSION = "v1.6.17-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

REQUIRED_RUNGS = ("deep81", "wide243")

OUTPUT_FILES = {
    "read": "native_deepwide_evidence_read.md",
    "decision": "native_deepwide_evidence_decision.json",
    "rung_summary": "native_deepwide_rung_summary.csv",
    "seed_block": "native_deepwide_seed_block_summary.csv",
    "ablation_summary": "native_deepwide_ablation_summary.csv",
    "ablation_gate_summary": "native_deepwide_ablation_gate_summary.csv",
    "baseline_definitions": "native_deepwide_ablation_definitions.csv",
    "state_lanes": "native_deepwide_state_lanes.csv",
    "audit": "native_deepwide_evidence_audit.json",
    "bundle": "native_deepwide_evidence_bundle.zip",
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


def _summary_by_baseline(summary_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("baseline", "")): row for row in summary_rows}


def _require_four_profile_matrix_dirs(matrix_dirs: Iterable[Path], *, profile: str) -> list[Path]:
    dirs = [Path(path) for path in matrix_dirs]
    if not dirs:
        raise ValueError(f"No matrix directories supplied for native {profile} evidence.")
    by_gate: dict[str, Path] = {}
    profiles: dict[str, str] = {}
    for matrix_dir in dirs:
        ident = read_matrix(matrix_dir)
        if ident.gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if ident.gate in by_gate:
            raise ValueError(f"Duplicate native gate matrix coverage for {profile}: {ident.gate}")
        by_gate[ident.gate] = matrix_dir
        profiles[ident.gate] = ident.profile
    missing = [gate for gate in NATIVE_GATE_NAMES if gate not in by_gate]
    if missing:
        raise ValueError(f"Missing native gate matrix coverage for {profile}: " + ", ".join(missing))
    wrong_profile = {gate: found for gate, found in profiles.items() if found != profile}
    if wrong_profile:
        details = ", ".join(f"{gate}={found}" for gate, found in sorted(wrong_profile.items()))
        raise ValueError(f"Native {profile} evidence requires profile `{profile}`; found {details}")
    return [by_gate[gate] for gate in NATIVE_GATE_NAMES]


def _state_lanes(native_row: dict[str, object], *, weather_rung: str) -> list[dict[str, object]]:
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
            "borrowed or insufficient relation held as structured zero",
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
        {
            "weather_rung": weather_rung,
            "lane": lane,
            "count": count,
            "meaning": meaning,
            "lane_status": status,
        }
        for lane, count, meaning, status in lanes
    ]


def _ablation_enemy_status(summary_rows: list[dict[str, object]]) -> dict[str, object]:
    by_baseline = _summary_by_baseline(summary_rows)
    enemy_names = [name for name in by_baseline if name != "native_final_trinary_witness"]
    rows = [by_baseline[name] for name in enemy_names]
    wound_needles = [
        "breach_introduced",
        "structured_zero_overcrowned",
        "dead_safe_fails_earned_preservation",
        "earned_expression_lost",
        "witness_pressure_hidden",
    ]
    wounding = [
        str(row.get("baseline", ""))
        for row in rows
        if any(needle in str(row.get("baseline_status", "")) for needle in wound_needles)
    ]
    return {
        "enemy_count": len(rows),
        "wounding_enemy_count": len(wounding),
        "wounding_enemies": wounding,
        "raw_expression_only_wounds": "raw_expression_only" in wounding,
        "dead_safe_no_crown_wounds": "dead_safe_no_crown" in wounding,
        "gate_ablation_wounds": any(name in wounding for name in ["no_relation_gate_raw", "no_return_gate_raw", "average_gate_raw"]),
        "zero_state_ablation_wounds": any(name in wounding for name in ["no_zero_hold", "no_echo_independence", "no_return_debt_witness"]),
    }


def _rung_decision(weather_rung: str, summary_rows: list[dict[str, object]]) -> str:
    by_baseline = _summary_by_baseline(summary_rows)
    native = by_baseline.get("native_final_trinary_witness")
    if native is None:
        return f"hold_native_{weather_rung}_missing_native_control"
    if _int(native, "final_false_one_crowns"):
        return f"resist_native_{weather_rung}_false_crown_breach"
    earned_visible = _int(native, "final_earned_one_events") > 0
    false_pressure_visible = _int(native, "raw_false_one_pressure") > 0 and _int(native, "false_one_demoted_count") >= _int(native, "raw_false_one_pressure")
    latent_visible = _int(native, "latent_overcrown_pressure") > 0
    relation_debt_visible = _int(native, "relation_debt_count") > 0
    return_debt_visible = _int(native, "return_debt_count") > 0
    structured_zero_visible = _int(native, "structured_zero_pressure") > 0
    ablation = _ablation_enemy_status(summary_rows)
    ablations_wounded = ablation["wounding_enemy_count"] >= 3
    if earned_visible and false_pressure_visible and relation_debt_visible and return_debt_visible and ablations_wounded:
        return f"expand_native_{weather_rung}_debt_lanes_visible"
    if earned_visible and false_pressure_visible and structured_zero_visible and ablations_wounded:
        return f"witness_native_{weather_rung}_zero_visible_debt_lanes_partial"
    if earned_visible and false_pressure_visible and ablations_wounded:
        return f"witness_native_{weather_rung}_false_pressure_strong_debt_lanes_absent"
    if earned_visible and ablations_wounded:
        return f"witness_native_{weather_rung}_earned_preserved_but_pressure_incomplete"
    return f"hold_native_{weather_rung}_needs_stronger_or_clearer_pressure"


def _build_rung_result(weather_rung: str, matrix_dirs: Iterable[Path]) -> dict[str, object]:
    ordered_dirs = _require_four_profile_matrix_dirs(matrix_dirs, profile=weather_rung)
    seed_rows = build_seed_block_rows(ordered_dirs, require_four_gates=True)
    ablation_gate_rows, ablation_summary_rows = build_native_ablation_rows(ordered_dirs, require_four_gates=True)
    by_baseline = _summary_by_baseline(ablation_summary_rows)
    native = by_baseline.get("native_final_trinary_witness", {})
    state_rows = _state_lanes(native, weather_rung=weather_rung)
    decision = _rung_decision(weather_rung, ablation_summary_rows)
    for row in seed_rows:
        row["weather_rung"] = weather_rung
    for row in ablation_gate_rows:
        row["weather_rung"] = weather_rung
    for row in ablation_summary_rows:
        row["weather_rung"] = weather_rung
    debt_status = {
        "relation_debt_visible": _int(native, "relation_debt_count") > 0,
        "return_debt_visible": _int(native, "return_debt_count") > 0,
        "latent_overcrown_visible": _int(native, "latent_overcrown_pressure") > 0,
        "structured_zero_visible": _int(native, "structured_zero_pressure") > 0,
    }
    rung_summary = {
        "weather_rung": weather_rung,
        "decision": decision,
        "gates_represented": len({str(row["gate"]) for row in seed_rows}),
        "total_matrix_runs": sum(_int(row, "total_runs") for row in seed_rows),
        "final_earned_one_events": _int(native, "final_earned_one_events"),
        "raw_expression_pressure": _int(native, "raw_expression_pressure"),
        "raw_false_one_pressure": _int(native, "raw_false_one_pressure"),
        "false_one_demoted_count": _int(native, "false_one_demoted_count"),
        "latent_overcrown_pressure": _int(native, "latent_overcrown_pressure"),
        "relation_debt_count": _int(native, "relation_debt_count"),
        "return_debt_count": _int(native, "return_debt_count"),
        "structured_zero_pressure": _int(native, "structured_zero_pressure"),
        "final_false_one_crowns": _int(native, "final_false_one_crowns"),
        "ablation_wounding_enemy_count": _ablation_enemy_status(ablation_summary_rows)["wounding_enemy_count"],
        "relation_debt_visible": debt_status["relation_debt_visible"],
        "return_debt_visible": debt_status["return_debt_visible"],
        "structured_zero_visible": debt_status["structured_zero_visible"],
    }
    return {
        "weather_rung": weather_rung,
        "ordered_dirs": ordered_dirs,
        "seed_rows": seed_rows,
        "ablation_gate_rows": ablation_gate_rows,
        "ablation_summary_rows": ablation_summary_rows,
        "state_rows": state_rows,
        "rung_summary": rung_summary,
        "decision": decision,
        "debt_status": debt_status,
        "ablation_status": _ablation_enemy_status(ablation_summary_rows),
    }


def _global_decision(rung_results: list[dict[str, object]]) -> str:
    if len(rung_results) < len(REQUIRED_RUNGS):
        return "hold_native_deepwide_missing_required_rung"
    decisions = [str(result["decision"]) for result in rung_results]
    if any(decision.startswith("resist_") for decision in decisions):
        return "resist_native_deepwide_breach_or_regression"
    if all(decision.startswith("expand_") for decision in decisions):
        return "expand_native_deepwide_debt_lanes_visible"
    if all("false_pressure_strong" in decision or "zero_visible" in decision or decision.startswith("expand_") for decision in decisions):
        return "witness_native_deepwide_core_strong_debt_lanes_partial"
    return "witness_native_deepwide_needs_clearer_or_stronger_debt_pressure"


def _write_read(path: Path, *, rung_results: list[dict[str, object]], global_decision: str) -> None:
    lines = [
        "# Native Deep81 / Wide243 Evidence",
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
        global_decision,
        "```",
        "",
        "## Debt-lane requirement",
        "",
        "This gate does not treat bigger weather as automatic proof. `deep81` and `wide243` must preserve earned-one, demote false-one pressure, wound ablations, and explicitly report whether relation debt and return debt become visible. If debt lanes remain absent, the core zero-state debt grammar remains partial.",
        "",
        "## Rung summary",
        "",
        "| rung | decision | runs | earned | raw false | demoted | latent | relation debt | return debt | final false | ablation wounds |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in rung_results:
        row = result["rung_summary"]
        lines.append(
            f"| {row['weather_rung']} | {row['decision']} | {row['total_matrix_runs']} | {row['final_earned_one_events']} | "
            f"{row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | {row['latent_overcrown_pressure']} | "
            f"{row['relation_debt_count']} | {row['return_debt_count']} | {row['final_false_one_crowns']} | {row['ablation_wounding_enemy_count']} |"
        )
    lines.extend(
        [
            "",
            "## Trinary lane visibility by rung",
            "",
            "| rung | lane | count | status | meaning |",
            "|---|---|---:|---|---|",
        ]
    )
    for result in rung_results:
        for row in result["state_rows"]:
            lines.append(f"| {row['weather_rung']} | {row['lane']} | {row['count']} | {row['lane_status']} | {row['meaning']} |")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "A clean result here is still controlled synthetic-field software evidence. It does not prove physical dimensional genesis or observed-universe use. It only earns permission to continue toward fresh-seed reproduction and a correction package if the debt lanes and ablation comparisons are coherent.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_native_deepwide_evidence_report(*, output_dir: Path, deep81_matrix_dirs: Iterable[Path], wide243_matrix_dirs: Iterable[Path]) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    deep81_dirs = list(deep81_matrix_dirs)
    wide243_dirs = list(wide243_matrix_dirs)
    if not deep81_dirs:
        raise ValueError("Missing required deep81 matrix directories.")
    if not wide243_dirs:
        raise ValueError("Missing required wide243 matrix directories.")
    rung_results = [
        _build_rung_result("deep81", deep81_dirs),
        _build_rung_result("wide243", wide243_dirs),
    ]
    global_decision = _global_decision(rung_results)

    rung_summary_rows = [result["rung_summary"] for result in rung_results]
    seed_rows: list[dict[str, object]] = []
    ablation_gate_rows: list[dict[str, object]] = []
    ablation_summary_rows: list[dict[str, object]] = []
    state_rows: list[dict[str, object]] = []
    for result in rung_results:
        seed_rows.extend(result["seed_rows"])
        ablation_gate_rows.extend(result["ablation_gate_rows"])
        ablation_summary_rows.extend(result["ablation_summary_rows"])
        state_rows.extend(result["state_rows"])

    read_md = output_dir / OUTPUT_FILES["read"]
    decision_json = output_dir / OUTPUT_FILES["decision"]
    rung_summary_csv = output_dir / OUTPUT_FILES["rung_summary"]
    seed_csv = output_dir / OUTPUT_FILES["seed_block"]
    ablation_summary_csv = output_dir / OUTPUT_FILES["ablation_summary"]
    ablation_gate_csv = output_dir / OUTPUT_FILES["ablation_gate_summary"]
    definitions_csv = output_dir / OUTPUT_FILES["baseline_definitions"]
    lanes_csv = output_dir / OUTPUT_FILES["state_lanes"]
    audit_json = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(rung_summary_csv, rung_summary_rows)
    write_dict_rows_csv(seed_csv, seed_rows)
    write_dict_rows_csv(ablation_summary_csv, ablation_summary_rows)
    write_dict_rows_csv(ablation_gate_csv, ablation_gate_rows)
    write_dict_rows_csv(definitions_csv, build_definition_rows())
    write_dict_rows_csv(lanes_csv, state_rows)
    _write_read(read_md, rung_results=rung_results, global_decision=global_decision)

    decision_payload = {
        "version": CURRENT_VERSION,
        "global_decision": global_decision,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "required_weather_rungs": list(REQUIRED_RUNGS),
        "loaded_rungs": [str(result["weather_rung"]) for result in rung_results],
        "total_matrix_runs": sum(_int(row, "total_matrix_runs") for row in rung_summary_rows),
        "rung_decisions": {str(result["weather_rung"]): str(result["decision"]) for result in rung_results},
        "rung_summaries": rung_summary_rows,
        "debt_lane_requirement": {
            str(result["weather_rung"]): result["debt_status"] for result in rung_results
        },
        "ablation_enemy_status": {
            str(result["weather_rung"]): result["ablation_status"] for result in rung_results
        },
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "shadow_route_status": "historical_hold",
        "next_gate_if_earned": "v1.6.18-alpha fresh-seed reproduction and correction package planning",
    }
    decision_json.write_text(json.dumps(decision_payload, indent=2), encoding="utf-8")
    audit = {
        "output_files": OUTPUT_FILES,
        "required_weather_rungs": list(REQUIRED_RUNGS),
        "require_four_gates_per_rung": True,
        "deep81_matrix_dirs": [str(path) for path in deep81_dirs],
        "wide243_matrix_dirs": [str(path) for path in wide243_dirs],
        "seed_rows": len(seed_rows),
        "ablation_summary_rows": len(ablation_summary_rows),
        "ablation_gate_rows": len(ablation_gate_rows),
        "state_lane_rows": len(state_rows),
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(output_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="zerogate_native_deepwide_evidence_bundle")
    return {
        "read": read_md,
        "decision": decision_json,
        "rung_summary": rung_summary_csv,
        "seed_block": seed_csv,
        "ablation_summary": ablation_summary_csv,
        "ablation_gate_summary": ablation_gate_csv,
        "baseline_definitions": definitions_csv,
        "state_lanes": lanes_csv,
        "audit": audit_json,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate deep81 and wide243 native evidence against ablation baselines with debt-lane visibility checks.")
    parser.add_argument("--deep81-matrix-dir", type=Path, action="append", default=[], help="Completed deep81 matrix directory. Supply distinction, polarity, relation, and return.")
    parser.add_argument("--wide243-matrix-dir", type=Path, action="append", default=[], help="Completed wide243 matrix directory. Supply distinction, polarity, relation, and return.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_native_deepwide_evidence_report(output_dir=args.out, deep81_matrix_dirs=args.deep81_matrix_dir, wide243_matrix_dirs=args.wide243_matrix_dir)
    print(f"[native-deepwide] wrote {paths['read']}")
    print(f"[native-deepwide] bundle {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
