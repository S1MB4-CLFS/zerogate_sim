from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CLOSEOUT_CSV = "matrix_known_logic_closeout_summary.csv"
FINAL_OUTPUT_CSV = "matrix_final_output_summary.csv"
SUMMARY_MD = "matrix_summary.md"


@dataclass(frozen=True)
class MatrixIdentity:
    matrix_dir: Path
    matrix_label: str
    profile: str
    candidate_profile: str


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


def read_matrix_identity(matrix_dir: Path) -> MatrixIdentity:
    """Read matrix identity from matrix_summary.md when available."""

    matrix_dir = Path(matrix_dir)
    profile = "unknown"
    candidate_profile = "unknown"
    summary_path = matrix_dir / SUMMARY_MD
    if summary_path.exists():
        for line in summary_path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("Profile:"):
                profile = _parse_backtick_value(stripped) or profile
            elif stripped.startswith("Candidate profile:"):
                candidate_profile = _parse_backtick_value(stripped) or candidate_profile
    return MatrixIdentity(
        matrix_dir=matrix_dir,
        matrix_label=matrix_dir.name,
        profile=profile,
        candidate_profile=candidate_profile,
    )


def _final_counts(matrix_dir: Path) -> dict[str, int]:
    path = matrix_dir / FINAL_OUTPUT_CSV
    if not path.exists():
        return {
            "final_earned_one_events": 0,
            "raw_false_one_pressure": 0,
            "latent_overcrown_pressure": 0,
            "final_false_one_crowns": 0,
        }
    rows = _read_csv(path)
    final_false_crowns = 0
    for row in rows:
        truth_role = str(row.get("truth_role", ""))
        final_value = str(row.get("final_trinary_value", ""))
        final_symbol = str(row.get("final_trinary_symbol", ""))
        if truth_role == "trap" and (final_value == "1" or final_symbol == "+1"):
            final_false_crowns += 1
    return {
        "final_earned_one_events": sum(_int(row, "final_earned_one_count") for row in rows),
        "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
        "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
        "final_false_one_crowns": final_false_crowns,
    }


def build_cross_logic_rows(matrix_dirs: Iterable[Path]) -> list[dict[str, object]]:
    """Build one row per matrix/mirror closeout entry.

    The input directories must already be completed matrix run outputs containing
    `matrix_known_logic_closeout_summary.csv`. This function reads evidence from
    existing runs. It does not run a new proof harness and does not mutate the
    native zero-gate engine.
    """

    out: list[dict[str, object]] = []
    for matrix_dir in matrix_dirs:
        ident = read_matrix_identity(Path(matrix_dir))
        closeout_rows = _read_csv(ident.matrix_dir / CLOSEOUT_CSV)
        counts = _final_counts(ident.matrix_dir)
        for row in closeout_rows:
            out.append(
                {
                    "matrix_label": ident.matrix_label,
                    "matrix_dir": str(ident.matrix_dir),
                    "profile": ident.profile,
                    "candidate_profile": ident.candidate_profile,
                    "mirror": row.get("mirror", ""),
                    "closeout_status": row.get("closeout_status", ""),
                    "primary_pressure_count": _int(row, "primary_pressure_count"),
                    "secondary_pressure_count": _int(row, "secondary_pressure_count"),
                    "safety_breach_count": _int(row, "safety_breach_count"),
                    "useful_when": row.get("useful_when", ""),
                    "loss_report": row.get("loss_report", ""),
                    "final_earned_one_events": counts["final_earned_one_events"],
                    "raw_false_one_pressure": counts["raw_false_one_pressure"],
                    "latent_overcrown_pressure": counts["latent_overcrown_pressure"],
                    "final_false_one_crowns": counts["final_false_one_crowns"],
                }
            )
    return out


