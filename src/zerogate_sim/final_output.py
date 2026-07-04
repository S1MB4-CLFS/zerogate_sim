from __future__ import annotations

from collections import Counter
from pathlib import Path

from zerogate_sim.earned_one import build_earned_one_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv


def _final_band(row: dict[str, object]) -> tuple[int, str, str, str]:
    """Translate raw/earned evidence into final trinary output.

    Raw expression remains visible as pressure. Earned one becomes the only
    final +1 crown. False-one pressure is demoted into Resist, not accepted.
    """

    truth_role = str(row.get("truth_role", ""))
    raw = int(row.get("raw_expressed_count", 0) or 0)
    earned = int(row.get("earned_one_count", 0) or 0)
    false_one = int(row.get("false_one_count", 0) or 0)
    latent = int(row.get("latent_overcrown_count", 0) or 0)
    relation_debt = int(row.get("relation_debt_count", 0) or 0)
    echo_band = str(row.get("echo_independence_band", ""))

    if earned > 0:
        return 1, "+1", "earned_one", "raw expression survived truth-role and echo-independence witness"
    if false_one > 0:
        return -1, "-1", "false_one_demoted", "raw expression was trap pressure; final output refuses the crown"
    if latent > 0:
        return 0, "0+", "latent_overcrown_demoted", "latent/probe expressed locally but remains zero-held, not final one"
    if relation_debt > 0 or echo_band in {"relation_debt", "echo_debt_hold", "relation_supported"}:
        return 0, "0", "relation_debt_hold", "expression depends on support weather; keep in witness"
    if truth_role == "trap":
        return -1, "-1", "trap_contained", "trap did not earn expression"
    if truth_role == "latent":
        return 0, "0", "latent_contained", "latent/probe did not earn expression"
    if truth_role == "expresser" and raw <= 0:
        return 0, "0", "expresser_wound", "expected expresser did not earn one in this weather"
    return 0, "0", "witness_hold", "no final crown assigned"


