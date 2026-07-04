from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Iterable, Sequence

from zerogate_sim.role_stripped_feature_report import FORBIDDEN_SHADOW_INPUT_FIELDS

SHADOW_BASELINE_FILES = {
    "profile_comparison": "shadow_baseline_profile_comparison.csv",
    "family_comparison": "shadow_baseline_family_comparison.csv",
    "model_metrics": "shadow_baseline_model_metrics.csv",
    "read": "shadow_baseline_falsifier_read.md",
    "metrics": "shadow_baseline_falsifier_metrics.json",
    "audit": "shadow_baseline_falsifier_audit.json",
    "bundle": "shadow_baseline_falsifier_bundle.zip",
}

TARGET_FIELDS = {
    "target_raw_false_one_rate",
    "target_false_one_demotion_rate",
    "target_final_false_crown_rate",
    "target_relation_false_pressure_share",
}

EVALUATION_ONLY_FIELDS = TARGET_FIELDS | {"evaluation_family_label"}
FORBIDDEN_FEATURE_OR_SCORE_FIELDS = FORBIDDEN_SHADOW_INPUT_FIELDS | EVALUATION_ONLY_FIELDS

# Baselines are deliberately transparent. If a field is absent from the current
# role-stripped feature schema, that baseline is recorded as unavailable rather
# than invented from a proxy that would overstate the evidence.
BASELINE_FEATURE_FIELDS: dict[str, str] = {
    "raw_pressure_only": "feature_raw_pressure_rate",
    "earned_rate_only": "feature_earned_rate",
    "latent_hold_only": "feature_latent_hold_rate",
    "relation_debt_only": "feature_relation_debt_rate",
    "mirror_primary_only": "feature_mirror_primary_rate",
    "mirror_secondary_only": "feature_mirror_secondary_rate",
    "ablation_raw_as_final_only": "feature_ablation_raw_as_final_crown_risk_rate",
    "demotion_dependence_only": "feature_ablation_demotion_dependence_rate",
    "latent_hold_dependence_only": "feature_ablation_latent_hold_dependence_rate",
    "echo_independence_dependence_only": "feature_ablation_echo_independence_rate",
    "weakest_gate_only": "feature_weakest_gate_pressure_rate",
    "raw_strength_only": "feature_raw_strength_pressure_rate",
    "relation_gate_only": "feature_relation_gate_rate",
}

MINIMUM_BASELINE_MAP = {
    "random ranking": "random_deterministic",
    "raw-strength-only ranking": "raw_strength_only",
    "weakest-gate-only ranking": "weakest_gate_only",
    "relation-gate-only ranking": "relation_gate_only",
}

TARGET_NAME = "target_raw_false_one_rate"


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


def _format_float(value: float) -> str:
    if math.isnan(value) or math.isinf(value):
        return "0.000000"
    return f"{value:.6f}"


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _profile_key(row: dict[str, str]) -> tuple[str, str]:
    return (str(row.get("source_label", "") or ""), str(row.get("source_profile", "") or ""))


def _family_key(row: dict[str, str]) -> tuple[str, str]:
    return (str(row.get("source_label", "") or ""), str(row.get("family_id", "") or ""))


def _row_key(row: dict[str, str], *, scope: str) -> str:
    if scope == "family":
        return "::".join(_family_key(row))
    return "::".join(_profile_key(row))


def _forbidden_header_fields(rows: list[dict[str, str]], forbidden: set[str]) -> list[str]:
    if not rows:
        return []
    return sorted(set(rows[0].keys()) & forbidden)


def assert_no_forbidden_evaluation_fields(rows: list[dict[str, str]], *, source_name: str) -> None:
    forbidden = _forbidden_header_fields(rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS)
    if forbidden:
        raise ValueError(f"Forbidden role/target fields in score or feature input {source_name}: {', '.join(forbidden)}")


def assert_targets_are_evaluation_only(rows: list[dict[str, str]], *, source_name: str) -> None:
    forbidden = _forbidden_header_fields(rows, FORBIDDEN_SHADOW_INPUT_FIELDS)
    if forbidden:
        raise ValueError(f"Forbidden role/answer-key fields in evaluation target input {source_name}: {', '.join(forbidden)}")
    if not rows or TARGET_NAME not in rows[0]:
        raise ValueError(f"Evaluation target input must include {TARGET_NAME}: {source_name}")


