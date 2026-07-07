from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.2-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "witness_lane_taxonomy_locked_latent_overcrown_held"
GATE_KIND = "lane_taxonomy_and_latent_overcrown_repair_not_closeout"
NEXT_GATE = "v1.7.3-alpha — Baseline and Ablation Falsifier Matrix"

OUTPUT_FILES = {
    "read": "v1_7_lane_taxonomy_read.md",
    "decision": "v1_7_lane_taxonomy_decision.json",
    "lane_taxonomy": "v1_7_lane_taxonomy.csv",
    "lane_boundaries": "v1_7_lane_boundaries.csv",
    "latent_overcrown_repair": "v1_7_latent_overcrown_repair.csv",
    "relation_return_specificity": "v1_7_relation_return_debt_specificity.csv",
    "candidate_family_map": "v1_7_candidate_family_lane_map.csv",
    "decision_rules": "v1_7_lane_visibility_decision_rules.csv",
    "falsifiers": "v1_7_lane_taxonomy_falsifiers.csv",
    "audit": "v1_7_lane_taxonomy_audit.json",
    "bundle": "v1_7_lane_taxonomy_bundle.zip",
}

LANE_TAXONOMY_ROWS = [
    {
        "lane": "earned_one",
        "final_state": "+1",
        "definition": "final expression; raw expression survived return-depth, temporal lineage, independence, and current harness witness",
        "positive_evidence_surface": "final_earned_one_count > 0; final_trinary_symbol = +1; final_band = earned_one",
        "must_not_be_confused_with": "raw_expression_pressure, dead_safe_refusal, latent_overcrown, borrowed_relation",
        "primary_code_surface": "final_output._final_band; earned_one.build_earned_one_rows; gates.C_Z weakest-gate law",
        "v1_7_2_status": "active_required_lane",
        "closeout_rule": "must remain visible; if false crowns stay zero only by killing earned-one, the core answer fails",
    },
    {
        "lane": "raw_expression_pressure",
        "final_state": "pre-final pressure",
        "definition": "local expression pressure produced before final witness; visible pressure, not final truth",
        "positive_evidence_surface": "raw_expression_pressure or raw_expressed_count > 0",
        "must_not_be_confused_with": "earned_one, false_one_pressure, latent_overcrown",
        "primary_code_surface": "gates.expressed; earned_one.raw_expressed_count; final_output.raw_expression_pressure",
        "v1_7_2_status": "active_required_lane",
        "closeout_rule": "must stay visible so final +1 cannot hide the pressure it filtered",
    },
    {
        "lane": "latent_overcrown",
        "final_state": "0 structured zero / fragile HOLD",
        "definition": "latent/probe raw expression pressure held in zero rather than falsely crowned",
        "positive_evidence_surface": "latent_overcrown_pressure or latent_overcrown_count > 0; first-alpha 2442/2442 historical hold; current fresh debt reproduction is seed-sensitive",
        "must_not_be_confused_with": "earned_one, generic_failure, relation_debt, return_debt, false_one_pressure",
        "primary_code_surface": "earned_one.latent_overcrown_count; final_output.latent_overcrown_demoted; witness ablation no_latent_hold enemy",
        "v1_7_2_status": "fragile_historical_pressure_explicit_hold_until_reproduced_or_narrowed",
        "closeout_rule": "cannot silently carry a +1 closeout; reproduce in later v1.7 pressure or narrow / close partial at v1.7.8",
    },
    {
        "lane": "relation_debt",
        "final_state": "0 structured zero",
        "definition": "relation is meaningful but incomplete, under-owned, borrowed, unstable, or global-only; hold instead of crown or kill",
        "positive_evidence_surface": "relation_debt_count > 0; earned_one_band = relation_debt_expression; final_band = relation_debt_hold",
        "must_not_be_confused_with": "return_debt, latent_overcrown, earned_one, field_echo_false_one",
        "primary_code_surface": "earned_one.RELATION_DEBT_KINDS; relation_debt_count; echo_independence relation_debt bands",
        "v1_7_2_status": "active_required_lane",
        "closeout_rule": "must remain separate from return debt before baseline work",
    },
    {
        "lane": "return_debt",
        "final_state": "0 structured zero",
        "definition": "Gamma is meaningful but observed return, memory, closure, or return-depth has not paid the debt",
        "positive_evidence_surface": "return_debt_count > 0; return_debt_dpr_hold; return_debt_near_expression; return_gap_quarantine",
        "must_not_be_confused_with": "relation_debt, latent_overcrown, collapse, false_return_theater, earned_one",
        "primary_code_surface": "GateScores.return_potential; gates.return_score; earned_one.RETURN_DEBT_KINDS; return_debt_count",
        "v1_7_2_status": "active_required_lane",
        "closeout_rule": "must remain Gamma/B-specific; no zero-crossing shortcut",
    },
    {
        "lane": "false_one_pressure",
        "final_state": "-1 resist / demotion",
        "definition": "trap or unsafe raw expression pressure exposed before final crown",
        "positive_evidence_surface": "raw_false_one_pressure > 0 and false_one_demoted_count >= raw_false_one_pressure; final_false_one_crowns = 0",
        "must_not_be_confused_with": "latent_overcrown, relation_debt, return_debt, earned_one",
        "primary_code_surface": "truth_role trap; earned_one.false_one_count; final_output.false_one_demoted",
        "v1_7_2_status": "active_required_lane",
        "closeout_rule": "any final false-one crown is a stop condition",
    },
]

