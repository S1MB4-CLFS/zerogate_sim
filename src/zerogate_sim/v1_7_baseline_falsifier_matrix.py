from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.3-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "baseline_falsifier_matrix_locked_no_core_closeout"
GATE_KIND = "baseline_and_ablation_falsifier_matrix_not_closeout"
NEXT_GATE = "v1.7.4-alpha — Perturbation Spectrum Witness"

OUTPUT_FILES = {
    "read": "v1_7_baseline_falsifier_matrix_read.md",
    "decision": "v1_7_baseline_falsifier_matrix_decision.json",
    "baseline_matrix": "v1_7_baseline_falsifier_matrix.csv",
    "failure_modes": "v1_7_baseline_failure_modes.csv",
    "pass_rules": "v1_7_baseline_pass_rules.csv",
    "input_schema": "v1_7_baseline_input_schema.csv",
    "evaluation": "v1_7_baseline_evaluation.csv",
    "audit": "v1_7_baseline_falsifier_audit.json",
    "bundle": "v1_7_baseline_falsifier_matrix_bundle.zip",
}

REQUIRED_BASELINE_ENEMIES = [
    "raw_expression_only",
    "binary_raw_or_fail",
    "dead_safe_no_crown",
    "average_gate_raw",
    "no_return_gate_raw",
    "no_relation_gate_raw",
    "no_lineage_or_return_depth_witness",
    "no_echo_independence_witness",
    "no_zero_hold_witness",
]

BASELINE_MATRIX_ROWS = [
    {
        "baseline": "native_final_trinary_witness",
        "family": "control",
        "what_it_removes_or_collapses": "nothing; preserves Four Gates plus final witness stack",
        "must_show_or_fail_by": "must preserve earned-one, hold structured zero/debt, demote false-one pressure, and keep final false-one crowns at zero",
        "native_counterproof_required": "final_earned_one_events > 0; structured_zero_pressure visible when pressure exists; final_false_one_crowns = 0",
        "fatal_if": "native itself creates a final false-one crown or becomes dead-safe by refusing earned-one",
        "v1_7_3_status": "required_control",
    },
    {
        "baseline": "raw_expression_only",
        "family": "raw",
        "what_it_removes_or_collapses": "return-depth, lineage, echo-independence, truth-role witness, and structured zero",
        "must_show_or_fail_by": "should overcrown raw false-one, latent, relation-debt, or return-debt pressure when adversarial pressure exists",
        "native_counterproof_required": "native demotes / holds what raw-only crowns",
        "fatal_if": "raw-only matches native without false crowns while preserving earned-one and debt visibility",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "binary_raw_or_fail",
        "family": "binary_collapse",
        "what_it_removes_or_collapses": "trinary witness; turns structured zero into generic not +1 or raw +1",
        "must_show_or_fail_by": "should erase zero-state meaning or crown pressure too early",
        "native_counterproof_required": "native keeps +1 / 0 / -1 lanes separately visible",
        "fatal_if": "binary collapse explains the full lane set as well as native",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "dead_safe_no_crown",
        "family": "degenerate_safety",
        "what_it_removes_or_collapses": "all final crowns",
        "must_show_or_fail_by": "gets zero false crowns only by losing real earned-one",
        "native_counterproof_required": "native keeps earned-one visible while also keeping final false crowns at zero",
        "fatal_if": "native cannot preserve earned-one better than dead-safe refusal",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "average_gate_raw",
        "family": "gate_ablation",
        "what_it_removes_or_collapses": "weakest-gate law; averages D/P/R/B",
        "must_show_or_fail_by": "allows strong gates to compensate for a missing gate",
        "native_counterproof_required": "native refuses crowns where one required gate is weak",
        "fatal_if": "average-gate explains final outcomes equally well without overcrown wounds",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_return_gate_raw",
        "family": "gate_ablation",
        "what_it_removes_or_collapses": "observed return B as a required native gate",
        "must_show_or_fail_by": "crowns D/P/R pressure that has not paid observed-return debt",
        "native_counterproof_required": "native holds Gamma-high / B-incomplete candidates as return debt or rejects false return theater",
        "fatal_if": "no-return performs as safely as native on return-debt pressure",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_relation_gate_raw",
        "family": "gate_ablation",
        "what_it_removes_or_collapses": "relation R as a required native gate",
        "must_show_or_fail_by": "crowns D/P/B pressure without owned relation",
        "native_counterproof_required": "native holds under-owned / borrowed / unstable relation pressure instead of crowning it",
        "fatal_if": "no-relation performs as safely as native on relation-debt pressure",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_lineage_or_return_depth_witness",
        "family": "final_witness_ablation",
        "what_it_removes_or_collapses": "temporal lineage and return-depth maturation after raw expression",
        "must_show_or_fail_by": "crowns local expression before it endures and returns repeatedly",
        "native_counterproof_required": "native delays final +1 until depth / lineage witness is paid",
        "fatal_if": "no-lineage/no-depth can preserve lane distinctions as well as native",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_echo_independence_witness",
        "family": "final_witness_ablation",
        "what_it_removes_or_collapses": "echo-independence / borrowed-relation witness",
        "must_show_or_fail_by": "promotes field echo or borrowed relation pressure as earned-one",
        "native_counterproof_required": "native holds relation debt or demotes false-one pressure when relation is borrowed",
        "fatal_if": "no-echo performs as safely as native on relation-echo pressure",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_zero_hold_witness",
        "family": "final_witness_ablation",
        "what_it_removes_or_collapses": "active structured zero / debt hold",
        "must_show_or_fail_by": "forces latent, relation debt, return debt, or quarantine pressure into crown or generic failure",
        "native_counterproof_required": "native keeps zero-state as visible structured witness",
        "fatal_if": "no-zero-hold explains the result without losing lane information or overcrowning pressure",
        "v1_7_3_status": "required_enemy",
    },
    {
        "baseline": "no_false_one_demotion_witness",
        "family": "final_witness_ablation",
        "what_it_removes_or_collapses": "trap / false-one demotion layer",
        "must_show_or_fail_by": "allows raw false-one pressure to become final false-one crowns",
        "native_counterproof_required": "native keeps raw false-one pressure visible but uncrowned",
        "fatal_if": "demotion removal does not create a visible wound when false-one pressure exists",
        "v1_7_3_status": "additional_enemy",
    },
]

