from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.27-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
NEXT_GATE = "v1.6.28-alpha — v1.6 Closeout Decision"
V2_STATUS = "not_ready_until_v1_7_success"
ZENODO_ACTION = "no_upload_yet_prepare_new_version_later"
CLAIM_CANDIDATE = (
    "In controlled synthetic adversarial fields, the Four Gates witness operationalizes "
    "a synthetic zero-zone gating principle: it delays premature expression, preserves "
    "earned expression, holds unresolved relation/return debt as structured zero, and "
    "demotes false-one pressure better than raw, binary, dead-safe, and ablated witnesses."
)

OUTPUT_FILES = {
    "read": "four_gates_manuscript_correction_package_read.md",
    "decision": "four_gates_manuscript_correction_package_decision.json",
    "outline": "four_gates_v2_manuscript_outline.md",
    "patch_map": "four_gates_manuscript_patch_map.csv",
    "claim_lanes": "four_gates_claim_lane_register.csv",
    "evidence_table": "four_gates_canonical_evidence_table.csv",
    "zenodo_plan": "four_gates_zenodo_new_version_plan.md",
    "audit": "four_gates_manuscript_correction_package_audit.json",
    "bundle": "four_gates_manuscript_correction_package_bundle.zip",
}

CANONICAL_EVIDENCE_ROWS = [
    {
        "gate": "triad27 debt evidence",
        "version": "v1.6.20-alpha",
        "decision": "expand_four_gates_triad27_debt_evidence",
        "canonical_folder": "runs/four_gates_triad27_debt_v1_6_20/four_gates_triad27_debt_evidence",
        "what_it_supports": "small-weather Four Gates debt-state visibility and native false-one demotion",
        "caveat": "small-weather only",
    },
    {
        "gate": "deep81 / wide243 debt evidence",
        "version": "v1.6.21-alpha",
        "decision": "expand_four_gates_deepwide_debt_evidence",
        "canonical_folder": "runs/four_gates_deepwide_debt_v1_6_21/four_gates_deepwide_debt_evidence",
        "what_it_supports": "deeper-weather relation/return debt visibility with earned-one preservation and zero final false crowns",
        "caveat": "some debt candidate families inactive",
    },
    {
        "gate": "fresh-seed debt reproduction",
        "version": "v1.6.22-alpha",
        "decision": "expand_four_gates_fresh_seed_debt_reproduction",
        "canonical_folder": "runs/four_gates_fresh_seed_reproduction_v1_6_22",
        "what_it_supports": "qualitative reproduction on fresh seeds 9-17",
        "caveat": "latent overcrown did not reproduce; relation/return debt did",
    },
    {
        "gate": "anti-tautology audit",
        "version": "v1.6.25-alpha",
        "decision": "witness_bounded_role_shaped_but_witness_computed",
        "canonical_folder": "runs/four_gates_anti_tautology_audit_v1_6_25",
        "what_it_supports": "debt states are witness-counted and numerically visible while remaining designed-profile shaped",
        "caveat": "not independent role-blind discovery",
    },
    {
        "gate": "reproduction command package",
        "version": "v1.6.26-alpha",
        "decision": "expand_reproduction_command_package_ready_for_manuscript_correction",
        "canonical_folder": "runs/four_gates_reproduction_command_package_v1_6_26",
        "what_it_supports": "small smoke and heavy reference/fresh reproduction commands are packaged for later review",
        "caveat": "adds no new science claim",
    },
]