LANE_BOUNDARY_ROWS = [
    {
        "boundary": "raw_vs_earned",
        "left_lane": "raw_expression_pressure",
        "right_lane": "earned_one",
        "distinction": "raw is local pressure; earned-one is final +1 after return-depth, lineage, independence, and harness witness",
        "failure_if_blurred": "the model crowns loud pressure before witness",
    },
    {
        "boundary": "latent_vs_earned",
        "left_lane": "latent_overcrown",
        "right_lane": "earned_one",
        "distinction": "latent/probe pressure may locally express but remains zero-held until it earns final witness",
        "failure_if_blurred": "seed-sensitive not-yet pressure becomes a fake +1",
    },
    {
        "boundary": "latent_vs_false_one",
        "left_lane": "latent_overcrown",
        "right_lane": "false_one_pressure",
        "distinction": "latent is not-yet / probe pressure held in zero; false-one is trap pressure demoted by resist",
        "failure_if_blurred": "the witness kills all ambiguity or treats traps as mere not-yet",
    },
    {
        "boundary": "relation_vs_return_debt",
        "left_lane": "relation_debt",
        "right_lane": "return_debt",
        "distinction": "relation debt is incomplete ownership/binding; return debt is Gamma high while observed B/depth/closure is incomplete",
        "failure_if_blurred": "the debt lane becomes a generic hold and v1.7 cannot answer the core question",
    },
    {
        "boundary": "return_debt_vs_false_return_theater",
        "left_lane": "return_debt",
        "right_lane": "raw_expression_pressure",
        "distinction": "return debt has meaningful D/P/R/Gamma but insufficient B/depth; false-return theater is crossing/oscillation without memory",
        "failure_if_blurred": "zero crossing gets crowned as return",
    },
    {
        "boundary": "false_one_vs_baseline_safety",
        "left_lane": "false_one_pressure",
        "right_lane": "dead_safe_refusal",
        "distinction": "demotion is only meaningful if earned-one remains visible; dead-safe avoids false crowns by refusing all crowns",
        "failure_if_blurred": "non-crowning gets mistaken for intelligence",
    },
]

LATENT_OVERCROWN_REPAIR_ROWS = [
    {
        "surface": "first_research_alpha_archived_record",
        "observed_status": "reproduced_historical_hold",
        "evidence_note": "initial proof 1194/1194 held; fresh reproduction 1248/1248 held; combined 2442/2442 held",
        "v1_7_2_disposition": "lineage_evidence_only_not_current_closeout_proof",
        "allowed_claim": "latent overcrown has historical proof-record support inside generated toy fields",
        "blocked_claim": "historical latent overcrown alone answers the current v1.7 controlled synthetic-field question",
    },
    {
        "surface": "v1_6_20_triad27_debt_evidence",
        "observed_status": "visible_small_weather",
        "evidence_note": "triad27 debt evidence card reports 3 latent overcrown events",
        "v1_7_2_disposition": "visible_but_small_weather",
        "allowed_claim": "latent overcrown can appear in the repaired debt lane",
        "blocked_claim": "triad27 visibility proves deeper-weather reproduction",
    },
    {
        "surface": "v1_6_21_deep81_wide243_reference_debt_evidence",
        "observed_status": "visible_reference_deeper_weather",
        "evidence_note": "README/current index records reference latent overcrown pressure before fresh reproduction",
        "v1_7_2_disposition": "reference_visibility_not_enough",
        "allowed_claim": "reference deeper-weather runs saw latent overcrown pressure",
        "blocked_claim": "reference visibility alone is a stable current lane",
    },
    {
        "surface": "v1_6_22_fresh_seed_debt_reproduction",
        "observed_status": "not_reproduced_cleanly",
        "evidence_note": "current evidence index says latent overcrown did not reproduce; README records 18 -> 0",
        "v1_7_2_disposition": "fragile_hold_requiring_rewitness_or_claim_narrowing",
        "allowed_claim": "latent overcrown is seed-sensitive in the current evidence line",
        "blocked_claim": "latent overcrown is a reproduced current lane without caveat",
    },
    {
        "surface": "v1_7_2_repair_decision",
        "observed_status": "explicit_HOLD",
        "evidence_note": "the lane remains named but cannot carry a +1 closeout until later evidence reproduces it or v1.7.8 narrows the question",
        "v1_7_2_disposition": "no_ghost_lane_no_fake_crown",
        "allowed_claim": "v1.7.2 has repaired the claim boundary by making the latent lane caveat explicit",
        "blocked_claim": "the latent lane is silently fixed because the taxonomy is cleaner",
    },
]

