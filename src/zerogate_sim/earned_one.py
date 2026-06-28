from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from zerogate_sim.gates import GateScores
from zerogate_sim.echo_independence import build_echo_independence_rows
from zerogate_sim.reporting import write_dict_rows_csv

AXIS_RE = re.compile(r"(?:^|_)r([MZP])(?:_|$)")


def _base_candidate_id(candidate_id: str) -> str:
    return candidate_id.split(":", 1)[-1]


def _scenario_name(candidate_id: str) -> str:
    return candidate_id.split(":", 1)[0] if ":" in candidate_id else ""


def _relation_axis(candidate_id: str) -> str:
    match = AXIS_RE.search(_scenario_name(candidate_id))
    return match.group(1) if match else ""


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _candidate_band(*, truth_role: str, raw_expressed: int, false_one: int, latent_overcrown: int, relation_debt: int, earned_one: int) -> tuple[str, str]:
    """Matrix-level earned-one witness.

    This does not change the four-gate expression law. It reads the raw +1 events
    through truth role and echo-independence. The purpose is to separate earned
    one from false one without loosening the core gate.
    """

    if false_one > 0:
        return "false_one_breach", "trap_was_crowned_by_raw_gate"
    if latent_overcrown > 0:
        return "latent_overcrown_hold", "latent_probe_expressed_but_not_earned_one"
    if relation_debt > 0:
        return "relation_debt_expression", "expresser_needs_relation_plus_weather"
    if earned_one > 0:
        return "earned_one", "expresser_crowned_after_independence_witness"
    if truth_role == "expresser":
        return "expresser_wound", "expected_expresser_did_not_earn_one"
    return "contained", "no_raw_expression"


def build_earned_one_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    echo_rows = build_echo_independence_rows(gate_rows)
    echo_by_id = {str(row["candidate_id"]): row for row in echo_rows}

    grouped: dict[str, list[GateScores]] = defaultdict(list)
    for _, row in gate_rows:
        grouped[_base_candidate_id(row.candidate_id)].append(row)

    out: list[dict[str, object]] = []
    for candidate_id in sorted(grouped):
        rows = grouped[candidate_id]
        first = rows[0]
        echo = echo_by_id.get(candidate_id, {})
        echo_band = str(echo.get("echo_independence_band", "unknown"))
        relation_dependency = float(echo.get("relation_dependency_score", 0.0) or 0.0)
        independence = float(echo.get("echo_independence_score", 1.0) or 1.0)

        raw_expressed = [row for row in rows if row.expressed]
        raw_expressed_count = len(raw_expressed)
        relation_plus_raw = sum(1 for row in raw_expressed if _relation_axis(row.candidate_id) == "P")
        relation_zero_raw = sum(1 for row in raw_expressed if _relation_axis(row.candidate_id) == "Z")
        relation_minus_raw = sum(1 for row in raw_expressed if _relation_axis(row.candidate_id) == "M")

        false_one_count = 0
        latent_overcrown_count = 0
        relation_debt_count = 0
        earned_one_count = 0

        if first.truth_role == "trap":
            false_one_count = raw_expressed_count
        elif first.truth_role == "latent":
            latent_overcrown_count = raw_expressed_count
        elif first.truth_role == "expresser":
            if echo_band == "relation_debt":
                relation_debt_count = raw_expressed_count
            else:
                earned_one_count = raw_expressed_count

        band, reason = _candidate_band(
            truth_role=first.truth_role,
            raw_expressed=raw_expressed_count,
            false_one=false_one_count,
            latent_overcrown=latent_overcrown_count,
            relation_debt=relation_debt_count,
            earned_one=earned_one_count,
        )
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first.kind,
                "truth_role": first.truth_role,
                "runs": len(rows),
                "raw_expressed_count": raw_expressed_count,
                "earned_one_count": earned_one_count,
                "false_one_count": false_one_count,
                "latent_overcrown_count": latent_overcrown_count,
                "relation_debt_count": relation_debt_count,
                "relation_minus_raw_expression": relation_minus_raw,
                "relation_zero_raw_expression": relation_zero_raw,
                "relation_plus_raw_expression": relation_plus_raw,
                "echo_independence_band": echo_band,
                "relation_dependency_score": relation_dependency,
                "echo_independence_score": independence,
                "earned_one_band": band,
                "earned_one_reason": reason,
                "mean_strength": _mean([row.strength for row in rows]),
                "mean_zero_coherence": _mean([row.zero_coherence for row in rows]),
                "mean_return_potential": _mean([row.return_potential for row in rows]),
                "mean_return_observed": _mean([row.return_observed for row in rows]),
            }
        )
    return out


