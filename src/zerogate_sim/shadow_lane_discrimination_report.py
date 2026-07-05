from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from zerogate_sim.shadow_discrimination_report import LANE_BY_TARGET

LANE_DISCRIMINATION_FILES = {
    "metrics": "shadow_lane_discrimination_metrics.csv",
    "lane_summary": "shadow_lane_discrimination_summary.csv",
    "decision": "shadow_lane_discrimination_decision.json",
    "audit": "shadow_lane_discrimination_audit.json",
    "read": "shadow_lane_discrimination_read.md",
    "bundle": "shadow_lane_discrimination_bundle.zip",
}

TARGET_TO_LANE_SCORE = {
    "target_false_pressure_density_rate": "shadow_density_pressure_score",
    "target_raw_false_one_rate": "shadow_raw_false_one_pressure_score",
    "target_false_one_demotion_rate": "shadow_demotion_pressure_score",
    "target_hold_or_demote_rate": "shadow_hold_or_demote_pressure_score",
    "target_relation_false_pressure_share": "shadow_relation_specific_pressure_score",
    "target_return_false_pressure_share": "shadow_return_specific_pressure_score",
    "target_native_breach_rate": "shadow_native_breach_proxy_score",
}

STANDARD_BASE_SUBPATHS = {
    "family_scores": Path("shadow_score") / "shadow_score_family_scores.csv",
    "evaluation_targets": Path("role_stripped") / "role_stripped_evaluation_targets.csv",
    "hardening_comparison": Path("weather_hardening") / "weather_hardening_baseline_comparison.csv",
}

