from __future__ import annotations

import argparse
import json
from pathlib import Path

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.10-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = "Can a final trinary witness distinguish earned-one from raw expression pressure, latent overcrown, relation debt, return debt, and false-one pressure under controlled synthetic-field adversarial weather?"
DECISION = "controlled_synthetic_field_answer_earned"
ANSWER_SYMBOL = "+1"
ANSWER_STATUS = "yes_inside_controlled_synthetic_field_adversarial_weather"
NEXT_GATE = "Manuscript v2 upgrade gate — before v1.8"

OUTPUT_FILES = {
    "read": "v1_7_core_question_closeout_read.md",
    "decision": "v1_7_core_question_closeout_decision.json",
    "answer_status": "v1_7_answer_status_card.csv",
    "condition_status": "v1_7_full_answer_conditions.csv",
    "boundary": "v1_7_closeout_claim_boundary.csv",
    "go_no_go": "v1_7_go_no_go_for_manuscript_v2.csv",
    "evidence": "v1_7_closeout_evidence_snapshot.csv",
    "bundle": "v1_7_core_question_closeout_bundle.zip",
}

HOLDOUT_ROWS = [
    {"weather_rung": "triad27", "earned_one": 839, "raw_expression_pressure": 1283, "latent_overcrown": 9, "relation_debt": 39, "return_debt": 75, "false_one_pressure": 321, "final_false_one_crowns": 0, "lane_pattern": "true"},
    {"weather_rung": "deep81", "earned_one": 1950, "raw_expression_pressure": 3012, "latent_overcrown": 9, "relation_debt": 120, "return_debt": 126, "false_one_pressure": 807, "final_false_one_crowns": 0, "lane_pattern": "true"},
    {"weather_rung": "wide243", "earned_one": 9417, "raw_expression_pressure": 14058, "latent_overcrown": 21, "relation_debt": 465, "return_debt": 612, "false_one_pressure": 3543, "final_false_one_crowns": 0, "lane_pattern": "true"},
]

FULL_ANSWER_CONDITIONS = [
    {"condition": "lane_visibility", "status": "pass", "evidence": "+1 earned-one, raw pressure, latent overcrown, relation debt, return debt, and false-one pressure are all visible across the three-rung holdout ladder", "boundary": "lane visibility is controlled synthetic-field evidence, not unknown-field discovery"},
    {"condition": "earned_one_preservation", "status": "pass", "evidence": "earned-one remains visible at 12,206 total across triad27/deep81/wide243", "boundary": "not a dead-safe no-crown witness"},
    {"condition": "false_one_safety", "status": "pass", "evidence": "final false-one crowns remain 0 while false-one pressure reaches 4,671", "boundary": "zero final false crowns are meaningful because pressure is present"},
    {"condition": "structured_zero", "status": "pass", "evidence": "latent overcrown, relation debt, and return debt remain visible as zero-state lanes", "boundary": "structured zero is not binary failure"},
    {"condition": "return_specificity", "status": "pass", "evidence": "return-potential, observed return, return-depth, and return debt were separated in v1.7.1 and v1.7.2 before holdout", "boundary": "no physical gravity or topology claim"},
    {"condition": "baseline_superiority", "status": "pass", "evidence": "baseline and ablation falsifier matrix was locked before perturbation/holdout evidence; dead-safe, raw, binary, average-gate, no-return, and no-zero-hold explanations are blocked by lane requirements", "boundary": "baseline language remains inside repo-defined controlled witnesses"},
    {"condition": "role_dependence_audit", "status": "pass", "evidence": "masked role-dependence and post-holdout anti-tautology checks block label-only, name-leakage, vacuity, and dead-safe readings", "boundary": "does not solve role-blind discovery"},
    {"condition": "fresh_holdout_pressure", "status": "pass", "evidence": "fresh seed block 18-26 and separated triad27/deep81/wide243 rungs preserve the target lane pattern", "boundary": "not independent generator validation"},
    {"condition": "reviewer_path", "status": "pass", "evidence": "v1.7.9 adds reviewer start-here path, reproduction order, expected outputs, evidence manifest, and strict handoff expectations", "boundary": "reviewer package makes closeout auditable; it is not the answer by itself"},
]

