from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from dataclasses import fields
from pathlib import Path
from typing import Iterable, Sequence

from zerogate_sim.final_output import build_final_output_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv
from zerogate_sim.seed_block_report import NATIVE_GATE_NAMES, read_matrix, write_seed_block_report
from zerogate_sim.shadow_feature_design import SHADOW_ENGINEERED_FEATURE_COLUMNS, with_engineered_shadow_features
from zerogate_sim.shadow_score_report import write_shadow_score_report
from zerogate_sim.shadow_weather_hardening_report import write_shadow_weather_hardening_report

HARDENED_FILES = {
    "cell_features": "triad27_hardened_cell_features.csv",
    "cell_targets": "triad27_hardened_cell_targets.csv",
    "read": "triad27_hardened_evidence_read.md",
    "audit": "triad27_hardened_evidence_audit.json",
    "bundle": "triad27_hardened_evidence_bundle.zip",
}

FEATURES_DIR = "role_stripped"
SCORE_DIR = "shadow_score"
SEED_BLOCK_DIR = "seed_block"
HARDENING_DIR = "weather_hardening"

FORBIDDEN_FEATURE_FIELDS = {
    "gate",
    "truth_role",
    "candidate_profile",
    "role_label",
    "trap",
    "expresser",
    "latent_probe",
    "designed_truth_role",
    "answer_key",
    "evaluation_family_label",
}

GATE_SCORE_FIELDS = {field.name for field in fields(GateScores)}


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: object, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value if value not in {None, ""} else default)
    except (TypeError, ValueError):
        return default


