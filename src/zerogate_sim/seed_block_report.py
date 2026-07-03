from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from zerogate_sim.comparison_preset import NATIVE_GATE_NAMES
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

FINAL_OUTPUT_CSV = "matrix_final_output_summary.csv"
CLOSEOUT_CSV = "matrix_known_logic_closeout_summary.csv"
SUMMARY_MD = "matrix_summary.md"

GATE_BY_CANDIDATE_PROFILE = {
    "adversary_distinction": "distinction",
    "adversary_polarity": "polarity",
    "adversary_relation": "relation",
    "adversary_return": "return",
}


@dataclass(frozen=True)
class MatrixRead:
    matrix_dir: Path
    matrix_label: str
    gate: str
    profile: str
    candidate_profile: str
    seed_range: str
    total_runs: int


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


def _parse_backtick_value(line: str) -> str:
    if "`" not in line:
        return ""
    parts = line.split("`")
    return parts[1].strip() if len(parts) >= 3 else ""


def _parse_int_backtick_value(line: str) -> int:
    value = _parse_backtick_value(line)
    try:
        return int(float(value))
    except ValueError:
        return 0


def _gate_from_label_or_profile(matrix_label: str, candidate_profile: str) -> str:
    if candidate_profile in GATE_BY_CANDIDATE_PROFILE:
        return GATE_BY_CANDIDATE_PROFILE[candidate_profile]
    for gate in NATIVE_GATE_NAMES:
        if matrix_label.startswith(f"{gate}_"):
            return gate
    return "unknown"


def read_matrix(matrix_dir: Path) -> MatrixRead:
    matrix_dir = Path(matrix_dir)
    profile = "unknown"
    candidate_profile = "unknown"
    seed_range = "unknown"
    total_runs = 0
    summary_path = matrix_dir / SUMMARY_MD
    if summary_path.exists():
        for line in summary_path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("Profile:"):
                profile = _parse_backtick_value(stripped) or profile
            elif stripped.startswith("Candidate profile:"):
                candidate_profile = _parse_backtick_value(stripped) or candidate_profile
            elif stripped.startswith("Seeds per scenario:"):
                parts = stripped.split("`")
                if len(parts) >= 5:
                    seed_range = f"{parts[1]}-{parts[3]}"
                else:
                    seed_range = _parse_backtick_value(stripped) or seed_range
            elif stripped.startswith("Total runs:"):
                total_runs = _parse_int_backtick_value(stripped)
    gate = _gate_from_label_or_profile(matrix_dir.name, candidate_profile)
    return MatrixRead(
        matrix_dir=matrix_dir,
        matrix_label=matrix_dir.name,
        gate=gate,
        profile=profile,
        candidate_profile=candidate_profile,
        seed_range=seed_range,
        total_runs=total_runs,
    )


def matrix_dirs_from_preset_dir(preset_dir: Path) -> list[Path]:
    preset_dir = Path(preset_dir)
    if not preset_dir.exists():
        raise FileNotFoundError(f"Preset directory not found: {preset_dir}")
    out: list[Path] = []
    for path in sorted(preset_dir.iterdir()):
        if path.is_dir() and (path / CLOSEOUT_CSV).exists() and (path / FINAL_OUTPUT_CSV).exists():
            out.append(path)
    return out


def _final_counts(matrix_dir: Path) -> dict[str, int]:
    rows = _read_csv(matrix_dir / FINAL_OUTPUT_CSV)
    final_false_crowns = 0
    trap_final_crowns = 0
    for row in rows:
        truth_role = str(row.get("truth_role", ""))
        final_value = str(row.get("final_trinary_value", ""))
        final_symbol = str(row.get("final_trinary_symbol", ""))
        if truth_role == "trap" and (final_value == "1" or final_symbol == "+1"):
            final_false_crowns += 1
            trap_final_crowns += 1
    return {
        "final_earned_one_events": sum(_int(row, "final_earned_one_count") for row in rows),
        "raw_expression_pressure": sum(_int(row, "raw_expression_pressure") for row in rows),
        "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
        "false_one_demoted_count": sum(_int(row, "false_one_demoted_count") for row in rows),
        "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
        "latent_overcrown_demoted_count": sum(_int(row, "latent_overcrown_demoted_count") for row in rows),
        "relation_debt_count": sum(_int(row, "relation_debt_count") for row in rows),
        "final_false_one_crowns": final_false_crowns,
        "trap_final_crowns": trap_final_crowns,
    }


