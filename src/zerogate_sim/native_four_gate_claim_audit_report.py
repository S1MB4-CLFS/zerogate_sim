from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Iterable

CURRENT_VERSION = "v1.6.14-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

AUDIT_FILES = {
    "read": "native_four_gate_claim_audit_read.md",
    "decision": "native_four_gate_claim_audit_decision.json",
    "readiness": "native_four_gate_readiness_criteria.csv",
    "route": "native_four_gate_route.csv",
    "claim_lanes": "native_four_gate_claim_lanes.csv",
    "audit": "native_four_gate_claim_audit_audit.json",
    "bundle": "native_four_gate_claim_audit_bundle.zip",
}

CLAIM_LANES: list[dict[str, object]] = [
    {
        "lane": "+1 earned-one",
        "positive_success": "earned expression preserved",
        "failure_mode": "dead-safe witness refuses too much or promotes raw pressure",
        "required_measure": "final earned-one count, earned-one preservation rate, earned-vs-raw separation",
        "must_beat": "binary/no-crown and raw-as-final ablations",
    },
    {
        "lane": "0 latent overcrown",
        "positive_success": "latent pressure held as structured zero, not treated as generic failure",
        "failure_mode": "latent pressure is crowned or erased",
        "required_measure": "latent_overcrown_pressure, latent held/demoted count, zero-state category accounting",
        "must_beat": "no-zero-hold and binary failure bucket ablations",
    },
    {
        "lane": "0 relation debt",
        "positive_success": "borrowed relation is held until ownership / independence is earned",
        "failure_mode": "relation echo becomes final +1 or disappears from accounting",
        "required_measure": "relation_debt_count, echo-independence dependence, relation adversary pressure",
        "must_beat": "no-relation and no-echo-independence ablations",
    },
    {
        "lane": "0 return debt",
        "positive_success": "collapse-to-zero and shallow zero-crossing are held instead of called return",
        "failure_mode": "return theater passes as coherent return or return debt is not measured",
        "required_measure": "return_debt_count, return-integrity gap, return adversary pressure",
        "must_beat": "no-return and average-gate ablations",
    },
    {
        "lane": "-1 false-one pressure",
        "positive_success": "trap pressure remains visible and is demoted without final crown",
        "failure_mode": "false-one pressure crowned or hidden",
        "required_measure": "raw_false_one_pressure, false_one_demoted_count, final_false_one_crowns",
        "must_beat": "raw-expression-only and no-false-one-demotion ablations",
    },
]

READINESS_CRITERIA: list[dict[str, object]] = [
    {
        "criterion": "four dedicated adversarial families",
        "why": "first-alpha had three dedicated pre-return corpora; repaired proof must include return theater as its own pressure family",
        "pass_condition": "distinction, polarity, relation, and return each appear as native run families",
        "status": "required_before_claim_closeout",
    },
    {
        "criterion": "positive zero-state accounting",
        "why": "zero is not just non-crown; it must hold latent, relation, return, quarantine, and not-yet pressure as structured state",
        "pass_condition": "reports separate latent overcrown, relation debt, return debt, and false-one demotion",
        "status": "required_before_claim_closeout",
    },
    {
        "criterion": "native ablation enemies",
        "why": "zero final false crowns alone is too easy; a dead witness can crown nothing",
        "pass_condition": "native witness beats raw-only, binary-only, no-return, no-relation, no-lineage/depth, no-echo, and no-zero-hold alternatives",
        "status": "next_gate_v1.6.15",
    },
    {
        "criterion": "triad27 first",
        "why": "local expression weather should catch simple wounds before deeper weather is allowed",
        "pass_condition": "four-corpus triad27 reports trinary outcome accounting and ablation comparison",
        "status": "planned_v1.6.16",
    },
    {
        "criterion": "deep81 / wide243 after triad27",
        "why": "bigger weather must not hide local failure",
        "pass_condition": "deep81 and wide243 native evidence are run only after triad27 passes ablations",
        "status": "planned_v1.6.17",
    },
    {
        "criterion": "fresh-seed reproduction",
        "why": "a single proof path can overfit the generated field design",
        "pass_condition": "fresh seeds reproduce the main native result before manuscript/evidence correction",
        "status": "planned_v1.6.18",
    },
    {
        "criterion": "claim lane separation",
        "why": "simulation support, mathematical analogy, and physical speculation carry different evidence burdens",
        "pass_condition": "README, ROADMAP, paper correction notes, and DOI plan separate those lanes",
        "status": "required_before_v2.0_review_release",
    },
]

