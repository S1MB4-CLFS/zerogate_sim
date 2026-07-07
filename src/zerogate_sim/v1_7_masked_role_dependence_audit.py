from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.5-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "masked_role_dependence_audit_locked_no_role_blind_claim"
GATE_KIND = "masked_role_dependence_audit_not_closeout"
NEXT_GATE = "v1.7.6-alpha — Fresh Holdout Synthetic-Field Challenge"

OUTPUT_FILES = {
    "read": "v1_7_masked_role_dependence_audit_read.md",
    "decision": "v1_7_masked_role_dependence_audit_decision.json",
    "audit_rules": "v1_7_masked_role_audit_rules.csv",
    "masked_numeric_visibility": "v1_7_masked_numeric_visibility.csv",
    "role_dependence_pressure": "v1_7_role_dependence_pressure.csv",
    "input_schema": "v1_7_masked_role_audit_input_schema.csv",
    "evaluation": "v1_7_masked_role_audit_evaluation.csv",
    "audit": "v1_7_masked_role_audit.json",
    "bundle": "v1_7_masked_role_dependence_audit_bundle.zip",
}

REQUIRED_MASKED_LANES = [
    "earned_one",
    "raw_expression_pressure",
    "latent_overcrown",
    "relation_debt",
    "return_debt",
    "false_one_pressure",
    "final_false_one_crowns",
]

MASKED_AUDIT_RULE_ROWS = [
    {
        "audit_rule": "mask_role_labels",
        "meaning": "designed roles may define the controlled harness, but the reviewer-facing audit must hide direct role labels before lane interpretation",
        "pass_signal": "role_labels_masked is true and no direct role column is required to classify the numeric lane pattern",
        "failure_signal": "lane assignment is a role-label recount",
        "claim_boundary": "masked audit, not role-blind discovery",
    },
    {
        "audit_rule": "separate_witness_computed_from_role_shaped",
        "meaning": "report whether lanes are computed from witness metrics or merely explained after seeing the designed role",
        "pass_signal": "earned-one, relation debt, return debt, false-one pressure, and false-crown safety remain visible numerically",
        "failure_signal": "lanes become unintelligible without role labels",
        "claim_boundary": "designed-profile shaped evidence may still be useful if witness-computed",
    },
    {
        "audit_rule": "forbid_role_blind_discovery_language",
        "meaning": "passing a masked audit does not mean unknown-field discovery is solved",
        "pass_signal": "decision language keeps the line bounded to controlled designed scenarios",
        "failure_signal": "masked numeric visibility is translated into role-blind discovery",
        "claim_boundary": "role-stripped / role-blind wording waits for later holdout and independent generator gates",
    },
    {
        "audit_rule": "false_crown_stop_survives_masking",
        "meaning": "role masking must not hide final false-one crowns",
        "pass_signal": "final_false_one_crowns remains explicit and zero in the audit decision",
        "failure_signal": "a false crown appears or is averaged away",
        "claim_boundary": "safe failure remains the controlling witness obligation",
    },
]

