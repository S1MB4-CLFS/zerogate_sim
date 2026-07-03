from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from zerogate_sim.comparison_preset import NATIVE_GATE_NAMES
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.seed_block_report import FINAL_OUTPUT_CSV, matrix_dirs_from_preset_dir, read_matrix


@dataclass(frozen=True)
class AblationRule:
    name: str
    description: str


ABLATION_RULES: tuple[AblationRule, ...] = (
    AblationRule(
        "control",
        "Native final witness as recorded by the matrix final-output summaries.",
    ),
    AblationRule(
        "raw_as_final",
        "Remove the final witness: every raw expression pressure event is treated as final +1.",
    ),
    AblationRule(
        "no_false_one_demotion",
        "Remove the false-one demotion layer: trap raw expression is allowed to crown.",
    ),
    AblationRule(
        "no_latent_hold",
        "Remove latent/probe zero-hold: latent overcrown pressure is promoted as final +1.",
    ),
    AblationRule(
        "no_echo_independence",
        "Remove echo/relation-debt witness: relation-dependent expression is promoted as final +1.",
    ),
)

RULE_BY_NAME = {rule.name: rule for rule in ABLATION_RULES}


@dataclass(frozen=True)
class FinalRowCounts:
    raw_expression_pressure: int
    final_earned_one_count: int
    raw_false_one_pressure: int
    false_one_demoted_count: int
    latent_overcrown_pressure: int
    latent_overcrown_demoted_count: int
    relation_debt_count: int
    final_false_one_crowns: int
    truth_role: str


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


def _is_final_plus_one(row: dict[str, object]) -> bool:
    return str(row.get("final_trinary_value", "")) == "1" or str(row.get("final_trinary_symbol", "")) == "+1"


def _counts(row: dict[str, object]) -> FinalRowCounts:
    truth_role = str(row.get("truth_role", ""))
    final_false = 1 if truth_role == "trap" and _is_final_plus_one(row) else 0
    return FinalRowCounts(
        raw_expression_pressure=_int(row, "raw_expression_pressure"),
        final_earned_one_count=_int(row, "final_earned_one_count"),
        raw_false_one_pressure=_int(row, "raw_false_one_pressure"),
        false_one_demoted_count=_int(row, "false_one_demoted_count"),
        latent_overcrown_pressure=_int(row, "latent_overcrown_pressure"),
        latent_overcrown_demoted_count=_int(row, "latent_overcrown_demoted_count"),
        relation_debt_count=_int(row, "relation_debt_count"),
        final_false_one_crowns=final_false,
        truth_role=truth_role,
    )


