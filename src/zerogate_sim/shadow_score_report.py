from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Iterable

from zerogate_sim.role_stripped_feature_report import FORBIDDEN_SHADOW_INPUT_FIELDS

SHADOW_SCORE_FILES = {
    "profile_scores": "shadow_score_profile_scores.csv",
    "family_scores": "shadow_score_family_scores.csv",
    "read": "shadow_score_read.md",
    "formula": "shadow_score_formula.json",
    "audit": "shadow_score_forbidden_field_audit.json",
    "bundle": "shadow_score_bundle.zip",
}

# Transparent report-side weights. They are deliberately simple so the first
# prototype can be inspected and falsified before any learned detector exists.
SHADOW_SCORE_WEIGHTS: dict[str, float] = {
    "feature_raw_pressure_rate": 0.14,
    "feature_latent_hold_rate": 0.16,
    "feature_relation_debt_rate": 0.06,
    "feature_mirror_primary_rate": 0.12,
    "feature_mirror_secondary_rate": 0.06,
    "feature_ablation_raw_as_final_crown_risk_rate": 0.18,
    "feature_ablation_demotion_dependence_rate": 0.18,
    "feature_ablation_latent_hold_dependence_rate": 0.08,
    "feature_ablation_echo_independence_rate": 0.02,
}

# v1.6.10-alpha adds fixed lane-specific candidate scores. These do not
# replace the historical frozen shadow_score above and they are not learned or
# retuned against targets. They split the report-side pressure witness into
# candidate lanes so later discrimination reports can ask whether any lane sees
# pressure kind beyond raw intensity and dumb baselines.
SHADOW_LANE_SCORE_WEIGHTS: dict[str, dict[str, float]] = {
    "shadow_density_pressure_score": {
        "feature_raw_pressure_rate": 0.40,
        "feature_latent_hold_rate": 0.25,
        "feature_relation_debt_rate": 0.20,
        "feature_weakest_gate_pressure_rate": 0.15,
    },
    "shadow_raw_false_one_pressure_score": {
        "feature_raw_pressure_rate": 0.35,
        "feature_raw_strength_pressure_rate": 0.20,
        "feature_weakest_gate_pressure_rate": 0.20,
        "feature_ablation_raw_as_final_crown_risk_rate": 0.15,
        "feature_relation_debt_rate": 0.10,
    },
    "shadow_demotion_pressure_score": {
        "feature_raw_pressure_rate": 0.30,
        "feature_latent_hold_rate": 0.20,
        "feature_ablation_demotion_dependence_rate": 0.25,
        "feature_ablation_raw_as_final_crown_risk_rate": 0.15,
        "feature_weakest_gate_pressure_rate": 0.10,
    },
    "shadow_hold_or_demote_pressure_score": {
        "feature_latent_hold_rate": 0.35,
        "feature_raw_pressure_rate": 0.25,
        "feature_relation_debt_rate": 0.20,
        "feature_weakest_gate_pressure_rate": 0.10,
        "feature_ablation_demotion_dependence_rate": 0.10,
    },
    "shadow_relation_specific_pressure_score": {
        "feature_relation_debt_rate": 0.30,
        "feature_relation_gate_rate": 0.25,
        "feature_relation_limiting_rate": 0.25,
        "feature_ablation_echo_independence_rate": 0.15,
        "feature_mirror_secondary_rate": 0.05,
    },
    "shadow_return_specific_pressure_score": {
        "feature_return_limiting_rate": 0.35,
        "feature_return_gate_inverse_rate": 0.25,
        "feature_weakest_gate_pressure_rate": 0.20,
        "feature_raw_pressure_rate": 0.15,
        "feature_latent_hold_rate": 0.05,
    },
    "shadow_native_breach_proxy_score": {
        "feature_weakest_gate_pressure_rate": 0.35,
        "feature_raw_pressure_rate": 0.25,
        "feature_raw_strength_pressure_rate": 0.20,
        "feature_return_limiting_rate": 0.10,
        "feature_relation_limiting_rate": 0.10,
    },
}

SCORE_LANE_LABELS: dict[str, str] = {
    "shadow_density_pressure_score": "density_pressure",
    "shadow_raw_false_one_pressure_score": "raw_false_one",
    "shadow_demotion_pressure_score": "demotion",
    "shadow_hold_or_demote_pressure_score": "hold_or_demote",
    "shadow_relation_specific_pressure_score": "relation_specific",
    "shadow_return_specific_pressure_score": "return_specific",
    "shadow_native_breach_proxy_score": "native_breach_proxy",
}


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