NON_BASELINE_MODELS = set(TARGET_TO_LANE_SCORE.values()) | {"shadow_score"}


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


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _zscore(values: Sequence[float]) -> list[float]:
    sd = _std(values)
    mean = _mean(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [(value - mean) / sd for value in values]


def _rankdata(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg
        i = j
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
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


def _metric(scores: Sequence[float], targets: Sequence[float]) -> dict[str, object]:
    comparable, pairwise = _pairwise_accuracy(scores, targets)
    top_n = max(1, math.ceil(len(scores) * 0.25)) if scores else 0
    order = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    top_targets = [targets[index] for index in order[:top_n]]
    mean_top = _mean(top_targets)
    mean_all = _mean(targets)
    lift = (mean_top / mean_all) if mean_all else 0.0
    return {
        "row_count": len(scores),
        "comparable_pairs": comparable,
        "pairwise_order_accuracy": _format_float(pairwise),
        "spearman_rank_correlation": _format_float(_spearman(scores, targets)),
        "top_bucket_size": top_n,
        "top_bucket_target_lift": _format_float(lift),
    }


def _metric_tuple(row: dict[str, object]) -> tuple[float, float, float]:
    return (
        float(row.get("pairwise_order_accuracy", 0) or 0),
        float(row.get("spearman_rank_correlation", 0) or 0),
        float(row.get("top_bucket_target_lift", 0) or 0),
    )


def _key(row: dict[str, str]) -> str:
    return f"{row.get('source_label', '')}::{row.get('family_id', '')}"


def _target_rows_by_key(target_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {_key(row): row for row in target_rows if str(row.get("family_id", "") or "").strip()}


def _score_rows_by_key(score_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {_key(row): row for row in score_rows if str(row.get("family_id", "") or "").strip()}


def _comparison_groups(comparison_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in comparison_rows:
        if row.get("scope") != "family":
            continue
        grouped[str(row.get("target_name", ""))].append(row)
    return grouped


def _baseline_metric_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_model: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    for row in rows:
        model = str(row.get("model_name", ""))
        if not model or model in NON_BASELINE_MODELS or model.startswith("shadow_"):
            continue
        key = str(row.get("row_key", ""))
        by_model[model][key] = (_float(row, "model_score"), _float(row, "target_value"))
    metrics: list[dict[str, object]] = []
    for model, values in sorted(by_model.items()):
        ordered = sorted(values)
        scores = [values[key][0] for key in ordered]
        targets = [values[key][1] for key in ordered]
        metric = _metric(scores, targets)
        metric["model_name"] = model
        metrics.append(metric)
    return metrics


def _best_metric(rows: list[dict[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    return max(rows, key=_metric_tuple)


def _baseline_score_by_key(rows: list[dict[str, str]], model_name: str) -> dict[str, float]:
    return {
        str(row.get("row_key", "")): _float(row, "model_score")
        for row in rows
        if row.get("model_name") == model_name
    }


def _target_values_by_key(rows: list[dict[str, str]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in rows:
        key = str(row.get("row_key", ""))
        if key and key not in out:
            out[key] = _float(row, "target_value")
    return out


def _lane_decision(lane_metric: dict[str, object] | None, best_baseline: dict[str, object] | None, residual_pairwise: float, residual_spearman: float) -> str:
    if lane_metric is None:
        return "resist_lane_score_missing"
    if int(lane_metric.get("comparable_pairs", 0) or 0) <= 0:
        return "hold_insufficient_variation"
    if best_baseline is None:
        return "hold_no_available_baseline"
    lane_tuple = _metric_tuple(lane_metric)
    baseline_tuple = _metric_tuple(best_baseline)
    if lane_tuple < baseline_tuple:
        return "resist_lane_under_baseline"
    if lane_tuple == baseline_tuple:
        return "witness_lane_trivial_tie"
    if residual_pairwise >= 0.55 and residual_spearman > 0.15:
        return "expand_lane_above_baseline_with_residual_signal_not_detector"
    return "witness_lane_above_baseline_but_residual_weak"


def _metrics_for_target(*, target_name: str, score_column: str, score_by_key: dict[str, dict[str, str]], target_by_key: dict[str, dict[str, str]], comparison_rows: list[dict[str, str]]) -> dict[str, object]:
    keys = sorted(key for key in score_by_key if key in target_by_key and target_name in target_by_key[key])
    lane_scores = [_float(score_by_key[key], score_column) for key in keys]
    targets = [_float(target_by_key[key], target_name) for key in keys]
    lane_metric = _metric(lane_scores, targets) if keys else None
    baseline_metrics = _baseline_metric_rows(comparison_rows)
    best_baseline = _best_metric(baseline_metrics)
    residual_pairwise = 0.0
    residual_spearman = 0.0
    best_name = ""
    if best_baseline is not None and keys:
        best_name = str(best_baseline["model_name"])
        baseline_by_key = _baseline_score_by_key(comparison_rows, best_name)
        target_by_comparison_key = _target_values_by_key(comparison_rows)
        aligned_keys = [key for key in keys if key in baseline_by_key and key in target_by_comparison_key]
        if aligned_keys:
            residual_target = [a - b for a, b in zip(_zscore([target_by_comparison_key[key] for key in aligned_keys]), _zscore([baseline_by_key[key] for key in aligned_keys]))]
            aligned_lane = [_float(score_by_key[key], score_column) for key in aligned_keys]
            _, residual_pairwise = _pairwise_accuracy(aligned_lane, residual_target)
            residual_spearman = _spearman(aligned_lane, residual_target)
    decision = _lane_decision(lane_metric, best_baseline, residual_pairwise, residual_spearman)
    lane = LANE_BY_TARGET.get(target_name, target_name.replace("target_", ""))
    out = {
        "scope": "family",
        "target_name": target_name,
        "lane": lane,
        "lane_score_column": score_column,
        "lane_decision": decision,
        "row_count": len(keys),
        "best_baseline_model": best_name,
        "lane_residual_pairwise_order_accuracy": _format_float(residual_pairwise),
        "lane_residual_spearman": _format_float(residual_spearman),
    }
    if lane_metric is not None:
        for key, value in lane_metric.items():
            out[f"lane_{key}"] = value
    if best_baseline is not None:
        for key, value in best_baseline.items():
            out[f"best_baseline_{key}"] = value
        out["lane_minus_baseline_pairwise"] = _format_float(float(out.get("lane_pairwise_order_accuracy", 0) or 0) - float(best_baseline.get("pairwise_order_accuracy", 0) or 0))
        out["lane_minus_baseline_spearman"] = _format_float(float(out.get("lane_spearman_rank_correlation", 0) or 0) - float(best_baseline.get("spearman_rank_correlation", 0) or 0))
        out["lane_minus_baseline_lift"] = _format_float(float(out.get("lane_top_bucket_target_lift", 0) or 0) - float(best_baseline.get("top_bucket_target_lift", 0) or 0))
    return out


def _global_decision(rows: list[dict[str, object]]) -> str:
    by_lane = {str(row["lane"]): str(row["lane_decision"]) for row in rows}
    density_expands = by_lane.get("density_pressure", "").startswith("expand")
    specific_lanes = ["raw_false_one", "demotion", "hold_or_demote", "relation_specific", "return_specific"]
    specific_expands = [lane for lane in specific_lanes if by_lane.get(lane, "").startswith("expand")]
    specific_resists = [lane for lane in specific_lanes if by_lane.get(lane, "").startswith("resist")]
    if specific_expands and not specific_resists:
        return "expand_lane_split_specific_candidate_not_detector"
    if density_expands and specific_resists:
        return "witness_lane_split_density_only_specific_not_earned"
    if specific_resists:
        return "resist_lane_split_specific_discrimination_not_earned"
    if any("trivial" in decision for decision in by_lane.values()):
        return "witness_lane_split_trivial_ties_not_closed"
    return "witness_lane_split_not_closed"


def _write_read(path: Path, *, decision: dict[str, object], rows: list[dict[str, object]]) -> None:
    lines = [
        "# ZeroGateSim Shadow Lane Discrimination Report",
        "",
        "## Claim boundary",
        "",
        "This `v1.6.10-alpha` report does not retune the historical shadow score and does not claim role-blind discovery. It evaluates fixed lane-specific candidate scores against separated targets and dumb baselines. It is not role-blind discovery.",
        "",
        "The native witness remains:",
        "",
        "```text",
        "C_Z = min(D, P, R, B)",
        "```",
        "",
        f"Global lane decision: `{decision['global_decision']}`",
        "",
        "## Lane decisions",
        "",
        "| lane | target | score column | decision | best baseline | lane pairwise | baseline pairwise | residual spearman |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['lane']} | {row['target_name']} | {row['lane_score_column']} | {row['lane_decision']} | "
            f"{row.get('best_baseline_model', '')} | {row.get('lane_pairwise_order_accuracy', '')} | "
            f"{row.get('best_baseline_pairwise_order_accuracy', '')} | {row.get('lane_residual_spearman', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A lane can only earn candidate signal if it beats the best available dumb baseline and shows residual structure after that baseline has explained the easy pressure. This is still a report-side candidate signal, not detector closeout.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / LANE_DISCRIMINATION_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_shadow_lane_discrimination_bundle",
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


def _resolve_standard_paths(evidence_base: Path | None, family_scores: Path | None, evaluation_targets: Path | None, hardening_comparison: Path | None) -> tuple[Path, Path, Path]:
    if evidence_base is not None:
        base = Path(evidence_base)
        family_scores = family_scores or base / STANDARD_BASE_SUBPATHS["family_scores"]
        evaluation_targets = evaluation_targets or base / STANDARD_BASE_SUBPATHS["evaluation_targets"]
        hardening_comparison = hardening_comparison or base / STANDARD_BASE_SUBPATHS["hardening_comparison"]
    if family_scores is None or evaluation_targets is None or hardening_comparison is None:
        raise ValueError("Supply --evidence-base or all of --family-scores, --evaluation-targets, and --hardening-comparison.")
    return Path(family_scores), Path(evaluation_targets), Path(hardening_comparison)


def write_shadow_lane_discrimination_report(
    *,
    output_dir: Path,
    evidence_base: Path | None = None,
    family_scores: Path | None = None,
    evaluation_targets: Path | None = None,
    hardening_comparison: Path | None = None,
) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    family_scores, evaluation_targets, hardening_comparison = _resolve_standard_paths(evidence_base, family_scores, evaluation_targets, hardening_comparison)

    score_rows = _read_csv(family_scores)
    target_rows = _read_csv(evaluation_targets)
    comparison_rows = _read_csv(hardening_comparison)
    score_by_key = _score_rows_by_key(score_rows)
    target_by_key = _target_rows_by_key(target_rows)
    comparison_by_target = _comparison_groups(comparison_rows)

    missing_score_columns = sorted(score for score in TARGET_TO_LANE_SCORE.values() if score_rows and score not in score_rows[0])
    if missing_score_columns:
        raise ValueError("Missing lane score columns in family score input: " + ", ".join(missing_score_columns))

    metric_rows: list[dict[str, object]] = []
    for target_name, score_column in TARGET_TO_LANE_SCORE.items():
        if target_name not in comparison_by_target:
            continue
        metric_rows.append(
            _metrics_for_target(
                target_name=target_name,
                score_column=score_column,
                score_by_key=score_by_key,
                target_by_key=target_by_key,
                comparison_rows=comparison_by_target[target_name],
            )
        )

    decision = {
        "version": "v1.6.10-alpha",
        "global_decision": _global_decision(metric_rows),
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "score_boundary": "fixed lane-specific report-side candidate scores; no retuning and no role-blind discovery claim",
        "lane_count": len(metric_rows),
        "lane_decisions": {str(row["lane"]): str(row["lane_decision"]) for row in metric_rows},
    }

    metrics_path = output_dir / LANE_DISCRIMINATION_FILES["metrics"]
    summary_path = output_dir / LANE_DISCRIMINATION_FILES["lane_summary"]
    decision_path = output_dir / LANE_DISCRIMINATION_FILES["decision"]
    audit_path = output_dir / LANE_DISCRIMINATION_FILES["audit"]
    read_path = output_dir / LANE_DISCRIMINATION_FILES["read"]

    _write_csv(metrics_path, metric_rows)
    _write_csv(
        summary_path,
        [
            {
                "lane": row["lane"],
                "target_name": row["target_name"],
                "lane_score_column": row["lane_score_column"],
                "lane_decision": row["lane_decision"],
                "best_baseline_model": row.get("best_baseline_model", ""),
                "lane_minus_baseline_pairwise": row.get("lane_minus_baseline_pairwise", ""),
                "lane_residual_spearman": row.get("lane_residual_spearman", ""),
            }
            for row in metric_rows
        ],
    )
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    audit = {
        "report_name": "shadow_lane_discrimination_report",
        "family_scores": str(family_scores),
        "evaluation_targets": str(evaluation_targets),
        "hardening_comparison": str(hardening_comparison),
        "target_to_lane_score": TARGET_TO_LANE_SCORE,
        "targets_loaded_after_scoring_only": True,
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    _write_read(read_path, decision=decision, rows=metric_rows)
    bundle_path = _write_bundle(output_dir)
    return {
        "shadow_lane_discrimination_metrics": metrics_path,
        "shadow_lane_discrimination_summary": summary_path,
        "shadow_lane_discrimination_decision": decision_path,
        "shadow_lane_discrimination_audit": audit_path,
        "shadow_lane_discrimination_read": read_path,
        "shadow_lane_discrimination_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate fixed lane-specific shadow candidate scores against hardened weather baselines.")
    parser.add_argument("--evidence-base", type=Path, help="Standard evidence base containing role_stripped/, shadow_score/, and weather_hardening/.")
    parser.add_argument("--family-scores", type=Path, help="Path to shadow_score_family_scores.csv with v1.6.10 lane score columns.")
    parser.add_argument("--evaluation-targets", type=Path, help="Path to role_stripped_evaluation_targets.csv.")
    parser.add_argument("--hardening-comparison", type=Path, help="Path to weather_hardening_baseline_comparison.csv.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_lane_discrimination_v1_6_10"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_shadow_lane_discrimination_report(
        output_dir=args.out,
        evidence_base=args.evidence_base,
        family_scores=args.family_scores,
        evaluation_targets=args.evaluation_targets,
        hardening_comparison=args.hardening_comparison,
    )
    print("ZeroGateSim shadow lane discrimination report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
