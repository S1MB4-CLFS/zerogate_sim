from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv

AXIS_RE = re.compile(r"(?:^|_)r([MZP])(?:_|$)")
RELATION_AXES = ("M", "Z", "P")


def _base_candidate_id(candidate_id: str) -> str:
    return candidate_id.split(":", 1)[-1]


def _scenario_name(candidate_id: str) -> str:
    return candidate_id.split(":", 1)[0] if ":" in candidate_id else ""


def _relation_axis(candidate_id: str) -> str:
    match = AXIS_RE.search(_scenario_name(candidate_id))
    return match.group(1) if match else ""


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rate(num: int, den: int) -> float:
    return float(num / den) if den else 0.0


def _band(*, truth_role: str, expressed_count: int, relation_dependency_score: float, relation_plus_share: float, expressed_axes: int) -> tuple[str, str]:
    """Classify candidate-level echo independence.

    This is a matrix-level witness, not a single-run gate. It asks whether a
    candidate earns expression across relation weather, or only appears when the
    relation axis is pushed plus. A relation-plus-only trap is the false-one wound
    exposed by F26.
    """

    if expressed_count <= 0:
        return "contained", "no_expression"
    if truth_role == "trap" and relation_dependency_score >= 0.20 and relation_plus_share >= 0.80:
        return "echo_breach", "trap_expression_relation_plus_dependent"
    if truth_role == "trap":
        return "trap_breach", "trap_expression_not_yet_echo_classified"
    if truth_role == "latent" and relation_dependency_score >= 0.20 and relation_plus_share >= 0.80:
        return "echo_debt_hold", "latent_expression_relation_plus_dependent"
    if truth_role == "expresser" and relation_dependency_score >= 0.20 and relation_plus_share >= 0.80:
        return "relation_debt", "expresser_needs_relation_plus_weather"
    if expressed_axes >= 2:
        return "independent_expression", "expresses_across_relation_weather"
    return "relation_supported", "expression_relation_sensitive"


def build_echo_independence_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    grouped: dict[str, list[GateScores]] = defaultdict(list)
    for _, row in gate_rows:
        grouped[_base_candidate_id(row.candidate_id)].append(row)

    out: list[dict[str, object]] = []
    for candidate_id in sorted(grouped):
        rows = grouped[candidate_id]
        first = rows[0]
        axis_runs = {axis: 0 for axis in RELATION_AXES}
        axis_expr = {axis: 0 for axis in RELATION_AXES}
        for row in rows:
            axis = _relation_axis(row.candidate_id)
            if axis not in axis_runs:
                continue
            axis_runs[axis] += 1
            if row.expressed:
                axis_expr[axis] += 1

        axis_rates = {axis: _rate(axis_expr[axis], axis_runs[axis]) for axis in RELATION_AXES}
        expressed_count = sum(1 for row in rows if row.expressed)
        expressed_rate = _rate(expressed_count, len(rows))
        expressed_axes = sum(1 for axis in RELATION_AXES if axis_expr[axis] > 0)
        plus_share = _rate(axis_expr["P"], expressed_count)
        relation_dependency = max(0.0, axis_rates["P"] - max(axis_rates["M"], axis_rates["Z"]))
        independence = max(0.0, 1.0 - relation_dependency * plus_share)
        band, reason = _band(
            truth_role=first.truth_role,
            expressed_count=expressed_count,
            relation_dependency_score=relation_dependency,
            relation_plus_share=plus_share,
            expressed_axes=expressed_axes,
        )
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first.kind,
                "truth_role": first.truth_role,
                "runs": len(rows),
                "expressed_count": expressed_count,
                "expressed_rate": expressed_rate,
                "relation_minus_expressed": axis_expr["M"],
                "relation_zero_expressed": axis_expr["Z"],
                "relation_plus_expressed": axis_expr["P"],
                "relation_minus_rate": axis_rates["M"],
                "relation_zero_rate": axis_rates["Z"],
                "relation_plus_rate": axis_rates["P"],
                "expressed_relation_axes": expressed_axes,
                "relation_plus_share": plus_share,
                "relation_dependency_score": relation_dependency,
                "echo_independence_score": independence,
                "echo_independence_band": band,
                "echo_independence_reason": reason,
                "mean_strength": _mean([row.strength for row in rows]),
                "mean_relation": _mean([row.relation for row in rows]),
                "mean_return_potential": _mean([row.return_potential for row in rows]),
                "mean_return_observed": _mean([row.return_observed for row in rows]),
                "mean_zero_coherence": _mean([row.zero_coherence for row in rows]),
                "mean_signal_echo_score": _mean([row.echo_mimic_score for row in rows]),
            }
        )
    return out


def _write_echo_independence_read(path: Path, rows: list[dict[str, object]]) -> None:
    bands = Counter(str(row["echo_independence_band"]) for row in rows)
    breaches = [row for row in rows if row["echo_independence_band"] in {"echo_breach", "trap_breach"}]
    relation_debts = [row for row in rows if row["echo_independence_band"] in {"relation_debt", "echo_debt_hold"}]
    independent = [row for row in rows if row["echo_independence_band"] == "independent_expression"]

    lines: list[str] = []
    lines.append("# ZeroGateSim Echo-Independence Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a matrix-level witness, not a new fifth gate. It asks whether expression survives relation-weather changes or appears only when relation is pushed plus. The target wound is borrowed coherence: a candidate that looks like +1 only because the field carries it.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Independent-expression candidates: `{len(independent)}`. These express across more than one relation weather and are less likely to be field echoes.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Relation-debt candidates: `{len(relation_debts)}`. These may be real, latent, or developmental, but they still depend heavily on relation-plus weather.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Echo/trap breach candidates: `{len(breaches)}`. These are dangerous because they represent false one, not conservative holding.")
    lines.append("")
    lines.append("## Band counts")
    lines.append("")
    for band, count in sorted(bands.items()):
        lines.append(f"- `{band}`: `{count}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | band | expressed | r- | r0 | r+ | dep | indep | reason |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    ranked = sorted(
        rows,
        key=lambda row: (
            0 if row["echo_independence_band"] == "echo_breach" else 1 if row["echo_independence_band"] == "trap_breach" else 2,
            -float(row["relation_dependency_score"]),
            str(row["candidate_id"]),
        ),
    )
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['echo_independence_band']} | "
            f"{row['expressed_count']} | {row['relation_minus_expressed']} | {row['relation_zero_expressed']} | {row['relation_plus_expressed']} | "
            f"{float(row['relation_dependency_score']):.3f} | {float(row['echo_independence_score']):.3f} | {row['echo_independence_reason']} |"
        )
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if breaches:
        names = ", ".join(f"`{row['candidate_id']}`" for row in breaches[:9])
        lines.append(f"Echo-independence found the false-one wound: {names}. These candidates express by relation dependence and must not be treated as earned one without an independence repair.")
    else:
        lines.append("No echo-independence breach detected. This does not prove reality; it means the current candidate field did not crown a relation-plus-only trap.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_echo_independence_outputs(output_dir: Path, gate_rows: list[tuple[int, GateScores]]) -> dict[str, Path]:
    rows = build_echo_independence_rows(gate_rows)
    csv_path = output_dir / "matrix_echo_independence_summary.csv"
    read_path = output_dir / "matrix_echo_independence_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_echo_independence_read(read_path, rows)
    return {
        "matrix_echo_independence_summary": csv_path,
        "matrix_echo_independence_read": read_path,
    }
