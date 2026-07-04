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
    BASELINE_FEATURE_FIELDS,
    FORBIDDEN_FEATURE_OR_SCORE_FIELDS,
    MINIMUM_BASELINE_MAP,
    _available_model_scores,
    _ensure_dir,
    _forbidden_header_fields,
    _read_csv,
    _write_csv,
    assert_no_forbidden_evaluation_fields,
    assert_targets_are_evaluation_only,
)

WEATHER_HARDENING_FILES = {
    "baseline_comparison": "weather_hardening_baseline_comparison.csv",
    "target_diagnostics": "weather_hardening_target_diagnostics.csv",
    "native_gate_metrics": "weather_hardening_native_gate_metrics.csv",
    "decision": "weather_hardening_decision.json",
    "audit": "weather_hardening_audit.json",
    "read": "weather_hardening_read.md",
    "bundle": "weather_hardening_bundle.zip",
}

WEATHER_LADDER = {
    "triad27": "3^3 local expression weather",
    "deep81": "3^4 perturbation / late-shock bridge",
    "wide243": "3^5 temporal-depth / time-axis stress",
}

DEFAULT_REQUIRED_RUNGS = tuple(WEATHER_LADDER.keys())

STANDARD_TARGET_FIELDS = (
    "target_raw_false_one_rate",
    "target_false_one_demotion_rate",
    "target_final_false_crown_rate",
    "target_relation_false_pressure_share",
    "target_false_pressure_density_rate",
    "target_hold_or_demote_rate",
    "target_return_false_pressure_share",
    "target_native_breach_rate",
)

STANDARD_BASE_SUBPATHS = {
    "profile_features": Path("role_stripped") / "role_stripped_profile_features.csv",
    "family_features": Path("role_stripped") / "role_stripped_family_features.csv",
    "evaluation_targets": Path("role_stripped") / "role_stripped_evaluation_targets.csv",
    "profile_scores": Path("shadow_score") / "shadow_score_profile_scores.csv",
    "family_scores": Path("shadow_score") / "shadow_score_family_scores.csv",
    "seed_summary": Path("seed_block") / "seed_block_four_gate_summary.csv",
}


class EvidenceSource(dict):
    """Small typed dict-like holder without requiring Python 3.12 TypedDict imports in docs."""


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
    return "::".join(_family_key(row) if scope == "family" else _profile_key(row))


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
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def _pairwise_accuracy(scores: Sequence[float], targets: Sequence[float]) -> tuple[int, float]:
    comparable = 0
    correct = 0.0
    for i in range(len(scores)):
        for j in range(i + 1, len(scores)):
            target_delta = targets[i] - targets[j]
            if target_delta == 0:
                continue
            comparable += 1
            score_delta = scores[i] - scores[j]
            if score_delta == 0:
                correct += 0.5
            elif (score_delta > 0 and target_delta > 0) or (score_delta < 0 and target_delta < 0):
                correct += 1.0
    return comparable, (correct / comparable if comparable else 0.0)


