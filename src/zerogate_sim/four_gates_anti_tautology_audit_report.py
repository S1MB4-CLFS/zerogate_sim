from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.6.25-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
REQUIRED_RUNGS = ("deep81", "wide243")
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation/return debt, and false-one pressure under controlled "
    "synthetic-field adversarial weather?"
)

REPRO_DECISION_FILE = "four_gates_fresh_seed_debt_reproduction_decision.json"
REPRO_RUNG_COMPARISON_FILE = "four_gates_fresh_seed_rung_comparison.csv"
REPRO_STATE_LANE_COMPARISON_FILE = "four_gates_fresh_seed_state_lane_comparison.csv"
EVIDENCE_DECISION_FILE = "four_gates_deepwide_debt_evidence_decision.json"
EVIDENCE_RUNG_SUMMARY_FILE = "four_gates_deepwide_debt_rung_summary.csv"
EVIDENCE_CANDIDATE_LANES_FILE = "four_gates_deepwide_debt_candidate_lanes.csv"
EVIDENCE_STATE_LANES_FILE = "four_gates_deepwide_state_lanes.csv"

OUTPUT_FILES = {
    "read": "four_gates_anti_tautology_audit_read.md",
    "decision": "four_gates_anti_tautology_audit_decision.json",
    "role_dependence": "four_gates_anti_tautology_role_dependence.csv",
    "witness_dependence": "four_gates_anti_tautology_witness_dependence.csv",
    "masked_evaluation": "four_gates_anti_tautology_masked_evaluation.csv",
    "debt_specificity": "four_gates_anti_tautology_debt_specificity.csv",
    "audit": "four_gates_anti_tautology_audit.json",
    "bundle": "four_gates_anti_tautology_audit_bundle.zip",
}

DEBT_LANES = {
    "0 relation debt": "relation_debt_count",
    "0 return debt": "return_debt_count",
}

ROLE_KEYS = ("candidate_profile", "truth_role", "kind", "candidate_id")
FORBIDDEN_STRONG_CLAIMS = (
    "independent discovery",
    "role-blind discovery",
    "physical proof",
    "cosmology proof",
    "spacetime metric claim",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "visible", "clean_zero"}


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def _load_reproduction_dir(reproduction_dir: Path) -> dict[str, Any]:
    reproduction_dir = Path(reproduction_dir)
    decision = _read_json(reproduction_dir / REPRO_DECISION_FILE)
    native = decision.get("native_witness_unchanged")
    if native != NATIVE_WITNESS:
        raise ValueError(f"Reproduction native witness mismatch: {native!r}")
    rung_rows = _read_csv(reproduction_dir / REPRO_RUNG_COMPARISON_FILE)
    state_rows = _read_csv(reproduction_dir / REPRO_STATE_LANE_COMPARISON_FILE)
    by_rung = {str(row.get("weather_rung", "")): row for row in rung_rows}
    missing = [rung for rung in REQUIRED_RUNGS if rung not in by_rung]
    if missing:
        raise ValueError("Reproduction comparison missing required rung(s): " + ", ".join(missing))
    return {
        "dir": reproduction_dir,
        "decision": decision,
        "rung_rows": rung_rows,
        "state_rows": state_rows,
        "by_rung": by_rung,
    }


def _load_evidence_dir(evidence_dir: Path) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir)
    decision = _read_json(evidence_dir / EVIDENCE_DECISION_FILE)
    native = decision.get("native_witness_unchanged")
    if native != NATIVE_WITNESS:
        raise ValueError(f"Evidence native witness mismatch: {native!r}")
    loaded = decision.get("loaded_rungs", [])
    missing = [rung for rung in REQUIRED_RUNGS if rung not in loaded]
    if missing:
        raise ValueError("Evidence decision missing required rung(s): " + ", ".join(missing))
    rung_rows = _read_csv(evidence_dir / EVIDENCE_RUNG_SUMMARY_FILE)
    candidate_rows = _read_csv(evidence_dir / EVIDENCE_CANDIDATE_LANES_FILE)
    state_rows = _read_csv(evidence_dir / EVIDENCE_STATE_LANES_FILE)
    return {
        "dir": evidence_dir,
        "decision": decision,
        "rung_rows": rung_rows,
        "candidate_rows": candidate_rows,
        "state_rows": state_rows,
        "by_rung": {str(row.get("weather_rung", "")): row for row in rung_rows},
    }


