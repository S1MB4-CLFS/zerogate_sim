from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from pathlib import Path
from typing import Iterable, Sequence

from zerogate_sim.role_stripped_feature_report import FORBIDDEN_SHADOW_INPUT_FIELDS
from zerogate_sim.shadow_baseline_falsifier_report import (
    FORBIDDEN_FEATURE_OR_SCORE_FIELDS,
    TARGET_NAME,
    _comparison_rows,
    _ensure_dir,
    _forbidden_header_fields,
    _join_scope_rows,
    _metric_rows,
    _read_csv,
    _scope_decision,
    _split_targets,
    _write_csv,
    assert_no_forbidden_evaluation_fields,
    assert_targets_are_evaluation_only,
)

SHADOW_HOLDOUT_FILES = {
    "profile_comparison": "shadow_holdout_profile_comparison.csv",
    "family_comparison": "shadow_holdout_family_comparison.csv",
    "model_metrics": "shadow_holdout_model_metrics.csv",
    "read": "shadow_holdout_evaluation_read.md",
    "metrics": "shadow_holdout_evaluation_metrics.json",
    "audit": "shadow_holdout_evaluation_audit.json",
    "bundle": "shadow_holdout_evaluation_bundle.zip",
}

DEFAULT_REQUIRED_SOURCES = ("deep81", "wide243")


def _source_values(rows: Sequence[dict[str, str]]) -> set[str]:
    values: set[str] = set()
    for row in rows:
        for key in ["source_label", "source_profile"]:
            value = str(row.get(key, "") or "").strip()
            if value:
                values.add(value)
    return values


def _source_matches(source_values: set[str], required: str) -> bool:
    required_norm = required.strip().lower()
    if not required_norm:
        return True
    for value in source_values:
        value_norm = value.lower()
        if value_norm == required_norm or required_norm in value_norm:
            return True
    return False


def assert_required_holdout_sources(profile_rows: list[dict[str, str]], required_sources: Sequence[str]) -> None:
    source_values = _source_values(profile_rows)
    missing = [source for source in required_sources if not _source_matches(source_values, source)]
    if missing:
        available = ", ".join(sorted(source_values)) or "none"
        raise ValueError(f"Missing required holdout source(s): {', '.join(missing)}. Available sources: {available}")


def _holdout_result(decision: dict[str, object]) -> str:
    result = str(decision.get("falsifier_result", "unknown"))
    mapping = {
        "resist_shadow_score_missing": "resist_holdout_shadow_score_missing",
        "resist_shadow_not_better_than_available_baselines": "resist_holdout_shadow_not_better_than_available_baselines",
        "witness_shadow_beats_available_baselines_exact_minimum_incomplete": "witness_holdout_shadow_beats_available_baselines_exact_minimum_incomplete",
        "expand_shadow_beats_exact_baselines_not_detector": "expand_holdout_shadow_beats_exact_baselines_not_detector",
        "witness_insufficient_target_variation": "witness_holdout_insufficient_target_variation",
        "witness_no_available_baselines": "witness_holdout_no_available_baselines",
    }
    return mapping.get(result, f"witness_holdout_{result}")


def _best_model(metric_rows: list[dict[str, object]]) -> dict[str, object] | None:
    if not metric_rows:
        return None
    return max(
        metric_rows,
        key=lambda row: (
            float(row.get("pairwise_order_accuracy", 0) or 0),
            float(row.get("spearman_rank_correlation", 0) or 0),
            float(row.get("top_bucket_target_lift", 0) or 0),
        ),
    )


