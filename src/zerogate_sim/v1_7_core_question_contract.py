from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.0-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
CLAIM_DOMAIN = "controlled_synthetic_field_adversarial_weather"
V1_7_DECISION_STATE = "0_question_contract_opened_no_new_evidence"
NEXT_GATE = "v1.7.1-alpha — Return Gate Trace Lock"

BOUNDED_CLAIM_UNDER_TEST = (
    "Inside controlled synthetic-field adversarial weather, the final trinary witness "
    "distinguishes earned-one from raw expression pressure, latent overcrown, relation "
    "debt, return debt, and false-one pressure better than raw, binary, dead-safe, "
    "average-gate, and ablated witnesses, while preserving final false-one crowns at zero."
)

OUTPUT_FILES = {
    "read": "v1_7_core_question_contract_read.md",
    "contract": "v1_7_core_question_contract.json",
    "lanes": "v1_7_lane_contract.csv",
    "answer_states": "v1_7_answer_states.csv",
    "falsifiers": "v1_7_falsifier_register.csv",
    "forbidden": "v1_7_forbidden_claims.csv",
    "audit": "v1_7_core_question_contract_audit.json",
    "bundle": "v1_7_core_question_contract_bundle.zip",
}

LANE_ROWS = [
    {
        "lane": "earned_one",
        "trinary_state": "+1",
        "meaning": "final expression; crown accepted only after raw expression survives return-depth, lineage, independence, and current harness witness",
        "must_distinguish_from": "raw_expression_pressure, dead_safe_refusal, borrowed_relation",
        "v1_7_status": "required_lane",
    },
    {
        "lane": "raw_expression_pressure",
        "trinary_state": "pre-final pressure",
        "meaning": "local expression pressure; not final truth and not final +1",
        "must_distinguish_from": "earned_one",
        "v1_7_status": "required_lane",
    },
    {
        "lane": "latent_overcrown",
        "trinary_state": "0",
        "meaning": "candidate pressure held in structured zero rather than falsely crowned",
        "must_distinguish_from": "earned_one, generic_failure, false_one_pressure",
        "v1_7_status": "required_but_fragile_lane_seed_sensitive_until_repaired_or_demoted",
    },
    {
        "lane": "relation_debt",
        "trinary_state": "0",
        "meaning": "relation looks meaningful but remains incomplete, borrowed, unstable, or not earned enough for final +1",
        "must_distinguish_from": "earned_one, raw_expression_pressure, return_debt",
        "v1_7_status": "required_lane",
    },
    {
        "lane": "return_debt",
        "trinary_state": "0",
        "meaning": "distinction, polarity, and relation create return-potential, but observed return / memory / depth does not pay the debt",
        "must_distinguish_from": "relation_debt, collapse, false_return_theater, earned_one",
        "v1_7_status": "required_lane",
    },
    {
        "lane": "false_one_pressure",
        "trinary_state": "-1",
        "meaning": "candidate pressure appears expressible but is exposed as unsafe for final crown",
        "must_distinguish_from": "latent_hold, relation_debt, earned_one",
        "v1_7_status": "required_lane",
    },
]

ANSWER_STATE_ROWS = [
    {
        "state": "+1",
        "meaning": "yes, the core question is answered inside controlled synthetic-field adversarial weather",
        "required_evidence": "all required lanes visible, baselines beaten, holdout/fresh pressure survives, role-dependence bounded, final false-one crowns remain zero",
        "forbidden_upgrade": "role-blind discovery, observed-universe bridge, physics/cosmology proof",
    },
    {
        "state": "0",
        "meaning": "partial, bounded, or unresolved; preserve evidence but do not crown the full question",
        "required_evidence": "at least one lane, baseline, holdout, or role-dependence condition remains unresolved",
        "forbidden_upgrade": "calling a partial answer a full answer because the pattern is beautiful",
    },
    {
        "state": "-1",
        "meaning": "no; the full core question is not earned under controlled synthetic-field adversarial weather",
        "required_evidence": "false crowns, lane collapse, dead-safe equivalence, baseline equivalence, or role-label recounting defeats the claim",
        "forbidden_upgrade": "patching the wording to hide the failed question",
    },
]

