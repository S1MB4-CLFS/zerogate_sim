from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.8-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
DECISION = "repo_cleanup_cohesion_check_locked_not_closeout"
GATE_KIND = "front_page_repo_cohesion_check_not_reviewer_package"
NEXT_GATE = "v1.7.9-alpha — Reviewer Start Here / Reproduction Package"
CLOSEOUT_GATE = "v1.7.10-alpha — Core Question Closeout"

OUTPUT_FILES = {
    "read": "v1_7_repo_cleanup_cohesion_check_read.md",
    "decision": "v1_7_repo_cleanup_cohesion_check_decision.json",
    "front_page": "v1_7_front_page_routes.csv",
    "cohesion": "v1_7_repo_cohesion_checks.csv",
    "evidence": "v1_7_current_holdout_snapshot.csv",
    "release_shift": "v1_7_release_shift.csv",
    "bundle": "v1_7_repo_cleanup_cohesion_check_bundle.zip",
}

FRONT_PAGE_ROUTES = [
    {
        "route": "current_evidence_state",
        "readme_label": "Current evidence state",
        "target": "docs/current_evidence_state.md",
        "reason": "keeps the README readable while preserving the detailed evidence ledger",
    },
    {
        "route": "latest_holdout_snapshot",
        "readme_label": "Latest v1.7 holdout snapshot",
        "target": "docs/v1_7_latest_holdout_snapshot.md",
        "reason": "puts the 27/81/243 result on the front page as visual cards without pretending it is a packaged reproduction bundle",
    },
    {
        "route": "anti_tautology_path",
        "readme_label": "Anti-tautology / role-dependence path",
        "target": "docs/v1_7_anti_tautology_role_dependence_check.md",
        "reason": "makes the post-holdout audit inspectable before reviewer packaging",
    },
    {
        "route": "known_routine",
        "readme_label": "Known audit routine",
        "target": "docs/v1_7_anti_tautology_known_routine.md",
        "reason": "shows the standard sanity-check pattern: pre-registration, holdout, controls, leakage checks, baselines, and bounded claims",
    },
    {
        "route": "recent_native_history",
        "readme_label": "Recent native evidence history",
        "target": "docs/recent_native_evidence_history.md",
        "reason": "moves the long version list out of the README while preserving traceability",
    },
    {
        "route": "version_truth",
        "readme_label": "Version truth",
        "target": "docs/version_truth.md",
        "reason": "keeps release spine and version notes out of the front page body",
    },
    {
        "route": "repo_cohesion_check",
        "readme_label": "Repo cleanup / cohesion check",
        "target": "docs/v1_7_repo_cleanup_cohesion_check.md",
        "reason": "documents why v1.7.8 exists before reviewer packaging",
    },
]

COHESION_CHECKS = [
    {
        "check": "readme_front_page_math_and_visual_cards_preserved",
        "pass_signal": "README carries math witness, visual holdout cards, top-card links, and a compact holdout snapshot, not the full evidence ledger",
        "failure_signal": "README strips the math witness, replaces the latest evidence cards with spreadsheet posture, or becomes a wall of version notes",
        "claim_boundary": "readability repair, not new scientific evidence",
    },
    {
        "check": "current_evidence_state_has_home",
        "pass_signal": "detailed evidence state moved to docs/current_evidence_state.md",
        "failure_signal": "canonical evidence state is split across README fragments",
        "claim_boundary": "documentation cohesion only",
    },
    {
        "check": "recent_native_history_has_home",
        "pass_signal": "recent native evidence route moved to docs/recent_native_evidence_history.md",
        "failure_signal": "historical version list remains unlabeled at the bottom of README",
        "claim_boundary": "traceability repair only",
    },
    {
        "check": "anti_tautology_path_is_inspectable",
        "pass_signal": "README links to anti-tautology doc, known routine, and input schema",
        "failure_signal": "post-holdout audit exists but is hidden from the front page",
        "claim_boundary": "audit visibility only",
    },
    {
        "check": "version_route_shift_is_explicit",
        "pass_signal": "reviewer package shifts to v1.7.9 and closeout shifts to v1.7.10",
        "failure_signal": "roadmap still sends reviewer packaging directly after anti-tautology or closeout one step too early",
        "claim_boundary": "roadmap sequencing only",
    },
    {
        "check": "forbidden_claims_still_blocked",
        "pass_signal": "README, evidence docs, and release note keep role-blind, physics, cosmology, and observed-universe claims blocked",
        "failure_signal": "local holdout snapshot is worded as external proof or role-blind discovery",
        "claim_boundary": "claim discipline only",
    },
]

