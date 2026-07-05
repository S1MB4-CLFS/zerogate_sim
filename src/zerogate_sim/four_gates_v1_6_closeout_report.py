from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.28-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CLOSEOUT_DECISION = "expand_v1_6_bounded_controlled_synthetic_claim_earned_for_v1_7"
V1_7_ALLOWED_GATE = "v1.7.0-alpha — Operational Claim Definition"
V2_STATUS = "not_ready_until_v1_7_success"
ZENODO_ACTION = "no_upload_yet"

CLAIM_FOR_V1_7 = (
    "In controlled synthetic adversarial fields, the Four Gates witness operationalizes "
    "a synthetic zero-zone gating principle: it delays premature expression, preserves "
    "earned expression, holds unresolved relation/return debt as structured zero, and "
    "demotes false-one pressure better than raw, binary, dead-safe, and ablated witnesses."
)

BOUNDED_CLOSEOUT_CLAIM = (
    "v1.6 earns a bounded controlled-synthetic claim: the Four Gates witness can preserve "
    "earned expression, hold relation/return debt as structured zero, and demote false-one "
    "pressure in designed synthetic adversarial fields, while simpler witnesses expose failure modes."
)

OUTPUT_FILES = {
    "read": "four_gates_v1_6_closeout_read.md",
    "decision": "four_gates_v1_6_closeout_decision.json",
    "claim_decision": "four_gates_v1_6_claim_decision_register.csv",
    "evidence_table": "four_gates_v1_6_closeout_evidence_table.csv",
    "caveats": "four_gates_v1_6_caveats_and_demotions.csv",
    "v1_7_entry": "four_gates_v1_7_entry_requirements.csv",
    "audit": "four_gates_v1_6_closeout_audit.json",
    "bundle": "four_gates_v1_6_closeout_bundle.zip",
}

EVIDENCE_ROWS = [
    {
        "gate": "triad27 debt evidence",
        "version": "v1.6.20-alpha",
        "decision": "expand_four_gates_triad27_debt_evidence",
        "weather": "triad27 = 3^3 local expression weather",
        "earned_one_visible": 925,
        "relation_debt_visible": 30,
        "return_debt_visible": 63,
        "false_one_pressure_visible": 402,
        "final_false_one_crowns": 0,
        "caveat": "small-weather only; some debt families inactive",
        "closeout_role": "supports the first positive structured-zero gate under small weather",
    },
    {
        "gate": "deep81 / wide243 debt evidence",
        "version": "v1.6.21-alpha",
        "decision": "expand_four_gates_deepwide_debt_evidence",
        "weather": "deep81 + wide243 deeper adversarial weather",
        "earned_one_visible": 11984,
        "relation_debt_visible": 351,
        "return_debt_visible": 660,
        "false_one_pressure_visible": 4980,
        "final_false_one_crowns": 0,
        "caveat": "some debt candidate families inactive; still controlled synthetic evidence",
        "closeout_role": "supports that relation/return debt lanes survive deeper weather",
    },
    {
        "gate": "fresh-seed debt reproduction",
        "version": "v1.6.22-alpha",
        "decision": "expand_four_gates_fresh_seed_debt_reproduction",
        "weather": "fresh seeds 9-17 compared with reference seeds 0-8",
        "earned_one_visible": "deep81 1934; wide243 9798",
        "relation_debt_visible": "deep81 72; wide243 456",
        "return_debt_visible": "deep81 75; wide243 462",
        "false_one_pressure_visible": "deep81 882; wide243 3777",
        "final_false_one_crowns": 0,
        "caveat": "latent overcrown did not reproduce; relation/return debt did",
        "closeout_role": "supports qualitative reproduction of the main Four Gates debt pattern",
    },
    {
        "gate": "anti-tautology audit",
        "version": "v1.6.25-alpha",
        "decision": "witness_bounded_role_shaped_but_witness_computed",
        "weather": "audit over fresh-seed debt evidence",
        "earned_one_visible": "masked numeric pattern visible",
        "relation_debt_visible": "witness-counted and debt-specific",
        "return_debt_visible": "witness-counted and debt-specific",
        "false_one_pressure_visible": "witness-counted",
        "final_false_one_crowns": 0,
        "caveat": "role/profile dependence remains high; not role-blind discovery",
        "closeout_role": "bounds the claim and prevents independent-discovery overclaim",
    },
    {
        "gate": "reproduction package + manuscript correction package",
        "version": "v1.6.26-alpha / v1.6.27-alpha",
        "decision": "packaged_for_closeout",
        "weather": "not new evidence",
        "earned_one_visible": "n/a",
        "relation_debt_visible": "n/a",
        "return_debt_visible": "n/a",
        "false_one_pressure_visible": "n/a",
        "final_false_one_crowns": "n/a",
        "caveat": "packaging and manuscript planning only",
        "closeout_role": "makes the current evidence line reproducible and future-v2-ready, without uploading to Zenodo",
    },
]