CLAIM_LANE_ROWS = [
    {
        "lane": "simulation_supported",
        "claim": CLAIM_CANDIDATE,
        "status_for_v2_draft": "candidate_after_v1_6_closeout_and_v1_7_success",
        "required_language": "controlled synthetic adversarial fields; designed-profile shaped but witness-counted",
        "forbidden_upgrade": "independent discovery or observed-universe proof",
    },
    {
        "lane": "historical_first_alpha",
        "claim": "The current Zenodo manuscript is a good first-research-alpha artifact focused on raw expression versus earned-one and false-one demotion.",
        "status_for_v2_draft": "preserve_as_historical_artifact",
        "required_language": "three pre-return adversarial corpora plus return as measured gate / witness requirement",
        "forbidden_upgrade": "pretending first-alpha already had four dedicated adversarial corpora",
    },
    {
        "lane": "mathematical_analogy",
        "claim": "Projective polarity, functional duality, closure, and measurement/update analogies may explain why relation and return debt are meaningful zero states.",
        "status_for_v2_draft": "optional_context_not_evidence",
        "required_language": "analogy; design inspiration; not proof",
        "forbidden_upgrade": "claiming known mathematics proves ZeroGateSim ontology",
    },
    {
        "lane": "physics_topology_hold",
        "claim": "Quantum, topology, ER=EPR, and observed-universe comparisons remain future analogy / bridge work only.",
        "status_for_v2_draft": "defer_or_hold",
        "required_language": "not part of v1.6 evidence claim",
        "forbidden_upgrade": "spacetime metric, wormhole, quantum gravity, or cosmology proof",
    },
    {
        "lane": "role_blind_shadow",
        "claim": "The v1.6 shadow route was useful historical diagnostic work but did not earn role-blind discovery.",
        "status_for_v2_draft": "history_vault_only_unless_needed_as_negative_control_story",
        "required_language": "historical diagnostic HOLD",
        "forbidden_upgrade": "role-blind detector claim",
    },
]

PATCH_MAP_ROWS = [
    {
        "current_manuscript_area": "title / abstract / front proof card",
        "current_status": "first-research-alpha proof posture with 13,122 runs, three adversarial corpora, 0 final false-one crowns",
        "v2_action": "keep the first-alpha result as historical source and add a new later-evidence posture only after v1.7 succeeds",
        "reason": "the uploaded paper is good as first-alpha, but newer repo evidence shifted from false-one refusal to full +1/0/-1 debt-state evidence",
    },
    {
        "current_manuscript_area": "claim boundary",
        "current_status": "already strong: not cosmology, not physical dimensional genesis, not trinary reality",
        "v2_action": "preserve the red boundary, update supported claim to controlled synthetic-field Four Gates witness only if closeout earns it",
        "reason": "the old boundary is one of the paper's best features and should not be weakened",
    },
    {
        "current_manuscript_area": "adversarial corpora / proof harness",
        "current_status": "three corpora: distinction, polarity, relation; return present as gate and witness requirement",
        "v2_action": "add repaired four-corpus and debt-candidate evidence section; explain the three-corpus / four-gate distinction; do not rewrite history",
        "reason": "the v1.6 repair added dedicated return and debt evidence without pretending it existed in first-alpha",
    },
    {
        "current_manuscript_area": "zero-state discussion",
        "current_status": "zero is active, mostly via latent overcrown and refusal to crown false-one pressure",
        "v2_action": "add relation debt and return debt as structured-zero evidence lanes with fresh-seed caveat",
        "reason": "the newer evidence finally makes the 0-state positive rather than just not-crowned",
    },
    {
        "current_manuscript_area": "figures",
        "current_status": "first-alpha proof card, trinary witness stack, three-corpus proof harness visual",
        "v2_action": "replace or supplement with current Four Gates evidence cards and corrected four-corpus/debt-route visual set",
        "reason": "README current surface now uses current evidence cards while legacy visuals belong in history vault",
    },
    {
        "current_manuscript_area": "limitations",
        "current_status": "toy-field domain, designed roles, metric dependence, no external validation, bounded literature integration",
        "v2_action": "keep all current limitations and add role-shaped/witness-counted anti-tautology boundary",
        "reason": "v1.6.25 shows the result is controlled synthetic evidence, not independent discovery",
    },
    {
        "current_manuscript_area": "conclusion",
        "current_status": "raw expression is pressure; earned-one is final +1; 0 final false crowns",
        "v2_action": "preserve this as first-alpha conclusion and add new conclusion only after v1.7 if earned",
        "reason": "the old paper remains very good; v2 should be additive and corrective, not an embarrassed overwrite",
    },
]


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _outline_text() -> str:
    lines = [
        "# Zero-Gate Dimensional Genesis v2 Manuscript Outline Candidate",
        "",
        f"**Prepared by:** `{CURRENT_VERSION}`",
        "**Status:** planning package only; not a full v2 manuscript.",
        "",
        "## Editorial stance",
        "",
        "The first Zenodo manuscript should remain a historical first-research-alpha artifact. It is good and should not be treated as an error to erase.",
        "",
        "A future v2 manuscript should be additive and corrective:",
        "",
        "- keep the original conceptual spine;",
        "- preserve the original proof as first-alpha history;",
        "- explain the three-corpus / four-gate distinction honestly;",
        "- add repaired Four Gates debt evidence only after v1.7 succeeds;",
        "- keep all physical / observed-universe claims out of the supported evidence lane.",
        "",
        "## Candidate v2 structure",
        "",
        "1. Orientation and lineage: original seeing -> first-alpha proof -> repaired Four Gates debt evidence.",
        "2. Claim boundary: controlled synthetic-field witness model, not cosmology or physical proof.",
        "3. Four Gates of Becoming: distinction, polarity, relation, return.",
        "4. Raw expression versus earned-one: preserve the original repair.",
        "5. Structured zero: latent, relation debt, return debt, not-yet pressure.",
        "6. Native witness: `C_Z = min(D, P, R, B)` and final trinary output.",
        "7. Historical first-alpha proof record: three pre-return adversarial corpora and fresh-seed reproduction.",
        "8. Repaired evidence route: four-corpus controls, debt candidates, triad27/deep81/wide243, fresh seeds.",
        "9. Ablation baselines: raw, binary, dead-safe, no-relation, no-return, average-gate enemies.",
        "10. Anti-tautology audit: designed-profile shaped but witness-counted; no role-blind discovery claim.",
        "11. Limitations: synthetic field, designed candidates, metric dependence, no external empirical validation.",
        "12. Mathematical analogy appendix: projective / functional / measurement analogies as interpretation only.",
        "13. Future work: external reproduction, effective dimension comparisons, literature deepening, DOI plan.",
        "",
        "## Required before writing full v2",
        "",
        "- v1.6 closeout decision is complete.",
        "- v1.7 operational claim package succeeds.",
        "- canonical evidence and reproduction commands are inspectable from a clean repo.",
        "- no active text implies role-blind discovery, physics proof, or observed-universe proof.",
    ]
    return "\n".join(lines) + "\n"