def _rate(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return "0.000000"
    return f"{numerator / denominator:.6f}"


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _opaque_family_id(*, source_label: str, gate: str, scenario: str, row: dict[str, object]) -> str:
    payload = {
        "source_label": source_label,
        "source_profile": "triad27",
        "scenario": scenario,
        "total_runs": str(row.get("total_runs", "")),
        "raw_pressure": str(row.get("raw_expression_pressure", "")),
        "latent_pressure": str(row.get("latent_overcrown_pressure", "")),
        "relation_debt": str(row.get("relation_debt_count", "")),
        "mean_strength": str(row.get("mean_strength", "")),
        "mean_zero_coherence": str(row.get("mean_zero_coherence", "")),
        "gate_digest_salt": hashlib.sha256(gate.encode("utf-8")).hexdigest()[:8],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]
    return f"{source_label}_cell_{digest}"


def _gate_score_from_row(row: dict[str, str], *, scenario: str) -> GateScores:
    kwargs: dict[str, object] = {}
    for name in GATE_SCORE_FIELDS:
        raw = row.get(name, "")
        if name == "candidate_id":
            kwargs[name] = f"{scenario}:{raw}"
        elif name in {"designed_stable", "expressed", "observed_stable"}:
            kwargs[name] = _bool(raw)
        elif name in {"expected_trinary", "zero_depth", "trinary_value", "zero_band_value"}:
            kwargs[name] = _int(raw)
        elif name in {
            "strength",
            "distinction",
            "polarity",
            "relation",
            "return_observed",
            "return_potential",
            "echo_mimic_score",
            "zero_coherence",
            "latent_score",
            "observed_stability_score",
        }:
            kwargs[name] = _float(raw)
        else:
            kwargs[name] = raw
    return GateScores(**kwargs)  # type: ignore[arg-type]


def _scenario_seed_dirs(matrix_dir: Path, scenario: str) -> list[Path]:
    scenario_dir = matrix_dir / scenario
    if not scenario_dir.exists():
        raise FileNotFoundError(f"Missing scenario directory: {scenario_dir}")
    seed_dirs = sorted(path for path in scenario_dir.iterdir() if path.is_dir() and (path / "gate_scores.csv").exists())
    if not seed_dirs:
        raise FileNotFoundError(f"No seed gate_scores.csv files found under: {scenario_dir}")
    return seed_dirs


def _cell_gate_scores(matrix_dir: Path, scenario: str) -> list[tuple[int, GateScores]]:
    rows: list[tuple[int, GateScores]] = []
    for seed_dir in _scenario_seed_dirs(matrix_dir, scenario):
        seed = _int(seed_dir.name.replace("seed_", ""))
        for row in _read_csv(seed_dir / "gate_scores.csv"):
            rows.append((seed, _gate_score_from_row(row, scenario=scenario)))
    return rows


def _scenario_axis_rows(matrix_dir: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv(matrix_dir / "matrix_scenario_summary.csv")
    return {str(row.get("scenario", "")): row for row in rows}


def _final_false_one_crowns(final_rows: list[dict[str, object]]) -> int:
    return sum(
        int(row.get("raw_false_one_pressure", 0) or 0)
        for row in final_rows
        if str(row.get("truth_role", "")) == "trap" and int(row.get("final_trinary_value", 0) or 0) == 1
    )


def _cell_summary(*, source_label: str, gate: str, matrix_dir: Path, scenario: str, axis_row: dict[str, str]) -> dict[str, object]:
    gate_rows = _cell_gate_scores(matrix_dir, scenario)
    final_rows = build_final_output_rows(gate_rows)
    denominator = len({seed for seed, _ in gate_rows})
    candidate_count = len({row.candidate_id for _, row in gate_rows})

    raw_expression = sum(int(row["raw_expression_pressure"]) for row in final_rows)
    earned = sum(int(row["final_earned_one_count"]) for row in final_rows)
    raw_false = sum(int(row["raw_false_one_pressure"]) for row in final_rows)
    false_demoted = sum(int(row["false_one_demoted_count"]) for row in final_rows)
    latent = sum(int(row["latent_overcrown_pressure"]) for row in final_rows)
    latent_demoted = sum(int(row["latent_overcrown_demoted_count"]) for row in final_rows)
    relation_debt = sum(int(row["relation_debt_count"]) for row in final_rows)
    final_false = _final_false_one_crowns(final_rows)

    all_scores = [row for _, row in gate_rows]
    mean_strength = _mean([row.strength for row in all_scores])
    mean_zero = _mean([row.zero_coherence for row in all_scores])
    mean_relation = _mean([row.relation for row in all_scores])
    mean_return = _mean([row.return_observed for row in all_scores])
    mean_weakest_pressure = _mean([1.0 - row.zero_coherence for row in all_scores])
    raw_strength_pressure = _mean([row.strength for row in all_scores if row.expressed]) if raw_expression else 0.0
    limiting_return_count = sum(1 for row in all_scores if row.limiting_gate == "return")
    limiting_relation_count = sum(1 for row in all_scores if row.limiting_gate == "relation")

    out: dict[str, object] = {
        "source_label": source_label,
        "source_profile": "triad27",
        "gate": gate,
        "scenario": scenario,
        "noise_axis": axis_row.get("noise_axis", ""),
        "relation_axis": axis_row.get("relation_axis", ""),
        "expansion_axis": axis_row.get("expansion_axis", ""),
        "perturbation_axis": axis_row.get("perturbation_axis", ""),
        "time_axis": axis_row.get("time_axis", ""),
        "total_runs": denominator,
        "candidate_count": candidate_count,
        "raw_expression_pressure": raw_expression,
        "final_earned_one_events": earned,
        "raw_false_one_pressure": raw_false,
        "false_one_demoted_count": false_demoted,
        "latent_overcrown_pressure": latent,
        "latent_overcrown_demoted_count": latent_demoted,
        "relation_debt_count": relation_debt,
        "final_false_one_crowns": final_false,
        "trap_final_crowns": final_false,
        "mean_strength": f"{mean_strength:.6f}",
        "mean_zero_coherence": f"{mean_zero:.6f}",
        "mean_relation": f"{mean_relation:.6f}",
        "mean_return": f"{mean_return:.6f}",
        "mean_weakest_gate_pressure": f"{mean_weakest_pressure:.6f}",
        "raw_strength_pressure": f"{raw_strength_pressure:.6f}",
        "limiting_return_count": limiting_return_count,
        "limiting_relation_count": limiting_relation_count,
    }
    out["family_id"] = _opaque_family_id(source_label=source_label, gate=gate, scenario=scenario, row=out)
    return out


def _collect_cell_rows(matrix_dirs: Iterable[Path], *, source_label: str = "triad27") -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    seen_gates: set[str] = set()
    for matrix_dir in matrix_dirs:
        ident = read_matrix(Path(matrix_dir))
        if ident.profile != "triad27":
            raise ValueError(f"Expected triad27 matrix profile, got {ident.profile}: {matrix_dir}")
        if ident.gate not in set(NATIVE_GATE_NAMES):
            raise ValueError(f"Cannot infer native gate for matrix directory: {matrix_dir}")
        if ident.gate in seen_gates:
            raise ValueError(f"Duplicate native gate matrix coverage: {ident.gate}")
        seen_gates.add(ident.gate)
        axis_by_scenario = _scenario_axis_rows(Path(matrix_dir))
        for scenario in sorted(axis_by_scenario):
            out.append(_cell_summary(source_label=source_label, gate=ident.gate, matrix_dir=Path(matrix_dir), scenario=scenario, axis_row=axis_by_scenario[scenario]))
    missing = [gate for gate in NATIVE_GATE_NAMES if gate not in seen_gates]
    if missing:
        raise ValueError("Missing native gate matrix coverage: " + ", ".join(missing))
    return out


def _profile_feature_row(cell_rows: list[dict[str, object]], *, source_label: str = "triad27") -> dict[str, object]:
    total_runs = sum(_int(row.get("total_runs")) for row in cell_rows)
    raw = sum(_int(row.get("raw_expression_pressure")) for row in cell_rows)
    earned = sum(_int(row.get("final_earned_one_events")) for row in cell_rows)
    latent = sum(_int(row.get("latent_overcrown_pressure")) for row in cell_rows)
    relation_debt = sum(_int(row.get("relation_debt_count")) for row in cell_rows)
    mean_strength = _mean([_float(row.get("mean_strength")) for row in cell_rows])
    mean_weakest = _mean([_float(row.get("mean_weakest_gate_pressure")) for row in cell_rows])
    mean_relation = _mean([_float(row.get("mean_relation")) for row in cell_rows])
    mean_return = _mean([_float(row.get("mean_return")) for row in cell_rows])
    return {
        "source_label": source_label,
        "source_profile": "triad27_hardened_cell",
        "family_count": len(cell_rows),
        "total_runs": total_runs,
        "feature_earned_rate": _rate(earned, total_runs),
        "feature_raw_pressure_rate": _rate(raw, total_runs),
        "feature_latent_hold_rate": _rate(latent, total_runs),
        "feature_relation_debt_rate": _rate(relation_debt, total_runs),
        "feature_mirror_primary_rate": "0.000000",
        "feature_mirror_secondary_rate": "0.000000",
        "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
        "feature_ablation_demotion_dependence_rate": "0.000000",
        "feature_ablation_latent_hold_dependence_rate": "0.000000",
        "feature_ablation_echo_independence_rate": "0.000000",
        "feature_raw_strength_pressure_rate": f"{mean_strength:.6f}",
        "feature_weakest_gate_pressure_rate": f"{mean_weakest:.6f}",
        "feature_relation_gate_rate": f"{mean_relation:.6f}",
        "feature_return_gate_rate": f"{mean_return:.6f}",
        "boundary": "triad27_hardened_profile_role_stripped_no_gate_labels",
    }


def _profile_target_row(cell_rows: list[dict[str, object]], *, source_label: str = "triad27") -> dict[str, object]:
    total_runs = sum(_int(row.get("total_runs")) for row in cell_rows)
    raw_false = sum(_int(row.get("raw_false_one_pressure")) for row in cell_rows)
    false_demoted = sum(_int(row.get("false_one_demoted_count")) for row in cell_rows)
    final_false = sum(_int(row.get("final_false_one_crowns")) for row in cell_rows)
    latent = sum(_int(row.get("latent_overcrown_pressure")) for row in cell_rows)
    latent_demoted = sum(_int(row.get("latent_overcrown_demoted_count")) for row in cell_rows)
    relation_debt = sum(_int(row.get("relation_debt_count")) for row in cell_rows)
    relation_false = sum(_int(row.get("raw_false_one_pressure")) for row in cell_rows if row.get("gate") == "relation")
    return_false = sum(_int(row.get("raw_false_one_pressure")) for row in cell_rows if row.get("gate") == "return")
    return {
        "source_label": source_label,
        "source_profile": "triad27_hardened_cell",
        "total_runs": total_runs,
        "target_raw_false_one_rate": _rate(raw_false, total_runs),
        "target_false_one_demotion_rate": _rate(false_demoted, total_runs),
        "target_final_false_crown_rate": _rate(final_false, total_runs),
        "target_relation_false_pressure_share": _rate(relation_false, raw_false),
        "target_false_pressure_density_rate": _rate(raw_false + latent + relation_debt, total_runs),
        "target_hold_or_demote_rate": _rate(false_demoted + latent_demoted, total_runs),
        "target_return_false_pressure_share": _rate(return_false, raw_false),
        "target_native_breach_rate": _rate(final_false, total_runs),
        "boundary": "triad27_hardened_targets_loaded_after_scoring_only",
    }


def _family_feature_rows(cell_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in cell_rows:
        total_runs = _int(row.get("total_runs"))
        rows.append(
            {
                "source_label": row["source_label"],
                "source_profile": "triad27_hardened_cell",
                "family_id": row["family_id"],
                "weather_cell": row["scenario"],
                "noise_axis": row["noise_axis"],
                "relation_axis": row["relation_axis"],
                "expansion_axis": row["expansion_axis"],
                "total_runs": total_runs,
                "feature_earned_rate": _rate(_int(row.get("final_earned_one_events")), total_runs),
                "feature_raw_pressure_rate": _rate(_int(row.get("raw_expression_pressure")), total_runs),
                "feature_latent_hold_rate": _rate(_int(row.get("latent_overcrown_pressure")), total_runs),
                "feature_relation_debt_rate": _rate(_int(row.get("relation_debt_count")), total_runs),
                "feature_mirror_primary_rate": "0.000000",
                "feature_mirror_secondary_rate": "0.000000",
                "feature_ablation_raw_as_final_crown_risk_rate": "0.000000",
                "feature_ablation_demotion_dependence_rate": "0.000000",
                "feature_ablation_latent_hold_dependence_rate": "0.000000",
                "feature_ablation_echo_independence_rate": "0.000000",
                "feature_raw_strength_pressure_rate": row.get("raw_strength_pressure", "0.000000"),
                "feature_weakest_gate_pressure_rate": row.get("mean_weakest_gate_pressure", "0.000000"),
                "feature_relation_gate_rate": row.get("mean_relation", "0.000000"),
                "feature_return_gate_rate": row.get("mean_return", "0.000000"),
                "feature_return_limiting_rate": _rate(_int(row.get("limiting_return_count")), total_runs * max(1, _int(row.get("candidate_count")))),
                "feature_relation_limiting_rate": _rate(_int(row.get("limiting_relation_count")), total_runs * max(1, _int(row.get("candidate_count")))),
                "boundary": "triad27_hardened_cell_role_stripped_no_native_gate_label",
            }
        )
    return sorted(rows, key=lambda item: str(item["family_id"]))


def _family_target_rows(cell_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in cell_rows:
        total_runs = _int(row.get("total_runs"))
        raw_false = _int(row.get("raw_false_one_pressure"))
        false_demoted = _int(row.get("false_one_demoted_count"))
        latent = _int(row.get("latent_overcrown_pressure"))
        latent_demoted = _int(row.get("latent_overcrown_demoted_count"))
        relation_debt = _int(row.get("relation_debt_count"))
        final_false = _int(row.get("final_false_one_crowns"))
        rows.append(
            {
                "source_label": row["source_label"],
                "family_id": row["family_id"],
                "evaluation_family_label": f"{row['gate']}:{row['scenario']}",
                "target_raw_false_one_rate": _rate(raw_false, total_runs),
                "target_false_one_demotion_rate": _rate(false_demoted, total_runs),
                "target_final_false_crown_rate": _rate(final_false, total_runs),
                "target_relation_false_pressure_share": _rate(raw_false if row.get("gate") == "relation" else 0, raw_false),
                "target_false_pressure_density_rate": _rate(raw_false + latent + relation_debt, total_runs),
                "target_hold_or_demote_rate": _rate(false_demoted + latent_demoted, total_runs),
                "target_return_false_pressure_share": _rate(raw_false if row.get("gate") == "return" else 0, raw_false),
                "target_native_breach_rate": _rate(final_false, total_runs),
                "boundary": "triad27_hardened_cell_target_separate_from_role_stripped_features",
            }
        )
    return sorted(rows, key=lambda item: str(item["family_id"]))


def _write_role_stripped_files(output_dir: Path, cell_rows: list[dict[str, object]]) -> dict[str, Path]:
    role_dir = _ensure_dir(output_dir / FEATURES_DIR)
    profile_features = [with_engineered_shadow_features(_profile_feature_row(cell_rows))]
    family_features = [with_engineered_shadow_features(row) for row in _family_feature_rows(cell_rows)]
    targets = [_profile_target_row(cell_rows)] + _family_target_rows(cell_rows)

    profile_path = role_dir / "role_stripped_profile_features.csv"
    family_path = role_dir / "role_stripped_family_features.csv"
    target_path = role_dir / "role_stripped_evaluation_targets.csv"
    read_path = role_dir / "role_stripped_feature_read.md"
    audit_path = role_dir / "role_stripped_forbidden_field_audit.json"
    bundle_path = role_dir / "role_stripped_feature_bundle.zip"

    _write_csv(profile_path, profile_features)
    _write_csv(family_path, family_features)
    _write_csv(target_path, targets)

    feature_headers = set(family_features[0].keys()) | set(profile_features[0].keys())
    forbidden = sorted(feature_headers & FORBIDDEN_FEATURE_FIELDS)
    audit = {
        "feature_files_role_stripped": not forbidden,
        "forbidden_feature_fields_found": forbidden,
        "family_rows_are_cell_level": True,
        "family_row_count": len(family_features),
        "target_rows_loaded_after_scoring_only": True,
        "exact_baseline_fields_present": [
            "feature_raw_strength_pressure_rate",
            "feature_weakest_gate_pressure_rate",
            "feature_relation_gate_rate",
            "feature_return_gate_rate",
        ],
        "engineered_shadow_feature_columns": sorted(SHADOW_ENGINEERED_FEATURE_COLUMNS),
        "feature_design_boundary": "v1.6.12 feature candidates are role-stripped observable columns computed before target loading",
        "boundary": "v1.6.8 hardens triad27 by evaluating cell-level weather families; feature rows do not expose native gate labels or truth roles",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        "# ZeroGateSim Triad27 Hardened Role-Stripped Features",
        "",
        "This directory is generated by `v1.6.8-alpha` hardened triad27 evidence. It converts four native triad27 matrix runs into cell-level role-stripped family rows before shadow scoring.",
        "",
        "Feature rows may include observable weather axes, pressure rates, exact baseline fields, and v1.6.12 engineered feature candidates. They must not include native gate labels, truth roles, candidate profiles, answer keys, or target fields.",
        "",
        "The target file keeps the native gate/scenario label only as `evaluation_family_label`, after scoring, so the shadow score cannot read it as an input.",
        "",
        f"Family rows: `{len(family_features)}`",
        f"Target rows: `{len(targets)}`",
        "",
        "Native witness unchanged:",
        "",
        "```text",
        "C_Z = min(D, P, R, B)",
        "```",
        "",
    ]
    read_path.write_text("\n".join(lines), encoding="utf-8")
    _write_bundle(role_dir, bundle_path)
    return {
        "role_stripped_profile_features": profile_path,
        "role_stripped_family_features": family_path,
        "role_stripped_evaluation_targets": target_path,
        "role_stripped_feature_read": read_path,
        "role_stripped_forbidden_field_audit": audit_path,
        "role_stripped_feature_bundle": bundle_path,
    }


def _write_bundle(base_dir: Path, bundle_path: Path) -> Path:
    manifest_path = base_dir / "bundle_manifest.json"
    files = sorted(path for path in base_dir.rglob("*") if path.is_file() and path != bundle_path and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_triad27_hardened_evidence_bundle",
        "file_count_excluding_manifest": len([path for path in files if path != manifest_path]),
        "files": [
            {"path": path.relative_to(base_dir).as_posix(), "size_bytes": path.stat().st_size}
            for path in files
            if path != manifest_path
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    files = sorted(path for path in base_dir.rglob("*") if path.is_file() and path != bundle_path)
    if bundle_path.exists():
        bundle_path.unlink()
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.relative_to(base_dir).as_posix())
    return bundle_path


def _write_read(path: Path, *, cell_rows: list[dict[str, object]], hardening_decision_path: Path) -> None:
    total_runs = sum(_int(row.get("total_runs")) for row in cell_rows)
    raw_false = sum(_int(row.get("raw_false_one_pressure")) for row in cell_rows)
    final_false = sum(_int(row.get("final_false_one_crowns")) for row in cell_rows)
    cells = len(cell_rows)
    lines = [
        "# ZeroGateSim Shadow Triad27 Hardened Evidence",
        "",
        "## Claim boundary",
        "",
        "This `v1.6.8-alpha` report is the first harder triad27 battlefield for the shadow line. It does not retune the shadow score and does not claim role-blind discovery.",
        "",
        "It takes four native triad27 matrix runs — distinction, polarity, relation, and return — and converts them into cell-level role-stripped family rows. The goal is to stop a four-family summary from hiding trivial baseline ties.",
        "",
        "Native witness remains:",
        "",
        "```text",
        "C_Z = min(D, P, R, B)",
        "```",
        "",
        "## Weather rung",
        "",
        "```text",
        "triad27 = 3^3 local expression weather",
        "```",
        "",
        "## Evidence generated",
        "",
        f"Cell-level family rows: `{cells}`",
        f"Total matrix runs represented across cell rows: `{total_runs}`",
        f"Raw false-one pressure events: `{raw_false}`",
        f"Final false-one crowns: `{final_false}`",
        "",
        "## Harder judge",
        "",
        "The generated evidence base immediately runs `zerogate-shadow-weather-hardening` against itself with required rung `triad27`. The hardening decision is written to:",
        "",
        f"`{hardening_decision_path.as_posix()}`",
        "",
        "If the shadow score is merely tied by raw pressure, weakest gate, relation gate, return gate, or other dumb baselines, the hardening report must call that witness/resist — not victory.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_shadow_triad27_hardened_evidence_report(*, output_dir: Path, matrix_dirs: Iterable[Path]) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    matrix_dirs = [Path(path) for path in matrix_dirs]
    if not matrix_dirs:
        raise ValueError("At least one completed matrix directory is required.")

    seed_paths = write_seed_block_report(output_dir=output_dir / SEED_BLOCK_DIR, matrix_dirs=matrix_dirs, require_four_gates=True)
    cell_rows = _collect_cell_rows(matrix_dirs, source_label="triad27")

    cell_dir = _ensure_dir(output_dir / "cell_evidence")
    cell_features_path = cell_dir / HARDENED_FILES["cell_features"]
    cell_targets_path = cell_dir / HARDENED_FILES["cell_targets"]
    _write_csv(cell_features_path, [with_engineered_shadow_features(row) for row in _family_feature_rows(cell_rows)])
    _write_csv(cell_targets_path, _family_target_rows(cell_rows))

    role_paths = _write_role_stripped_files(output_dir, cell_rows)
    score_paths = write_shadow_score_report(
        output_dir=output_dir / SCORE_DIR,
        profile_features=role_paths["role_stripped_profile_features"],
        family_features=role_paths["role_stripped_family_features"],
    )
    hardening_paths = write_shadow_weather_hardening_report(
        output_dir=output_dir / HARDENING_DIR,
        sources={"triad27": output_dir},
        required_rungs=("triad27",),
    )

    read_path = output_dir / HARDENED_FILES["read"]
    audit_path = output_dir / HARDENED_FILES["audit"]
    bundle_path = output_dir / HARDENED_FILES["bundle"]
    _write_read(read_path, cell_rows=cell_rows, hardening_decision_path=hardening_paths["weather_hardening_decision"])
    audit = {
        "version": "v1.6.12-alpha",
        "base_report_lineage": "v1.6.8-alpha hardened triad27 generator with v1.6.12 engineered features",
        "report_name": "shadow_triad27_hardened_evidence_report",
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "score_freeze_boundary": "the current transparent shadow score is scored before targets are joined; no score retuning in this report",
        "role_blind_boundary": "harder triad27 evidence only; not role-blind discovery and not detector closeout",
        "matrix_dirs": [str(path) for path in matrix_dirs],
        "cell_family_rows": len(cell_rows),
        "generated_standard_base_paths": [SEED_BLOCK_DIR, FEATURES_DIR, SCORE_DIR, HARDENING_DIR],
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    _write_bundle(output_dir, bundle_path)

    paths: dict[str, Path] = {
        "triad27_hardened_evidence_read": read_path,
        "triad27_hardened_evidence_audit": audit_path,
        "triad27_hardened_evidence_bundle": bundle_path,
        "triad27_hardened_cell_features": cell_features_path,
        "triad27_hardened_cell_targets": cell_targets_path,
    }
    paths.update(seed_paths)
    paths.update(role_paths)
    paths.update(score_paths)
    paths.update(hardening_paths)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a harder cell-level triad27 evidence base for the shadow line and immediately run weather hardening on it.")
    parser.add_argument("--matrix-dir", action="append", type=Path, default=[], help="Completed triad27 matrix directory. Supply distinction, polarity, relation, and return.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_triad27_hardened_evidence_v1_6_8"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_shadow_triad27_hardened_evidence_report(output_dir=args.out, matrix_dirs=args.matrix_dir)
    print("ZeroGateSim shadow triad27 hardened evidence complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