def _split_targets(target_rows: list[dict[str, str]]) -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    profile_targets: dict[tuple[str, str], dict[str, str]] = {}
    family_targets: dict[tuple[str, str], dict[str, str]] = {}
    for row in target_rows:
        family_id = str(row.get("family_id", "") or "").strip()
        if family_id:
            family_targets[_family_key(row)] = row
        else:
            profile_targets[_profile_key(row)] = row
    return profile_targets, family_targets


def _join_scope_rows(
    *,
    scope: str,
    feature_rows: list[dict[str, str]],
    score_rows: list[dict[str, str]],
    target_rows: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, dict[str, str] | str]]:
    if scope not in {"profile", "family"}:
        raise ValueError(f"Unknown scope: {scope}")
    key_fn = _profile_key if scope == "profile" else _family_key
    score_by_key = {key_fn(row): row for row in score_rows}
    joined: list[dict[str, dict[str, str] | str]] = []
    missing_scores: list[str] = []
    missing_targets: list[str] = []
    for feature in feature_rows:
        key = key_fn(feature)
        key_text = "::".join(key)
        score = score_by_key.get(key)
        target = target_rows.get(key)
        if score is None:
            missing_scores.append(key_text)
            continue
        if target is None:
            missing_targets.append(key_text)
            continue
        joined.append({"scope": scope, "key": key_text, "feature": feature, "score": score, "target": target})
    if missing_scores:
        raise ValueError(f"Missing {scope} score rows for: {', '.join(missing_scores)}")
    if missing_targets:
        raise ValueError(f"Missing {scope} target rows for: {', '.join(missing_targets)}")
    return joined


def _stable_random_score(key: str) -> float:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return int(digest, 16) / float(0xFFFFFFFFFFFFFFFF)


def _available_model_scores(feature: dict[str, str], score: dict[str, str], *, key: str) -> dict[str, float]:
    out = {
        "shadow_score": _float(score, "shadow_score"),
        "random_deterministic": _stable_random_score(key),
    }
    for model, field in BASELINE_FEATURE_FIELDS.items():
        if field in feature and str(feature.get(field, "") or "") != "":
            out[model] = _float(feature, field)
    return out