ROUTE_STEPS: list[dict[str, object]] = [
    {
        "version": "v1.6.14-alpha",
        "gate": "native four-gate claim audit",
        "question": CORE_QUESTION,
        "pass_condition": "route and readiness criteria are explicit; shadow remains historical/HOLD; no Zenodo route yet",
        "stop_condition": "route tries to jump directly to manuscript correction or observed-universe bridge",
    },
    {
        "version": "v1.6.15-alpha",
        "gate": "native ablation baselines",
        "question": "Does the final trinary witness beat raw/binary/ablated alternatives while preserving earned-one and structured zero?",
        "pass_condition": "native witness beats ablations on +1 preservation, 0-state hold, and -1 demotion",
        "stop_condition": "native witness only looks good because competitors are not implemented or zero-state is not measured",
    },
    {
        "version": "v1.6.16-alpha",
        "gate": "four-corpus triad27 native evidence",
        "question": "Does the repaired native claim hold under 3^3 local expression weather across all four adversarial families?",
        "pass_condition": "triad27 reports trinary confusion accounting and ablation comparison with zero final false crowns",
        "stop_condition": "triad27 fails, or bigger weather is used to hide local failure",
    },
    {
        "version": "v1.6.17-alpha",
        "gate": "deep81 / wide243 native evidence",
        "question": "Does the native witness survive perturbation and temporal-depth weather after triad27 passes?",
        "pass_condition": "deep81/wide243 preserve the same claim lanes and beat ablations",
        "stop_condition": "deeper weather loses relation/return debt accounting or earned-one preservation",
    },
    {
        "version": "v1.6.18-alpha",
        "gate": "fresh-seed reproduction and correction package planning",
        "question": "Is the controlled synthetic-field result reproducible and ready to be separated into simulation support, analogy, and speculation lanes?",
        "pass_condition": "fresh seeds reproduce; correction package is ready; no Zenodo upload yet unless authorized",
        "stop_condition": "public language exceeds controlled synthetic-field evidence",
    },
]


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_read(path: Path) -> None:
    lines = [
        "# Native Four-Gate Claim Audit",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** route correction / scientific readiness audit, not manuscript release",
        "**Boundary:** not Zenodo yet, not physics proof, not observed-universe bridge, not shadow revival",
        "",
        "## Core question",
        "",
        f"> {CORE_QUESTION}",
        "",
        "## Native witness",
        "",
        "```text",
        NATIVE_WITNESS,
        "```",
        "",
        "The audit exists because zero final false crowns alone is not enough. A witness that crowns nothing is safe and useless. The native claim must show three coordinated movements: earned-one preservation, structured zero hold, and false-one demotion.",
        "",
        "## Claim lanes",
        "",
        "| lane | positive success | failure mode | must beat |",
        "|---|---|---|---|",
    ]
    for row in CLAIM_LANES:
        lines.append(f"| {row['lane']} | {row['positive_success']} | {row['failure_mode']} | {row['must_beat']} |")
    lines.extend([
        "",
        "## Readiness criteria",
        "",
        "| criterion | pass condition | status |",
        "|---|---|---|",
    ])
    for row in READINESS_CRITERIA:
        lines.append(f"| {row['criterion']} | {row['pass_condition']} | {row['status']} |")
    lines.extend([
        "",
        "## Route",
        "",
        "| version | gate | stop condition |",
        "|---|---|---|",
    ])
    for row in ROUTE_STEPS:
        lines.append(f"| `{row['version']}` | {row['gate']} | {row['stop_condition']} |")
    lines.extend([
        "",
        "## Decision",
        "",
        "```text",
        "hold_native_claim_not_closed_yet",
        "```",
        "",
        "The native four-gate idea remains the active route. The role-stripped shadow route remains historical/HOLD. The next scientific step is native ablation baselines, not Zenodo, not v2.0, not observed-universe bridge work.",
        "",
        "## Forbidden shortcuts",
        "",
        "- do not describe role-aware synthetic-field proof as role-blind discovery;",
        "- do not use zero final false crowns as the whole claim;",
        "- do not skip positive zero-state accounting;",
        "- do not start deep81/wide243 before four-corpus triad27 and ablations;",
        "- do not begin Zenodo correction until the native route earns a coherent package;",
        "- do not claim that math or observed-universe similarities prove ZeroGateSim is how reality works.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_native_four_gate_claim_audit_report(*, output_dir: Path) -> dict[str, Path]:
    output_dir = _ensure_dir(Path(output_dir))
    paths = {key: output_dir / name for key, name in AUDIT_FILES.items()}
    _write_read(paths["read"])
    _write_csv(paths["readiness"], READINESS_CRITERIA)
    _write_csv(paths["route"], ROUTE_STEPS)
    _write_csv(paths["claim_lanes"], CLAIM_LANES)
    decision = {
        "version": CURRENT_VERSION,
        "global_decision": "hold_native_claim_not_closed_yet",
        "core_question": CORE_QUESTION,
        "native_witness_unchanged": NATIVE_WITNESS,
        "shadow_route_status": "historical_diagnostic_hold",
        "zenodo_route_allowed": False,
        "observed_universe_bridge_allowed": False,
        "role_blind_discovery_claim": False,
        "next_gate": "v1.6.15-alpha native ablation baselines",
        "required_before_v2_0": [row["criterion"] for row in READINESS_CRITERIA],
    }
    paths["decision"].write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
    audit = {
        "files": {key: path.name for key, path in paths.items()},
        "report_side_only": True,
        "native_witness_mutated": False,
        "requires_existing_runs": False,
        "deletes_runs": False,
    }
    paths["audit"].write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    with zipfile.ZipFile(paths["bundle"], "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for key in ["read", "decision", "readiness", "route", "claim_lanes", "audit"]:
            zf.write(paths[key], arcname=paths[key].name)
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write the ZeroGateSim native four-gate claim audit report.")
    parser.add_argument("--out", required=True, help="Output directory for the audit report.")
    args = parser.parse_args(argv)
    paths = write_native_four_gate_claim_audit_report(output_dir=Path(args.out))
    print(paths["read"])
    print(paths["decision"])
    print(paths["bundle"])


if __name__ == "__main__":
    main()
