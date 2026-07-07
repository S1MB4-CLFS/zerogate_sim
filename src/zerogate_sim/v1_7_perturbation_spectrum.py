from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.4-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "perturbation_spectrum_witness_locked_no_core_closeout"
GATE_KIND = "perturbation_spectrum_witness_not_closeout"
NEXT_GATE = "v1.7.5-alpha — Masked Role-Dependence Audit"

OUTPUT_FILES = {
    "read": "v1_7_perturbation_spectrum_read.md",
    "decision": "v1_7_perturbation_spectrum_decision.json",
    "witness_spectrum": "v1_7_witness_spectrum.csv",
    "perturbation_curve": "v1_7_perturbation_curve.csv",
    "weather_curve": "v1_7_weather_curve_summary.csv",
    "quiet_lane_activation": "v1_7_expected_quiet_lane_activation.csv",
    "input_schema": "v1_7_perturbation_spectrum_input_schema.csv",
    "evaluation": "v1_7_perturbation_spectrum_evaluation.csv",
    "audit": "v1_7_perturbation_spectrum_audit.json",
    "bundle": "v1_7_perturbation_spectrum_bundle.zip",
}

REQUIRED_SPECTRUM_LANES = [
    "earned_one",
    "raw_expression_pressure",
    "latent_overcrown",
    "relation_debt",
    "return_debt",
    "echo_dependence",
    "lineage_instability",
    "false_one_pressure",
    "final_false_one_crowns",
]

WEATHER_RUNG_ROWS = [
    {
        "weather_rung": "triad27",
        "shape": "3^3",
        "role": "local expression weather",
        "pressure_axes": "local noise / relation / expansion controls",
        "v1_7_4_use": "minimum curve rung; checks that raw expression and structured zero lanes remain visible before deeper pressure",
        "fail_if": "triad27 already collapses all lanes into generic success/failure",
    },
    {
        "weather_rung": "deep81",
        "shape": "3^4",
        "role": "perturbation / late-shock bridge",
        "pressure_axes": "adds perturbation pressure to local weather",
        "v1_7_4_use": "tests whether raw pressure, relation debt, return debt, and false-one demotion move under pressure without becoming false crowns",
        "fail_if": "late perturbation creates new-looking pressure and native witness crowns it without return / lineage / independence",
    },
    {
        "weather_rung": "wide243",
        "shape": "3^5",
        "role": "temporal-depth / time-axis stress",
        "pressure_axes": "adds temporal-depth pressure to perturbation weather",
        "v1_7_4_use": "tests safe degradation across the full controlled weather ladder before masked-role audit",
        "fail_if": "temporal pressure erases earned-one or creates final false-one crowns",
    },
]

