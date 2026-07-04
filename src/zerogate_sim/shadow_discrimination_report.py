from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

DISCRIMINATION_FILES = {
    "target_metrics": "shadow_discrimination_target_metrics.csv",
    "residual_metrics": "shadow_discrimination_residual_metrics.csv",
    "lane_summary": "shadow_discrimination_lane_summary.csv",
    "decision": "shadow_discrimination_decision.json",
    "audit": "shadow_discrimination_audit.json",
    "read": "shadow_discrimination_read.md",
    "bundle": "shadow_discrimination_bundle.zip",
}

LANE_BY_TARGET = {
    "target_false_pressure_density_rate": "density_pressure",
    "target_raw_false_one_rate": "raw_false_one",
    "target_false_one_demotion_rate": "demotion",
    "target_hold_or_demote_rate": "hold_or_demote",
    "target_relation_false_pressure_share": "relation_specific",
    "target_return_false_pressure_share": "return_specific",
    "target_native_breach_rate": "native_breach_proxy",
}

IMPORTANT_TARGETS = tuple(LANE_BY_TARGET.keys())


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


def _best_metric(rows: list[dict[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None
    return max(rows, key=_metric_tuple)


def _group_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("rung", ""), row.get("scope", ""), row.get("target_name", ""))].append(row)
    return grouped


def _pivot_group(rows: list[dict[str, str]]) -> tuple[list[str], dict[str, dict[str, float]], list[float]]:
    row_keys = sorted({row["row_key"] for row in rows})
    targets_by_key = {row["row_key"]: _float(row, "target_value") for row in rows}
    models = sorted({row["model_name"] for row in rows})
    scores: dict[str, dict[str, float]] = {model: {} for model in models}
    for row in rows:
        scores[row["model_name"]][row["row_key"]] = _float(row, "model_score")
    targets = [targets_by_key[key] for key in row_keys]
    return row_keys, scores, targets


def _target_decision(shadow: dict[str, object] | None, best_baseline: dict[str, object] | None, residual: dict[str, object] | None) -> str:
    if shadow is None:
        return "resist_shadow_missing"
    if int(shadow.get("comparable_pairs", 0) or 0) <= 0:
        return "hold_insufficient_variation"
    if best_baseline is None:
        return "hold_no_available_baseline"
    shadow_tuple = _metric_tuple(shadow)
    baseline_tuple = _metric_tuple(best_baseline)
    if shadow_tuple < baseline_tuple:
        return "resist_shadow_under_baseline"
    if shadow_tuple == baseline_tuple:
        return "witness_shadow_trivial_tie"
    if residual is not None:
        residual_spearman = float(residual.get("shadow_residual_spearman", 0) or 0)
        residual_pairwise = float(residual.get("shadow_residual_pairwise_order_accuracy", 0) or 0)
        if residual_pairwise >= 0.55 and residual_spearman > 0.15:
            return "expand_shadow_above_baseline_with_residual_signal_not_detector"
        return "witness_shadow_above_baseline_but_residual_weak"
    return "expand_shadow_above_baseline_not_detector"


def _target_metrics_and_residuals(comparison_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    target_metrics: list[dict[str, object]] = []
    residual_metrics: list[dict[str, object]] = []
    for (rung, scope, target_name), rows in sorted(_group_rows(comparison_rows).items()):
        row_keys, model_scores, targets = _pivot_group(rows)
        group_metrics: list[dict[str, object]] = []
        for model_name, score_by_key in sorted(model_scores.items()):
            if any(key not in score_by_key for key in row_keys):
                continue
            scores = [score_by_key[key] for key in row_keys]
            metric = _metric(scores, targets)
            metric.update({"rung": rung, "scope": scope, "target_name": target_name, "model_name": model_name})
            group_metrics.append(metric)
            target_metrics.append(metric)

        shadow = next((row for row in group_metrics if row["model_name"] == "shadow_score"), None)
        baselines = [row for row in group_metrics if row["model_name"] != "shadow_score"]
        best_baseline = _best_metric(baselines)
        if shadow is None or best_baseline is None:
            continue
        baseline_name = str(best_baseline["model_name"])
        shadow_scores = [model_scores["shadow_score"][key] for key in row_keys]
        baseline_scores = [model_scores[baseline_name][key] for key in row_keys]
        target_z = _zscore(targets)
        baseline_z = _zscore(baseline_scores)
        residual_target = [target - base for target, base in zip(target_z, baseline_z)]
        comparable, pairwise = _pairwise_accuracy(shadow_scores, residual_target)
        residual_row = {
            "rung": rung,
            "scope": scope,
            "target_name": target_name,
            "lane": LANE_BY_TARGET.get(target_name, "other"),
            "row_count": len(row_keys),
            "best_baseline_model": baseline_name,
            "shadow_pairwise_order_accuracy": shadow["pairwise_order_accuracy"],
            "best_baseline_pairwise_order_accuracy": best_baseline["pairwise_order_accuracy"],
            "shadow_spearman_rank_correlation": shadow["spearman_rank_correlation"],
            "best_baseline_spearman_rank_correlation": best_baseline["spearman_rank_correlation"],
            "shadow_top_bucket_target_lift": shadow["top_bucket_target_lift"],
            "best_baseline_top_bucket_target_lift": best_baseline["top_bucket_target_lift"],
            "shadow_minus_baseline_pairwise": _format_float(float(shadow["pairwise_order_accuracy"]) - float(best_baseline["pairwise_order_accuracy"])),
            "shadow_minus_baseline_spearman": _format_float(float(shadow["spearman_rank_correlation"]) - float(best_baseline["spearman_rank_correlation"])),
            "shadow_minus_baseline_lift": _format_float(float(shadow["top_bucket_target_lift"]) - float(best_baseline["top_bucket_target_lift"])),
            "residual_target_definition": "z(target)-z(best_available_baseline_score)",
            "shadow_residual_comparable_pairs": comparable,
            "shadow_residual_pairwise_order_accuracy": _format_float(pairwise),
            "shadow_residual_spearman": _format_float(_spearman(shadow_scores, residual_target)),
        }
        residual_row["target_decision"] = _target_decision(shadow, best_baseline, residual_row)
        residual_metrics.append(residual_row)
    return target_metrics, residual_metrics


def _lane_summary_rows(residual_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in residual_rows:
        grouped[(str(row["rung"]), str(row["scope"]), str(row["lane"]))].append(row)
    out: list[dict[str, object]] = []
    for (rung, scope, lane), rows in sorted(grouped.items()):
        decisions = [str(row["target_decision"]) for row in rows]
        if any(decision.startswith("expand") or "above_baseline" in decision for decision in decisions):
            lane_state = "expand_lane_has_candidate_signal"
        elif any(decision.startswith("resist") for decision in decisions):
            lane_state = "resist_lane_under_baseline"
        elif any("trivial" in decision for decision in decisions):
            lane_state = "witness_lane_trivial_tie"
        else:
            lane_state = "witness_lane_not_closed"
        out.append(
            {
                "rung": rung,
                "scope": scope,
                "lane": lane,
                "target_count": len(rows),
                "lane_state": lane_state,
                "targets": ",".join(str(row["target_name"]) for row in rows),
                "decisions": ",".join(decisions),
            }
        )
    return out


def _global_decision(lane_rows: list[dict[str, object]]) -> str:
    family_rows = [row for row in lane_rows if row.get("scope") == "family"] or lane_rows
    lane_states = {str(row["lane"]): str(row["lane_state"]) for row in family_rows}
    specific_lanes = ["relation_specific", "return_specific", "demotion", "hold_or_demote", "raw_false_one"]
    has_specific_resist = any(lane_states.get(lane, "").startswith("resist") for lane in specific_lanes)
    density_expands = lane_states.get("density_pressure", "").startswith("expand")
    has_any_expand = any(state.startswith("expand") for state in lane_states.values())
    if density_expands and has_specific_resist:
        return "witness_shadow_density_only_specific_discrimination_not_earned"
    if has_specific_resist:
        return "resist_shadow_discrimination_not_earned"
    if has_any_expand:
        return "expand_shadow_discrimination_candidate_not_detector"
    if any("trivial" in state for state in lane_states.values()):
        return "witness_shadow_trivial_after_discrimination_audit"
    return "witness_shadow_discrimination_not_closed"


def _resolve_comparison_input(path: Path) -> Path:
    if path.is_dir():
        candidate = path / "weather_hardening_baseline_comparison.csv"
        if candidate.exists():
            return candidate
    return path


def _write_read(path: Path, *, decision: dict[str, object], residual_rows: list[dict[str, object]], lane_rows: list[dict[str, object]]) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Shadow Discrimination Repair Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This `v1.6.9-alpha` report does not retune the shadow score and does not claim role-blind discovery. It asks what the current frozen shadow score sees after the best available dumb baseline has already explained the easy part of each target.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append(f"Global discrimination decision: `{decision['global_decision']}`")
    lines.append("")
    lines.append("## What changed")
    lines.append("")
    lines.append("- compares shadow against the best available baseline for every target, not only one headline target;")
    lines.append("- computes residual target pressure as `z(target)-z(best_available_baseline_score)`;")
    lines.append("- separates density pressure from relation-specific, return-specific, demotion, hold/demotion, and raw-false-one lanes;")
    lines.append("- treats `shadow sees pressure` as weaker than `shadow sees what dumb baselines did not already explain`.")
    lines.append("")
    lines.append("## Lane summary")
    lines.append("")
    lines.append("| rung | scope | lane | state | targets |")
    lines.append("|---|---|---|---|---|")
    for row in lane_rows:
        lines.append(f"| {row['rung']} | {row['scope']} | {row['lane']} | {row['lane_state']} | {row['targets']} |")
    lines.append("")
    lines.append("## Target residual diagnostics")
    lines.append("")
    lines.append("| rung | scope | target | best baseline | decision | shadow-baseline pairwise | shadow residual spearman |")
    lines.append("|---|---|---|---|---|---:|---:|")
    for row in residual_rows:
        lines.append(
            f"| {row['rung']} | {row['scope']} | {row['target_name']} | {row['best_baseline_model']} | "
            f"{row['target_decision']} | {row['shadow_minus_baseline_pairwise']} | {row['shadow_residual_spearman']} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("If the result says density-only, the frozen score is mostly detecting pressure density, not yet relation/return/demotion-specific false-one structure. That is a valid scientific wound, not a failure of the native witness. The next repair should target discriminating pressure kind before attempting deeper `deep81` / `wide243` trust.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / DISCRIMINATION_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_shadow_discrimination_bundle",
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


def write_shadow_discrimination_report(*, output_dir: Path, hardening_comparison: Path) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    comparison_path = _resolve_comparison_input(Path(hardening_comparison))
    comparison_rows = _read_csv(comparison_path)
    if not comparison_rows:
        raise ValueError(f"Weather hardening comparison is empty: {comparison_path}")
    required = {"rung", "scope", "row_key", "model_name", "model_score", "target_name", "target_value"}
    missing = sorted(required - set(comparison_rows[0].keys()))
    if missing:
        raise ValueError(f"Weather hardening comparison is missing required fields: {', '.join(missing)}")

    target_metrics, residual_metrics = _target_metrics_and_residuals(comparison_rows)
    lane_rows = _lane_summary_rows(residual_metrics)
    global_decision = _global_decision(lane_rows)

    target_metrics_path = output_dir / DISCRIMINATION_FILES["target_metrics"]
    residual_metrics_path = output_dir / DISCRIMINATION_FILES["residual_metrics"]
    lane_path = output_dir / DISCRIMINATION_FILES["lane_summary"]
    decision_path = output_dir / DISCRIMINATION_FILES["decision"]
    audit_path = output_dir / DISCRIMINATION_FILES["audit"]
    read_path = output_dir / DISCRIMINATION_FILES["read"]

    _write_csv(target_metrics_path, target_metrics)
    _write_csv(residual_metrics_path, residual_metrics)
    _write_csv(lane_path, lane_rows)

    decision = {
        "version": "v1.6.9-alpha",
        "report_name": "shadow_discrimination_report",
        "global_decision": global_decision,
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
        "score_freeze_boundary": "report reads existing hardening comparison rows and does not retune the shadow score",
        "role_blind_boundary": "discrimination audit only; no role-blind discovery claim",
        "lane_summary": lane_rows,
    }
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    audit = {
        "input": str(comparison_path),
        "input_kind": "weather_hardening_baseline_comparison.csv",
        "target_fields_observed": sorted({row.get("target_name", "") for row in comparison_rows}),
        "model_names_observed": sorted({row.get("model_name", "") for row in comparison_rows}),
        "residual_target_definition": "z(target)-z(best_available_baseline_score)",
        "score_retuned": False,
        "native_witness_unchanged": "C_Z = min(D, P, R, B)",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    _write_read(read_path, decision=decision, residual_rows=residual_metrics, lane_rows=lane_rows)
    bundle_path = _write_bundle(output_dir)
    return {
        "shadow_discrimination_target_metrics": target_metrics_path,
        "shadow_discrimination_residual_metrics": residual_metrics_path,
        "shadow_discrimination_lane_summary": lane_path,
        "shadow_discrimination_decision": decision_path,
        "shadow_discrimination_audit": audit_path,
        "shadow_discrimination_read": read_path,
        "shadow_discrimination_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit whether frozen shadow scores discriminate anything beyond the best available dumb baseline.")
    parser.add_argument("--hardening-comparison", type=Path, required=True, help="Path to weather_hardening_baseline_comparison.csv or a directory containing it.")
    parser.add_argument("--out", type=Path, default=Path("runs/shadow_discrimination_report_v1_6_9"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_shadow_discrimination_report(output_dir=args.out, hardening_comparison=args.hardening_comparison)
    print("ZeroGateSim shadow discrimination report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
