from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from zerogate_sim import __version__
from zerogate_sim.reporting import ensure_dir


@dataclass(frozen=True)
class IncludeResult:
    source: str
    status: str
    bundled_path: str
    reason: str
    source_relative_path: str = ""


def _run_git(args: Sequence[str], *, cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return f"git unavailable: {exc}"
    return result.stdout.strip()


def _safe_bundle_parts(path: Path, *, repo_root: Path) -> tuple[str, ...]:
    """Return safe source-relative path parts for an included handoff file.

    v1.4.3 truth repair: include files must not be flattened to only their
    basename. Matrix outputs often share names such as
    ``matrix_known_logic_closeout_read.md``; flattening those paths overwrites
    evidence from distinction / polarity / relation runs. The bundle path must
    preserve enough source-relative structure to keep every requested witness
    separate.
    """

    try:
        root = repo_root.resolve()
    except OSError:
        root = repo_root.absolute()

    source_path = path
    if path.is_absolute():
        try:
            source_path = path.resolve().relative_to(root)
        except (OSError, ValueError):
            # External absolute file: include it under an explicit external
            # namespace instead of flattening it or leaking an unsafe drive/root.
            source_path = Path("__external__", *path.parts[1:]) if len(path.parts) > 1 else Path("__external__", path.name)

    parts: list[str] = []
    for part in source_path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            parts.append("__parent__")
            continue
        cleaned = part.replace(":", "").replace("\\", "_").replace("/", "_").strip()
        if cleaned:
            parts.append(cleaned)

    if not parts:
        parts = [path.name or "include"]
    return tuple(parts)


def _unique_target(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}__{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _copy_include(path: Path, out_dir: Path, *, repo_root: Path) -> IncludeResult:
    source = str(path)
    if not path.exists():
        return IncludeResult(source=source, status="missing", bundled_path="", reason="path does not exist")
    if not path.is_file():
        return IncludeResult(source=source, status="not_file", bundled_path="", reason="path exists but is not a file")

    include_dir = ensure_dir(out_dir / "included")
    rel_parts = _safe_bundle_parts(path, repo_root=repo_root)
    target = _unique_target(include_dir.joinpath(*rel_parts))
    ensure_dir(target.parent)
    target.write_bytes(path.read_bytes())

    source_relative_path = "/".join(rel_parts)
    bundled_path = target.relative_to(out_dir).as_posix()
    reason = "copied" if target.name == rel_parts[-1] else "copied with collision suffix"
    return IncludeResult(
        source=source,
        status="included",
        bundled_path=bundled_path,
        reason=reason,
        source_relative_path=source_relative_path,
    )


def _raise_for_missing_includes(results: list[IncludeResult]) -> None:
    bad = [item for item in results if item.status != "included"]
    if not bad:
        return
    lines = ["One or more requested handoff include files are missing or invalid:"]
    for item in bad:
        lines.append(f"- {item.source}: {item.status} ({item.reason})")
    raise FileNotFoundError("\n".join(lines))


def build_test_handoff(
    *,
    out_dir: Path,
    version: str | None = None,
    status: str = "passed",
    notes: list[str] | None = None,
    repo_root: Path | None = None,
    includes: list[Path] | None = None,
    zip_name: str = "assistant_test_handoff.zip",
    allow_missing_includes: bool = False,
) -> dict[str, Path]:
    """Write an assistant-readable bundle after Marek's local test gates.

    This does not decide whether a version is true. It preserves the local gate
    result, repo state, and included result files so the next chat/assistant can
    read the result without guessing from screenshots and memory crumbs.

    v1.4.2 truth repair: requested includes are strict by default. A handoff that
    says tests passed but silently omits a missing report file is a false witness.

    v1.4.3 truth repair: included files preserve source-relative paths under the
    bundle's ``included/`` directory so reports with the same basename from
    different run folders cannot overwrite each other.
    """

    out_dir = ensure_dir(out_dir)
    repo_root = repo_root or Path.cwd()
    notes = notes or []
    includes = includes or []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    include_results = [_copy_include(include, out_dir, repo_root=repo_root) for include in includes]
    if not allow_missing_includes:
        _raise_for_missing_includes(include_results)

    included_files = [item.bundled_path for item in include_results if item.status == "included"]
    missing_includes = [item for item in include_results if item.status != "included"]

    data = {
        "bundle_kind": "zerogate_assistant_test_handoff",
        "created_utc": now,
        "requested_version": version or __version__,
        "package_version": __version__,
        "status": status,
        "notes": notes,
        "repo_root": str(repo_root),
        "git_status_short": _run_git(["status", "--short"], cwd=repo_root),
        "git_log_oneline_decorate": _run_git(["--no-pager", "log", "--oneline", "--decorate", "-8"], cwd=repo_root),
        "git_tags_v": _run_git(["tag", "--list", "v*", "--sort=-creatordate"], cwd=repo_root),
        "included_files": included_files,
        "include_results": [item.__dict__ for item in include_results],
        "missing_includes": [item.__dict__ for item in missing_includes],
        "missing_include_count": len(missing_includes),
        "strict_includes": not allow_missing_includes,
    }

    json_path = out_dir / "assistant_test_handoff.json"
    md_path = out_dir / "assistant_test_handoff.md"
    zip_path = out_dir / zip_name

    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# ZeroGateSim Assistant Test Handoff")
    lines.append("")
    lines.append(f"Created UTC: `{now}`")
    lines.append(f"Requested version: `{data['requested_version']}`")
    lines.append(f"Package version: `{data['package_version']}`")
    lines.append(f"Status: `{status}`")
    lines.append(f"Strict includes: `{data['strict_includes']}`")
    lines.append(f"Missing include count: `{len(missing_includes)}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No notes supplied.")
    lines.append("")
    lines.append("## Git status")
    lines.append("")
    lines.append("```text")
    lines.append(data["git_status_short"] or "clean")
    lines.append("```")
    lines.append("")
    lines.append("## Recent log")
    lines.append("")
    lines.append("```text")
    lines.append(data["git_log_oneline_decorate"] or "unavailable")
    lines.append("```")
    lines.append("")
    lines.append("## Included files")
    lines.append("")
    if included_files:
        for item in included_files:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Include audit")
    lines.append("")
    if include_results:
        lines.append("| source | status | bundled path | source-relative path | reason |")
        lines.append("|---|---|---|---|---|")
        for item in include_results:
            bundled = item.bundled_path or ""
            source_rel = item.source_relative_path or ""
            lines.append(f"| `{item.source}` | `{item.status}` | `{bundled}` | `{source_rel}` | {item.reason} |")
    else:
        lines.append("- No include paths requested.")
    lines.append("")
    if missing_includes:
        lines.append("## Missing includes")
        lines.append("")
        for item in missing_includes:
            lines.append(f"- `{item.source}` — {item.status}: {item.reason}")
        lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("This bundle records local gate results for continuation. It is not proof of cosmology, not proof of final theory truth, and not a substitute for the repo tests or release boundary.")
    lines.append("")
    lines.append("Truth rule: a requested include that is missing is a failed handoff unless explicitly allowed with `--allow-missing-include`. Requested includes preserve source-relative paths so same-named reports from different runs cannot overwrite each other.")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(md_path, arcname=md_path.name)
        zf.write(json_path, arcname=json_path.name)
        for item in included_files:
            path = out_dir / item
            if path.exists() and path.is_file():
                zf.write(path, arcname=item)
    return {
        "assistant_test_handoff_md": md_path,
        "assistant_test_handoff_json": json_path,
        "assistant_test_handoff_zip": zip_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a ZeroGateSim assistant-readable test handoff bundle.")
    parser.add_argument("--out", type=Path, default=Path("runs/assistant_test_handoff"))
    parser.add_argument("--version", default=None)
    parser.add_argument("--status", choices=["passed", "failed", "hold", "partial"], default="passed")
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--include", action="append", type=Path, default=[])
    parser.add_argument("--allow-missing-include", action="store_true", help="Record missing include paths instead of failing. Use only when missing files are expected.")
    parser.add_argument("--zip-name", default="assistant_test_handoff.zip")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = build_test_handoff(
        out_dir=args.out,
        version=args.version,
        status=args.status,
        notes=list(args.note),
        includes=list(args.include),
        zip_name=args.zip_name,
        allow_missing_includes=args.allow_missing_include,
    )
    print("ZeroGateSim assistant test handoff complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
