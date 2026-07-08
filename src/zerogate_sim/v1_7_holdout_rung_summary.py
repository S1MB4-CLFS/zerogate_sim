from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.10-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"

OUTPUT_FILES = {
    "row": "v1_7_holdout_rung_row.csv",
    "read": "v1_7_holdout_rung_summary_read.md",
    "top_card": "v1_7_holdout_rung_top_card.md",
    "full_report": "v1_7_holdout_rung_full_output_report.md",
    "matrix_totals": "v1_7_holdout_rung_matrix_totals.csv",
    "html_card": "v1_7_holdout_rung_top_card.html",
    "summary_json": "v1_7_holdout_rung_summary.json",
    "decision": "v1_7_holdout_rung_summary_decision.json",
    "bundle": "v1_7_holdout_rung_summary_bundle.zip",
}

ROW_FIELDS = [
    "holdout_run_id",
    "weather_rung",
    "fresh_seed_block",
    "candidate_names_masked",
    "expected_manifest_frozen",
    "reference_profile_reused",
    "earned_controls_present",
    "lane_pattern_matches_expected",
    "final_earned_one_events",
    "raw_expression_pressure",
    "latent_overcrown",
    "relation_debt",
    "return_debt",
    "false_one_pressure",
    "final_false_one_crowns",
]

COUNT_FIELDS = [
    "raw_expression_pressure",
    "final_earned_one_count",
    "raw_false_one_pressure",
    "false_one_demoted_count",
    "latent_overcrown_pressure",
    "latent_overcrown_demoted_count",
    "relation_debt_count",
    "return_debt_count",
]


def _intish(value: object) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _matrix_totals(path: Path) -> dict[str, object]:
    rows = _read_csv(path)
    totals = {field: 0 for field in COUNT_FIELDS}
    final_false_one_crowns = 0
    for row in rows:
        for field in COUNT_FIELDS:
            totals[field] += _intish(row.get(field))
        truth_role = str(row.get("truth_role", "")).strip().lower()
        final_symbol = str(row.get("final_trinary_symbol", "")).strip()
        final_value = str(row.get("final_trinary_value", "")).strip()
        if truth_role == "trap" and (final_symbol == "+1" or final_value == "1"):
            final_false_one_crowns += max(1, _intish(row.get("final_earned_one_count")))
    return {
        "matrix": path.parent.name,
        "path": str(path),
        "candidate_rows": len(rows),
        **totals,
        "final_false_one_crowns": final_false_one_crowns,
    }


def _lane_pattern(row: dict[str, object]) -> bool:
    return (
        _intish(row["final_false_one_crowns"]) == 0
        and _intish(row["final_earned_one_events"]) > 0
        and _intish(row["raw_expression_pressure"]) > 0
        and _intish(row["latent_overcrown"]) > 0
        and _intish(row["relation_debt"]) > 0
        and _intish(row["return_debt"]) > 0
        and _intish(row["false_one_pressure"]) > 0
    )


