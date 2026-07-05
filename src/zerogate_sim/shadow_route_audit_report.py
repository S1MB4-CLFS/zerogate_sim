from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Iterable

CURRENT_VERSION = "v1.6.11-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"

ROUTE_AUDIT_FILES = {
    "read": "shadow_route_audit_read.md",
    "decision": "shadow_route_audit_decision.json",
    "steps": "shadow_route_audit_steps.csv",
    "feature_design": "shadow_route_feature_design.csv",
    "audit": "shadow_route_audit_audit.json",
    "bundle": "shadow_route_audit_bundle.zip",
}

ROUTE_STEPS: list[dict[str, object]] = [
    {
        "version": "v1.6.8-alpha",
        "gate": "hardened triad27 evidence",
        "purpose": "move shadow triad27 from one profile / four families into cell-level evidence",
        "result": "native witness survived; shadow went under hardened baselines on specific targets",
        "decision": "witness: harder battlefield exists; no deeper weather claim yet",
    },
    {
        "version": "v1.6.9-alpha",
        "gate": "shadow discrimination residual audit",
        "purpose": "ask what remains after the best dumb baseline explains easy pressure",
        "result": "density signal only; relation/return/demotion discrimination not earned",
        "decision": "witness: shadow sees pressure amount, not pressure kind",
    },
    {
        "version": "v1.6.10-alpha",
        "gate": "shadow lane split",
        "purpose": "split the global shadow surface into fixed candidate lanes without retuning the historical score",
        "result": "lane formulas exist; evidence still decides whether any lane earns non-trivial signal",
        "decision": "witness: scoring surface is inspectable but not yet trusted",
    },
    {
        "version": CURRENT_VERSION,
        "gate": "roadmap truth and feature-design audit",
        "purpose": "repair release spine and define the next shadow feature design before implementation",
        "result": "map repaired; future route bounded; feature design remains proposal only",
        "decision": "hold: ready for feature implementation only after map is clean",
    },
]

FEATURE_DESIGN: list[dict[str, object]] = [
    {
        "lane": "relation_specific",
        "feature_family": "relation ownership / borrowed-relation contrast",
        "why_needed": "relation false pressure was under raw-strength baselines; current features do not separate owned relation from borrowed relation well enough",
        "candidate_observables": "relation debt rate; echo-independence dependence; mirror-secondary pressure; relation/return divergence; relation persistence after weather shift",
        "forbidden_shortcut": "truth_role, trap/expresser labels, target false-one rates, family names or row order",
        "success_test": "beats raw-strength and relation-only baselines on hardened triad27 relation-specific targets",
    },
    {
        "lane": "return_specific",
        "feature_family": "return integrity / collapse-vs-return contrast",
        "why_needed": "return-specific pressure was under raw-strength baselines; zero-crossing and raw pressure can mimic return",
        "candidate_observables": "return gate rate; weakest-gate pressure rate; return debt; return/raw divergence; sustained return after late pressure",
        "forbidden_shortcut": "native role labels, post-score targets, score retuning after seeing holdout outcome",
        "success_test": "beats raw-strength and return-only baselines on hardened triad27 return-specific targets",
    },
    {
        "lane": "demotion",
        "feature_family": "demotion trajectory / refusal pressure",
        "why_needed": "demotion is currently mostly tracked by raw pressure; the score must see why pressure was refused, not merely that pressure was high",
        "candidate_observables": "ablation demotion dependence; false-pressure persistence; hold-or-demote pressure; gate imbalance before demotion",
        "forbidden_shortcut": "final target columns or any field derived from the evaluation target after scoring",
        "success_test": "beats raw-pressure-only on demotion and hold-or-demote targets without native witness mutation",
    },
    {
        "lane": "zero_hold_ambiguity",
        "feature_family": "structured zero / not-yet pressure",
        "why_needed": "zero should hold latent or ambiguous pressure instead of collapsing all non-crowns into failure",
        "candidate_observables": "latent hold rate; relation debt rate; zero-depth maturity proxy; weak-gate alternation; not-yet persistence",
        "forbidden_shortcut": "crowning all high-pressure cases or turning zero into a binary failure bucket",
        "success_test": "separates held ambiguity from demoted false pressure while preserving final false-crown safety",
    },
    {
        "lane": "density_residual",
        "feature_family": "residual pressure after dumb baselines",
        "why_needed": "density is the only lane with candidate signal; it must become a foundation rather than a fake detector",
        "candidate_observables": "residual after raw-pressure-only; residual after raw-strength-only; weakest-gate residual; pressure shape rather than pressure amount",
        "forbidden_shortcut": "calling density detection role-blind discovery",
        "success_test": "density remains visible while specific lanes improve beyond best dumb baselines",
    },
]