def _variant_counts(row: dict[str, object], variant: str) -> dict[str, int]:
    c = _counts(row)

    if variant == "control":
        return {
            "final_earned_one_events": c.final_earned_one_count,
            "raw_expression_pressure": c.raw_expression_pressure,
            "raw_false_one_pressure": c.raw_false_one_pressure,
            "false_one_demoted_count": c.false_one_demoted_count,
            "latent_overcrown_pressure": c.latent_overcrown_pressure,
            "latent_overcrown_demoted_count": c.latent_overcrown_demoted_count,
            "relation_debt_count": c.relation_debt_count,
            "final_false_one_crowns": c.final_false_one_crowns,
            "trap_final_crowns": c.final_false_one_crowns,
            "promoted_latent_pressure": 0,
            "promoted_relation_debt": 0,
            "pressure_hidden_by_ablation": 0,
        }

    if variant == "raw_as_final":
        final_false = c.raw_false_one_pressure if c.truth_role == "trap" else 0
        hidden = c.false_one_demoted_count + c.latent_overcrown_demoted_count + c.relation_debt_count
        return {
            "final_earned_one_events": c.raw_expression_pressure,
            "raw_expression_pressure": c.raw_expression_pressure,
            "raw_false_one_pressure": c.raw_false_one_pressure,
            "false_one_demoted_count": 0,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "relation_debt_count": 0,
            "final_false_one_crowns": final_false,
            "trap_final_crowns": final_false,
            "promoted_latent_pressure": c.latent_overcrown_pressure,
            "promoted_relation_debt": c.relation_debt_count,
            "pressure_hidden_by_ablation": hidden,
        }

    if variant == "no_false_one_demotion":
        final_false = c.raw_false_one_pressure if c.truth_role == "trap" else 0
        return {
            "final_earned_one_events": c.final_earned_one_count + c.raw_false_one_pressure,
            "raw_expression_pressure": c.raw_expression_pressure,
            "raw_false_one_pressure": c.raw_false_one_pressure,
            "false_one_demoted_count": 0,
            "latent_overcrown_pressure": c.latent_overcrown_pressure,
            "latent_overcrown_demoted_count": c.latent_overcrown_demoted_count,
            "relation_debt_count": c.relation_debt_count,
            "final_false_one_crowns": final_false,
            "trap_final_crowns": final_false,
            "promoted_latent_pressure": 0,
            "promoted_relation_debt": 0,
            "pressure_hidden_by_ablation": c.false_one_demoted_count,
        }

    if variant == "no_latent_hold":
        return {
            "final_earned_one_events": c.final_earned_one_count + c.latent_overcrown_pressure,
            "raw_expression_pressure": c.raw_expression_pressure,
            "raw_false_one_pressure": c.raw_false_one_pressure,
            "false_one_demoted_count": c.false_one_demoted_count,
            "latent_overcrown_pressure": 0,
            "latent_overcrown_demoted_count": 0,
            "relation_debt_count": c.relation_debt_count,
            "final_false_one_crowns": c.final_false_one_crowns,
            "trap_final_crowns": c.final_false_one_crowns,
            "promoted_latent_pressure": c.latent_overcrown_pressure,
            "promoted_relation_debt": 0,
            "pressure_hidden_by_ablation": c.latent_overcrown_demoted_count,
        }

    if variant == "no_echo_independence":
        return {
            "final_earned_one_events": c.final_earned_one_count + c.relation_debt_count,
            "raw_expression_pressure": c.raw_expression_pressure,
            "raw_false_one_pressure": c.raw_false_one_pressure,
            "false_one_demoted_count": c.false_one_demoted_count,
            "latent_overcrown_pressure": c.latent_overcrown_pressure,
            "latent_overcrown_demoted_count": c.latent_overcrown_demoted_count,
            "relation_debt_count": 0,
            "final_false_one_crowns": c.final_false_one_crowns,
            "trap_final_crowns": c.final_false_one_crowns,
            "promoted_latent_pressure": 0,
            "promoted_relation_debt": c.relation_debt_count,
            "pressure_hidden_by_ablation": c.relation_debt_count,
        }

    raise ValueError(f"Unknown ablation variant: {variant}")


def _sum_counts(rows: Iterable[dict[str, int]]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for row in rows:
        for key, value in row.items():
            out[key] += int(value)
    return dict(out)


def _status(counts: dict[str, int], *, control_counts: dict[str, int] | None = None) -> str:
    if counts.get("final_false_one_crowns", 0):
        return "breach_introduced"
    if control_counts:
        earned_delta = counts.get("final_earned_one_events", 0) - control_counts.get("final_earned_one_events", 0)
        hidden_delta = counts.get("pressure_hidden_by_ablation", 0)
        if earned_delta > 0 and hidden_delta > 0:
            return "overcrown_pressure_promoted"
    if counts.get("pressure_hidden_by_ablation", 0):
        return "witness_pressure_hidden"
    if counts.get("raw_false_one_pressure", 0) or counts.get("latent_overcrown_pressure", 0) or counts.get("relation_debt_count", 0):
        return "pressure_visible_no_breach"
    return "quiet_no_breach"


def _gate_matrix_dirs(matrix_dirs: Iterable[Path], *, require_four_gates: bool) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    seen: dict[str, Path] = {}
    for matrix_dir in matrix_dirs:
        ident = read_matrix(Path(matrix_dir))
        gate = ident.gate
        if gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if gate in seen:
            raise ValueError(f"Duplicate native gate matrix coverage: {gate}")
        seen[gate] = Path(matrix_dir)
    if require_four_gates:
        missing = [gate for gate in NATIVE_GATE_NAMES if gate not in seen]
        if missing:
            raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))
    for gate in NATIVE_GATE_NAMES:
        if gate in seen:
            pairs.append((gate, seen[gate]))
    for gate in sorted(set(seen) - set(NATIVE_GATE_NAMES)):
        pairs.append((gate, seen[gate]))
    return pairs