FAILURE_MODE_ROWS = [
    {
        "failure_mode": "dead_safe_equivalence",
        "breaks_claim_if": "zero false crowns are achieved only by refusing real earned-one",
        "watch_baseline": "dead_safe_no_crown",
        "minimal_repair": "report earned-one preservation beside false-crown safety",
        "overdo_risk": "calling non-crowning intelligence",
    },
    {
        "failure_mode": "raw_pressure_equivalence",
        "breaks_claim_if": "raw expression pressure alone explains the final witness result",
        "watch_baseline": "raw_expression_only",
        "minimal_repair": "show which raw pressure became structured zero or resist instead of final +1",
        "overdo_risk": "burying false pressure in aggregate earned-one counts",
    },
    {
        "failure_mode": "binary_collapse_equivalence",
        "breaks_claim_if": "binary raw/fail reporting preserves the same information as trinary output",
        "watch_baseline": "binary_raw_or_fail",
        "minimal_repair": "show lane-level zero-state accounting",
        "overdo_risk": "turning every 0 into a decorative label",
    },
    {
        "failure_mode": "average_gate_compensation",
        "breaks_claim_if": "averaging D/P/R/B performs as well as weakest-gate coherence",
        "watch_baseline": "average_gate_raw",
        "minimal_repair": "expose candidates where one missing gate must block a crown",
        "overdo_risk": "tuning thresholds until the average baseline behaves like native",
    },
    {
        "failure_mode": "return_gate_ablation_survives",
        "breaks_claim_if": "removing observed return does not wound the distinction between earned-one and return debt",
        "watch_baseline": "no_return_gate_raw",
        "minimal_repair": "stress Gamma-high / B-incomplete candidates",
        "overdo_risk": "pretending zero crossing is return",
    },
    {
        "failure_mode": "relation_gate_ablation_survives",
        "breaks_claim_if": "removing relation does not wound relation-debt or echo-pressure behavior",
        "watch_baseline": "no_relation_gate_raw",
        "minimal_repair": "stress under-owned and borrowed relation families",
        "overdo_risk": "turning relation debt into generic hold",
    },
    {
        "failure_mode": "lineage_depth_ablation_survives",
        "breaks_claim_if": "local raw expression can be crowned without return-depth or temporal lineage",
        "watch_baseline": "no_lineage_or_return_depth_witness",
        "minimal_repair": "make maturity / repeated-return delay visible in reports",
        "overdo_risk": "blocking real earned-one forever",
    },
    {
        "failure_mode": "echo_independence_ablation_survives",
        "breaks_claim_if": "borrowed relation or field echo still behaves like earned-one when echo witness is removed",
        "watch_baseline": "no_echo_independence_witness",
        "minimal_repair": "separate owned relation from borrowed relation in lane reports",
        "overdo_risk": "treating every relation as suspicious and killing genuine relation",
    },
    {
        "failure_mode": "no_zero_hold_ablation_survives",
        "breaks_claim_if": "structured zero is not needed to distinguish latent, relation debt, return debt, and quarantine pressure",
        "watch_baseline": "no_zero_hold_witness",
        "minimal_repair": "show zero-state lane counts and promotion wounds",
        "overdo_risk": "creating decorative zero subtypes with no decision role",
    },
]

