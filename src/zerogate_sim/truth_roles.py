from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv


def _base_candidate_id(candidate_id: str) -> str:
    return candidate_id.split(":")[-1]


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _role_posture(row: GateScores) -> str:
    """Read one candidate posture against its expected truth role.

    This is witness grammar. It does not change the gate. It only prevents the
    reports from judging expressers, latent probes, and traps with one binary
    scoreboard.
    """

    role = row.truth_role
    if role == "expresser":
        if row.expressed:
            return "expresser_fulfilled"
        if row.zero_band in {"fertile_hold", "witness_hold", "quarantine_hold"}:
            return f"expresser_{row.zero_band}"
        return "expresser_rejected_wound"
    if role == "latent":
        if row.expressed:
            return "latent_overcrowned"
        if row.zero_band in {"fertile_hold", "witness_hold", "quarantine_hold"}:
            return f"latent_{row.zero_band}"
        return "latent_cold_rejection"
    # trap
    if row.expressed:
        if row.echo_mimic_band == "echo_breach":
            return "trap_echo_breach"
        return "trap_breach"
    if row.zero_band in {"fertile_hold", "witness_hold"}:
        return f"trap_soft_mimic_{row.zero_band}"
    return "trap_contained"


def _candidate_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    grouped: dict[str, list[GateScores]] = defaultdict(list)
    for _, row in gate_rows:
        grouped[_base_candidate_id(row.candidate_id)].append(row)

    out: list[dict[str, object]] = []
    for candidate_id in sorted(grouped):
        rows = grouped[candidate_id]
        first = rows[0]
        postures = Counter(_role_posture(row) for row in rows)
        zero_bands = Counter(row.zero_band for row in rows)
        echo_bands = Counter(row.echo_mimic_band for row in rows)
        n = len(rows)
        breach_count = sum(1 for row in rows if row.truth_role == "trap" and row.expressed)
        echo_breach_count = sum(1 for row in rows if row.echo_mimic_band == "echo_breach")
        latent_overcrown_count = sum(1 for row in rows if row.truth_role == "latent" and row.expressed)
        expresser_rejection_count = sum(1 for row in rows if row.truth_role == "expresser" and row.zero_band == "rejected")
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first.kind,
                "truth_role": first.truth_role,
                "expected_trinary": first.expected_trinary,
                "runs": n,
                "expressed_count": sum(1 for row in rows if row.expressed),
                "expressed_rate": sum(1 for row in rows if row.expressed) / n,
                "fertile_hold_count": zero_bands.get("fertile_hold", 0),
                "witness_hold_count": zero_bands.get("witness_hold", 0),
                "quarantine_hold_count": zero_bands.get("quarantine_hold", 0),
                "rejected_count": zero_bands.get("rejected", 0),
                "dominant_role_posture": postures.most_common(1)[0][0],
                "dominant_role_posture_count": postures.most_common(1)[0][1],
                "breach_count": breach_count,
                "echo_breach_count": echo_breach_count,
                "latent_overcrown_count": latent_overcrown_count,
                "expresser_rejection_count": expresser_rejection_count,
                "mean_echo_mimic_score": _mean([row.echo_mimic_score for row in rows]),
                "max_echo_mimic_score": max(row.echo_mimic_score for row in rows),
                "dominant_echo_band": echo_bands.most_common(1)[0][0],
                "mean_strength": _mean([row.strength for row in rows]),
                "mean_C_Z": _mean([row.zero_coherence for row in rows]),
                "mean_return_potential": _mean([row.return_potential for row in rows]),
                "mean_return_observed": _mean([row.return_observed for row in rows]),
            }
        )
    return out


