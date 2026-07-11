from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.11-alpha"
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


def _strict_int(value: object, *, field: str, source: Path) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{source}: missing required numeric field {field!r}")
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source}: malformed numeric field {field!r}: {value!r}") from exc
    if not number.is_integer():
        raise ValueError(f"{source}: non-integral count field {field!r}: {value!r}")
    return int(number)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: empty matrix final-output summary")
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matrix_totals(path: Path) -> dict[str, object]:
    rows = _read_csv(path)
    totals = {field: 0 for field in COUNT_FIELDS}
    opportunities = 0
    final_false_one_crowns = 0
    canonical_rows: list[dict[str, object]] = []
    seen_candidate_ids: set[str] = set()
    for row in rows:
        runs = _strict_int(row.get("runs"), field="runs", source=path)
        if runs <= 0:
            raise ValueError(f"{path}: runs must be positive")
        opportunities += runs
        counts: dict[str, int] = {}
        for field in COUNT_FIELDS:
            count = _strict_int(row.get(field), field=field, source=path)
            if count < 0 or count > runs:
                raise ValueError(f"{path}: {field} must satisfy 0 <= count <= runs")
            counts[field] = count
            totals[field] += count
        if counts["false_one_demoted_count"] != counts["raw_false_one_pressure"]:
            raise ValueError(f"{path}: false-one pressure/demotion counts disagree")
        if counts["latent_overcrown_demoted_count"] != counts["latent_overcrown_pressure"]:
            raise ValueError(f"{path}: latent pressure/demotion counts disagree")
        partition = (
            counts["final_earned_one_count"]
            + counts["raw_false_one_pressure"]
            + counts["latent_overcrown_pressure"]
            + counts["relation_debt_count"]
            + counts["return_debt_count"]
        )
        if partition != counts["raw_expression_pressure"]:
            raise ValueError(f"{path}: final lane counts do not partition raw expression")
        truth_role = str(row.get("truth_role", "")).strip().lower()
        final_symbol = str(row.get("final_trinary_symbol", "")).strip()
        final_value = str(row.get("final_trinary_value", "")).strip()
        if truth_role == "trap" and (final_symbol == "+1" or final_value == "1"):
            final_false_one_crowns += max(
                1,
                _strict_int(row.get("final_earned_one_count"), field="final_earned_one_count", source=path),
            )
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            raise ValueError(f"{path}: candidate_id is required")
        if candidate_id in seen_candidate_ids:
            raise ValueError(f"{path}: duplicate candidate_id {candidate_id!r}")
        seen_candidate_ids.add(candidate_id)
        canonical_rows.append(
            {
                "candidate_id": candidate_id,
                "truth_role": truth_role,
                "final_trinary_symbol": final_symbol,
                "final_trinary_value": _strict_int(
                    row.get("final_trinary_value"),
                    field="final_trinary_value",
                    source=path,
                ),
                "runs": runs,
                **counts,
            }
        )
    semantic_payload = json.dumps(
        sorted(canonical_rows, key=lambda row: str(row["candidate_id"])),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "matrix": path.parent.name,
        "path": str(path),
        "source_sha256": _sha256(path),
        "semantic_sha256": hashlib.sha256(semantic_payload).hexdigest(),
        "candidate_rows": len(rows),
        "opportunities": opportunities,
        **totals,
        "final_false_one_crowns": final_false_one_crowns,
    }


def _legacy_lane_presence(row: dict[str, object]) -> bool:
    return (
        int(row["final_false_one_crowns"]) == 0
        and int(row["final_earned_one_events"]) > 0
        and int(row["raw_expression_pressure"]) > 0
        and int(row["latent_overcrown"]) > 0
        and int(row["relation_debt"]) > 0
        and int(row["return_debt"]) > 0
        and int(row["false_one_pressure"]) > 0
    )