def _comparison_rows(joined_rows: list[dict[str, dict[str, str] | str]], *, scope: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for joined in joined_rows:
        key = str(joined["key"])
        feature = joined["feature"]
        score = joined["score"]
        target = joined["target"]
        assert isinstance(feature, dict)
        assert isinstance(score, dict)
        assert isinstance(target, dict)
        models = _available_model_scores(feature, score, key=key)
        for model_name, model_score in models.items():
            out.append(
                {
                    "scope": scope,
                    "row_key": key,
                    "source_label": feature.get("source_label", ""),
                    "source_profile": feature.get("source_profile", ""),
                    "family_id": feature.get("family_id", ""),
                    "model_name": model_name,
                    "model_score": _format_float(model_score),
                    "target_raw_false_one_rate": _format_float(_float(target, "target_raw_false_one_rate")),
                    "target_false_one_demotion_rate": _format_float(_float(target, "target_false_one_demotion_rate")),
                    "target_final_false_crown_rate": _format_float(_float(target, "target_final_false_crown_rate")),
                    "evaluation_family_label": target.get("evaluation_family_label", ""),
                    "evaluation_boundary": "targets_compared_after_scores_no_role_labels_loaded_as_features",
                }
            )
    return out


def _rankdata(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        average_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = average_rank
        i = j
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return 0.0
    rx = _rankdata(xs)
    ry = _rankdata(ys)
    mx = _mean(rx)
    my = _mean(ry)
    numerator = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    denom_x = math.sqrt(sum((x - mx) ** 2 for x in rx))
    denom_y = math.sqrt(sum((y - my) ** 2 for y in ry))
    if denom_x == 0.0 or denom_y == 0.0:
        return 0.0
    return numerator / (denom_x * denom_y)


def _pairwise_order_accuracy(scores: Sequence[float], targets: Sequence[float]) -> tuple[float, int]:
    comparable = 0
    correct = 0.0
    for i in range(len(scores)):
        for j in range(i + 1, len(scores)):
            target_delta = targets[i] - targets[j]
            if target_delta == 0.0:
                continue
            score_delta = scores[i] - scores[j]
            comparable += 1
            if score_delta == 0.0:
                correct += 0.5
            elif score_delta * target_delta > 0:
                correct += 1.0
    if comparable == 0:
        return 0.0, 0
    return correct / comparable, comparable


def _top_bucket_lift(scores: Sequence[float], targets: Sequence[float]) -> tuple[float, float, float, int]:
    if not scores or not targets:
        return 0.0, 0.0, 0.0, 0
    top_n = max(1, math.ceil(len(scores) * 0.25))
    ordered = sorted(zip(scores, targets), key=lambda pair: pair[0], reverse=True)
    top_targets = [target for _, target in ordered[:top_n]]
    mean_top = _mean(top_targets)
    mean_all = _mean(list(targets))
    lift = mean_top / mean_all if mean_all > 0 else 0.0
    return lift, mean_top, mean_all, top_n


def _metric_rows(comparison_rows: list[dict[str, object]], *, scope: str) -> list[dict[str, object]]:
    by_model: dict[str, list[dict[str, object]]] = {}
    for row in comparison_rows:
        by_model.setdefault(str(row["model_name"]), []).append(row)
    rows: list[dict[str, object]] = []
    for model_name, model_rows in sorted(by_model.items()):
        scores = [float(row["model_score"]) for row in model_rows]
        targets = [float(row[TARGET_NAME]) for row in model_rows]
        pairwise, comparable_pairs = _pairwise_order_accuracy(scores, targets)
        lift, mean_top, mean_all, top_n = _top_bucket_lift(scores, targets)
        rows.append(
            {
                "scope": scope,
                "model_name": model_name,
                "target_name": TARGET_NAME,
                "row_count": len(model_rows),
                "comparable_pairs": comparable_pairs,
                "pairwise_order_accuracy": _format_float(pairwise),
                "spearman_rank_correlation": _format_float(_spearman(scores, targets)),
                "top_bucket_size": top_n,
                "top_bucket_target_lift": _format_float(lift),
                "mean_target_top_bucket": _format_float(mean_top),
                "mean_target_all": _format_float(mean_all),
            }
        )
    return rows


def _model_metric_map(metric_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row["model_name"]): row for row in metric_rows}


def _baseline_status(feature_rows: list[dict[str, str]], metric_rows: list[dict[str, object]]) -> dict[str, object]:
    available_models = {str(row["model_name"]) for row in metric_rows}
    feature_header = set(feature_rows[0].keys()) if feature_rows else set()
    minimum: dict[str, dict[str, str]] = {}
    for label, model in MINIMUM_BASELINE_MAP.items():
        if model in available_models:
            status = "available_exact"
            used = model
        elif label == "raw-strength-only ranking" and "raw_pressure_only" in available_models:
            status = "proxy_available_raw_pressure_only_not_exact_raw_strength"
            used = "raw_pressure_only"
        elif label == "relation-gate-only ranking" and "relation_debt_only" in available_models:
            status = "proxy_available_relation_debt_only_not_exact_relation_gate"
            used = "relation_debt_only"
        else:
            needed_field = BASELINE_FEATURE_FIELDS.get(model, "")
            status = "unavailable_in_current_role_stripped_feature_schema"
            used = needed_field
        minimum[label] = {"status": status, "model_or_needed_field": used}
    return {
        "available_models": sorted(available_models),
        "available_feature_fields": sorted(feature_header),
        "minimum_baseline_status": minimum,
    }


def _scope_decision(metric_rows: list[dict[str, object]], feature_rows: list[dict[str, str]]) -> dict[str, object]:
    metrics = _model_metric_map(metric_rows)
    shadow = metrics.get("shadow_score")
    status = _baseline_status(feature_rows, metric_rows)
    if shadow is None:
        return {"falsifier_result": "resist_shadow_score_missing", **status}
    comparable_pairs = int(shadow.get("comparable_pairs", 0) or 0)
    if comparable_pairs <= 0:
        return {"falsifier_result": "witness_insufficient_target_variation", "shadow_model": shadow, **status}
    baseline_metrics = [row for name, row in metrics.items() if name != "shadow_score"]
    if not baseline_metrics:
        return {"falsifier_result": "witness_no_available_baselines", "shadow_model": shadow, **status}
    best_baseline = max(
        baseline_metrics,
        key=lambda row: (
            float(row.get("pairwise_order_accuracy", 0) or 0),
            float(row.get("spearman_rank_correlation", 0) or 0),
            float(row.get("top_bucket_target_lift", 0) or 0),
        ),
    )
    shadow_pairwise = float(shadow.get("pairwise_order_accuracy", 0) or 0)
    best_pairwise = float(best_baseline.get("pairwise_order_accuracy", 0) or 0)
    exact_minimum_ready = all(
        item["status"] == "available_exact"
        for item in status["minimum_baseline_status"].values()  # type: ignore[index]
    )
    if shadow_pairwise <= best_pairwise:
        result = "resist_shadow_not_better_than_available_baselines"
    elif not exact_minimum_ready:
        result = "witness_shadow_beats_available_baselines_exact_minimum_incomplete"
    else:
        result = "expand_shadow_beats_exact_baselines_not_detector"
    return {
        "falsifier_result": result,
        "shadow_model": shadow,
        "best_available_baseline": best_baseline,
        **status,
    }


def _write_read(
    path: Path,
    *,
    profile_metric_rows: list[dict[str, object]],
    family_metric_rows: list[dict[str, object]],
    decisions: dict[str, object],
) -> None:
    def _best(rows: list[dict[str, object]]) -> dict[str, object] | None:
        if not rows:
            return None
        return max(
            rows,
            key=lambda row: (
                float(row.get("pairwise_order_accuracy", 0) or 0),
                float(row.get("spearman_rank_correlation", 0) or 0),
                float(row.get("top_bucket_target_lift", 0) or 0),
            ),
        )

    lines: list[str] = []
    lines.append("# ZeroGateSim Shadow Baseline/Falsifier Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report starts the `v1.6.3-alpha` baseline/falsifier gate for the role-blind shadow line.")
    lines.append("")
    lines.append("It compares already-written transparent shadow scores against separated evaluation targets and trivial role-stripped baselines. Targets are loaded only for evaluation after scoring, not as score inputs.")
    lines.append("")
    lines.append("This is not role-blind discovery, not a detector closeout, not a crown/demotion rule, and not a replacement for the current role-aware witness.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append("## Primary target")
    lines.append("")
    lines.append(f"The primary evaluation target is `{TARGET_NAME}`. Ranking metrics ask whether higher report-side scores align with higher known false-one-like pressure after the role-stripped score has already been written.")
    lines.append("")
    lines.append("## Falsifier rule")
    lines.append("")
    lines.append("If `shadow_score` does not beat trivial available baselines, the shadow is not earned. If it beats available baselines but exact minimum baselines are unavailable in the current feature schema, the result remains held in witness rather than upgraded to discovery.")
    lines.append("")
    for scope, metric_rows in [("profile", profile_metric_rows), ("family", family_metric_rows)]:
        decision = decisions.get(scope, {})
        lines.append(f"## {scope.title()} scope")
        lines.append("")
        lines.append(f"Falsifier result: `{decision.get('falsifier_result', 'unknown') if isinstance(decision, dict) else 'unknown'}`")
        best = _best(metric_rows)
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
    lines.append("## Schema honesty")
    lines.append("")
    lines.append("The v1.6.0 design named random, raw-strength-only, weakest-gate-only, and relation-gate-only as minimum baselines. This report records which exact baselines are present in the current role-stripped feature schema and refuses to invent missing ones.")
    lines.append("")
    lines.append("## Next gate")
    lines.append("")
    lines.append("`v1.6.4-alpha` should run a held-out `deep81` / `wide243` role-stripped evaluation with exact gate baselines if the source feature schema provides them. Until holdout passes, the shadow remains report-side evidence only.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / SHADOW_BASELINE_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_shadow_baseline_falsifier_bundle",
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


def write_shadow_baseline_falsifier_report(
    *,
    output_dir: Path,
    profile_features: Path,
    family_features: Path,
    profile_scores: Path,
    family_scores: Path,
    evaluation_targets: Path,
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
    decisions = {
        "profile": _scope_decision(profile_metric_rows, profile_feature_rows),
        "family": _scope_decision(family_metric_rows, family_feature_rows),
    }

    profile_comparison_path = output_dir / SHADOW_BASELINE_FILES["profile_comparison"]
    family_comparison_path = output_dir / SHADOW_BASELINE_FILES["family_comparison"]
    model_metrics_path = output_dir / SHADOW_BASELINE_FILES["model_metrics"]
    read_path = output_dir / SHADOW_BASELINE_FILES["read"]
    metrics_path = output_dir / SHADOW_BASELINE_FILES["metrics"]
    audit_path = output_dir / SHADOW_BASELINE_FILES["audit"]

    _write_csv(profile_comparison_path, profile_comparison)
    _write_csv(family_comparison_path, family_comparison)
    _write_csv(model_metrics_path, model_metrics)
    _write_read(read_path, profile_metric_rows=profile_metric_rows, family_metric_rows=family_metric_rows, decisions=decisions)

    metrics = {
        "version": "v1.6.3-alpha",
        "report_name": "shadow_baseline_falsifier_report",
        "primary_target": TARGET_NAME,
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "role_blind_boundary": "targets compared only after role-stripped scores are written; no role-blind discovery claim",
        "decisions": decisions,
        "model_metrics": model_metrics,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    audit = {
        "feature_and_score_inputs_role_stripped": True,
        "targets_loaded_after_scoring_for_evaluation_only": True,
        "target_file_loaded": True,
        "forbidden_shadow_input_fields": sorted(FORBIDDEN_SHADOW_INPUT_FIELDS),
        "forbidden_feature_or_score_fields": sorted(FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "profile_feature_forbidden_fields_found": _forbidden_header_fields(profile_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "family_feature_forbidden_fields_found": _forbidden_header_fields(family_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "profile_score_forbidden_fields_found": _forbidden_header_fields(profile_score_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "family_score_forbidden_fields_found": _forbidden_header_fields(family_score_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "target_forbidden_role_fields_found": _forbidden_header_fields(target_rows, FORBIDDEN_SHADOW_INPUT_FIELDS),
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    bundle_path = _write_bundle(output_dir)
    return {
        "shadow_baseline_profile_comparison": profile_comparison_path,
        "shadow_baseline_family_comparison": family_comparison_path,
        "shadow_baseline_model_metrics": model_metrics_path,
        "shadow_baseline_falsifier_read": read_path,
        "shadow_baseline_falsifier_metrics": metrics_path,
        "shadow_baseline_falsifier_audit": audit_path,
        "shadow_baseline_falsifier_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare ZeroGateSim transparent shadow scores against role-stripped baselines and separated evaluation targets.")
    parser.add_argument("--profile-features", type=Path, required=True, help="Path to role_stripped_profile_features.csv.")
    parser.add_argument("--family-features", type=Path, required=True, help="Path to role_stripped_family_features.csv.")
    parser.add_argument("--profile-scores", type=Path, required=True, help="Path to shadow_score_profile_scores.csv.")
    parser.add_argument("--family-scores", type=Path, required=True, help="Path to shadow_score_family_scores.csv.")
    parser.add_argument("--evaluation-targets", type=Path, required=True, help="Path to role_stripped_evaluation_targets.csv.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_baseline_falsifier_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_shadow_baseline_falsifier_report(
        output_dir=args.out,
        profile_features=args.profile_features,
        family_features=args.family_features,
        profile_scores=args.profile_scores,
        family_scores=args.family_scores,
        evaluation_targets=args.evaluation_targets,
    )
    print("ZeroGateSim shadow baseline/falsifier report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