CLAIM_DECISION_ROWS = [
    {
        "claim_lane": "bounded_controlled_synthetic_four_gates_witness",
        "closeout_state": "+1 earned_for_v1_7",
        "claim_text": BOUNDED_CLOSEOUT_CLAIM,
        "evidence_basis": "triad27/deep81/wide243 debt evidence, fresh-seed reproduction, ablation wounds, anti-tautology audit",
        "v1_7_status": "allowed_to_operationalize_and_make_externally_auditable",
    },
    {
        "claim_lane": "synthetic_zero_zone_gating_principle",
        "closeout_state": "0 candidate_for_v1_7_not_final_crown",
        "claim_text": CLAIM_FOR_V1_7,
        "evidence_basis": "v1.6 supports the pattern; v1.7 must make the claim cleanly auditable",
        "v1_7_status": "target_claim_for_operational_definition_and_review_package",
    },
    {
        "claim_lane": "independent_role_blind_debt_discovery",
        "closeout_state": "-1 not_earned",
        "claim_text": "Debt states are independently discovered without designed-profile structure.",
        "evidence_basis": "anti-tautology audit reports high role/profile dependence",
        "v1_7_status": "blocked_unless_future_route_explicitly_reopens_and_earns_it",
    },
    {
        "claim_lane": "observed_universe_or_physics_bridge",
        "closeout_state": "-1 deferred_not_claimed",
        "claim_text": "The observed universe or physical dimensional genesis uses the Four Gates witness.",
        "evidence_basis": "none in v1.6; only controlled synthetic evidence exists",
        "v1_7_status": "not_part_of_v1_7_claim_package",
    },
    {
        "claim_lane": "shadow_route",
        "closeout_state": "0 historical_diagnostic_hold",
        "claim_text": "The role-stripped shadow route detected false-one/debt states independently.",
        "evidence_basis": "shadow route failed to beat baselines and remains history vault material",
        "v1_7_status": "do_not_surface_as_active_claim",
    },
]

CAVEAT_ROWS = [
    {
        "caveat": "controlled synthetic domain",
        "status": "active_boundary",
        "plain_language": "The result is about generated synthetic adversarial fields, not physical reality.",
    },
    {
        "caveat": "designed-profile shaped debt candidates",
        "status": "active_boundary",
        "plain_language": "Debt states are intentionally generated near-success structures; they are witness-counted but not independently discovered.",
    },
    {
        "caveat": "latent overcrown did not fresh-seed reproduce",
        "status": "bounded_partial",
        "plain_language": "Relation/return debt reproduced; latent overcrown did not reproduce and must not be overstated.",
    },
    {
        "caveat": "some debt candidate families inactive",
        "status": "bounded_partial",
        "plain_language": "Relation_debt_global and several return-debt families carried the visible debt lanes; not every designed family activated.",
    },
    {
        "caveat": "no physics / cosmology / observed-universe proof",
        "status": "forbidden_overclaim",
        "plain_language": "Mathematical and physics analogies may inspire future work but are not evidence for v1.6.",
    },
    {
        "caveat": "no Zenodo v2 upload yet",
        "status": "deferred",
        "plain_language": "The current Zenodo paper remains a historical first-research-alpha artifact; v2 waits until v1.7 succeeds.",
    },
]

V1_7_ENTRY_ROWS = [
    {
        "gate": "v1.7.0-alpha",
        "role": "Operational Claim Definition",
        "requirement": "Define operationalizes, synthetic, zero-zone, gating, and principle in repo/manuscript terms.",
        "failure_condition": "claim remains poetic or ambiguous",
    },
    {
        "gate": "v1.7.1-alpha",
        "role": "Evidence Package Alignment and Reviewer Path",
        "requirement": "Align README, evidence index, reproduction package, and claim lanes so a reviewer can follow the evidence without chat history.",
        "failure_condition": "reviewer must infer evidence from scattered runs or historical docs",
    },
    {
        "gate": "v1.7.2-alpha",
        "role": "External Small-Run Reproduction Instructions",
        "requirement": "Make small reproduction instructions clear enough for an external user to run and inspect.",
        "failure_condition": "reproduction depends on Marek's local runs or hidden files",
    },
    {
        "gate": "v1.7.3-alpha",
        "role": "Stable External-Review Release Candidate",
        "requirement": "Produce a stable package where the bounded claim, caveats, evidence, and reproduction route all agree.",
        "failure_condition": "claim language exceeds controlled synthetic evidence",
    },
]


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _readme_lines() -> list[str]:
    return [
        "# Four Gates v1.6 Closeout Decision",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Decision:** `{CLOSEOUT_DECISION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "## Closeout verdict",
        "",
        "v1.6 closes as a bounded `+1` for the controlled synthetic-field evidence line.",
        "",
        BOUNDED_CLOSEOUT_CLAIM,
        "",
        "This does not crown broader claims. The role-blind, observed-universe, physics, cosmology, and ontology lanes remain unearned or deferred.",
        "",
        "## Trinary closeout",
        "",
        "```text",
        "+1 earned  — controlled synthetic-field Four Gates witness evidence may enter v1.7 operationalization.",
        " 0 witness — synthetic zero-zone gating principle is the v1.7 claim candidate, not a v1.6 final crown.",
        "-1 resist  — role-blind discovery, shadow-route success, and physics / observed-universe claims are not earned.",
        "```",
        "",
        "## Why the closeout is earned enough for v1.7",
        "",
        "- triad27 debt evidence showed earned-one, relation debt, return debt, and false-one demotion under small weather;",
        "- deep81 / wide243 debt evidence preserved the pattern under deeper weather;",
        "- fresh seeds reproduced the main relation/return debt pattern;",
        "- raw, binary, dead-safe, no-relation, no-return, and average-gate witnesses were wounded;",
        "- the anti-tautology audit bounded the result as designed-profile shaped but witness-counted;",
        "- the reproduction and manuscript correction packages prepared review paths without starting Zenodo or v2 paper work.",
        "",
        "## What remains bounded",
        "",
        "- The result is controlled synthetic-field evidence only.",
        "- Debt states are intentionally generated near-success structures, not independent natural discoveries.",
        "- Latent overcrown did not reproduce on fresh seeds and must not be overstated.",
        "- Some debt candidate families were inactive.",
        "- The current Zenodo manuscript remains the historical first-research-alpha artifact until v1.7 earns a v2 paper route.",
        "",
        "## Next gate",
        "",
        f"`{V1_7_ALLOWED_GATE}`",
        "",
        "v1.7 must make the claim auditable or demote it. It must not inflate v1.6 beyond its controlled synthetic boundary.",
    ]


