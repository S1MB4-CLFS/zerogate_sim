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
from zerogate_sim.fuzzy_mirror import build_fuzzy_mirror_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.paraconsistent_mirror import (
    PARA_CONFLICT_LOCALIZED,
    PARA_CONFLICT_OVERCROWNED,
    build_paraconsistent_mirror_rows_from_final_rows,
)
from zerogate_sim.reporting import write_dict_rows_csv
from zerogate_sim.three_valued_mirror import THREE_UNKNOWN, build_three_valued_mirror_rows_from_final_rows


def _count(rows: Iterable[dict[str, object]], key: str, value: object) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def _sum_int(rows: Iterable[dict[str, object]], key: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get(key, 0) or 0)
        except (TypeError, ValueError):
            continue
    return total


def build_known_logic_closeout_rows(
    gate_rows: list[tuple[int, GateScores]],
    *,
    threshold: float = 0.55,
) -> list[dict[str, object]]:
    """Build the v1.3 mirror closeout rows.

    This is not a new logic mirror. It summarizes the four projection mirrors so
    the v1.3 line can close with an explicit loss report before wider comparison
    work begins.
    """

    final_rows = build_final_output_rows(gate_rows)
    fuzzy_rows = build_fuzzy_mirror_rows(gate_rows, threshold=threshold)
    belnap_rows = build_belnap_mirror_rows_from_final_rows(final_rows)
    para_rows = build_paraconsistent_mirror_rows_from_final_rows(final_rows)
    three_rows = build_three_valued_mirror_rows_from_final_rows(final_rows)

    fuzzy_average_overcrown = _sum_int(fuzzy_rows, "average_overcrown_pressure")
    fuzzy_product_strict = _sum_int(fuzzy_rows, "product_stricter_than_native")

    belnap_counts = Counter(str(row["belnap_value"]) for row in belnap_rows)
    para_counts = Counter(str(row["paraconsistent_value"]) for row in para_rows)
    three_unknown = _count(three_rows, "kleene_value", THREE_UNKNOWN)
    three_loss = _sum_int(three_rows, "zero_compression_loss_flag")
    para_overcrowned = _sum_int(para_rows, "local_explosion_flag")

    return [
        {
            "mirror": "fuzzy_many_valued",
            "native_question": "Do softer or stricter continuous conjunctions hide or sharpen native weakest-gate pressure?",
            "primary_pressure_count": fuzzy_average_overcrown,
            "secondary_pressure_count": fuzzy_product_strict,
            "safety_breach_count": 0,
            "closeout_status": "average_overcrown_visible" if fuzzy_average_overcrown else "quiet",
            "useful_when": "comparing C_Z=min(D,P,R,B) against product, average, and Lukasiewicz-style continuous conjunctions",
            "loss_report": "sees continuous gate pressure but cannot crown earned-one without return-depth, lineage, independence, and final witness",
        },
        {
            "mirror": "belnap_evidence_state",
            "native_question": "Does final-output evidence separate evidence-for, evidence-against, both, and neither?",
            "primary_pressure_count": belnap_counts.get(BELNAP_BOTH, 0),
            "secondary_pressure_count": belnap_counts.get(BELNAP_FALSE_ONLY, 0),
            "safety_breach_count": 0,
            "closeout_status": "both_state_visible" if belnap_counts.get(BELNAP_BOTH, 0) else "evidence_map_quiet",
            "useful_when": "raw positive-looking pressure and contrary witness need to be seen together instead of flattened",
            "loss_report": "preserves evidence-for/evidence-against shape but does not decide native truth or replace the final trinary witness",
        },
        {
            "mirror": "paraconsistent_conflict_locality",
            "native_question": "Does conflict pressure stay local instead of exploding into arbitrary final +1?",
            "primary_pressure_count": para_counts.get(PARA_CONFLICT_LOCALIZED, 0),
            "secondary_pressure_count": para_counts.get(PARA_CONFLICT_OVERCROWNED, 0),
            "safety_breach_count": para_overcrowned,
            "closeout_status": "breach" if para_overcrowned else "localized_or_quiet",
            "useful_when": "positive-looking pressure and contrary evidence coexist and must not become a crown by contradiction",
            "loss_report": "preserves conflict-locality pressure but does not prove contradiction is metaphysically fundamental",
        },
        {
            "mirror": "kleene_lukasiewicz_compression",
            "native_question": "What disappears when native final output is compressed to true / unknown / false?",
            "primary_pressure_count": three_loss,
            "secondary_pressure_count": three_unknown,
            "safety_breach_count": 0,
            "closeout_status": "zero_compression_loss_visible" if three_loss else "quiet",
            "useful_when": "showing how much native zero grammar is lost when all holds become unknown",
            "loss_report": "collapses 0+, 0, 0-, latent containment, relation debt, and expresser wounds into one unknown bucket",
        },
    ]


