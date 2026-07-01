from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from zerogate_sim.final_output import build_final_output_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv

BELNAP_TRUE_ONLY = "true_only"
BELNAP_FALSE_ONLY = "false_only"
BELNAP_BOTH = "both"
BELNAP_NEITHER = "neither"

BELNAP_SYMBOLS = {
    BELNAP_TRUE_ONLY: "T",
    BELNAP_FALSE_ONLY: "F",
    BELNAP_BOTH: "B",
    BELNAP_NEITHER: "N",
}


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _evidence_counts(row: dict[str, object]) -> tuple[int, int, list[str], list[str]]:
    """Return evidence-for and evidence-against counts for final +1.

    This is a Belnap-style evidence mirror, not native ZeroGate logic. Raw
    expression counts as evidence-for expression pressure. False-one demotion,
    latent overcrown, relation debt, and clean containment count as evidence
    against final earned-one depending on the final band.
    """

    raw = _int(row, "raw_expression_pressure")
    earned = _int(row, "final_earned_one_count")
    false_pressure = _int(row, "raw_false_one_pressure")
    false_demoted = _int(row, "false_one_demoted_count")
    latent = _int(row, "latent_overcrown_pressure")
    relation_debt = _int(row, "relation_debt_count")
    final_band = str(row.get("final_band", ""))

    evidence_for = 0
    evidence_against = 0
    for_reasons: list[str] = []
    against_reasons: list[str] = []

    if earned > 0:
        evidence_for += earned
        for_reasons.append("earned_one")
    elif raw > 0:
        evidence_for += raw
        for_reasons.append("raw_expression_pressure")

    if false_pressure > 0 or false_demoted > 0:
        evidence_against += max(false_pressure, false_demoted)
        against_reasons.append("false_one_demoted")
    if latent > 0:
        evidence_against += latent
        against_reasons.append("latent_overcrown_hold")
    if relation_debt > 0:
        evidence_against += relation_debt
        against_reasons.append("relation_debt_hold")
    if raw <= 0 and final_band in {"trap_contained", "expresser_wound"}:
        evidence_against += 1
        against_reasons.append(final_band)

    return evidence_for, evidence_against, for_reasons, against_reasons


def belnap_value_from_final_row(row: dict[str, object]) -> tuple[str, str, str]:
    """Project one final-output row into a Belnap evidence state.

    T / true_only: evidence for final +1 without current contrary pressure.
    F / false_only: evidence against final +1 without current positive pressure.
    B / both: positive-looking expression pressure plus contrary witness.
    N / neither: no decisive evidence-for or evidence-against final +1.
    """

    evidence_for, evidence_against, for_reasons, against_reasons = _evidence_counts(row)
    if evidence_for > 0 and evidence_against > 0:
        value = BELNAP_BOTH
    elif evidence_for > 0:
        value = BELNAP_TRUE_ONLY
    elif evidence_against > 0:
        value = BELNAP_FALSE_ONLY
    else:
        value = BELNAP_NEITHER

    reason_parts: list[str] = []
    if for_reasons:
        reason_parts.append("for=" + "+".join(for_reasons))
    if against_reasons:
        reason_parts.append("against=" + "+".join(against_reasons))
    reason = "; ".join(reason_parts) if reason_parts else "no_decisive_evidence"
    return value, BELNAP_SYMBOLS[value], reason


def build_belnap_mirror_rows_from_final_rows(final_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in final_rows:
        evidence_for, evidence_against, for_reasons, against_reasons = _evidence_counts(row)
        value, symbol, reason = belnap_value_from_final_row(row)
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "kind": row.get("kind", ""),
                "truth_role": row.get("truth_role", ""),
                "runs": row.get("runs", 0),
                "raw_expression_pressure": row.get("raw_expression_pressure", 0),
                "final_earned_one_count": row.get("final_earned_one_count", 0),
                "raw_false_one_pressure": row.get("raw_false_one_pressure", 0),
                "latent_overcrown_pressure": row.get("latent_overcrown_pressure", 0),
                "relation_debt_count": row.get("relation_debt_count", 0),
                "final_trinary_symbol": row.get("final_trinary_symbol", ""),
                "final_band": row.get("final_band", ""),
                "evidence_for_final_one": evidence_for,
                "evidence_against_final_one": evidence_against,
                "evidence_for_reasons": "+".join(for_reasons) or "none",
                "evidence_against_reasons": "+".join(against_reasons) or "none",
                "belnap_value": value,
                "belnap_symbol": symbol,
                "belnap_reason": reason,
            }
        )
    return out


