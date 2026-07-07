from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.7-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "anti_tautology_role_dependence_check_locked_not_closeout"
GATE_KIND = "post_holdout_anti_tautology_role_dependence_check_not_closeout"
NEXT_GATE = "v1.7.8-alpha — Reviewer Start Here / Reproduction Package"

REQUIRED_RUNGS = ["triad27", "deep81", "wide243"]
REQUIRED_LANES = [
    "earned_one",
    "raw_expression_pressure",
    "latent_overcrown",
    "relation_debt",
    "return_debt",
    "false_one_pressure",
    "final_false_one_crowns",
]

OUTPUT_FILES = {
    "read": "v1_7_anti_tautology_role_dependence_check_read.md",
    "decision": "v1_7_anti_tautology_role_dependence_check_decision.json",
    "routine": "v1_7_anti_tautology_known_routine.csv",
    "conditions": "v1_7_anti_tautology_audit_conditions.csv",
    "role_dependence": "v1_7_role_dependence_post_holdout_checks.csv",
    "input_schema": "v1_7_anti_tautology_role_dependence_input_schema.csv",
    "evaluation": "v1_7_anti_tautology_role_dependence_evaluation.csv",
    "audit": "v1_7_anti_tautology_role_dependence_audit.json",
    "bundle": "v1_7_anti_tautology_role_dependence_check_bundle.zip",
}

KNOWN_ROUTINE_ROWS = [
    {
        "routine_step": "pre_registration_trace",
        "known_pattern": "pre-register expected outputs before scoring or interpreting results",
        "what_it_checks": "expected_manifest_frozen must be true; post-hoc lane sculpting is not allowed",
        "failure_signal": "expected manifest is absent, late, or rewritten after output inspection",
        "why_it_is_respected": "standard empirical discipline: hypotheses and acceptance criteria are fixed before reading the result",
    },
    {
        "routine_step": "holdout_split_trace",
        "known_pattern": "separate reference/tuning cases from fresh or held-out evaluation cases",
        "what_it_checks": "fresh seed block, held-out profile variant, reference_profile_reused=false, and all three weather rungs present",
        "failure_signal": "the known reference profile is rerun and called validation",
        "why_it_is_respected": "holdout evaluation is a basic guard against fitting to the training/reference surface",
    },
    {
        "routine_step": "negative_control_false_crown_stop",
        "known_pattern": "negative controls must remain negative; any positive hit is a stop condition",
        "what_it_checks": "final_false_one_crowns remains zero while false_one_pressure remains visible",
        "failure_signal": "false-one pressure receives final +1 or the false-crown count is averaged away",
        "why_it_is_respected": "negative controls expose whether the method can refuse success, not only produce success",
    },
    {
        "routine_step": "positive_control_dead_safe_guard",
        "known_pattern": "positive controls must remain detectable so a no-error result is not just dead-safe refusal",
        "what_it_checks": "final_earned_one_events > 0 and earned_controls_present=true",
        "failure_signal": "zero false crowns are achieved by crowning nothing",
        "why_it_is_respected": "a classifier that never predicts positive can look safe while learning nothing",
    },
    {
        "routine_step": "label_leakage_and_role_dependence_check",
        "known_pattern": "mask labels/proxies that could directly carry the answer before evaluating lane assignment",
        "what_it_checks": "candidate_names_masked=true, optional role_labels_masked=true, optional role_leakage_score below threshold, and label_only_lane_assignment=false",
        "failure_signal": "lane assignment is just role/name recounting",
        "why_it_is_respected": "leakage checks are a standard sanity test when labels or group IDs could encode the target",
    },
    {
        "routine_step": "ablation_and_alternative_explanation_pressure",
        "known_pattern": "compare against simpler explanations and require the mechanism to explain what they cannot",
        "what_it_checks": "result is not reducible to raw-only, binary, dead-safe, average-gate, no-return, or no-zero-hold witness logic",
        "failure_signal": "a cheap baseline explains the result equally well",
        "why_it_is_respected": "baseline and ablation pressure prevent a mechanism claim from being true by vocabulary alone",
    },
    {
        "routine_step": "mechanism_self_explanation",
        "known_pattern": "the audit must describe what it checks and why each check matters",
        "what_it_checks": "the generated readme includes decision grammar, pass/fail logic, role-dependence boundaries, and next gate",
        "failure_signal": "the audit emits numbers without explaining the mechanism boundary",
        "why_it_is_respected": "reviewers need a trace from data columns to decision, not an oracle verdict",
    },
]