def _write_closeout_read(path: Path, rows: list[dict[str, object]]) -> None:
    safety_breaches = sum(int(row.get("safety_breach_count", 0) or 0) for row in rows)
    visible_pressure = sum(int(row.get("primary_pressure_count", 0) or 0) for row in rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim v1.3 Known-Logic Mirror Closeout")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a closeout witness for projection mirrors, not a new native gate and not an identity claim. ZeroGateSim is not fuzzy logic, Belnap logic, Priest/paraconsistent logic, Kleene logic, or Lukasiewicz logic.")
    lines.append("")
    lines.append("The v1.3 mirror line asks what each formal mirror preserves, what it exposes, and what it destroys when native ZeroGateSim output is translated.")
    lines.append("")
    lines.append("## Closeout posture")
    lines.append("")
    lines.append(f"Visible mirror pressure count: `{visible_pressure}`")
    lines.append(f"Safety breach count: `{safety_breaches}`")
    lines.append("")
    if safety_breaches:
        lines.append("Resist: at least one mirror reports a safety breach. Inspect before advancing beyond v1.3.")
    else:
        lines.append("Witness: no mirror-level safety breach is present. Projection losses may still be visible; those are the point of the closeout, not a reason to pretend equivalence.")
    lines.append("")
    lines.append("## Mirror table")
    lines.append("")
    lines.append("| mirror | status | primary pressure | secondary pressure | breach | useful when | loss report |")
    lines.append("|---|---|---:|---:|---:|---|---|")
    for row in rows:
        lines.append(
            f"| {row['mirror']} | {row['closeout_status']} | {row['primary_pressure_count']} | "
            f"{row['secondary_pressure_count']} | {row['safety_breach_count']} | {row['useful_when']} | {row['loss_report']} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The fuzzy mirror is the gate-pressure mirror. The Belnap mirror is the evidence-state mirror. The paraconsistent mirror is the conflict-locality mirror. The Kleene / Lukasiewicz mirror is the compression-loss mirror.")
    lines.append("")
    lines.append("A mirror is useful only if it makes a native wound easier to see. If it makes ZeroGateSim look stronger by hiding return, lineage, independence, or zero-state depth, the mirror failed its witness job.")
    lines.append("")
    lines.append("## Next boundary")
    lines.append("")
    lines.append("The v1.3 line is ready to close when this file reports no safety breach and every mirror has an explicit loss report. The next line may compare mirror behavior across stronger adversarial runs, but it must not turn projection into borrowed authority.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_known_logic_closeout_outputs(
    output_dir: Path,
    gate_rows: list[tuple[int, GateScores]],
    *,
    threshold: float = 0.55,
) -> dict[str, Path]:
    rows = build_known_logic_closeout_rows(gate_rows, threshold=threshold)
    csv_path = output_dir / "matrix_known_logic_closeout_summary.csv"
    read_path = output_dir / "matrix_known_logic_closeout_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_closeout_read(read_path, rows)
    return {
        "matrix_known_logic_closeout_summary": csv_path,
        "matrix_known_logic_closeout_read": read_path,
    }
