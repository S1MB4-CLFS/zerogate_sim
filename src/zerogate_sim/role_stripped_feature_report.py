from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Iterable

FORBIDDEN_SHADOW_INPUT_FIELDS = {
    "trap",
    "expresser",
    "latent_probe",
    "truth_role",
    "role_label",
    "candidate_profile",
    "designed_truth_role",
    "answer_key",
}

FEATURE_FILE_NAMES = {
    "profile_features": "role_stripped_profile_features.csv",
    "family_features": "role_stripped_family_features.csv",
    "evaluation_targets": "role_stripped_evaluation_targets.csv",
    "read": "role_stripped_feature_read.md",
    "audit": "role_stripped_forbidden_field_audit.json",
    "bundle": "role_stripped_feature_bundle.zip",
}

OPAQUE_FAMILY_ID_FIELDS = (
    "seed_range",
    "total_runs",
    "final_earned_one_events",
    "raw_expression_pressure",
    "latent_overcrown_pressure",
    "relation_debt_count",
    "mirror_primary_pressure",
    "mirror_secondary_pressure",
)


def _opaque_family_id(label: str, row: dict[str, str]) -> str:
    """Return a deterministic non-sequential family id without role/gate labels.

    The old v1.6.1 surface used `<label>_family_001` style ids. That was
    convenient, but row order could leak gate-family identity. The holdout line
    needs an id that preserves feature/target joins without carrying `gate`,
    `candidate_profile`, `truth_role`, or a simple ordinal shortcut.
    """

    payload = {"source_label": label}
    for key in OPAQUE_FAMILY_ID_FIELDS:
        payload[key] = str(row.get(key, "") or "")
    digest_source = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:12]
    return f"{label}_opaque_{digest}"


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


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.000000"
    return f"{numerator / denominator:.6f}"


def _source_profile(rows: list[dict[str, str]]) -> str:
    values = {str(row.get("profile", "unknown") or "unknown") for row in rows}
    return values.pop() if len(values) == 1 else "mixed"


def parse_labeled_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"Expected LABEL=PATH, got: {value}")
    label, raw_path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Missing label in LABEL=PATH value: {value}")
    return label, Path(raw_path.strip())


def _ablation_by_variant(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("variant", "")): row for row in rows}


def _ablation_rate(variants: dict[str, dict[str, str]], variant: str, key: str, denominator: int) -> str:
    return _rate(_int(variants.get(variant, {}), key), denominator)


def _feature_header_is_role_stripped(fieldnames: Iterable[str]) -> bool:
    exact = set(fieldnames)
    return not any(field in exact for field in FORBIDDEN_SHADOW_INPUT_FIELDS)


def _profile_feature_row(label: str, seed_rows: list[dict[str, str]], ablation_rows: list[dict[str, str]]) -> dict[str, object]:
    total_runs = sum(_int(row, "total_runs") for row in seed_rows)
    raw_expression = sum(_int(row, "raw_expression_pressure") for row in seed_rows)
    final_earned = sum(_int(row, "final_earned_one_events") for row in seed_rows)
    latent = sum(_int(row, "latent_overcrown_pressure") for row in seed_rows)
    relation_debt = sum(_int(row, "relation_debt_count") for row in seed_rows)
    mirror_primary = sum(_int(row, "mirror_primary_pressure") for row in seed_rows)
    mirror_secondary = sum(_int(row, "mirror_secondary_pressure") for row in seed_rows)
    variants = _ablation_by_variant(ablation_rows)
    ablation_total = _int(variants.get("control", {}), "total_matrix_runs") or total_runs
    return {
        "source_label": label,
        "source_profile": _source_profile(seed_rows),
        "family_count": len(seed_rows),
        "total_runs": total_runs,
        "feature_earned_rate": _rate(final_earned, total_runs),
        "feature_raw_pressure_rate": _rate(raw_expression, total_runs),
        "feature_latent_hold_rate": _rate(latent, total_runs),
        "feature_relation_debt_rate": _rate(relation_debt, total_runs),
        "feature_mirror_primary_rate": _rate(mirror_primary, total_runs),
        "feature_mirror_secondary_rate": _rate(mirror_secondary, total_runs),
        "feature_ablation_raw_as_final_crown_risk_rate": _ablation_rate(variants, "raw_as_final", "final_false_one_crowns", ablation_total),
        "feature_ablation_demotion_dependence_rate": _ablation_rate(variants, "no_false_one_demotion", "final_false_one_crowns", ablation_total),
        "feature_ablation_latent_hold_dependence_rate": _ablation_rate(variants, "no_latent_hold", "promoted_latent_pressure", ablation_total),
        "feature_ablation_echo_independence_rate": _ablation_rate(variants, "no_echo_independence", "promoted_relation_debt", ablation_total),
        "boundary": "role_stripped_features_only_no_truth_role_labels",
    }