HOLDOUT_SNAPSHOT_ROWS = [
    {
        "weather_rung": "triad27",
        "evidence_status": "local assistant-handoff snapshot, not packaged reproduction bundle",
        "final_earned_one_events": 839,
        "raw_expression_pressure": 1283,
        "latent_overcrown": 9,
        "relation_debt": 39,
        "return_debt": 75,
        "false_one_pressure": 321,
        "final_false_one_crowns": 0,
        "lane_pattern_matches_expected": "true",
    },
    {
        "weather_rung": "deep81",
        "evidence_status": "local assistant-handoff snapshot, not packaged reproduction bundle",
        "final_earned_one_events": 1950,
        "raw_expression_pressure": 3012,
        "latent_overcrown": 9,
        "relation_debt": 120,
        "return_debt": 126,
        "false_one_pressure": 807,
        "final_false_one_crowns": 0,
        "lane_pattern_matches_expected": "true",
    },
    {
        "weather_rung": "wide243",
        "evidence_status": "local assistant-handoff snapshot, not packaged reproduction bundle",
        "final_earned_one_events": 9417,
        "raw_expression_pressure": 14058,
        "latent_overcrown": 21,
        "relation_debt": 465,
        "return_debt": 612,
        "false_one_pressure": 3543,
        "final_false_one_crowns": 0,
        "lane_pattern_matches_expected": "true",
    },
]

RELEASE_SHIFT_ROWS = [
    {
        "version": "v1.7.7-alpha",
        "role": "Anti-Tautology Audit / Role-Dependence Check",
        "status": "complete before cleanup",
        "reason": "fresh holdout should face tautology, leakage, vacuity, dead-safe, and role-dependence pressure before packaging",
    },
    {
        "version": "v1.7.8-alpha",
        "role": "Repo Cleanup / Cohesion Check",
        "status": "current gate",
        "reason": "README, evidence index, release spine, and audit path need a coherent front page before reviewer packaging",
    },
    {
        "version": "v1.7.9-alpha",
        "role": "Reviewer Start Here / Reproduction Package",
        "status": "next gate",
        "reason": "only after the repo presents the evidence and audit path cleanly should reviewer commands be packaged",
    },
    {
        "version": "v1.7.10-alpha",
        "role": "Core Question Closeout",
        "status": "later gate",
        "reason": "the closeout sentence must wait for reviewer/reproduction package truth",
    },
]


def _sum_snapshot(key: str) -> int:
    return sum(int(row[key]) for row in HOLDOUT_SNAPSHOT_ROWS)


