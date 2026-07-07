from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.6-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "fresh_holdout_challenge_locked_not_closeout"
GATE_KIND = "fresh_holdout_synthetic_field_challenge_not_closeout"
NEXT_GATE = "v1.7.7-alpha — Anti-Tautology Audit / Role-Dependence Check"
RUN_ORDER_ANSWER = (
    "v1.7.6 locks the fresh-holdout design and evaluation schema. After v1.7.6 is CI green, "
    "run triad27 first, inspect its report/evaluator/handoff, then run deep81, then wide243. "
    "Only after all three rungs are safe should v1.7.7 package the reviewer path."
)

REQUIRED_WEATHER_RUNGS = ["triad27", "deep81", "wide243"]

OUTPUT_FILES = {
    "read": "v1_7_fresh_holdout_challenge_read.md",
    "decision": "v1_7_fresh_holdout_challenge_decision.json",
    "holdout_design": "v1_7_holdout_design.csv",
    "expected_outputs": "v1_7_holdout_expected_outputs.csv",
    "weather_ladder": "v1_7_holdout_weather_ladder.csv",
    "run_order": "v1_7_holdout_run_order.csv",
    "candidate_masking": "v1_7_candidate_name_masking.csv",
    "input_schema": "v1_7_holdout_input_schema.csv",
    "output_structure": "v1_7_holdout_output_structure.csv",
    "evaluation": "v1_7_holdout_evaluation.csv",
    "audit": "v1_7_holdout_audit.json",
    "bundle": "v1_7_fresh_holdout_challenge_bundle.zip",
}

HOLDOUT_DESIGN_ROWS = [
    {
        "design_rule": "fresh_seed_block",
        "meaning": "use seeds not used by the reference profile summaries under review",
        "pass_signal": "fresh_seed_block is named and separated from the reference seed block",
        "failure_signal": "reference seeds are reused and called fresh",
        "claim_boundary": "fresh holdout inside controlled synthetic fields, not unknown-field discovery",
    },
    {
        "design_rule": "held_out_profile_variant",
        "meaning": "run controlled profile variants that were not used to tune the reference report language",
        "pass_signal": "heldout_profile_variant is explicit and reference_profile_reused is false",
        "failure_signal": "the known reference profile is rerun and called holdout",
        "claim_boundary": "held-out controlled variant, not independent generator family yet",
    },
    {
        "design_rule": "candidate_name_masking",
        "meaning": "hide candidate names before lane interpretation so names cannot carry the answer",
        "pass_signal": "candidate_names_masked is true in every evaluated row",
        "failure_signal": "lane interpretation depends on candidate names or obvious role-like names",
        "claim_boundary": "candidate masking is weaker than role-blind discovery but stronger than public-name recounting",
    },
    {
        "design_rule": "expected_manifest_first",
        "meaning": "write lane-level expected outputs before the holdout summary is evaluated",
        "pass_signal": "expected_manifest_frozen is true before the run summary is read",
        "failure_signal": "the expected lane pattern is written after looking at outputs",
        "claim_boundary": "predeclared witness expectations, not post-hoc victory sculpture",
    },
    {
        "design_rule": "weather_ladder_complete",
        "meaning": "full holdout pressure requires triad27, deep81, and wide243 summaries",
        "pass_signal": "all three weather rungs are present before reviewer packaging or closeout pressure",
        "failure_signal": "only the friendly rung is run",
        "claim_boundary": "all-weather controlled holdout; still not external empirical validation",
    },
    {
        "design_rule": "false_crown_stop",
        "meaning": "any final false-one crown blocks later +1 closeout language",
        "pass_signal": "final_false_one_crowns remains zero in every holdout row",
        "failure_signal": "a false crown appears or is averaged away",
        "claim_boundary": "safe failure remains the controlling obligation",
    },
    {
        "design_rule": "latent_overcrown_reproduce_or_hold",
        "meaning": "latent overcrown is fragile; it must reproduce or remain explicit HOLD before v1.7 closeout",
        "pass_signal": "latent overcrown is either visible in fresh holdout or marked as latent HOLD for v1.7.10 narrowing",
        "failure_signal": "latent overcrown silently becomes stable evidence without reproducing",
        "claim_boundary": "do not fake the fragile lane",
    },
]