FALSIFIER_ROWS = [
    {
        "falsifier": "lane_visibility_failure",
        "breaks_claim_if": "earned-one, raw pressure, latent overcrown, relation debt, return debt, or false-one pressure cannot be represented as distinct states",
        "minimal_required_repair": "lane taxonomy repair or core question narrowing",
        "overdo_risk": "inventing new lanes to save the claim",
    },
    {
        "falsifier": "earned_one_dead_safe_failure",
        "breaks_claim_if": "final false crowns stay zero only because real earned-one is refused",
        "minimal_required_repair": "compare native witness against dead-safe baseline and report earned-one preservation",
        "overdo_risk": "calling non-crowning intelligence",
    },
    {
        "falsifier": "false_one_final_crown",
        "breaks_claim_if": "any designed trap or false-one pressure receives final +1 under the tested weather",
        "minimal_required_repair": "stop closeout, inspect gate and final-witness path, rerun only after repair",
        "overdo_risk": "averaging the false crown away in aggregate totals",
    },
    {
        "falsifier": "return_specificity_collapse",
        "breaks_claim_if": "return-potential, observed return, return-depth, and return debt collapse into one vague return score",
        "minimal_required_repair": "v1.7.1 return trace lock before more evidence",
        "overdo_risk": "turning return into metaphor machinery instead of measurable witness behavior",
    },
    {
        "falsifier": "baseline_equivalence",
        "breaks_claim_if": "raw, binary, dead-safe, average-gate, no-return, no-relation, no-lineage, no-echo, or no-zero-hold witnesses explain the result equally well",
        "minimal_required_repair": "baseline and ablation falsifier matrix",
        "overdo_risk": "adding more baselines without deciding what failure means",
    },
    {
        "falsifier": "role_label_recounting",
        "breaks_claim_if": "lane assignment is only role-label recounting rather than witness-computed numeric behavior",
        "minimal_required_repair": "masked role-dependence audit",
        "overdo_risk": "pretending masked role audit equals role-blind discovery",
    },
    {
        "falsifier": "holdout_failure",
        "breaks_claim_if": "the pattern survives only the reference profile or known seed family",
        "minimal_required_repair": "fresh holdout synthetic-field challenge",
        "overdo_risk": "moving into independent-generator work before the controlled holdout is honest",
    },
    {
        "falsifier": "reader_path_failure",
        "breaks_claim_if": "a cold reviewer cannot understand the question, witness, lanes, falsifiers, and boundaries without private chat history",
        "minimal_required_repair": "reviewer-start-here package",
        "overdo_risk": "making another evidence cathedral instead of a narrow door",
    },
]

FORBIDDEN_CLAIM_ROWS = [
    {
        "claim": "observed_universe_bridge",
        "status": "forbidden_in_v1_7_0",
        "reason": "the current evidence is controlled synthetic-field software evidence only",
    },
    {
        "claim": "physics_or_cosmology_proof",
        "status": "forbidden_in_v1_7_0",
        "reason": "no physical observation, spacetime metric, or cosmology experiment is being tested",
    },
    {
        "claim": "role_blind_discovery_solved",
        "status": "forbidden_in_v1_7_0",
        "reason": "designed-role harness and masked-role audit are not independent role-blind discovery",
    },
    {
        "claim": "new_native_gate_or_mutated_native_math",
        "status": "forbidden_in_v1_7_0",
        "reason": "v1.7 audits the native witness; it does not change C_Z = min(D, P, R, B)",
    },
    {
        "claim": "manuscript_v2_is_ready_now",
        "status": "forbidden_in_v1_7_0",
        "reason": "manuscript v2 waits until the v1.7 core question closes or is deliberately held as partial",
    },
]


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines() -> list[str]:
    return [
        "# v1.7 Core Question Contract",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision state:** `{V1_7_DECISION_STATE}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Contract",
        "",
        "`v1.7.0-alpha` opens the answer line. It does not answer the question yet.",
        "",
        "The claim under test is:",
        "",
        f"> {BOUNDED_CLAIM_UNDER_TEST}",
        "",
        "This is a controlled synthetic-field claim. It is not a physics claim, not a cosmology claim, not an observed-universe bridge, and not role-blind discovery.",
        "",
        "## Required lane set",
        "",
        "| lane | state | status |",
        "|---|---|---|",
        *[f"| `{row['lane']}` | `{row['trinary_state']}` | {row['v1_7_status']} |" for row in LANE_ROWS],
        "",
        "## Falsifier posture",
        "",
        "Every strong word in the claim must have a way to fail. If one of the required lanes collapses, if a simpler baseline explains the result, if a false-one receives a final crown, or if the lane assignment is just role-label recounting, the full answer cannot close `+1`.",
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}` locks the return-gate trace: return-potential, observed return, return-depth, return debt, collapse, and false return theater must remain separable.",
    ]