MASKED_NUMERIC_VISIBILITY_ROWS = [
    {
        "visible_signal": "earned_one",
        "why_it_matters": "proves the audit is not dead-safe; real earned expression must remain crownable",
        "masked_view_requirement": "final earned-one events or equivalent witness-computed +1 count visible without direct role labels",
        "safe_decision": "+1 only when return-depth, lineage, and independence are still paid",
        "must_not_do": "treat lack of crowns as success if earned controls disappear",
    },
    {
        "visible_signal": "relation_debt",
        "why_it_matters": "pressure from borrowed, unstable, or under-owned relation must remain structured zero, not label bookkeeping",
        "masked_view_requirement": "relation-debt count or relation-debt score visible from numeric witness metrics",
        "safe_decision": "0 relation-debt hold",
        "must_not_do": "explain relation debt only by revealing the candidate role",
    },
    {
        "visible_signal": "return_debt",
        "why_it_matters": "Gamma without observed return must remain debt, not crown",
        "masked_view_requirement": "return-potential / observed-return gap visible without direct role labels",
        "safe_decision": "0 return-debt hold",
        "must_not_do": "treat high D/P/R or zero crossing as observed return",
    },
    {
        "visible_signal": "false_one_pressure",
        "why_it_matters": "trap-shaped pressure must remain visible enough to demote before final crown",
        "masked_view_requirement": "raw false-one pressure or adversarial pressure count visible under masked numeric review",
        "safe_decision": "-1 demotion or 0 quarantine before crown",
        "must_not_do": "hide pressure because labels are hidden",
    },
    {
        "visible_signal": "final_false_one_crowns",
        "why_it_matters": "the smallest number remains the loudest stop condition",
        "masked_view_requirement": "final false-one crown count is explicit in every masked audit summary",
        "safe_decision": "must remain 0",
        "must_not_do": "average a false crown away in totals",
    },
]

ROLE_DEPENDENCE_PRESSURE_ROWS = [
    {
        "pressure_state": "masked_core_lanes_visible",
        "meaning": "numeric witness pattern shows earned-one, relation debt, return debt, false-one pressure, and zero false crowns without direct role labels",
        "decision": "expand within controlled designed scenario; do not claim role-blind discovery",
        "overdo_risk": "turning masked readability into unknown-field discovery",
    },
    {
        "pressure_state": "designed_profile_shaped_hold",
        "meaning": "outputs are witness-computed but still depend on designed profile family and harness expectations",
        "decision": "witness / hold; later holdout required",
        "overdo_risk": "calling designed-profile shaping a flaw instead of a boundary",
    },
    {
        "pressure_state": "role_leakage_pressure",
        "meaning": "direct role information or proxy leakage appears to carry lane assignment",
        "decision": "hold or resist until leakage is removed or bounded",
        "overdo_risk": "hiding leakage behind pretty lane language",
    },
    {
        "pressure_state": "label_only_lane_failure",
        "meaning": "lane assignment fails when role labels are hidden",
        "decision": "resist; the lane is not yet witness-computed",
        "overdo_risk": "keeping the lane in the full answer sentence anyway",
    },
    {
        "pressure_state": "false_crown_stop",
        "meaning": "a false-one crown appears under masked audit",
        "decision": "resist and block closeout",
        "overdo_risk": "averaging the stop condition into aggregate success",
    },
]

