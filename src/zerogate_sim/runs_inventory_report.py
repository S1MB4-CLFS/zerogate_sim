from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Iterable

RUNS_INVENTORY_FILES = {
    "csv": "runs_inventory.csv",
    "read": "runs_cleanup_plan.md",
    "audit": "runs_inventory_audit.json",
    "bundle": "runs_inventory_bundle.zip",
}

KEEP_PREFIXES = (
    "proof_wide243_",
    "first_research_alpha_",
    "controlled_deep81_",
    "controlled_wide243_",
    "four_gate_reconciliation_",
    "shadow_triad27_harder_",
    "shadow_discrimination_",
    "shadow_lane_discrimination_",
    "shadow_weather_hardening_",
    "seed_block_four_gate_",
    "witness_ablation_",
    "comparison_preset_",
    "cross_logic_",
)

ARCHIVE_PREFIXES = (
    "assistant_test_handoff_",
)

LOCAL_REPORT_PREFIXES = (
    "shadow_score_report_",
    "role_stripped_feature_report_",
    "shadow_triad27_actual_",
    "shadow_triad27_hardened_",
)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _dir_size(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def _contains_zip(path: Path) -> bool:
    return any(file.suffix.lower() == ".zip" for file in path.rglob("*") if file.is_file())


def classify_run_dir(name: str) -> tuple[str, str]:
    if name.startswith(KEEP_PREFIXES):
        return "keep_history", "historical proof/evidence root or current scientific evidence output"
    if name.startswith(ARCHIVE_PREFIXES):
        return "archive_or_delete_after_confirmation", "assistant continuity handoff; local evidence shell, not Git truth"
    if name.startswith(LOCAL_REPORT_PREFIXES):
        return "review_then_archive", "generated local report; keep only if it is the latest relevant evidence or referenced by a handoff"
    return "witness_review_before_action", "unrecognized run folder; do not delete without manual review"


def inventory_runs(*, runs_dir: Path) -> list[dict[str, object]]:
    if not runs_dir.exists():
        raise FileNotFoundError(f"Runs directory does not exist: {runs_dir}")
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in runs_dir.iterdir() if item.is_dir()):
        classification, reason = classify_run_dir(path.name)
        rows.append(
            {
                "name": path.name,
                "classification": classification,
                "reason": reason,
                "size_bytes": _dir_size(path),
                "contains_zip": str(_contains_zip(path)),
                "last_modified": path.stat().st_mtime,
                "safety": "no_delete_default",
            }
        )
    return rows


def _write_read(path: Path, *, runs_dir: Path, rows: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["classification"])] = counts.get(str(row["classification"]), 0) + 1
    lines = [
        "# ZeroGateSim Runs Cleanup Plan",
        "",
        "## Claim boundary",
        "",
        "This report is a local hygiene aid. It does not delete files. It classifies `runs/` folders so Marek can decide what to keep, archive, or remove after evidence is safely represented elsewhere.",
        "",
        "Rules:",
        "",
        "```text",
        "runs/ = local evidence and continuity memory",
        "assistant_test_handoff_* = local assistant handoff, not Git truth",
        "no deletion by default",
        "historical proof roots are protected",
        "```",
        "",
        f"Runs directory: `{runs_dir}`",
        f"Folders seen: `{len(rows)}`",
        "",
        "## Classification counts",
        "",
        "| classification | count |",
        "|---|---:|",
    ]
    for classification, count in sorted(counts.items()):
        lines.append(f"| {classification} | {count} |")
    lines.extend(
        [
            "",
            "## Suggested handling",
            "",
            "| folder | classification | reason |",
            "|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(f"| {row['name']} | {row['classification']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Manual cleanup rule",
            "",
            "Do not delete by vibes. Archive or delete only after checking whether the folder is referenced by a current README, release note, handoff ZIP, Zenodo correction package, or active evidence route.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / RUNS_INVENTORY_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_runs_inventory_bundle",
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


def write_runs_inventory_report(*, output_dir: Path, runs_dir: Path) -> dict[str, Path]:
    output_dir = _ensure_dir(output_dir)
    rows = inventory_runs(runs_dir=Path(runs_dir))
    csv_path = output_dir / RUNS_INVENTORY_FILES["csv"]
    read_path = output_dir / RUNS_INVENTORY_FILES["read"]
    audit_path = output_dir / RUNS_INVENTORY_FILES["audit"]
    _write_csv(csv_path, rows)
    _write_read(read_path, runs_dir=Path(runs_dir), rows=rows)
    audit = {
        "version": "v1.6.10-alpha",
        "report_name": "runs_inventory_report",
        "runs_dir": str(runs_dir),
        "folder_count": len(rows),
        "deletes_files": False,
        "safety": "classification_only_no_delete_default",
        "protected_prefixes": KEEP_PREFIXES,
        "assistant_handoff_boundary": "handoff folders are local evidence shells and must not be staged into Git",
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    bundle_path = _write_bundle(output_dir)
    return {
        "runs_inventory_csv": csv_path,
        "runs_cleanup_plan": read_path,
        "runs_inventory_audit": audit_path,
        "runs_inventory_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify local ZeroGateSim runs/ folders without deleting anything.")
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--out", type=Path, default=Path("runs/runs_inventory_v1_6_10"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_runs_inventory_report(output_dir=args.out, runs_dir=args.runs_dir)
    print("ZeroGateSim runs inventory report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