def build_ablation_gate_rows(matrix_dirs: Iterable[Path], *, variants: Iterable[str] | None = None, require_four_gates: bool = True) -> list[dict[str, object]]:
    variant_names = list(variants or [rule.name for rule in ABLATION_RULES])
    unknown = [name for name in variant_names if name not in RULE_BY_NAME]
    if unknown:
        raise ValueError("Unknown ablation variant(s): " + ", ".join(unknown))

    gate_dirs = _gate_matrix_dirs(matrix_dirs, require_four_gates=require_four_gates)
    out: list[dict[str, object]] = []
    for gate, matrix_dir in gate_dirs:
        ident = read_matrix(matrix_dir)
        final_rows = _read_csv(matrix_dir / FINAL_OUTPUT_CSV)
        control_counts = _sum_counts(_variant_counts(row, "control") for row in final_rows)
        for variant in variant_names:
            counts = _sum_counts(_variant_counts(row, variant) for row in final_rows)
            status = _status(counts, control_counts=control_counts if variant != "control" else None)
            out.append(
                {
                    "variant": variant,
                    "gate": gate,
                    "matrix_label": ident.matrix_label,
                    "matrix_dir": str(matrix_dir),
                    "candidate_profile": ident.candidate_profile,
                    "seed_range": ident.seed_range,
                    "total_runs": ident.total_runs,
                    "final_earned_one_events": counts.get("final_earned_one_events", 0),
                    "earned_delta_from_control": counts.get("final_earned_one_events", 0) - control_counts.get("final_earned_one_events", 0),
                    "raw_expression_pressure": counts.get("raw_expression_pressure", 0),
                    "raw_false_one_pressure": counts.get("raw_false_one_pressure", 0),
                    "false_one_demoted_count": counts.get("false_one_demoted_count", 0),
                    "latent_overcrown_pressure": counts.get("latent_overcrown_pressure", 0),
                    "latent_overcrown_demoted_count": counts.get("latent_overcrown_demoted_count", 0),
                    "relation_debt_count": counts.get("relation_debt_count", 0),
                    "final_false_one_crowns": counts.get("final_false_one_crowns", 0),
                    "trap_final_crowns": counts.get("trap_final_crowns", 0),
                    "promoted_latent_pressure": counts.get("promoted_latent_pressure", 0),
                    "promoted_relation_debt": counts.get("promoted_relation_debt", 0),
                    "pressure_hidden_by_ablation": counts.get("pressure_hidden_by_ablation", 0),
                    "ablation_status": status,
                }
            )
    return out