WITNESS_SPECTRUM_ROWS = [
    {
        "lane": "earned_one",
        "expected_curve_behavior": "should persist under ordinary controlled weather and degrade only when required structure is actually destroyed",
        "safe_failure_state": "0 hold or lower earned count when depth / lineage / independence cannot be witnessed",
        "must_not_do": "keep +1 alive by ignoring missing return, relation, lineage, or independence",
        "primary_countermetric": "earned_one_preservation_rate",
        "v1_7_4_status": "required_curve_lane",
    },
    {
        "lane": "raw_expression_pressure",
        "expected_curve_behavior": "may rise, move, or destabilize as pressure increases",
        "safe_failure_state": "remains pressure until final witness earns or holds/demotes it",
        "must_not_do": "be mistaken for final +1 merely because it is loud",
        "primary_countermetric": "raw_pressure_count",
        "v1_7_4_status": "required_curve_lane",
    },
    {
        "lane": "latent_overcrown",
        "expected_curve_behavior": "may activate only in designed not-yet / probe regions and remains structured zero until reproduced or narrowed",
        "safe_failure_state": "0 structured hold or explicit HOLD if seed-sensitive",
        "must_not_do": "borrow the old proof record as a current full-answer crown",
        "primary_countermetric": "latent_overcrown_pressure_count",
        "v1_7_4_status": "required_but_fragile_curve_lane",
    },
    {
        "lane": "relation_debt",
        "expected_curve_behavior": "should increase or become visible when relation is borrowed, unstable, global-only, or under-owned",
        "safe_failure_state": "0 relation-debt hold",
        "must_not_do": "collapse into return debt or generic failure",
        "primary_countermetric": "relation_debt_count",
        "v1_7_4_status": "required_curve_lane",
    },
    {
        "lane": "return_debt",
        "expected_curve_behavior": "should become visible when D/P/R create Gamma but observed return, memory, closure, or depth is incomplete",
        "safe_failure_state": "0 return-debt hold",
        "must_not_do": "treat zero crossing, oscillation, or Gamma alone as observed return",
        "primary_countermetric": "return_debt_count",
        "v1_7_4_status": "required_curve_lane",
    },
    {
        "lane": "echo_dependence",
        "expected_curve_behavior": "should light up when candidate coherence is borrowed from field relation or weather",
        "safe_failure_state": "0 relation debt or -1 false-one demotion depending on trap pressure",
        "must_not_do": "promote field echo as independent earned-one",
        "primary_countermetric": "echo_dependence_count",
        "v1_7_4_status": "required_diagnostic_lane",
    },
    {
        "lane": "lineage_instability",
        "expected_curve_behavior": "should light up when early/witness/late windows disagree or raw expression arrives without temporal maturity",
        "safe_failure_state": "0 not-yet / lineage hold",
        "must_not_do": "crown one-window fireworks",
        "primary_countermetric": "lineage_instability_count",
        "v1_7_4_status": "required_diagnostic_lane",
    },
    {
        "lane": "false_one_pressure",
        "expected_curve_behavior": "may rise under adversarial pressure and must be demoted before final crown",
        "safe_failure_state": "-1 resist / demotion",
        "must_not_do": "hide pressure or crown it",
        "primary_countermetric": "raw_false_one_pressure_count",
        "v1_7_4_status": "required_curve_lane",
    },
    {
        "lane": "final_false_one_crowns",
        "expected_curve_behavior": "must remain zero across controlled perturbation curves",
        "safe_failure_state": "stop / resist if nonzero",
        "must_not_do": "average a false crown away in totals",
        "primary_countermetric": "final_false_one_crowns",
        "v1_7_4_status": "stop_condition_lane",
    },
]

PERTURBATION_CURVE_ROWS = [
    {
        "curve_rule": "spectrum_not_scalar",
        "meaning": "report lane behavior across pressure rather than one victory count",
        "required_columns": "weather_rung, pressure_level, earned_one, raw_expression_pressure, relation_debt, return_debt, false_one_pressure, final_false_one_crowns",
        "pass_signal": "different lanes move differently under pressure while final false crowns remain zero",
        "failure_signal": "a single scalar hides lane collapse or false crown pressure",
    },
    {
        "curve_rule": "safe_degradation",
        "meaning": "raw metrics may degrade or rise, but final witness must fail safely",
        "required_columns": "final_earned_one_events, structured_zero_total, false_one_pressure, final_false_one_crowns",
        "pass_signal": "+1 when earned, 0 when unresolved, -1 when false",
        "failure_signal": "perturbation produces fake novelty and gets final +1 without return / lineage / independence",
    },
    {
        "curve_rule": "quiet_lane_activation",
        "meaning": "lanes expected to stay quiet should not activate without corresponding pressure",
        "required_columns": "expected_quiet_lane, quiet_lane_activation_count, activation_reason",
        "pass_signal": "unexpected activation is reported as pressure requiring witness, not discovery",
        "failure_signal": "quiet-lane activation is celebrated as evidence without falsifier routing",
    },
    {
        "curve_rule": "fragile_latent_overcrown_hold",
        "meaning": "latent overcrown remains named but seed-sensitive until reproduced or narrowed",
        "required_columns": "latent_overcrown, weather_rung, seed_block",
        "pass_signal": "latent pressure is held or explicitly marked unresolved",
        "failure_signal": "latent overcrown is silently treated as stable current evidence",
    },
]

