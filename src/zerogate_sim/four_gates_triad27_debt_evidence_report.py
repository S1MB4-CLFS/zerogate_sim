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

CURRENT_VERSION = "v1.6.20-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
DEBT_PROFILE = "four_gates_debt"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

OUTPUT_FILES = {
    "read": "four_gates_triad27_debt_evidence_read.md",
    "decision": "four_gates_triad27_debt_evidence_decision.json",
    "native_seed_block": "four_gates_triad27_native_seed_block_summary.csv",
    "native_ablation_summary": "four_gates_triad27_native_ablation_summary.csv",
    "native_ablation_gate_summary": "four_gates_triad27_native_ablation_gate_summary.csv",
    "debt_candidate_lanes": "four_gates_triad27_debt_candidate_lanes.csv",
    "state_lanes": "four_gates_triad27_state_lanes.csv",
    "baseline_definitions": "four_gates_triad27_ablation_definitions.csv",
    "audit": "four_gates_triad27_debt_evidence_audit.json",
    "bundle": "four_gates_triad27_debt_evidence_bundle.zip",
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


def _require_native_triad27_matrix_dirs(matrix_dirs: Iterable[Path]) -> list[Path]:
    dirs = [Path(path) for path in matrix_dirs]
    if not dirs:
        raise ValueError("No native triad27 matrix directories supplied.")
    by_gate: dict[str, Path] = {}
    profiles: dict[str, str] = {}
    candidate_profiles: dict[str, str] = {}
    for matrix_dir in dirs:
        ident = read_matrix(matrix_dir)
        if ident.gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if ident.gate in by_gate:
            raise ValueError(f"Duplicate native gate matrix coverage: {ident.gate}")
        by_gate[ident.gate] = matrix_dir
        profiles[ident.gate] = ident.profile
        candidate_profiles[ident.gate] = ident.candidate_profile
    missing = [gate for gate in NATIVE_GATE_NAMES if gate not in by_gate]
    if missing:
        raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))
    non_triad = {gate: profile for gate, profile in profiles.items() if profile != "triad27"}
    if non_triad:
        details = ", ".join(f"{gate}={profile}" for gate, profile in sorted(non_triad.items()))
        raise ValueError("Native debt evidence requires profile `triad27`; found " + details)
    wrong = {
        gate: candidate_profile
        for gate, candidate_profile in candidate_profiles.items()
        if candidate_profile != f"adversary_{gate}"
    }
    if wrong:
        details = ", ".join(f"{gate}={candidate_profile}" for gate, candidate_profile in sorted(wrong.items()))
        raise ValueError("Native adversary matrix directories must use matching candidate profiles; found " + details)
    return [by_gate[gate] for gate in NATIVE_GATE_NAMES]


def _require_debt_matrix_dir(debt_matrix_dir: Path) -> Path:
    debt_matrix_dir = Path(debt_matrix_dir)
    ident = read_matrix(debt_matrix_dir)
    if ident.profile != "triad27":
        raise ValueError(f"Debt evidence requires profile `triad27`; found {ident.profile}")
    if ident.candidate_profile != DEBT_PROFILE:
        raise ValueError(f"Debt evidence requires candidate profile `{DEBT_PROFILE}`; found {ident.candidate_profile}")
    return debt_matrix_dir


def _native_state_lanes(native_row: dict[str, object], debt_counts: dict[str, int]) -> list[dict[str, object]]:
    lanes = [
        (
            "+1 earned-one",
            _int(native_row, "final_earned_one_events") + debt_counts["earned"],
            "native adversary earned-one plus debt-control earned-one",
            "visible" if (_int(native_row, "final_earned_one_events") + debt_counts["earned"]) else "not_visible",
        ),
        (
            "0 latent overcrown",
            _int(native_row, "latent_overcrown_pressure") + debt_counts["latent"],
            "raw pressure held in zero rather than crowned",
            "visible" if (_int(native_row, "latent_overcrown_pressure") + debt_counts["latent"]) else "not_visible",
        ),
        (
            "0 relation debt",
            _int(native_row, "relation_debt_count") + debt_counts["relation_debt"],
            "meaningful but incomplete / under-owned relation held as zero",
            "visible" if (_int(native_row, "relation_debt_count") + debt_counts["relation_debt"]) else "not_visible",
        ),
        (
            "0 return debt",
            _int(native_row, "return_debt_count") + debt_counts["return_debt"],
            "return changed or incomplete and held as zero",
            "visible" if (_int(native_row, "return_debt_count") + debt_counts["return_debt"]) else "not_visible",
        ),
        (
            "-1 false-one pressure",
            _int(native_row, "raw_false_one_pressure"),
            "trap / false-one pressure seen and demoted in native adversaries",
            "visible" if _int(native_row, "raw_false_one_pressure") else "not_visible",
        ),
        (
            "-1 final false-one crowns",
            _int(native_row, "final_false_one_crowns") + debt_counts["final_false_crowns"],
            "final false crown breach count",
            "breach" if (_int(native_row, "final_false_one_crowns") + debt_counts["final_false_crowns"]) else "clean_zero",
        ),
    ]
    return [
        {"lane": lane, "count": count, "meaning": meaning, "lane_status": status}
        for lane, count, meaning, status in lanes
    ]


