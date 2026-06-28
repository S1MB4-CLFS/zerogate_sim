from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

import numpy as np

from zerogate_sim.gates import GateScores, evaluate_run
from zerogate_sim.reporting import write_dict_rows_csv
from zerogate_sim.signals import SimulationRun

# Three overlapping temporal witness windows. Overlap is deliberate: a returner
# needs enough temporal thickness to show a cycle, not a chopped little fragment
# pretending to be time.
TEMPORAL_WINDOWS: tuple[tuple[str, float, float], ...] = (
    ("early", 0.00, 0.50),
    ("witness", 0.25, 0.75),
    ("late", 0.50, 1.00),
)

ZERO_BAND_ORDER = {
    "rejected": -1,
    "quarantine_hold": 0,
    "witness_hold": 1,
    "fertile_hold": 2,
    "expressed": 3,
}

ENDURANCE_ORDER = {
    "temporal_rejection": -1,
    "temporal_quarantine": 0,
    "temporal_witness": 1,
    "temporal_fertile": 2,
    "temporal_expression": 3,
}


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _window_run(run: SimulationRun, start_ratio: float, end_ratio: float) -> SimulationRun:
    n = run.signals.shape[1]
    start = max(0, min(n - 2, int(round(start_ratio * n))))
    end = max(start + 2, min(n, int(round(end_ratio * n))))
    metadata = dict(run.metadata)
    metadata["temporal_window"] = {"start_ratio": start_ratio, "end_ratio": end_ratio}
    return SimulationRun(
        t=run.t[start:end],
        signals=run.signals[:, start:end],
        specs=run.specs,
        seed=run.seed,
        metadata=metadata,
    )


def _window_scores_by_candidate(
    run: SimulationRun,
    *,
    noise_floor: float,
    gate_threshold: float = 0.55,
    strength_threshold: float = 0.40,
) -> dict[str, dict[str, GateScores]]:
    out: dict[str, dict[str, GateScores]] = {}
    for window_name, start, end in TEMPORAL_WINDOWS:
        window = _window_run(run, start, end)
        scores = evaluate_run(
            window,
            noise_floor=noise_floor,
            gate_threshold=gate_threshold,
            strength_threshold=strength_threshold,
        )
        for row in scores:
            out.setdefault(row.candidate_id, {})[window_name] = row
    return out


def _state_score(row: GateScores) -> int:
    return ZERO_BAND_ORDER.get(row.zero_band, row.trinary_value)


def _transition_signature(rows: list[GateScores]) -> str:
    return ">".join(row.zero_band_symbol for row in rows)


def _return_trace(rows: list[GateScores]) -> str:
    return ">".join(f"{row.return_observed:.3f}" for row in rows)


def _endurance_score(rows: list[GateScores]) -> float:
    scores = [_state_score(row) for row in rows]
    mapped = [(score + 1.0) / 4.0 for score in scores]  # -1..3 -> 0..1
    mean_state = _mean(mapped)
    mean_return = _mean([row.return_observed for row in rows])
    mean_coherence = _mean([row.zero_coherence for row in rows])
    late_weight = mapped[-1]
    # Penalize wild posture flipping. A candidate can transform, but if it keeps
    # thrashing between rooms it has not stood the test of time yet.
    transition_count = sum(1 for a, b in zip(scores[:-1], scores[1:]) if a != b)
    steadiness = 1.0 - (transition_count / max(1, len(scores) - 1))
    return max(0.0, min(1.0, 0.30 * mean_state + 0.25 * mean_return + 0.25 * mean_coherence + 0.10 * late_weight + 0.10 * steadiness))


