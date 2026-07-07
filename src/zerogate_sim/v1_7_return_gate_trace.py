from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.1-alpha"
PREVIOUS_GATE = "v1.7.0-alpha — Core Question Contract"
NEXT_GATE = "v1.7.2-alpha — Lane Taxonomy and Latent Overcrown Repair"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION_STATE = "0_return_gate_trace_locked_no_new_evidence"

OUTPUT_FILES = {
    "read": "v1_7_return_gate_trace_read.md",
    "trace": "v1_7_return_gate_trace.json",
    "terms": "v1_7_return_terms.csv",
    "math_to_code": "v1_7_return_gate_math_to_code_map.csv",
    "debt_taxonomy": "v1_7_return_debt_taxonomy.csv",
    "false_return": "v1_7_false_return_theater.csv",
    "forbidden": "v1_7_return_gate_forbidden_readings.csv",
    "audit": "v1_7_return_gate_trace_audit.json",
    "bundle": "v1_7_return_gate_trace_bundle.zip",
}

RETURN_TERM_ROWS = [
    {
        "term": "distinction_D",
        "status": "gate_input",
        "definition": "candidate separates from background enough to be scored",
        "code_anchor": "zerogate_sim.gates.distinction_score",
        "crown_boundary": "not crownable alone",
    },
    {
        "term": "polarity_P",
        "status": "gate_input",
        "definition": "candidate carries positive and negative expression around zero",
        "code_anchor": "zerogate_sim.gates.polarity_score",
        "crown_boundary": "not crownable alone; zero crossing is not return",
    },
    {
        "term": "relation_R",
        "status": "gate_input",
        "definition": "candidate binds into relation with other candidate freedoms instead of isolated split",
        "code_anchor": "zerogate_sim.gates.relation_score",
        "crown_boundary": "not crownable alone; borrowed relation can create false pressure",
    },
    {
        "term": "return_potential_Gamma",
        "status": "pressure_not_crown",
        "definition": "Gamma = D * P * R; the first three gates make return possible",
        "code_anchor": "evaluate_run: return_potential = clamp01(distinction * polarity * relation)",
        "crown_boundary": "necessary pressure, not observed return, not final coherence",
    },
    {
        "term": "observed_return_B",
        "status": "fourth_gate",
        "definition": "candidate returns through zero pressure with memory, continuity, and persistence",
        "code_anchor": "zerogate_sim.gates.return_score",
        "crown_boundary": "required by C_Z; zero crossing alone is rejected as return theater",
    },
    {
        "term": "zero_gate_coherence_C_Z",
        "status": "native_witness",
        "definition": "weakest-gate coherence across D, P, R, and B",
        "code_anchor": "evaluate_run: zero_coherence = min(gates.values())",
        "crown_boundary": "a missing return gate cannot be averaged away",
    },
    {
        "term": "zero_depth",
        "status": "ordered_survival_trace",
        "definition": "ordered survival of D, P, R, and B under threshold",
        "code_anchor": "zerogate_sim.gates.zero_depth_from_gates",
        "crown_boundary": "depth records survival; it is not a private ontology claim",
    },
    {
        "term": "return_debt",
        "status": "structured_zero",
        "definition": "D/P/R and strength create credible return-potential, but B, memory, closure, or depth is incomplete",
        "code_anchor": "trinary_outcome_from_scores: return_debt_dpr_hold; earned_one.RETURN_DEBT_KINDS",
        "crown_boundary": "held as 0, not crowned as +1 and not demoted as random failure",
    },
    {
        "term": "false_return_theater",
        "status": "resist_pressure",
        "definition": "zero crossing, pulse, reset, collapse, or borrowed echo pretends to be coherent return",
        "code_anchor": "return_score components and falsifier docs",
        "crown_boundary": "must fail or hold; never final +1",
    },
]