def _debt_candidate_lanes(debt_matrix_dir: Path) -> tuple[list[dict[str, object]], dict[str, int]]:
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


def _decision(native: dict[str, object], debt_counts: dict[str, int], ablation: dict[str, object]) -> str:
    if _int(native, "final_false_one_crowns") or debt_counts["final_false_crowns"]:
        return "resist_four_gates_triad27_debt_false_crown_breach"
    earned_visible = _int(native, "final_earned_one_events") > 0 and debt_counts["earned"] > 0
    false_pressure_visible = _int(native, "raw_false_one_pressure") > 0 and _int(native, "false_one_demoted_count") >= _int(native, "raw_false_one_pressure")
    relation_debt_visible = debt_counts["relation_debt"] > 0
    return_debt_visible = debt_counts["return_debt"] > 0
    ablations_wounded = int(ablation["wounding_enemy_count"]) >= 3
    if earned_visible and false_pressure_visible and relation_debt_visible and return_debt_visible and ablations_wounded:
        return "expand_four_gates_triad27_debt_evidence"
    if earned_visible and false_pressure_visible and (relation_debt_visible or return_debt_visible) and ablations_wounded:
        return "witness_four_gates_triad27_debt_partial"
    if earned_visible and false_pressure_visible and ablations_wounded:
        return "witness_four_gates_triad27_core_strong_debt_absent"
    return "hold_four_gates_triad27_debt_evidence_incomplete"