def classify_temporal_endurance(rows: list[GateScores]) -> tuple[int, str, str, str, float]:
    """Classify temporal endurance without changing the expression gate.

    The core gate asks: did this candidate earn expression in the full field?
    This witness asks: did its posture endure through early/witness/late time?

    +1 temporal_expression: expression endures or matures into late expression.
    0+ temporal_fertile: near expression over time; retest before repair.
    0 temporal_witness: mixed but meaningful; keep watching.
    0- temporal_quarantine: unsafe decay/debt; do not build on it yet.
    -1 temporal_rejection: no credible temporal zero-structure.
    """

    scores = [_state_score(row) for row in rows]
    bands = [row.zero_band for row in rows]
    symbols = [row.zero_band_symbol for row in rows]
    late = rows[-1]
    early = rows[0]
    endurance = _endurance_score(rows)

    expressed_count = sum(1 for band in bands if band == "expressed")
    fertile_count = sum(1 for band in bands if band == "fertile_hold")
    witness_count = sum(1 for band in bands if band == "witness_hold")
    quarantine_count = sum(1 for band in bands if band == "quarantine_hold")
    rejected_count = sum(1 for band in bands if band == "rejected")

    # +1: earned expression withstands time, or the candidate matures into late
    # expression without falling through quarantine/rejection first.
    if late.zero_band == "expressed" and rejected_count == 0 and quarantine_count == 0:
        if expressed_count >= 2:
            return 1, "temporal_expression", "+1T", "expression_endured", endurance
        if max(scores[:-1]) >= 1:
            return 1, "temporal_expression", "+1T", "late_expression_matured", endurance

    # 0+: close, living pressure. No poison state, enough coherent zero shape.
    if rejected_count == 0 and quarantine_count == 0:
        if fertile_count + expressed_count >= 2:
            return 1, "temporal_fertile", "0+T", "fertile_temporal_hold", endurance
        if late.zero_band == "fertile_hold" and early.zero_band in {"witness_hold", "fertile_hold", "expressed"}:
            return 1, "temporal_fertile", "0+T", "late_fertile_hold", endurance

    # 0-: visible temporal debt. Decay from a stronger early state into unsafe
    # late posture is more important than the fact it once looked pretty.
    if late.zero_band in {"quarantine_hold", "rejected"} and max(scores[:-1]) >= 2:
        return -1, "temporal_quarantine", "0-T", "temporal_decay_quarantine", endurance
    if quarantine_count >= 2 and expressed_count == 0:
        return -1, "temporal_quarantine", "0-T", "repeated_quarantine", endurance

    # -1: all three windows reject. Nothing stood long enough to deserve the
    # witness room.
    if rejected_count == len(rows):
        return -1, "temporal_rejection", "-1T", "rejected_across_time", endurance

    # 0: mixed or unresolved. The proper middle: neither crown nor shovel.
    if witness_count + fertile_count + expressed_count > 0:
        return 0, "temporal_witness", "0T", "temporal_witness_hold", endurance

    return -1, "temporal_quarantine", "0-T", "weak_temporal_pressure", endurance


def build_temporal_rows(
    *,
    run: SimulationRun,
    scenario: str,
    seed: int,
    noise_axis: int,
    relation_axis: int,
    expansion_axis: int,
    perturbation_axis: int | str | None,
    time_axis: int | str | None = None,
    noise_floor: float = 0.12,
    gate_threshold: float = 0.55,
    strength_threshold: float = 0.40,
) -> list[dict[str, object]]:
    """Return candidate-level temporal endurance rows for one run."""

    by_candidate = _window_scores_by_candidate(
        run,
        noise_floor=noise_floor,
        gate_threshold=gate_threshold,
        strength_threshold=strength_threshold,
    )
    out: list[dict[str, object]] = []
    for spec in run.specs:
        windows = by_candidate[spec.candidate_id]
        rows = [windows[name] for name, _, _ in TEMPORAL_WINDOWS]
        temporal_value, temporal_band, temporal_symbol, temporal_reason, endurance = classify_temporal_endurance(rows)
        state_scores = [_state_score(row) for row in rows]
        transition_count = sum(1 for a, b in zip(state_scores[:-1], state_scores[1:]) if a != b)
        out.append(
            {
                "scenario": scenario,
                "seed": seed,
                "candidate_id": spec.candidate_id,
                "kind": spec.kind,
                "designed_stable": spec.designed_stable,
                "truth_role": rows[-1].truth_role,
                "expected_trinary": rows[-1].expected_trinary,
                "noise_axis": noise_axis,
                "relation_axis": relation_axis,
                "expansion_axis": expansion_axis,
                "perturbation_axis": "" if perturbation_axis is None else perturbation_axis,
                "time_axis": "" if time_axis is None else time_axis,
                "early_band": rows[0].zero_band,
                "witness_band": rows[1].zero_band,
                "late_band": rows[2].zero_band,
                "early_symbol": rows[0].zero_band_symbol,
                "witness_symbol": rows[1].zero_band_symbol,
                "late_symbol": rows[2].zero_band_symbol,
                "transition_signature": _transition_signature(rows),
                "return_cycle_trace": _return_trace(rows),
                "early_strength": rows[0].strength,
                "witness_strength": rows[1].strength,
                "late_strength": rows[2].strength,
                "early_C_Z": rows[0].zero_coherence,
                "witness_C_Z": rows[1].zero_coherence,
                "late_C_Z": rows[2].zero_coherence,
                "early_return": rows[0].return_observed,
                "witness_return": rows[1].return_observed,
                "late_return": rows[2].return_observed,
                "early_zero_depth": rows[0].zero_depth,
                "witness_zero_depth": rows[1].zero_depth,
                "late_zero_depth": rows[2].zero_depth,
                "transition_count": transition_count,
                "temporal_value": temporal_value,
                "temporal_band": temporal_band,
                "temporal_symbol": temporal_symbol,
                "temporal_reason": temporal_reason,
                "endurance_score": endurance,
            }
        )
    return out