def _role_rows(candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    roles = sorted({str(row["truth_role"]) for row in candidate_rows})
    out: list[dict[str, object]] = []
    for role in roles:
        rows = [row for row in candidate_rows if str(row["truth_role"]) == role]
        runs = sum(int(row["runs"]) for row in rows)
        out.append(
            {
                "truth_role": role,
                "candidates": len(rows),
                "runs": runs,
                "expressed_count": sum(int(row["expressed_count"]) for row in rows),
                "breach_count": sum(int(row["breach_count"]) for row in rows),
                "echo_breach_count": sum(int(row["echo_breach_count"]) for row in rows),
                "latent_overcrown_count": sum(int(row["latent_overcrown_count"]) for row in rows),
                "expresser_rejection_count": sum(int(row["expresser_rejection_count"]) for row in rows),
                "mean_echo_mimic_score": _mean([float(row["mean_echo_mimic_score"]) for row in rows]),
                "max_echo_mimic_score": max(float(row["max_echo_mimic_score"]) for row in rows) if rows else 0.0,
            }
        )
    return out


def _write_truth_role_read(path: Path, candidate_rows: list[dict[str, object]], role_rows: list[dict[str, object]]) -> None:
    trap_breaches = [row for row in candidate_rows if int(row["breach_count"]) > 0]
    echo_breaches = [row for row in candidate_rows if int(row["echo_breach_count"]) > 0]
    latent_overcrowns = [row for row in candidate_rows if int(row["latent_overcrown_count"]) > 0]
    expresser_wounds = [row for row in candidate_rows if int(row["expresser_rejection_count"]) > 0]

    lines: list[str] = []
    lines.append("# ZeroGateSim Truth-Role Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This file repairs the candidate truth layer. It does not change the zero-gate expression law. It reads candidates as +1 expressers, 0 latent/probes, or -1 traps so the field is not judged by one binary scoreboard.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    for row in role_rows:
        if row["truth_role"] == "expresser":
            lines.append(f"Expresser candidates: `{row['candidates']}` across `{row['runs']}` role-runs; expresser rejection wounds: `{row['expresser_rejection_count']}`.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    for row in role_rows:
        if row["truth_role"] == "latent":
            lines.append(f"Latent/probe candidates: `{row['candidates']}` across `{row['runs']}` role-runs; overcrowned latent runs: `{row['latent_overcrown_count']}`.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    for row in role_rows:
        if row["truth_role"] == "trap":
            lines.append(f"Trap candidates: `{row['candidates']}` across `{row['runs']}` role-runs; expression breaches: `{row['breach_count']}`; echo breaches: `{row['echo_breach_count']}`.")
    lines.append("")
    lines.append("## Candidate pressure table")
    lines.append("")
    lines.append("| candidate | kind | role | dominant posture | expressed | breaches | echo breach | mean echo |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|")
    for row in candidate_rows:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['dominant_role_posture']} | "
            f"{row['expressed_count']} | {row['breach_count']} | {row['echo_breach_count']} | {float(row['mean_echo_mimic_score']):.3f} |"
        )
    lines.append("")
    lines.append("## Breach focus")
    lines.append("")
    if trap_breaches:
        lines.append("Trap expression breaches detected. These are the dangerous cases: false one, not merely conservative holding.")
        for row in sorted(trap_breaches, key=lambda r: (-int(r["breach_count"]), str(r["candidate_id"])))[:9]:
            lines.append(f"- `{row['candidate_id']}` `{row['kind']}` breach_count=`{row['breach_count']}`, echo_breach_count=`{row['echo_breach_count']}`, mean_echo=`{float(row['mean_echo_mimic_score']):.3f}`")
    else:
        lines.append("No trap expression breaches detected.")
    lines.append("")
    if echo_breaches:
        lines.append("Echo-mimic pressure is present. These candidates may be riding the field rather than earning independent return:")
        for row in sorted(echo_breaches, key=lambda r: (-int(r["echo_breach_count"]), str(r["candidate_id"])))[:9]:
            lines.append(f"- `{row['candidate_id']}` `{row['kind']}` echo_breach_count=`{row['echo_breach_count']}`, max_echo=`{float(row['max_echo_mimic_score']):.3f}`")
    else:
        lines.append("No echo-mimic breaches detected.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    lines.append("The field now knows that not every non-trap should be expected to express and not every non-expression is failure. The dangerous wound is narrower: a trap crowned as +1, especially when echo-mimic pressure is high.")
    lines.append("")
    if latent_overcrowns:
        lines.append("Latent overcrown pressure exists and should be watched before any gate mutation.")
    if expresser_wounds:
        lines.append("Some expresser wounds remain; read them through lineage before changing the core.")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_echo_report(path: Path, candidate_rows: list[dict[str, object]]) -> None:
    ranked = sorted(candidate_rows, key=lambda row: (-int(row["echo_breach_count"]), -float(row["max_echo_mimic_score"]), str(row["candidate_id"])))
    lines: list[str] = []
    lines.append("# ZeroGateSim Echo-Mimic Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("Echo-mimic is a diagnostic, not a new gate. It marks candidates whose signal is strongly explained by the leave-one-out field average. Echo is not always bad; it becomes dangerous when a trap is crowned as expression by borrowing the field's coherence.")
    lines.append("")
    lines.append("| candidate | kind | role | expressed | echo breaches | max echo | dominant echo band |")
    lines.append("|---|---|---|---:|---:|---:|---|")
    for row in ranked[:27]:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['expressed_count']} | "
            f"{row['echo_breach_count']} | {float(row['max_echo_mimic_score']):.3f} | {row['dominant_echo_band']} |"
        )
    lines.append("")
    lines.append("## Repair pressure")
    lines.append("")
    lines.append("If echo breach persists, do not loosen the zero-gate. Add an independence / echo-debt witness first. False expression is more dangerous than conservative holding.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_truth_role_outputs(output_dir: Path, gate_rows: list[tuple[int, GateScores]]) -> dict[str, Path]:
    candidate_rows = _candidate_rows(gate_rows)
    role_rows = _role_rows(candidate_rows)
    candidate_csv = output_dir / "matrix_truth_role_candidate_summary.csv"
    role_csv = output_dir / "matrix_truth_role_summary.csv"
    read_md = output_dir / "matrix_truth_role_read.md"
    echo_md = output_dir / "matrix_echo_mimic_report.md"
    write_dict_rows_csv(candidate_csv, candidate_rows)
    write_dict_rows_csv(role_csv, role_rows)
    _write_truth_role_read(read_md, candidate_rows, role_rows)
    _write_echo_report(echo_md, candidate_rows)
    return {
        "matrix_truth_role_candidate_summary": candidate_csv,
        "matrix_truth_role_summary": role_csv,
        "matrix_truth_role_read": read_md,
        "matrix_echo_mimic_report": echo_md,
    }
