from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from zerogate_sim.comparison_preset import NATIVE_GATE_NAMES
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.seed_block_report import FINAL_OUTPUT_CSV, read_matrix

CURRENT_VERSION = "v1.6.15-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Does the final trinary witness preserve earned-one, hold structured zero pressure, "
    "and demote false-one pressure better than raw, binary, and ablated alternatives?"
)
DEFAULT_GATE_THRESHOLD = 0.55
DEFAULT_STRENGTH_THRESHOLD = 0.40

OUTPUT_FILES = {
    "read": "native_ablation_baselines_read.md",
    "decision": "native_ablation_baselines_decision.json",
    "summary": "native_ablation_baseline_summary.csv",
    "gate_summary": "native_ablation_baseline_gate_summary.csv",
    "definitions": "native_ablation_baseline_definitions.csv",
    "audit": "native_ablation_baselines_audit.json",
    "bundle": "native_ablation_baselines_bundle.zip",
}


@dataclass(frozen=True)
class BaselineDefinition:
    name: str
    family: str
    purpose: str
    expected_failure: str
    evidence_source: str


BASELINE_DEFINITIONS: tuple[BaselineDefinition, ...] = (
    BaselineDefinition(
        "native_final_trinary_witness",
        "control",
        "Current full final trinary witness using the native four-gate expression law and final witness stack.",
        "Should preserve earned-one, hold structured zero pressure, and demote false-one pressure without final false crowns.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "dead_safe_no_crown",
        "degenerate",
        "Refuses every crown; proves why zero false crowns alone is not enough.",
        "Avoids false crowns only by destroying earned-one preservation.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "raw_expression_only",
        "raw",
        "Treats every raw expression pressure event as final +1.",
        "Should overcrown traps and latent/debt pressure when adversarial pressure exists.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "binary_raw_or_fail",
        "binary",
        "Collapses the trinary witness into raw +1 vs generic failure / not +1.",
        "Should erase structured zero and often crown raw pressure too early.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "no_zero_hold",
        "witness_ablation",
        "Removes the active zero-state hold and promotes latent/relation/return debt pressure.",
        "Should convert witness pressure into counterfeit earned-one.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "no_false_one_demotion",
        "witness_ablation",
        "Removes trap / false-one demotion from the final witness.",
        "Should allow raw false-one pressure to become final false crowns.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "no_echo_independence",
        "witness_ablation",
        "Removes relation-debt / echo-independence witness.",
        "Should promote borrowed relation pressure as final earned-one.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "no_return_debt_witness",
        "witness_ablation",
        "Removes return-debt holding where available or proxied.",
        "Should promote collapse-to-zero / shallow return pressure when that pressure is visible.",
        "matrix_final_output_summary.csv",
    ),
    BaselineDefinition(
        "no_relation_gate_raw",
        "gate_ablation",
        "Approximates raw expression with distinction, polarity, and return but without relation as a required gate.",
        "Should inflate expression when relation is the missing constraint.",
        "per-seed gate_scores.csv",
    ),
    BaselineDefinition(
        "no_return_gate_raw",
        "gate_ablation",
        "Approximates raw expression with distinction, polarity, and relation but without observed return as a required gate.",
        "Should inflate expression when return is the missing constraint.",
        "per-seed gate_scores.csv",
    ),
    BaselineDefinition(
        "average_gate_raw",
        "gate_ablation",
        "Uses an average of D/P/R/B instead of weakest-gate C_Z.",
        "Should allow strong gates to average away a missing gate.",
        "per-seed gate_scores.csv",
    ),
)

DEFINITION_BY_NAME = {item.name: item for item in BASELINE_DEFINITIONS}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _float(row: dict[str, object], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _bool(row: dict[str, object], key: str) -> bool:
    value = row.get(key, False)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "+1"}


def _is_final_plus_one(row: dict[str, object]) -> bool:
    return str(row.get("final_trinary_value", "")) == "1" or str(row.get("final_trinary_symbol", "")) == "+1"