def _write_read(path: Path) -> None:
    totals = {
        "earned": _sum_snapshot("final_earned_one_events"),
        "raw": _sum_snapshot("raw_expression_pressure"),
        "latent": _sum_snapshot("latent_overcrown"),
        "relation": _sum_snapshot("relation_debt"),
        "return": _sum_snapshot("return_debt"),
        "false_pressure": _sum_snapshot("false_one_pressure"),
        "false_crowns": _sum_snapshot("final_false_one_crowns"),
    }
    lines = [
        "# v1.7.8-alpha — Repo Cleanup / Cohesion Check",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        f"**Decision:** `{DECISION}`",
        "",
        "This gate exists because the project had enough new v1.7 material that the README was turning into evidence soup. The repair is front-page cohesion, not a new science crown.",
        "",
        "## What this gate checks",
        "",
    ]
    for row in COHESION_CHECKS:
        lines.append(f"- `{row['check']}` — {row['pass_signal']}.")
    lines.extend([
        "",
        "## Front-page routes",
        "",
        "| route | target | reason |",
        "|---|---|---|",
    ])
    for row in FRONT_PAGE_ROUTES:
        lines.append(f"| {row['route']} | `{row['target']}` | {row['reason']} |")
    lines.extend([
        "",
        "## Latest holdout snapshot",
        "",
        "This snapshot is local assistant-handoff evidence from the v1.7.6 fresh holdout ladder. It is not the reviewer reproduction package and it does not close the core question.",
        "",
        "Visual card assets:",
        "",
        "- docs/assets/v1_7_6_triad27_holdout_card.svg",
        "- docs/assets/v1_7_6_deep81_holdout_card.svg",
        "- docs/assets/v1_7_6_wide243_holdout_card.svg",
        "- docs/assets/v1_7_6_holdout_total_card.svg",
        "",
        "```text",
        f"+1 earned-one total       = {totals['earned']}",
        f"raw expression pressure   = {totals['raw']}",
        f"0 latent overcrown        = {totals['latent']}",
        f"0 relation debt           = {totals['relation']}",
        f"0 return debt             = {totals['return']}",
        f"-1 false-one pressure     = {totals['false_pressure']}",
        f"final false-one crowns    = {totals['false_crowns']}",
        "```",
        "",
        "## Route shift",
        "",
        f"- Next gate: `{NEXT_GATE}`",
        f"- Closeout gate: `{CLOSEOUT_GATE}`",
        "- Manuscript v2 waits until the closeout gate succeeds or deliberately freezes a bounded partial-answer record.",
        "",
        "## Boundary",
        "",
        "This check does not claim role-blind discovery, independent generator validation, physics, cosmology, or observed-universe proof. It only makes the repo surfaces coherent enough to package the next reviewer path without making readers walk through a haunted spreadsheet attic.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_v1_7_repo_cleanup_cohesion_check(out: str | Path) -> dict[str, Path]:
    out_dir = ensure_dir(out)
    paths = {name: out_dir / filename for name, filename in OUTPUT_FILES.items()}

    _write_read(paths["read"])
    write_dict_rows_csv(paths["front_page"], FRONT_PAGE_ROUTES)
    write_dict_rows_csv(paths["cohesion"], COHESION_CHECKS)
    write_dict_rows_csv(paths["evidence"], HOLDOUT_SNAPSHOT_ROWS)
    write_dict_rows_csv(paths["release_shift"], RELEASE_SHIFT_ROWS)

    decision = {
        "version": CURRENT_VERSION,
        "decision": DECISION,
        "gate_kind": GATE_KIND,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "core_question_closed": False,
        "reviewer_package_started": False,
        "manuscript_v2_started": False,
        "role_blind_discovery_claimed": False,
        "physics_or_cosmology_claimed": False,
        "front_page_routes": [row["target"] for row in FRONT_PAGE_ROUTES],
        "latest_snapshot_totals": {
            "final_earned_one_events": _sum_snapshot("final_earned_one_events"),
            "raw_expression_pressure": _sum_snapshot("raw_expression_pressure"),
            "latent_overcrown": _sum_snapshot("latent_overcrown"),
            "relation_debt": _sum_snapshot("relation_debt"),
            "return_debt": _sum_snapshot("return_debt"),
            "false_one_pressure": _sum_snapshot("false_one_pressure"),
            "final_false_one_crowns": _sum_snapshot("final_false_one_crowns"),
        },
        "next_gate": NEXT_GATE,
        "closeout_gate": CLOSEOUT_GATE,
    }
    paths["decision"].write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    bundle_path = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="v1_7_repo_cleanup_cohesion_check_bundle",
    )
    paths["bundle"] = bundle_path
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the v1.7.8 repo cleanup / cohesion check report.")
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_8_repo_cleanup_cohesion_check"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = build_v1_7_repo_cleanup_cohesion_check(args.out)
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
