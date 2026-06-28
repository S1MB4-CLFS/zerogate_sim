from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean

from zerogate_sim.reporting import write_dict_rows_csv


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def classify_lineage(row: dict[str, object]) -> str:
    """Classify the early>witness>late posture path.

    This is witness grammar, not a new gate. It asks how the candidate travelled:
    did it endure, mature, hold, decay, quarantine, or fail?
    """

    early = str(row.get("early_band", ""))
    witness = str(row.get("witness_band", ""))
    late = str(row.get("late_band", ""))
    bands = [early, witness, late]

    if bands == ["expressed", "expressed", "expressed"]:
        return "expression_endured"
    if late == "expressed" and early != "expressed":
        return "matured_to_expression"
    if early == "expressed" and late != "expressed":
        return "expression_returned_to_zero"
    if late == "fertile_hold":
        return "late_fertile_hold"
    if late == "witness_hold":
        return "late_witness_hold"
    if late == "quarantine_hold":
        return "late_quarantine_hold"
    if late == "rejected" and max(_band_score(b) for b in bands[:2]) >= 2:
        return "decayed_to_rejection"
    if bands == ["rejected", "rejected", "rejected"]:
        return "rejected_through_time"
    return "mixed_lineage"


def _band_score(band: str) -> int:
    return {
        "rejected": -1,
        "quarantine_hold": 0,
        "witness_hold": 1,
        "fertile_hold": 2,
        "expressed": 3,
    }.get(band, -1)


def _transition_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str]] = Counter()
    designed_counts: Counter[tuple[str, str]] = Counter()
    trap_counts: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        lineage = classify_lineage(row)
        signature = str(row.get("transition_signature", ""))
        key = (lineage, signature)
        counts[key] += 1
        if bool(row.get("designed_stable")):
            designed_counts[key] += 1
        else:
            trap_counts[key] += 1
        examples.setdefault(key, set()).add(str(row.get("candidate_id", "")))

    out: list[dict[str, object]] = []
    for (lineage, signature), count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        out.append(
            {
                "lineage_class": lineage,
                "transition_signature": signature,
                "count": count,
                "designed_count": designed_counts.get((lineage, signature), 0),
                "trap_count": trap_counts.get((lineage, signature), 0),
                "candidate_examples": ",".join(sorted(examples[(lineage, signature)])),
            }
        )
    return out


def _candidate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for candidate_id in sorted({str(row["candidate_id"]) for row in rows}):
        subset = [row for row in rows if str(row["candidate_id"]) == candidate_id]
        first = subset[0]
        lineages = Counter(classify_lineage(row) for row in subset)
        transitions = Counter(str(row.get("transition_signature", "")) for row in subset)
        temporal = Counter(str(row.get("temporal_band", "")) for row in subset)
        n = len(subset)
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first.get("kind", ""),
                "designed_stable": first.get("designed_stable", False),
                "runs": n,
                "dominant_lineage": lineages.most_common(1)[0][0] if lineages else "",
                "dominant_lineage_count": lineages.most_common(1)[0][1] if lineages else 0,
                "dominant_transition": transitions.most_common(1)[0][0] if transitions else "",
                "dominant_transition_count": transitions.most_common(1)[0][1] if transitions else 0,
                "expression_endured": lineages.get("expression_endured", 0),
                "matured_to_expression": lineages.get("matured_to_expression", 0),
                "returned_to_zero": lineages.get("expression_returned_to_zero", 0),
                "late_fertile_hold": lineages.get("late_fertile_hold", 0),
                "late_witness_hold": lineages.get("late_witness_hold", 0),
                "late_quarantine_hold": lineages.get("late_quarantine_hold", 0),
                "rejected_through_time": lineages.get("rejected_through_time", 0),
                "temporal_expression": temporal.get("temporal_expression", 0),
                "temporal_fertile": temporal.get("temporal_fertile", 0),
                "temporal_witness": temporal.get("temporal_witness", 0),
                "temporal_quarantine": temporal.get("temporal_quarantine", 0),
                "temporal_rejection": temporal.get("temporal_rejection", 0),
                "mean_endurance": _mean([float(row.get("endurance_score", 0.0)) for row in subset]),
            }
        )
    return out


def _write_read(path: Path, rows: list[dict[str, object]], candidate_rows: list[dict[str, object]], transition_rows: list[dict[str, object]]) -> None:
    designed = [row for row in rows if bool(row.get("designed_stable"))]
    traps = [row for row in rows if not bool(row.get("designed_stable"))]
    designed_rejections = [row for row in designed if str(row.get("temporal_band")) == "temporal_rejection"]
    trap_expr = [row for row in traps if str(row.get("temporal_band")) == "temporal_expression"]
    matured = sum(int(row["matured_to_expression"]) for row in candidate_rows)
    endured = sum(int(row["expression_endured"]) for row in candidate_rows)
    returned = sum(int(row["returned_to_zero"]) for row in candidate_rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Temporal Lineage Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This file reads posture movement through early / witness / late windows. It does not change the gate and does not prove physics. It shows how candidates keep, gain, lose, or withhold their name when time touches them.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Expression endured paths: `{endured}`")
    lines.append(f"Matured-to-expression paths: `{matured}`")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Returned-to-zero / held-after-expression paths: `{returned}`")
    lines.append("These are not automatically failures. They are paths where expression touched zero again and must be read by posture, not binary pride.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Designed temporal rejections: `{len(designed_rejections)}`")
    lines.append(f"Trap temporal-expression breaches: `{len(trap_expr)}`")
    lines.append("")
    lines.append("## Dominant candidate lineages")
    lines.append("")
    lines.append("| candidate | kind | designed | dominant lineage | mean endurance |")
    lines.append("|---|---|---:|---|---:|")
    for row in candidate_rows[:27]:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['designed_stable']} | {row['dominant_lineage']} | {float(row['mean_endurance']):.3f} |"
        )
    lines.append("")
    lines.append("## Dominant transition paths")
    lines.append("")
    lines.append("| lineage | transition | count | designed | traps |")
    lines.append("|---|---|---:|---:|---:|")
    for row in transition_rows[:27]:
        lines.append(
            f"| {row['lineage_class']} | {row['transition_signature']} | {row['count']} | {row['designed_count']} | {row['trap_count']} |"
        )
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    lines.append("The question is no longer only whether a candidate passed. The question is whether its path through time looks like endurance, maturation, return-to-zero, quarantine debt, or rejection. That is the first lineage grammar of the zero-zone.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_lineage_outputs(output_dir: Path, temporal_rows: list[dict[str, object]]) -> dict[str, Path]:
    transitions = _transition_rows(temporal_rows)
    candidates = _candidate_rows(temporal_rows)
    transition_path = output_dir / "matrix_lineage_transitions.csv"
    candidate_path = output_dir / "matrix_lineage_candidate_summary.csv"
    read_path = output_dir / "matrix_lineage_read.md"
    write_dict_rows_csv(transition_path, transitions)
    write_dict_rows_csv(candidate_path, candidates)
    _write_read(read_path, temporal_rows, candidates, transitions)
    return {
        "matrix_lineage_transitions": transition_path,
        "matrix_lineage_candidate_summary": candidate_path,
        "matrix_lineage_read": read_path,
    }
