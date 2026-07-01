from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from zerogate_sim import __version__
from zerogate_sim.reporting import ensure_dir


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


def _copy_include(path: Path, out_dir: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    include_dir = ensure_dir(out_dir / "included")
    target = include_dir / path.name
    target.write_bytes(path.read_bytes())
    return target.relative_to(out_dir).as_posix()


def build_test_handoff(
    *,
    out_dir: Path,
    version: str | None = None,
    status: str = "passed",
    notes: list[str] | None = None,
    repo_root: Path | None = None,
    includes: list[Path] | None = None,
    zip_name: str = "assistant_test_handoff.zip",
) -> dict[str, Path]:
    """Write an assistant-readable bundle after Marek's local test gates.

    This does not decide whether a version is true. It preserves the local gate
    result, repo state, and optional included files so the next chat/assistant can
    read the result without guessing from screenshots and memory crumbs.
    """

    out_dir = ensure_dir(out_dir)
    repo_root = repo_root or Path.cwd()
    notes = notes or []
    includes = includes or []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    included_files: list[str] = []
    for include in includes:
        copied = _copy_include(include, out_dir)
        if copied is not None:
            included_files.append(copied)

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
    lines.append("## Boundary")
    lines.append("")
    lines.append("This bundle records local gate results for continuation. It is not proof of cosmology, not proof of final theory truth, and not a substitute for the repo tests or release boundary.")
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
    )
    print("ZeroGateSim assistant test handoff complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