def _final_false_one_crowns(rows: Iterable[dict[str, object]]) -> int:
    return sum(
        _int(row, "raw_false_one_pressure")
        for row in rows
        if str(row.get("truth_role", "")) == "trap" and _is_final_plus_one(row)
    )


def _return_debt_proxy(row: dict[str, object]) -> int:
    explicit = _int(row, "return_debt_count")
    if explicit:
        return explicit
    raw = _int(row, "raw_expression_pressure")
    if raw <= 0:
        return 0
    if _int(row, "final_earned_one_count") or _int(row, "raw_false_one_pressure") or _int(row, "latent_overcrown_pressure") or _int(row, "relation_debt_count"):
        return 0
    potential = _float(row, "mean_return_potential")
    observed = _float(row, "mean_return_observed")
    if potential >= 0.55 and observed < 0.55 and potential - observed >= 0.15:
        return raw
    return 0


def _final_row_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    return {
        "final_earned_one_events": sum(_int(row, "final_earned_one_count") for row in rows),
        "raw_expression_pressure": sum(_int(row, "raw_expression_pressure") for row in rows),
        "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
        "false_one_demoted_count": sum(_int(row, "false_one_demoted_count") for row in rows),
        "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
        "latent_overcrown_demoted_count": sum(_int(row, "latent_overcrown_demoted_count") for row in rows),
        "relation_debt_count": sum(_int(row, "relation_debt_count") for row in rows),
        "return_debt_count": sum(_return_debt_proxy(row) for row in rows),
        "final_false_one_crowns": _final_false_one_crowns(rows),
    }


def _matrix_dirs(matrix_dirs: Iterable[Path], *, require_four_gates: bool = True) -> list[tuple[str, Path]]:
    seen: dict[str, Path] = {}
    for matrix_dir in matrix_dirs:
        path = Path(matrix_dir)
        ident = read_matrix(path)
        gate = ident.gate
        if gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if gate in seen:
            raise ValueError(f"Duplicate native gate matrix coverage: {gate}")
        seen[gate] = path
    if require_four_gates:
        missing = [gate for gate in NATIVE_GATE_NAMES if gate not in seen]
        if missing:
            raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))
    ordered = [(gate, seen[gate]) for gate in NATIVE_GATE_NAMES if gate in seen]
    ordered.extend((gate, seen[gate]) for gate in sorted(set(seen) - set(NATIVE_GATE_NAMES)))
    return ordered


