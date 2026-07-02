from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from zerogate_sim.belnap_mirror import (
    BELNAP_BOTH,
    BELNAP_FALSE_ONLY,
    BELNAP_NEITHER,
    BELNAP_TRUE_ONLY,
    build_belnap_mirror_rows_from_final_rows,
)
from zerogate_sim.final_output import build_final_output_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv

PARA_CONFLICT_LOCALIZED = "conflict_localized"
PARA_CONFLICT_OVERCROWNED = "conflict_overcrowned"
PARA_TRUE_WITHOUT_CONFLICT = "true_without_conflict"
PARA_FALSE_WITHOUT_CONFLICT = "false_without_conflict"
PARA_NEITHER_WITHOUT_CONFLICT = "neither_without_conflict"


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _is_final_crown(row: dict[str, object]) -> bool:
    return str(row.get("final_trinary_symbol", "")) == "+1" or str(row.get("final_band", "")) == "earned_one"


def paraconsistent_value_from_belnap_row(row: dict[str, object]) -> tuple[str, int, str]:
    """Project a Belnap evidence row into a conflict-locality mirror.

    This is not Priest logic and not a native ZeroGate gate. It asks whether a
    local conflict state remains local: positive-looking pressure plus contrary
    witness must not become final +1 merely because a contradiction exists.
    """

    belnap_value = str(row.get("belnap_value", ""))
    evidence_for = _int(row, "evidence_for_final_one")
    evidence_against = _int(row, "evidence_against_final_one")
    contradiction_load = min(evidence_for, evidence_against)

    if belnap_value == BELNAP_BOTH:
        if _is_final_crown(row):
            return PARA_CONFLICT_OVERCROWNED, 1, "local_conflict_was_crowned"
        return PARA_CONFLICT_LOCALIZED, 0, "local_conflict_held_or_demoted"
    if belnap_value == BELNAP_TRUE_ONLY:
        return PARA_TRUE_WITHOUT_CONFLICT, 0, "positive_evidence_without_contrary_witness"
    if belnap_value == BELNAP_FALSE_ONLY:
        return PARA_FALSE_WITHOUT_CONFLICT, 0, "contrary_witness_without_positive_pressure"
    if belnap_value == BELNAP_NEITHER:
        return PARA_NEITHER_WITHOUT_CONFLICT, 0, "no_decisive_pressure"
    if contradiction_load > 0:
        return PARA_CONFLICT_LOCALIZED, 0, "implicit_conflict_localized"
    return PARA_NEITHER_WITHOUT_CONFLICT, 0, "unknown_projection_state"


def build_paraconsistent_mirror_rows_from_belnap_rows(belnap_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in belnap_rows:
        value, explosion_flag, reason = paraconsistent_value_from_belnap_row(row)
        evidence_for = _int(row, "evidence_for_final_one")
        evidence_against = _int(row, "evidence_against_final_one")
        contradiction_load = min(evidence_for, evidence_against)
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "kind": row.get("kind", ""),
                "truth_role": row.get("truth_role", ""),
                "final_trinary_symbol": row.get("final_trinary_symbol", ""),
                "final_band": row.get("final_band", ""),
                "belnap_value": row.get("belnap_value", ""),
                "belnap_symbol": row.get("belnap_symbol", ""),
                "evidence_for_final_one": evidence_for,
                "evidence_against_final_one": evidence_against,
                "contradiction_load": contradiction_load,
                "positive_excess": max(0, evidence_for - evidence_against),
                "contrary_excess": max(0, evidence_against - evidence_for),
                "paraconsistent_value": value,
                "local_explosion_flag": explosion_flag,
                "locality_reason": reason,
            }
        )
    return out


