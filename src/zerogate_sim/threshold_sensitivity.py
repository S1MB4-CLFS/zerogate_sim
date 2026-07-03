from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

SUMMARY_CSV = "seed_block_four_gate_summary.csv"
MIRROR_CSV = "seed_block_four_gate_mirror_summary.csv"
READ_MD = "seed_block_four_gate_read.md"


@dataclass(frozen=True)
class ThresholdVariant:
    label: str
    report_dir: Path


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


def parse_variant_arg(value: str) -> ThresholdVariant:
    """Parse `label=path` CLI arguments for threshold sensitivity reports."""

    label, sep, raw_path = value.partition("=")
    if not sep or not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("variant must use label=path")
    return ThresholdVariant(label=label.strip(), report_dir=Path(raw_path.strip()))


def _summary_status(row: dict[str, object]) -> str:
    if _int(row, "final_false_one_crowns") or _int(row, "mirror_safety_breach_total"):
        return "breach"
    if (
        _int(row, "raw_false_one_pressure")
        or _int(row, "latent_overcrown_pressure")
        or _int(row, "relation_debt_count")
        or _int(row, "mirror_primary_pressure")
        or _int(row, "mirror_secondary_pressure")
    ):
        return "pressure_visible_no_breach"
    return "quiet_no_breach"


def build_threshold_summary_rows(variants: list[ThresholdVariant]) -> list[dict[str, object]]:
    if not variants:
        raise ValueError("At least one threshold variant is required.")

    rows: list[dict[str, object]] = []
    baseline_earned: int | None = None
    baseline_raw_false: int | None = None
    for order, variant in enumerate(variants):
        summary_rows = _read_csv(variant.report_dir / SUMMARY_CSV)
        if not summary_rows:
            raise ValueError(f"No gate rows in {variant.report_dir / SUMMARY_CSV}")
        total_runs = sum(_int(row, "total_runs") for row in summary_rows)
        earned = sum(_int(row, "final_earned_one_events") for row in summary_rows)
        raw_false = sum(_int(row, "raw_false_one_pressure") for row in summary_rows)
        false_demoted = sum(_int(row, "false_one_demoted_count") for row in summary_rows)
        latent = sum(_int(row, "latent_overcrown_pressure") for row in summary_rows)
        relation_debt = sum(_int(row, "relation_debt_count") for row in summary_rows)
        final_false = sum(_int(row, "final_false_one_crowns") for row in summary_rows)
        trap_final = sum(_int(row, "trap_final_crowns") for row in summary_rows)
        mirror_primary = sum(_int(row, "mirror_primary_pressure") for row in summary_rows)
        mirror_secondary = sum(_int(row, "mirror_secondary_pressure") for row in summary_rows)
        mirror_breach = sum(_int(row, "mirror_safety_breach_total") for row in summary_rows)
        status = "breach" if final_false or mirror_breach else "pressure_visible_no_breach" if (raw_false or latent or relation_debt or mirror_primary or mirror_secondary) else "quiet_no_breach"
        if baseline_earned is None:
            baseline_earned = earned
            baseline_raw_false = raw_false
        rows.append(
            {
                "variant": variant.label,
                "variant_order": order,
                "report_dir": str(variant.report_dir),
                "gates_read": len({str(row.get("gate", "")) for row in summary_rows if str(row.get("gate", ""))}),
                "total_matrix_runs": total_runs,
                "final_earned_one_events": earned,
                "earned_delta_from_baseline": earned - int(baseline_earned or 0),
                "raw_false_one_pressure": raw_false,
                "raw_false_delta_from_baseline": raw_false - int(baseline_raw_false or 0),
                "false_one_demoted_count": false_demoted,
                "latent_overcrown_pressure": latent,
                "relation_debt_count": relation_debt,
                "final_false_one_crowns": final_false,
                "trap_final_crowns": trap_final,
                "mirror_primary_pressure": mirror_primary,
                "mirror_secondary_pressure": mirror_secondary,
                "mirror_safety_breach_total": mirror_breach,
                "threshold_status": status,
            }
        )
    return rows


