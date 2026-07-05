from __future__ import annotations

import argparse
import json
from pathlib import Path

from zerogate_sim.config import SimulationConfig
from zerogate_sim.gates import evaluate_run
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.signals import CandidateSpec, candidate_specs, generate_pressure_field

CURRENT_VERSION = "v1.6.19-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
PROFILE_NAME = "four_gates_debt"

OUTPUT_FILES = {
    "read": "four_gates_debt_candidate_generator_read.md",
    "decision": "four_gates_debt_candidate_generator_decision.json",
    "candidate_specs": "four_gates_debt_candidate_specs.csv",
    "lane_targets": "four_gates_debt_lane_targets.csv",
    "preview_scores": "four_gates_debt_preview_gate_scores.csv",
    "audit": "four_gates_debt_candidate_generator_audit.json",
    "bundle": "four_gates_debt_candidate_generator_bundle.zip",
}

LANE_BY_KIND = {
    "earned_return_control": "+1 earned-one",
    "false_one_trap_control": "-1 false-one demotion",
    "relation_debt_local": "0 relation debt",
    "return_debt_local": "0 return debt",
    "relation_debt_global_a": "0 relation debt",
    "relation_debt_global_b": "0 relation debt",
    "closure_gap_candidate": "0 return debt",
    "dual_return_gap_candidate": "0 return debt",
    "perturbation_survival_candidate": "0 return debt / 0 latent overcrown",
}

DIAGNOSTIC_BY_KIND = {
    "earned_return_control": "return memory preserved; closure gap low",
    "false_one_trap_control": "raw local pressure should be exposed as false-one",
    "relation_debt_local": "relation ownership gap / relation stability gap",
    "return_debt_local": "return memory gap / dual-return gap",
    "relation_debt_global_a": "factorization gap / global relation with local incompleteness",
    "relation_debt_global_b": "factorization gap / global relation with local incompleteness",
    "closure_gap_candidate": "closure gap after double-witness return",
    "dual_return_gap_candidate": "dual-return gap after complementary witness pressure",
    "perturbation_survival_candidate": "perturbation survival gap / zero-hold eligibility",
}


def expected_lane_for_kind(kind: str) -> str:
    return LANE_BY_KIND.get(kind, "0 witness hold")


def diagnostic_for_kind(kind: str) -> str:
    return DIAGNOSTIC_BY_KIND.get(kind, "zero-hold eligibility")


def _spec_row(spec: CandidateSpec) -> dict[str, object]:
    return {
        "candidate_id": spec.candidate_id,
        "kind": spec.kind,
        "truth_role": spec.truth_role,
        "expected_lane": expected_lane_for_kind(spec.kind),
        "diagnostic_focus": diagnostic_for_kind(spec.kind),
        "amplitude": spec.amplitude,
        "frequency": spec.frequency,
        "phase": spec.phase,
        "noise": spec.noise,
        "bias": spec.bias,
        "drift": spec.drift,
        "coupling_group": "" if spec.coupling_group is None else spec.coupling_group,
        "relation_weight": spec.relation_weight,
        "description": spec.description,
    }


def _lane_target_rows(specs: list[CandidateSpec]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for lane in sorted({expected_lane_for_kind(spec.kind) for spec in specs}):
        members = [spec for spec in specs if expected_lane_for_kind(spec.kind) == lane]
        rows.append(
            {
                "expected_lane": lane,
                "candidate_count": len(members),
                "candidate_ids": ",".join(spec.candidate_id for spec in members),
                "primary_purpose": _lane_purpose(lane),
            }
        )
    return rows


def _lane_purpose(lane: str) -> str:
    if lane.startswith("+1"):
        return "positive control; prove the witness is not dead-safe"
    if lane.startswith("-1"):
        return "negative control; prove traps still demote"
    if "relation debt" in lane:
        return "make relation debt visible as structured zero"
    if "return debt" in lane:
        return "make return debt visible as structured zero"
    return "witness-hold pressure"


def _preview_rows(*, seed: int, steps: int, dt: float) -> list[dict[str, object]]:
    specs = candidate_specs(PROFILE_NAME)
    run = generate_pressure_field(seed=seed, n_steps=steps, dt=dt, specs=specs)
    rows = evaluate_run(run, strength_threshold=0.40)
    out: list[dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "candidate_id": row.candidate_id,
                "kind": row.kind,
                "truth_role": row.truth_role,
                "expected_lane": expected_lane_for_kind(row.kind),
                "preview_trinary_value": row.trinary_value,
                "preview_trinary_outcome": row.trinary_outcome,
                "preview_zero_band": row.zero_band,
                "preview_zero_band_reason": row.zero_band_reason,
                "strength": row.strength,
                "distinction": row.distinction,
                "polarity": row.polarity,
                "relation": row.relation,
                "return_observed": row.return_observed,
                "return_potential": row.return_potential,
                "zero_coherence": row.zero_coherence,
                "zero_depth": row.zero_depth,
                "limiting_gate": row.limiting_gate,
            }
        )
    return out


def _decision(specs: list[CandidateSpec]) -> str:
    lanes = {expected_lane_for_kind(spec.kind) for spec in specs}
    required = {"+1 earned-one", "-1 false-one demotion", "0 relation debt", "0 return debt"}
    if not required.issubset(lanes):
        return "hold_debt_candidate_generator_missing_required_lane"
    if len([spec for spec in specs if spec.truth_role == "latent"]) < 5:
        return "hold_debt_candidate_generator_insufficient_zero_candidates"
    return "hold_debt_candidate_generator_ready_for_triad27_debt_evidence"