RELATION_RETURN_SPECIFICITY_ROWS = [
    {
        "debt_lane": "relation_debt",
        "signal_shape": "D/P may be meaningful while binding is under-owned, global-only, unstable, or borrowed",
        "primary_question": "does the candidate own the relation enough to deserve one?",
        "typical_candidates": "relation_debt_local; relation_debt_global_a; relation_debt_global_b; field_echo as pressure if trap-shaped",
        "hold_reason": "relation has not become owned stable structure",
        "not_this": "Gamma high with observed return incomplete",
    },
    {
        "debt_lane": "return_debt",
        "signal_shape": "D/P/R create Gamma, but B, memory, continuity, closure, or depth remains incomplete",
        "primary_question": "did the candidate return with preserved structure?",
        "typical_candidates": "return_debt_local; closure_gap_candidate; dual_return_gap_candidate; perturbation_survival_candidate",
        "hold_reason": "return-potential has not paid observed-return debt",
        "not_this": "borrowed or under-owned relation before return is even the main wound",
    },
    {
        "debt_lane": "shared_boundary",
        "signal_shape": "both are structured zero, not hidden failure and not hidden +1",
        "primary_question": "which mechanism is missing: ownership of relation or completion of return?",
        "typical_candidates": "candidate may migrate under weather, but report must name the limiting wound",
        "hold_reason": "zero-state carries useful diagnostic pressure",
        "not_this": "flat middle state with no mechanism",
    },
]

CANDIDATE_FAMILY_MAP_ROWS = [
    {
        "candidate_family": "earned_return_control",
        "example_ids": "D00,D09",
        "expected_lane": "earned_one",
        "role": "positive control",
        "taxonomy_note": "must keep +1 visible so safety does not become dead-safe refusal",
    },
    {
        "candidate_family": "false_one_trap_control",
        "example_ids": "D01,D10",
        "expected_lane": "false_one_pressure",
        "role": "false-one control",
        "taxonomy_note": "raw pressure should demote before final crown",
    },
    {
        "candidate_family": "relation_debt_local",
        "example_ids": "D02",
        "expected_lane": "relation_debt",
        "role": "local relation debt probe",
        "taxonomy_note": "D/P can be meaningful while relation is under-owned",
    },
    {
        "candidate_family": "relation_debt_global_a / relation_debt_global_b",
        "example_ids": "D04,D05",
        "expected_lane": "relation_debt",
        "role": "global relation debt probe",
        "taxonomy_note": "paired relation can matter without either local part earning +1",
    },
    {
        "candidate_family": "return_debt_local",
        "example_ids": "D03",
        "expected_lane": "return_debt",
        "role": "local return debt probe",
        "taxonomy_note": "relation matters but return comes back changed",
    },
    {
        "candidate_family": "closure_gap_candidate",
        "example_ids": "D06",
        "expected_lane": "return_debt",
        "role": "closure repair probe",
        "taxonomy_note": "first witness frame survives, but closure does not return the same structure",
    },
    {
        "candidate_family": "dual_return_gap_candidate",
        "example_ids": "D07",
        "expected_lane": "return_debt",
        "role": "dual return probe",
        "taxonomy_note": "complementary pressure changes the candidate without automatically earning +1",
    },
    {
        "candidate_family": "perturbation_survival_candidate",
        "example_ids": "D08",
        "expected_lane": "return_debt_or_latent_overcrown_hold",
        "role": "edge-case bridge",
        "taxonomy_note": "survival alone is not earned return; this family may be the future latent-overcrown repair probe",
    },
    {
        "candidate_family": "field_echo",
        "example_ids": "F26",
        "expected_lane": "false_one_pressure_or_relation_debt_depending_role",
        "role": "relation echo pressure",
        "taxonomy_note": "borrowed relation must not be crowned as independent one",
    },
]

