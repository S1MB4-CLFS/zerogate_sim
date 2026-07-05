from __future__ import annotations

import argparse
import json
from pathlib import Path

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.18-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
FRAMEWORK_NAME = "Four Gates of Becoming"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

OUTPUT_FILES = {
    "read": "four_gates_debt_candidate_design_read.md",
    "decision": "four_gates_debt_candidate_design_decision.json",
    "candidate_families": "four_gates_debt_candidate_families.csv",
    "diagnostics": "four_gates_debt_diagnostics.csv",
    "claim_lanes": "four_gates_claim_lanes.csv",
    "route": "four_gates_debt_route.csv",
    "forbidden_claims": "four_gates_forbidden_claims.csv",
    "audit": "four_gates_debt_candidate_design_audit.json",
    "bundle": "four_gates_debt_candidate_design_bundle.zip",
}


def build_candidate_family_rows() -> list[dict[str, object]]:
    return [
        {
            "family": "earned_return_control",
            "candidate_shape": "D/P/R strong; return preserves coherent identity across witness pressure.",
            "expected_primary_state": "+1 earned-one",
            "must_not_be": "dead-safe hold or false demotion",
            "diagnostic_focus": "return memory preserved; closure gap low; final crown earned",
            "next_test_role": "positive control for earned-one preservation",
        },
        {
            "family": "false_one_trap_control",
            "candidate_shape": "local raw expression appears strong but relation or return is borrowed, unstable, or trap-shaped.",
            "expected_primary_state": "-1 false-one demotion",
            "must_not_be": "final +1 crown",
            "diagnostic_focus": "false pressure exposed; raw/binary baselines should overcrown",
            "next_test_role": "negative control for demotion and ablation wounds",
        },
        {
            "family": "relation_debt_local",
            "candidate_shape": "D and P are strong; relation is near-threshold, unstable, borrowed, or not yet owned.",
            "expected_primary_state": "0 relation debt",
            "must_not_be": "+1 earned-one or -1 trap demotion",
            "diagnostic_focus": "relation ownership gap; relation stability gap; near-incidence without crown",
            "next_test_role": "make relation debt visible as structured zero",
        },
        {
            "family": "return_debt_local",
            "candidate_shape": "D/P/R are meaningful; return begins but comes back altered, weak, or memory-incomplete.",
            "expected_primary_state": "0 return debt",
            "must_not_be": "+1 earned-one or -1 trap demotion",
            "diagnostic_focus": "return memory gap; dual-return gap; closure gap; perturbation survival gap",
            "next_test_role": "make return debt visible as structured zero",
        },
        {
            "family": "relation_debt_global",
            "candidate_shape": "local components are incomplete or misleading alone, but paired/global relation is structured enough to hold.",
            "expected_primary_state": "0 relation debt",
            "must_not_be": "local +1 crown or local -1 garbage demotion",
            "diagnostic_focus": "factorization gap; global relation strength; local incompleteness gap",
            "next_test_role": "test whether relation can be global without being crownable locally",
        },
        {
            "family": "closure_gap_candidate",
            "candidate_shape": "candidate survives first witness frame but double-witness / closure does not return the same structure.",
            "expected_primary_state": "0 return debt",
            "must_not_be": "automatic demotion or premature crown",
            "diagnostic_focus": "closure gap between raw expression and returned/closed expression",
            "next_test_role": "test return as closure rather than simple coming-back",
        },
        {
            "family": "perturbation_survival_candidate",
            "candidate_shape": "candidate remains meaningful after perturbation but loses enough coherence to require hold.",
            "expected_primary_state": "0 return debt or 0 latent overcrown",
            "must_not_be": "false-one demotion when structure survives partially",
            "diagnostic_focus": "perturbation survival gap; before/after coherence memory",
            "next_test_role": "stress zero-hold under late shock without collapsing to falsehood",
        },
    ]