def _role_dependence_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    debt_rows = [row for row in candidate_rows if row.get("assigned_lane") in DEBT_LANES]
    rows: list[dict[str, object]] = []
    for lane, count_key in DEBT_LANES.items():
        lane_rows = [row for row in debt_rows if row.get("assigned_lane") == lane]
        kinds = sorted({str(row.get("kind", "")) for row in lane_rows})
        profiles = sorted({str(row.get("candidate_profile", "")) for row in lane_rows})
        truth_roles = sorted({str(row.get("truth_role", "")) for row in lane_rows})
        role_named_rows = [
            row
            for row in lane_rows
            if "debt" in str(row.get("kind", "")).lower()
            or "gap" in str(row.get("kind", "")).lower()
            or str(row.get("candidate_profile", "")) == "four_gates_debt"
        ]
        rows.append(
            {
                "lane": lane,
                "row_count": len(lane_rows),
                "event_count": sum(_int(row, count_key) for row in lane_rows),
                "candidate_profiles": ";".join(profiles),
                "truth_roles": ";".join(truth_roles),
                "candidate_kinds": ";".join(kinds),
                "role_named_fraction": round(_safe_div(len(role_named_rows), len(lane_rows)), 6),
                "role_dependence_status": "high_designed_candidate_profile_dependence" if role_named_rows else "low_direct_role_name_dependence",
            }
        )
    rows.append(
        {
            "lane": "all debt lanes",
            "row_count": len(debt_rows),
            "event_count": sum(_int(row, "relation_debt_count") + _int(row, "return_debt_count") for row in debt_rows),
            "candidate_profiles": ";".join(sorted({str(row.get("candidate_profile", "")) for row in debt_rows})),
            "truth_roles": ";".join(sorted({str(row.get("truth_role", "")) for row in debt_rows})),
            "candidate_kinds": ";".join(sorted({str(row.get("kind", "")) for row in debt_rows})),
            "role_named_fraction": round(_safe_div(len([row for row in debt_rows if str(row.get("candidate_profile", "")) == "four_gates_debt"]), len(debt_rows)), 6),
            "role_dependence_status": "high_designed_candidate_profile_dependence" if debt_rows else "no_debt_rows_detected",
        }
    )
    return rows


def _witness_dependence_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for lane, count_key in DEBT_LANES.items():
        lane_rows = [row for row in candidate_rows if row.get("assigned_lane") == lane]
        correct_count_rows = [row for row in lane_rows if _int(row, count_key) > 0]
        wrong_counterpart = "return_debt_count" if count_key == "relation_debt_count" else "relation_debt_count"
        counterpart_rows = [row for row in lane_rows if _int(row, wrong_counterpart) > 0]
        rows.append(
            {
                "lane": lane,
                "row_count": len(lane_rows),
                "event_count": sum(_int(row, count_key) for row in lane_rows),
                "witness_count_column": count_key,
                "rows_with_required_witness_count": len(correct_count_rows),
                "rows_with_opposite_debt_count": len(counterpart_rows),
                "witness_dependence_status": "witness_count_derived" if lane_rows and len(correct_count_rows) == len(lane_rows) else "witness_count_incomplete_or_absent",
            }
        )
    earned_rows = [row for row in candidate_rows if row.get("assigned_lane") == "+1 earned-one"]
    false_crowns = sum(_int(row, "final_false_one_crowns") for row in candidate_rows)
    rows.append(
        {
            "lane": "+1 earned-one controls",
            "row_count": len(earned_rows),
            "event_count": sum(_int(row, "final_earned_one_count") for row in earned_rows),
            "witness_count_column": "final_earned_one_count",
            "rows_with_required_witness_count": len([row for row in earned_rows if _int(row, "final_earned_one_count") > 0]),
            "rows_with_opposite_debt_count": 0,
            "witness_dependence_status": "earned_one_count_derived" if earned_rows else "earned_controls_absent",
        }
    )
    rows.append(
        {
            "lane": "final false-one crowns",
            "row_count": len(candidate_rows),
            "event_count": false_crowns,
            "witness_count_column": "final_false_one_crowns",
            "rows_with_required_witness_count": 0,
            "rows_with_opposite_debt_count": 0,
            "witness_dependence_status": "clean_zero" if false_crowns == 0 else "breach",
        }
    )
    return rows