DECISION_RULE_ROWS = [
    {
        "rule_id": "earned_one_visibility",
        "question": "Does the native/final witness still preserve real earned-one?",
        "pass_condition": "final_earned_one_count > 0 and earned expressers remain visible",
        "hold_or_fail": "dead-safe refusal if zero false crowns occur only because all crowns are refused",
    },
    {
        "rule_id": "latent_overcrown_integrity",
        "question": "Is latent overcrown visible and reproduced in the current evidence line?",
        "pass_condition": "latent_overcrown_pressure > 0 in fresh/holdout evidence or explicit claim narrowing before closeout",
        "hold_or_fail": "HOLD if seed-sensitive; fail if it stays in +1 closeout without caveat",
    },
    {
        "rule_id": "relation_debt_specificity",
        "question": "Can relation debt be named without using return debt as a trash label?",
        "pass_condition": "relation_debt_count > 0 with relation-specific candidate families or echo-debt diagnosis",
        "hold_or_fail": "HOLD if relation debt only appears through role labels or generic non-crown",
    },
    {
        "rule_id": "return_debt_specificity",
        "question": "Can return debt be named as Gamma high but B/depth incomplete?",
        "pass_condition": "return_debt_count > 0 or return_gap quarantine/fertile hold with Gamma/B separation visible",
        "hold_or_fail": "HOLD if return debt collapses into zero crossing or generic hold",
    },
    {
        "rule_id": "false_one_safety",
        "question": "Does false-one pressure stay visible and demoted?",
        "pass_condition": "raw_false_one_pressure > 0; false_one_demoted_count >= raw_false_one_pressure; final_false_one_crowns = 0",
        "hold_or_fail": "STOP if any trap receives final +1",
    },
    {
        "rule_id": "baseline_gate_forward",
        "question": "Is v1.7.3 allowed to begin?",
        "pass_condition": "lane taxonomy locked and latent overcrown caveat explicit",
        "hold_or_fail": "HOLD if any lane remains ghost-labeled or if latent overcrown is silently counted as reproduced",
    },
]