AUDIT_CONDITION_ROWS = [
    {
        "condition": "all_weather_rungs_present",
        "pass_rule": "triad27, deep81, and wide243 rows are present before reviewer packaging",
        "resist_if": "any required rung is missing for the full post-holdout audit",
        "claim_boundary": "controlled synthetic-field all-weather holdout, not external validation",
    },
    {
        "condition": "not_vacuous_no_false_crowns",
        "pass_rule": "false_one_pressure > 0 and final_false_one_crowns = 0",
        "resist_if": "false-one pressure is absent everywhere or any false crown appears",
        "claim_boundary": "the witness must face pressure and refuse the crown",
    },
    {
        "condition": "not_dead_safe",
        "pass_rule": "final_earned_one_events > 0 with earned_controls_present=true",
        "resist_if": "no earned-one events appear or earned controls are absent",
        "claim_boundary": "safety by refusing all +1 is not witness intelligence",
    },
    {
        "condition": "structured_zero_not_generic_failure",
        "pass_rule": "relation_debt > 0 and return_debt > 0 are visible as structured zero lanes",
        "resist_if": "debt lanes collapse into generic failure or disappear",
        "claim_boundary": "zero-state must do work, not act as a junk drawer",
    },
    {
        "condition": "latent_overcrown_reproduced_or_bounded",
        "pass_rule": "latent_overcrown is visible or explicitly kept as HOLD in the decision",
        "resist_if": "latent overcrown is silently crowned or erased",
        "claim_boundary": "fragile lanes may hold; they may not fake stability",
    },
    {
        "condition": "manifest_before_result",
        "pass_rule": "expected_manifest_frozen=true for every evaluated row",
        "resist_if": "expected manifest is post-hoc or absent",
        "claim_boundary": "no victory sculpture after seeing outputs",
    },
    {
        "condition": "candidate_name_masking",
        "pass_rule": "candidate_names_masked=true for every evaluated row",
        "resist_if": "candidate names or names shaped like roles carry the lane assignment",
        "claim_boundary": "masking is a leakage guard, not role-blind discovery",
    },
    {
        "condition": "reference_profile_not_reused",
        "pass_rule": "reference_profile_reused=false for every evaluated row",
        "resist_if": "reference profile is reused and called holdout",
        "claim_boundary": "fresh controlled holdout, not independent generator proof",
    },
]

ROLE_DEPENDENCE_CHECK_ROWS = [
    {
        "check": "designed_profile_boundary",
        "meaning": "designed adversarial families may shape the harness; the audit must say so explicitly",
        "pass_signal": "decision keeps designed-profile language bounded",
        "failure_signal": "controlled designed-profile result becomes role-blind discovery language",
    },
    {
        "check": "label_leakage_pressure",
        "meaning": "direct candidate names, role labels, or obvious proxies must not carry lane assignment",
        "pass_signal": "candidate_names_masked=true and optional role leakage score <= 0.25",
        "failure_signal": "role labels or candidate names determine the lane",
    },
    {
        "check": "witness_count_dependence",
        "meaning": "the audit must be grounded in final witness counts, debt lanes, and false-crown stops",
        "pass_signal": "counts show earned-one, raw pressure, relation/return debt, false pressure, and zero false crowns",
        "failure_signal": "the audit relies on prose labels instead of numeric lane evidence",
    },
    {
        "check": "tautology_pressure",
        "meaning": "the result must not be true because the definition already bakes in success",
        "pass_signal": "negative and positive controls are both active, and simpler witnesses remain named as alternative explanations",
        "failure_signal": "success follows by definition even if no pressure exists",
    },
    {
        "check": "bounded_claim_translation",
        "meaning": "the final wording must match the evidence domain exactly",
        "pass_signal": "controlled synthetic-field claim only",
        "failure_signal": "role-blind, unknown-field, physics, cosmology, or observed-universe language appears",
    },
]