def _float(row: dict[str, object], key: str) -> float:
    try:
        return float(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalise_pressure(value: float) -> float:
    """Saturating transform for rates that may exceed 1.0, such as mirror pressure."""
    value = max(0.0, float(value))
    return value / (1.0 + value) if value else 0.0


def _feature_pressure(row: dict[str, str], feature: str) -> float:
    """Return a bounded pressure value for ordinary and inverse lane features."""
    if feature == "feature_return_gate_inverse_rate":
        # Higher return gate means less return-failure pressure. Treat the
        # inverse as a transparent report-side pressure proxy, not a native gate.
        return max(0.0, min(1.0, 1.0 - _float(row, "feature_return_gate_rate")))
    return _normalise_pressure(_float(row, feature))


def _band(score: float) -> str:
    if score >= 0.35:
        return "high_pressure_watch"
    if score >= 0.18:
        return "pressure_watch"
    if score >= 0.08:
        return "weak_watch"
    return "quiet_watch"


def _forbidden_header_fields(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    header = set(rows[0].keys())
    return sorted(header & FORBIDDEN_SHADOW_INPUT_FIELDS)


def assert_role_stripped_rows(rows: list[dict[str, str]], *, source_name: str) -> None:
    forbidden = _forbidden_header_fields(rows)
    if forbidden:
        raise ValueError(f"Forbidden role/answer-key fields in {source_name}: {', '.join(forbidden)}")


def _lane_scores(row: dict[str, str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for score_name, weights in SHADOW_LANE_SCORE_WEIGHTS.items():
        scores[score_name] = sum(weight * _feature_pressure(row, feature) for feature, weight in weights.items())
    return scores


def _score_row(row: dict[str, str], *, scope: str) -> dict[str, object]:
    contributions: dict[str, float] = {}
    for feature, weight in SHADOW_SCORE_WEIGHTS.items():
        contributions[feature] = weight * _normalise_pressure(_float(row, feature))
    score = sum(contributions.values())
    lane_scores = _lane_scores(row)
    strongest = max(contributions, key=contributions.get) if contributions else "none"
    primary_lane = max(lane_scores, key=lane_scores.get) if lane_scores else "none"
    out: dict[str, object] = {
        "scope": scope,
        "source_label": row.get("source_label", ""),
        "source_profile": row.get("source_profile", ""),
        "family_id": row.get("family_id", ""),
        "total_runs": row.get("total_runs", ""),
        "shadow_score": f"{score:.6f}",
        "shadow_band": _band(score),
        "strongest_contributor": strongest,
        "shadow_primary_lane": SCORE_LANE_LABELS.get(primary_lane, primary_lane),
        "shadow_primary_lane_score": f"{lane_scores.get(primary_lane, 0.0):.6f}",
        "score_status": "report_only_no_crown_no_demotion",
        "boundary": "transparent_shadow_score_no_role_labels_no_targets_loaded",
    }
    for score_name, lane_score in lane_scores.items():
        out[score_name] = f"{lane_score:.6f}"
    for feature, contribution in contributions.items():
        out[f"contribution_{feature}"] = f"{contribution:.6f}"
    return out


def score_rows(rows: list[dict[str, str]], *, scope: str, source_name: str) -> list[dict[str, object]]:
    assert_role_stripped_rows(rows, source_name=source_name)
    return [_score_row(row, scope=scope) for row in rows]


def _top_rows(rows: list[dict[str, object]], *, limit: int = 5) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: float(row.get("shadow_score", 0) or 0), reverse=True)[:limit]


def _write_read(path: Path, *, profile_scores: list[dict[str, object]], family_scores: list[dict[str, object]]) -> None:
    top_profile = _top_rows(profile_scores)
    top_family = _top_rows(family_scores)
    lines: list[str] = []
    lines.append("# ZeroGateSim Transparent Shadow Score Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report starts the `v1.6.2-alpha` transparent shadow-score prototype. It reads role-stripped feature files and writes a report-side risk score.")
    lines.append("")
    lines.append("It is not a role-blind detector yet. It does not read evaluation targets, designed truth-role labels, or answer keys. It does not crown, demote, or replace the current role-aware witness.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append("## Formula")
    lines.append("")
    lines.append("Each feature rate is first passed through a saturating transform:")
    lines.append("")
    lines.append("```text")
    lines.append("N(x) = x / (1 + x)")
    lines.append("```")
    lines.append("")
    lines.append("The transparent shadow score is:")
    lines.append("")
    lines.append("```text")
    lines.append("S_shadow = sum_j w_j N(x_j)")
    lines.append("```")
    lines.append("")
    lines.append("Weights are fixed in `shadow_score_formula.json` for inspection. This is deliberately not learned yet.")
    lines.append("")
    lines.append("## v1.6.10 lane-specific candidate scores")
    lines.append("")
    lines.append("The historical `shadow_score` remains frozen as the v1.6.2 report-side score. `v1.6.10-alpha` adds fixed lane-specific candidate scores so later discrimination reports can ask whether any lane sees pressure kind beyond raw intensity and dumb baselines:")
    lines.append("")
    lines.append("```text")
    lines.append("density_pressure")
    lines.append("raw_false_one")
    lines.append("demotion")
    lines.append("hold_or_demote")
    lines.append("relation_specific")
    lines.append("return_specific")
    lines.append("native_breach_proxy")
    lines.append("```")
    lines.append("")
    lines.append("These lane scores are not a detector and do not crown, demote, or mutate the native witness.")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append("- `shadow_score_profile_scores.csv` — source-level transparent scores.")
    lines.append("- `shadow_score_family_scores.csv` — opaque family-level transparent scores.")
    lines.append("- `shadow_score_formula.json` — fixed feature weights and score boundary.")
    lines.append("- `shadow_score_forbidden_field_audit.json` — confirms role/answer-key fields were refused.")
    lines.append("")
    lines.append("## Top profile scores")
    lines.append("")
    lines.append("| source | profile | score | band | strongest contributor |")
    lines.append("|---|---|---:|---|---|")
    for row in top_profile:
        lines.append(f"| {row.get('source_label', '')} | {row.get('source_profile', '')} | {row.get('shadow_score', '')} | {row.get('shadow_band', '')} | {row.get('strongest_contributor', '')} |")
    lines.append("")
    lines.append("## Top family scores")
    lines.append("")
    lines.append("| source | family | score | band | strongest contributor |")
    lines.append("|---|---|---:|---|---|")
    for row in top_family:
        lines.append(f"| {row.get('source_label', '')} | {row.get('family_id', '')} | {row.get('shadow_score', '')} | {row.get('shadow_band', '')} | {row.get('strongest_contributor', '')} |")
    lines.append("")
    lines.append("## Evaluation route")
    lines.append("")
    lines.append("These scores are pressure witnesses, not verdicts. Later baseline, weather-hardening, and discrimination reports must compare them against separated targets and dumb baselines. If the frozen score cannot beat simple baselines or cannot explain residual pressure beyond them, role-blind shadow is not earned.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / SHADOW_SCORE_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_transparent_shadow_score_bundle",
        "file_count_excluding_manifest": len([path for path in files if path != manifest_path]),
        "files": [
            {"path": path.relative_to(output_dir).as_posix(), "size_bytes": path.stat().st_size}
            for path in files
            if path != manifest_path
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path != bundle_path)
    if bundle_path.exists():
        bundle_path.unlink()
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.relative_to(output_dir).as_posix())
    return bundle_path


def write_shadow_score_report(
    *,
    output_dir: Path,
    profile_features: Path,
    family_features: Path,
) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    profile_rows = _read_csv(Path(profile_features))
    family_rows = _read_csv(Path(family_features))
    if not profile_rows:
        raise ValueError(f"Profile feature file is empty: {profile_features}")
    if not family_rows:
        raise ValueError(f"Family feature file is empty: {family_features}")

    profile_scores = score_rows(profile_rows, scope="profile", source_name=str(profile_features))
    family_scores = score_rows(family_rows, scope="family", source_name=str(family_features))

    profile_scores_path = output_dir / SHADOW_SCORE_FILES["profile_scores"]
    family_scores_path = output_dir / SHADOW_SCORE_FILES["family_scores"]
    read_path = output_dir / SHADOW_SCORE_FILES["read"]
    formula_path = output_dir / SHADOW_SCORE_FILES["formula"]
    audit_path = output_dir / SHADOW_SCORE_FILES["audit"]

    _write_csv(profile_scores_path, profile_scores)
    _write_csv(family_scores_path, family_scores)
    _write_read(read_path, profile_scores=profile_scores, family_scores=family_scores)

    formula = {
        "version": "v1.6.2-alpha",
        "score_name": "transparent_shadow_score",
        "normalisation": "N(x)=x/(1+x)",
        "weights": SHADOW_SCORE_WEIGHTS,
        "lane_scores_version": "v1.6.10-alpha",
        "lane_scores_boundary": "fixed report-side candidate lane scores; not learned, not tuned against targets, not detector closeout",
        "lane_score_weights": SHADOW_LANE_SCORE_WEIGHTS,
        "lane_score_labels": SCORE_LANE_LABELS,
        "special_lane_feature": "feature_return_gate_inverse_rate = max(0, min(1, 1 - feature_return_gate_rate))",
        "role_blind_boundary": "score reads role-stripped feature files only; targets are not loaded",
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    formula_path.write_text(json.dumps(formula, indent=2), encoding="utf-8")

    audit = {
        "feature_files_role_stripped": True,
        "profile_forbidden_fields_found": _forbidden_header_fields(profile_rows),
        "family_forbidden_fields_found": _forbidden_header_fields(family_rows),
        "forbidden_shadow_input_fields": sorted(FORBIDDEN_SHADOW_INPUT_FIELDS),
        "target_file_loaded": False,
        "target_file_boundary": "evaluation targets are reserved for later baseline/falsifier, weather-hardening, and discrimination reports",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle_path = _write_bundle(output_dir)
    return {
        "shadow_score_profile_scores": profile_scores_path,
        "shadow_score_family_scores": family_scores_path,
        "shadow_score_read": read_path,
        "shadow_score_formula": formula_path,
        "shadow_score_forbidden_field_audit": audit_path,
        "shadow_score_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a transparent report-side shadow score from role-stripped ZeroGateSim feature files.")
    parser.add_argument("--profile-features", type=Path, required=True, help="Path to role_stripped_profile_features.csv.")
    parser.add_argument("--family-features", type=Path, required=True, help="Path to role_stripped_family_features.csv.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_score_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_shadow_score_report(output_dir=args.out, profile_features=args.profile_features, family_features=args.family_features)
    print("ZeroGateSim transparent shadow score report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