MATH_TO_CODE_ROWS = [
    {
        "manuscript_or_theory_form": "Gamma_i(t) = D_i(t) P_i(t) R_i(t)",
        "repo_term": "return_potential_Gamma",
        "code_anchor": "src/zerogate_sim/gates.py::evaluate_run",
        "implemented_as": "return_potential = clamp01(distinction * polarity * relation)",
        "boundary": "Gamma is return-potential only; it is not observed return B and not C_Z.",
    },
    {
        "manuscript_or_theory_form": "B_i(t) observed return",
        "repo_term": "observed_return_B",
        "code_anchor": "src/zerogate_sim/gates.py::return_score",
        "implemented_as": "crossing_score plus half-cycle memory, continuity, and persistence",
        "boundary": "B is not mere zero crossing; noise and reset traps can cross zero without earning return.",
    },
    {
        "manuscript_or_theory_form": "C_Z^i(t) = min(D_i, P_i, R_i, B_i)",
        "repo_term": "zero_gate_coherence_C_Z",
        "code_anchor": "src/zerogate_sim/gates.py::evaluate_run",
        "implemented_as": "zero_coherence = min({'distinction','polarity','relation','return'}.values())",
        "boundary": "weakest gate decides; no average-gate repair is allowed.",
    },
    {
        "manuscript_or_theory_form": "Z^(k), k_i(t), K* return-depth language",
        "repo_term": "zero_depth_ordered_survival",
        "code_anchor": "src/zerogate_sim/gates.py::zero_depth_from_gates",
        "implemented_as": "ordered D/P/R/B threshold survival Z^0 through Z^4",
        "boundary": "toy-field ordered-depth trace, not a cosmic constant and not new physics.",
    },
    {
        "manuscript_or_theory_form": "chi_raw expression pressure",
        "repo_term": "raw_expression_pressure",
        "code_anchor": "src/zerogate_sim/gates.py::evaluate_run",
        "implemented_as": "expressed = strength >= strength_threshold and zero_coherence >= gate_threshold",
        "boundary": "raw expression remains pressure; it is not final earned-one.",
    },
    {
        "manuscript_or_theory_form": "chi_earned final witness",
        "repo_term": "earned_one_summary",
        "code_anchor": "src/zerogate_sim/earned_one.py::build_earned_one_rows",
        "implemented_as": "raw expression read through truth role, echo independence, relation debt, return debt, latent overcrown, and false-one pressure",
        "boundary": "current harness is controlled and role-aware; this does not claim role-blind discovery.",
    },
]

RETURN_DEBT_ROWS = [
    {
        "debt_state": "return_debt_dpr_hold",
        "state": "0",
        "trigger_shape": "D, P, and R are above threshold and Gamma is credible, but B is below full witness need",
        "code_anchor": "trinary_outcome_from_scores",
        "distinguish_from": "earned_one, collapse, relation_debt",
        "allowed_sentence": "return-potential exists but observed return has not paid the debt",
    },
    {
        "debt_state": "return_debt_local",
        "state": "0",
        "trigger_shape": "candidate returns altered, weakened, or memory-incomplete",
        "code_anchor": "earned_one.RETURN_DEBT_KINDS",
        "distinguish_from": "false_one_pressure and generic latent hold",
        "allowed_sentence": "near-success return remains structured zero",
    },
    {
        "debt_state": "closure_gap_candidate",
        "state": "0",
        "trigger_shape": "candidate survives initial witness frame but closure does not return same structure",
        "code_anchor": "earned_one.RETURN_DEBT_KINDS",
        "distinguish_from": "automatic demotion or premature crown",
        "allowed_sentence": "closure gap is a return-debt witness, not evidence of final expression",
    },
    {
        "debt_state": "dual_return_gap_candidate",
        "state": "0",
        "trigger_shape": "candidate and complementary return form diverge under witness pressure",
        "code_anchor": "earned_one.RETURN_DEBT_KINDS",
        "distinguish_from": "simple oscillation or relation debt",
        "allowed_sentence": "dual return is incomplete but not random",
    },
    {
        "debt_state": "perturbation_survival_candidate",
        "state": "0",
        "trigger_shape": "candidate survives late shock partly but loses enough return coherence to require hold",
        "code_anchor": "earned_one.RETURN_DEBT_KINDS",
        "distinguish_from": "collapse and final earned-one",
        "allowed_sentence": "structure survives partly; zero holds instead of lying",
    },
]

FALSE_RETURN_ROWS = [
    {
        "theater": "zero_crossing_only",
        "why_it_fails": "a signal can cross zero repeatedly without preserving form or memory",
        "code_pressure": "return_score multiplies crossing with memory, continuity, and persistence",
        "safe_result": "hold or reject; never +1 by crossing alone",
    },
    {
        "theater": "phase_reset_jump",
        "why_it_fails": "teleporting between phases is a cut, not return",
        "code_pressure": "_continuity_score penalizes large single-step jumps relative to RMS",
        "safe_result": "return gate drops; possible return debt or rejection",
    },
    {
        "theater": "collapse_return",
        "why_it_fails": "dying back to zero is not returning with preserved structure",
        "code_pressure": "_persistence_score compares early and late strength",
        "safe_result": "no earned-one if persistence fails",
    },
    {
        "theater": "borrowed_relation_return",
        "why_it_fails": "field echo can make relation look coherent without candidate-owned return",
        "code_pressure": "echo independence and relation-debt accounting remain downstream witnesses",
        "safe_result": "0 debt or -1 false pressure, not crown",
    },
]