PASS_RULE_ROWS = [
    {
        "rule_id": "native_control_safety",
        "required_observation": "native final_false_one_crowns = 0",
        "failure_if": "native final_false_one_crowns > 0",
        "decision_effect": "-1 stop for the core question until repaired",
    },
    {
        "rule_id": "earned_one_preservation",
        "required_observation": "native final_earned_one_events > 0 and dead_safe loses earned-one",
        "failure_if": "dead-safe ties native because native also refuses earned-one",
        "decision_effect": "dead-safe safety is not enough; native must be better",
    },
    {
        "rule_id": "structured_zero_accounting",
        "required_observation": "native keeps latent / relation / return debt visible while no-zero-hold or raw/binary variants erase or promote them",
        "failure_if": "structured zero carries no observable difference",
        "decision_effect": "0 hold or claim narrowing",
    },
    {
        "rule_id": "false_one_demotion",
        "required_observation": "false-one pressure is visible and demoted by native while raw/no-demotion variants overcrown it",
        "failure_if": "false-one demotion is not distinguishable from raw or binary behavior",
        "decision_effect": "0 hold or -1 if false crowns appear",
    },
    {
        "rule_id": "gate_necessity",
        "required_observation": "average/no-return/no-relation variants show a wound when the missing gate matters",
        "failure_if": "simpler gate formulas explain the same result equally well",
        "decision_effect": "0 hold; baseline pressure not answered",
    },
    {
        "rule_id": "witness_stack_necessity",
        "required_observation": "no-lineage/no-depth and no-echo variants fail on premature or borrowed coherence",
        "failure_if": "final witness stack adds no observable safety or lane information",
        "decision_effect": "0 hold; final witness not yet justified",
    },
]

INPUT_SCHEMA_ROWS = [
    {"field": "baseline", "required": "yes", "meaning": "baseline/enemy name matching the v1.7.3 matrix"},
    {"field": "final_earned_one_events", "required": "yes", "meaning": "final +1 count under the given baseline"},
    {"field": "earned_lost", "required": "recommended", "meaning": "earned-one lost relative to native; important for dead-safe"},
    {"field": "raw_expression_pressure", "required": "recommended", "meaning": "raw pressure visible under the baseline"},
    {"field": "raw_false_one_pressure", "required": "recommended", "meaning": "raw false-one pressure visible under the baseline"},
    {"field": "structured_zero_pressure", "required": "recommended", "meaning": "latent/relation/return debt pressure held as zero"},
    {"field": "structured_zero_promoted", "required": "recommended", "meaning": "zero/debt pressure promoted or erased by the baseline"},
    {"field": "final_false_one_crowns", "required": "yes", "meaning": "final false-one crowns under the baseline"},
    {"field": "baseline_status", "required": "optional", "meaning": "upstream baseline status, preserved if present"},
]


