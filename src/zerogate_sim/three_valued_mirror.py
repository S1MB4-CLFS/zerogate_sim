from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from zerogate_sim.final_output import build_final_output_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv

THREE_TRUE = "true"
THREE_FALSE = "false"
THREE_UNKNOWN = "unknown"

THREE_SYMBOLS = {
    THREE_TRUE: "T",
    THREE_FALSE: "F",
    THREE_UNKNOWN: "U",
}


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _project_final_symbol(row: dict[str, object]) -> tuple[str, str, str]:
    """Project one final-output row into a three-valued compression mirror.

    This is not full Kleene K3 or Lukasiewicz L3 semantics. It is the first
    value-level compression mirror: final +1 becomes true, final -1 becomes
    false, and every final 0-state becomes unknown. The loss report is the
    point: native ZeroGateSim zero grammar is richer than this compression.
    """

    symbol = str(row.get("final_trinary_symbol", ""))
    final_band = str(row.get("final_band", ""))

    if symbol == "+1" or final_band == "earned_one":
        return THREE_TRUE, THREE_SYMBOLS[THREE_TRUE], "final_earned_one_projects_to_true"
    if symbol == "-1":
        return THREE_FALSE, THREE_SYMBOLS[THREE_FALSE], "final_resist_projects_to_false"
    return THREE_UNKNOWN, THREE_SYMBOLS[THREE_UNKNOWN], "final_zero_projects_to_unknown"


def _loss_band(row: dict[str, object], value: str) -> tuple[int, str]:
    final_band = str(row.get("final_band", ""))
    raw = _int(row, "raw_expression_pressure")
    latent = _int(row, "latent_overcrown_pressure")
    relation_debt = _int(row, "relation_debt_count")

    if value != THREE_UNKNOWN:
        return 0, "no_zero_compression_loss"

    if final_band == "relation_debt_hold" or relation_debt > 0:
        return 1, "relation_debt_collapsed_to_unknown"
    if final_band == "latent_overcrown_demoted" or latent > 0:
        return 1, "latent_overcrown_collapsed_to_unknown"
    if final_band == "expresser_wound":
        return 1, "expresser_wound_collapsed_to_unknown"
    if final_band == "latent_contained":
        return 1, "latent_contained_collapsed_to_unknown"
    if raw > 0:
        return 1, "raw_pressure_zero_collapsed_to_unknown"
    return 1, "zero_hold_collapsed_to_unknown"


def build_three_valued_mirror_rows_from_final_rows(final_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in final_rows:
        value, symbol, reason = _project_final_symbol(row)
        loss_flag, loss_band = _loss_band(row, value)
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "kind": row.get("kind", ""),
                "truth_role": row.get("truth_role", ""),
                "runs": row.get("runs", 0),
                "final_trinary_symbol": row.get("final_trinary_symbol", ""),
                "final_band": row.get("final_band", ""),
                "raw_expression_pressure": row.get("raw_expression_pressure", 0),
                "final_earned_one_count": row.get("final_earned_one_count", 0),
                "raw_false_one_pressure": row.get("raw_false_one_pressure", 0),
                "latent_overcrown_pressure": row.get("latent_overcrown_pressure", 0),
                "relation_debt_count": row.get("relation_debt_count", 0),
                "kleene_value": value,
                "kleene_symbol": symbol,
                "lukasiewicz_value": value,
                "lukasiewicz_symbol": symbol,
                "projection_reason": reason,
                "zero_compression_loss_flag": loss_flag,
                "zero_compression_loss_band": loss_band,
            }
        )
    return out


def build_three_valued_mirror_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    return build_three_valued_mirror_rows_from_final_rows(build_final_output_rows(gate_rows))