EXPECTED_OUTPUT_ROWS = [
    {
        "lane": "earned_one",
        "required_for_full_question": "yes",
        "expected_holdout_behavior": "real earned controls still receive final +1 under fresh seeds and held-out profile variants",
        "pass_signal": "final_earned_one_events > 0 when earned controls are present",
        "failure_signal": "dead-safe witness refuses real earned-one",
        "safe_decision": "+1 only when return-depth, lineage, and independence are paid",
    },
    {
        "lane": "raw_expression_pressure",
        "required_for_full_question": "yes",
        "expected_holdout_behavior": "raw pressure remains visible before the final witness decides",
        "pass_signal": "raw_expression_pressure > 0 under adversarial holdout pressure",
        "failure_signal": "raw pressure is hidden or equated with final truth",
        "safe_decision": "pressure only, never final truth by itself",
    },
    {
        "lane": "latent_overcrown",
        "required_for_full_question": "conditional",
        "expected_holdout_behavior": "fresh holdout either reproduces latent overcrown or explicitly keeps it in HOLD for v1.7.10 narrowing",
        "pass_signal": "latent_overcrown > 0 or decision names latent hold",
        "failure_signal": "latent overcrown remains unreproduced but stays in a +1 closeout sentence",
        "safe_decision": "0 latent-overcrown hold unless reproduced",
    },
    {
        "lane": "relation_debt",
        "required_for_full_question": "yes",
        "expected_holdout_behavior": "borrowed, unstable, or under-owned relation becomes structured zero",
        "pass_signal": "relation_debt > 0 when relation pressure appears",
        "failure_signal": "relation debt collapses into generic failure or gets crowned",
        "safe_decision": "0 relation-debt hold",
    },
    {
        "lane": "return_debt",
        "required_for_full_question": "yes",
        "expected_holdout_behavior": "Gamma without observed return, memory, or depth becomes structured zero",
        "pass_signal": "return_debt > 0 when return-potential / observed-return gap appears",
        "failure_signal": "zero crossing or high D/P/R is treated as observed return",
        "safe_decision": "0 return-debt hold",
    },
    {
        "lane": "false_one_pressure",
        "required_for_full_question": "yes",
        "expected_holdout_behavior": "trap-shaped or false-one pressure remains visible and demoted before crown",
        "pass_signal": "false_one_pressure > 0 and final_false_one_crowns = 0",
        "failure_signal": "false-one pressure receives final +1 or disappears from reports",
        "safe_decision": "-1 demotion or 0 quarantine before crown",
    },
    {
        "lane": "final_false_one_crowns",
        "required_for_full_question": "stop_condition",
        "expected_holdout_behavior": "must remain zero across all holdout rungs",
        "pass_signal": "final_false_one_crowns = 0 in every row",
        "failure_signal": "any final false-one crown appears",
        "safe_decision": "RESIST and block closeout",
    },
]

WEATHER_LADDER_ROWS = [
    {
        "weather_rung": "triad27",
        "cells": 27,
        "purpose": "local expression weather / first fresh holdout smoke",
        "run_timing": "after v1.7.6 CI green and before v1.7.7 packaging",
        "success_signal": "local lane pattern visible without false crowns",
    },
    {
        "weather_rung": "deep81",
        "cells": 81,
        "purpose": "perturbation and late-shock bridge",
        "run_timing": "after triad27 holdout is safe and before v1.7.7 packaging",
        "success_signal": "perturbation pressure degrades safely, not into false crown",
    },
    {
        "weather_rung": "wide243",
        "cells": 243,
        "purpose": "temporal-depth / time-axis stress",
        "run_timing": "after deep81 holdout is safe and before v1.7.7 packaging",
        "success_signal": "full ladder summary ready for audit, cleanup, reviewer packaging, and v1.7.10 closeout pressure",
    },
]

