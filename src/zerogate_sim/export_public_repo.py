"""Create a clean public-source export for ZeroGateSim.

This tool copies source-control-safe files into a ZIP while excluding local
weather: runs, virtual environments, caches, build outputs, and heavy bundles.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

DEFAULT_OUT = Path("exports/zerogate_sim_public_repo_v1_0_1_alpha.zip")
ROOT_NAME = "zerogate_sim"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "ENV",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "runs",
    "exports",
    "scratch",
    "tmp",
    ".vscode",
    ".idea",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
}

EXCLUDE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "READMAP.md",
}

EXCLUDE_CONTAINS = (
    ".egg-info",
)

@dataclass(frozen=True)
class ExportFile:
    source: Path
    relative: Path
    size: int


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def should_exclude(path: Path, repo: Path, out_path: Path | None = None) -> tuple[bool, str]:
    rel = path.relative_to(repo)
    parts = set(rel.parts)
    name = path.name

    if out_path is not None and path.resolve() == out_path.resolve():
        return True, "output_zip"
    if any(part in EXCLUDE_DIRS for part in parts):
        return True, "excluded_dir"
    if name in EXCLUDE_NAMES:
        return True, "excluded_name"
    if any(str(rel).replace("\\", "/").endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
        return True, "excluded_suffix"
    if any(token in str(rel) for token in EXCLUDE_CONTAINS):
        return True, "excluded_token"
    return False, "included"


def collect_files(repo: Path, out_path: Path) -> tuple[list[ExportFile], list[dict[str, str]]]:
    files: list[ExportFile] = []
    skipped: list[dict[str, str]] = []
    for path in sorted(repo.rglob("*")):
        if path.is_dir():
            continue
        excluded, reason = should_exclude(path, repo, out_path)
        rel = path.relative_to(repo)
        if excluded:
            skipped.append({"path": str(rel).replace("\\", "/"), "reason": reason})
            continue
        files.append(ExportFile(source=path, relative=rel, size=path.stat().st_size))
    return files, skipped


def write_export(
    repo: Path,
    out_path: Path,
    *,
    dry_run: bool = False,
    max_file_mb: float = 100.0,
    max_total_mb: float = 200.0,
    allow_large: bool = False,
) -> dict[str, object]:
    repo = repo.resolve()
    out_path = out_path.resolve()
    files, skipped = collect_files(repo, out_path)
    total_size = sum(item.size for item in files)
    largest = sorted(files, key=lambda item: item.size, reverse=True)[:9]

    max_file = max((item.size for item in files), default=0)
    max_file_limit = int(max_file_mb * 1024 * 1024)
    max_total_limit = int(max_total_mb * 1024 * 1024)

    if not allow_large:
        if max_file > max_file_limit:
            offenders = [f"{item.relative} ({item.size} bytes)" for item in largest if item.size > max_file_limit]
            raise SystemExit("Export refused: file larger than limit. " + "; ".join(offenders))
        if total_size > max_total_limit:
            raise SystemExit(
                f"Export refused: total included source size {total_size} bytes exceeds limit {max_total_limit} bytes. "
                "Use --allow-large only if you intentionally reviewed the export."
            )

    manifest = {
        "repo": str(repo),
        "out": str(out_path),
        "root_name": ROOT_NAME,
        "dry_run": dry_run,
        "included_file_count": len(files),
        "included_total_bytes": total_size,
        "skipped_file_count": len(skipped),
        "largest_included_files": [
            {"path": str(item.relative).replace("\\", "/"), "bytes": item.size}
            for item in largest
        ],
        "skipped_sample": skipped[:54],
        "boundary": "Generated runs, virtual environments, caches, build outputs, and ZIP evidence bundles are excluded.",
    }

    if dry_run:
        return manifest

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as zf:
        for item in files:
            arcname = Path(ROOT_NAME) / item.relative
            zf.write(item.source, arcname.as_posix())
        zf.writestr(f"{ROOT_NAME}/PUBLIC_EXPORT_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")

    manifest["zip_bytes"] = out_path.stat().st_size
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a clean ZeroGateSim public-repo export ZIP.")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Repo root, default current directory.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output ZIP path.")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without writing ZIP.")
    parser.add_argument("--allow-large", action="store_true", help="Allow export above safety size limits after manual review.")
    parser.add_argument("--max-file-mb", type=float, default=100.0, help="Safety limit per included file.")
    parser.add_argument("--max-total-mb", type=float, default=200.0, help="Safety limit for included source total.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = write_export(
        repo=args.repo,
        out_path=args.out,
        dry_run=args.dry_run,
        max_file_mb=args.max_file_mb,
        max_total_mb=args.max_total_mb,
        allow_large=args.allow_large,
    )
    print(json.dumps(manifest, indent=2))
    if not args.dry_run:
        print(f"\nPublic export written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