QUIET_LANE_ACTIVATION_ROWS = [
    {
        "expected_quiet_lane": "final_false_one_crowns",
        "should_stay_quiet_when": "all adversarial pressure is correctly held or demoted",
        "activation_meaning": "stop condition; a false-one crown defeats v1.7.4 and blocks core closeout",
        "action": "RESIST and inspect gate/final-witness path before continuing",
    },
    {
        "expected_quiet_lane": "earned_one_on_trap_pressure",
        "should_stay_quiet_when": "candidate is trap-shaped or raw false-one pressure is present",
        "activation_meaning": "trap pressure became a crown",
        "action": "RESIST; do not average away the false crown",
    },
    {
        "expected_quiet_lane": "relation_debt_without_relation_pressure",
        "should_stay_quiet_when": "relation is owned, stable, and local enough",
        "activation_meaning": "possible over-sensitive relation debt or unmodeled borrowed coherence",
        "action": "WITNESS; inspect before calling discovery",
    },
    {
        "expected_quiet_lane": "return_debt_without_gamma_gap",
        "should_stay_quiet_when": "observed return and return-depth are paid",
        "activation_meaning": "possible false-return detector overreach or hidden return gap",
        "action": "WITNESS; separate Gamma from B before interpretation",
    },
    {
        "expected_quiet_lane": "latent_overcrown_under_fresh_seeds",
        "should_stay_quiet_when": "the fresh profile does not produce not-yet/probe overcrown pressure",
        "activation_meaning": "candidate for reproduction pressure, not a stable crown",
        "action": "HOLD; keep seed-sensitive status explicit",
    },
]

INPUT_SCHEMA_ROWS = [
    {"column": "weather_rung", "required": True, "meaning": "triad27, deep81, or wide243"},
    {"column": "pressure_level", "required": True, "meaning": "ordered perturbation pressure label or numeric level"},
    {"column": "final_earned_one_events", "required": True, "meaning": "count of final +1 earned-one events"},
    {"column": "earned_lost", "required": False, "meaning": "earned controls lost under pressure, if known"},
    {"column": "raw_expression_pressure", "required": True, "meaning": "local raw expression pressure count"},
    {"column": "latent_overcrown", "required": False, "meaning": "latent/probe overcrown pressure held in zero"},
    {"column": "relation_debt", "required": True, "meaning": "structured zero relation-debt count"},
    {"column": "return_debt", "required": True, "meaning": "structured zero return-debt count"},
    {"column": "echo_dependence", "required": False, "meaning": "borrowed-relation / echo-dependence diagnostic count"},
    {"column": "lineage_instability", "required": False, "meaning": "temporal lineage instability / not-yet diagnostic count"},
    {"column": "false_one_pressure", "required": True, "meaning": "raw false-one or trap pressure detected"},
    {"column": "final_false_one_crowns", "required": True, "meaning": "final +1 crowns assigned to false-one pressure; must remain zero"},
]


def _to_int(value: object) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    return int(float(text))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _lane_visibility_flags(row: dict[str, object]) -> dict[str, bool]:
    return {
        "earned_one_visible": _to_int(row.get("final_earned_one_events")) > 0,
        "raw_pressure_visible": _to_int(row.get("raw_expression_pressure")) > 0,
        "latent_overcrown_visible": _to_int(row.get("latent_overcrown")) > 0,
        "relation_debt_visible": _to_int(row.get("relation_debt")) > 0,
        "return_debt_visible": _to_int(row.get("return_debt")) > 0,
        "echo_dependence_visible": _to_int(row.get("echo_dependence")) > 0,
        "lineage_instability_visible": _to_int(row.get("lineage_instability")) > 0,
        "false_one_pressure_visible": _to_int(row.get("false_one_pressure")) > 0,
        "final_false_one_crowns_visible": _to_int(row.get("final_false_one_crowns")) > 0,
    }