def _scenario_group(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for scenario in sorted({str(row["scenario"]) for row in rows}):
        subset = [row for row in rows if row["scenario"] == scenario]
        designed = [row for row in subset if str(row.get("truth_role", "")) == "expresser"]
        latent = [row for row in subset if str(row.get("truth_role", "")) == "latent"]
        traps = [row for row in subset if str(row.get("truth_role", "")) == "trap"]
        transitions = Counter(str(row["transition_signature"]) for row in designed)
        temporal_counts = Counter(str(row["temporal_band"]) for row in designed)
        trap_expr = [row for row in traps if str(row["temporal_band"]) == "temporal_expression"]
        first = subset[0]
        out.append(
            {
                "scenario": scenario,
                "noise_axis": first["noise_axis"],
                "relation_axis": first["relation_axis"],
                "expansion_axis": first["expansion_axis"],
                "perturbation_axis": first["perturbation_axis"],
                "time_axis": first.get("time_axis", ""),
                "candidate_windows": len(subset),
                "designed_candidate_windows": len(designed),
                "latent_candidate_windows": len(latent),
                "trap_candidate_windows": len(traps),
                "designed_temporal_expression": temporal_counts.get("temporal_expression", 0),
                "designed_temporal_fertile": temporal_counts.get("temporal_fertile", 0),
                "designed_temporal_witness": temporal_counts.get("temporal_witness", 0),
                "designed_temporal_quarantine": temporal_counts.get("temporal_quarantine", 0),
                "designed_temporal_rejection": temporal_counts.get("temporal_rejection", 0),
                "trap_temporal_expression": len(trap_expr),
                "mean_designed_endurance": _mean([float(row["endurance_score"]) for row in designed]),
                "dominant_designed_transition": transitions.most_common(1)[0][0] if transitions else "",
                "dominant_designed_transition_count": transitions.most_common(1)[0][1] if transitions else 0,
            }
        )
    return out


def _candidate_group(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for candidate_id in sorted({str(row["candidate_id"]) for row in rows}):
        subset = [row for row in rows if row["candidate_id"] == candidate_id]
        counts = Counter(str(row["temporal_band"]) for row in subset)
        transitions = Counter(str(row["transition_signature"]) for row in subset)
        first = subset[0]
        n = len(subset)
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first["kind"],
                "designed_stable": first["designed_stable"],
                "truth_role": first.get("truth_role", ""),
                "expected_trinary": first.get("expected_trinary", ""),
                "runs": n,
                "temporal_expression_count": counts.get("temporal_expression", 0),
                "temporal_expression_rate": counts.get("temporal_expression", 0) / n,
                "temporal_fertile_count": counts.get("temporal_fertile", 0),
                "temporal_fertile_rate": counts.get("temporal_fertile", 0) / n,
                "temporal_witness_count": counts.get("temporal_witness", 0),
                "temporal_witness_rate": counts.get("temporal_witness", 0) / n,
                "temporal_quarantine_count": counts.get("temporal_quarantine", 0),
                "temporal_quarantine_rate": counts.get("temporal_quarantine", 0) / n,
                "temporal_rejection_count": counts.get("temporal_rejection", 0),
                "temporal_rejection_rate": counts.get("temporal_rejection", 0) / n,
                "mean_endurance_score": _mean([float(row["endurance_score"]) for row in subset]),
                "dominant_transition": transitions.most_common(1)[0][0] if transitions else "",
                "dominant_transition_count": transitions.most_common(1)[0][1] if transitions else 0,
            }
        )
    return out