def _gate_score_rows(matrix_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(matrix_dir.rglob("gate_scores.csv")):
        rows.extend(_read_csv(path))
    return rows


def _native_counts_from_final_rows(final_rows: list[dict[str, object]]) -> dict[str, int]:
    c = _final_row_counts(final_rows)
    return {
        **c,
        "structured_zero_pressure": c["latent_overcrown_pressure"] + c["relation_debt_count"] + c["return_debt_count"],
        "structured_zero_promoted": 0,
        "earned_lost": 0,
        "pressure_hidden_by_ablation": 0,
        "zero_state_erased": 0,
    }


def _variant_counts_from_final_rows(final_rows: list[dict[str, object]], variant: str) -> dict[str, int]:
    native = _native_counts_from_final_rows(final_rows)
    earned = native["final_earned_one_events"]
    raw = native["raw_expression_pressure"]
    raw_false = native["raw_false_one_pressure"]
    latent = native["latent_overcrown_pressure"]
    relation = native["relation_debt_count"]
    return_debt = native["return_debt_count"]
    zero = latent + relation + return_debt

    if variant == "native_final_trinary_witness":
        return native
    if variant == "dead_safe_no_crown":
        return {
            **native,
            "final_earned_one_events": 0,
            "false_one_demoted_count": raw_false,
            "final_false_one_crowns": 0,
            "earned_lost": earned,
            "structured_zero_promoted": 0,
            "pressure_hidden_by_ablation": earned + zero,
            "zero_state_erased": zero,
        }
    if variant in {"raw_expression_only", "binary_raw_or_fail"}:
        return {
            **native,
            "final_earned_one_events": raw,
            "false_one_demoted_count": 0,
            "latent_overcrown_pressure": 0,
            "relation_debt_count": 0,
            "return_debt_count": 0,
            "final_false_one_crowns": raw_false,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": zero,
            "pressure_hidden_by_ablation": zero + raw_false,
            "zero_state_erased": zero,
        }
    if variant == "no_zero_hold":
        return {
            **native,
            "final_earned_one_events": earned + zero,
            "latent_overcrown_pressure": 0,
            "relation_debt_count": 0,
            "return_debt_count": 0,
            "structured_zero_pressure": 0,
            "structured_zero_promoted": zero,
            "pressure_hidden_by_ablation": zero,
            "zero_state_erased": zero,
        }
    if variant == "no_false_one_demotion":
        return {
            **native,
            "final_earned_one_events": earned + raw_false,
            "false_one_demoted_count": 0,
            "final_false_one_crowns": raw_false,
            "pressure_hidden_by_ablation": raw_false,
        }
    if variant == "no_echo_independence":
        return {
            **native,
            "final_earned_one_events": earned + relation,
            "relation_debt_count": 0,
            "structured_zero_pressure": latent + return_debt,
            "structured_zero_promoted": relation,
            "pressure_hidden_by_ablation": relation,
            "zero_state_erased": relation,
        }
    if variant == "no_return_debt_witness":
        return {
            **native,
            "final_earned_one_events": earned + return_debt,
            "return_debt_count": 0,
            "structured_zero_pressure": latent + relation,
            "structured_zero_promoted": return_debt,
            "pressure_hidden_by_ablation": return_debt,
            "zero_state_erased": return_debt,
        }
    raise ValueError(f"Unsupported final-row baseline variant: {variant}")


def _variant_counts_from_gate_rows(gate_rows: list[dict[str, str]], variant: str) -> dict[str, int]:
    counts = defaultdict(int)
    for row in gate_rows:
        strength = _float(row, "strength")
        d = _float(row, "distinction")
        p = _float(row, "polarity")
        r = _float(row, "relation")
        b = _float(row, "return_observed")
        role = str(row.get("truth_role", ""))
        if variant == "no_relation_gate_raw":
            expr = strength >= DEFAULT_STRENGTH_THRESHOLD and min(d, p, b) >= DEFAULT_GATE_THRESHOLD
        elif variant == "no_return_gate_raw":
            expr = strength >= DEFAULT_STRENGTH_THRESHOLD and min(d, p, r) >= DEFAULT_GATE_THRESHOLD
        elif variant == "average_gate_raw":
            expr = strength >= DEFAULT_STRENGTH_THRESHOLD and ((d + p + r + b) / 4.0) >= DEFAULT_GATE_THRESHOLD
        else:
            expr = _bool(row, "expressed") or str(row.get("trinary_value", "")) == "1"
        if not expr:
            continue
        counts["raw_expression_pressure"] += 1
        if role == "trap":
            counts["raw_false_one_pressure"] += 1
            counts["final_false_one_crowns"] += 1
        elif role == "latent":
            counts["structured_zero_promoted"] += 1
            counts["zero_state_erased"] += 1
            counts["final_earned_one_events"] += 1
        elif role == "expresser":
            counts["final_earned_one_events"] += 1
    counts.setdefault("false_one_demoted_count", 0)
    counts.setdefault("latent_overcrown_pressure", 0)
    counts.setdefault("relation_debt_count", 0)
    counts.setdefault("return_debt_count", 0)
    counts.setdefault("structured_zero_pressure", 0)
    counts.setdefault("earned_lost", 0)
    counts["pressure_hidden_by_ablation"] = counts.get("final_false_one_crowns", 0) + counts.get("zero_state_erased", 0)
    return dict(counts)


def _baseline_status(counts: dict[str, int], *, native_counts: dict[str, int], variant: str) -> str:
    if variant == "native_final_trinary_witness":
        if counts.get("final_false_one_crowns", 0):
            return "native_breach"
        if counts.get("final_earned_one_events", 0) > 0 and (counts.get("structured_zero_pressure", 0) or counts.get("raw_false_one_pressure", 0)):
            return "native_witness_visible_work"
        return "native_quiet"
    if variant == "dead_safe_no_crown":
        return "dead_safe_fails_earned_preservation" if native_counts.get("final_earned_one_events", 0) else "dead_safe_inconclusive"
    if counts.get("final_false_one_crowns", 0):
        return "breach_introduced"
    if counts.get("structured_zero_promoted", 0):
        return "structured_zero_overcrowned"
    if counts.get("earned_lost", 0):
        return "earned_expression_lost"
    if counts.get("pressure_hidden_by_ablation", 0):
        return "witness_pressure_hidden"
    return "no_visible_ablation_wound"


def _summary_status(summary_rows: list[dict[str, object]]) -> str:
    native = next((row for row in summary_rows if row["baseline"] == "native_final_trinary_witness"), None)
    if native is None:
        return "hold_no_native_control"
    if _int(native, "final_false_one_crowns"):
        return "resist_native_breach"
    non_native = [row for row in summary_rows if row["baseline"] != "native_final_trinary_witness"]
    if not non_native:
        return "hold_definitions_only"
    if any(str(row["baseline_status"]) in {"breach_introduced", "structured_zero_overcrowned", "dead_safe_fails_earned_preservation"} for row in non_native):
        return "expand_native_ablation_enemies_expose_witness_work"
    return "witness_ablations_need_stronger_pressure"


def build_definition_rows() -> list[dict[str, object]]:
    return [item.__dict__ for item in BASELINE_DEFINITIONS]


def build_native_ablation_rows(matrix_dirs: Iterable[Path], *, require_four_gates: bool = True) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    gate_dirs = _matrix_dirs(matrix_dirs, require_four_gates=require_four_gates)
    gate_rows_out: list[dict[str, object]] = []
    for gate, matrix_dir in gate_dirs:
        ident = read_matrix(matrix_dir)
        final_rows = _read_csv(matrix_dir / FINAL_OUTPUT_CSV)
        gate_score_rows = _gate_score_rows(matrix_dir)
        native_counts = _variant_counts_from_final_rows(final_rows, "native_final_trinary_witness")
        for definition in BASELINE_DEFINITIONS:
            if definition.name in {"no_relation_gate_raw", "no_return_gate_raw", "average_gate_raw"}:
                counts = _variant_counts_from_gate_rows(gate_score_rows, definition.name)
            else:
                counts = _variant_counts_from_final_rows(final_rows, definition.name)
            status = _baseline_status(counts, native_counts=native_counts, variant=definition.name)
            gate_rows_out.append(
                {
                    "baseline": definition.name,
                    "baseline_family": definition.family,
                    "gate": gate,
                    "matrix_label": ident.matrix_label,
                    "matrix_dir": str(matrix_dir),
                    "candidate_profile": ident.candidate_profile,
                    "seed_range": ident.seed_range,
                    "total_runs": ident.total_runs,
                    "final_earned_one_events": counts.get("final_earned_one_events", 0),
                    "earned_delta_from_native": counts.get("final_earned_one_events", 0) - native_counts.get("final_earned_one_events", 0),
                    "earned_lost": counts.get("earned_lost", 0),
                    "raw_expression_pressure": counts.get("raw_expression_pressure", 0),
                    "raw_false_one_pressure": counts.get("raw_false_one_pressure", 0),
                    "false_one_demoted_count": counts.get("false_one_demoted_count", 0),
                    "latent_overcrown_pressure": counts.get("latent_overcrown_pressure", 0),
                    "relation_debt_count": counts.get("relation_debt_count", 0),
                    "return_debt_count": counts.get("return_debt_count", 0),
                    "structured_zero_pressure": counts.get("structured_zero_pressure", 0),
                    "structured_zero_promoted": counts.get("structured_zero_promoted", 0),
                    "zero_state_erased": counts.get("zero_state_erased", 0),
                    "final_false_one_crowns": counts.get("final_false_one_crowns", 0),
                    "pressure_hidden_by_ablation": counts.get("pressure_hidden_by_ablation", 0),
                    "baseline_status": status,
                }
            )
    summary_rows = build_summary_rows(gate_rows_out)
    return gate_rows_out, summary_rows


def build_summary_rows(gate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_baseline: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in gate_rows:
        by_baseline[str(row["baseline"])].append(row)
    native_rows = by_baseline.get("native_final_trinary_witness", [])
    native_earned = sum(_int(row, "final_earned_one_events") for row in native_rows)
    out: list[dict[str, object]] = []
    for definition in BASELINE_DEFINITIONS:
        rows = by_baseline.get(definition.name, [])
        if not rows:
            continue
        statuses = sorted({str(row["baseline_status"]) for row in rows})
        final_false = sum(_int(row, "final_false_one_crowns") for row in rows)
        zero_promoted = sum(_int(row, "structured_zero_promoted") for row in rows)
        earned_lost = sum(_int(row, "earned_lost") for row in rows)
        earned = sum(_int(row, "final_earned_one_events") for row in rows)
        out.append(
            {
                "baseline": definition.name,
                "baseline_family": definition.family,
                "gates_read": len({str(row["gate"]) for row in rows}),
                "total_matrix_runs": sum(_int(row, "total_runs") for row in rows),
                "final_earned_one_events": earned,
                "earned_delta_from_native": earned - native_earned,
                "earned_lost": earned_lost,
                "raw_expression_pressure": sum(_int(row, "raw_expression_pressure") for row in rows),
                "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
                "false_one_demoted_count": sum(_int(row, "false_one_demoted_count") for row in rows),
                "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
                "relation_debt_count": sum(_int(row, "relation_debt_count") for row in rows),
                "return_debt_count": sum(_int(row, "return_debt_count") for row in rows),
                "structured_zero_pressure": sum(_int(row, "structured_zero_pressure") for row in rows),
                "structured_zero_promoted": zero_promoted,
                "zero_state_erased": sum(_int(row, "zero_state_erased") for row in rows),
                "final_false_one_crowns": final_false,
                "pressure_hidden_by_ablation": sum(_int(row, "pressure_hidden_by_ablation") for row in rows),
                "baseline_status": ";".join(statuses),
            }
        )
    return out


def _write_read(path: Path, *, summary_rows: list[dict[str, object]], definitions_only: bool) -> None:
    decision = _summary_status(summary_rows)
    lines = [
        "# Native Ablation Baselines",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** native baseline enemy definition and optional evaluation",
        "**Boundary:** no Zenodo route, no shadow revival, no observed-universe bridge, no native witness mutation",
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
        "The purpose of this gate is to stop `0 final false-one crowns` from being a lazy victory. A dead-safe witness can crown nothing. A serious final trinary witness must preserve +1, hold structured 0, and resist -1 better than ablations.",
        "",
    ]
    if definitions_only:
        lines.extend([
            "## Evaluation state",
            "",
            "No matrix directories were supplied. This run defines the ablation enemies but does not evaluate evidence yet.",
            "",
        ])
    else:
        lines.extend([
            "## Decision",
            "",
            "```text",
            decision,
            "```",
            "",
            "## Summary",
            "",
            "| baseline | family | gates | earned | Δ earned | lost earned | raw false | false demoted | zero pressure | zero promoted | final false | status |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ])
        for row in summary_rows:
            lines.append(
                f"| {row['baseline']} | {row['baseline_family']} | {row['gates_read']} | {row['final_earned_one_events']} | "
                f"{row['earned_delta_from_native']} | {row['earned_lost']} | {row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | "
                f"{row['structured_zero_pressure']} | {row['structured_zero_promoted']} | {row['final_false_one_crowns']} | {row['baseline_status']} |"
            )
        lines.append("")
    lines.extend([
        "## Baseline definitions",
        "",
        "| baseline | family | purpose | expected failure | source |",
        "|---|---|---|---|---|",
    ])
    for item in BASELINE_DEFINITIONS:
        lines.append(f"| {item.name} | {item.family} | {item.purpose} | {item.expected_failure} | {item.evidence_source} |")
    lines.extend([
        "",
        "## Pass condition for the next evidence gate",
        "",
        "The native witness must beat these baselines on three movements at once: earned-one preservation, structured zero-state accounting, and false-one demotion. If it only avoids false crowns by refusing expression or hiding zero-state pressure, it fails.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_native_ablation_baselines_report(*, output_dir: Path, matrix_dirs: Iterable[Path] | None = None, require_four_gates: bool = True) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    matrix_dirs = list(matrix_dirs or [])
    definitions_only = not matrix_dirs
    definition_rows = build_definition_rows()
    if definitions_only:
        gate_rows: list[dict[str, object]] = []
        summary_rows: list[dict[str, object]] = []
    else:
        gate_rows, summary_rows = build_native_ablation_rows(matrix_dirs, require_four_gates=require_four_gates)

    definitions_csv = output_dir / OUTPUT_FILES["definitions"]
    summary_csv = output_dir / OUTPUT_FILES["summary"]
    gate_csv = output_dir / OUTPUT_FILES["gate_summary"]
    read_md = output_dir / OUTPUT_FILES["read"]
    decision_json = output_dir / OUTPUT_FILES["decision"]
    audit_json = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(definitions_csv, definition_rows)
    write_dict_rows_csv(summary_csv, summary_rows)
    write_dict_rows_csv(gate_csv, gate_rows)
    _write_read(read_md, summary_rows=summary_rows, definitions_only=definitions_only)
    decision = {
        "version": CURRENT_VERSION,
        "global_decision": "hold_baseline_definitions_only" if definitions_only else _summary_status(summary_rows),
        "native_witness_unchanged": NATIVE_WITNESS,
        "matrix_dirs_supplied": len(matrix_dirs),
        "definitions_only": definitions_only,
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "shadow_route_status": "historical_hold",
        "next_gate": "v1.6.16-alpha four-corpus triad27 native evidence",
    }
    decision_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    audit = {
        "output_files": OUTPUT_FILES,
        "baseline_count": len(BASELINE_DEFINITIONS),
        "require_four_gates": require_four_gates,
        "baseline_names": [item.name for item in BASELINE_DEFINITIONS],
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(output_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="zerogate_native_ablation_baselines_bundle")
    return {
        "read": read_md,
        "decision": decision_json,
        "summary": summary_csv,
        "gate_summary": gate_csv,
        "definitions": definitions_csv,
        "audit": audit_json,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build native ablation baseline definitions and optional evaluation from completed four-gate matrix dirs.")
    parser.add_argument("--matrix-dir", type=Path, action="append", default=[], help="Completed matrix directory. Supply four dirs for D/P/R/return evaluation.")
    parser.add_argument("--allow-partial-gates", action="store_true", help="Allow fewer than all four native gate families.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_native_ablation_baselines_report(
        output_dir=args.out,
        matrix_dirs=args.matrix_dir,
        require_four_gates=not args.allow_partial_gates,
    )
    print(f"[native-ablation] wrote {paths['read']}")
    print(f"[native-ablation] bundle {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