def _profile_target_row(label: str, seed_rows: list[dict[str, str]]) -> dict[str, object]:
    total_runs = sum(_int(row, "total_runs") for row in seed_rows)
    raw_false = sum(_int(row, "raw_false_one_pressure") for row in seed_rows)
    false_demoted = sum(_int(row, "false_one_demoted_count") for row in seed_rows)
    final_false = sum(_int(row, "final_false_one_crowns") for row in seed_rows)
    latent = sum(_int(row, "latent_overcrown_pressure") for row in seed_rows)
    latent_demoted = sum(_int(row, "latent_overcrown_demoted_count") for row in seed_rows)
    relation_debt = sum(_int(row, "relation_debt_count") for row in seed_rows)
    mirror_breach = sum(_int(row, "mirror_safety_breach_total") for row in seed_rows)
    relation_false = sum(_int(row, "raw_false_one_pressure") for row in seed_rows if str(row.get("gate", "")) == "relation")
    return_false = sum(_int(row, "raw_false_one_pressure") for row in seed_rows if str(row.get("gate", "")) == "return")
    return {
        "source_label": label,
        "source_profile": _source_profile(seed_rows),
        "total_runs": total_runs,
        "target_raw_false_one_rate": _rate(raw_false, total_runs),
        "target_false_one_demotion_rate": _rate(false_demoted, total_runs),
        "target_final_false_crown_rate": _rate(final_false, total_runs),
        "target_relation_false_pressure_share": _rate(relation_false, raw_false),
        "target_false_pressure_density_rate": _rate(raw_false + latent + relation_debt, total_runs),
        "target_hold_or_demote_rate": _rate(false_demoted + latent_demoted, total_runs),
        "target_return_false_pressure_share": _rate(return_false, raw_false),
        "target_native_breach_rate": _rate(final_false + mirror_breach, total_runs),
        "boundary": "evaluation_targets_only_do_not_load_as_shadow_features",
    }