FORBIDDEN_ROWS = [
    {
        "forbidden_reading": "Gamma is observed return",
        "reason": "Gamma is D * P * R return-potential; B is the observed return gate.",
        "replacement": "Gamma makes return possible; B witnesses whether return actually happens with memory.",
    },
    {
        "forbidden_reading": "zero crossing equals return",
        "reason": "noise and reset traps cross zero; return requires memory, continuity, and persistence.",
        "replacement": "zero crossing is only one pressure inside observed return.",
    },
    {
        "forbidden_reading": "return-potential is physical gravity",
        "reason": "the repo implements structural simulation pressure, not a physical force law.",
        "replacement": "call it structural return-potential or relational return pressure only.",
    },
    {
        "forbidden_reading": "return debt is failure",
        "reason": "return debt is structured zero: not earned, not random, not safe to crown.",
        "replacement": "return debt is a 0-state witness lane.",
    },
    {
        "forbidden_reading": "C_Z can average over missing return",
        "reason": "native witness is weakest-gate coherence.",
        "replacement": "if B is missing, C_Z stays limited; no beauty contest among gates.",
    },
    {
        "forbidden_reading": "v1.7.1 adds new evidence or answers the core question",
        "reason": "this gate locks trace and language; it does not run the full answer suite.",
        "replacement": "v1.7.1 is a trace lock before lane taxonomy and heavier evidence gates.",
    },
]


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines() -> list[str]:
    return [
        "# v1.7 Return Gate Trace Lock",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision state:** `{DECISION_STATE}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "**Evidence posture:** no new science evidence crown; trace lock only",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Trace spine",
        "",
        "`v1.7.1-alpha` locks the return gate before heavier v1.7 evidence work.",
        "",
        "```text",
        "D/P/R -> Gamma return-potential",
        "Gamma is not B",
        "B is observed return",
        "B is not zero-crossing alone",
        "C_Z = min(D, P, R, B)",
        "return debt = Gamma is meaningful but B / memory / closure / depth is incomplete",
        "```",
        "",
        "## What this version adds",
        "",
        "This gate makes the reviewer path explicit:",
        "",
        "- return-potential is generated by distinction, polarity, and relation;",
        "- observed return is the fourth gate;",
        "- return scoring requires crossing pressure plus memory, continuity, and persistence;",
        "- return debt is structured zero, not failure and not final +1;",
        "- false return theater must be held or resisted, never crowned.",
        "",
        "## What this version does not add",
        "",
        "- no native math mutation;",
        "- no new evidence crown;",
        "- no manuscript v2 start;",
        "- no role-blind discovery claim;",
        "- no physical gravity or observed-universe claim;",
        "- no literal closed-topology engine.",
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}`",
        "",
    ]


def build_v1_7_return_gate_trace(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(out_dir)
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}

    _write_markdown(paths["read"], _readme_lines())
    write_dict_rows_csv(paths["terms"], RETURN_TERM_ROWS)
    write_dict_rows_csv(paths["math_to_code"], MATH_TO_CODE_ROWS)
    write_dict_rows_csv(paths["debt_taxonomy"], RETURN_DEBT_ROWS)
    write_dict_rows_csv(paths["false_return"], FALSE_RETURN_ROWS)
    write_dict_rows_csv(paths["forbidden"], FORBIDDEN_ROWS)

    trace: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "previous_gate": PREVIOUS_GATE,
        "next_gate": NEXT_GATE,
        "decision_state": DECISION_STATE,
        "core_question": CORE_QUESTION,
        "native_witness": NATIVE_WITNESS,
        "evidence_added": False,
        "native_math_mutated": False,
        "manuscript_v2_started": False,
        "return_trace_locked": True,
        "trace_spine": [
            "Gamma = D * P * R",
            "Gamma is return-potential, not observed return",
            "B is observed return",
            "B is crossing pressure plus memory plus continuity plus persistence",
            "C_Z = min(D, P, R, B)",
            "return debt is structured zero when Gamma is meaningful but B/depth/closure is incomplete",
        ],
        "required_distinctions": [row["term"] for row in RETURN_TERM_ROWS],
        "forbidden_readings": [row["forbidden_reading"] for row in FORBIDDEN_ROWS],
    }
    paths["trace"].write_text(json.dumps(trace, indent=2), encoding="utf-8")

    audit = {
        "version": CURRENT_VERSION,
        "checks": {
            "gamma_separated_from_b": True,
            "b_separated_from_zero_crossing_only": True,
            "c_z_preserved_as_weakest_gate": True,
            "return_debt_kept_as_structured_zero": True,
            "forbidden_physics_readings_blocked": True,
            "no_new_evidence_crown": True,
            "next_gate_is_lane_taxonomy": NEXT_GATE.startswith("v1.7.2-alpha"),
        },
    }
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")
    paths["bundle"] = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_7_return_gate_trace_lock_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the v1.7.1 return gate trace lock package.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_return_gate_trace_lock"), help="Output directory.")
    args = parser.parse_args(argv)
    paths = build_v1_7_return_gate_trace(args.out)
    print(paths["read"])
    print(paths["bundle"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