RUN_ORDER_ROWS = [
    {
        "step": 1,
        "when": "v1.7.6-alpha merged and CI green",
        "action": "run triad27 fresh holdout summary only",
        "why": "small local expression weather catches output plumbing, false-crown, and dead-safe failures first",
        "next_allowed": "inspect triad27 report/evaluator/handoff before deep81; repair or HOLD if red",
    },
    {
        "step": 2,
        "when": "triad27 report/evaluator/handoff are valid",
        "action": "run deep81 fresh holdout summary only",
        "why": "perturbation / late-shock bridge tests whether lane pattern degrades safely after the smallest rung is proven",
        "next_allowed": "inspect deep81 report/evaluator/handoff before wide243; repair or HOLD if red",
    },
    {
        "step": 3,
        "when": "deep81 report/evaluator/handoff are valid",
        "action": "run wide243 fresh holdout summary only",
        "why": "temporal-depth stress is required before full v1.7 closeout can be trusted",
        "next_allowed": "v1.7.7 anti-tautology audit if safe; v1.7.8 cleanup and v1.7.9 reviewer package before any v1.7.10 +1",
    },
    {
        "step": 4,
        "when": "triad27 / deep81 / wide243 summaries and handoffs exist",
        "action": "audit anti-tautology / role-dependence in v1.7.7-alpha",
        "why": "anti-tautology audit should inspect actual holdout summaries before cleanup and reviewer packaging",
        "next_allowed": "v1.7.8 cleanup after audit; v1.7.9 reviewer path after cleanup; v1.7.10 closeout only later",
    },
]

RUN_ORDER_FORBIDDEN = [
    "do not use an all-weather one-shot runner before triad27 proves the report/evaluator/handoff pipeline",
    "do not print a COMPLETE banner after any failed required include or report gate",
    "do not call local run artifacts repo truth unless a later patch deliberately promotes them",
]

OUTPUT_STRUCTURE_ROWS = [
    {
        "output_layer": "full_output_report",
        "required_payload": "complete system report / decision JSON / CSV evidence needed for deep assistant review",
        "handoff_role": "--full-output-report",
        "future_human_display_use": "source for expandable technical trace, tables, and audit cards",
        "repo_truth_boundary": "local run evidence only unless deliberately promoted by a later patch",
    },
    {
        "output_layer": "compressed_summary",
        "required_payload": "short reader state: rung status, lane counts, false-crown status, boundary, next action",
        "handoff_role": "--compressed-summary",
        "future_human_display_use": "top card / dashboard / reviewer quick read",
        "repo_truth_boundary": "summary must point to full output report, not replace it",
    },
    {
        "output_layer": "visual_outputs",
        "required_payload": "SVG/PNG/HTML/cards or plots that make the lane structure legible",
        "handoff_role": "--visual-output",
        "future_human_display_use": "human-friendly display layer after the evidence pipeline is stable",
        "repo_truth_boundary": "visuals orient; they do not upgrade the claim",
    },
    {
        "output_layer": "historical_report_label_note",
        "required_payload": "included debt-evidence report modules may retain historical internal report-version labels",
        "handoff_role": "--report-label-note",
        "future_human_display_use": "prevents reviewer confusion when v1.6 report modules are wrapped by v1.7.6 evaluation",
        "repo_truth_boundary": "active package/evaluator boundary decides the current gate",
    },
]

CANDIDATE_MASKING_ROWS = [
    {
        "masking_rule": "mask_candidate_names",
        "meaning": "candidate display names are replaced with neutral ids before lane interpretation",
        "pass_signal": "candidate_names_masked is true",
        "failure_signal": "semantic candidate names carry the expected answer",
    },
    {
        "masking_rule": "mask_role_language",
        "meaning": "role-like language is absent from holdout summary columns used for lane evaluation",
        "pass_signal": "role labels are unavailable to the reviewer path",
        "failure_signal": "expresser / trap / latent names or proxies become the classifier",
    },
    {
        "masking_rule": "preserve_numeric_witness",
        "meaning": "masking must not remove D/P/R/B, return-depth, lineage, independence, or lane counters",
        "pass_signal": "lane counters remain computable after masking",
        "failure_signal": "masking hides the evidence rather than removing label leakage",
    },
]