def _write_read(path: Path, row: dict[str, object]) -> None:
    lines = [
        f"# v1.7 {row['weather_rung']} Holdout Rung Summary",
        "",
        "This is a controlled synthetic-field rung summary. It is not core-question closeout and not role-blind discovery.",
        "",
        f"Native witness: `{NATIVE_WITNESS}`",
        "",
        "| lane | count |",
        "|---|---:|",
        f"| +1 earned-one | {row['final_earned_one_events']} |",
        f"| raw expression pressure | {row['raw_expression_pressure']} |",
        f"| 0 latent overcrown | {row['latent_overcrown']} |",
        f"| 0 relation debt | {row['relation_debt']} |",
        f"| 0 return debt | {row['return_debt']} |",
        f"| -1 false-one pressure | {row['false_one_pressure']} |",
        f"| final false-one crowns | {row['final_false_one_crowns']} |",
        "",
        "Boundary: controlled synthetic-field evidence only. A false handoff is a false crown.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_top_card(path: Path, row: dict[str, object]) -> None:
    status = "WITNESS" if row["lane_pattern_matches_expected"] == "true" else "HOLD"
    path.write_text(
        "\n".join([
            f"# {row['weather_rung']} Holdout Top Card",
            "",
            f"**Status:** `{status}`",
            f"**Final false-one crowns:** `{row['final_false_one_crowns']}`",
            f"**Earned-one:** `{row['final_earned_one_events']}`",
            f"**False-one pressure:** `{row['false_one_pressure']}`",
            "",
            "No core-question closeout here. Inspect before moving deeper.",
        ]) + "\n",
        encoding="utf-8",
    )


def _write_html(path: Path, row: dict[str, object]) -> None:
    def e(value: object) -> str:
        return html.escape(str(value))
    cards = [
        ("+1 earned-one", row["final_earned_one_events"]),
        ("raw pressure", row["raw_expression_pressure"]),
        ("0 latent", row["latent_overcrown"]),
        ("0 relation debt", row["relation_debt"]),
        ("0 return debt", row["return_debt"]),
        ("-1 false pressure", row["false_one_pressure"]),
        ("final false crowns", row["final_false_one_crowns"]),
    ]
    body = "".join(f"<div><b>{e(label)}</b><br>{e(value)}</div>" for label, value in cards)
    path.write_text(
        f"<!doctype html><meta charset='utf-8'><title>{e(row['weather_rung'])} holdout</title><body><h1>{e(row['weather_rung'])} holdout rung</h1>{body}<p>Controlled synthetic-field evidence only.</p></body>",
        encoding="utf-8",
    )


def build_v1_7_holdout_rung_summary(
    out: str | Path,
    *,
    rung: str,
    start_seed: int,
    count: int,
    matrix_final_outputs: Iterable[str | Path],
) -> dict[str, Path]:
    out_dir = ensure_dir(Path(out))
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}
    totals = [_matrix_totals(Path(path)) for path in matrix_final_outputs]
    aggregate = {field: sum(_intish(row.get(field)) for row in totals) for field in COUNT_FIELDS}
    final_false_one_crowns = sum(_intish(row.get("final_false_one_crowns")) for row in totals)
    seed_block = f"{start_seed}-{start_seed + count - 1}"
    row: dict[str, object] = {
        "holdout_run_id": f"v1_7_9_{rung}_seed_{seed_block.replace('-', '_')}",
        "weather_rung": rung,
        "fresh_seed_block": seed_block,
        "candidate_names_masked": "true",
        "expected_manifest_frozen": "true",
        "reference_profile_reused": "false",
        "earned_controls_present": "true",
        "final_earned_one_events": aggregate["final_earned_one_count"],
        "raw_expression_pressure": aggregate["raw_expression_pressure"],
        "latent_overcrown": aggregate["latent_overcrown_pressure"],
        "relation_debt": aggregate["relation_debt_count"],
        "return_debt": aggregate["return_debt_count"],
        "false_one_pressure": aggregate["raw_false_one_pressure"],
        "final_false_one_crowns": final_false_one_crowns,
    }
    row["lane_pattern_matches_expected"] = "true" if _lane_pattern(row) else "false"
    write_dict_rows_csv(paths["row"], [row])
    write_dict_rows_csv(paths["matrix_totals"], totals)
    _write_read(paths["read"], row)
    _write_top_card(paths["top_card"], row)
    _write_html(paths["html_card"], row)
    paths["full_report"].write_text(paths["read"].read_text(encoding="utf-8") + "\nSee matrix totals CSV for per-matrix counts.\n", encoding="utf-8")
    paths["summary_json"].write_text(json.dumps({"row": row, "matrix_totals": totals}, indent=2) + "\n", encoding="utf-8")
    decision = {
        "version": CURRENT_VERSION,
        "native_witness": NATIVE_WITNESS,
        "core_question_closed": False,
        "rung": rung,
        "lane_pattern_matches_expected": row["lane_pattern_matches_expected"] == "true",
        "final_false_one_crowns": final_false_one_crowns,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    paths["bundle"] = write_evidence_bundle(out_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="v1_7_holdout_rung_summary_bundle")
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a v1.7 holdout rung summary from matrix final-output CSVs.")
    parser.add_argument("--rung", choices=["triad27", "deep81", "wide243"], required=True)
    parser.add_argument("--start-seed", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--matrix-final-output", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = build_v1_7_holdout_rung_summary(args.out, rung=args.rung, start_seed=args.start_seed, count=args.count, matrix_final_outputs=args.matrix_final_output)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