INPUT_SCHEMA_ROWS = [
    {
        "column": "weather_rung",
        "required": "yes",
        "meaning": "weather rung under audit: triad27, deep81, or wide243",
        "example": "triad27",
    },
    {
        "column": "fresh_seed_block",
        "required": "yes",
        "meaning": "seed block used for the fresh holdout run",
        "example": "18-26",
    },
    {
        "column": "candidate_names_masked",
        "required": "yes",
        "meaning": "boolean: candidate names were masked before reviewer-facing lane interpretation",
        "example": "true",
    },
    {
        "column": "expected_manifest_frozen",
        "required": "yes",
        "meaning": "boolean: lane expectations were frozen before result interpretation",
        "example": "true",
    },
    {
        "column": "reference_profile_reused",
        "required": "yes",
        "meaning": "boolean: whether the reference profile was reused and mislabeled as holdout",
        "example": "false",
    },
    {
        "column": "earned_controls_present",
        "required": "yes",
        "meaning": "boolean: earned-one controls were present so the witness cannot pass by refusing all crowns",
        "example": "true",
    },
    {
        "column": "lane_pattern_matches_expected",
        "required": "yes",
        "meaning": "boolean: rung-level lane pattern matched the pre-frozen expected pattern",
        "example": "true",
    },
    {
        "column": "final_earned_one_events",
        "required": "yes",
        "meaning": "positive-control count; must be > 0 for a non-dead-safe pass",
        "example": "839",
    },
    {
        "column": "raw_expression_pressure",
        "required": "yes",
        "meaning": "raw pressure count before final witness; must be visible so the witness is not hiding pressure",
        "example": "1283",
    },
    {
        "column": "latent_overcrown",
        "required": "yes",
        "meaning": "latent-overcrown count; may remain bounded but must not be silently crowned or erased",
        "example": "9",
    },
    {
        "column": "relation_debt",
        "required": "yes",
        "meaning": "structured-zero relation-debt count",
        "example": "39",
    },
    {
        "column": "return_debt",
        "required": "yes",
        "meaning": "structured-zero return-debt count",
        "example": "75",
    },
    {
        "column": "false_one_pressure",
        "required": "yes",
        "meaning": "negative-control pressure count; must be > 0 so zero false crowns are not vacuous",
        "example": "321",
    },
    {
        "column": "final_false_one_crowns",
        "required": "yes",
        "meaning": "hard stop count; must be zero",
        "example": "0",
    },
    {
        "column": "role_labels_masked",
        "required": "optional",
        "meaning": "stronger leakage flag if a role-label audit is available; true/false",
        "example": "true",
    },
    {
        "column": "role_leakage_score",
        "required": "optional",
        "meaning": "0..1 role/proxy leakage pressure if measured; > 0.25 becomes HOLD",
        "example": "0.03",
    },
    {
        "column": "label_only_lane_assignment",
        "required": "optional",
        "meaning": "boolean: lane assignment requires labels rather than witness metrics; true becomes RESIST",
        "example": "false",
    },
]


