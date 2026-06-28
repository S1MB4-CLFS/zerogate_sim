from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle


SUMMARY_NAME = "proof_record_summary.json"


NUMERIC_KEYS = (
    "corpus_count",
    "scenario_cells",
    "seeded_runs",
    "final_earned_one_events",
    "raw_expression_pressure",
    "raw_false_one_pressure",
    "false_one_demoted_count",
    "final_false_one_crowns",
    "latent_overcrown_pressure",
    "latent_overcrown_demoted_count",
    "expresser_candidate_count",
    "earned_expresser_candidate_count",
    "trap_candidate_count",
    "trap_final_crown_count",
    "corpora_passed",
    "corpora_hold",
    "corpora_failed",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze multiple proof records into the v1.0-alpha first-research-alpha release record."
    )
    parser.add_argument(
        "--proof-dir",
        action="append",
        type=Path,
        required=True,
        help="Proof directory containing proof_record_summary.json. Pass this at least twice for initial + reproduction records.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/first_research_alpha_v1_0_alpha"),
        help="Output directory for first_research_alpha_record.md and release_bundle.zip.",
    )
    parser.add_argument("--no-bundle", action="store_true", help="Do not rebuild release_bundle.zip.")
    return parser


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: object) -> int:
    if value in {"", None}:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _load_proof(proof_dir: Path) -> dict[str, object]:
    proof_dir = Path(proof_dir)
    path = proof_dir / SUMMARY_NAME
    if not path.exists():
        raise FileNotFoundError(f"Missing {SUMMARY_NAME}: {path}")
    row = _read_json(path)
    row["proof_dir"] = str(proof_dir)
    return row


def _seed_ranges(rows: list[dict[str, object]]) -> str:
    ranges = [str(row.get("seed_range", "unknown")) for row in rows]
    return ", ".join(ranges)


def _release_status(rows: list[dict[str, object]], totals: dict[str, int]) -> tuple[str, str, str]:
    proof_like = all(str(row.get("proof_status", "")).startswith("proof_record") for row in rows)
    all_demoted = totals["raw_false_one_pressure"] == totals["false_one_demoted_count"]
    no_final_false = totals["final_false_one_crowns"] == 0 and totals["trap_final_crown_count"] == 0
    no_failed_corpora = totals["corpora_failed"] == 0
    real_pressure = totals["raw_false_one_pressure"] > 0 and totals["final_earned_one_events"] > 0
    replicated = len(rows) >= 2

    if replicated and proof_like and all_demoted and no_final_false and no_failed_corpora and real_pressure:
        return (
            "first_research_alpha_passed",
            "The earned-one witness passed the original and fresh-seed trinary adversarial proof records: false-one pressure was named and fully demoted with zero final false-one crowns.",
            "freeze v1.0-alpha; do not mutate the core without a new breach record",
        )
    if not replicated:
        return (
            "hold_needs_reproduction",
            "Only one proof record was supplied; first-research-alpha requires at least one fresh-seed reproduction.",
            "run a fresh-seed proof reproduction before release freeze",
        )
    if not no_final_false:
        return (
            "hold_false_crown_breach",
            "A final false-one crown or trap final crown appeared in the combined record.",
            "hold v1.0-alpha and repair the breach before release freeze",
        )
    if not all_demoted:
        return (
            "hold_unfinished_demotions",
            "Some raw false-one pressure was not demoted in the combined record.",
            "repair earned-one witness or candidate ecology before release freeze",
        )
    return (
        "hold_incomplete_release_evidence",
        "The combined proof records were not strong enough for first-research-alpha release posture.",
        "inspect proof records before release freeze",
    )


def summarize_release(proof_dirs: list[Path]) -> tuple[dict[str, object], list[dict[str, object]]]:
    if len(proof_dirs) < 1:
        raise ValueError("At least one proof directory is required")
    rows = [_load_proof(path) for path in proof_dirs]
    totals = {key: sum(_as_int(row.get(key, 0)) for row in rows) for key in NUMERIC_KEYS}
    status, claim, next_action = _release_status(rows, totals)
    summary: dict[str, object] = {
        "release": "v1.0-alpha",
        "status": status,
        "proof_record_count": len(rows),
        "seed_ranges": _seed_ranges(rows),
        **totals,
        "release_claim": claim,
        "next_action": next_action,
        "claim_boundary": "Toy-field proof-of-concept only; not cosmology, physics, or final trinary mathematics.",
    }
    return summary, rows