INPUT_SCHEMA_ROWS = [
    {
        "column": "candidate_set",
        "required": "yes",
        "meaning": "masked candidate group, run id, or scenario id under review",
        "example": "wide243_masked_seed_block_A",
    },
    {
        "column": "role_labels_masked",
        "required": "yes",
        "meaning": "boolean flag: direct designed roles were hidden before numeric lane review",
        "example": "true",
    },
    {
        "column": "role_leakage_score",
        "required": "yes",
        "meaning": "0..1 pressure that role labels or role-like proxies are leaking into the audit",
        "example": "0.03",
    },
    {
        "column": "label_only_lane_assignment",
        "required": "yes",
        "meaning": "boolean flag: lane assignment requires role labels rather than witness metrics",
        "example": "false",
    },
    {
        "column": "final_earned_one_events",
        "required": "yes",
        "meaning": "masked visible earned-one count or equivalent final +1 signal",
        "example": "128",
    },
    {
        "column": "raw_expression_pressure",
        "required": "yes",
        "meaning": "masked visible raw pressure count before final witness",
        "example": "188",
    },
    {
        "column": "latent_overcrown",
        "required": "no",
        "meaning": "masked visible latent-overcrown pressure if present; may remain HOLD",
        "example": "12",
    },
    {
        "column": "relation_debt",
        "required": "yes",
        "meaning": "masked visible relation-debt count or equivalent structured-zero signal",
        "example": "17",
    },
    {
        "column": "return_debt",
        "required": "yes",
        "meaning": "masked visible return-debt count or equivalent Gamma/B gap signal",
        "example": "9",
    },
    {
        "column": "false_one_pressure",
        "required": "yes",
        "meaning": "masked visible false-one pressure count",
        "example": "31",
    },
    {
        "column": "final_false_one_crowns",
        "required": "yes",
        "meaning": "stop-condition count; must be zero for any later expand decision",
        "example": "0",
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


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "masked"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _lane_visibility_flags(row: dict[str, object]) -> dict[str, bool]:
    return {
        "earned_one_visible": _to_int(row.get("final_earned_one_events")) > 0,
        "raw_pressure_visible": _to_int(row.get("raw_expression_pressure")) > 0,
        "latent_overcrown_visible": _to_int(row.get("latent_overcrown")) > 0,
        "relation_debt_visible": _to_int(row.get("relation_debt")) > 0,
        "return_debt_visible": _to_int(row.get("return_debt")) > 0,
        "false_one_pressure_visible": _to_int(row.get("false_one_pressure")) > 0,
        "zero_false_crowns": _to_int(row.get("final_false_one_crowns")) == 0,
    }


def classify_masked_role_row(row: dict[str, object]) -> str:
    final_false_crowns = _to_int(row.get("final_false_one_crowns"))
    if final_false_crowns > 0:
        return "resist_false_crown_stop"
    if not _to_bool(row.get("role_labels_masked")):
        return "hold_labels_unmasked"
    if _to_bool(row.get("label_only_lane_assignment")):
        return "resist_label_only_lane_assignment"
    if _to_float(row.get("role_leakage_score")) > 0.25:
        return "hold_role_leakage_pressure"

    flags = _lane_visibility_flags(row)
    if (
        flags["earned_one_visible"]
        and flags["raw_pressure_visible"]
        and flags["relation_debt_visible"]
        and flags["return_debt_visible"]
        and flags["false_one_pressure_visible"]
        and flags["zero_false_crowns"]
    ):
        return "witness_masked_core_lanes_visible"
    if flags["false_one_pressure_visible"] and flags["zero_false_crowns"]:
        return "witness_false_pressure_demoted_under_mask"
    if flags["relation_debt_visible"] or flags["return_debt_visible"] or flags["latent_overcrown_visible"]:
        return "witness_structured_zero_visible_under_mask"
    if flags["earned_one_visible"] and flags["raw_pressure_visible"]:
        return "witness_raw_and_earned_visible_under_mask"
    return "hold_masked_partial_or_unpressured"


def evaluate_masked_role_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    evaluation: list[dict[str, object]] = []
    for row in rows:
        flags = _lane_visibility_flags(row)
        evaluation.append(
            {
                "candidate_set": row.get("candidate_set", ""),
                "row_status": classify_masked_role_row(row),
                "role_labels_masked": _to_bool(row.get("role_labels_masked")),
                "role_leakage_score": _to_float(row.get("role_leakage_score")),
                "label_only_lane_assignment": _to_bool(row.get("label_only_lane_assignment")),
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


def collapse_masked_role_evaluation_decision(evaluation_rows: Iterable[dict[str, object]]) -> str:
    rows = list(evaluation_rows)
    if not rows:
        return "masked_role_audit_locked_evaluation_not_run"
    statuses = {str(row.get("row_status", "")) for row in rows}
    if "resist_false_crown_stop" in statuses:
        return "resist_masked_role_false_crown_stop"
    if "resist_label_only_lane_assignment" in statuses:
        return "resist_role_label_only_lane_failure"
    if {"hold_labels_unmasked", "hold_role_leakage_pressure"} & statuses:
        return "hold_masked_role_audit_leakage_or_unmasked"

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
            return "expand_masked_role_audit_core_lanes_visible_no_role_blind_claim"
        return "witness_masked_role_audit_core_lanes_visible_latent_hold"
    if statuses & {"witness_false_pressure_demoted_under_mask", "witness_structured_zero_visible_under_mask"}:
        return "witness_masked_role_audit_partial_designed_profile_shaped"
    return "hold_masked_role_audit_partial_or_unpressured"


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines(evaluation_rows: list[dict[str, object]], evaluation_decision: str) -> list[str]:
    lines = [
        "# v1.7 Masked Role-Dependence Audit",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "`v1.7.5-alpha` does not close the core question. It pressures the sharpest boundary left by the controlled harness: whether lane outputs remain witness-computed when direct role labels are masked.",
        "",
        "## Masked audit law",
        "",
        "Designed roles may define the controlled adversarial harness. They may not become the hidden mechanism that assigns lanes.",
        "",
        "The masked audit asks whether these signals remain numerically visible without direct role labels:",
        "",
        "```text",
        "earned-one",
        "raw expression pressure",
        "latent overcrown",
        "relation debt",
        "return debt",
        "false-one pressure",
        "final false-one crowns",
        "```",
        "",
        "Passing this audit is not role-blind discovery. It is a bounded witness that the current controlled designed profile is not merely role-label bookkeeping.",
        "",
        "## Evaluation decision",
        "",
        f"`{evaluation_decision}`",
        "",
    ]
    if evaluation_rows:
        lines.extend(
            [
                "| candidate set | status | masked | leakage | false crowns |",
                "|---|---|---|---:|---:|",
                *[
                    f"| `{row['candidate_set']}` | `{row['row_status']}` | {row['role_labels_masked']} | {row['role_leakage_score']:.3f} | {row['final_false_one_crowns']} |"
                    for row in evaluation_rows
                ],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No masked numeric summary CSV was supplied. This gate locks the schema and decision grammar before evidence summaries are attached.",
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
            f"`{NEXT_GATE}` pressures whether the lane pattern survives fresh seeds, held-out profile variants, controlled weather shifts, and candidate-name masking.",
        ]
    )
    return lines


def build_v1_7_masked_role_dependence_audit(output_dir: Path, *, masked_summary_csv: Path | None = None) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    evaluation_rows: list[dict[str, object]] = []
    if masked_summary_csv is not None:
        evaluation_rows = evaluate_masked_role_rows(_read_csv(Path(masked_summary_csv)))
    evaluation_decision = collapse_masked_role_evaluation_decision(evaluation_rows)

    _write_markdown(paths["read"], _readme_lines(evaluation_rows, evaluation_decision))
    write_dict_rows_csv(paths["audit_rules"], MASKED_AUDIT_RULE_ROWS)
    write_dict_rows_csv(paths["masked_numeric_visibility"], MASKED_NUMERIC_VISIBILITY_ROWS)
    write_dict_rows_csv(paths["role_dependence_pressure"], ROLE_DEPENDENCE_PRESSURE_ROWS)
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
        "required_masked_lanes": REQUIRED_MASKED_LANES,
        "masked_summary_csv": str(masked_summary_csv) if masked_summary_csv is not None else None,
        "evaluation_rows": len(evaluation_rows),
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "v1.7.5 separates witness-computed lane visibility from role-label assignment.",
        "integration_modularity": "This is a masked role-dependence audit gate; it does not revive shadow as discovery, start manuscript v2, or mutate native math.",
        "witness_translation": "Passing masked numeric visibility supports controlled designed-profile witness computation, not role-blind false-one discovery.",
        "trace": "masked candidate set -> leakage check -> numeric lane visibility -> false-crown stop -> bounded decision.",
        "overdo_risk": "Translating masked readability into unknown-field discovery before fresh holdout and independent generator pressure.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_masked_role_dependence_audit_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 masked role-dependence audit package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_masked_role_dependence_audit"))
    parser.add_argument("--masked-summary-csv", type=Path, default=None, help="Optional masked numeric summary CSV to evaluate against v1.7.5 rules.")
    args = parser.parse_args(argv)
    paths = build_v1_7_masked_role_dependence_audit(args.out, masked_summary_csv=args.masked_summary_csv)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