def _mirror_counts(matrix_dir: Path) -> tuple[dict[str, int], list[dict[str, str]]]:
    rows = _read_csv(matrix_dir / CLOSEOUT_CSV)
    return (
        {
            "mirror_primary_pressure": sum(_int(row, "primary_pressure_count") for row in rows),
            "mirror_secondary_pressure": sum(_int(row, "secondary_pressure_count") for row in rows),
            "mirror_safety_breach_total": sum(_int(row, "safety_breach_count") for row in rows),
        },
        rows,
    )


def build_seed_block_rows(matrix_dirs: Iterable[Path], *, require_four_gates: bool = True) -> list[dict[str, object]]:
    reads = [read_matrix(Path(path)) for path in matrix_dirs]
    if not reads:
        raise ValueError("No completed matrix directories supplied.")

    by_gate: dict[str, MatrixRead] = {}
    duplicates: list[str] = []
    for item in reads:
        if item.gate == "unknown":
            raise ValueError(f"Cannot infer native gate for matrix directory: {item.matrix_dir}")
        if item.gate in by_gate:
            duplicates.append(item.gate)
        by_gate[item.gate] = item

    if duplicates:
        raise ValueError("Duplicate native gate matrix coverage: " + ", ".join(sorted(set(duplicates))))

    if require_four_gates:
        missing = [gate for gate in NATIVE_GATE_NAMES if gate not in by_gate]
        if missing:
            raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))

    out: list[dict[str, object]] = []
    for gate in NATIVE_GATE_NAMES:
        if gate not in by_gate:
            continue
        item = by_gate[gate]
        final_counts = _final_counts(item.matrix_dir)
        mirror_counts, _ = _mirror_counts(item.matrix_dir)
        safety_breach = mirror_counts["mirror_safety_breach_total"]
        final_false = final_counts["final_false_one_crowns"]
        raw_false = final_counts["raw_false_one_pressure"]
        pressure = raw_false + final_counts["latent_overcrown_pressure"] + final_counts["relation_debt_count"] + mirror_counts["mirror_primary_pressure"]
        if safety_breach or final_false:
            status = "breach"
        elif pressure:
            status = "pressure_visible_no_breach"
        else:
            status = "quiet_no_breach"
        out.append(
            {
                "gate": gate,
                "matrix_label": item.matrix_label,
                "matrix_dir": str(item.matrix_dir),
                "profile": item.profile,
                "candidate_profile": item.candidate_profile,
                "seed_range": item.seed_range,
                "total_runs": item.total_runs,
                "final_earned_one_events": final_counts["final_earned_one_events"],
                "raw_expression_pressure": final_counts["raw_expression_pressure"],
                "raw_false_one_pressure": raw_false,
                "false_one_demoted_count": final_counts["false_one_demoted_count"],
                "latent_overcrown_pressure": final_counts["latent_overcrown_pressure"],
                "latent_overcrown_demoted_count": final_counts["latent_overcrown_demoted_count"],
                "relation_debt_count": final_counts["relation_debt_count"],
                "final_false_one_crowns": final_false,
                "trap_final_crowns": final_counts["trap_final_crowns"],
                "mirror_primary_pressure": mirror_counts["mirror_primary_pressure"],
                "mirror_secondary_pressure": mirror_counts["mirror_secondary_pressure"],
                "mirror_safety_breach_total": safety_breach,
                "seed_block_status": status,
            }
        )
    return out