def _read_training_shadow_metrics(path: Path | None) -> dict[str, object]:
    if path is None:
        return {"training_metrics_loaded": False}
    if not path.exists():
        raise FileNotFoundError(f"Training metrics file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, object] = {"training_metrics_loaded": True, "training_metrics_path": str(path)}
    decisions = data.get("decisions", {}) if isinstance(data, dict) else {}
    if isinstance(decisions, dict):
        for scope in ["profile", "family"]:
            scope_decision = decisions.get(scope, {})
            if isinstance(scope_decision, dict):
                shadow = scope_decision.get("shadow_model", {})
                if isinstance(shadow, dict):
                    out[f"training_{scope}_shadow_pairwise_order_accuracy"] = shadow.get("pairwise_order_accuracy", "")
                    out[f"training_{scope}_shadow_comparable_pairs"] = shadow.get("comparable_pairs", "")
    return out


def _write_read(
    path: Path,
    *,
    required_sources: Sequence[str],
    source_values: set[str],
    profile_metric_rows: list[dict[str, object]],
    family_metric_rows: list[dict[str, object]],
    decisions: dict[str, dict[str, object]],
) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Shadow Holdout Evaluation Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report is the `v1.6.5-alpha` holdout gate for the role-blind shadow line. It evaluates already-written transparent shadow scores on declared held-out `deep81` / `wide243` role-stripped evidence.")
    lines.append("")
    lines.append("It is not role-blind discovery, not a detector closeout, not a crown/demotion rule, and not a replacement for the current role-aware witness. Targets are loaded only after scores already exist.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append("## Holdout declaration")
    lines.append("")
    lines.append(f"Required holdout sources: `{', '.join(required_sources)}`")
    lines.append(f"Observed source labels/profiles: `{', '.join(sorted(source_values))}`")
    lines.append("")
    lines.append("The report checks source coverage and refuses to treat an in-sample score comparison as holdout merely because the file names are attractive. Gremlin costume rejected at the door.")
    lines.append("")
    lines.append("## Evaluation rule")
    lines.append("")
    lines.append("Score first. Compare later. The feature and score files must not contain role labels, answer keys, or evaluation target fields. The target table is joined only after the score rows are complete.")
    lines.append("")
    for scope, metric_rows in [("profile", profile_metric_rows), ("family", family_metric_rows)]:
        decision = decisions.get(scope, {})
        lines.append(f"## {scope.title()} holdout scope")
        lines.append("")
        lines.append(f"Holdout result: `{decision.get('holdout_result', 'unknown')}`")
        best = _best_model(metric_rows)
        if best:
            lines.append(f"Best model by primary metric: `{best['model_name']}`")
        lines.append("")
        lines.append("| model | rows | pairs | pairwise accuracy | Spearman | top-bucket lift |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in sorted(metric_rows, key=lambda item: str(item["model_name"])):
            lines.append(
                f"| {row['model_name']} | {row['row_count']} | {row['comparable_pairs']} | "
                f"{row['pairwise_order_accuracy']} | {row['spearman_rank_correlation']} | {row['top_bucket_target_lift']} |"
            )
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("A passing holdout result can support the phrase `survived this role-stripped holdout comparison`. It still cannot support `solved role-blind false-one detection`.")
    lines.append("")
    lines.append("If exact minimum baselines are unavailable in the feature schema, the correct state remains witness even when the shadow beats available baselines.")
    lines.append("")
    lines.append("## Next gate")
    lines.append("")
    lines.append("`v1.6.6-alpha` may close the v1.6 shadow line with a visual/report closeout only if this holdout result and CI are green. Otherwise the line stays in HOLD.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / SHADOW_HOLDOUT_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_shadow_holdout_evaluation_bundle",
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


def write_shadow_holdout_evaluation_report(
    *,
    output_dir: Path,
    profile_features: Path,
    family_features: Path,
    profile_scores: Path,
    family_scores: Path,
    evaluation_targets: Path,
    required_sources: Sequence[str] = DEFAULT_REQUIRED_SOURCES,
    training_metrics: Path | None = None,
) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    profile_feature_rows = _read_csv(Path(profile_features))
    family_feature_rows = _read_csv(Path(family_features))
    profile_score_rows = _read_csv(Path(profile_scores))
    family_score_rows = _read_csv(Path(family_scores))
    target_rows = _read_csv(Path(evaluation_targets))

    if not profile_feature_rows:
        raise ValueError(f"Profile feature file is empty: {profile_features}")
    if not family_feature_rows:
        raise ValueError(f"Family feature file is empty: {family_features}")
    if not profile_score_rows:
        raise ValueError(f"Profile score file is empty: {profile_scores}")
    if not family_score_rows:
        raise ValueError(f"Family score file is empty: {family_scores}")
    if not target_rows:
        raise ValueError(f"Evaluation target file is empty: {evaluation_targets}")

    assert_required_holdout_sources(profile_feature_rows, required_sources)
    for rows, name in [
        (profile_feature_rows, str(profile_features)),
        (family_feature_rows, str(family_features)),
        (profile_score_rows, str(profile_scores)),
        (family_score_rows, str(family_scores)),
    ]:
        assert_no_forbidden_evaluation_fields(rows, source_name=name)
    assert_targets_are_evaluation_only(target_rows, source_name=str(evaluation_targets))

    profile_targets, family_targets = _split_targets(target_rows)
    joined_profile = _join_scope_rows(
        scope="profile",
        feature_rows=profile_feature_rows,
        score_rows=profile_score_rows,
        target_rows=profile_targets,
    )
    joined_family = _join_scope_rows(
        scope="family",
        feature_rows=family_feature_rows,
        score_rows=family_score_rows,
        target_rows=family_targets,
    )

    profile_comparison = _comparison_rows(joined_profile, scope="profile")
    family_comparison = _comparison_rows(joined_family, scope="family")
    profile_metric_rows = _metric_rows(profile_comparison, scope="profile")
    family_metric_rows = _metric_rows(family_comparison, scope="family")
    model_metrics = profile_metric_rows + family_metric_rows

    base_profile_decision = _scope_decision(profile_metric_rows, profile_feature_rows)
    base_family_decision = _scope_decision(family_metric_rows, family_feature_rows)
    decisions = {
        "profile": {**base_profile_decision, "holdout_result": _holdout_result(base_profile_decision)},
        "family": {**base_family_decision, "holdout_result": _holdout_result(base_family_decision)},
    }
    source_values = _source_values(profile_feature_rows)
    training = _read_training_shadow_metrics(training_metrics)

    profile_comparison_path = output_dir / SHADOW_HOLDOUT_FILES["profile_comparison"]
    family_comparison_path = output_dir / SHADOW_HOLDOUT_FILES["family_comparison"]
    model_metrics_path = output_dir / SHADOW_HOLDOUT_FILES["model_metrics"]
    read_path = output_dir / SHADOW_HOLDOUT_FILES["read"]
    metrics_path = output_dir / SHADOW_HOLDOUT_FILES["metrics"]
    audit_path = output_dir / SHADOW_HOLDOUT_FILES["audit"]

    _write_csv(profile_comparison_path, profile_comparison)
    _write_csv(family_comparison_path, family_comparison)
    _write_csv(model_metrics_path, model_metrics)
    _write_read(
        read_path,
        required_sources=required_sources,
        source_values=source_values,
        profile_metric_rows=profile_metric_rows,
        family_metric_rows=family_metric_rows,
        decisions=decisions,
    )

    metrics = {
        "version": "v1.6.5-alpha",
        "report_name": "shadow_holdout_evaluation_report",
        "primary_target": TARGET_NAME,
        "required_holdout_sources": list(required_sources),
        "observed_sources": sorted(source_values),
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "role_blind_boundary": "holdout targets compared only after role-stripped scores are written; no role-blind discovery claim",
        "training_reference": training,
        "decisions": decisions,
        "model_metrics": model_metrics,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    audit = {
        "feature_and_score_inputs_role_stripped": True,
        "targets_loaded_after_scoring_for_evaluation_only": True,
        "holdout_sources_required": list(required_sources),
        "holdout_sources_observed": sorted(source_values),
        "target_file_loaded": True,
        "forbidden_shadow_input_fields": sorted(FORBIDDEN_SHADOW_INPUT_FIELDS),
        "forbidden_feature_or_score_fields": sorted(FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "profile_feature_forbidden_fields_found": _forbidden_header_fields(profile_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "family_feature_forbidden_fields_found": _forbidden_header_fields(family_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "profile_score_forbidden_fields_found": _forbidden_header_fields(profile_score_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "family_score_forbidden_fields_found": _forbidden_header_fields(family_score_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "target_forbidden_role_fields_found": _forbidden_header_fields(target_rows, FORBIDDEN_SHADOW_INPUT_FIELDS),
        "score_freeze_boundary": "this report reads already-written shadow scores and does not tune score weights",
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    bundle_path = _write_bundle(output_dir)
    return {
        "shadow_holdout_profile_comparison": profile_comparison_path,
        "shadow_holdout_family_comparison": family_comparison_path,
        "shadow_holdout_model_metrics": model_metrics_path,
        "shadow_holdout_evaluation_read": read_path,
        "shadow_holdout_evaluation_metrics": metrics_path,
        "shadow_holdout_evaluation_audit": audit_path,
        "shadow_holdout_evaluation_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate already-written ZeroGateSim shadow scores on declared held-out role-stripped evidence.")
    parser.add_argument("--profile-features", type=Path, required=True, help="Path to holdout role_stripped_profile_features.csv.")
    parser.add_argument("--family-features", type=Path, required=True, help="Path to holdout role_stripped_family_features.csv.")
    parser.add_argument("--profile-scores", type=Path, required=True, help="Path to holdout shadow_score_profile_scores.csv.")
    parser.add_argument("--family-scores", type=Path, required=True, help="Path to holdout shadow_score_family_scores.csv.")
    parser.add_argument("--evaluation-targets", type=Path, required=True, help="Path to holdout role_stripped_evaluation_targets.csv.")
    parser.add_argument("--required-source", action="append", default=[], help="Required holdout source label/profile. Defaults to deep81 and wide243 when omitted.")
    parser.add_argument("--training-metrics", type=Path, default=None, help="Optional v1.6.3 shadow_baseline_falsifier_metrics.json for reference only.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_holdout_evaluation_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    required_sources = tuple(args.required_source) if args.required_source else DEFAULT_REQUIRED_SOURCES
    paths = write_shadow_holdout_evaluation_report(
        output_dir=args.out,
        profile_features=args.profile_features,
        family_features=args.family_features,
        profile_scores=args.profile_scores,
        family_scores=args.family_scores,
        evaluation_targets=args.evaluation_targets,
        required_sources=required_sources,
        training_metrics=args.training_metrics,
    )
    print("ZeroGateSim shadow holdout evaluation report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