def build_final_output_rows_from_earned_rows(earned_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in earned_rows:
        value, symbol, band, reason = _final_band(row)
        raw = int(row["raw_expressed_count"])
        earned = int(row["earned_one_count"])
        false_one = int(row["false_one_count"])
        latent = int(row["latent_overcrown_count"])
        relation_debt = int(row["relation_debt_count"])
        out.append(
            {
                "candidate_id": row["candidate_id"],
                "kind": row["kind"],
                "truth_role": row["truth_role"],
                "runs": row["runs"],
                "raw_expression_pressure": raw,
                "final_earned_one_count": earned,
                "raw_false_one_pressure": false_one,
                "false_one_demoted_count": false_one,
                "latent_overcrown_pressure": latent,
                "latent_overcrown_demoted_count": latent,
                "relation_debt_count": relation_debt,
                "final_trinary_value": value,
                "final_trinary_symbol": symbol,
                "final_band": band,
                "final_reason": reason,
                "echo_independence_band": row["echo_independence_band"],
                "relation_dependency_score": row["relation_dependency_score"],
                "echo_independence_score": row["echo_independence_score"],
                "relation_minus_raw_expression": row["relation_minus_raw_expression"],
                "relation_zero_raw_expression": row["relation_zero_raw_expression"],
                "relation_plus_raw_expression": row["relation_plus_raw_expression"],
                "mean_strength": row["mean_strength"],
                "mean_zero_coherence": row["mean_zero_coherence"],
                "mean_return_potential": row["mean_return_potential"],
                "mean_return_observed": row["mean_return_observed"],
            }
        )
    return out


def _final_false_one_crowns(rows: list[dict[str, object]]) -> int:
    return sum(
        int(row.get("raw_false_one_pressure", 0) or 0)
        for row in rows
        if int(row.get("final_trinary_value", 0) or 0) == 1 and str(row.get("truth_role", "")) == "trap"
    )


def _confirmation_status(rows: list[dict[str, object]]) -> tuple[str, str]:
    total_earned = sum(int(row["final_earned_one_count"]) for row in rows)
    false_pressure = sum(int(row["raw_false_one_pressure"]) for row in rows)
    final_false_crowns = _final_false_one_crowns(rows)
    latent_pressure = sum(int(row["latent_overcrown_pressure"]) for row in rows)
    expressers = [row for row in rows if row["truth_role"] == "expresser"]
    earned_expressers = [row for row in expressers if int(row["final_earned_one_count"]) > 0]

    if total_earned > 0 and false_pressure > 0 and final_false_crowns == 0 and len(earned_expressers) >= 3:
        return (
            "toy_domain_confirmed",
            "earned-one witness separated real expressers from false-one pressure and demoted traps without silencing the core expressers",
        )
    if total_earned > 0 and final_false_crowns == 0:
        return (
            "supported_pending_pressure",
            "earned-one witness is coherent, but the matrix needs more adversarial pressure before first-research-alpha victory",
        )
    return (
        "hold",
        "final output did not yet earn enough separation to claim toy-domain confirmation",
    )


def build_final_output_rows(gate_rows: list[tuple[int, GateScores]]) -> list[dict[str, object]]:
    return build_final_output_rows_from_earned_rows(build_earned_one_rows(gate_rows))


def write_final_output_rows(output_dir: Path, rows: list[dict[str, object]]) -> dict[str, Path]:
    csv_path = output_dir / "matrix_final_output_summary.csv"
    read_path = output_dir / "matrix_final_output_read.md"
    confirmation_path = output_dir / "matrix_theory_confirmation_read.md"
    write_dict_rows_csv(csv_path, rows)
    _write_final_output_read(read_path, rows)
    _write_confirmation_read(confirmation_path, rows)
    return {
        "matrix_final_output_summary": csv_path,
        "matrix_final_output_read": read_path,
        "matrix_theory_confirmation_read": confirmation_path,
    }



def _write_final_output_read(path: Path, rows: list[dict[str, object]]) -> None:
    bands = Counter(str(row["final_band"]) for row in rows)
    total_raw = sum(int(row["raw_expression_pressure"]) for row in rows)
    total_earned = sum(int(row["final_earned_one_count"]) for row in rows)
    false_pressure = sum(int(row["raw_false_one_pressure"]) for row in rows)
    false_demoted = sum(int(row["false_one_demoted_count"]) for row in rows)
    latent_pressure = sum(int(row["latent_overcrown_pressure"]) for row in rows)
    latent_demoted = sum(int(row["latent_overcrown_demoted_count"]) for row in rows)
    final_false_crowns = _final_false_one_crowns(rows)
    earned_candidates = [row for row in rows if int(row["final_earned_one_count"]) > 0]
    demoted_false = [row for row in rows if int(row["false_one_demoted_count"]) > 0]
    demoted_latent = [row for row in rows if int(row["latent_overcrown_demoted_count"]) > 0]
    status, status_reason = _confirmation_status(rows)

    lines: list[str] = []
    lines.append("# ZeroGateSim Final Trinary Output")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is the primary output witness. Raw expression is pressure, not final truth. Earned-one is the only accepted +1 crown. False-one and latent overcrown events remain visible, but they are demoted before the final output.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Final earned-one events: `{total_earned}` from `{len(earned_candidates)}` candidates.")
    lines.append(f"Raw expression pressure remains visible: `{total_raw}` events.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Latent overcrown pressure: `{latent_pressure}`; demoted before final crown: `{latent_demoted}`.")
    lines.append("The zero-zone does not erase these. It holds them as 0-state pressure.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Raw false-one pressure: `{false_pressure}`; false-one events demoted: `{false_demoted}`; final false-one crowns: `{final_false_crowns}`.")
    lines.append("")
    lines.append("## Confirmation posture")
    lines.append("")
    lines.append(f"Status: `{status}`")
    lines.append("")
    lines.append(status_reason + ".")
    lines.append("")
    if status == "toy_domain_confirmed":
        lines.append("This confirms the current software theory inside the toy-field domain. It does not confirm cosmology or physical reality. The primate may celebrate the containment; it may not notarize the universe.")
    else:
        lines.append("This does not yet confirm the software theory in this run. It marks the current hold state without hiding the pressure.")
    lines.append("")
    lines.append("## Final band counts")
    lines.append("")
    for band, count in sorted(bands.items()):
        lines.append(f"- `{band}`: `{count}`")
    lines.append("")
    lines.append("## Candidate table")
    lines.append("")
    lines.append("| candidate | kind | role | final | band | raw pressure | earned one | false demoted | latent demoted | echo band | r- | r0 | r+ |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|")
    ranked = sorted(
        rows,
        key=lambda row: (
            0 if int(row["false_one_demoted_count"]) > 0 else 1 if int(row["final_earned_one_count"]) > 0 else 2 if int(row["latent_overcrown_demoted_count"]) > 0 else 3,
            -int(row["raw_expression_pressure"]),
            str(row["candidate_id"]),
        ),
    )
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['final_trinary_symbol']} | {row['final_band']} | "
            f"{row['raw_expression_pressure']} | {row['final_earned_one_count']} | {row['false_one_demoted_count']} | {row['latent_overcrown_demoted_count']} | "
            f"{row['echo_independence_band']} | {row['relation_minus_raw_expression']} | {row['relation_zero_raw_expression']} | {row['relation_plus_raw_expression']} |"
        )
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if demoted_false:
        names = ", ".join(f"`{row['candidate_id']}`" for row in demoted_false[:9])
        lines.append(f"False-one pressure was detected and refused final crown: {names}.")
    if earned_candidates:
        names = ", ".join(f"`{row['candidate_id']}`" for row in earned_candidates[:9])
        lines.append(f"Earned-one survived as final +1: {names}.")
    if demoted_latent:
        names = ", ".join(f"`{row['candidate_id']}`" for row in demoted_latent[:9])
        lines.append(f"Latent/probe overcrown was held in zero: {names}.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_confirmation_read(path: Path, rows: list[dict[str, object]]) -> None:
    status, reason = _confirmation_status(rows)
    total_raw = sum(int(row["raw_expression_pressure"]) for row in rows)
    total_earned = sum(int(row["final_earned_one_count"]) for row in rows)
    false_pressure = sum(int(row["raw_false_one_pressure"]) for row in rows)
    final_false_crowns = _final_false_one_crowns(rows)
    latent_pressure = sum(int(row["latent_overcrown_pressure"]) for row in rows)
    earned = [row for row in rows if int(row["final_earned_one_count"]) > 0]
    false_demoted = [row for row in rows if int(row["false_one_demoted_count"]) > 0]
    latent_demoted = [row for row in rows if int(row["latent_overcrown_demoted_count"]) > 0]

    lines: list[str] = []
    lines.append("# ZeroGateSim Theory Confirmation Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("Confirmation here means internal toy-domain confirmation of the current zero-gate software theory: earned expression can be separated from false one and latent overcrown under structured trinary weather. It does not mean proof of cosmology, physics, or final trinary mathematics.")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"The final witness accepts `{total_earned}` earned-one events from `{len(earned)}` candidates.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"The final witness keeps `{latent_pressure}` latent overcrown events in zero-state instead of pretending they are final one.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"The final witness detects `{false_pressure}` raw false-one pressure events and allows `{final_false_crowns}` final false-one crowns.")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(f"Status: `{status}`")
    lines.append("")
    lines.append(reason + ".")
    lines.append("")
    if false_demoted:
        lines.append("Raw false one was not hidden; it was named and demoted. That matters more than a pretty clean run, because the theory met an enemy and refused it final crown.")
    if latent_demoted:
        lines.append("Latent overcrown was not erased; it was held. That preserves the zero-zone instead of forcing every pressure into binary pass/fail.")
    lines.append("")
    lines.append("## Next boundary")
    lines.append("")
    lines.append("First-research-alpha victory is close when this final-output posture repeats across fresh seeds and at least one adversarial candidate corpus. The core gate should remain held unless final-output breaches reappear.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_output_outputs(output_dir: Path, gate_rows: list[tuple[int, GateScores]]) -> dict[str, Path]:
    return write_final_output_rows(output_dir, build_final_output_rows(gate_rows))
