from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


POWER_NAMES = {
    0: "runs",
    1: "witness_artifacts",
    2: "discriminator",
    3: "predictive_zero_ready",
    4: "role_blind_shadow",
    5: "holy_shit_detector",
}


@dataclass(frozen=True)
class PowerCheckResult:
    reached_power: int
    posture: str
    summary_rows: list[dict[str, object]]
    fail_rows: list[dict[str, object]]
    metrics: dict[str, object]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_dict_rows_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if value in {"", None}:
        return 0
    try:
        return int(float(str(value)))
    except ValueError:
        return 0


def _safe_int(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _exists_with_rows(path: Path) -> bool:
    return bool(_read_csv(path))


def _status(pass_condition: bool, *, fail_condition: bool = False) -> str:
    if fail_condition:
        return "fail"
    return "pass" if pass_condition else "hold"


def _artifact_flags(matrix_dir: Path) -> dict[str, bool]:
    return {
        "final_output": _exists_with_rows(matrix_dir / "matrix_final_output_summary.csv"),
        "earned_one": _exists_with_rows(matrix_dir / "matrix_earned_one_summary.csv"),
        "echo_independence": _exists_with_rows(matrix_dir / "matrix_echo_independence_summary.csv"),
        "temporal": _exists_with_rows(matrix_dir / "matrix_temporal_candidate_summary.csv"),
        "lineage": _exists_with_rows(matrix_dir / "matrix_lineage_candidate_summary.csv"),
        "seed_summary": _exists_with_rows(matrix_dir / "matrix_seed_summary.csv"),
        "role_blind_shadow": _exists_with_rows(matrix_dir / "matrix_role_blind_shadow_summary.csv"),
        "pressure_confirmation": _exists_with_rows(matrix_dir / "matrix_pressure_confirmation_summary.csv"),
    }


def _final_metrics(final_rows: list[dict[str, str]]) -> dict[str, object]:
    raw_expression = sum(_int(row, "raw_expression_pressure") for row in final_rows)
    earned_one = sum(_int(row, "final_earned_one_count") for row in final_rows)
    false_pressure = sum(_int(row, "raw_false_one_pressure") for row in final_rows)
    false_demoted = sum(_int(row, "false_one_demoted_count") for row in final_rows)
    latent_pressure = sum(_int(row, "latent_overcrown_pressure") for row in final_rows)
    latent_demoted = sum(_int(row, "latent_overcrown_demoted_count") for row in final_rows)
    relation_debt = sum(_int(row, "relation_debt_count") for row in final_rows)

    final_false_crowns = 0
    trap_final_crowns = 0
    earned_candidates = 0
    false_pressure_candidates = 0
    latent_pressure_candidates = 0
    final_bands: Counter[str] = Counter()

    for row in final_rows:
        truth_role = str(row.get("truth_role", ""))
        final_symbol = str(row.get("final_trinary_symbol", ""))
        final_band = str(row.get("final_band", ""))
        final_value = str(row.get("final_trinary_value", ""))
        final_bands[final_band] += 1
        if _int(row, "final_earned_one_count") > 0:
            earned_candidates += 1
        if _int(row, "raw_false_one_pressure") > 0:
            false_pressure_candidates += 1
        if _int(row, "latent_overcrown_pressure") > 0:
            latent_pressure_candidates += 1
        if truth_role == "trap" and (final_symbol == "+1" or final_value == "1" or final_band == "earned_one"):
            final_false_crowns += 1
            trap_final_crowns += 1

    return {
        "candidate_rows": len(final_rows),
        "raw_expression_pressure": raw_expression,
        "final_earned_one_events": earned_one,
        "earned_candidate_count": earned_candidates,
        "raw_false_one_pressure": false_pressure,
        "false_one_demoted_count": false_demoted,
        "false_pressure_candidate_count": false_pressure_candidates,
        "latent_overcrown_pressure": latent_pressure,
        "latent_overcrown_demoted_count": latent_demoted,
        "latent_pressure_candidate_count": latent_pressure_candidates,
        "relation_debt_count": relation_debt,
        "final_false_one_crowns": final_false_crowns,
        "trap_final_crowns": trap_final_crowns,
        "final_band_counts": dict(sorted(final_bands.items())),
    }


def _baseline_pressure(matrix_dir: Path) -> tuple[str, str]:
    seed_rows = _read_csv(matrix_dir / "matrix_seed_summary.csv")
    if not seed_rows:
        return "hold", "matrix_seed_summary.csv not present; baseline comparison pressure not readable"
    counts = Counter(str(row.get("best_designed_model", "")) for row in seed_rows if row.get("best_designed_model"))
    if not counts:
        return "hold", "best_designed_model column missing or empty"
    top_model, top_count = counts.most_common(1)[0]
    safe_models = {"zero_gate_expression", "zero_gate_min"}
    if top_model in safe_models:
        return "pass", f"top designed-label baseline is {top_model} in {top_count} seed rows"
    return "hold", f"baseline pressure: top designed-label model is {top_model} in {top_count} seed rows"


def _role_blind_status(matrix_dir: Path) -> tuple[str, str]:
    rows = _read_csv(matrix_dir / "matrix_role_blind_shadow_summary.csv")
    if not rows:
        return "hold", "role-blind shadow detector has not been implemented for this matrix yet"
    status_counts = Counter(str(row.get("shadow_status", row.get("status", ""))) for row in rows)
    if status_counts.get("pass", 0) or status_counts.get("supported", 0):
        return "pass", f"role-blind shadow rows present: {dict(status_counts)}"
    if status_counts.get("fail", 0):
        return "fail", f"role-blind shadow reports failures: {dict(status_counts)}"
    return "hold", f"role-blind shadow rows present but not decisive: {dict(status_counts)}"


def _pressure_confirmation_status(matrix_dir: Path) -> tuple[str, str]:
    rows = _read_csv(matrix_dir / "matrix_pressure_confirmation_summary.csv")
    if not rows:
        return "hold", "no later-pressure confirmation file yet; holy-shit detector remains future work"
    confirmed = sum(_safe_int(row.get("confirmed_refusal", 0)) for row in rows)
    if confirmed > 0:
        return "pass", f"{confirmed} tempting refusals were later confirmed under fresh pressure"
    return "hold", "pressure confirmation file exists, but no confirmed tempting refusal was recorded"


def build_power_check(matrix_dir: Path) -> PowerCheckResult:
    matrix_dir = Path(matrix_dir)
    flags = _artifact_flags(matrix_dir)
    final_rows = _read_csv(matrix_dir / "matrix_final_output_summary.csv")
    metrics = _final_metrics(final_rows) if final_rows else {
        "candidate_rows": 0,
        "raw_expression_pressure": 0,
        "final_earned_one_events": 0,
        "earned_candidate_count": 0,
        "raw_false_one_pressure": 0,
        "false_one_demoted_count": 0,
        "false_pressure_candidate_count": 0,
        "latent_overcrown_pressure": 0,
        "latent_overcrown_demoted_count": 0,
        "latent_pressure_candidate_count": 0,
        "relation_debt_count": 0,
        "final_false_one_crowns": 0,
        "trap_final_crowns": 0,
        "final_band_counts": {},
    }

    final_false_crowns = int(metrics["final_false_one_crowns"])
    false_pressure = int(metrics["raw_false_one_pressure"])
    false_demoted = int(metrics["false_one_demoted_count"])
    latent_pressure = int(metrics["latent_overcrown_pressure"])
    latent_demoted = int(metrics["latent_overcrown_demoted_count"])
    earned = int(metrics["final_earned_one_events"])
    raw = int(metrics["raw_expression_pressure"])

    witness_stack_complete = all(flags[name] for name in ("final_output", "earned_one", "echo_independence", "temporal", "lineage"))
    discriminator_ok = bool(
        final_rows
        and earned > 0
        and false_pressure > 0
        and false_demoted >= false_pressure
        and final_false_crowns == 0
    )
    predictive_zero_ready = bool(
        witness_stack_complete
        and (latent_pressure > 0 or int(metrics["relation_debt_count"]) > 0)
        and latent_demoted >= latent_pressure
    )
    role_blind_state, role_blind_reason = _role_blind_status(matrix_dir)
    confirmation_state, confirmation_reason = _pressure_confirmation_status(matrix_dir)
    baseline_state, baseline_reason = _baseline_pressure(matrix_dir)

    power_rows = [
        {
            "power_state": "POWER 0",
            "name": POWER_NAMES[0],
            "status": _status(bool(final_rows)),
            "evidence": f"matrix_final_output_summary rows={len(final_rows)}",
            "boundary": "execution evidence only; not truth",
        },
        {
            "power_state": "POWER 1",
            "name": POWER_NAMES[1],
            "status": _status(witness_stack_complete),
            "evidence": ", ".join(f"{key}={value}" for key, value in sorted(flags.items()) if key in {"final_output", "earned_one", "echo_independence", "temporal", "lineage"}),
            "boundary": "artifact completeness does not prove the math; native invariant tests remain separate",
        },
        {
            "power_state": "POWER 2",
            "name": POWER_NAMES[2],
            "status": _status(discriminator_ok, fail_condition=final_false_crowns > 0 or false_demoted < false_pressure),
            "evidence": f"earned={earned}; raw_false={false_pressure}; false_demoted={false_demoted}; final_false_crowns={final_false_crowns}",
            "boundary": "role-aware adversarial proof discriminator, not role-blind discovery",
        },
        {
            "power_state": "POWER 3",
            "name": POWER_NAMES[3],
            "status": _status(predictive_zero_ready, fail_condition=latent_demoted < latent_pressure),
            "evidence": f"latent_pressure={latent_pressure}; latent_demoted={latent_demoted}; relation_debt={metrics['relation_debt_count']}; temporal_artifact={flags['temporal']}",
            "boundary": "ready for zero-band prediction tests; not yet proof that zero predicts future behavior",
        },
        {
            "power_state": "POWER 4",
            "name": POWER_NAMES[4],
            "status": role_blind_state,
            "evidence": role_blind_reason,
            "boundary": "shadow detector only; must not replace role-aware proof witness yet",
        },
        {
            "power_state": "POWER 5",
            "name": POWER_NAMES[5],
            "status": confirmation_state,
            "evidence": confirmation_reason,
            "boundary": "requires later-pressure confirmation of a tempting refusal",
        },
    ]

    fail_rows = [
        {
            "fail_state": "FAIL A",
            "name": "raw_plus_overcrown",
            "status": _status(false_demoted >= false_pressure and latent_demoted >= latent_pressure, fail_condition=false_demoted < false_pressure or latent_demoted < latent_pressure),
            "evidence": f"raw={raw}; false_pressure={false_pressure}; false_demoted={false_demoted}; latent_pressure={latent_pressure}; latent_demoted={latent_demoted}",
            "repair_hint": "raw +1 must remain pressure until final witness permits crown",
        },
        {
            "fail_state": "FAIL B",
            "name": "final_false_one_crown",
            "status": _status(final_false_crowns == 0, fail_condition=final_false_crowns > 0),
            "evidence": f"final_false_one_crowns={final_false_crowns}; trap_final_crowns={metrics['trap_final_crowns']}",
            "repair_hint": "inspect final-output rows before touching gates",
        },
        {
            "fail_state": "FAIL C",
            "name": "flat_zero_bucket",
            "status": _status(latent_pressure > 0 or int(metrics["relation_debt_count"]) > 0),
            "evidence": f"latent_pressure={latent_pressure}; relation_debt={metrics['relation_debt_count']}",
            "repair_hint": "zero must preserve latent, relation-debt, quarantine, and not-yet pressure",
        },
        {
            "fail_state": "FAIL D",
            "name": "role_labels_do_all_work",
            "status": role_blind_state,
            "evidence": role_blind_reason,
            "repair_hint": "build role-blind shadow detector before claiming unsupervised false-one detection",
        },
        {
            "fail_state": "FAIL E",
            "name": "simpler_baseline_pressure",
            "status": baseline_state,
            "evidence": baseline_reason,
            "repair_hint": "if a simple baseline wins, repair the witness instead of decorating it",
        },
        {
            "fail_state": "FAIL F",
            "name": "seed_or_threshold_dependency",
            "status": "hold",
            "evidence": "requires planned sensitivity and fresh-pressure tests",
            "repair_hint": "do not treat one seed range or one threshold as final proof",
        },
        {
            "fail_state": "FAIL G",
            "name": "overclaim_language",
            "status": "hold",
            "evidence": "requires human review of README, paper, and public release language",
            "repair_hint": "toy-field software evidence must not become cosmology claim",
        },
    ]

    reached = -1
    for row in power_rows:
        if row["status"] == "pass":
            reached = int(str(row["power_state"]).split()[1])
        else:
            break

    hard_fail = any(row["status"] == "fail" for row in power_rows + fail_rows)
    posture = "fail" if hard_fail else "power" if reached >= 2 else "hold"
    metrics = dict(metrics)
    metrics.update(
        {
            "matrix_dir": str(matrix_dir),
            "reached_power": reached,
            "reached_power_name": POWER_NAMES.get(reached, "none"),
            "posture": posture,
            "artifact_flags": flags,
        }
    )
    return PowerCheckResult(
        reached_power=reached,
        posture=posture,
        summary_rows=power_rows,
        fail_rows=fail_rows,
        metrics=metrics,
    )


def _write_read(path: Path, result: PowerCheckResult) -> None:
    metrics = result.metrics
    reached = result.reached_power
    lines: list[str] = []
    lines.append("# ZeroGateSim Power-Up / Fail Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report does not prove cosmology, physical dimensional genesis, or final trinary logic. It reads matrix/proof artifacts and asks whether the current run is merely producing files or becoming harder to fool inside generated toy fields.")
    lines.append("")
    lines.append("## Current posture")
    lines.append("")
    lines.append(f"Posture: `{result.posture}`")
    lines.append(f"Reached power: `POWER {reached}` — `{metrics.get('reached_power_name', 'none')}`")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"Candidate rows: `{metrics['candidate_rows']}`")
    lines.append(f"Raw expression pressure: `{metrics['raw_expression_pressure']}`")
    lines.append(f"Final earned-one events: `{metrics['final_earned_one_events']}`")
    lines.append(f"Raw false-one pressure: `{metrics['raw_false_one_pressure']}`")
    lines.append(f"False-one demoted count: `{metrics['false_one_demoted_count']}`")
    lines.append(f"Latent overcrown pressure: `{metrics['latent_overcrown_pressure']}`")
    lines.append(f"Latent overcrown demoted count: `{metrics['latent_overcrown_demoted_count']}`")
    lines.append(f"Final false-one crowns: `{metrics['final_false_one_crowns']}`")
    lines.append("")
    lines.append("## Power ladder")
    lines.append("")
    lines.append("| power | name | status | evidence | boundary |")
    lines.append("|---|---|---|---|---|")
    for row in result.summary_rows:
        lines.append(f"| {row['power_state']} | {row['name']} | {row['status']} | {row['evidence']} | {row['boundary']} |")
    lines.append("")
    lines.append("## Fail ladder")
    lines.append("")
    lines.append("| fail | name | status | evidence | repair hint |")
    lines.append("|---|---|---|---|---|")
    for row in result.fail_rows:
        lines.append(f"| {row['fail_state']} | {row['name']} | {row['status']} | {row['evidence']} | {row['repair_hint']} |")
    lines.append("")
    lines.append("## Holy-shit boundary")
    lines.append("")
    lines.append("The holy-shit detector is not a big run count. It is reached only when the simulator refuses or holds a tempting candidate before collapse is obvious, names the wound, and later fresh pressure confirms that refusal. Until role-blind shadow and later-pressure confirmation exist, POWER 5 must remain HOLD.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if result.posture == "fail":
        lines.append("This matrix is in FAIL. Inspect the failing row before changing the core gate; the wound may be in artifact completeness, witness stack, baselines, or real false-one leakage.")
    elif reached >= 3:
        lines.append("This matrix has reached the predictive-zero-ready floor: the witness stack is present, false-one pressure is demoted, and zero-state pressure is visible enough to justify the next zero-band prediction tests.")
    elif reached >= 2:
        lines.append("This matrix has reached discriminator floor: it crowns earned-one while demoting visible false-one pressure, but predictive-zero and role-blind work remain ahead.")
    else:
        lines.append("This matrix is in HOLD. It may run, but it has not yet earned a power-up claim.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_power_check_outputs(matrix_dir: Path) -> dict[str, Path]:
    matrix_dir = Path(matrix_dir)
    result = build_power_check(matrix_dir)
    summary_path = matrix_dir / "matrix_power_check_summary.csv"
    fail_path = matrix_dir / "matrix_power_check_fail_summary.csv"
    read_path = matrix_dir / "matrix_power_check_read.md"
    _write_dict_rows_csv(summary_path, result.summary_rows)
    _write_dict_rows_csv(fail_path, result.fail_rows)
    _write_read(read_path, result)
    return {
        "matrix_power_check_summary": summary_path,
        "matrix_power_check_fail_summary": fail_path,
        "matrix_power_check_read": read_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read a ZeroGateSim matrix/proof output directory and write a Power-Up / Fail witness report."
    )
    parser.add_argument("--matrix-dir", type=Path, default=Path("."), help="Directory containing matrix_final_output_summary.csv and related witness artifacts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_power_check_outputs(args.matrix_dir)
    result = build_power_check(args.matrix_dir)
    print("ZeroGateSim power-check complete.")
    print(f"- posture: {result.posture}")
    print(f"- reached: POWER {result.reached_power} ({POWER_NAMES.get(result.reached_power, 'none')})")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 1 if result.posture == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