def _write_read(
    path: Path,
    *,
    seed_rows: list[dict[str, object]],
    native_summary_rows: list[dict[str, object]],
    debt_rows: list[dict[str, object]],
    debt_counts: dict[str, int],
    state_rows: list[dict[str, object]],
    decision: str,
) -> None:
    native = _summary_by_baseline(native_summary_rows).get("native_final_trinary_witness", {})
    ablation = _ablation_enemy_status(native_summary_rows)
    lines = [
        "# Four Gates Triad27 Debt Evidence",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** first repaired triad27 evidence gate for debt-shaped zero-state candidates",
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
        decision,
        "```",
        "",
        "## Native adversary control",
        "",
        f"- Gates represented: `{len({str(row['gate']) for row in seed_rows})}`",
        f"- Matrix runs represented: `{sum(_int(row, 'total_runs') for row in seed_rows)}`",
        f"- Final earned-one events: `{_int(native, 'final_earned_one_events')}`",
        f"- Raw false-one pressure: `{_int(native, 'raw_false_one_pressure')}`",
        f"- False-one demotions: `{_int(native, 'false_one_demoted_count')}`",
        f"- Final false-one crowns: `{_int(native, 'final_false_one_crowns')}`",
        f"- Wounding ablation enemies: `{ablation['wounding_enemy_count']}`",
        "",
        "## Debt candidate profile",
        "",
        f"- Candidate profile: `{DEBT_PROFILE}`",
        f"- Raw expression pressure: `{debt_counts['raw_pressure']}`",
        f"- Earned-one control events: `{debt_counts['earned']}`",
        f"- Latent overcrown events: `{debt_counts['latent']}`",
        f"- Relation debt events: `{debt_counts['relation_debt']}`",
        f"- Return debt events: `{debt_counts['return_debt']}`",
        f"- Final false-one crowns: `{debt_counts['final_false_crowns']}`",
        "",
        "## Trinary state lanes",
        "",
        "| lane | count | status | meaning |",
        "|---|---:|---|---|",
    ]
    for row in state_rows:
        lines.append(f"| {row['lane']} | {row['count']} | {row['lane_status']} | {row['meaning']} |")
    lines.extend(
        [
            "",
            "## Debt candidate lanes",
            "",
            "| candidate | kind | role | lane | raw | earned | latent | relation debt | return debt | false pressure | final false | band |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in debt_rows:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['assigned_lane']} | "
            f"{row['raw_expression_pressure']} | {row['final_earned_one_count']} | {row['latent_overcrown_pressure']} | "
            f"{row['relation_debt_count']} | {row['return_debt_count']} | {row['raw_false_one_pressure']} | "
            f"{row['final_false_one_crowns']} | {row['final_band']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is the first gate that asks whether zero can hold incomplete-but-meaningful becoming, not only reject false-one pressure. A pass here is still synthetic-field evidence only; it does not prove physics or ontology.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_triad27_debt_evidence_report(
    *,
    output_dir: Path,
    matrix_dirs: Iterable[Path],
    debt_matrix_dir: Path,
) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    native_dirs = _require_native_triad27_matrix_dirs(matrix_dirs)
    debt_dir = _require_debt_matrix_dir(debt_matrix_dir)

    seed_rows = build_seed_block_rows(native_dirs, require_four_gates=True)
    native_gate_rows, native_summary_rows = build_native_ablation_rows(native_dirs, require_four_gates=True)
    debt_rows, debt_counts = _debt_candidate_lanes(debt_dir)
    native = _summary_by_baseline(native_summary_rows).get("native_final_trinary_witness", {})
    state_rows = _native_state_lanes(native, debt_counts)
    ablation = _ablation_enemy_status(native_summary_rows)
    decision = _decision(native, debt_counts, ablation)

    read_path = output_dir / OUTPUT_FILES["read"]
    decision_path = output_dir / OUTPUT_FILES["decision"]
    seed_path = output_dir / OUTPUT_FILES["native_seed_block"]
    native_summary_path = output_dir / OUTPUT_FILES["native_ablation_summary"]
    native_gate_path = output_dir / OUTPUT_FILES["native_ablation_gate_summary"]
    debt_lanes_path = output_dir / OUTPUT_FILES["debt_candidate_lanes"]
    state_lanes_path = output_dir / OUTPUT_FILES["state_lanes"]
    definitions_path = output_dir / OUTPUT_FILES["baseline_definitions"]
    audit_path = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(seed_path, seed_rows)
    write_dict_rows_csv(native_summary_path, native_summary_rows)
    write_dict_rows_csv(native_gate_path, native_gate_rows)
    write_dict_rows_csv(debt_lanes_path, debt_rows)
    write_dict_rows_csv(state_lanes_path, state_rows)
    write_dict_rows_csv(definitions_path, build_definition_rows())
    _write_read(
        read_path,
        seed_rows=seed_rows,
        native_summary_rows=native_summary_rows,
        debt_rows=debt_rows,
        debt_counts=debt_counts,
        state_rows=state_rows,
        decision=decision,
    )
    decision_data = {
        "version": CURRENT_VERSION,
        "global_decision": decision,
        "native_witness_unchanged": NATIVE_WITNESS,
        "weather_rung": "triad27",
        "native_gates": [str(row["gate"]) for row in seed_rows],
        "debt_candidate_profile": DEBT_PROFILE,
        "native_total_matrix_runs": sum(_int(row, "total_runs") for row in seed_rows),
        "debt_matrix_runs": read_matrix(debt_dir).total_runs,
        "native_final_false_one_crowns": _int(native, "final_false_one_crowns"),
        "native_raw_false_one_pressure": _int(native, "raw_false_one_pressure"),
        "native_false_one_demoted_count": _int(native, "false_one_demoted_count"),
        "native_final_earned_one_events": _int(native, "final_earned_one_events"),
        "debt_counts": debt_counts,
        "state_lane_visibility": state_rows,
        "ablation_enemy_status": ablation,
        "boundary": "controlled synthetic-field evidence only; no Zenodo route, no shadow revival, no observed-universe bridge",
    }
    decision_path.write_text(json.dumps(decision_data, indent=2, sort_keys=True), encoding="utf-8")
    audit_path.write_text(
        json.dumps(
            {
                "required_native_gates": list(NATIVE_GATE_NAMES),
                "required_weather_rung": "triad27",
                "required_debt_candidate_profile": DEBT_PROFILE,
                "native_matrix_dirs": [str(path) for path in native_dirs],
                "debt_matrix_dir": str(debt_dir),
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
    bundle_path = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_four_gates_triad27_debt_evidence_bundle",
    )
    return {
        "read": read_path,
        "decision": decision_path,
        "native_seed_block": seed_path,
        "native_ablation_summary": native_summary_path,
        "native_ablation_gate_summary": native_gate_path,
        "debt_candidate_lanes": debt_lanes_path,
        "state_lanes": state_lanes_path,
        "baseline_definitions": definitions_path,
        "audit": audit_path,
        "bundle": bundle_path,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write Four Gates triad27 debt evidence report.")
    parser.add_argument("--matrix-dir", action="append", type=Path, required=True, help="Native triad27 adversary matrix directory. Repeat four times.")
    parser.add_argument("--debt-matrix-dir", type=Path, required=True, help="Triad27 matrix directory using candidate-profile four_gates_debt.")
    parser.add_argument("--out", type=Path, required=True, help="Output report directory.")
    args = parser.parse_args(argv)
    paths = write_four_gates_triad27_debt_evidence_report(
        output_dir=args.out,
        matrix_dirs=args.matrix_dir,
        debt_matrix_dir=args.debt_matrix_dir,
    )
    print("Four Gates triad27 debt evidence report written:")
    for key in ["read", "decision", "bundle"]:
        print(f"- {key}: {paths[key]}")


if __name__ == "__main__":  # pragma: no cover
    main()