def build_v1_6_closeout(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(out_dir)
    read_path = out_dir / OUTPUT_FILES["read"]
    decision_path = out_dir / OUTPUT_FILES["decision"]
    claim_decision_path = out_dir / OUTPUT_FILES["claim_decision"]
    evidence_path = out_dir / OUTPUT_FILES["evidence_table"]
    caveat_path = out_dir / OUTPUT_FILES["caveats"]
    v1_7_path = out_dir / OUTPUT_FILES["v1_7_entry"]
    audit_path = out_dir / OUTPUT_FILES["audit"]

    _write_markdown(read_path, _readme_lines())
    write_dict_rows_csv(claim_decision_path, CLAIM_DECISION_ROWS)
    write_dict_rows_csv(evidence_path, EVIDENCE_ROWS)
    write_dict_rows_csv(caveat_path, CAVEAT_ROWS)
    write_dict_rows_csv(v1_7_path, V1_7_ENTRY_ROWS)

    decision: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "decision": CLOSEOUT_DECISION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "bounded_claim": BOUNDED_CLOSEOUT_CLAIM,
        "v1_7_claim_candidate": CLAIM_FOR_V1_7,
        "v1_7_allowed": True,
        "allowed_next_gate": V1_7_ALLOWED_GATE,
        "v2_status": V2_STATUS,
        "zenodo_action_now": ZENODO_ACTION,
        "earned_lanes": [
            "controlled_synthetic_four_gates_witness",
            "earned_one_preservation",
            "relation_debt_visibility",
            "return_debt_visibility",
            "false_one_demotion",
            "ablation_wounds",
            "fresh_seed_qualitative_reproduction",
        ],
        "partial_lanes": [
            "synthetic_zero_zone_gating_principle_claim_candidate_for_v1_7",
            "latent_overcrown_seed_sensitivity",
            "designed_profile_shaped_debt_candidates",
        ],
        "demoted_or_blocked_lanes": [
            "role_blind_discovery",
            "shadow_route_success",
            "observed_universe_bridge",
            "physics_or_cosmology_proof",
            "spacetime_metric_claim",
        ],
        "closeout_state": {
            "+1": "bounded controlled synthetic evidence earned enough for v1.7 operationalization",
            "0": "broader zero-zone gating principle remains a v1.7 audit target",
            "-1": "unearned overclaims remain blocked",
        },
    }
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "version": CURRENT_VERSION,
        "output_files": OUTPUT_FILES,
        "row_counts": {
            "evidence_rows": len(EVIDENCE_ROWS),
            "claim_decision_rows": len(CLAIM_DECISION_ROWS),
            "caveat_rows": len(CAVEAT_ROWS),
            "v1_7_entry_rows": len(V1_7_ENTRY_ROWS),
        },
        "bundle_kind": "four_gates_v1_6_closeout_bundle",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="four_gates_v1_6_closeout_bundle",
    )

    return {
        "read": read_path,
        "decision": decision_path,
        "claim_decision": claim_decision_path,
        "evidence_table": evidence_path,
        "caveats": caveat_path,
        "v1_7_entry": v1_7_path,
        "audit": audit_path,
        "bundle": bundle,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write Four Gates v1.6 closeout decision materials.")
    parser.add_argument("--out", type=Path, default=Path("runs/four_gates_v1_6_closeout"))
    args = parser.parse_args(argv)
    paths = build_v1_6_closeout(args.out)
    print(paths["read"])
    print(paths["bundle"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