def build_matrix_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["matrix_label"])].append(row)

    out: list[dict[str, object]] = []
    for matrix_label in sorted(grouped):
        subset = grouped[matrix_label]
        first = subset[0]
        primary_total = sum(_int(row, "primary_pressure_count") for row in subset)
        secondary_total = sum(_int(row, "secondary_pressure_count") for row in subset)
        breach_total = sum(_int(row, "safety_breach_count") for row in subset)
        pressure_by_mirror = {str(row["mirror"]): _int(row, "primary_pressure_count") for row in subset}
        status = "breach" if breach_total else "pressure_visible" if primary_total or secondary_total else "quiet"
        out.append(
            {
                "matrix_label": matrix_label,
                "matrix_dir": first["matrix_dir"],
                "profile": first["profile"],
                "candidate_profile": first["candidate_profile"],
                "mirrors_read": len(subset),
                "visible_primary_pressure_total": primary_total,
                "visible_secondary_pressure_total": secondary_total,
                "safety_breach_total": breach_total,
                "fuzzy_pressure": pressure_by_mirror.get("fuzzy_many_valued", 0),
                "belnap_both_pressure": pressure_by_mirror.get("belnap_evidence_state", 0),
                "paraconsistent_localized_pressure": pressure_by_mirror.get("paraconsistent_conflict_locality", 0),
                "three_valued_loss_pressure": pressure_by_mirror.get("kleene_lukasiewicz_compression", 0),
                "final_earned_one_events": first["final_earned_one_events"],
                "raw_false_one_pressure": first["raw_false_one_pressure"],
                "latent_overcrown_pressure": first["latent_overcrown_pressure"],
                "final_false_one_crowns": first["final_false_one_crowns"],
                "comparison_status": status,
            }
        )
    return out


def build_mirror_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["mirror"])].append(row)

    out: list[dict[str, object]] = []
    for mirror in sorted(grouped):
        subset = grouped[mirror]
        statuses = Counter(str(row.get("closeout_status", "")) for row in subset)
        out.append(
            {
                "mirror": mirror,
                "matrices_read": len(subset),
                "primary_pressure_total": sum(_int(row, "primary_pressure_count") for row in subset),
                "secondary_pressure_total": sum(_int(row, "secondary_pressure_count") for row in subset),
                "safety_breach_total": sum(_int(row, "safety_breach_count") for row in subset),
                "dominant_status": statuses.most_common(1)[0][0] if statuses else "",
                "status_counts": ";".join(f"{name}:{count}" for name, count in sorted(statuses.items())),
                "loss_report": subset[0].get("loss_report", ""),
            }
        )
    return out