def _write_read(path: Path, *, specs: list[CandidateSpec], decision: str, seed: int, steps: int) -> None:
    lane_rows = _lane_target_rows(specs)
    lines = [
        "# Four Gates Debt Candidate Generator",
        "",
        f"**Version:** `{CURRENT_VERSION}`",
        "**Status:** generator implementation gate, not heavy evidence",
        "**Boundary:** no Zenodo route, no shadow revival, no observed-universe bridge, no spacetime metric claim",
        "",
        "## Native witness",
        "",
        "```text",
        NATIVE_WITNESS,
        "```",
        "",
        "This version implements debt-shaped candidate families without changing the native witness law. The candidates are near-success states: structured enough to hold, incomplete enough not to crown, and wrong to demote.",
        "",
        "## Decision",
        "",
        "```text",
        decision,
        "```",
        "",
        "## Candidate profile",
        "",
        f"Matrix runs can now use `--candidate-profile {PROFILE_NAME}`.",
        "",
        "## Expected lanes",
        "",
        "| expected lane | candidates | ids | purpose |",
        "|---|---:|---|---|",
    ]
    for row in lane_rows:
        lines.append(f"| {row['expected_lane']} | {row['candidate_count']} | {row['candidate_ids']} | {row['primary_purpose']} |")
    lines.extend(
        [
            "",
            "## Candidate families",
            "",
            "| id | kind | role | expected lane | diagnostic focus | description |",
            "|---|---|---|---|---|---|",
        ]
    )
    for spec in specs:
        lines.append(
            f"| {spec.candidate_id} | {spec.kind} | {spec.truth_role} | {expected_lane_for_kind(spec.kind)} | "
            f"{diagnostic_for_kind(spec.kind)} | {spec.description} |"
        )
    lines.extend(
        [
            "",
            "## Preview run",
            "",
            f"A small preview is written using seed `{seed}` and `{steps}` steps. It is a generator sanity check, not a claim that debt evidence passed.",
            "",
            "## Next gate",
            "",
            "`v1.6.20-alpha` should run four-corpus `triad27` debt evidence using this profile. Pass requires earned-one preservation, false-one demotion, visible relation debt, visible return debt, ablation wounds, and zero final false-one crowns.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_four_gates_debt_candidate_generator_report(*, output_dir: Path, seed: int = 19, steps: int = 240, dt: float = 0.05) -> dict[str, Path]:
    output_dir = ensure_dir(output_dir)
    specs = candidate_specs(PROFILE_NAME)
    spec_rows = [_spec_row(spec) for spec in specs]
    lane_rows = _lane_target_rows(specs)
    preview_rows = _preview_rows(seed=seed, steps=steps, dt=dt)
    decision = _decision(specs)

    read_md = output_dir / OUTPUT_FILES["read"]
    decision_json = output_dir / OUTPUT_FILES["decision"]
    specs_csv = output_dir / OUTPUT_FILES["candidate_specs"]
    lanes_csv = output_dir / OUTPUT_FILES["lane_targets"]
    preview_csv = output_dir / OUTPUT_FILES["preview_scores"]
    audit_json = output_dir / OUTPUT_FILES["audit"]

    write_dict_rows_csv(specs_csv, spec_rows)
    write_dict_rows_csv(lanes_csv, lane_rows)
    write_dict_rows_csv(preview_csv, preview_rows)
    _write_read(read_md, specs=specs, decision=decision, seed=seed, steps=steps)
    decision_doc = {
        "version": CURRENT_VERSION,
        "global_decision": decision,
        "native_witness_unchanged": NATIVE_WITNESS,
        "candidate_profile": PROFILE_NAME,
        "candidate_count": len(specs),
        "expected_lanes": [row["expected_lane"] for row in lane_rows],
        "matrix_profile_ready": True,
        "heavy_evidence_run_completed": False,
        "zenodo_route_allowed": False,
        "shadow_route_status": "historical_hold",
        "observed_universe_bridge_allowed": False,
        "next_gate": "v1.6.20-alpha four-corpus triad27 debt evidence",
    }
    decision_json.write_text(json.dumps(decision_doc, indent=2), encoding="utf-8")
    audit = {
        "output_files": OUTPUT_FILES,
        "preview_seed": seed,
        "preview_steps": steps,
        "preview_dt": dt,
        "candidate_profile_registered": PROFILE_NAME,
        "native_witness_mutated": False,
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle = write_evidence_bundle(output_dir, bundle_name=OUTPUT_FILES["bundle"], bundle_kind="zerogate_four_gates_debt_candidate_generator_bundle")
    return {
        "read": read_md,
        "decision": decision_json,
        "candidate_specs": specs_csv,
        "lane_targets": lanes_csv,
        "preview_scores": preview_csv,
        "audit": audit_json,
        "bundle": bundle,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Four Gates debt candidate generator report.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    parser.add_argument("--seed", type=int, default=19, help="Preview seed; not a heavy evidence claim.")
    parser.add_argument("--steps", type=int, default=240, help="Preview step count; not a heavy evidence claim.")
    parser.add_argument("--dt", type=float, default=0.05, help="Preview dt.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = write_four_gates_debt_candidate_generator_report(output_dir=args.out, seed=args.seed, steps=args.steps, dt=args.dt)
    print(f"[four-gates-debt-generator] wrote {paths['read']}")
    print(f"[four-gates-debt-generator] bundle {paths['bundle']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