def _int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate_baseline_summary_rows(summary_rows: Iterable[dict[str, Any]]) -> list[dict[str, object]]:
    """Classify an already-produced baseline summary against the v1.7.3 matrix.

    The input can be the v1.6.15-style native ablation summary or any compatible
    CSV with the fields listed in INPUT_SCHEMA_ROWS. Missing required enemies are
    reported as HOLD rather than silently passing. This function does not run heavy
    evidence; it only witnesses a summary surface.
    """

    rows_by_name = {str(row.get("baseline", "")): row for row in summary_rows if row.get("baseline")}
    native = rows_by_name.get("native_final_trinary_witness", {})
    native_earned = _int(native, "final_earned_one_events")
    native_false = _int(native, "final_false_one_crowns")
    evaluated: list[dict[str, object]] = []
    for matrix_row in BASELINE_MATRIX_ROWS:
        name = matrix_row["baseline"]
        row = rows_by_name.get(name)
        if row is None:
            evaluated.append(
                {
                    "baseline": name,
                    "family": matrix_row["family"],
                    "matrix_status": "hold_not_evaluated",
                    "reason": "baseline summary row missing; matrix remains a falsifier requirement",
                    "final_earned_one_events": 0,
                    "earned_delta_from_native": 0,
                    "earned_lost": 0,
                    "structured_zero_promoted": 0,
                    "final_false_one_crowns": 0,
                    "upstream_status": "missing",
                }
            )
            continue

        earned = _int(row, "final_earned_one_events")
        earned_lost = _int(row, "earned_lost")
        zero_promoted = _int(row, "structured_zero_promoted")
        false_crowns = _int(row, "final_false_one_crowns")
        upstream = str(row.get("baseline_status", ""))

        if name == "native_final_trinary_witness":
            if false_crowns > 0:
                status = "resist_native_false_crown"
                reason = "native control produced final false-one crowns"
            elif earned > 0:
                status = "native_control_visible"
                reason = "native preserves earned-one while remaining available for false-crown safety checks"
            else:
                status = "hold_native_quiet"
                reason = "native did not show earned-one preservation in this summary"
        elif name == "dead_safe_no_crown":
            if false_crowns <= native_false and (earned_lost > 0 or (native_earned > 0 and earned < native_earned)):
                status = "enemy_fails_dead_safe_refusal"
                reason = "dead-safe avoids false crowns by losing earned-one"
            else:
                status = "hold_dead_safe_not_pressured"
                reason = "dead-safe did not visibly lose earned-one in this summary"
        elif false_crowns > native_false:
            status = "enemy_fails_false_crowns"
            reason = "baseline introduces final false-one crowns beyond native"
        elif zero_promoted > 0:
            status = "enemy_fails_zero_overcrown"
            reason = "baseline promotes or erases structured zero/debt pressure"
        elif earned_lost > 0:
            status = "enemy_fails_earned_loss"
            reason = "baseline loses earned-one that native preserves"
        else:
            status = "hold_needs_stronger_pressure"
            reason = "baseline did not show a decisive wound in this summary"

        evaluated.append(
            {
                "baseline": name,
                "family": matrix_row["family"],
                "matrix_status": status,
                "reason": reason,
                "final_earned_one_events": earned,
                "earned_delta_from_native": earned - native_earned,
                "earned_lost": earned_lost,
                "structured_zero_promoted": zero_promoted,
                "final_false_one_crowns": false_crowns,
                "upstream_status": upstream,
            }
        )
    return evaluated