def _write_report_read(
    path: Path,
    *,
    matrix_rows: list[dict[str, object]],
    mirror_rows: list[dict[str, object]],
) -> None:
    matrices = len(matrix_rows)
    breach_total = sum(_int(row, "safety_breach_total") for row in matrix_rows)
    primary_total = sum(_int(row, "visible_primary_pressure_total") for row in matrix_rows)
    secondary_total = sum(_int(row, "visible_secondary_pressure_total") for row in matrix_rows)
    final_false_crowns = sum(_int(row, "final_false_one_crowns") for row in matrix_rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Cross-Logic Comparison Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report aggregates completed matrix runs. It does not run a new proof harness, mutate the native gate, or claim identity with fuzzy, Belnap, paraconsistent, Kleene, or Lukasiewicz logic.")
    lines.append("")
    lines.append("The purpose is to compare how the v1.3 projection mirrors behave across stronger or multiple adversarial toy-field runs.")
    lines.append("")
    lines.append("## Comparison posture")
    lines.append("")
    lines.append(f"Matrix runs read: `{matrices}`")
    lines.append(f"Primary mirror pressure total: `{primary_total}`")
    lines.append(f"Secondary mirror pressure total: `{secondary_total}`")
    lines.append(f"Mirror safety breach total: `{breach_total}`")
    lines.append(f"Final false-one crowns across read matrices: `{final_false_crowns}`")
    lines.append("")
    if breach_total or final_false_crowns:
        lines.append("Resist: at least one matrix reports a mirror breach or final false-one crown. Do not advance the claim; inspect the specific matrix and mirror rows.")
    elif primary_total or secondary_total:
        lines.append("Witness: mirror pressure is visible without safety breach. The report is doing its job: it exposes where each projection mirror sees or loses native pressure.")
    else:
        lines.append("Witness: the read matrices were quiet under the projection mirrors. Quiet is not proof; it is only this comparison posture.")
    lines.append("")
    lines.append("## Matrix table")
    lines.append("")
    lines.append("| matrix | profile | candidate profile | status | primary | secondary | breach | earned | false pressure | final false crowns |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|")
    for row in matrix_rows:
        lines.append(
            f"| {row['matrix_label']} | {row['profile']} | {row['candidate_profile']} | {row['comparison_status']} | "
            f"{row['visible_primary_pressure_total']} | {row['visible_secondary_pressure_total']} | {row['safety_breach_total']} | "
            f"{row['final_earned_one_events']} | {row['raw_false_one_pressure']} | {row['final_false_one_crowns']} |"
        )
    lines.append("")
    lines.append("## Mirror table")
    lines.append("")
    lines.append("| mirror | matrices | primary | secondary | breach | dominant status | loss report |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for row in mirror_rows:
        lines.append(
            f"| {row['mirror']} | {row['matrices_read']} | {row['primary_pressure_total']} | "
            f"{row['secondary_pressure_total']} | {row['safety_breach_total']} | {row['dominant_status']} | {row['loss_report']} |"
        )
    lines.append("")
    lines.append("## Witness translation")
    lines.append("")
    lines.append("Fuzzy pressure asks whether softer or stricter continuous aggregation hides a wounded gate. Belnap pressure asks whether evidence-for and evidence-against are both visible. Paraconsistent pressure asks whether conflict stays local. Three-valued pressure asks what disappears when native zero grammar collapses into unknown.")
    lines.append("")
    lines.append("A cross-logic report is useful only when it keeps those mirrors separate. If the report is used as borrowed authority, it failed.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_cross_logic_report_outputs(matrix_dirs: Iterable[Path], output_dir: Path) -> dict[str, Path]:
    output_dir = ensure_dir(Path(output_dir))
    rows = build_cross_logic_rows(matrix_dirs)
    if not rows:
        raise ValueError("At least one matrix directory with known-logic closeout rows is required")
    matrix_rows = build_matrix_summary_rows(rows)
    mirror_rows = build_mirror_summary_rows(rows)

    summary_csv = output_dir / "cross_logic_comparison_summary.csv"
    matrix_csv = output_dir / "cross_logic_comparison_matrix_summary.csv"
    mirror_csv = output_dir / "cross_logic_comparison_mirror_summary.csv"
    read_md = output_dir / "cross_logic_comparison_read.md"

    write_dict_rows_csv(summary_csv, rows)
    write_dict_rows_csv(matrix_csv, matrix_rows)
    write_dict_rows_csv(mirror_csv, mirror_rows)
    _write_report_read(read_md, matrix_rows=matrix_rows, mirror_rows=mirror_rows)
    bundle = write_evidence_bundle(
        output_dir,
        bundle_name="cross_logic_report_bundle.zip",
        bundle_kind="zerogate_cross_logic_comparison_bundle",
    )
    return {
        "cross_logic_comparison_summary": summary_csv,
        "cross_logic_comparison_matrix_summary": matrix_csv,
        "cross_logic_comparison_mirror_summary": mirror_csv,
        "cross_logic_comparison_read": read_md,
        "cross_logic_report_bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate known-logic mirror closeout outputs across completed ZeroGateSim matrix runs."
    )
    parser.add_argument(
        "--matrix-dir",
        action="append",
        type=Path,
        required=True,
        help="Matrix output directory containing matrix_known_logic_closeout_summary.csv. Repeat for multiple runs.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/cross_logic_comparison"),
        help="Output directory for the cross-logic comparison report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_cross_logic_report_outputs(args.matrix_dir, args.out)
    print("ZeroGateSim cross-logic comparison report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Upload cross_logic_report_bundle.zip or assistant_test_handoff.zip for review. Projection mirrors are pressure tests, not borrowed authority.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