BOUNDARY_ROWS = [
    {"lane": "allowed", "claim": "The v1.7 core question is answered +1 inside controlled synthetic-field adversarial weather.", "reason": "all full-answer conditions pass inside the bounded domain"},
    {"lane": "allowed", "claim": "The final trinary witness distinguishes the target lanes in the v1.7 controlled synthetic-field line.", "reason": "earned-one, raw pressure, latent overcrown, relation debt, return debt, false-one pressure, and zero final false crowns remain visible across the ladder"},
    {"lane": "allowed", "claim": "Manuscript v2 may now begin as a bounded correction/upgrade before v1.8.", "reason": "the software question has a closeout state that the old manuscript does not yet reflect"},
    {"lane": "forbidden", "claim": "Role-blind discovery is solved.", "reason": "role-dependence remains bounded and role-stripped discovery waits for a later line"},
    {"lane": "forbidden", "claim": "Independent generator validation is done.", "reason": "v1.8 is the independent synthetic challenge line"},
    {"lane": "forbidden", "claim": "Physics, cosmology, observed-universe, dimensional-origin, quantum, wormhole, or spacetime proof.", "reason": "the evidence remains controlled synthetic-field software evidence"},
    {"lane": "forbidden", "claim": "The original manuscript is already upgraded.", "reason": "manuscript v2 starts after this closeout; it is not created by this code gate"},
]

GO_NO_GO_ROWS = [
    {"target": "manuscript_v2_upgrade", "decision": "go_bounded", "reason": "v1.7 closes +1 inside controlled synthetic-field adversarial weather"},
    {"target": "v1.8_independent_synthetic_challenge", "decision": "hold", "reason": "v1.8 waits until manuscript v2 is drafted or deliberately frozen"},
    {"target": "role_blind_discovery_language", "decision": "resist", "reason": "role-blind route waits for role-stripped feature/holdout line"},
    {"target": "physics_or_cosmology_language", "decision": "resist", "reason": "outside the evidence boundary"},
    {"target": "zenodo_new_version", "decision": "hold", "reason": "archive/upload waits for manuscript v2 and bounded claim language"},
]


def _total(key: str) -> int:
    return sum(int(row[key]) for row in HOLDOUT_ROWS)


def closeout_totals() -> dict[str, int]:
    return {
        "earned_one": _total("earned_one"),
        "raw_expression_pressure": _total("raw_expression_pressure"),
        "latent_overcrown": _total("latent_overcrown"),
        "relation_debt": _total("relation_debt"),
        "return_debt": _total("return_debt"),
        "false_one_pressure": _total("false_one_pressure"),
        "final_false_one_crowns": _total("final_false_one_crowns"),
    }


def answer_status_rows() -> list[dict[str, object]]:
    totals = closeout_totals()
    return [
        {
            "version": CURRENT_VERSION,
            "answer_symbol": ANSWER_SYMBOL,
            "answer_status": ANSWER_STATUS,
            "decision": DECISION,
            "native_witness": NATIVE_WITNESS,
            "earned_one": totals["earned_one"],
            "raw_expression_pressure": totals["raw_expression_pressure"],
            "latent_overcrown": totals["latent_overcrown"],
            "relation_debt": totals["relation_debt"],
            "return_debt": totals["return_debt"],
            "false_one_pressure": totals["false_one_pressure"],
            "final_false_one_crowns": totals["final_false_one_crowns"],
            "core_question_closed": "true",
            "role_blind_discovery_claimed": "false",
            "physics_or_cosmology_claimed": "false",
            "next_gate": NEXT_GATE,
        }
    ]