FALSIFIER_ROWS = [
    {
        "falsifier": "ghost_latent_overcrown",
        "breaks_claim_if": "latent overcrown remains in the full claim as if current evidence reproduced it cleanly",
        "minimal_repair": "mark latent overcrown as fragile HOLD until later reproduction or closeout narrowing",
        "overdo_risk": "deleting the lane and pretending historical evidence never existed",
    },
    {
        "falsifier": "flat_zero",
        "breaks_claim_if": "latent, relation debt, return debt, quarantine, and not-yet all collapse into one generic zero",
        "minimal_repair": "publish lane taxonomy and boundary rules",
        "overdo_risk": "creating decorative sub-lanes that never affect evidence decisions",
    },
    {
        "falsifier": "relation_return_blur",
        "breaks_claim_if": "relation debt and return debt cannot be separated by mechanism",
        "minimal_repair": "keep relation-ownership and Gamma/B observed-return boundaries explicit",
        "overdo_risk": "turning every non-crown into return debt because return sounds profound",
    },
    {
        "falsifier": "raw_pressure_crown",
        "breaks_claim_if": "raw expression pressure is treated as final earned-one",
        "minimal_repair": "force raw-vs-earned table and final witness stack before baseline work",
        "overdo_risk": "over-tightening until real earned-one is refused",
    },
    {
        "falsifier": "trap_as_latent",
        "breaks_claim_if": "false-one pressure is softened into latent hold to avoid a resist decision",
        "minimal_repair": "keep trap/false-one demotion separate from latent not-yet pressure",
        "overdo_risk": "moralizing traps instead of measuring them",
    },
]


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines() -> list[str]:
    return [
        "# v1.7 Lane Taxonomy and Latent Overcrown Repair",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "This gate does not answer the full question. It makes the lane set auditable before baseline and ablation falsifiers begin.",
        "",
        "## Lane set",
        "",
        "| lane | final state | v1.7.2 status |",
        "|---|---|---|",
        *[f"| `{row['lane']}` | `{row['final_state']}` | {row['v1_7_2_status']} |" for row in LANE_TAXONOMY_ROWS],
        "",
        "## Latent overcrown repair",
        "",
        "Latent overcrown is not erased and not crowned. The historical first-research-alpha record held it cleanly, but the current Four Gates fresh-seed debt line made it seed-sensitive. Therefore `v1.7.2-alpha` repairs the claim surface by placing latent overcrown in explicit HOLD:",
        "",
        "```text",
        "latent overcrown = named lane + historical support + current seed-sensitivity",
        "closeout status = reproduce later, narrow later, or close v1.7 partial",
        "```",
        "",
        "No ghost lane. No fake crown. No haunted bookkeeping.",
        "",
        "## Mechanism boundaries",
        "",
        "- raw expression pressure is not earned-one;",
        "- latent overcrown is not false-one pressure;",
        "- relation debt is not return debt;",
        "- return debt requires Gamma/B separation from `v1.7.1-alpha`;",
        "- false-one pressure remains a resist lane, not a softened hold;",
        "- zero-state remains structured witness, not a flat trash can.",
        "",
        "## Boundaries",
        "",
        "- no new heavy evidence crown;",
        "- no native witness mutation;",
        "- no role-blind discovery claim;",
        "- no manuscript v2 start;",
        "- no physics, topology, dimension, or observed-universe claim.",
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}`",
        "",
        "Baseline work may begin only because the lane set now tells the baselines exactly what they must fail to explain.",
    ]


def build_v1_7_lane_taxonomy(output_dir: Path) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    paths = {key: output_dir / value for key, value in OUTPUT_FILES.items() if key != "bundle"}

    _write_markdown(paths["read"], _readme_lines())
    write_dict_rows_csv(paths["lane_taxonomy"], LANE_TAXONOMY_ROWS)
    write_dict_rows_csv(paths["lane_boundaries"], LANE_BOUNDARY_ROWS)
    write_dict_rows_csv(paths["latent_overcrown_repair"], LATENT_OVERCROWN_REPAIR_ROWS)
    write_dict_rows_csv(paths["relation_return_specificity"], RELATION_RETURN_SPECIFICITY_ROWS)
    write_dict_rows_csv(paths["candidate_family_map"], CANDIDATE_FAMILY_MAP_ROWS)
    write_dict_rows_csv(paths["decision_rules"], DECISION_RULE_ROWS)
    write_dict_rows_csv(paths["falsifiers"], FALSIFIER_ROWS)

    latent_status = next(row for row in LANE_TAXONOMY_ROWS if row["lane"] == "latent_overcrown")
    decision: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "decision": DECISION,
        "gate_kind": GATE_KIND,
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "new_heavy_evidence_added": False,
        "manuscript_v2_started": False,
        "required_lanes": [row["lane"] for row in LANE_TAXONOMY_ROWS],
        "lane_boundaries": [row["boundary"] for row in LANE_BOUNDARY_ROWS],
        "latent_overcrown_v1_7_2_status": latent_status["v1_7_2_status"],
        "latent_overcrown_closeout_rule": latent_status["closeout_rule"],
        "latent_overcrown_silently_reproduced": False,
        "relation_debt_equals_return_debt": False,
        "raw_expression_equals_earned_one": False,
        "false_one_pressure_softened_to_latent": False,
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "mechanism_boundary": "The lane taxonomy separates raw pressure, final crown, structured zero/debt, and resist/demotion before baseline claims begin.",
        "integration_modularity": "v1.7.2 lands as a taxonomy/repair package only; it does not add heavy evidence, start manuscript v2, or mutate native math.",
        "witness_translation": "Latent overcrown is preserved as a named lane but explicitly held as seed-sensitive in the current evidence line.",
        "trace": "A reviewer can follow lane -> evidence surface -> code surface -> closeout rule without private explanation.",
        "overdo_risk": "Inventing new lanes to rescue a weak one, or deleting latent overcrown to avoid the caveat.",
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    bundle = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_lane_taxonomy_bundle",
    )
    paths["bundle"] = bundle
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7 lane taxonomy and latent-overcrown repair package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_lane_taxonomy"))
    args = parser.parse_args(argv)
    paths = build_v1_7_lane_taxonomy(args.out)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