def build_diagnostic_rows() -> list[dict[str, object]]:
    return [
        {
            "diagnostic": "relation_ownership_gap",
            "meaning": "Difference between owned relation and borrowed/ambient relation.",
            "debt_signal": "middle gap: relation meaningful but not owned enough to crown",
            "primary_lane": "0 relation debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "relation_stability_gap",
            "meaning": "Relation appears in a window but does not endure across witness windows.",
            "debt_signal": "unstable relation that should be held rather than crowned or killed",
            "primary_lane": "0 relation debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "factorization_gap",
            "meaning": "Paired/global structure is not reducible to local component scores alone.",
            "debt_signal": "global relation exists while local parts remain incomplete",
            "primary_lane": "0 relation debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "return_memory_gap",
            "meaning": "How much coherent structure is lost or altered when expression returns through zero.",
            "debt_signal": "changed-but-meaningful return, not collapse",
            "primary_lane": "0 return debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "dual_return_gap",
            "meaning": "Gap between raw expression and its returned form after complementary / dual witness pressure.",
            "debt_signal": "return is incomplete but non-random",
            "primary_lane": "0 return debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "closure_gap",
            "meaning": "Gap between candidate and its double-witness / closure repair form.",
            "debt_signal": "candidate needs closure-hold before final crown",
            "primary_lane": "0 return debt",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "perturbation_survival_gap",
            "meaning": "Difference between pre-shock and post-shock coherent identity.",
            "debt_signal": "structure survives partly; zero should hold instead of demote",
            "primary_lane": "0 return debt / 0 latent overcrown",
            "implementation_status": "design_next",
        },
        {
            "diagnostic": "zero_hold_eligibility",
            "meaning": "Candidate is structured enough not to demote, incomplete enough not to crown.",
            "debt_signal": "the missing middle state becomes measurable",
            "primary_lane": "0 relation debt / 0 return debt",
            "implementation_status": "design_next",
        },
    ]


def build_claim_lane_rows() -> list[dict[str, object]]:
    return [
        {
            "lane": "formal_computational",
            "allowed_use": "Implemented simulator behavior, candidate families, metrics, ablations, and controlled synthetic-field results.",
            "claim_status": "active",
            "boundary": "Must be tested in repo evidence before public crown.",
        },
        {
            "lane": "mathematical_analogy",
            "allowed_use": "Projective polarity, functional duality, bipolar/biconjugate return, Hilbert/bidual return as design analogies.",
            "claim_status": "analogy_allowed",
            "boundary": "Inspires diagnostics; does not prove ZeroGateSim or physical reality.",
        },
        {
            "lane": "physics_topology_hold",
            "allowed_use": "Quantum measurement, entanglement, ER/EPR, high-dimensional topology as analogy pressure only.",
            "claim_status": "hold",
            "boundary": "May not become evidence for ZeroGateSim without separate external work.",
        },
        {
            "lane": "forbidden_claims",
            "allowed_use": "None.",
            "claim_status": "resist",
            "boundary": "No spacetime metric claim, no wormhole proof, no universe proof, no ZeroGate gravity claim.",
        },
    ]


def build_forbidden_claim_rows() -> list[dict[str, object]]:
    return [
        {
            "forbidden_claim": "ZeroGateSim proves physical dimensional genesis.",
            "reason": "The evidence is controlled synthetic-field software evidence, not observational physics.",
            "replacement": "ZeroGateSim tests a computational witness grammar inside controlled synthetic fields.",
        },
        {
            "forbidden_claim": "The universe uses the Four Gates of Becoming.",
            "reason": "This is an ontological claim not earned by toy/synthetic runs.",
            "replacement": "The Four Gates of Becoming are a testable modeling grammar.",
        },
        {
            "forbidden_claim": "Projective geometry, functional analysis, or quantum mechanics proves ZeroGateSim.",
            "reason": "Those structures provide analogies and candidate-design pressure, not validation.",
            "replacement": "Mathematical analogies motivate debt diagnostics that must be tested.",
        },
        {
            "forbidden_claim": "ER=EPR, wormholes, or high-dimensional topology establish the return gate.",
            "reason": "These are physics/topology HOLD analogies and not active evidence lanes.",
            "replacement": "Use them only to inspire global-relation and closure-gap synthetic candidates.",
        },
        {
            "forbidden_claim": "A spacetime metric or field equation has been derived for the four gates.",
            "reason": "No dimensional analysis, derivation, or physical validation exists in this repo.",
            "replacement": "No metric before measurement; no field equation before evidence.",
        },
    ]