INPUT_SCHEMA_ROWS = [
    {"column": "holdout_run_id", "required": "yes", "meaning": "unique holdout run or summary id", "example": "fresh_holdout_A_triad27"},
    {"column": "weather_rung", "required": "yes", "meaning": "triad27, deep81, or wide243", "example": "triad27"},
    {"column": "fresh_seed_block", "required": "yes", "meaning": "seed block not used for reference tuning", "example": "18-26"},
    {"column": "heldout_profile_variant", "required": "yes", "meaning": "controlled variant held out from reference profile design", "example": "closure_gap_variant_B"},
    {"column": "candidate_names_masked", "required": "yes", "meaning": "boolean: candidate names were masked before lane interpretation", "example": "true"},
    {"column": "expected_manifest_frozen", "required": "yes", "meaning": "boolean: lane-level expected outputs were written before reading results", "example": "true"},
    {"column": "reference_profile_reused", "required": "yes", "meaning": "boolean: known reference profile reused instead of held-out profile", "example": "false"},
    {"column": "earned_controls_present", "required": "yes", "meaning": "boolean: earned controls were present and expected to remain crownable", "example": "true"},
    {"column": "lane_pattern_matches_expected", "required": "yes", "meaning": "boolean: observed lane pattern matches predeclared expectation", "example": "true"},
    {"column": "final_earned_one_events", "required": "yes", "meaning": "final +1 count for earned controls", "example": "128"},
    {"column": "raw_expression_pressure", "required": "yes", "meaning": "raw pressure count before final witness", "example": "188"},
    {"column": "latent_overcrown", "required": "no", "meaning": "latent overcrown pressure if reproduced; may remain zero/HOLD", "example": "4"},
    {"column": "relation_debt", "required": "yes", "meaning": "structured-zero relation debt count", "example": "17"},
    {"column": "return_debt", "required": "yes", "meaning": "structured-zero return debt count", "example": "9"},
    {"column": "false_one_pressure", "required": "yes", "meaning": "false-one pressure count before final crown", "example": "31"},
    {"column": "final_false_one_crowns", "required": "yes", "meaning": "stop-condition count; must be zero", "example": "0"},
]


def _to_int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "masked", "frozen", "safe"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _weather_rung(value: object) -> str:
    return str(value or "").strip().lower()


def _lane_flags(row: dict[str, object]) -> dict[str, bool]:
    return {
        "earned_one_visible": _to_int(row.get("final_earned_one_events")) > 0,
        "raw_pressure_visible": _to_int(row.get("raw_expression_pressure")) > 0,
        "latent_overcrown_visible": _to_int(row.get("latent_overcrown")) > 0,
        "relation_debt_visible": _to_int(row.get("relation_debt")) > 0,
        "return_debt_visible": _to_int(row.get("return_debt")) > 0,
        "false_one_pressure_visible": _to_int(row.get("false_one_pressure")) > 0,
        "zero_false_crowns": _to_int(row.get("final_false_one_crowns")) == 0,
    }


def classify_holdout_row(row: dict[str, object]) -> str:
    if _to_int(row.get("final_false_one_crowns")) > 0:
        return "resist_false_crown_stop"
    rung = _weather_rung(row.get("weather_rung"))
    if rung not in REQUIRED_WEATHER_RUNGS:
        return "hold_unknown_weather_rung"
    if not _to_bool(row.get("expected_manifest_frozen")):
        return "hold_expected_manifest_not_frozen"
    if not _to_bool(row.get("candidate_names_masked")):
        return "hold_candidate_names_unmasked"
    if _to_bool(row.get("reference_profile_reused")):
        return "hold_reference_profile_reused"
    if not _to_bool(row.get("lane_pattern_matches_expected")):
        return "hold_lane_pattern_mismatch"
    flags = _lane_flags(row)
    if _to_bool(row.get("earned_controls_present")) and not flags["earned_one_visible"]:
        return "resist_dead_safe_earned_lost"
    if (
        flags["earned_one_visible"]
        and flags["raw_pressure_visible"]
        and flags["relation_debt_visible"]
        and flags["return_debt_visible"]
        and flags["false_one_pressure_visible"]
        and flags["zero_false_crowns"]
    ):
        if flags["latent_overcrown_visible"]:
            return "witness_holdout_core_lanes_visible_with_latent"
        return "witness_holdout_core_lanes_visible_latent_hold"
    if flags["false_one_pressure_visible"] and flags["zero_false_crowns"]:
        return "witness_holdout_partial_safe_failure"
    if flags["relation_debt_visible"] or flags["return_debt_visible"]:
        return "witness_holdout_structured_zero_partial"
    return "hold_holdout_partial_or_unpressured"


