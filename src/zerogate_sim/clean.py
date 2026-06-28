from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CleanupTarget:
    path: Path
    reason: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean generated ZeroGateSim repo artifacts without PowerShell script execution."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repo root to clean. Defaults to current directory.",
    )
    parser.add_argument(
        "--remove-runs",
        action="store_true",
        help="Also remove the generated runs/ evidence folder.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List cleanup targets without removing them.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm cleanup. Required unless --dry-run is used.",
    )
    return parser


def validate_repo_root(repo: Path) -> Path:
    repo = repo.expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"Repo folder not found: {repo}")
    if not (repo / "pyproject.toml").exists() or not (repo / "src" / "zerogate_sim").exists():
        raise SystemExit(f"Refusing cleanup: this does not look like the ZeroGateSim repo root: {repo}")
    return repo


def _iter_named_dirs(repo: Path, names: set[str]) -> Iterable[CleanupTarget]:
    for path in repo.rglob("*"):
        if not path.is_dir():
            continue
        if path.name in names:
            yield CleanupTarget(path, f"cache/build directory: {path.name}")


def _iter_egg_info(repo: Path) -> Iterable[CleanupTarget]:
    for path in repo.rglob("*.egg-info"):
        if path.is_dir():
            yield CleanupTarget(path, "editable/build metadata")


def _iter_python_bytecode(repo: Path) -> Iterable[CleanupTarget]:
    for pattern in ("*.pyc", "*.pyo"):
        for path in repo.rglob(pattern):
            if path.is_file():
                yield CleanupTarget(path, "python bytecode")
    coverage = repo / ".coverage"
    if coverage.exists() and coverage.is_file():
        yield CleanupTarget(coverage, "coverage file")


def collect_targets(repo: Path, *, remove_runs: bool = False) -> list[CleanupTarget]:
    repo = validate_repo_root(repo)
    targets: list[CleanupTarget] = []
    targets.extend(
        _iter_named_dirs(
            repo,
            {
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "build",
                "dist",
            },
        )
    )
    targets.extend(_iter_egg_info(repo))
    targets.extend(_iter_python_bytecode(repo))

    if remove_runs:
        runs = repo / "runs"
        if runs.exists():
            targets.append(CleanupTarget(runs, "generated run evidence"))

    # Avoid double-removal when a child lies inside a directory already targeted.
    unique: dict[Path, CleanupTarget] = {}
    for target in targets:
        resolved = target.path.resolve()
        if resolved == repo:
            continue
        unique[resolved] = CleanupTarget(resolved, target.reason)

    sorted_targets = sorted(unique.values(), key=lambda item: (len(item.path.parts), str(item.path).lower()))
    pruned: list[CleanupTarget] = []
    removed_parents: list[Path] = []
    for target in sorted_targets:
        if any(parent in target.path.parents for parent in removed_parents):
            continue
        pruned.append(target)
        if target.path.is_dir():
            removed_parents.append(target.path)
    return pruned


def remove_targets(targets: list[CleanupTarget]) -> None:
    for target in targets:
        if target.path.is_dir():
            shutil.rmtree(target.path, ignore_errors=True)
        elif target.path.exists():
            try:
                target.path.unlink()
            except FileNotFoundError:
                pass


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = validate_repo_root(args.repo)
    targets = collect_targets(repo, remove_runs=args.remove_runs)

    if not targets:
        print("Nothing to clean. Source tree already looks tidy.")
        return 0

    print("ZeroGateSim cleanup targets:")
    for target in targets:
        print(f"- {target.path} [{target.reason}]")

    if args.dry_run:
        print("\nDry run only. Nothing removed.")
        return 0

    if not args.yes:
        print("\nNo files removed. Re-run with --yes, or use --dry-run to inspect only.")
        return 2

    remove_targets(targets)
    print("\nCleanup complete.")
    if args.remove_runs:
        print("Runs removed. Recreate evidence with zerogate-demo or zerogate-batch.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