def build_ablation_summary_rows(gate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in gate_rows:
        grouped[str(row["variant"])].append(row)

    control = grouped.get("control", [])
    control_earned = sum(_int(row, "final_earned_one_events") for row in control)
    out: list[dict[str, object]] = []
    for variant in [rule.name for rule in ABLATION_RULES if rule.name in grouped] + sorted(set(grouped) - {rule.name for rule in ABLATION_RULES}):
        rows = grouped[variant]
        final_false = sum(_int(row, "final_false_one_crowns") for row in rows)
        hidden = sum(_int(row, "pressure_hidden_by_ablation") for row in rows)
        earned = sum(_int(row, "final_earned_one_events") for row in rows)
        counts = {
            "final_false_one_crowns": final_false,
            "pressure_hidden_by_ablation": hidden,
            "final_earned_one_events": earned,
        }
        out.append(
            {
                "variant": variant,
                "variant_description": RULE_BY_NAME.get(variant, AblationRule(variant, "custom ablation variant")).description,
                "gates_read": len({str(row["gate"]) for row in rows}),
                "total_matrix_runs": sum(_int(row, "total_runs") for row in rows),
                "final_earned_one_events": earned,
                "earned_delta_from_control": earned - control_earned,
                "raw_expression_pressure": sum(_int(row, "raw_expression_pressure") for row in rows),
                "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
                "false_one_demoted_count": sum(_int(row, "false_one_demoted_count") for row in rows),
                "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
                "latent_overcrown_demoted_count": sum(_int(row, "latent_overcrown_demoted_count") for row in rows),
                "relation_debt_count": sum(_int(row, "relation_debt_count") for row in rows),
                "final_false_one_crowns": final_false,
                "trap_final_crowns": sum(_int(row, "trap_final_crowns") for row in rows),
                "promoted_latent_pressure": sum(_int(row, "promoted_latent_pressure") for row in rows),
                "promoted_relation_debt": sum(_int(row, "promoted_relation_debt") for row in rows),
                "pressure_hidden_by_ablation": hidden,
                "ablation_status": _status(counts, control_counts={"final_earned_one_events": control_earned} if variant != "control" else None),
            }
        )
    return out


def _overall_status(summary_rows: list[dict[str, object]]) -> str:
    non_control = [row for row in summary_rows if str(row["variant"]) != "control"]
    if any(_int(row, "final_false_one_crowns") for row in non_control):
        return "ablation_exposes_false_crown_risk"
    if any(_int(row, "pressure_hidden_by_ablation") for row in non_control):
        return "ablation_exposes_witness_work"
    return "no_ablation_effect_detected"


def _write_read(path: Path, *, summary_rows: list[dict[str, object]], gate_rows: list[dict[str, object]]) -> None:
    status = _overall_status(summary_rows)
    control = next((row for row in summary_rows if row["variant"] == "control"), {})
    control_false = _int(control, "final_false_one_crowns")
    max_false = max((_int(row, "final_false_one_crowns") for row in summary_rows), default=0)
    max_hidden = max((_int(row, "pressure_hidden_by_ablation") for row in summary_rows), default=0)

    lines: list[str] = []
    lines.append("# ZeroGateSim Witness Ablation Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report is a post-hoc witness ablation over completed controlled synthetic-field matrix outputs. It does not re-run physics, prove cosmology, or change the native four-gate law.")
    lines.append("")
    lines.append("It asks a narrower mechanism question: which final witness layers are carrying visible work when raw expression, trap demotion, latent hold, or echo/relation-debt witness are disabled in accounting?")
    lines.append("")
    lines.append("## Ablation posture")
    lines.append("")
    lines.append(f"Variants read: `{len(summary_rows)}`")
    lines.append(f"Control final false-one crowns: `{control_false}`")
    lines.append(f"Maximum final false-one crowns under ablation: `{max_false}`")
    lines.append(f"Maximum pressure hidden by ablation: `{max_hidden}`")
    lines.append(f"Overall status: `{status}`")
    lines.append("")
    if status == "ablation_exposes_false_crown_risk":
        lines.append("Resist: at least one ablation promotes trap pressure into final +1. That is useful evidence that the removed witness layer is doing real safety work.")
    elif status == "ablation_exposes_witness_work":
        lines.append("Witness: no trap crown appears, but at least one ablation hides pressure that the control report kept visible. Treat that layer as doing accounting work, not decoration.")
    else:
        lines.append("Hold: the supplied ablations did not change the top-level posture. Either the field is too quiet or this ablation set is not yet strong enough.")
    lines.append("")
    lines.append("## Variant summary")
    lines.append("")
    lines.append("| variant | gates | runs | earned | Δ earned | raw false | false demoted | latent held | relation debt | final false | promoted latent | promoted debt | hidden pressure | status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in summary_rows:
        lines.append(
            f"| {row['variant']} | {row['gates_read']} | {row['total_matrix_runs']} | {row['final_earned_one_events']} | {row['earned_delta_from_control']} | "
            f"{row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | {row['latent_overcrown_pressure']} | {row['relation_debt_count']} | "
            f"{row['final_false_one_crowns']} | {row['promoted_latent_pressure']} | {row['promoted_relation_debt']} | {row['pressure_hidden_by_ablation']} | {row['ablation_status']} |"
        )
    lines.append("")
    lines.append("## Gate summary")
    lines.append("")
    lines.append("| variant | gate | runs | earned | Δ earned | raw false | false demoted | latent held | relation debt | final false | hidden pressure | status |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in gate_rows:
        lines.append(
            f"| {row['variant']} | {row['gate']} | {row['total_runs']} | {row['final_earned_one_events']} | {row['earned_delta_from_control']} | "
            f"{row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | {row['latent_overcrown_pressure']} | {row['relation_debt_count']} | "
            f"{row['final_false_one_crowns']} | {row['pressure_hidden_by_ablation']} | {row['ablation_status']} |"
        )
    lines.append("")
    lines.append("## Ablation definitions")
    lines.append("")
    for rule in ABLATION_RULES:
        lines.append(f"- `{rule.name}`: {rule.description}")
    lines.append("")
    lines.append("## Interpretation boundary")
    lines.append("")
    lines.append("A post-hoc ablation does not replace a future full simulator rerun with altered mechanics. It is the first accounting check: if removing a witness layer promotes hidden pressure or false crowns, that layer is doing visible work and deserves a stronger rerun later.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_witness_ablation_report(*, output_dir: Path, matrix_dirs: Iterable[Path], variants: Iterable[str] | None = None, require_four_gates: bool = True) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    gate_rows = build_ablation_gate_rows(matrix_dirs, variants=variants, require_four_gates=require_four_gates)
    summary_rows = build_ablation_summary_rows(gate_rows)

    summary_csv = output_dir / "witness_ablation_summary.csv"
    gate_csv = output_dir / "witness_ablation_gate_summary.csv"
    read_md = output_dir / "witness_ablation_read.md"

    write_dict_rows_csv(summary_csv, summary_rows)
    write_dict_rows_csv(gate_csv, gate_rows)
    _write_read(read_md, summary_rows=summary_rows, gate_rows=gate_rows)
    bundle = write_evidence_bundle(
        output_dir,
        bundle_name="witness_ablation_bundle.zip",
        bundle_kind="zerogate_witness_ablation_bundle",
    )
    return {
        "witness_ablation_summary": summary_csv,
        "witness_ablation_gate_summary": gate_csv,
        "witness_ablation_read": read_md,
        "witness_ablation_bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a post-hoc witness ablation report from completed four-gate matrix outputs.")
    parser.add_argument("--preset-dir", type=Path, default=None, help="Directory containing completed four-gate matrix run folders.")
    parser.add_argument("--matrix-dir", type=Path, action="append", default=[], help="Completed matrix directory. May be supplied four times.")
    parser.add_argument("--variant", choices=sorted(RULE_BY_NAME), action="append", default=None, help="Ablation variant to include. Defaults to all built-in variants.")
    parser.add_argument("--allow-partial-gates", action="store_true", help="Allow reports with fewer than all four native gates. Default requires D/P/R/return.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for ablation report files.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    matrix_dirs = list(args.matrix_dir)
    if args.preset_dir is not None:
        matrix_dirs.extend(matrix_dirs_from_preset_dir(args.preset_dir))
    if not matrix_dirs:
        parser.error("Supply --preset-dir or at least one --matrix-dir")
    paths = write_witness_ablation_report(
        output_dir=args.out,
        matrix_dirs=matrix_dirs,
        variants=args.variant,
        require_four_gates=not args.allow_partial_gates,
    )
    print(f"Wrote witness ablation report to {paths['witness_ablation_read']}")
    print(f"Wrote witness ablation bundle to {paths['witness_ablation_bundle']}")


if __name__ == "__main__":  # pragma: no cover
    main()
