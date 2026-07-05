from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.comparison_preset import NATIVE_GATE_NAMES
from zerogate_sim.native_ablation_baselines_report import build_definition_rows, build_native_ablation_rows
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.seed_block_report import build_seed_block_rows, read_matrix

CURRENT_VERSION = "v1.6.21-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
DEBT_PROFILE = "four_gates_debt"
REQUIRED_RUNGS = ("deep81", "wide243")
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

OUTPUT_FILES = {
    "read": "four_gates_deepwide_debt_evidence_read.md",
    "decision": "four_gates_deepwide_debt_evidence_decision.json",
    "rung_summary": "four_gates_deepwide_debt_rung_summary.csv",
    "native_seed_block": "four_gates_deepwide_native_seed_block_summary.csv",
    "native_ablation_summary": "four_gates_deepwide_native_ablation_summary.csv",
    "native_ablation_gate_summary": "four_gates_deepwide_native_ablation_gate_summary.csv",
    "debt_candidate_lanes": "four_gates_deepwide_debt_candidate_lanes.csv",
    "state_lanes": "four_gates_deepwide_state_lanes.csv",
    "baseline_definitions": "four_gates_deepwide_ablation_definitions.csv",
    "audit": "four_gates_deepwide_debt_evidence_audit.json",
    "bundle": "four_gates_deepwide_debt_evidence_bundle.zip",
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


def _require_native_matrix_dirs(matrix_dirs: Iterable[Path], *, profile: str) -> list[Path]:
    dirs = [Path(path) for path in matrix_dirs]
    if not dirs:
        raise ValueError(f"No native {profile} matrix directories supplied.")
    by_gate: dict[str, Path] = {}
    profiles: dict[str, str] = {}
    candidate_profiles: dict[str, str] = {}
    for matrix_dir in dirs:
        ident = read_matrix(matrix_dir)
        if ident.gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if ident.gate in by_gate:
            raise ValueError(f"Duplicate native gate matrix coverage for {profile}: {ident.gate}")
        by_gate[ident.gate] = matrix_dir
        profiles[ident.gate] = ident.profile
        candidate_profiles[ident.gate] = ident.candidate_profile
    missing = [gate for gate in NATIVE_GATE_NAMES if gate not in by_gate]
    if missing:
        raise ValueError(f"Missing native gate matrix coverage for {profile}: " + ", ".join(missing))
    wrong_profile = {gate: found for gate, found in profiles.items() if found != profile}
    if wrong_profile:
        details = ", ".join(f"{gate}={found}" for gate, found in sorted(wrong_profile.items()))
        raise ValueError(f"Native debt evidence requires profile `{profile}`; found {details}")
    wrong_candidate = {
        gate: candidate_profile
        for gate, candidate_profile in candidate_profiles.items()
        if candidate_profile != f"adversary_{gate}"
    }
    if wrong_candidate:
        details = ", ".join(f"{gate}={found}" for gate, found in sorted(wrong_candidate.items()))
        raise ValueError(f"Native {profile} adversary matrix directories must use matching candidate profiles; found {details}")
    return [by_gate[gate] for gate in NATIVE_GATE_NAMES]


def _require_debt_matrix_dir(debt_matrix_dir: Path, *, profile: str) -> Path:
    debt_matrix_dir = Path(debt_matrix_dir)
    ident = read_matrix(debt_matrix_dir)
    if ident.profile != profile:
        raise ValueError(f"Debt evidence requires profile `{profile}`; found {ident.profile}")
    if ident.candidate_profile != DEBT_PROFILE:
        raise ValueError(f"Debt evidence requires candidate profile `{DEBT_PROFILE}`; found {ident.candidate_profile}")
    return debt_matrix_dir


def _ablation_enemy_status(summary_rows: list[dict[str, object]]) -> dict[str, object]:
    by_baseline = _summary_by_baseline(summary_rows)
    enemy_names = [name for name in by_baseline if name != "native_final_trinary_witness"]
    wound_needles = [
        "breach_introduced",
        "structured_zero_overcrowned",
        "dead_safe_fails_earned_preservation",
        "earned_expression_lost",
        "witness_pressure_hidden",
    ]
    wounding = [
        str(row.get("baseline", ""))
        for name, row in by_baseline.items()
        if name != "native_final_trinary_witness"
        and any(needle in str(row.get("baseline_status", "")) for needle in wound_needles)
    ]
    return {
        "enemy_count": len(enemy_names),
        "wounding_enemy_count": len(wounding),
        "wounding_enemies": wounding,
        "dead_safe_no_crown_wounds": "dead_safe_no_crown" in wounding,
        "raw_expression_only_wounds": "raw_expression_only" in wounding,
        "gate_ablation_wounds": any(name in wounding for name in ["no_relation_gate_raw", "no_return_gate_raw", "average_gate_raw"]),
        "zero_state_ablation_wounds": any(name in wounding for name in ["no_zero_hold", "no_echo_independence", "no_return_debt_witness"]),
    }


def _debt_candidate_lanes(debt_matrix_dir: Path, *, weather_rung: str) -> tuple[list[dict[str, object]], dict[str, int]]:
    ident = read_matrix(debt_matrix_dir)
    rows = _read_csv(debt_matrix_dir / "matrix_final_output_summary.csv")
    out: list[dict[str, object]] = []
    counts = {
        "earned": 0,
        "latent": 0,
        "relation_debt": 0,
        "return_debt": 0,
        "raw_false": 0,
        "false_demoted": 0,
        "final_false_crowns": 0,
        "raw_pressure": 0,
    }
    for row in rows:
        final_value = str(row.get("final_trinary_value", ""))
        truth_role = str(row.get("truth_role", ""))
        final_false_crown = _int(row, "raw_false_one_pressure") if truth_role == "trap" and final_value == "1" else 0
        lane = "contained"
        if _int(row, "final_earned_one_count"):
            lane = "+1 earned-one"
        elif _int(row, "relation_debt_count"):
            lane = "0 relation debt"
        elif _int(row, "return_debt_count"):
            lane = "0 return debt"
        elif _int(row, "latent_overcrown_pressure"):
            lane = "0 latent overcrown"
        elif _int(row, "raw_false_one_pressure"):
            lane = "-1 false-one demotion"
        counts["earned"] += _int(row, "final_earned_one_count")
        counts["latent"] += _int(row, "latent_overcrown_pressure")
        counts["relation_debt"] += _int(row, "relation_debt_count")
        counts["return_debt"] += _int(row, "return_debt_count")
        counts["raw_false"] += _int(row, "raw_false_one_pressure")
        counts["false_demoted"] += _int(row, "false_one_demoted_count")
        counts["final_false_crowns"] += final_false_crown
        counts["raw_pressure"] += _int(row, "raw_expression_pressure")
        out.append(
            {
                "weather_rung": weather_rung,
                "matrix_label": ident.matrix_label,
                "profile": ident.profile,
                "candidate_profile": ident.candidate_profile,
                "candidate_id": row.get("candidate_id", ""),
                "kind": row.get("kind", ""),
                "truth_role": row.get("truth_role", ""),
                "assigned_lane": lane,
                "raw_expression_pressure": _int(row, "raw_expression_pressure"),
                "final_earned_one_count": _int(row, "final_earned_one_count"),
                "latent_overcrown_pressure": _int(row, "latent_overcrown_pressure"),
                "relation_debt_count": _int(row, "relation_debt_count"),
                "return_debt_count": _int(row, "return_debt_count"),
                "raw_false_one_pressure": _int(row, "raw_false_one_pressure"),
                "false_one_demoted_count": _int(row, "false_one_demoted_count"),
                "final_false_one_crowns": final_false_crown,
                "final_band": row.get("final_band", ""),
                "final_trinary_symbol": row.get("final_trinary_symbol", ""),
            }
        )
    return out, counts


def _state_lanes(native_row: dict[str, object], debt_counts: dict[str, int], *, weather_rung: str) -> list[dict[str, object]]:
    earned = _int(native_row, "final_earned_one_events") + debt_counts["earned"]
    latent = _int(native_row, "latent_overcrown_pressure") + debt_counts["latent"]
    relation_debt = _int(native_row, "relation_debt_count") + debt_counts["relation_debt"]
    return_debt = _int(native_row, "return_debt_count") + debt_counts["return_debt"]
    false_pressure = _int(native_row, "raw_false_one_pressure") + debt_counts["raw_false"]
    final_false = _int(native_row, "final_false_one_crowns") + debt_counts["final_false_crowns"]
    lanes = [
        ("+1 earned-one", earned, "native adversary earned-one plus debt-control earned-one", "visible" if earned else "not_visible"),
        ("0 latent overcrown", latent, "raw pressure held in zero rather than crowned", "visible" if latent else "not_visible"),
        ("0 relation debt", relation_debt, "meaningful but incomplete / under-owned relation held as zero", "visible" if relation_debt else "not_visible"),
        ("0 return debt", return_debt, "return changed or incomplete and held as zero", "visible" if return_debt else "not_visible"),
        ("-1 false-one pressure", false_pressure, "trap / false-one pressure seen and demoted", "visible" if false_pressure else "not_visible"),
        ("-1 final false-one crowns", final_false, "final false crown breach count", "breach" if final_false else "clean_zero"),
    ]
    return [
        {"weather_rung": weather_rung, "lane": lane, "count": count, "meaning": meaning, "lane_status": status}
        for lane, count, meaning, status in lanes
    ]


def _rung_decision(native: dict[str, object], debt_counts: dict[str, int], ablation: dict[str, object], *, weather_rung: str) -> str:
    if _int(native, "final_false_one_crowns") or debt_counts["final_false_crowns"]:
        return f"resist_four_gates_{weather_rung}_debt_false_crown_breach"
    native_false = _int(native, "raw_false_one_pressure")
    native_demoted = _int(native, "false_one_demoted_count")
    debt_false = debt_counts["raw_false"]
    debt_demoted = debt_counts["false_demoted"]
    earned_visible = _int(native, "final_earned_one_events") > 0 and debt_counts["earned"] > 0
    false_pressure_visible = (native_false + debt_false) > 0 and (native_demoted + debt_demoted) >= (native_false + debt_false)
    relation_debt_visible = (_int(native, "relation_debt_count") + debt_counts["relation_debt"]) > 0
    return_debt_visible = (_int(native, "return_debt_count") + debt_counts["return_debt"]) > 0
    ablations_wounded = int(ablation["wounding_enemy_count"]) >= 3
    if earned_visible and false_pressure_visible and relation_debt_visible and return_debt_visible and ablations_wounded:
        return f"expand_four_gates_{weather_rung}_debt_evidence"
    if earned_visible and false_pressure_visible and (relation_debt_visible or return_debt_visible) and ablations_wounded:
        return f"witness_four_gates_{weather_rung}_debt_partial"
    if earned_visible and false_pressure_visible and ablations_wounded:
        return f"witness_four_gates_{weather_rung}_core_strong_debt_absent"
    return f"hold_four_gates_{weather_rung}_debt_evidence_incomplete"


def _build_rung_result(*, weather_rung: str, native_dirs: Iterable[Path], debt_dir: Path) -> dict[str, object]:
    ordered_native_dirs = _require_native_matrix_dirs(native_dirs, profile=weather_rung)
    ordered_debt_dir = _require_debt_matrix_dir(debt_dir, profile=weather_rung)
    seed_rows = build_seed_block_rows(ordered_native_dirs, require_four_gates=True)
    native_gate_rows, native_summary_rows = build_native_ablation_rows(ordered_native_dirs, require_four_gates=True)
    native = _summary_by_baseline(native_summary_rows).get("native_final_trinary_witness", {})
    debt_rows, debt_counts = _debt_candidate_lanes(ordered_debt_dir, weather_rung=weather_rung)
    ablation = _ablation_enemy_status(native_summary_rows)
    state_rows = _state_lanes(native, debt_counts, weather_rung=weather_rung)
    decision = _rung_decision(native, debt_counts, ablation, weather_rung=weather_rung)
    for row in seed_rows:
        row["weather_rung"] = weather_rung
    for row in native_gate_rows:
        row["weather_rung"] = weather_rung
    for row in native_summary_rows:
        row["weather_rung"] = weather_rung
    total_native_runs = sum(_int(row, "total_runs") for row in seed_rows)
    debt_runs = read_matrix(ordered_debt_dir).total_runs
    rung_summary = {
        "weather_rung": weather_rung,
        "decision": decision,
        "native_total_matrix_runs": total_native_runs,
        "debt_matrix_runs": debt_runs,
        "final_earned_one_events": _int(native, "final_earned_one_events") + debt_counts["earned"],
        "native_final_earned_one_events": _int(native, "final_earned_one_events"),
        "debt_earned_one_events": debt_counts["earned"],
        "raw_false_one_pressure": _int(native, "raw_false_one_pressure") + debt_counts["raw_false"],
        "false_one_demoted_count": _int(native, "false_one_demoted_count") + debt_counts["false_demoted"],
        "latent_overcrown_pressure": _int(native, "latent_overcrown_pressure") + debt_counts["latent"],
        "relation_debt_count": _int(native, "relation_debt_count") + debt_counts["relation_debt"],
        "return_debt_count": _int(native, "return_debt_count") + debt_counts["return_debt"],
        "final_false_one_crowns": _int(native, "final_false_one_crowns") + debt_counts["final_false_crowns"],
        "ablation_wounding_enemy_count": ablation["wounding_enemy_count"],
        "relation_debt_visible": (_int(native, "relation_debt_count") + debt_counts["relation_debt"]) > 0,
        "return_debt_visible": (_int(native, "return_debt_count") + debt_counts["return_debt"]) > 0,
    }
    return {
        "weather_rung": weather_rung,
        "native_dirs": ordered_native_dirs,
        "debt_dir": ordered_debt_dir,
        "seed_rows": seed_rows,
        "native_gate_rows": native_gate_rows,
        "native_summary_rows": native_summary_rows,
        "debt_rows": debt_rows,
        "debt_counts": debt_counts,
        "ablation_status": ablation,
        "state_rows": state_rows,
        "rung_summary": rung_summary,
        "decision": decision,
    }


def _global_decision(rung_results: list[dict[str, object]]) -> str:
    if len(rung_results) < len(REQUIRED_RUNGS):
        return "hold_four_gates_deepwide_debt_missing_required_rung"
    decisions = [str(result["decision"]) for result in rung_results]
    if any(decision.startswith("resist_") for decision in decisions):
        return "resist_four_gates_deepwide_debt_breach_or_regression"
    if all(decision.startswith("expand_") for decision in decisions):
        return "expand_four_gates_deepwide_debt_evidence"
    if all(decision.startswith("expand_") or "debt_partial" in decision or "core_strong" in decision for decision in decisions):
        return "witness_four_gates_deepwide_debt_partial"
    return "hold_four_gates_deepwide_debt_evidence_incomplete"


def _write_read(path: Path, *, rung_results: list[dict[str, object]], global_decision: str) -> None:
    lines = [
        "# Four Gates Deep81 / Wide243 Debt Evidence",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** deeper-weather evidence gate for debt-shaped zero-state candidates",
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
        "## Rung summary",
        "",
        "| rung | decision | native runs | debt runs | earned | raw false | demoted | latent | relation debt | return debt | final false | ablation wounds |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in rung_results:
        row = result["rung_summary"]
        lines.append(
            f"| {row['weather_rung']} | {row['decision']} | {row['native_total_matrix_runs']} | {row['debt_matrix_runs']} | "
            f"{row['final_earned_one_events']} | {row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | "
            f"{row['latent_overcrown_pressure']} | {row['relation_debt_count']} | {row['return_debt_count']} | "
            f"{row['final_false_one_crowns']} | {row['ablation_wounding_enemy_count']} |"
        )
    lines.extend(
        [
            "",
            "## Trinary state lanes by rung",
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
            "This evidence asks whether the triad27 debt pattern survives the deeper weather ladder. A clean result is still controlled synthetic-field software evidence only. It does not prove physical dimensional genesis, observed-universe behavior, or a physics bridge.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_deepwide_debt_evidence_report(
    *,
    output_dir: Path,
    deep81_matrix_dirs: Iterable[Path],
    deep81_debt_matrix_dir: Path,
    wide243_matrix_dirs: Iterable[Path],
    wide243_debt_matrix_dir: Path,
) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    rung_results = [
        _build_rung_result(weather_rung="deep81", native_dirs=deep81_matrix_dirs, debt_dir=deep81_debt_matrix_dir),
        _build_rung_result(weather_rung="wide243", native_dirs=wide243_matrix_dirs, debt_dir=wide243_debt_matrix_dir),
    ]
    global_decision = _global_decision(rung_results)

    rung_summary_rows = [result["rung_summary"] for result in rung_results]
    seed_rows: list[dict[str, object]] = []
    native_gate_rows: list[dict[str, object]] = []
    native_summary_rows: list[dict[str, object]] = []
    debt_rows: list[dict[str, object]] = []
    state_rows: list[dict[str, object]] = []
    for result in rung_results:
        seed_rows.extend(result["seed_rows"])
        native_gate_rows.extend(result["native_gate_rows"])
        native_summary_rows.extend(result["native_summary_rows"])
        debt_rows.extend(result["debt_rows"])
        state_rows.extend(result["state_rows"])

    read_path = output_dir / OUTPUT_FILES["read"]
    decision_path = output_dir / OUTPUT_FILES["decision"]
    rung_summary_path = output_dir / OUTPUT_FILES["rung_summary"]
    native_seed_path = output_dir / OUTPUT_FILES["native_seed_block"]
    native_summary_path = output_dir / OUTPUT_FILES["native_ablation_summary"]
    native_gate_path = output_dir / OUTPUT_FILES["native_ablation_gate_summary"]
    debt_lanes_path = output_dir / OUTPUT_FILES["debt_candidate_lanes"]
    state_lanes_path = output_dir / OUTPUT_FILES["state_lanes"]
    definitions_path = output_dir / OUTPUT_FILES["baseline_definitions"]
    audit_path = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(rung_summary_path, rung_summary_rows)
    write_dict_rows_csv(native_seed_path, seed_rows)
    write_dict_rows_csv(native_summary_path, native_summary_rows)
    write_dict_rows_csv(native_gate_path, native_gate_rows)
    write_dict_rows_csv(debt_lanes_path, debt_rows)
    write_dict_rows_csv(state_lanes_path, state_rows)
    write_dict_rows_csv(definitions_path, build_definition_rows())
    _write_read(read_path, rung_results=rung_results, global_decision=global_decision)

    decision_payload = {
        "version": CURRENT_VERSION,
        "global_decision": global_decision,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "required_weather_rungs": list(REQUIRED_RUNGS),
        "loaded_rungs": [str(result["weather_rung"]) for result in rung_results],
        "debt_candidate_profile": DEBT_PROFILE,
        "total_native_matrix_runs": sum(_int(row, "native_total_matrix_runs") for row in rung_summary_rows),
        "total_debt_matrix_runs": sum(_int(row, "debt_matrix_runs") for row in rung_summary_rows),
        "rung_decisions": {str(result["weather_rung"]): str(result["decision"]) for result in rung_results},
        "rung_summaries": rung_summary_rows,
        "debt_counts_by_rung": {str(result["weather_rung"]): result["debt_counts"] for result in rung_results},
        "state_lane_visibility": state_rows,
        "ablation_enemy_status": {str(result["weather_rung"]): result["ablation_status"] for result in rung_results},
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "shadow_route_status": "historical_hold",
        "next_gate_if_earned": "v1.6.22-alpha fresh-seed debt reproduction",
    }
    decision_path.write_text(json.dumps(decision_payload, indent=2, sort_keys=True), encoding="utf-8")
    audit_path.write_text(
        json.dumps(
            {
                "output_files": OUTPUT_FILES,
                "required_weather_rungs": list(REQUIRED_RUNGS),
                "required_native_gates": list(NATIVE_GATE_NAMES),
                "required_debt_candidate_profile": DEBT_PROFILE,
                "require_four_gates_per_rung": True,
                "deep81_native_matrix_dirs": [str(path) for path in _require_native_matrix_dirs(deep81_matrix_dirs, profile="deep81")],
                "wide243_native_matrix_dirs": [str(path) for path in _require_native_matrix_dirs(wide243_matrix_dirs, profile="wide243")],
                "deep81_debt_matrix_dir": str(_require_debt_matrix_dir(deep81_debt_matrix_dir, profile="deep81")),
                "wide243_debt_matrix_dir": str(_require_debt_matrix_dir(wide243_debt_matrix_dir, profile="wide243")),
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
        bundle_kind="zerogate_four_gates_deepwide_debt_evidence_bundle",
    )
    return {
        "read": read_path,
        "decision": decision_path,
        "rung_summary": rung_summary_path,
        "native_seed_block": native_seed_path,
        "native_ablation_summary": native_summary_path,
        "native_ablation_gate_summary": native_gate_path,
        "debt_candidate_lanes": debt_lanes_path,
        "state_lanes": state_lanes_path,
        "baseline_definitions": definitions_path,
        "audit": audit_path,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Four Gates deep81 / wide243 debt evidence report.")
    parser.add_argument("--deep81-matrix-dir", action="append", type=Path, default=[], help="Native deep81 adversary matrix directory. Repeat four times.")
    parser.add_argument("--deep81-debt-matrix-dir", type=Path, required=True, help="deep81 matrix directory using candidate-profile four_gates_debt.")
    parser.add_argument("--wide243-matrix-dir", action="append", type=Path, default=[], help="Native wide243 adversary matrix directory. Repeat four times.")
    parser.add_argument("--wide243-debt-matrix-dir", type=Path, required=True, help="wide243 matrix directory using candidate-profile four_gates_debt.")
    parser.add_argument("--out", type=Path, required=True, help="Output report directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_four_gates_deepwide_debt_evidence_report(
        output_dir=args.out,
        deep81_matrix_dirs=args.deep81_matrix_dir,
        deep81_debt_matrix_dir=args.deep81_debt_matrix_dir,
        wide243_matrix_dirs=args.wide243_matrix_dir,
        wide243_debt_matrix_dir=args.wide243_debt_matrix_dir,
    )
    print("Four Gates deep81 / wide243 debt evidence report written:")
    for key in ["read", "decision", "bundle"]:
        print(f"- {key}: {paths[key]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