def build_mirror_rows(matrix_dirs: Iterable[Path]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for matrix_dir in matrix_dirs:
        ident = read_matrix(Path(matrix_dir))
        _, rows = _mirror_counts(ident.matrix_dir)
        for row in rows:
            mirror = str(row.get("mirror", ""))
            grouped[mirror].append(
                {
                    "gate": ident.gate,
                    "primary_pressure_count": _int(row, "primary_pressure_count"),
                    "secondary_pressure_count": _int(row, "secondary_pressure_count"),
                    "safety_breach_count": _int(row, "safety_breach_count"),
                    "closeout_status": row.get("closeout_status", ""),
                    "loss_report": row.get("loss_report", ""),
                }
            )

    out: list[dict[str, object]] = []
    for mirror in sorted(grouped):
        subset = grouped[mirror]
        statuses = Counter(str(row["closeout_status"]) for row in subset)
        out.append(
            {
                "mirror": mirror,
                "gates_read": len(subset),
                "primary_pressure_total": sum(_int(row, "primary_pressure_count") for row in subset),
                "secondary_pressure_total": sum(_int(row, "secondary_pressure_count") for row in subset),
                "safety_breach_total": sum(_int(row, "safety_breach_count") for row in subset),
                "gate_pressure_summary": ";".join(f"{row['gate']}:{row['primary_pressure_count']}" for row in subset),
                "dominant_status": statuses.most_common(1)[0][0] if statuses else "",
                "loss_report": subset[0].get("loss_report", ""),
            }
        )
    return out


def _overall_status(rows: list[dict[str, object]]) -> str:
    if any(_int(row, "final_false_one_crowns") or _int(row, "mirror_safety_breach_total") for row in rows):
        return "breach"
    if any(
        _int(row, "raw_false_one_pressure")
        or _int(row, "latent_overcrown_pressure")
        or _int(row, "relation_debt_count")
        or _int(row, "mirror_primary_pressure")
        or _int(row, "mirror_secondary_pressure")
        for row in rows
    ):
        return "pass_pressure_visible"
    return "pass_quiet"


def _write_read(path: Path, *, rows: list[dict[str, object]], mirror_rows: list[dict[str, object]]) -> None:
    total_runs = sum(_int(row, "total_runs") for row in rows)
    earned = sum(_int(row, "final_earned_one_events") for row in rows)
    raw_false = sum(_int(row, "raw_false_one_pressure") for row in rows)
    false_demoted = sum(_int(row, "false_one_demoted_count") for row in rows)
    latent = sum(_int(row, "latent_overcrown_pressure") for row in rows)
    relation_debt = sum(_int(row, "relation_debt_count") for row in rows)
    final_false = sum(_int(row, "final_false_one_crowns") for row in rows)
    mirror_breach = sum(_int(row, "safety_breach_total") for row in mirror_rows)
    status = _overall_status(rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Seed-Block Four-Gate Adversary Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report reads completed matrix runs from a controlled synthetic field. It does not prove cosmology, physical dimensional genesis, or that reality itself is trinary.")
    lines.append("")
    lines.append("It tests a narrower question: across dedicated distinction, polarity, relation, and return adversary corpora, does the final witness continue to separate earned-one from raw expression, latent pressure, relation/return debt, and false-one pressure?")
    lines.append("")
    lines.append("## Seed-block posture")
    lines.append("")
    lines.append(f"Native gates read: `{', '.join(str(row['gate']) for row in rows)}`")
    lines.append(f"Total matrix runs: `{total_runs}`")
    lines.append(f"Final earned-one events: `{earned}`")
    lines.append(f"Raw false-one pressure: `{raw_false}`")
    lines.append(f"False-one pressure demoted: `{false_demoted}`")
    lines.append(f"Latent overcrown pressure: `{latent}`")
    lines.append(f"Relation/return debt count: `{relation_debt}`")
    lines.append(f"Final false-one crowns: `{final_false}`")
    lines.append(f"Mirror safety breach total: `{mirror_breach}`")
    lines.append(f"Overall status: `{status}`")
    lines.append("")
    if status == "breach":
        lines.append("Resist: at least one gate block reports a final false-one crown or mirror safety breach. Do not advance the claim until the specific gate block is inspected.")
    elif status == "pass_pressure_visible":
        lines.append("Witness: adversarial pressure is visible and no final false-one crown or mirror safety breach is reported.")
    else:
        lines.append("Witness: no breach is reported, but this seed block is quiet. Treat it as a clean wiring result, not a strong pressure result.")
    lines.append("")
    lines.append("## Gate summary")
    lines.append("")
    lines.append("| gate | profile | candidate profile | seeds | runs | earned | raw false | false demoted | latent | relation debt | final false | mirror breach | status |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            f"| {row['gate']} | {row['profile']} | {row['candidate_profile']} | {row['seed_range']} | {row['total_runs']} | "
            f"{row['final_earned_one_events']} | {row['raw_false_one_pressure']} | {row['false_one_demoted_count']} | "
            f"{row['latent_overcrown_pressure']} | {row['relation_debt_count']} | {row['final_false_one_crowns']} | "
            f"{row['mirror_safety_breach_total']} | {row['seed_block_status']} |"
        )
    lines.append("")
    lines.append("## Mirror summary")
    lines.append("")
    lines.append("| mirror | gates | primary pressure | secondary pressure | breach | gate pressure summary | loss report |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for row in mirror_rows:
        lines.append(
            f"| {row['mirror']} | {row['gates_read']} | {row['primary_pressure_total']} | "
            f"{row['secondary_pressure_total']} | {row['safety_breach_total']} | {row['gate_pressure_summary']} | {row['loss_report']} |"
        )
    lines.append("")
    lines.append("## Next interpretation")
    lines.append("")
    lines.append("A passing seed block supports readiness for stronger synthetic experiments. It does not remove the need for threshold sensitivity, witness ablation, role-blind shadow design, and independent generator families.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_seed_block_report(
    *,
    output_dir: Path,
    matrix_dirs: Iterable[Path],
    require_four_gates: bool = True,
) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    matrix_dirs = list(matrix_dirs)
    rows = build_seed_block_rows(matrix_dirs, require_four_gates=require_four_gates)
    mirror_rows = build_mirror_rows(matrix_dirs)

    summary_csv = output_dir / "seed_block_four_gate_summary.csv"
    mirror_csv = output_dir / "seed_block_four_gate_mirror_summary.csv"
    read_md = output_dir / "seed_block_four_gate_read.md"
    write_dict_rows_csv(summary_csv, rows)
    write_dict_rows_csv(mirror_csv, mirror_rows)
    _write_read(read_md, rows=rows, mirror_rows=mirror_rows)
    bundle = write_evidence_bundle(output_dir, bundle_name="seed_block_report_bundle.zip", bundle_kind="zerogate_seed_block_four_gate_report_bundle")
    return {
        "seed_block_four_gate_summary": summary_csv,
        "seed_block_four_gate_mirror_summary": mirror_csv,
        "seed_block_four_gate_read": read_md,
        "seed_block_report_bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read completed four-gate adversary matrix runs and write a seed-block report.")
    parser.add_argument("--preset-dir", type=Path, default=None, help="Directory containing completed four-gate matrix run folders.")
    parser.add_argument("--matrix-dir", action="append", type=Path, default=[], help="Completed matrix directory. May be supplied multiple times.")
    parser.add_argument("--out", type=Path, default=Path("runs/seed_block_four_gate_report"))
    parser.add_argument("--allow-partial", action="store_true", help="Allow less than full distinction/polarity/relation/return coverage.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    matrix_dirs = list(args.matrix_dir)
    if args.preset_dir is not None:
        matrix_dirs.extend(matrix_dirs_from_preset_dir(args.preset_dir))
    paths = write_seed_block_report(output_dir=args.out, matrix_dirs=matrix_dirs, require_four_gates=not args.allow_partial)
    print("ZeroGateSim seed-block four-gate report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