def build_route_rows() -> list[dict[str, object]]:
    return [
        {
            "version": "v1.6.18-alpha",
            "gate": "Four Gates logic cleanup and debt candidate design",
            "pass_condition": "debt candidates and boundaries are defined before generation",
            "stop_condition": "active route confuses analogy with evidence or leaves debt undefined",
        },
        {
            "version": "v1.6.19-alpha",
            "gate": "debt candidate generator",
            "pass_condition": "near-success debt candidates can be generated without changing native C_Z",
            "stop_condition": "candidates are only traps wearing new labels",
        },
        {
            "version": "v1.6.20-alpha",
            "gate": "four-corpus triad27 debt evidence",
            "pass_condition": "earned-one, false-one demotion, latent overcrown, relation debt, return debt, and ablation wounds are visible",
            "stop_condition": "relation debt and return debt remain zero; demote full debt claim",
        },
        {
            "version": "v1.6.21-alpha",
            "gate": "deep81 / wide243 debt evidence",
            "pass_condition": "debt lanes survive perturbation and temporal-depth weather",
            "stop_condition": "debt lanes vanish or native witness regresses",
        },
        {
            "version": "v1.6.22-alpha",
            "gate": "fresh-seed debt reproduction",
            "pass_condition": "same qualitative pattern appears under fresh seeds",
            "stop_condition": "pattern is seed-specific or unstable",
        },
        {
            "version": "v1.6.23-alpha",
            "gate": "evidence consolidation and runs hygiene",
            "pass_condition": "canonical evidence index and local cleanup classification exist",
            "stop_condition": "cleanup risks deleting evidence or hiding failures",
        },
        {
            "version": "v1.6.24-alpha",
            "gate": "manuscript / README correction package planning",
            "pass_condition": "evidence, claim boundary, and correction plan are coherent",
            "stop_condition": "Zenodo/paper route starts before evidence closeout",
        },
    ]