def evaluate_holdout_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    evaluation: list[dict[str, object]] = []
    for row in rows:
        flags = _lane_flags(row)
        evaluation.append(
            {
                "holdout_run_id": row.get("holdout_run_id", ""),
                "weather_rung": _weather_rung(row.get("weather_rung")),
                "row_status": classify_holdout_row(row),
                "fresh_seed_block": row.get("fresh_seed_block", ""),
                "heldout_profile_variant": row.get("heldout_profile_variant", ""),
                "candidate_names_masked": _to_bool(row.get("candidate_names_masked")),
                "expected_manifest_frozen": _to_bool(row.get("expected_manifest_frozen")),
                "reference_profile_reused": _to_bool(row.get("reference_profile_reused")),
                "lane_pattern_matches_expected": _to_bool(row.get("lane_pattern_matches_expected")),
                "earned_one_visible": flags["earned_one_visible"],
                "raw_pressure_visible": flags["raw_pressure_visible"],
                "latent_overcrown_visible": flags["latent_overcrown_visible"],
                "relation_debt_visible": flags["relation_debt_visible"],
                "return_debt_visible": flags["return_debt_visible"],
                "false_one_pressure_visible": flags["false_one_pressure_visible"],
                "final_false_one_crowns": _to_int(row.get("final_false_one_crowns")),
            }
        )
    return evaluation


def collapse_holdout_evaluation_decision(evaluation_rows: Iterable[dict[str, object]]) -> str:
    rows = list(evaluation_rows)
    if not rows:
        return "fresh_holdout_challenge_locked_evaluation_not_run"
    statuses = {str(row.get("row_status", "")) for row in rows}
    if "resist_false_crown_stop" in statuses:
        return "resist_fresh_holdout_false_crown_stop"
    if "resist_dead_safe_earned_lost" in statuses:
        return "resist_fresh_holdout_dead_safe_or_earned_lost"
    protocol_holds = {
        "hold_unknown_weather_rung",
        "hold_expected_manifest_not_frozen",
        "hold_candidate_names_unmasked",
        "hold_reference_profile_reused",
    }
    if statuses & protocol_holds:
        return "hold_fresh_holdout_protocol_incomplete"
    if "hold_lane_pattern_mismatch" in statuses:
        return "hold_fresh_holdout_lane_pattern_mismatch"

    present_rungs = {str(row.get("weather_rung", "")) for row in rows}
    if not set(REQUIRED_WEATHER_RUNGS).issubset(present_rungs):
        return "hold_fresh_holdout_weather_ladder_incomplete"

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
            return "expand_fresh_holdout_all_weather_rungs_safe_for_reviewer_package"
        return "witness_fresh_holdout_all_weather_rungs_safe_latent_hold"
    if statuses & {"witness_holdout_partial_safe_failure", "witness_holdout_structured_zero_partial"}:
        return "witness_fresh_holdout_partial_ladder_or_lane_visibility"
    return "hold_fresh_holdout_partial_or_unpressured"


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines(evaluation_rows: list[dict[str, object]], evaluation_decision: str) -> list[str]:
    lines = [
        "# v1.7 Fresh Holdout Synthetic-Field Challenge",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "`v1.7.6-alpha` does not close the core question. It locks the fresh-holdout design: fresh seeds, held-out controlled profile variants, controlled weather shifts, candidate-name masking, and a predeclared lane manifest.",
        "",
        "## When to run triad27 / deep81 / wide243",
        "",
        RUN_ORDER_ANSWER,
        "",
        "The three-rung holdout ladder belongs after this gate is merged and CI green, so `v1.7.7-alpha` can package actual reproduction guidance instead of a promise-shaped fog machine.",
        "",
        "Process scar: run triad27 first and inspect the report, evaluator, and assistant handoff before deeper rungs. Do not use an all-weather one-shot runner until the smallest rung proves the output pipeline.",
        "",
        "Report label note: some debt-evidence builders are historical modules and may retain internal v1.6 report-version labels when wrapped by a v1.7.6 holdout evaluator. The active package/evaluator boundary remains `v1.7.6-alpha`.",
        "",
        "## Holdout law",
        "",
        "A holdout is not a rerun in a fake mustache. It must separate fresh seeds, held-out controlled variants, candidate-name masking, and predeclared lane expectations before the summary is judged.",
        "",
        "Required weather ladder:",
        "",
        "```text",
        "triad27 = 3^3 local expression weather",
        "deep81  = 3^4 perturbation / late-shock bridge",
        "wide243 = 3^5 temporal-depth / time-axis stress",
        "```",
        "",
        "## Evaluation decision",
        "",
        f"`{evaluation_decision}`",
        "",
    ]
    if evaluation_rows:
        lines.extend(
            [
                "| holdout run | rung | status | names masked | manifest frozen | false crowns |",
                "|---|---|---|---|---|---:|",
                *[
                    f"| `{row['holdout_run_id']}` | `{row['weather_rung']}` | `{row['row_status']}` | {row['candidate_names_masked']} | {row['expected_manifest_frozen']} | {row['final_false_one_crowns']} |"
                    for row in evaluation_rows
                ],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No fresh holdout summary CSV was supplied. This gate locks the schema, run order, and decision grammar before holdout summaries are attached.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This is controlled synthetic-field holdout design. It is not role-blind discovery, and it adds no physics claim, no manuscript v2, no independent generator-family claim, and no native math mutation.",
            "",
            "## Next gate",
            "",
            f"`{NEXT_GATE}` audits anti-tautology and role-dependence pressure after the holdout ladder has a clean summary or explicitly records what remains in HOLD.",
        ]
    )
    return lines