def build_belnap_mirror_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    return build_belnap_mirror_rows_from_final_rows(build_final_output_rows(gate_rows))


def _write_belnap_read(path: Path, rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["belnap_value"]) for row in rows)
    both_rows = [row for row in rows if row["belnap_value"] == BELNAP_BOTH]
    true_rows = [row for row in rows if row["belnap_value"] == BELNAP_TRUE_ONLY]
    false_rows = [row for row in rows if row["belnap_value"] == BELNAP_FALSE_ONLY]
    neither_rows = [row for row in rows if row["belnap_value"] == BELNAP_NEITHER]

    ranked = sorted(
        rows,
        key=lambda row: (
            0 if row["belnap_value"] == BELNAP_BOTH else 1 if row["belnap_value"] == BELNAP_FALSE_ONLY else 2,
            -int(row.get("evidence_against_final_one", 0) or 0),
            -int(row.get("evidence_for_final_one", 0) or 0),
            str(row.get("candidate_id", "")),
        ),
    )

    lines: list[str] = []
    lines.append("# ZeroGateSim Belnap Evidence-State Mirror")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a projection mirror, not an identity claim. ZeroGateSim is not Belnap-Dunn logic. The mirror asks how final-output evidence appears when separated into evidence-for final +1, evidence-against final +1, both, or neither.")
    lines.append("")
    lines.append("## Mirror values")
    lines.append("")
    lines.append("- `T` / `true_only`: evidence for final +1 without current contrary pressure.")
    lines.append("- `F` / `false_only`: evidence against final +1 without current positive expression pressure.")
    lines.append("- `B` / `both`: raw positive-looking pressure and contrary witness are both present.")
    lines.append("- `N` / `neither`: no decisive evidence-for or evidence-against final +1 in this mirror.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"True-only candidates: `{len(true_rows)}`")
    lines.append(f"False-only candidates: `{len(false_rows)}`")
    lines.append(f"Both / conflict-pressure candidates: `{len(both_rows)}`")
    lines.append(f"Neither candidates: `{len(neither_rows)}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | final | band | Belnap | for | against | reason |")
    lines.append("|---|---|---|---|---|---|---:|---:|---|")
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['final_trinary_symbol']} | "
            f"{row['final_band']} | {row['belnap_symbol']}:{row['belnap_value']} | "
            f"{row['evidence_for_final_one']} | {row['evidence_against_final_one']} | {row['belnap_reason']} |"
        )
    lines.append("")
    lines.append("## Loss report")
    lines.append("")
    lines.append("The Belnap mirror preserves whether positive and contrary evidence coexist. It does not preserve the whole native ZeroGate witness stack by itself: return-depth, temporal lineage, echo-independence, and the final trinary output remain native mechanisms. A `B` state is pressure under conflict, not permission to crown.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if both_rows:
        names = ", ".join(f"`{row['candidate_id']}`" for row in both_rows[:9])
        lines.append(f"Witness/Resist: conflict-pressure exists in {names}. These candidates carry positive-looking pressure and contrary witness at the same time; the mirror makes that local conflict visible without turning it into final +1.")
    elif counts.get(BELNAP_TRUE_ONLY, 0):
        lines.append("Expand: no Belnap both-state conflict appeared; true-only evidence remains visible. This does not prove equivalence, only that this run did not expose a conflict-pressure wound.")
    else:
        lines.append("Witness: the mirror found no true-only or both-state pressure. Read the final output and native reports before interpreting this as failure or safety.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_belnap_mirror_outputs(output_dir: Path, final_rows: Iterable[dict[str, object]] | None = None, gate_rows: list[tuple[int, GateScores]] | None = None) -> dict[str, Path]:
    if final_rows is None:
        if gate_rows is None:
            raise ValueError("provide final_rows or gate_rows")
        rows = build_belnap_mirror_rows(gate_rows)
    else:
        rows = build_belnap_mirror_rows_from_final_rows(final_rows)

    csv_path = output_dir / "matrix_belnap_mirror_summary.csv"
    read_path = output_dir / "matrix_belnap_mirror_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_belnap_read(read_path, rows)
    return {
        "matrix_belnap_mirror_summary": csv_path,
        "matrix_belnap_mirror_read": read_path,
    }