def build_threshold_gate_rows(variants: list[ThresholdVariant]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for order, variant in enumerate(variants):
        for row in _read_csv(variant.report_dir / SUMMARY_CSV):
            out.append(
                {
                    "variant": variant.label,
                    "variant_order": order,
                    "gate": row.get("gate", ""),
                    "matrix_label": row.get("matrix_label", ""),
                    "candidate_profile": row.get("candidate_profile", ""),
                    "seed_range": row.get("seed_range", ""),
                    "total_runs": _int(row, "total_runs"),
                    "final_earned_one_events": _int(row, "final_earned_one_events"),
                    "raw_false_one_pressure": _int(row, "raw_false_one_pressure"),
                    "false_one_demoted_count": _int(row, "false_one_demoted_count"),
                    "latent_overcrown_pressure": _int(row, "latent_overcrown_pressure"),
                    "relation_debt_count": _int(row, "relation_debt_count"),
                    "final_false_one_crowns": _int(row, "final_false_one_crowns"),
                    "mirror_primary_pressure": _int(row, "mirror_primary_pressure"),
                    "mirror_secondary_pressure": _int(row, "mirror_secondary_pressure"),
                    "mirror_safety_breach_total": _int(row, "mirror_safety_breach_total"),
                    "threshold_gate_status": _summary_status(row),
                }
            )
    return out


def build_threshold_mirror_rows(variants: list[ThresholdVariant]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for order, variant in enumerate(variants):
        for row in _read_csv(variant.report_dir / MIRROR_CSV):
            mirror = str(row.get("mirror", ""))
            item = {
                "variant": variant.label,
                "variant_order": order,
                "mirror": mirror,
                "gates_read": _int(row, "gates_read"),
                "primary_pressure_total": _int(row, "primary_pressure_total"),
                "secondary_pressure_total": _int(row, "secondary_pressure_total"),
                "safety_breach_total": _int(row, "safety_breach_total"),
                "dominant_status": row.get("dominant_status", ""),
            }
            grouped[mirror].append(item)

    out: list[dict[str, object]] = []
    for mirror in sorted(grouped):
        for row in sorted(grouped[mirror], key=lambda item: int(item["variant_order"])):
            out.append(row)
    return out


def _overall_status(summary_rows: list[dict[str, object]]) -> str:
    if any(_int(row, "final_false_one_crowns") or _int(row, "mirror_safety_breach_total") for row in summary_rows):
        return "breach"
    earned_values = [int(row["final_earned_one_events"]) for row in summary_rows]
    raw_false_values = [int(row["raw_false_one_pressure"]) for row in summary_rows]
    earned_span = max(earned_values) - min(earned_values) if earned_values else 0
    raw_false_span = max(raw_false_values) - min(raw_false_values) if raw_false_values else 0
    if earned_span or raw_false_span:
        return "sensitive_no_breach"
    return "stable_no_breach"


def _write_read(path: Path, *, summary_rows: list[dict[str, object]], gate_rows: list[dict[str, object]], mirror_rows: list[dict[str, object]]) -> None:
    status = _overall_status(summary_rows)
    earned_values = [int(row["final_earned_one_events"]) for row in summary_rows]
    raw_false_values = [int(row["raw_false_one_pressure"]) for row in summary_rows]
    final_false_total = sum(_int(row, "final_false_one_crowns") for row in summary_rows)
    mirror_breach_total = sum(_int(row, "mirror_safety_breach_total") for row in summary_rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Threshold Sensitivity Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report compares completed seed-block four-gate reports across threshold variants. It does not prove cosmology, physical dimensional genesis, or that reality itself is trinary.")
    lines.append("")
    lines.append("It asks a narrower engineering-science question: does the four-gate earned-one witness remain bounded when gate and/or strength thresholds move within a controlled band?")
    lines.append("")
    lines.append("## Sensitivity posture")
    lines.append("")
    lines.append(f"Variants read: `{len(summary_rows)}`")
    lines.append(f"Final earned-one range: `{min(earned_values) if earned_values else 0}` to `{max(earned_values) if earned_values else 0}`")
    lines.append(f"Raw false-one pressure range: `{min(raw_false_values) if raw_false_values else 0}` to `{max(raw_false_values) if raw_false_values else 0}`")
    lines.append(f"Final false-one crowns across variants: `{final_false_total}`")
    lines.append(f"Mirror safety breach total across variants: `{mirror_breach_total}`")
    lines.append(f"Overall status: `{status}`")
    lines.append("")
    if status == "breach":
        lines.append("Resist: at least one threshold variant produced a final false-one crown or mirror safety breach. Inspect that variant before advancing the claim.")
    elif status == "sensitive_no_breach":
        lines.append("Witness: no breach appeared, but counts move across threshold variants. Treat the result as bounded sensitivity, not threshold-invariant proof.")
    else:
        lines.append("Witness: no breach appeared and the core counts remained stable across the supplied variants.")
    lines.append("")
    lines.append("## Variant summary")
    lines.append("")
    lines.append("| variant | runs | earned | Δ earned | raw false | Δ raw false | false demoted | latent | relation debt | final false | mirror breach | status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in summary_rows:
        lines.append(
            f"| {row['variant']} | {row['total_matrix_runs']} | {row['final_earned_one_events']} | {row['earned_delta_from_baseline']} | "
            f"{row['raw_false_one_pressure']} | {row['raw_false_delta_from_baseline']} | {row['false_one_demoted_count']} | "
            f"{row['latent_overcrown_pressure']} | {row['relation_debt_count']} | {row['final_false_one_crowns']} | "
            f"{row['mirror_safety_breach_total']} | {row['threshold_status']} |"
        )
    lines.append("")
    lines.append("## Gate summary")
    lines.append("")
    lines.append("| variant | gate | runs | earned | raw false | false demoted | latent | relation debt | final false | mirror breach | status |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in gate_rows:
        lines.append(
            f"| {row['variant']} | {row['gate']} | {row['total_runs']} | {row['final_earned_one_events']} | "
            f"{row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | {row['latent_overcrown_pressure']} | "
            f"{row['relation_debt_count']} | {row['final_false_one_crowns']} | {row['mirror_safety_breach_total']} | {row['threshold_gate_status']} |"
        )
    lines.append("")
    lines.append("## Mirror summary")
    lines.append("")
    lines.append("| variant | mirror | primary pressure | secondary pressure | breach | status |")
    lines.append("|---|---|---:|---:|---:|---|")
    for row in mirror_rows:
        lines.append(
            f"| {row['variant']} | {row['mirror']} | {row['primary_pressure_total']} | "
            f"{row['secondary_pressure_total']} | {row['safety_breach_total']} | {row['dominant_status']} |"
        )
    lines.append("")
    lines.append("## Interpretation boundary")
    lines.append("")
    lines.append("A clean threshold sweep strengthens the controlled synthetic-field result only inside the tested threshold band. It does not remove the need for ablation, role-blind shadow design, independent generator families, or external comparison.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_threshold_sensitivity_report(*, output_dir: Path, variants: list[ThresholdVariant]) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    summary_rows = build_threshold_summary_rows(variants)
    gate_rows = build_threshold_gate_rows(variants)
    mirror_rows = build_threshold_mirror_rows(variants)

    summary_csv = output_dir / "threshold_sensitivity_summary.csv"
    gate_csv = output_dir / "threshold_sensitivity_gate_summary.csv"
    mirror_csv = output_dir / "threshold_sensitivity_mirror_summary.csv"
    read_md = output_dir / "threshold_sensitivity_read.md"
    write_dict_rows_csv(summary_csv, summary_rows)
    write_dict_rows_csv(gate_csv, gate_rows)
    write_dict_rows_csv(mirror_csv, mirror_rows)
    _write_read(read_md, summary_rows=summary_rows, gate_rows=gate_rows, mirror_rows=mirror_rows)
    bundle = write_evidence_bundle(output_dir, bundle_name="threshold_sensitivity_bundle.zip", bundle_kind="zerogate_threshold_sensitivity_report_bundle")
    return {
        "threshold_sensitivity_summary": summary_csv,
        "threshold_sensitivity_gate_summary": gate_csv,
        "threshold_sensitivity_mirror_summary": mirror_csv,
        "threshold_sensitivity_read": read_md,
        "threshold_sensitivity_bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read seed-block four-gate reports across threshold variants and write a sensitivity report.")
    parser.add_argument("--variant", action="append", type=parse_variant_arg, default=[], help="Threshold variant in label=path form. Supply multiple times.")
    parser.add_argument("--out", type=Path, default=Path("runs/threshold_sensitivity_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_threshold_sensitivity_report(output_dir=args.out, variants=list(args.variant))
    print("ZeroGateSim threshold sensitivity report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