def _write_three_valued_read(path: Path, rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["kleene_value"]) for row in rows)
    loss_counts = Counter(str(row["zero_compression_loss_band"]) for row in rows)
    unknown_rows = [row for row in rows if row["kleene_value"] == THREE_UNKNOWN]
    loss_rows = [row for row in rows if int(row.get("zero_compression_loss_flag", 0) or 0)]
    distinct_zero_bands = sorted({str(row.get("final_band", "")) for row in unknown_rows})

    ranked = sorted(
        rows,
        key=lambda row: (
            0 if int(row.get("zero_compression_loss_flag", 0) or 0) else 1,
            str(row.get("kleene_value", "")),
            str(row.get("candidate_id", "")),
        ),
    )

    lines: list[str] = []
    lines.append("# ZeroGateSim Kleene / Lukasiewicz Compression Mirror")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a projection mirror, not an identity claim. ZeroGateSim is not Kleene K3 logic and not Lukasiewicz L3 logic. This first mirror only asks what is lost when native final trinary output is compressed to true / unknown / false.")
    lines.append("")
    lines.append("## Compression rule")
    lines.append("")
    lines.append("- final `+1` earned-one -> `T` true")
    lines.append("- final `0` witness / hold / debt / wound -> `U` unknown")
    lines.append("- final `-1` resist / reject / demotion -> `F` false")
    lines.append("")
    lines.append("Kleene and Lukasiewicz systems differ in their full truth tables and implication behavior. This file does not implement those full systems. It records the value-level compression and the loss report needed before any deeper truth-table comparison.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"True projections: `{counts.get(THREE_TRUE, 0)}`")
    lines.append(f"Unknown projections: `{counts.get(THREE_UNKNOWN, 0)}`")
    lines.append(f"False projections: `{counts.get(THREE_FALSE, 0)}`")
    lines.append(f"Zero-compression loss candidates: `{len(loss_rows)}`")
    lines.append("")
    lines.append("## Native zero bands collapsed into U")
    lines.append("")
    if distinct_zero_bands:
        for band in distinct_zero_bands:
            lines.append(f"- `{band}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Loss bands")
    lines.append("")
    for band, count in sorted(loss_counts.items()):
        lines.append(f"- `{band}`: `{count}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | final | band | K3 | L3 | loss | reason |")
    lines.append("|---|---|---|---|---|---|---|---:|---|")
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['final_trinary_symbol']} | "
            f"{row['final_band']} | {row['kleene_symbol']}:{row['kleene_value']} | "
            f"{row['lukasiewicz_symbol']}:{row['lukasiewicz_value']} | {row['zero_compression_loss_flag']} | "
            f"{row['zero_compression_loss_band']} |"
        )
    lines.append("")
    lines.append("## Loss report")
    lines.append("")
    lines.append("This mirror intentionally collapses native ZeroGateSim zero grammar into a single unknown value. It cannot preserve the difference between latent containment, relation debt, expresser wound, fertile/witness/quarantine posture, or any future 0+ / 0 / 0- distinction that is still visible in native reports.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if loss_rows:
        names = ", ".join(f"`{row['candidate_id']}`" for row in loss_rows[:9])
        lines.append(f"Witness: compression loss is present in {names}. The three-valued mirror is useful precisely because it shows how much native zero information disappears when everything held is called unknown.")
    else:
        lines.append("Witness: no zero-compression loss appeared in this run. That does not prove equivalence; it means this field did not expose a held-state compression wound.")
    lines.append("")
    lines.append("A three-valued mirror can compress final posture. It cannot replace the native ZeroGate witness stack.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_three_valued_mirror_outputs(
    output_dir: Path,
    final_rows: Iterable[dict[str, object]] | None = None,
    gate_rows: list[tuple[int, GateScores]] | None = None,
) -> dict[str, Path]:
    if final_rows is None:
        if gate_rows is None:
            raise ValueError("provide final_rows or gate_rows")
        rows = build_three_valued_mirror_rows(gate_rows)
    else:
        rows = build_three_valued_mirror_rows_from_final_rows(final_rows)

    csv_path = output_dir / "matrix_three_valued_mirror_summary.csv"
    read_path = output_dir / "matrix_three_valued_mirror_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_three_valued_read(read_path, rows)
    return {
        "matrix_three_valued_mirror_summary": csv_path,
        "matrix_three_valued_mirror_read": read_path,
    }