def _write_earned_one_read(path: Path, rows: list[dict[str, object]]) -> None:
    bands = Counter(str(row["earned_one_band"]) for row in rows)
    false_ones = [row for row in rows if int(row["false_one_count"]) > 0]
    latent_overcrowns = [row for row in rows if int(row["latent_overcrown_count"]) > 0]
    relation_debts = [row for row in rows if int(row["relation_debt_count"]) > 0]
    earned = [row for row in rows if int(row["earned_one_count"]) > 0]

    total_raw = sum(int(row["raw_expressed_count"]) for row in rows)
    total_earned = sum(int(row["earned_one_count"]) for row in rows)
    total_false = sum(int(row["false_one_count"]) for row in rows)
    total_latent = sum(int(row["latent_overcrown_count"]) for row in rows)
    total_debt = sum(int(row["relation_debt_count"]) for row in rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Earned-One Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This file separates raw expression from earned one. It does not mutate the four-gate core. It asks whether a +1 event belongs to an expresser, a latent/probe, or a trap, and whether echo-independence exposes borrowed relation.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Earned-one events: `{total_earned}` from `{len(earned)}` candidates.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Raw expression events: `{total_raw}`. Latent overcrown holds: `{total_latent}`. Relation-debt expression events: `{total_debt}`.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"False-one breach events: `{total_false}` from `{len(false_ones)}` candidates.")
    lines.append("")
    lines.append("## Band counts")
    lines.append("")
    for band, count in sorted(bands.items()):
        lines.append(f"- `{band}`: `{count}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | band | raw +1 | earned | false one | latent overcrown | echo band | r- | r0 | r+ |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|")
    ranked = sorted(
        rows,
        key=lambda row: (
            0 if int(row["false_one_count"]) > 0 else 1 if int(row["latent_overcrown_count"]) > 0 else 2 if int(row["relation_debt_count"]) > 0 else 3,
            -int(row["raw_expressed_count"]),
            str(row["candidate_id"]),
        ),
    )
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['earned_one_band']} | "
            f"{row['raw_expressed_count']} | {row['earned_one_count']} | {row['false_one_count']} | {row['latent_overcrown_count']} | "
            f"{row['echo_independence_band']} | {row['relation_minus_raw_expression']} | {row['relation_zero_raw_expression']} | {row['relation_plus_raw_expression']} |"
        )
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if false_ones:
        names = ", ".join(f"`{row['candidate_id']}`" for row in false_ones[:9])
        lines.append(f"False one remains: {names}. The raw gate crowned a trap. This is the blocker before v1.0 research-alpha victory.")
    else:
        lines.append("No false-one breach remains in this matrix. That would satisfy the main resist boundary for v1.0 research-alpha, pending repeated weather.")
    if latent_overcrowns:
        names = ", ".join(f"`{row['candidate_id']}`" for row in latent_overcrowns[:9])
        lines.append(f"Latent overcrown pressure is present in: {names}. These are not trap breaches, but they are not earned one either.")
    if relation_debts:
        names = ", ".join(f"`{row['candidate_id']}`" for row in relation_debts[:9])
        lines.append(f"Relation-debt expressers require retest before being treated as fully independent: {names}.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_earned_one_outputs(output_dir: Path, gate_rows: list[tuple[int, GateScores]]) -> dict[str, Path]:
    rows = build_earned_one_rows(gate_rows)
    csv_path = output_dir / "matrix_earned_one_summary.csv"
    read_path = output_dir / "matrix_earned_one_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_earned_one_read(read_path, rows)
    return {"matrix_earned_one_summary": csv_path, "matrix_earned_one_read": read_path}