def _family_feature_rows(label: str, seed_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(seed_rows, start=1):
        total_runs = _int(row, "total_runs")
        out.append(
            {
                "source_label": label,
                "source_profile": str(row.get("profile", "unknown") or "unknown"),
                "family_id": _opaque_family_id(label, row),
                "seed_range": str(row.get("seed_range", "unknown") or "unknown"),
                "total_runs": total_runs,
                "feature_earned_rate": _rate(_int(row, "final_earned_one_events"), total_runs),
                "feature_raw_pressure_rate": _rate(_int(row, "raw_expression_pressure"), total_runs),
                "feature_latent_hold_rate": _rate(_int(row, "latent_overcrown_pressure"), total_runs),
                "feature_relation_debt_rate": _rate(_int(row, "relation_debt_count"), total_runs),
                "feature_mirror_primary_rate": _rate(_int(row, "mirror_primary_pressure"), total_runs),
                "feature_mirror_secondary_rate": _rate(_int(row, "mirror_secondary_pressure"), total_runs),
                "boundary": "opaque_family_row_role_stripped",
            }
        )
    return sorted(out, key=lambda item: str(item["family_id"]))


def _family_target_rows(label: str, seed_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(seed_rows, start=1):
        total_runs = _int(row, "total_runs")
        raw_false = _int(row, "raw_false_one_pressure")
        latent = _int(row, "latent_overcrown_pressure")
        relation_debt = _int(row, "relation_debt_count")
        false_demoted = _int(row, "false_one_demoted_count")
        latent_demoted = _int(row, "latent_overcrown_demoted_count")
        final_false = _int(row, "final_false_one_crowns")
        mirror_breach = _int(row, "mirror_safety_breach_total")
        out.append(
            {
                "source_label": label,
                "family_id": _opaque_family_id(label, row),
                "evaluation_family_label": str(row.get("gate", "unknown") or "unknown"),
                "target_raw_false_one_rate": _rate(raw_false, total_runs),
                "target_false_one_demotion_rate": _rate(false_demoted, total_runs),
                "target_final_false_crown_rate": _rate(final_false, total_runs),
                "target_false_pressure_density_rate": _rate(raw_false + latent + relation_debt, total_runs),
                "target_hold_or_demote_rate": _rate(false_demoted + latent_demoted, total_runs),
                "target_native_breach_rate": _rate(final_false + mirror_breach, total_runs),
                "boundary": "evaluation_target_separate_from_role_stripped_features",
            }
        )
    return sorted(out, key=lambda item: str(item["family_id"]))


def _write_read(path: Path, *, profile_features: list[dict[str, object]], family_features: list[dict[str, object]], target_rows: list[dict[str, object]]) -> None:
    total_runs = sum(_int(row, "total_runs") for row in profile_features)
    source_labels = ", ".join(str(row["source_label"]) for row in profile_features)
    lines: list[str] = []
    lines.append("# ZeroGateSim Role-Stripped Feature Extraction Report")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This report starts the `v1.6.1-alpha` role-stripped evidence line. It extracts observable feature tables from completed controlled synthetic-field reports without writing designed truth-role labels into the feature files.")
    lines.append("")
    lines.append("It is not a role-blind detector yet. It does not crown, demote, or replace the current role-aware witness. It prepares clean feature/target separation for later falsifier tests.")
    lines.append("")
    lines.append("The native witness remains:")
    lines.append("")
    lines.append("```text")
    lines.append("C_Z = min(D, P, R, B)")
    lines.append("```")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"Sources read: `{source_labels}`")
    lines.append(f"Total profile runs represented: `{total_runs}`")
    lines.append(f"Role-stripped family rows: `{len(family_features)}`")
    lines.append(f"Evaluation target rows: `{len(target_rows)}`")
    lines.append("")
    lines.append("## Role-stripped feature files")
    lines.append("")
    lines.append("- `role_stripped_profile_features.csv` — source-level observable features.")
    lines.append("- `role_stripped_family_features.csv` — opaque family-level observable features.")
    lines.append("- Family IDs are hashed from observable non-role fields so row order does not become a gate-label shortcut.")
    lines.append("")
    lines.append("These feature files must not include `candidate_profile`, `truth_role`, `role_label`, `trap`, `expresser`, `latent_probe`, `designed_truth_role`, or `answer_key` fields.")
    lines.append("")
    lines.append("## Evaluation targets")
    lines.append("")
    lines.append("`role_stripped_evaluation_targets.csv` keeps role-aware target values separate. A future shadow scorer may be evaluated against this file only after producing scores from the role-stripped feature files. v1.6.7 expands this target surface beyond raw false-one rate so triad27, deep81, and wide243 can be judged by harder target variety rather than a single easy answer window.")
    lines.append("")
    lines.append("## Profile summary")
    lines.append("")
    lines.append("| source | profile | runs | raw pressure rate | latent hold rate | ablation crown risk | demotion dependence |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for row in profile_features:
        lines.append(
            f"| {row['source_label']} | {row['source_profile']} | {row['total_runs']} | "
            f"{row['feature_raw_pressure_rate']} | {row['feature_latent_hold_rate']} | "
            f"{row['feature_ablation_raw_as_final_crown_risk_rate']} | {row['feature_ablation_demotion_dependence_rate']} |"
        )
    lines.append("")
    lines.append("## Next step")
    lines.append("")
    lines.append("`v1.6.2-alpha` may add a transparent shadow score prototype, but only as a report-side score. It must be evaluated against trivial baselines before any role-blind discovery language is earned.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / FEATURE_FILE_NAMES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_role_stripped_feature_report_bundle",
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


def write_role_stripped_feature_report(
    *,
    output_dir: Path,
    seed_summaries: dict[str, Path],
    ablation_summaries: dict[str, Path] | None = None,
) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    if not seed_summaries:
        raise ValueError("At least one seed-block summary is required.")
    ablation_summaries = ablation_summaries or {}

    profile_features: list[dict[str, object]] = []
    profile_targets: list[dict[str, object]] = []
    family_features: list[dict[str, object]] = []
    family_targets: list[dict[str, object]] = []

    for label, seed_path in seed_summaries.items():
        seed_rows = _read_csv(Path(seed_path))
        if not seed_rows:
            raise ValueError(f"Seed summary is empty: {seed_path}")
        ablation_rows: list[dict[str, str]] = []
        if label in ablation_summaries:
            ablation_rows = _read_csv(Path(ablation_summaries[label]))
        profile_features.append(_profile_feature_row(label, seed_rows, ablation_rows))
        profile_targets.append(_profile_target_row(label, seed_rows))
        family_features.extend(_family_feature_rows(label, seed_rows))
        family_targets.extend(_family_target_rows(label, seed_rows))

    profile_features_path = output_dir / FEATURE_FILE_NAMES["profile_features"]
    family_features_path = output_dir / FEATURE_FILE_NAMES["family_features"]
    targets_path = output_dir / FEATURE_FILE_NAMES["evaluation_targets"]
    read_path = output_dir / FEATURE_FILE_NAMES["read"]
    audit_path = output_dir / FEATURE_FILE_NAMES["audit"]

    _write_csv(profile_features_path, profile_features)
    _write_csv(family_features_path, family_features)
    _write_csv(targets_path, profile_targets + family_targets)
    _write_read(read_path, profile_features=profile_features, family_features=family_features, target_rows=profile_targets + family_targets)

    audit = {
        "feature_files_role_stripped": _feature_header_is_role_stripped(profile_features[0].keys()) and _feature_header_is_role_stripped(family_features[0].keys()),
        "forbidden_shadow_input_fields": sorted(FORBIDDEN_SHADOW_INPUT_FIELDS),
        "feature_files": [FEATURE_FILE_NAMES["profile_features"], FEATURE_FILE_NAMES["family_features"]],
        "target_file": FEATURE_FILE_NAMES["evaluation_targets"],
        "family_ids_are_opaque_nonsequential": True,
        "family_id_boundary": "family ids are deterministic hashes over observable non-role fields; they do not use gate, candidate_profile, truth_role, or ordinal row numbers",
        "target_file_boundary": "targets are separate and must not be loaded as shadow features",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle_path = _write_bundle(output_dir)
    return {
        "role_stripped_profile_features": profile_features_path,
        "role_stripped_family_features": family_features_path,
        "role_stripped_evaluation_targets": targets_path,
        "role_stripped_feature_read": read_path,
        "role_stripped_forbidden_field_audit": audit_path,
        "role_stripped_feature_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract role-stripped observable feature tables from completed ZeroGateSim evidence reports.")
    parser.add_argument("--seed-summary", action="append", default=[], help="LABEL=path/to/seed_block_four_gate_summary.csv. May be supplied multiple times.")
    parser.add_argument("--ablation-summary", action="append", default=[], help="LABEL=path/to/witness_ablation_summary.csv. May be supplied multiple times.")
    parser.add_argument("--out", type=Path, default=Path("runs/role_stripped_feature_report"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    seed_summaries = dict(parse_labeled_path(value) for value in args.seed_summary)
    ablation_summaries = dict(parse_labeled_path(value) for value in args.ablation_summary)
    paths = write_role_stripped_feature_report(output_dir=args.out, seed_summaries=seed_summaries, ablation_summaries=ablation_summaries)
    print("ZeroGateSim role-stripped feature report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