def classify_spectrum_row(row: dict[str, object]) -> str:
    flags = _lane_visibility_flags(row)
    final_false_crowns = _to_int(row.get("final_false_one_crowns"))
    earned = _to_int(row.get("final_earned_one_events"))
    earned_lost = _to_int(row.get("earned_lost"))
    structured_zero_total = _to_int(row.get("latent_overcrown")) + _to_int(row.get("relation_debt")) + _to_int(row.get("return_debt"))
    diagnostic_total = _to_int(row.get("echo_dependence")) + _to_int(row.get("lineage_instability"))
    false_pressure = _to_int(row.get("false_one_pressure"))
    raw_pressure = _to_int(row.get("raw_expression_pressure"))

    if final_false_crowns > 0:
        return "resist_false_crown_stop"
    if earned == 0 and earned_lost > 0:
        return "hold_dead_safe_or_overstress_possible"
    if earned > 0 and raw_pressure > 0 and (structured_zero_total > 0 or diagnostic_total > 0 or false_pressure > 0):
        return "expand_spectrum_lanes_visible_safe"
    if false_pressure > 0 and final_false_crowns == 0:
        return "witness_false_pressure_demoted"
    if structured_zero_total > 0:
        return "witness_structured_zero_visible"
    if flags["earned_one_visible"] and flags["raw_pressure_visible"]:
        return "witness_raw_and_earned_visible"
    return "hold_partial_or_no_pressure_visible"


def evaluate_perturbation_spectrum_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    evaluation: list[dict[str, object]] = []
    for row in rows:
        flags = _lane_visibility_flags(row)
        structured_zero_total = _to_int(row.get("latent_overcrown")) + _to_int(row.get("relation_debt")) + _to_int(row.get("return_debt"))
        evaluation.append(
            {
                "weather_rung": row.get("weather_rung", ""),
                "pressure_level": row.get("pressure_level", ""),
                "row_status": classify_spectrum_row(row),
                "earned_one_visible": flags["earned_one_visible"],
                "raw_pressure_visible": flags["raw_pressure_visible"],
                "structured_zero_total": structured_zero_total,
                "relation_debt_visible": flags["relation_debt_visible"],
                "return_debt_visible": flags["return_debt_visible"],
                "latent_overcrown_visible": flags["latent_overcrown_visible"],
                "echo_dependence_visible": flags["echo_dependence_visible"],
                "lineage_instability_visible": flags["lineage_instability_visible"],
                "false_one_pressure_visible": flags["false_one_pressure_visible"],
                "final_false_one_crowns": _to_int(row.get("final_false_one_crowns")),
            }
        )
    return evaluation


def collapse_spectrum_evaluation_decision(evaluation_rows: Iterable[dict[str, object]]) -> str:
    rows = list(evaluation_rows)
    if not rows:
        return "perturbation_spectrum_locked_evaluation_not_run"
    statuses = {str(row.get("row_status", "")) for row in rows}
    if "resist_false_crown_stop" in statuses:
        return "resist_perturbation_false_crown_stop"
    lane_flags = {
        "earned_one": any(bool(row.get("earned_one_visible")) for row in rows),
        "raw_expression_pressure": any(bool(row.get("raw_pressure_visible")) for row in rows),
        "relation_debt": any(bool(row.get("relation_debt_visible")) for row in rows),
        "return_debt": any(bool(row.get("return_debt_visible")) for row in rows),
        "false_one_pressure": any(bool(row.get("false_one_pressure_visible")) for row in rows),
        "zero_false_crowns": all(_to_int(row.get("final_false_one_crowns")) == 0 for row in rows),
    }
    if all(lane_flags.values()):
        if any(bool(row.get("latent_overcrown_visible")) for row in rows):
            return "expand_perturbation_spectrum_safe_failure_visible"
        return "witness_perturbation_spectrum_core_lanes_visible_latent_hold"
    if {"witness_false_pressure_demoted", "witness_structured_zero_visible"} & statuses:
        return "witness_perturbation_spectrum_partial"
    return "hold_perturbation_spectrum_partial_or_unpressured"


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines(evaluation_rows: list[dict[str, object]], evaluation_decision: str) -> list[str]:
    lines = [
        "# v1.7 Perturbation Spectrum Witness",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "`v1.7.4-alpha` does not close the core question. It locks the perturbation-spectrum surface so later evidence cannot hide behind one victory count.",
        "",
        "## Spectrum law",
        "",
        "Do not rely on one scalar. Report the lane spectrum across pressure:",
        "",
        "```text",
        "earned-one",
        "raw expression pressure",
        "latent overcrown",
        "relation debt",
        "return debt",
        "echo dependence",
        "lineage instability",
        "false-one pressure",
        "final false-one crowns",
        "```",
        "",
        "Raw metrics may move. The final witness must fail safely: `+1` when earned, `0` when unresolved, `-1` when false, never a false crown.",
        "",
        "## Weather ladder",
        "",
        "| rung | shape | role |",
        "|---|---|---|",
        *[f"| `{row['weather_rung']}` | `{row['shape']}` | {row['role']} |" for row in WEATHER_RUNG_ROWS],
        "",
        "## Evaluation decision",
        "",
        f"`{evaluation_decision}`",
        "",
    ]
    if evaluation_rows:
        lines.extend(
            [
                "| weather | pressure | status | final false crowns |",
                "|---|---|---|---:|",
                *[
                    f"| `{row['weather_rung']}` | `{row['pressure_level']}` | `{row['row_status']}` | {row['final_false_one_crowns']} |"
                    for row in evaluation_rows
                ],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No perturbation summary CSV was supplied. This gate locks the schema and decision grammar before evidence curves are attached.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This is controlled synthetic-field witness plumbing. It adds no physics claim, no role-blind discovery claim, no manuscript v2, and no native math mutation.",
            "",
            "## Next gate",
            "",
            f"`{NEXT_GATE}` pressures whether the lanes remain witness-computed when role labels are masked.",
        ]
    )
    return lines