def _to_int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _to_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "masked", "pass"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_many_csv(paths: Iterable[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.extend(_read_csv(path))
    return rows


def classify_audit_row(row: dict[str, object]) -> str:
    if _to_int(row.get("final_false_one_crowns")) > 0:
        return "resist_false_crown_stop"
    if not _to_bool(row.get("candidate_names_masked")):
        return "resist_candidate_name_leakage"
    if not _to_bool(row.get("expected_manifest_frozen")):
        return "resist_post_hoc_manifest"
    if _to_bool(row.get("reference_profile_reused")):
        return "resist_reference_profile_reused"
    if not _to_bool(row.get("earned_controls_present"), default=True):
        return "resist_dead_safe_missing_earned_controls"
    if _to_int(row.get("final_earned_one_events")) <= 0:
        return "resist_dead_safe_no_earned_one"
    if _to_int(row.get("false_one_pressure")) <= 0:
        return "hold_vacuous_no_false_pressure"
    if _to_bool(row.get("label_only_lane_assignment")):
        return "resist_label_only_lane_assignment"
    if row.get("role_labels_masked", "") not in {"", None} and not _to_bool(row.get("role_labels_masked")):
        return "hold_role_labels_unmasked"
    if _to_float(row.get("role_leakage_score")) > 0.25:
        return "hold_role_leakage_pressure"
    if not _to_bool(row.get("lane_pattern_matches_expected")):
        return "hold_lane_pattern_mismatch"
    if _to_int(row.get("relation_debt")) <= 0 or _to_int(row.get("return_debt")) <= 0:
        return "hold_structured_zero_debt_not_visible"
    if _to_int(row.get("raw_expression_pressure")) <= 0:
        return "hold_raw_pressure_not_visible"
    if _to_int(row.get("latent_overcrown")) <= 0:
        return "witness_core_lanes_visible_latent_hold"
    return "witness_post_holdout_audit_row_passed"


def evaluate_audit_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    evaluation: list[dict[str, object]] = []
    for row in rows:
        evaluation.append(
            {
                "weather_rung": row.get("weather_rung", ""),
                "row_status": classify_audit_row(row),
                "fresh_seed_block": row.get("fresh_seed_block", ""),
                "candidate_names_masked": _to_bool(row.get("candidate_names_masked")),
                "expected_manifest_frozen": _to_bool(row.get("expected_manifest_frozen")),
                "reference_profile_reused": _to_bool(row.get("reference_profile_reused")),
                "earned_controls_present": _to_bool(row.get("earned_controls_present"), default=True),
                "lane_pattern_matches_expected": _to_bool(row.get("lane_pattern_matches_expected")),
                "final_earned_one_events": _to_int(row.get("final_earned_one_events")),
                "raw_expression_pressure": _to_int(row.get("raw_expression_pressure")),
                "latent_overcrown": _to_int(row.get("latent_overcrown")),
                "relation_debt": _to_int(row.get("relation_debt")),
                "return_debt": _to_int(row.get("return_debt")),
                "false_one_pressure": _to_int(row.get("false_one_pressure")),
                "final_false_one_crowns": _to_int(row.get("final_false_one_crowns")),
                "role_labels_masked": _to_bool(row.get("role_labels_masked"), default=True) if row.get("role_labels_masked", "") not in {"", None} else "not_supplied",
                "role_leakage_score": _to_float(row.get("role_leakage_score")),
                "label_only_lane_assignment": _to_bool(row.get("label_only_lane_assignment")),
            }
        )
    return evaluation


def collapse_audit_decision(evaluation_rows: Iterable[dict[str, object]]) -> str:
    rows = list(evaluation_rows)
    if not rows:
        return "anti_tautology_role_dependence_check_locked_evaluation_not_run"
    statuses = {str(row.get("row_status", "")) for row in rows}
    rungs = {str(row.get("weather_rung", "")) for row in rows}
    missing_rungs = [rung for rung in REQUIRED_RUNGS if rung not in rungs]

    if any(status.startswith("resist_") for status in statuses):
        if "resist_false_crown_stop" in statuses:
            return "resist_audit_false_crown_stop"
        if "resist_post_hoc_manifest" in statuses:
            return "resist_audit_post_hoc_manifest"
        if "resist_candidate_name_leakage" in statuses or "resist_label_only_lane_assignment" in statuses:
            return "resist_audit_label_or_name_leakage"
        if "resist_dead_safe_no_earned_one" in statuses or "resist_dead_safe_missing_earned_controls" in statuses:
            return "resist_audit_dead_safe_or_missing_positive_control"
        if "resist_reference_profile_reused" in statuses:
            return "resist_audit_reference_profile_reused"
        return "resist_audit_failed_stop_condition"
    if missing_rungs:
        return "hold_audit_weather_ladder_incomplete"
    if statuses & {
        "hold_vacuous_no_false_pressure",
        "hold_role_labels_unmasked",
        "hold_role_leakage_pressure",
        "hold_lane_pattern_mismatch",
        "hold_structured_zero_debt_not_visible",
        "hold_raw_pressure_not_visible",
    }:
        return "hold_audit_role_dependence_or_tautology_pressure"
    if all(_to_int(row.get("final_false_one_crowns")) == 0 for row in rows) and all(
        _to_int(row.get("false_one_pressure")) > 0 for row in rows
    ):
        if any(str(row.get("row_status")) == "witness_core_lanes_visible_latent_hold" for row in rows):
            return "witness_audit_passed_with_latent_hold_no_role_blind_claim"
        return "expand_audit_passed_not_tautological_role_bounded"
    return "hold_audit_partial_or_unpressured"


def _summarize(evaluation_rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "weather_rungs_present": sorted({str(row.get("weather_rung", "")) for row in evaluation_rows if row.get("weather_rung", "")}),
        "total_final_earned_one_events": sum(_to_int(row.get("final_earned_one_events")) for row in evaluation_rows),
        "total_raw_expression_pressure": sum(_to_int(row.get("raw_expression_pressure")) for row in evaluation_rows),
        "total_latent_overcrown": sum(_to_int(row.get("latent_overcrown")) for row in evaluation_rows),
        "total_relation_debt": sum(_to_int(row.get("relation_debt")) for row in evaluation_rows),
        "total_return_debt": sum(_to_int(row.get("return_debt")) for row in evaluation_rows),
        "total_false_one_pressure": sum(_to_int(row.get("false_one_pressure")) for row in evaluation_rows),
        "total_final_false_one_crowns": sum(_to_int(row.get("final_false_one_crowns")) for row in evaluation_rows),
    }


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines(evaluation_rows: list[dict[str, object]], evaluation_decision: str) -> list[str]:
    summary = _summarize(evaluation_rows)
    lines = [
        "# v1.7 Anti-Tautology Audit / Role-Dependence Check",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "`v1.7.7-alpha` does not close the core question. It audits the fresh holdout ladder before reviewer packaging so the result cannot pass by tautology, label leakage, dead-safe refusal, or role-name recounting.",
        "",
        "## How the audit works",
        "",
        "The check follows a familiar empirical routine: pre-register expected outputs, evaluate held-out runs, keep positive and negative controls active, mask role/name leakage, compare against simpler explanations, and translate the result inside its evidence boundary.",
        "",
        "In ZeroGateSim terms, this means:",
        "",
        "```text",
        "fresh holdout rows -> rung completeness -> manifest-before-result check -> masking/leakage check -> positive-control check -> negative-control false-crown stop -> structured-zero/debt visibility -> bounded decision",
        "```",
        "",
        "Passing this audit is not role-blind discovery. It is a bounded witness that the post-holdout result is not merely tautological, vacuous, dead-safe, or role-label bookkeeping.",
        "",
        "## Evaluation decision",
        "",
        f"`{evaluation_decision}`",
        "",
    ]
    if evaluation_rows:
        lines.extend(
            [
                "## Aggregate",
                "",
                f"- Weather rungs present: `{', '.join(summary['weather_rungs_present'])}`",
                f"- Final earned-one events: `{summary['total_final_earned_one_events']}`",
                f"- Raw expression pressure: `{summary['total_raw_expression_pressure']}`",
                f"- Latent overcrown: `{summary['total_latent_overcrown']}`",
                f"- Relation debt: `{summary['total_relation_debt']}`",
                f"- Return debt: `{summary['total_return_debt']}`",
                f"- False-one pressure: `{summary['total_false_one_pressure']}`",
                f"- Final false-one crowns: `{summary['total_final_false_one_crowns']}`",
                "",
                "## Row decisions",
                "",
                "| rung | status | earned | raw pressure | latent | relation debt | return debt | false pressure | false crowns |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|",
                *[
                    f"| `{row['weather_rung']}` | `{row['row_status']}` | {row['final_earned_one_events']} | {row['raw_expression_pressure']} | {row['latent_overcrown']} | {row['relation_debt']} | {row['return_debt']} | {row['false_one_pressure']} | {row['final_false_one_crowns']} |"
                    for row in evaluation_rows
                ],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No holdout summary CSV was supplied. This gate locks the audit routine and decision grammar before reviewer packaging.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This is controlled synthetic-field audit plumbing. It adds no physics claim, no role-blind discovery claim, no manuscript v2, and no native math mutation.",
            "",
            "## Next gate",
            "",
            f"`{NEXT_GATE}` packages the reviewer-facing reproduction path only after this audit is readable and bounded.",
        ]
    )
    return lines


def build_v1_7_anti_tautology_role_dependence_check(
    output_dir: Path,
    *,
    holdout_summary_csvs: Iterable[Path] | None = None,
) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    csv_paths = [Path(path) for path in holdout_summary_csvs or []]
    raw_rows = read_many_csv(csv_paths) if csv_paths else []
    evaluation_rows = evaluate_audit_rows(raw_rows)
    evaluation_decision = collapse_audit_decision(evaluation_rows)
    summary = _summarize(evaluation_rows)

    _write_markdown(paths["read"], _readme_lines(evaluation_rows, evaluation_decision))
    write_dict_rows_csv(paths["routine"], KNOWN_ROUTINE_ROWS)
    write_dict_rows_csv(paths["conditions"], AUDIT_CONDITION_ROWS)
    write_dict_rows_csv(paths["role_dependence"], ROLE_DEPENDENCE_CHECK_ROWS)
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
        "role_blind_discovery_claimed": False,
        "core_question_closed": False,
        "holdout_summary_csvs": [str(path) for path in csv_paths],
        "evaluation_rows": len(evaluation_rows),
        "required_weather_rungs": REQUIRED_RUNGS,
        "required_lanes": REQUIRED_LANES,
        "summary": summary,
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "v1.7.7 tests whether the post-holdout result is non-vacuous, non-tautological, and not carried by role/name leakage.",
        "integration_modularity": "This gate sits between fresh holdout evidence and reviewer/reproduction packaging; it does not close the core question.",
        "witness_translation": "Passing means the controlled synthetic-field holdout result is audit-ready, not role-blind discovery or external validation.",
        "known_routine": [row["routine_step"] for row in KNOWN_ROUTINE_ROWS],
        "trace": "holdout rows -> pre-registration -> holdout split -> positive/negative controls -> masking/leakage -> structured-zero lanes -> bounded decision.",
        "overdo_risk": "Treating post-holdout audit readiness as the final v1.7 answer before reviewer package and closeout.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_anti_tautology_role_dependence_check_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 anti-tautology / role-dependence check package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_anti_tautology_role_dependence_check"))
    parser.add_argument(
        "--holdout-summary-csv",
        type=Path,
        action="append",
        default=None,
        help="Optional holdout summary CSV. May be supplied multiple times for triad27/deep81/wide243 rows.",
    )
    args = parser.parse_args(argv)
    paths = build_v1_7_anti_tautology_role_dependence_check(
        args.out,
        holdout_summary_csvs=args.holdout_summary_csv,
    )
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