def _write_read(path: Path) -> None:
    lines = [
        "# Four Gates of Becoming — Debt Candidate Design",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** design gate; no heavy evidence run; no Zenodo route",
        "**Native witness:** `C_Z = min(D, P, R, B)`",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Why this version exists",
        "",
        "The repaired native evidence is strong for earned-one preservation and false-one demotion, but relation debt and return debt remain absent or only partially visible. That means the next useful step is not larger weather. It is defining debt-shaped candidates: near-success states that deserve zero-hold rather than +1 crown or -1 demotion.",
        "",
        "## Four gates, cleaned",
        "",
        "- **Distinction** — something becomes separable from background.",
        "- **Polarity** — distinction gains complementary / opposed orientation around zero.",
        "- **Relation** — polarity binds into structure rather than split or drift.",
        "- **Return** — relation is forced through witness / perturbation / closure and what comes back is judged.",
        "",
        "Return is not merely coming back. Return asks what witness-return did to the candidate.",
        "",
        "```text",
        "+1 earned-one: returns with preserved coherent identity",
        " 0 relation/return debt: returns changed but meaningful, or relation is meaningful but incomplete",
        "-1 false-one pressure: return exposes borrowed, unstable, incoherent, or trap-like expression",
        "```",
        "",
        "## Candidate families",
        "",
        "| family | expected state | shape | diagnostic focus |",
        "|---|---|---|---|",
    ]
    for row in build_candidate_family_rows():
        lines.append(f"| {row['family']} | {row['expected_primary_state']} | {row['candidate_shape']} | {row['diagnostic_focus']} |")
    lines.extend([
        "",
        "## Diagnostic families",
        "",
        "| diagnostic | lane | meaning | debt signal |",
        "|---|---|---|---|",
    ])
    for row in build_diagnostic_rows():
        lines.append(f"| {row['diagnostic']} | {row['primary_lane']} | {row['meaning']} | {row['debt_signal']} |")
    lines.extend([
        "",
        "## Claim boundary",
        "",
        "The Four Gates of Becoming are the active computational grammar. Mathematical and physics/topology material may inspire candidate design, but they are not evidence that physical reality uses ZeroGateSim.",
        "",
        "Forbidden shortcuts:",
        "",
        "- no spacetime metric claim;",
        "- no wormhole proof;",
        "- no universe proof;",
        "",
    ])
    for row in build_forbidden_claim_rows():
        lines.append(f"- **Do not claim:** {row['forbidden_claim']}  ")
        lines.append(f"  **Use instead:** {row['replacement']}")
    lines.extend([
        "",
        "## Next gate",
        "",
        "`v1.6.19-alpha` should implement the debt candidate generator. It must not change `C_Z = min(D, P, R, B)`. It must create near-success candidates, not traps wearing debt masks.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_debt_candidate_design_report(*, output_dir: Path) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    read_md = output_dir / OUTPUT_FILES["read"]
    decision_json = output_dir / OUTPUT_FILES["decision"]
    families_csv = output_dir / OUTPUT_FILES["candidate_families"]
    diagnostics_csv = output_dir / OUTPUT_FILES["diagnostics"]
    claim_lanes_csv = output_dir / OUTPUT_FILES["claim_lanes"]
    route_csv = output_dir / OUTPUT_FILES["route"]
    forbidden_csv = output_dir / OUTPUT_FILES["forbidden_claims"]
    audit_json = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(families_csv, build_candidate_family_rows())
    write_dict_rows_csv(diagnostics_csv, build_diagnostic_rows())
    write_dict_rows_csv(claim_lanes_csv, build_claim_lane_rows())
    write_dict_rows_csv(route_csv, build_route_rows())
    write_dict_rows_csv(forbidden_csv, build_forbidden_claim_rows())
    _write_read(read_md)

    decision = {
        "version": CURRENT_VERSION,
        "global_decision": "hold_debt_candidate_design_ready_for_generator_implementation",
        "framework_name": FRAMEWORK_NAME,
        "native_witness_unchanged": NATIVE_WITNESS,
        "debt_candidate_families": [row["family"] for row in build_candidate_family_rows()],
        "relation_debt_defined": True,
        "return_debt_defined": True,
        "physics_topology_analogy_hold": True,
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "spacetime_metric_claim_allowed": False,
        "next_gate": "v1.6.19-alpha debt candidate generator",
    }
    decision_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "output_files": OUTPUT_FILES,
        "candidate_family_count": len(build_candidate_family_rows()),
        "diagnostic_count": len(build_diagnostic_rows()),
        "claim_lane_count": len(build_claim_lane_rows()),
        "forbidden_claim_count": len(build_forbidden_claim_rows()),
        "native_witness_mutated": False,
        "uses_dqrt_label": False,
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(output_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="zerogate_four_gates_debt_candidate_design_bundle")
    return {
        "read": read_md,
        "decision": decision_json,
        "candidate_families": families_csv,
        "diagnostics": diagnostics_csv,
        "claim_lanes": claim_lanes_csv,
        "route": route_csv,
        "forbidden_claims": forbidden_csv,
        "audit": audit_json,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write the Four Gates of Becoming debt candidate design report.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_four_gates_debt_candidate_design_report(output_dir=args.out)
    print(f"[four-gates-debt-design] wrote {paths['read']}")
    print(f"[four-gates-debt-design] bundle {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