def _zenodo_plan_text() -> str:
    lines = [
        "# Zenodo New-Version Plan — Hold Until v1.7 Success",
        "",
        f"**Prepared by:** `{CURRENT_VERSION}`",
        "**Action now:** no Zenodo upload, no metadata change required by this version.",
        "",
        "## Intended later route",
        "",
        "When the repo is ready, create a new version of the existing Zenodo record rather than editing the historical first-alpha paper into something it was not.",
        "",
        "The current Zenodo manuscript remains the historical first-research-alpha artifact. A future v2 paper should become the main readable version only after it earns that role.",
        "",
        "## What the future version must include",
        "",
        "- corrected claim boundary;",
        "- four-corpus / debt-state evidence summary;",
        "- fresh-seed reproduction summary;",
        "- anti-tautology boundary: designed-profile shaped but witness-counted;",
        "- reproduction command package reference;",
        "- limitations and deferred observed-universe bridge;",
        "- explicit statement that the old paper remains historical first-alpha source material.",
        "",
        "## What it must not include",
        "",
        "- claim that physical dimensional genesis is proven;",
        "- claim that reality is trinary;",
        "- claim that role-blind discovery is solved;",
        "- claim that physics/topology analogies prove ZeroGateSim;",
        "- hidden rewriting of the first-alpha proof record.",
    ]
    return "\n".join(lines) + "\n"