def _target_fields(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    available = set(rows[0].keys())
    fields = [field for field in STANDARD_TARGET_FIELDS if field in available]
    extras = sorted(field for field in available if field.startswith("target_") and field not in fields)
    return fields + extras


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
    key_fn = _family_key if scope == "family" else _profile_key
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


def _metric_for_model(rows: list[dict[str, object]], *, model_name: str, target_name: str) -> dict[str, object]:
    filtered = [row for row in rows if row["model_name"] == model_name and row["target_name"] == target_name]
    scores = [_float(row, "model_score") for row in filtered]
    targets = [_float(row, "target_value") for row in filtered]
    comparable_pairs, pairwise = _pairwise_accuracy(scores, targets)
    top_n = max(1, math.ceil(len(filtered) * 0.25)) if filtered else 0
    top = sorted(filtered, key=lambda row: _float(row, "model_score"), reverse=True)[:top_n]
    mean_top = _mean([_float(row, "target_value") for row in top])
    mean_all = _mean(targets)
    lift = (mean_top / mean_all) if mean_all else 0.0
    return {
        "target_name": target_name,
        "model_name": model_name,
        "row_count": len(filtered),
        "comparable_pairs": comparable_pairs,
        "pairwise_order_accuracy": _format_float(pairwise),
        "spearman_rank_correlation": _format_float(_spearman(scores, targets)),
        "top_bucket_size": top_n,
        "top_bucket_target_lift": _format_float(lift),
        "mean_target_top_bucket": _format_float(mean_top),
        "mean_target_all": _format_float(mean_all),
    }


def _comparison_rows_for_joined(joined_rows: list[dict[str, dict[str, str] | str]], *, rung: str, scope: str, target_fields: Sequence[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for joined in joined_rows:
        key = str(joined["key"])
        feature = joined["feature"]
        score = joined["score"]
        target = joined["target"]
        assert isinstance(feature, dict)
        assert isinstance(score, dict)
        assert isinstance(target, dict)
        models = _available_model_scores(feature, score, key=key)
        for target_name in target_fields:
            if target_name not in target or str(target.get(target_name, "") or "") == "":
                continue
            for model_name, model_score in models.items():
                rows.append(
                    {
                        "rung": rung,
                        "scope": scope,
                        "row_key": key,
                        "source_label": feature.get("source_label", ""),
                        "source_profile": feature.get("source_profile", ""),
                        "family_id": feature.get("family_id", ""),
                        "model_name": model_name,
                        "model_score": _format_float(model_score),
                        "target_name": target_name,
                        "target_value": _format_float(_float(target, target_name)),
                        "evaluation_family_label": target.get("evaluation_family_label", ""),
                        "evaluation_boundary": "targets_compared_after_scores_no_role_labels_loaded_as_features",
                    }
                )
    return rows


def _metrics_from_comparison(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    models = sorted({str(row["model_name"]) for row in rows})
    targets = sorted({str(row["target_name"]) for row in rows})
    return [_metric_for_model(rows, model_name=model, target_name=target) for target in targets for model in models]


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
            status = "unavailable_in_current_role_stripped_feature_schema"
            used = BASELINE_FEATURE_FIELDS.get(model, "")
        minimum[label] = {"status": status, "model_or_needed_field": used}
    return {
        "available_models": sorted(available_models),
        "available_feature_fields": sorted(feature_header),
        "minimum_baseline_status": minimum,
    }


def _best_metric(rows: list[dict[str, object]]) -> dict[str, object] | None:
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


def _primary_target_decision(metric_rows: list[dict[str, object]], feature_rows: list[dict[str, str]], *, target_name: str) -> dict[str, object]:
    rows = [row for row in metric_rows if row["target_name"] == target_name]
    status = _baseline_status(feature_rows, rows)
    shadow = next((row for row in rows if row["model_name"] == "shadow_score"), None)
    if shadow is None:
        return {"decision": "resist_shadow_missing", **status}
    comparable_pairs = int(shadow.get("comparable_pairs", 0) or 0)
    if comparable_pairs <= 0:
        return {"decision": "hold_insufficient_variation", "shadow_model": shadow, **status}
    baseline_metrics = [row for row in rows if row["model_name"] != "shadow_score"]
    if not baseline_metrics:
        return {"decision": "hold_no_available_baselines", "shadow_model": shadow, **status}
    best_baseline = _best_metric(baseline_metrics)
    assert best_baseline is not None
    shadow_tuple = (
        float(shadow.get("pairwise_order_accuracy", 0) or 0),
        float(shadow.get("spearman_rank_correlation", 0) or 0),
        float(shadow.get("top_bucket_target_lift", 0) or 0),
    )
    baseline_tuple = (
        float(best_baseline.get("pairwise_order_accuracy", 0) or 0),
        float(best_baseline.get("spearman_rank_correlation", 0) or 0),
        float(best_baseline.get("top_bucket_target_lift", 0) or 0),
    )
    exact_minimum_ready = all(
        item["status"] == "available_exact"
        for item in status["minimum_baseline_status"].values()  # type: ignore[index]
    )
    if shadow_tuple == baseline_tuple:
        decision = "witness_shadow_trivial_tie"
    elif shadow_tuple < baseline_tuple:
        decision = "resist_shadow_under_baseline"
    elif not exact_minimum_ready:
        decision = "witness_shadow_beats_available_baselines_exact_minimum_incomplete"
    else:
        decision = "expand_shadow_nontrivial_not_detector"
    return {"decision": decision, "shadow_model": shadow, "best_available_baseline": best_baseline, **status}


def _target_diagnostic_rows(
    *,
    rung: str,
    scope: str,
    metric_rows: list[dict[str, object]],
    feature_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    targets = sorted({str(row["target_name"]) for row in metric_rows})
    for target_name in targets:
        rows = [row for row in metric_rows if row["target_name"] == target_name]
        shadow = next((row for row in rows if row["model_name"] == "shadow_score"), None)
        baselines = [row for row in rows if row["model_name"] != "shadow_score"]
        best_baseline = _best_metric(baselines)
        best = _best_metric(rows)
        comparable = int(shadow.get("comparable_pairs", 0) or 0) if shadow else 0
        target_status = "informative" if comparable > 0 else "insufficient_variation"
        shadow_vs_baseline = "shadow_missing"
        if shadow and best_baseline:
            shadow_tuple = (
                float(shadow.get("pairwise_order_accuracy", 0) or 0),
                float(shadow.get("spearman_rank_correlation", 0) or 0),
                float(shadow.get("top_bucket_target_lift", 0) or 0),
            )
            baseline_tuple = (
                float(best_baseline.get("pairwise_order_accuracy", 0) or 0),
                float(best_baseline.get("spearman_rank_correlation", 0) or 0),
                float(best_baseline.get("top_bucket_target_lift", 0) or 0),
            )
            if shadow_tuple == baseline_tuple:
                shadow_vs_baseline = "shadow_right_but_trivial_tie"
            elif shadow_tuple > baseline_tuple:
                shadow_vs_baseline = "shadow_above_best_available_baseline"
            else:
                shadow_vs_baseline = "shadow_below_best_available_baseline"
        status = _baseline_status(feature_rows, rows)
        exact_minimum_ready = all(
            item["status"] == "available_exact"
            for item in status["minimum_baseline_status"].values()  # type: ignore[index]
        )
        out.append(
            {
                "rung": rung,
                "scope": scope,
                "target_name": target_name,
                "target_status": target_status,
                "shadow_vs_baseline": shadow_vs_baseline,
                "shadow_pairwise_order_accuracy": shadow.get("pairwise_order_accuracy", "") if shadow else "",
                "shadow_spearman_rank_correlation": shadow.get("spearman_rank_correlation", "") if shadow else "",
                "shadow_top_bucket_target_lift": shadow.get("top_bucket_target_lift", "") if shadow else "",
                "best_available_baseline": best_baseline.get("model_name", "") if best_baseline else "",
                "best_available_baseline_pairwise_order_accuracy": best_baseline.get("pairwise_order_accuracy", "") if best_baseline else "",
                "best_model": best.get("model_name", "") if best else "",
                "exact_minimum_baselines_ready": str(exact_minimum_ready),
            }
        )
    return out


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _native_gate_rows(seed_summary: Path | None, *, rung: str) -> list[dict[str, object]]:
    if seed_summary is None or not seed_summary.exists():
        return [
            {
                "rung": rung,
                "gate": "missing_seed_summary",
                "native_status": "witness_native_summary_not_supplied",
                "total_runs": 0,
                "raw_false_one_pressure": 0,
                "false_one_demoted_count": 0,
                "final_false_one_crowns": 0,
                "mirror_safety_breach_total": 0,
                "native_witness": "C_Z = min(D, P, R, B)",
            }
        ]
    rows = _read_csv(seed_summary)
    out: list[dict[str, object]] = []
    for row in rows:
        final_false = _int(row, "final_false_one_crowns")
        breach = _int(row, "mirror_safety_breach_total")
        pressure = _int(row, "raw_false_one_pressure") + _int(row, "latent_overcrown_pressure") + _int(row, "relation_debt_count")
        if final_false or breach:
            status = "resist_native_breach"
        elif pressure:
            status = "expand_native_pressure_visible_no_breach"
        else:
            status = "witness_native_quiet_no_breach"
        out.append(
            {
                "rung": rung,
                "gate": row.get("gate", ""),
                "native_status": status,
                "total_runs": row.get("total_runs", ""),
                "raw_expression_pressure": row.get("raw_expression_pressure", ""),
                "raw_false_one_pressure": row.get("raw_false_one_pressure", ""),
                "false_one_demoted_count": row.get("false_one_demoted_count", ""),
                "latent_overcrown_pressure": row.get("latent_overcrown_pressure", ""),
                "relation_debt_count": row.get("relation_debt_count", ""),
                "final_false_one_crowns": final_false,
                "mirror_safety_breach_total": breach,
                "native_witness": "C_Z = min(D, P, R, B)",
            }
        )
    return out


def parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"Expected RUNG=BASE_DIR, got: {value}")
    label, base = value.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Missing rung label in RUNG=BASE_DIR value: {value}")
    return label, Path(base.strip())


def _source_paths(label: str, base_dir: Path) -> dict[str, Path | str]:
    out: dict[str, Path | str] = {"rung": label, "base_dir": base_dir}
    for key, subpath in STANDARD_BASE_SUBPATHS.items():
        out[key] = base_dir / subpath
    return out


def _load_source(source: dict[str, Path | str]) -> dict[str, object]:
    rung = str(source["rung"])
    profile_features = Path(source["profile_features"])
    family_features = Path(source["family_features"])
    profile_scores = Path(source["profile_scores"])
    family_scores = Path(source["family_scores"])
    evaluation_targets = Path(source["evaluation_targets"])
    seed_summary = Path(source["seed_summary"])

    profile_feature_rows = _read_csv(profile_features)
    family_feature_rows = _read_csv(family_features)
    profile_score_rows = _read_csv(profile_scores)
    family_score_rows = _read_csv(family_scores)
    target_rows = _read_csv(evaluation_targets)
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

    target_fields = _target_fields(target_rows)
    profile_targets, family_targets = _split_targets(target_rows)
    joined_profile = _join_scope_rows(scope="profile", feature_rows=profile_feature_rows, score_rows=profile_score_rows, target_rows=profile_targets)
    joined_family = _join_scope_rows(scope="family", feature_rows=family_feature_rows, score_rows=family_score_rows, target_rows=family_targets)
    profile_comparison = _comparison_rows_for_joined(joined_profile, rung=rung, scope="profile", target_fields=target_fields)
    family_comparison = _comparison_rows_for_joined(joined_family, rung=rung, scope="family", target_fields=target_fields)
    profile_metrics = _metrics_from_comparison(profile_comparison)
    family_metrics = _metrics_from_comparison(family_comparison)
    return {
        "rung": rung,
        "target_fields": target_fields,
        "profile_feature_rows": profile_feature_rows,
        "family_feature_rows": family_feature_rows,
        "profile_comparison": profile_comparison,
        "family_comparison": family_comparison,
        "profile_metrics": profile_metrics,
        "family_metrics": family_metrics,
        "profile_diagnostics": _target_diagnostic_rows(rung=rung, scope="profile", metric_rows=profile_metrics, feature_rows=profile_feature_rows),
        "family_diagnostics": _target_diagnostic_rows(rung=rung, scope="family", metric_rows=family_metrics, feature_rows=family_feature_rows),
        "profile_decision": _primary_target_decision(profile_metrics, profile_feature_rows, target_name="target_raw_false_one_rate"),
        "family_decision": _primary_target_decision(family_metrics, family_feature_rows, target_name="target_raw_false_one_rate"),
        "native_gate_rows": _native_gate_rows(seed_summary, rung=rung),
    }


def _source_label_matches(rows: list[dict[str, str]], rung: str) -> bool:
    source_values = {str(row.get("source_label", "") or "").lower() for row in rows}
    profile_values = {str(row.get("source_profile", "") or "").lower() for row in rows}
    rung_norm = rung.lower()
    return any(rung_norm in value for value in source_values | profile_values)


def _global_decision(source_results: list[dict[str, object]], required_rungs: Sequence[str]) -> str:
    loaded = {str(result["rung"]) for result in source_results}
    missing = [rung for rung in required_rungs if rung not in loaded]
    native_rows = [row for result in source_results for row in result["native_gate_rows"]]  # type: ignore[index]
    if any(str(row.get("native_status", "")).startswith("resist") for row in native_rows):
        return "resist_native_breach"
    if missing:
        return "witness_weather_ladder_incomplete"
    decisions = [str(result["profile_decision"]["decision"]) for result in source_results]  # type: ignore[index]
    decisions.extend(str(result["family_decision"]["decision"]) for result in source_results)  # type: ignore[index]
    if any(decision.startswith("resist") for decision in decisions):
        return "resist_shadow_under_hardened_weather"
    if any("trivial_tie" in decision for decision in decisions):
        return "witness_shadow_trivial_under_hardened_weather"
    if any(decision.startswith("hold") or decision.startswith("witness") for decision in decisions):
        return "witness_shadow_not_closed_under_hardened_weather"
    return "expand_shadow_nontrivial_hardened_weather_not_detector"


def _write_read(path: Path, *, source_results: list[dict[str, object]], required_rungs: Sequence[str], global_decision: str) -> None:
    loaded = [str(result["rung"]) for result in source_results]
    lines: list[str] = []
    lines.append("# ZeroGateSim Shadow Weather Hardening Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This `v1.6.7-alpha` report hardens the shadow evaluation lane before any deeper holdout or closeout claim. It does not tune the shadow score, does not crown or demote candidates, and does not claim role-blind discovery.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append("## Weather ladder")
    lines.append("")
    lines.append("```text")
    lines.append("triad27 = 3^3 local expression weather")
    lines.append("deep81  = 3^4 perturbation / late-shock bridge")
    lines.append("wide243 = 3^5 temporal-depth / time-axis stress")
    lines.append("```")
    lines.append("")
    for rung, description in WEATHER_LADDER.items():
        marker = "loaded" if rung in loaded else "missing"
        lines.append(f"- `{rung}` — {description}; status: `{marker}`")
    lines.append("")
    lines.append(f"Global hardening decision: `{global_decision}`")
    lines.append("")
    lines.append("## What became harder")
    lines.append("")
    lines.append("- evaluates every supplied rung through one report instead of letting triad27, deep81, and wide243 live as separate green-looking islands;")
    lines.append("- evaluates all available target fields, not only raw false-one rate;")
    lines.append("- names shadow/right-but-trivial ties against dumb baselines instead of calling them wins;")
    lines.append("- records native gate pressure and final false-crown breaches beside shadow diagnostics;")
    lines.append("- keeps score-first / targets-later separation intact.")
    lines.append("")
    for result in source_results:
        rung = str(result["rung"])
        lines.append(f"## {rung} result")
        lines.append("")
        lines.append(f"Profile decision: `{result['profile_decision']['decision']}`")  # type: ignore[index]
        lines.append(f"Family decision: `{result['family_decision']['decision']}`")  # type: ignore[index]
        lines.append(f"Targets evaluated: `{', '.join(result['target_fields'])}`")  # type: ignore[index]
        lines.append("")
        lines.append("### Target diagnostics")
        lines.append("")
        lines.append("| scope | target | status | shadow vs baseline | best baseline | best model |")
        lines.append("|---|---|---|---|---|---|")
        diagnostics = list(result["profile_diagnostics"]) + list(result["family_diagnostics"])  # type: ignore[index]
        for row in diagnostics:
            lines.append(
                f"| {row['scope']} | {row['target_name']} | {row['target_status']} | "
                f"{row['shadow_vs_baseline']} | {row['best_available_baseline']} | {row['best_model']} |"
            )
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("A shadow score that is right but trivial because raw-pressure or mirror baselines are equally right has not earned scientific value. This report treats that as a witness or resist state, not a victory.")
    lines.append("")
    lines.append("If triad27 is still trivial, do not advance trust to deep81/wide243. If deep81 or wide243 are missing, the ladder is incomplete. If all rungs survive non-trivially, the only earned wording is `survived this hardened role-stripped weather comparison`, not `solved role-blind false-one detection`.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / WEATHER_HARDENING_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_shadow_weather_hardening_bundle",
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


def write_shadow_weather_hardening_report(
    *,
    output_dir: Path,
    sources: dict[str, Path],
    required_rungs: Sequence[str] = DEFAULT_REQUIRED_RUNGS,
) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    if not sources:
        raise ValueError("At least one RUNG=BASE_DIR source is required.")
    source_results: list[dict[str, object]] = []
    source_audit: list[dict[str, object]] = []
    for rung, base_dir in sorted(sources.items()):
        source = _source_paths(rung, Path(base_dir))
        result = _load_source(source)
        profile_feature_rows = result["profile_feature_rows"]  # type: ignore[assignment]
        family_feature_rows = result["family_feature_rows"]  # type: ignore[assignment]
        assert isinstance(profile_feature_rows, list)
        assert isinstance(family_feature_rows, list)
        source_audit.append(
            {
                "rung": rung,
                "base_dir": str(base_dir),
                "profile_source_label_matches_rung": _source_label_matches(profile_feature_rows, rung),
                "family_source_label_matches_rung": _source_label_matches(family_feature_rows, rung),
                "profile_feature_forbidden_fields_found": _forbidden_header_fields(profile_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
                "family_feature_forbidden_fields_found": _forbidden_header_fields(family_feature_rows, FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
            }
        )
        source_results.append(result)

    baseline_comparison_rows: list[dict[str, object]] = []
    target_diagnostics: list[dict[str, object]] = []
    native_gate_rows: list[dict[str, object]] = []
    for result in source_results:
        baseline_comparison_rows.extend(result["profile_comparison"])  # type: ignore[arg-type]
        baseline_comparison_rows.extend(result["family_comparison"])  # type: ignore[arg-type]
        target_diagnostics.extend(result["profile_diagnostics"])  # type: ignore[arg-type]
        target_diagnostics.extend(result["family_diagnostics"])  # type: ignore[arg-type]
        native_gate_rows.extend(result["native_gate_rows"])  # type: ignore[arg-type]

    global_decision = _global_decision(source_results, required_rungs)

    baseline_path = output_dir / WEATHER_HARDENING_FILES["baseline_comparison"]
    diagnostics_path = output_dir / WEATHER_HARDENING_FILES["target_diagnostics"]
    native_path = output_dir / WEATHER_HARDENING_FILES["native_gate_metrics"]
    decision_path = output_dir / WEATHER_HARDENING_FILES["decision"]
    audit_path = output_dir / WEATHER_HARDENING_FILES["audit"]
    read_path = output_dir / WEATHER_HARDENING_FILES["read"]

    _write_csv(baseline_path, baseline_comparison_rows)
    _write_csv(diagnostics_path, target_diagnostics)
    _write_csv(native_path, native_gate_rows)

    decision = {
        "version": "v1.6.7-alpha",
        "report_name": "shadow_weather_hardening_report",
        "global_decision": global_decision,
        "required_rungs": list(required_rungs),
        "loaded_rungs": [str(result["rung"]) for result in source_results],
        "weather_ladder": WEATHER_LADDER,
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "score_freeze_boundary": "the report reads already-written shadow scores and does not tune score weights",
        "role_blind_boundary": "hardened weather comparison only; no role-blind discovery claim",
        "per_rung": {
            str(result["rung"]): {
                "target_fields": result["target_fields"],
                "profile_decision": result["profile_decision"],
                "family_decision": result["family_decision"],
            }
            for result in source_results
        },
    }
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "feature_and_score_inputs_role_stripped": True,
        "targets_loaded_after_scoring_for_evaluation_only": True,
        "source_audit": source_audit,
        "forbidden_shadow_input_fields": sorted(FORBIDDEN_SHADOW_INPUT_FIELDS),
        "forbidden_feature_or_score_fields": sorted(FORBIDDEN_FEATURE_OR_SCORE_FIELDS),
        "score_freeze_boundary": "no score retuning in v1.6.7-alpha",
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    _write_read(read_path, source_results=source_results, required_rungs=required_rungs, global_decision=global_decision)
    bundle_path = _write_bundle(output_dir)
    return {
        "weather_hardening_baseline_comparison": baseline_path,
        "weather_hardening_target_diagnostics": diagnostics_path,
        "weather_hardening_native_gate_metrics": native_path,
        "weather_hardening_decision": decision_path,
        "weather_hardening_audit": audit_path,
        "weather_hardening_read": read_path,
        "weather_hardening_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harden ZeroGateSim shadow evaluation across triad27/deep81/wide243 weather evidence without retuning the score.")
    parser.add_argument("--source", action="append", default=[], help="Evidence source in the form RUNG=BASE_DIR. BASE_DIR must contain role_stripped/ and shadow_score/ outputs; seed_block/ is read when present.")
    parser.add_argument("--required-rung", action="append", default=[], help="Required weather rung. Defaults to triad27, deep81, and wide243.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_weather_hardening_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = dict(parse_source(value) for value in args.source)
    required_rungs = tuple(args.required_rung) if args.required_rung else DEFAULT_REQUIRED_RUNGS
    paths = write_shadow_weather_hardening_report(output_dir=args.out, sources=sources, required_rungs=required_rungs)
    print("ZeroGateSim shadow weather hardening report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