def _write_read(path: Path) -> None:
    totals = closeout_totals()
    lines = [
        "# v1.7.10-alpha — Core Question Closeout",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        f"**Decision:** `{ANSWER_SYMBOL} {DECISION}`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Answer",
        "",
        "> Yes — inside controlled synthetic-field adversarial weather.",
        "",
        "The final trinary witness distinguishes earned-one from raw expression pressure, latent overcrown, relation debt, return debt, and false-one pressure across the bounded v1.7 evidence line.",
        "",
        "This does not prove role-blind discovery, independent generator transfer, physics, cosmology, observed-universe behavior, dimensional origin, quantum gravity, or trinary reality.",
        "",
        "## Closeout card",
        "",
        "```text",
        f"+1 earned-one total       = {totals['earned_one']}",
        f"raw expression pressure   = {totals['raw_expression_pressure']}",
        f"0 latent overcrown        = {totals['latent_overcrown']}",
        f"0 relation debt           = {totals['relation_debt']}",
        f"0 return debt             = {totals['return_debt']}",
        f"-1 false-one pressure     = {totals['false_one_pressure']}",
        f"final false-one crowns    = {totals['final_false_one_crowns']}",
        "answer                    = +1 bounded controlled synthetic-field answer",
        "```",
        "",
        "## Full-answer conditions",
        "",
        "| condition | status | evidence | boundary |",
        "|---|---|---|---|",
    ]
    for row in FULL_ANSWER_CONDITIONS:
        lines.append(f"| {row['condition']} | {row['status']} | {row['evidence']} | {row['boundary']} |")
    lines.extend([
        "",
        "## Go / no-go",
        "",
        "- **GO:** manuscript v2 as a bounded upgrade/correction before v1.8.",
        "- **HOLD:** v1.8 independent synthetic challenge until manuscript v2 is drafted or deliberately frozen.",
        "- **RESIST:** role-blind discovery, independent generator validation, physics/cosmology/observed-universe claims.",
        "",
        "## Final closeout sentence",
        "",
        "> ZeroGateSim v1.7.10-alpha closes the v1.7 core question as +1 inside controlled synthetic-field adversarial weather: the final trinary witness distinguishes earned-one from raw expression pressure, latent overcrown, relation debt, return debt, and false-one pressure, while preserving earned-one, holding structured zero/debt lanes, demoting false-one pressure, and maintaining zero final false-one crowns.",
        "",
        "## Next movement",
        "",
        f"`{NEXT_GATE}`.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_v1_7_core_question_closeout(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(out_dir)
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}

    _write_read(paths["read"])
    write_dict_rows_csv(paths["answer_status"], answer_status_rows())
    write_dict_rows_csv(paths["condition_status"], FULL_ANSWER_CONDITIONS)
    write_dict_rows_csv(paths["boundary"], BOUNDARY_ROWS)
    write_dict_rows_csv(paths["go_no_go"], GO_NO_GO_ROWS)
    write_dict_rows_csv(paths["evidence"], HOLDOUT_ROWS)

    totals = closeout_totals()
    decision = {
        "version": CURRENT_VERSION,
        "decision": DECISION,
        "answer_symbol": ANSWER_SYMBOL,
        "answer_status": ANSWER_STATUS,
        "core_question": CORE_QUESTION,
        "core_question_closed": True,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "final_false_one_crowns": totals["final_false_one_crowns"],
        "earned_one": totals["earned_one"],
        "raw_expression_pressure": totals["raw_expression_pressure"],
        "latent_overcrown": totals["latent_overcrown"],
        "relation_debt": totals["relation_debt"],
        "return_debt": totals["return_debt"],
        "false_one_pressure": totals["false_one_pressure"],
        "full_answer_conditions_passed": all(row["status"] == "pass" for row in FULL_ANSWER_CONDITIONS),
        "manuscript_v2_go": "go_bounded",
        "v1_8_allowed_now": False,
        "role_blind_discovery_claimed": False,
        "independent_generator_validation_claimed": False,
        "physics_or_cosmology_claimed": False,
        "manuscript_v2_started": False,
        "next_gate": NEXT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2), encoding="utf-8")
    write_evidence_bundle(out_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="v1_7_core_question_closeout_bundle")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the v1.7.10 core question closeout report.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_10_core_question_closeout"))
    args = parser.parse_args(argv)
    paths = build_v1_7_core_question_closeout(args.out)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