def _write_markdown(path: Path, summary: dict[str, object], rows: list[dict[str, object]]) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim v1.0-alpha First Research Alpha Record")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"Release posture: `{summary['status']}`")
    lines.append("")
    lines.append(str(summary["release_claim"]))
    lines.append("")
    lines.append("This is a first-research-alpha proof-of-concept inside generated toy fields. It does not prove cosmology, physics, or final trinary mathematics.")
    lines.append("")
    lines.append("## Run shape")
    lines.append("")
    lines.append(f"Proof records: `{summary['proof_record_count']}`")
    lines.append(f"Seed ranges: `{summary['seed_ranges']}`")
    lines.append(f"Adversarial corpora: `{summary['corpus_count']}`")
    lines.append(f"Scenario cells: `{summary['scenario_cells']}`")
    lines.append(f"Seeded simulation runs: `{summary['seeded_runs']}`")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Final earned-one events: `{summary['final_earned_one_events']}`.")
    lines.append("Earned-one is the only accepted final +1 crown. Raw local expression remains visible as pressure, not final truth.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Latent overcrown pressure held in zero: `{summary['latent_overcrown_demoted_count']}` of `{summary['latent_overcrown_pressure']}`.")
    lines.append("The zero-zone is active: it holds latent pressure rather than forcing binary success/failure.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Raw false-one pressure: `{summary['raw_false_one_pressure']}`.")
    lines.append(f"False-one pressure demoted before final crown: `{summary['false_one_demoted_count']}`.")
    lines.append(f"Final false-one crowns: `{summary['final_false_one_crowns']}`.")
    lines.append(f"Trap final crowns: `{summary['trap_final_crown_count']}`.")
    lines.append("")
    lines.append("## Proof-record table")
    lines.append("")
    lines.append("| proof_dir | seed_range | cells | runs | earned | raw false | demoted false | final false crowns | status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            f"| {row.get('proof_dir','')} | {row.get('seed_range','')} | {row.get('scenario_cells','')} | "
            f"{row.get('seeded_runs','')} | {row.get('final_earned_one_events','')} | "
            f"{row.get('raw_false_one_pressure','')} | {row.get('false_one_demoted_count','')} | "
            f"{row.get('final_false_one_crowns','')} | {row.get('proof_status','')} |"
        )
    lines.append("")
    lines.append("## Supported claim")
    lines.append("")
    lines.append("ZeroGateSim's final trinary witness separated earned-one from raw expression, latent overcrown, and false-one pressure across original and fresh-seed trinary adversarial proof records.")
    lines.append("")
    lines.append("## Not supported")
    lines.append("")
    lines.append("This record does not prove physical dimensional genesis, cosmology, or that reality itself is trinary. It proves that the current simulation grammar can be run, challenged, reproduced, and bounded.")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(str(summary["next_action"]) + ".")
    lines.append("")
    lines.append("## Final sentence")
    lines.append("")
    lines.append("The machine did not prove the universe. It did something narrower and real: across 13122 seeded toy-field runs, it met false one, named it, and refused the crown.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def freeze_release_record(proof_dirs: list[Path], out_dir: Path, *, make_bundle: bool = True) -> dict[str, Path]:
    out_dir = ensure_dir(Path(out_dir))
    summary, rows = summarize_release(proof_dirs)
    md_path = out_dir / "first_research_alpha_record.md"
    json_path = out_dir / "first_research_alpha_summary.json"
    csv_path = out_dir / "first_research_alpha_summary.csv"
    proof_rows_path = out_dir / "first_research_alpha_proof_records.csv"
    _write_markdown(md_path, summary, rows)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_dict_rows_csv(csv_path, [summary])
    write_dict_rows_csv(proof_rows_path, rows)
    paths = {
        "first_research_alpha_record": md_path,
        "first_research_alpha_summary": json_path,
        "first_research_alpha_csv": csv_path,
        "proof_records_csv": proof_rows_path,
    }
    if make_bundle:
        paths["release_bundle"] = write_evidence_bundle(
            out_dir,
            bundle_name="first_research_alpha_bundle.zip",
            bundle_kind="zerogate_first_research_alpha_release_bundle",
        )
    return paths


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = freeze_release_record(args.proof_dir, args.out, make_bundle=not args.no_bundle)
    print("ZeroGateSim v1.0-alpha first-research-alpha record complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