def build_paraconsistent_mirror_rows_from_final_rows(final_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    belnap_rows = build_belnap_mirror_rows_from_final_rows(final_rows)
    return build_paraconsistent_mirror_rows_from_belnap_rows(belnap_rows)


def build_paraconsistent_mirror_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    return build_paraconsistent_mirror_rows_from_final_rows(build_final_output_rows(gate_rows))


def _write_paraconsistent_read(path: Path, rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["paraconsistent_value"]) for row in rows)
    conflict_rows = [row for row in rows if row["paraconsistent_value"] in {PARA_CONFLICT_LOCALIZED, PARA_CONFLICT_OVERCROWNED}]
    overcrowned = [row for row in rows if int(row.get("local_explosion_flag", 0) or 0)]
    localized = [row for row in rows if row["paraconsistent_value"] == PARA_CONFLICT_LOCALIZED]
    total_contradiction_load = sum(int(row.get("contradiction_load", 0) or 0) for row in rows)

    ranked = sorted(
        rows,
        key=lambda row: (
            0 if int(row.get("local_explosion_flag", 0) or 0) else 1 if row["paraconsistent_value"] == PARA_CONFLICT_LOCALIZED else 2,
            -int(row.get("contradiction_load", 0) or 0),
            str(row.get("candidate_id", "")),
        ),
    )

    lines: list[str] = []
    lines.append("# ZeroGateSim Paraconsistent Conflict-Locality Mirror")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a projection mirror, not an identity claim. ZeroGateSim is not Priest logic or any complete paraconsistent logic system. The mirror asks one narrow conflict-locality question: when positive-looking pressure and contrary witness coexist, does the conflict stay local instead of exploding into arbitrary final +1?")
    lines.append("")
    lines.append("## Conflict-locality rule")
    lines.append("")
    lines.append("> raw +1 plus debt must not explode into arbitrary final +1.")
    lines.append("")
    lines.append("A local conflict may be visible, useful, and worth preserving. It is still not permission to crown.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"Conflict candidates: `{len(conflict_rows)}`")
    lines.append(f"Localized conflict candidates: `{len(localized)}`")
    lines.append(f"Overcrowned conflict candidates: `{len(overcrowned)}`")
    lines.append(f"Total contradiction load: `{total_contradiction_load}`")
    lines.append("")
    lines.append("## Projection bands")
    lines.append("")
    for band, count in sorted(counts.items()):
        lines.append(f"- `{band}`: `{count}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | final | band | Belnap | para value | for | against | load | explosion | reason |")
    lines.append("|---|---|---|---|---|---|---|---:|---:|---:|---:|---|")
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['final_trinary_symbol']} | "
            f"{row['final_band']} | {row['belnap_symbol']}:{row['belnap_value']} | {row['paraconsistent_value']} | "
            f"{row['evidence_for_final_one']} | {row['evidence_against_final_one']} | {row['contradiction_load']} | "
            f"{row['local_explosion_flag']} | {row['locality_reason']} |"
        )
    lines.append("")
    lines.append("## Loss report")
    lines.append("")
    lines.append("This mirror preserves the local/nonlocal shape of conflict pressure. It does not decide native truth, does not replace the final trinary witness, and does not prove contradiction is metaphysically fundamental. A localized conflict is still pressure under witness.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if overcrowned:
        names = ", ".join(f"`{row['candidate_id']}`" for row in overcrowned[:9])
        lines.append(f"Resist: local conflict was crowned in {names}. This is a conflict-locality breach and must be inspected before any celebration.")
    elif localized:
        names = ", ".join(f"`{row['candidate_id']}`" for row in localized[:9])
        lines.append(f"Witness/Resist: conflict pressure remained local in {names}. The mirror sees contradiction without turning it into final +1.")
    else:
        lines.append("Witness: no explicit conflict-locality pressure appeared in this run. This is not proof of safety; it means this mirror found no Belnap-both state to localize.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_paraconsistent_mirror_outputs(
    output_dir: Path,
    final_rows: Iterable[dict[str, object]] | None = None,
    gate_rows: list[tuple[int, GateScores]] | None = None,
) -> dict[str, Path]:
    if final_rows is None:
        if gate_rows is None:
            raise ValueError("provide final_rows or gate_rows")
        rows = build_paraconsistent_mirror_rows(gate_rows)
    else:
        rows = build_paraconsistent_mirror_rows_from_final_rows(final_rows)

    csv_path = output_dir / "matrix_paraconsistent_mirror_summary.csv"
    read_path = output_dir / "matrix_paraconsistent_mirror_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_paraconsistent_read(read_path, rows)
    return {
        "matrix_paraconsistent_mirror_summary": csv_path,
        "matrix_paraconsistent_mirror_read": read_path,
    }