def _masked_evaluation_rows(reproduction: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rung in REQUIRED_RUNGS:
        repro_row = reproduction["by_rung"][rung]
        evidence_row = evidence["by_rung"].get(rung, {})
        relation = _int(evidence_row, "relation_debt_count")
        ret = _int(evidence_row, "return_debt_count")
        earned = _int(evidence_row, "final_earned_one_events")
        raw_false = _int(evidence_row, "raw_false_one_pressure")
        demoted = _int(evidence_row, "false_one_demoted_count")
        final_false = _int(evidence_row, "final_false_one_crowns")
        rows.append(
            {
                "weather_rung": rung,
                "masked_inputs": "numeric evidence counts only; candidate kind/profile/truth_role ignored",
                "fresh_seed_reproduction_status": repro_row.get("reproduction_status", ""),
                "earned_visible": earned > 0,
                "relation_debt_visible": relation > 0,
                "return_debt_visible": ret > 0,
                "false_pressure_demoted": raw_false > 0 and demoted >= raw_false,
                "final_false_crowns_clean": final_false == 0,
                "masked_pattern_status": "masked_numeric_pattern_visible" if earned > 0 and relation > 0 and ret > 0 and raw_false > 0 and demoted >= raw_false and final_false == 0 else "masked_numeric_pattern_incomplete",
            }
        )
    return rows


def _debt_specificity_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_lane: dict[str, list[dict[str, str]]] = {lane: [] for lane in DEBT_LANES}
    for row in candidate_rows:
        lane = row.get("assigned_lane", "")
        if lane in by_lane:
            by_lane[lane].append(row)
    relation_kinds = {str(row.get("kind", "")) for row in by_lane["0 relation debt"]}
    return_kinds = {str(row.get("kind", "")) for row in by_lane["0 return debt"]}
    overlap = sorted(relation_kinds & return_kinds)
    rows: list[dict[str, object]] = []
    rows.append(
        {
            "check": "relation_vs_return_kind_overlap",
            "relation_kinds": ";".join(sorted(relation_kinds)),
            "return_kinds": ";".join(sorted(return_kinds)),
            "overlap": ";".join(overlap),
            "specificity_status": "distinct_kind_families" if relation_kinds and return_kinds and not overlap else "overlapping_or_missing_debt_kinds",
        }
    )
    for lane, rows_for_lane in by_lane.items():
        count_key = DEBT_LANES[lane]
        rows.append(
            {
                "check": lane,
                "relation_kinds": ";".join(sorted({str(row.get("kind", "")) for row in rows_for_lane})),
                "return_kinds": "",
                "overlap": "",
                "specificity_status": "visible_specific_lane" if rows_for_lane and sum(_int(row, count_key) for row in rows_for_lane) > 0 else "missing_specific_lane",
            }
        )
    return rows


def _make_decision(
    *,
    reproduction: dict[str, Any],
    role_rows: list[dict[str, object]],
    witness_rows: list[dict[str, object]],
    masked_rows: list[dict[str, object]],
    specificity_rows: list[dict[str, object]],
) -> dict[str, Any]:
    reproduction_decision = reproduction["decision"].get("global_decision", "")
    role_high = any(str(row.get("role_dependence_status")) == "high_designed_candidate_profile_dependence" for row in role_rows)
    witness_ok = all(
        str(row.get("witness_dependence_status")) in {"witness_count_derived", "earned_one_count_derived", "clean_zero"}
        for row in witness_rows
    )
    masked_ok = all(str(row.get("masked_pattern_status")) == "masked_numeric_pattern_visible" for row in masked_rows)
    specificity_ok = any(str(row.get("specificity_status")) == "distinct_kind_families" for row in specificity_rows)
    if (
        reproduction_decision.startswith("resist_")
        or any(str(row.get("witness_dependence_status")) == "breach" for row in witness_rows)
        or any(row.get("final_false_crowns_clean") is False for row in masked_rows)
    ):
        global_decision = "resist_anti_tautology_audit_breach_or_regression"
    elif role_high and witness_ok and masked_ok and specificity_ok:
        global_decision = "witness_bounded_role_shaped_but_witness_computed"
    elif witness_ok and masked_ok and specificity_ok:
        global_decision = "expand_anti_tautology_audit_witness_derived_enough"
    else:
        global_decision = "hold_anti_tautology_audit_incomplete"
    if global_decision.startswith("expand_"):
        claim_status = "+1 earned audit: debt states are witness-derived enough for bounded synthetic zero-zone gating language"
    elif global_decision.startswith("witness_"):
        claim_status = "0 bounded audit: debt states reproduce and are witness-counted, but the current evidence remains designed-profile / role-shaped"
    elif global_decision.startswith("resist_"):
        claim_status = "-1 demoted audit: breach or regression blocks the claim"
    else:
        claim_status = "0 hold audit: insufficient evidence for claim upgrade"
    return {
        "version": CURRENT_VERSION,
        "core_question": CORE_QUESTION,
        "global_decision": global_decision,
        "claim_status": claim_status,
        "native_witness_unchanged": NATIVE_WITNESS,
        "reproduction_decision": reproduction_decision,
        "role_dependency_high": role_high,
        "witness_count_dependence_ok": witness_ok,
        "masked_numeric_pattern_visible": masked_ok,
        "debt_specificity_ok": specificity_ok,
        "stronger_claim_not_earned": "independent role-blind discovery of debt states" if role_high else "none",
        "allowed_next_gate": "v1.6.26-alpha reproduction command package" if not global_decision.startswith("resist_") else "stop and repair before v1.6.26",
        "forbidden_claims": list(FORBIDDEN_STRONG_CLAIMS),
        "observed_universe_bridge_allowed": False,
        "shadow_route_allowed": False,
        "zenodo_route_allowed": False,
    }


def _write_read(path: Path, *, decision: dict[str, Any], role_rows: list[dict[str, object]], masked_rows: list[dict[str, object]]) -> None:
    lines = [
        "# Four Gates Anti-Tautology Audit / Role-Dependence Check",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Boundary:** no Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim, no native witness mutation.",
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
        "## Decision",
        "",
        "```text",
        str(decision["global_decision"]),
        "```",
        "",
        str(decision["claim_status"]),
        "",
        "## What this audit checks",
        "",
        "This gate asks whether the debt result is only a label-counting trick. It separates designed-profile dependence from witness-count dependence.",
        "",
        "- Role dependence: debt candidates are explicitly debt-shaped and belong to `four_gates_debt`.",
        "- Witness dependence: debt lanes must be assigned through `relation_debt_count` and `return_debt_count`, not merely through candidate names.",
        "- Masked evaluation: when candidate labels are ignored, the numeric state pattern must still show earned-one, relation debt, return debt, false-pressure demotion, and zero final false crowns.",
        "- Debt specificity: relation debt and return debt should be distinguishable, not one generic hold bucket.",
        "",
        "## Role-dependence summary",
        "",
        "| lane | rows | events | role dependence | candidate kinds |",
        "|---|---:|---:|---|---|",
    ]
    for row in role_rows:
        lines.append(
            f"| {row['lane']} | {row['row_count']} | {row['event_count']} | {row['role_dependence_status']} | {row['candidate_kinds']} |"
        )
    lines.extend([
        "",
        "## Masked numeric pattern",
        "",
        "| rung | status | earned | relation debt | return debt | false pressure demoted | final false crowns clean |",
        "|---|---|---|---|---|---|---|",
    ])
    for row in masked_rows:
        lines.append(
            f"| {row['weather_rung']} | {row['masked_pattern_status']} | {row['earned_visible']} | {row['relation_debt_visible']} | {row['return_debt_visible']} | {row['false_pressure_demoted']} | {row['final_false_crowns_clean']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The current result is not independent role-blind discovery. The debt evidence uses deliberately designed near-success candidate families. That is allowed for a controlled synthetic-field proof, but it bounds the claim.",
        "",
        "The useful result is narrower: the Four Gates witness can represent, preserve, and reproduce structured zero/debt states under designed controlled synthetic weather while maintaining earned-one and false-one separation.",
        "",
        "## Next gate",
        "",
        f"`{decision['allowed_next_gate']}`",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_anti_tautology_audit_report(
    *,
    output_dir: Path,
    fresh_reproduction_dir: Path,
    fresh_evidence_dir: Path,
) -> dict[str, Path]:
    output_dir = ensure_dir(Path(output_dir))
    reproduction = _load_reproduction_dir(Path(fresh_reproduction_dir))
    evidence = _load_evidence_dir(Path(fresh_evidence_dir))
    role_rows = _role_dependence_rows(evidence["candidate_rows"])
    witness_rows = _witness_dependence_rows(evidence["candidate_rows"])
    masked_rows = _masked_evaluation_rows(reproduction, evidence)
    specificity_rows = _debt_specificity_rows(evidence["candidate_rows"])
    decision = _make_decision(
        reproduction=reproduction,
        role_rows=role_rows,
        witness_rows=witness_rows,
        masked_rows=masked_rows,
        specificity_rows=specificity_rows,
    )

    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    _write_read(paths["read"], decision=decision, role_rows=role_rows, masked_rows=masked_rows)
    paths["decision"].write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
    write_dict_rows_csv(paths["role_dependence"], role_rows)
    write_dict_rows_csv(paths["witness_dependence"], witness_rows)
    write_dict_rows_csv(paths["masked_evaluation"], masked_rows)
    write_dict_rows_csv(paths["debt_specificity"], specificity_rows)
    audit = {
        "version": CURRENT_VERSION,
        "source_reproduction_dir": str(Path(fresh_reproduction_dir)),
        "source_evidence_dir": str(Path(fresh_evidence_dir)),
        "output_files": {key: path.name for key, path in paths.items()},
        "native_witness_unchanged": NATIVE_WITNESS,
        "forbidden_claims": list(FORBIDDEN_STRONG_CLAIMS),
    }
    paths["audit"].write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="four_gates_anti_tautology_audit_bundle",
    )
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Four Gates anti-tautology / role-dependence audit.")
    parser.add_argument("--fresh-reproduction-dir", required=True, type=Path, help="Folder containing v1.6.22 fresh-seed reproduction report outputs.")
    parser.add_argument("--fresh-evidence-dir", required=True, type=Path, help="Folder containing fresh Four Gates deepwide debt evidence outputs.")
    parser.add_argument("--out", required=True, type=Path, help="Output folder for audit report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_four_gates_anti_tautology_audit_report(
        output_dir=args.out,
        fresh_reproduction_dir=args.fresh_reproduction_dir,
        fresh_evidence_dir=args.fresh_evidence_dir,
    )
    print(f"Wrote Four Gates anti-tautology audit report to {args.out}")
    for key in ["read", "decision", "role_dependence", "witness_dependence", "masked_evaluation", "debt_specificity", "bundle"]:
        print(f"{key}: {paths[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