def _write_read(path: Path, row: dict[str, object]) -> None:
    lines = [
        f"# v1.7.11 {row['weather_rung']} Rung Accounting Summary",
        "",
        "**Scientific status:** `HOLD_CONSTRUCTION_BOUND`",
        "",
        "This is a denominated accounting view of the legacy role-aware harness. It is not a blind-witness pass, core-question closeout, or role-blind discovery result.",
        "",
        f"Native witness: `{NATIVE_WITNESS}`",
        "",
        "| lane | count | rate over opportunities |",
        "|---|---:|---:|",
        f"| +1 earned-one | {row['final_earned_one_events']} | {float(row['earned_one_rate']):.6%} |",
        f"| raw expression pressure | {row['raw_expression_pressure']} | {float(row['raw_expression_rate']):.6%} |",
        f"| 0 latent overcrown | {row['latent_overcrown']} | {float(row['latent_overcrown_rate']):.6%} |",
        f"| 0 relation debt | {row['relation_debt']} | {float(row['relation_debt_rate']):.6%} |",
        f"| 0 return debt | {row['return_debt']} | {float(row['return_debt_rate']):.6%} |",
        f"| -1 false-one pressure | {row['false_one_pressure']} | {float(row['false_one_pressure_rate']):.6%} |",
        f"| final false-one crowns | {row['final_false_one_crowns']} | {float(row['final_false_one_crown_rate']):.6%} |",
        "",
        f"Opportunity denominator: `{row['opportunities']}`.",
        f"Duplicate matrix artifacts supplied: `{row['duplicate_input_artifact_count']}`.",
        "",
        "Masking, frozen-manifest status, and reference independence are `not_verified` because aggregate final-output CSVs cannot prove them. A false handoff is a false crown.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_top_card(path: Path, row: dict[str, object]) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {row['weather_rung']} Accounting Top Card",
                "",
                "**Status:** `HOLD_CONSTRUCTION_BOUND`",
                f"**Opportunities:** `{row['opportunities']}`",
                f"**Earned-one:** `{row['final_earned_one_events']}` ({float(row['earned_one_rate']):.6%})",
                f"**False-one pressure:** `{row['false_one_pressure']}` ({float(row['false_one_pressure_rate']):.6%})",
                f"**Final false-one crowns:** `{row['final_false_one_crowns']}`",
                "",
                "Legacy lane presence is descriptive only. Provenance and blindness are not established by this aggregate.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_html(path: Path, row: dict[str, object]) -> None:
    def e(value: object) -> str:
        return html.escape(str(value))

    cards = [
        ("opportunities", row["opportunities"]),
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
        f"<!doctype html><meta charset='utf-8'><title>{e(row['weather_rung'])} accounting</title>"
        f"<body><h1>{e(row['weather_rung'])} accounting</h1><p>HOLD_CONSTRUCTION_BOUND</p>{body}"
        "<p>Aggregate role-aware accounting only; provenance claims are not verified.</p></body>",
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
    if rung not in {"triad27", "deep81", "wide243"}:
        raise ValueError(f"unsupported rung {rung!r}")
    if count <= 0:
        raise ValueError("count must be positive")
    out_dir = ensure_dir(Path(out))
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}
    supplied_paths = [Path(path) for path in matrix_final_outputs]
    if not supplied_paths:
        raise ValueError("at least one matrix final-output CSV is required")

    all_totals = [_matrix_totals(path) for path in supplied_paths]
    unique_totals: list[dict[str, object]] = []
    seen_hashes: set[str] = set()
    for total in all_totals:
        source_hash = str(total["semantic_sha256"])
        duplicate = source_hash in seen_hashes
        total["duplicate_content"] = str(duplicate).lower()
        if duplicate:
            continue
        seen_hashes.add(source_hash)
        unique_totals.append(total)

    aggregate = {field: sum(int(row[field]) for row in unique_totals) for field in COUNT_FIELDS}
    opportunities = sum(int(row["opportunities"]) for row in unique_totals)
    if opportunities <= 0:
        raise ValueError("opportunity denominator must be positive")
    final_false_one_crowns = sum(int(row["final_false_one_crowns"]) for row in unique_totals)
    duplicate_count = len(all_totals) - len(unique_totals)
    seed_block = f"{start_seed}-{start_seed + count - 1}"
    row: dict[str, object] = {
        "holdout_run_id": f"v1_7_11_{rung}_seed_{seed_block.replace('-', '_')}",
        "weather_rung": rung,
        "fresh_seed_block": seed_block,
        "evidence_mode": "legacy_aggregate_accounting_only",
        "scientific_status": "HOLD_CONSTRUCTION_BOUND",
        "provenance_status": "not_verified_from_aggregate_csv",
        "candidate_names_masked": "not_verified",
        "expected_manifest_frozen": "not_verified",
        "reference_profile_reused": "not_verified",
        "earned_controls_present": "observed_after_label_join" if aggregate["final_earned_one_count"] > 0 else "not_observed",
        "lane_pattern_matches_expected": "not_a_pass_condition",
        "input_artifact_count": len(all_totals),
        "unique_input_artifact_count": len(unique_totals),
        "duplicate_input_artifact_count": duplicate_count,
        "opportunities": opportunities,
        "final_earned_one_events": aggregate["final_earned_one_count"],
        "raw_expression_pressure": aggregate["raw_expression_pressure"],
        "latent_overcrown": aggregate["latent_overcrown_pressure"],
        "relation_debt": aggregate["relation_debt_count"],
        "return_debt": aggregate["return_debt_count"],
        "false_one_pressure": aggregate["raw_false_one_pressure"],
        "final_false_one_crowns": final_false_one_crowns,
    }
    row["legacy_lane_presence_observed"] = str(_legacy_lane_presence(row)).lower()
    row["earned_one_rate"] = int(row["final_earned_one_events"]) / opportunities
    row["raw_expression_rate"] = int(row["raw_expression_pressure"]) / opportunities
    row["latent_overcrown_rate"] = int(row["latent_overcrown"]) / opportunities
    row["relation_debt_rate"] = int(row["relation_debt"]) / opportunities
    row["return_debt_rate"] = int(row["return_debt"]) / opportunities
    row["false_one_pressure_rate"] = int(row["false_one_pressure"]) / opportunities
    row["final_false_one_crown_rate"] = final_false_one_crowns / opportunities

    write_dict_rows_csv(paths["row"], [row])
    write_dict_rows_csv(paths["matrix_totals"], all_totals)
    _write_read(paths["read"], row)
    _write_top_card(paths["top_card"], row)
    _write_html(paths["html_card"], row)
    paths["full_report"].write_text(
        paths["read"].read_text(encoding="utf-8") + "\nSee matrix totals CSV for source hashes and duplicate diagnostics.\n",
        encoding="utf-8",
    )
    paths["summary_json"].write_text(
        json.dumps({"row": row, "matrix_totals": all_totals}, indent=2) + "\n",
        encoding="utf-8",
    )
    decision = {
        "version": CURRENT_VERSION,
        "native_witness": NATIVE_WITNESS,
        "decision": "hold_legacy_aggregate_not_integrity_verified",
        "scientific_status": "HOLD_CONSTRUCTION_BOUND",
        "core_question_closed": False,
        "provenance_verified": False,
        "lane_pattern_matches_expected": False,
        "legacy_lane_presence_observed": row["legacy_lane_presence_observed"] == "true",
        "accounting_status": "invalid_duplicate_inputs" if duplicate_count else "unique_within_supplied_artifacts",
        "opportunities": opportunities,
        "duplicate_input_artifact_count": duplicate_count,
        "final_false_one_crowns": final_false_one_crowns,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    paths["bundle"] = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="v1_7_11_holdout_rung_accounting_bundle",
    )
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a fail-closed v1.7.11 rung accounting summary from legacy matrix final-output CSVs.")
    parser.add_argument("--rung", choices=["triad27", "deep81", "wide243"], required=True)
    parser.add_argument("--start-seed", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--matrix-final-output", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = build_v1_7_holdout_rung_summary(
        args.out,
        rung=args.rung,
        start_seed=args.start_seed,
        count=args.count,
        matrix_final_outputs=args.matrix_final_output,
    )
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