def build_v1_7_core_question_contract(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(out_dir)

    read_path = out_dir / OUTPUT_FILES["read"]
    contract_path = out_dir / OUTPUT_FILES["contract"]
    lanes_path = out_dir / OUTPUT_FILES["lanes"]
    states_path = out_dir / OUTPUT_FILES["answer_states"]
    falsifiers_path = out_dir / OUTPUT_FILES["falsifiers"]
    forbidden_path = out_dir / OUTPUT_FILES["forbidden"]
    audit_path = out_dir / OUTPUT_FILES["audit"]

    _write_markdown(read_path, _readme_lines())
    write_dict_rows_csv(lanes_path, LANE_ROWS)
    write_dict_rows_csv(states_path, ANSWER_STATE_ROWS)
    write_dict_rows_csv(falsifiers_path, FALSIFIER_ROWS)
    write_dict_rows_csv(forbidden_path, FORBIDDEN_CLAIM_ROWS)

    contract: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "decision_state": V1_7_DECISION_STATE,
        "core_question": CORE_QUESTION,
        "claim_domain": CLAIM_DOMAIN,
        "native_witness": NATIVE_WITNESS,
        "bounded_claim_under_test": BOUNDED_CLAIM_UNDER_TEST,
        "lane_count": len(LANE_ROWS),
        "required_lanes": [row["lane"] for row in LANE_ROWS],
        "answer_states": [row["state"] for row in ANSWER_STATE_ROWS],
        "falsifier_count": len(FALSIFIER_ROWS),
        "forbidden_claims": [row["claim"] for row in FORBIDDEN_CLAIM_ROWS],
        "next_gate": NEXT_GATE,
        "evidence_added": False,
        "manuscript_v2_started": False,
        "role_blind_discovery_claimed": False,
        "observed_universe_claimed": False,
        "native_math_mutated": False,
    }
    contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    audit: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "checks": {
            "core_question_named": CORE_QUESTION.endswith("?"),
            "native_witness_preserved": NATIVE_WITNESS == "C_Z = min(D, P, R, B)",
            "all_core_lanes_named": len(contract["required_lanes"]) == 6,
            "trinary_answer_states_named": contract["answer_states"] == ["+1", "0", "-1"],
            "falsifiers_present": len(FALSIFIER_ROWS) >= 8,
            "forbidden_claims_present": len(FORBIDDEN_CLAIM_ROWS) >= 5,
            "no_new_evidence_claim": contract["evidence_added"] is False,
            "next_gate_is_return_trace_lock": NEXT_GATE.startswith("v1.7.1-alpha"),
        },
        "stop_if": "claim language outruns controlled synthetic-field evidence",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    bundle_path = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="v1_7_core_question_contract_bundle",
    )

    return {
        "read": read_path,
        "contract": contract_path,
        "lanes": lanes_path,
        "answer_states": states_path,
        "falsifiers": falsifiers_path,
        "forbidden": forbidden_path,
        "audit": audit_path,
        "bundle": bundle_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the v1.7 core-question contract package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_core_question_contract"))
    args = parser.parse_args(argv)
    paths = build_v1_7_core_question_contract(args.out)
    print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