def build_v1_7_fresh_holdout_challenge(output_dir: Path, *, holdout_summary_csv: Path | None = None) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    evaluation_rows: list[dict[str, object]] = []
    if holdout_summary_csv is not None:
        evaluation_rows = evaluate_holdout_rows(_read_csv(Path(holdout_summary_csv)))
    evaluation_decision = collapse_holdout_evaluation_decision(evaluation_rows)

    _write_markdown(paths["read"], _readme_lines(evaluation_rows, evaluation_decision))
    write_dict_rows_csv(paths["holdout_design"], HOLDOUT_DESIGN_ROWS)
    write_dict_rows_csv(paths["expected_outputs"], EXPECTED_OUTPUT_ROWS)
    write_dict_rows_csv(paths["weather_ladder"], WEATHER_LADDER_ROWS)
    write_dict_rows_csv(paths["run_order"], RUN_ORDER_ROWS)
    write_dict_rows_csv(paths["candidate_masking"], CANDIDATE_MASKING_ROWS)
    write_dict_rows_csv(paths["input_schema"], INPUT_SCHEMA_ROWS)
    write_dict_rows_csv(paths["output_structure"], OUTPUT_STRUCTURE_ROWS)
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
        "independent_generator_claimed": False,
        "core_question_closed": False,
        "required_weather_rungs": REQUIRED_WEATHER_RUNGS,
        "run_order_answer": RUN_ORDER_ANSWER,
        "run_order_forbidden": RUN_ORDER_FORBIDDEN,
        "output_structure_layers": [row["output_layer"] for row in OUTPUT_STRUCTURE_ROWS],
        "historical_report_label_note": "Some included debt-evidence builders may retain historical internal report-version labels; the active holdout evaluator boundary remains v1.7.6-alpha.",
        "holdout_summary_csv": str(holdout_summary_csv) if holdout_summary_csv is not None else None,
        "evaluation_rows": len(evaluation_rows),
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "v1.7.6 separates fresh holdout pressure from reference-profile reruns.",
        "integration_modularity": "The gate locks holdout design and optional evaluation summary before reviewer packaging; it does not start manuscript v2 or mutate native math.",
        "witness_translation": "Passing the full ladder supports controlled synthetic-field holdout survival, not role-blind discovery or external reality proof.",
        "trace": "fresh seeds -> held-out profile variant -> masked candidate names -> frozen expected manifest -> triad27/deep81/wide243 summary -> false-crown stop.",
        "overdo_risk": "Running only the friendly rung, or treating a clean controlled holdout as independent generator evidence.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_fresh_holdout_challenge_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 fresh holdout synthetic-field challenge package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_fresh_holdout_challenge"))
    parser.add_argument("--holdout-summary-csv", type=Path, default=None, help="Optional holdout summary CSV to evaluate against v1.7.6 rules.")
    args = parser.parse_args(argv)
    paths = build_v1_7_fresh_holdout_challenge(args.out, holdout_summary_csv=args.holdout_summary_csv)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