def collapse_evaluation_decision(evaluation_rows: list[dict[str, object]]) -> str:
    if not evaluation_rows:
        return "baseline_falsifier_matrix_locked_evaluation_not_run"
    statuses = {str(row["matrix_status"]) for row in evaluation_rows}
    if "resist_native_false_crown" in statuses:
        return "resist_native_breach"
    required_missing = {
        row["baseline"]
        for row in evaluation_rows
        if row["baseline"] in REQUIRED_BASELINE_ENEMIES and row["matrix_status"] == "hold_not_evaluated"
    }
    if required_missing:
        return "hold_missing_required_baselines"
    exposed = [s for s in statuses if s.startswith("enemy_fails_")]
    if exposed and "enemy_fails_dead_safe_refusal" in statuses:
        return "expand_baseline_enemies_expose_witness_work"
    if exposed:
        return "witness_partial_baseline_wounds_visible"
    return "hold_need_stronger_pressure"


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines(evaluation_rows: list[dict[str, object]], decision: str) -> list[str]:
    lines = [
        "# v1.7 Baseline and Ablation Falsifier Matrix",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Evaluation decision:** `{decision}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "This gate does not close the core question. It locks the weaker enemies that the final trinary witness must beat before any later `+1` closeout can be trusted.",
        "",
        "## Required enemies",
        "",
        "| baseline | family | what it removes / collapses | fatal if |",
        "|---|---|---|---|",
    ]
    for row in BASELINE_MATRIX_ROWS:
        lines.append(f"| `{row['baseline']}` | {row['family']} | {row['what_it_removes_or_collapses']} | {row['fatal_if']} |")
    lines.extend([
        "",
        "## Especially fatal failure",
        "",
        "```text",
        "A dead-safe witness gets zero false crowns by refusing real earned-one.",
        "```",
        "",
        "That is not intelligence. That is a locked door with a lab badge.",
        "",
        "## Pass posture",
        "",
        "Native must win three ways at once:",
        "",
        "1. preserve earned-one;",
        "2. hold structured zero/debt as visible `0`;",
        "3. demote false-one pressure without final false-one crowns.",
        "",
    ])
    if evaluation_rows:
        lines.extend([
            "## Evaluation witness",
            "",
            "| baseline | status | earned | earned delta | zero promoted | final false |",
            "|---|---|---:|---:|---:|---:|",
        ])
        for row in evaluation_rows:
            lines.append(
                f"| `{row['baseline']}` | {row['matrix_status']} | {row['final_earned_one_events']} | "
                f"{row['earned_delta_from_native']} | {row['structured_zero_promoted']} | {row['final_false_one_crowns']} |"
            )
        lines.append("")
    else:
        lines.extend([
            "## Evaluation witness",
            "",
            "No baseline summary CSV was supplied. This run locks the falsifier matrix but does not claim baseline superiority yet.",
            "",
        ])
    lines.extend([
        "## Boundaries",
        "",
        "- no native witness mutation;",
        "- no new heavy evidence crown;",
        "- no role-blind discovery claim;",
        "- no manuscript v2 start;",
        "- no physics, topology, dimensions, cosmology, or observed-universe claim.",
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}`",
    ])
    return lines


def build_v1_7_baseline_falsifier_matrix(output_dir: Path, *, baseline_summary_csv: Path | None = None) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    evaluation_rows: list[dict[str, object]] = []
    if baseline_summary_csv is not None:
        evaluation_rows = evaluate_baseline_summary_rows(_read_csv(Path(baseline_summary_csv)))
    evaluation_decision = collapse_evaluation_decision(evaluation_rows)

    _write_markdown(paths["read"], _readme_lines(evaluation_rows, evaluation_decision))
    write_dict_rows_csv(paths["baseline_matrix"], BASELINE_MATRIX_ROWS)
    write_dict_rows_csv(paths["failure_modes"], FAILURE_MODE_ROWS)
    write_dict_rows_csv(paths["pass_rules"], PASS_RULE_ROWS)
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
        "required_baseline_enemies": REQUIRED_BASELINE_ENEMIES,
        "baseline_count": len(BASELINE_MATRIX_ROWS),
        "failure_mode_count": len(FAILURE_MODE_ROWS),
        "baseline_summary_csv": str(baseline_summary_csv) if baseline_summary_csv is not None else None,
        "evaluation_rows": len(evaluation_rows),
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "v1.7.3 defines what weaker witnesses remove, what wound they should expose, and what would make native equivalence fatal.",
        "integration_modularity": "This is a falsifier-matrix gate; it does not mutate native math, start manuscript v2, or claim the full v1.7 answer.",
        "witness_translation": "Zero false crowns are not enough; earned-one preservation and structured-zero visibility must be reported beside safety.",
        "trace": "baseline -> removed mechanism -> expected wound -> native counterproof -> fatal equivalence.",
        "overdo_risk": "Adding endless baselines without deciding what failure means.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_baseline_falsifier_matrix_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 baseline and ablation falsifier matrix package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_baseline_falsifier_matrix"))
    parser.add_argument("--baseline-summary-csv", type=Path, default=None, help="Optional baseline summary CSV to witness against the v1.7.3 matrix.")
    args = parser.parse_args(argv)
    paths = build_v1_7_baseline_falsifier_matrix(args.out, baseline_summary_csv=args.baseline_summary_csv)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