def write_temporal_outputs(root_dir: Path, temporal_rows: list[dict[str, object]]) -> dict[str, Path]:
    """Write temporal endurance witness CSVs and speakable read."""

    scenario_rows = _scenario_group(temporal_rows)
    candidate_rows = _candidate_group(temporal_rows)
    trace_csv = root_dir / "matrix_temporal_trace.csv"
    scenario_csv = root_dir / "matrix_temporal_scenario_summary.csv"
    candidate_csv = root_dir / "matrix_temporal_candidate_summary.csv"
    read_md = root_dir / "matrix_temporal_read.md"
    write_dict_rows_csv(trace_csv, temporal_rows)
    write_dict_rows_csv(scenario_csv, scenario_rows)
    write_dict_rows_csv(candidate_csv, candidate_rows)
    write_temporal_read(read_md, scenario_rows=scenario_rows, candidate_rows=candidate_rows)
    return {
        "matrix_temporal_trace": trace_csv,
        "matrix_temporal_scenario_summary": scenario_csv,
        "matrix_temporal_candidate_summary": candidate_csv,
        "matrix_temporal_read": read_md,
    }


def write_temporal_read(
    path: Path,
    *,
    scenario_rows: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
) -> None:
    total_scenarios = len(scenario_rows)
    trap_expr = sum(int(row.get("trap_temporal_expression", 0)) for row in scenario_rows)
    designed_reject = sum(int(row.get("designed_temporal_rejection", 0)) for row in scenario_rows)
    designed_quarantine = sum(int(row.get("designed_temporal_quarantine", 0)) for row in scenario_rows)
    mean_endurance = _mean([float(row["mean_designed_endurance"]) for row in scenario_rows])

    lines: list[str] = []
    lines.append("# ZeroGateSim Temporal Endurance Read")
    lines.append("")
    lines.append("This is the time witness. It does not change the zero-gate core. It asks whether a candidate posture survives early, witness, and late time instead of passing from one lucky window.")
    lines.append("")
    lines.append("## Field posture")
    lines.append("")
    lines.append(f"Scenarios read: `{total_scenarios}`")
    lines.append(f"Mean designed temporal endurance: `{mean_endurance:.3f}`")
    lines.append(f"Trap temporal-expression breaches: `{trap_expr}`")
    lines.append(f"Designed temporal quarantine count: `{designed_quarantine}`")
    lines.append(f"Designed temporal rejection count: `{designed_reject}`")
    lines.append("")
    lines.append("## Candidate endurance")
    lines.append("")
    lines.append("| candidate | kind | designed | +1T | 0+T | 0T | 0-T | -1T | mean endurance | dominant transition |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for row in candidate_rows:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['designed_stable']} | "
            f"{row['temporal_expression_count']} | {row['temporal_fertile_count']} | "
            f"{row['temporal_witness_count']} | {row['temporal_quarantine_count']} | "
            f"{row['temporal_rejection_count']} | {float(row['mean_endurance_score']):.3f} | "
            f"{row['dominant_transition']} |"
        )
    lines.append("")
    lines.append("## Witness translation")
    lines.append("")
    if trap_expr:
        lines.append("Resist: at least one trap achieved temporal expression. Inspect before any theory celebration.")
    elif designed_reject:
        lines.append("Resist: no trap was crowned, but designed candidates reached temporal -1. This is a conservative wound, not a breach.")
    elif designed_quarantine:
        lines.append("Witness: no breach and no designed -1, but some designed candidates fall into temporal quarantine. The core is safe; time pressure is still strict.")
    else:
        lines.append("Expand: no breach, no designed temporal rejection, and no designed temporal quarantine. The field endured the current temporal witness.")
    lines.append("")
    lines.append("0+T means a candidate is temporally fertile. 0T means it needs more time/pressure. 0-T means temporal quarantine: interesting pressure, not a building stone. -1T is true rejection across time.")
    lines.append("")
    lines.append("The primate can count windows. The witness asks whether the posture kept its name after time touched it.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