FUTURE_ROUTE: list[dict[str, object]] = [
    {
        "version": "v1.6.12-alpha",
        "gate": "shadow feature implementation",
        "question": "Can new observable, role-stripped feature columns expose pressure kind rather than pressure amount?",
        "pass_condition": "features are emitted before targets load; no forbidden fields; tests show relation/return/demotion candidate features exist",
        "stop_condition": "feature formulas require targets or role labels",
    },
    {
        "version": "v1.6.13-alpha",
        "gate": "hardened triad27 rerun",
        "question": "Do the new features improve lane discrimination on the hardened triad27 battlefield?",
        "pass_condition": "at least one specific lane beats best dumb baseline without harming native witness boundary",
        "stop_condition": "all specific lanes remain under raw pressure or raw strength baselines",
    },
    {
        "version": "v1.6.14-alpha",
        "gate": "shadow decision gate",
        "question": "Should the shadow line advance, hold as diagnostic-only, or be demoted?",
        "pass_condition": "explicit +1/0/-1 decision written before deeper weather",
        "stop_condition": "route tries to move to deep81/wide243 while triad27 specificity remains unearned",
    },
    {
        "version": "v1.7.0-alpha",
        "gate": "deep81 / wide243 extension only if earned",
        "question": "Does earned triad27 specificity survive perturbation and temporal-depth weather?",
        "pass_condition": "triad27 specificity already earned; deep81/wide243 evaluated under the same hardening judge",
        "stop_condition": "bigger weather is used to hide triad27 failure",
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
        "# ZeroGateSim Shadow Route Audit and Feature-Design Proposal",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** roadmap truth repair + feature-design proposal, not implementation",
        "**Boundary:** not role-blind discovery, not detector closeout, not native witness mutation",
        "",
        "## Native witness boundary",
        "",
        "```text",
        NATIVE_WITNESS,
        "```",
        "",
        "This audit exists because the route must stop reacting one wound at a time. The map must say several steps ahead what is being tested, what would falsify it, and when to stop.",
        "",
        "## Current wound",
        "",
        "The hardened triad27 evidence and lane split show a specific state:",
        "",
        "```text",
        "native four-gate witness: standing",
        "shadow density pressure: candidate signal",
        "shadow relation / return / demotion specificity: not earned",
        "```",
        "",
        "So the next work is not deeper weather. The next work is feature design for pressure kind.",
        "",
        "## Route already earned",
        "",
        "| version | gate | decision |",
        "|---|---|---|",
    ]
    for row in ROUTE_STEPS:
        lines.append(f"| `{row['version']}` | {row['gate']} | {row['decision']} |")
    lines.extend(
        [
            "",
            "## Feature design proposal",
            "",
            "These are proposed observable feature families. They do not retune the score and do not read targets before scoring.",
            "",
            "| lane | feature family | why needed | success test |",
            "|---|---|---|---|",
        ]
    )
    for row in FEATURE_DESIGN:
        lines.append(
            f"| `{row['lane']}` | {row['feature_family']} | {row['why_needed']} | {row['success_test']} |"
        )
    lines.extend(
        [
            "",
            "## Next route",
            "",
            "| version | gate | question | stop condition |",
            "|---|---|---|---|",
        ]
    )
    for row in FUTURE_ROUTE:
        lines.append(
            f"| `{row['version']}` | {row['gate']} | {row['question']} | {row['stop_condition']} |"
        )
    lines.extend(
        [
            "",
            "## Stop law",
            "",
            "```text",
            "Do not move to deep81 / wide243 while triad27 specificity is unearned.",
            "Do not call density pressure detection role-blind discovery.",
            "Do not mutate native C_Z to make shadow look better.",
            "Do not let README / ROADMAP / release notes disagree about current version truth.",
            "```",
            "",
            "This audit is a hold/route gate. It prepares v1.6.12 implementation only if the map stays clean.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bundle(output_dir: Path, paths: dict[str, Path]) -> None:
    bundle = paths["bundle"]
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for key, path in paths.items():
            if key == "bundle":
                continue
            zf.write(path, path.relative_to(output_dir))


def write_shadow_route_audit_report(*, output_dir: Path) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    paths = {key: output_dir / filename for key, filename in ROUTE_AUDIT_FILES.items()}
    _write_csv(paths["steps"], ROUTE_STEPS + FUTURE_ROUTE)
    _write_csv(paths["feature_design"], FEATURE_DESIGN)
    decision = {
        "version": CURRENT_VERSION,
        "global_decision": "hold_map_repaired_feature_design_ready_not_implemented",
        "native_witness_unchanged": NATIVE_WITNESS,
        "shadow_state": "density_pressure_candidate_signal_specific_discrimination_not_earned",
        "next_allowed_gate": "v1.6.12-alpha shadow feature implementation",
        "blocked_gate": "deep81 / wide243 extension until triad27 specificity is earned",
        "role_blind_discovery_claim": False,
        "score_retuning": False,
        "feature_design_rows": len(FEATURE_DESIGN),
        "future_route_rows": len(FUTURE_ROUTE),
    }
    paths["decision"].write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = {
        "version_truth": CURRENT_VERSION,
        "report_side_only": True,
        "requires_targets": False,
        "native_witness_unchanged": NATIVE_WITNESS,
        "forbidden_claims": [
            "role-blind discovery",
            "detector closeout",
            "native witness mutation",
            "deep81 / wide243 trust before triad27 specificity",
        ],
    }
    paths["audit"].write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_read(paths["read"])
    _write_bundle(output_dir, paths)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write the ZeroGateSim shadow route audit and feature-design proposal.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_route_audit_v1_6_11"))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    paths = write_shadow_route_audit_report(output_dir=args.out)
    print(f"Wrote shadow route audit: {paths['read']}")


if __name__ == "__main__":
    main()