def _readme_text() -> str:
    lines = [
        "# Four Gates Manuscript Correction Package",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "**Status:** correction package only; not the full v2 manuscript.",
        "",
        "## Decision",
        "",
        "The package is ready for v1.6 closeout, not for Zenodo upload.",
        "",
        "The first manuscript remains a valuable historical first-research-alpha paper. It does not need to be erased. A later v2 paper should preserve that lineage while adding repaired Four Gates debt evidence if v1.7 earns the operational claim package.",
        "",
        "## Core correction",
        "",
        "The original paper already makes a strong boundary: generated toy fields, not cosmology or physical proof. The correction package keeps that strength and updates what later evidence added:",
        "",
        "- first-alpha proof: three pre-return adversarial corpora plus return as measured gate / witness requirement;",
        "- current repaired route: distinction, polarity, relation, return controls plus debt-shaped candidates;",
        "- current evidence: relation debt and return debt visible as structured zero under controlled synthetic weather;",
        "- audit boundary: designed-profile shaped but witness-counted, not independent role-blind discovery.",
        "",
        "## Supported manuscript direction",
        "",
        f"> {CLAIM_CANDIDATE}",
        "",
        "This sentence remains a candidate until v1.6 closeout and v1.7 operational packaging complete.",
        "",
        "## Package contents",
        "",
        "- `four_gates_v2_manuscript_outline.md` — future v2 structure candidate.",
        "- `four_gates_manuscript_patch_map.csv` — section-by-section correction map for the current manuscript.",
        "- `four_gates_claim_lane_register.csv` — simulation support / historical / mathematical analogy / physics HOLD lanes.",
        "- `four_gates_canonical_evidence_table.csv` — evidence gates needed for the future manuscript.",
        "- `four_gates_zenodo_new_version_plan.md` — no-upload plan for later Zenodo new-version work.",
        "",
        "## Boundary",
        "",
        "No Zenodo route starts here. No full v2 paper is generated here. No observed-universe bridge is claimed here.",
    ]
    return "\n".join(lines) + "\n"


def build_manuscript_correction_package(out_dir: Path) -> dict[str, Path]:
    out_dir = ensure_dir(Path(out_dir))
    read_path = out_dir / OUTPUT_FILES["read"]
    decision_path = out_dir / OUTPUT_FILES["decision"]
    outline_path = out_dir / OUTPUT_FILES["outline"]
    patch_map_path = out_dir / OUTPUT_FILES["patch_map"]
    claim_lanes_path = out_dir / OUTPUT_FILES["claim_lanes"]
    evidence_table_path = out_dir / OUTPUT_FILES["evidence_table"]
    zenodo_plan_path = out_dir / OUTPUT_FILES["zenodo_plan"]
    audit_path = out_dir / OUTPUT_FILES["audit"]

    _write_markdown(read_path, _readme_text().splitlines())
    outline_path.write_text(_outline_text(), encoding="utf-8")
    zenodo_plan_path.write_text(_zenodo_plan_text(), encoding="utf-8")
    write_dict_rows_csv(patch_map_path, PATCH_MAP_ROWS)
    write_dict_rows_csv(claim_lanes_path, CLAIM_LANE_ROWS)
    write_dict_rows_csv(evidence_table_path, CANONICAL_EVIDENCE_ROWS)

    decision = {
        "version": CURRENT_VERSION,
        "decision": "expand_manuscript_correction_package_ready_for_closeout",
        "native_witness_unchanged": NATIVE_WITNESS,
        "next_gate": NEXT_GATE,
        "zenodo_action_now": ZENODO_ACTION,
        "v2_status": V2_STATUS,
        "old_manuscript_status": "preserve_as_historical_first_research_alpha_artifact",
        "full_v2_paper_ready": False,
        "requires_v1_7_success_for_v2": True,
        "claim_candidate": CLAIM_CANDIDATE,
        "forbidden_claims": [
            "physical dimensional genesis proven",
            "cosmology proven",
            "reality itself proven trinary",
            "role-blind discovery solved",
            "physics/topology analogy proves ZeroGateSim",
        ],
        "allowed_next_gate": NEXT_GATE,
    }
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "version": CURRENT_VERSION,
        "output_files": OUTPUT_FILES,
        "canonical_evidence_rows": len(CANONICAL_EVIDENCE_ROWS),
        "claim_lane_rows": len(CLAIM_LANE_ROWS),
        "patch_map_rows": len(PATCH_MAP_ROWS),
        "includes_zenodo_plan": True,
        "zenodo_upload_allowed_now": False,
        "native_witness_unchanged": NATIVE_WITNESS,
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle_path = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="four_gates_manuscript_correction_package",
    )
    return {
        "read": read_path,
        "decision": decision_path,
        "outline": outline_path,
        "patch_map": patch_map_path,
        "claim_lanes": claim_lanes_path,
        "evidence_table": evidence_table_path,
        "zenodo_plan": zenodo_plan_path,
        "audit": audit_path,
        "bundle": bundle_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Four Gates manuscript correction package.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for correction package files.")
    args = parser.parse_args(argv)
    paths = build_manuscript_correction_package(args.out)
    print(paths["read"])
    print(paths["bundle"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