def build_v1_7_perturbation_spectrum(output_dir: Path, *, spectrum_summary_csv: Path | None = None) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    evaluation_rows: list[dict[str, object]] = []
    if spectrum_summary_csv is not None:
        evaluation_rows = evaluate_perturbation_spectrum_rows(_read_csv(Path(spectrum_summary_csv)))
    evaluation_decision = collapse_spectrum_evaluation_decision(evaluation_rows)

    _write_markdown(paths["read"], _readme_lines(evaluation_rows, evaluation_decision))
    write_dict_rows_csv(paths["witness_spectrum"], WITNESS_SPECTRUM_ROWS)
    write_dict_rows_csv(paths["perturbation_curve"], PERTURBATION_CURVE_ROWS)
    write_dict_rows_csv(paths["weather_curve"], WEATHER_RUNG_ROWS)
    write_dict_rows_csv(paths["quiet_lane_activation"], QUIET_LANE_ACTIVATION_ROWS)
    write_dict_rows_csv(paths["input_schema"], INPUT_SCHEMA_ROWS)
    write_dict_rows_csv(paths["evaluation"], evaluation_rows)

    decision: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "decision": DECISION,
        "evaluation_decision": evaluation_decision,
        "gate_kind": GATE_KIND,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "new_heavy_evidence_added": False,
        "manuscript_v2_started": False,
        "core_question_closed": False,
        "required_spectrum_lanes": REQUIRED_SPECTRUM_LANES,
        "weather_rungs": [row["weather_rung"] for row in WEATHER_RUNG_ROWS],
        "spectrum_summary_csv": str(spectrum_summary_csv) if spectrum_summary_csv is not None else None,
        "evaluation_rows": len(evaluation_rows),
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "v1.7.4 separates raw movement under perturbation from final trinary witness behavior.",
        "integration_modularity": "This is a spectrum and curve-schema gate; it does not mutate native math, start manuscript v2, or claim the full v1.7 answer.",
        "witness_translation": "A pressure curve is useful only if it reports safe failure and false-crown stops, not just aggregate victories.",
        "trace": "weather rung -> pressure level -> lane spectrum -> safe-failure status -> core-question hold/expand/resist.",
        "overdo_risk": "Turning curve plumbing into a new evidence crown before masked-role and holdout pressure.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_perturbation_spectrum_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 perturbation spectrum witness package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_perturbation_spectrum"))
    parser.add_argument("--spectrum-summary-csv", type=Path, default=None, help="Optional perturbation spectrum summary CSV to evaluate against v1.7.4 rules.")
    args = parser.parse_args(argv)
    paths = build_v1_7_perturbation_spectrum(args.out, spectrum_summary_csv=args.spectrum_summary_csv)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
