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
    full_output_reports: list[Path] | None = None,
    compressed_summaries: list[Path] | None = None,
    visual_outputs: list[Path] | None = None,
    report_label_notes: list[str] | None = None,
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

    v1.7.6 holdout-output repair: assistant handoffs may classify included
    files as full output reports, compressed summaries, or visual outputs. This
    lets a future reviewer package carry the complete system output and a
    human-readable compressed state in one handoff without treating local run
    artifacts as repo truth.
    """

    out_dir = ensure_dir(out_dir)
    repo_root = repo_root or Path.cwd()
    notes = notes or []
    includes = includes or []
    full_output_reports = full_output_reports or []
    compressed_summaries = compressed_summaries or []
    visual_outputs = visual_outputs or []
    report_label_notes = report_label_notes or []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    role_inputs = {
        "full_output_reports": full_output_reports,
        "compressed_summaries": compressed_summaries,
        "visual_outputs": visual_outputs,
        "generic_includes": includes,
    }
    role_results: dict[str, list[IncludeResult]] = {}
    include_results: list[IncludeResult] = []
    for role, paths in role_inputs.items():
        copied = [_copy_include(include, out_dir, repo_root=repo_root) for include in paths]
        role_results[role] = copied
        include_results.extend(copied)

    if not allow_missing_includes:
        _raise_for_missing_includes(include_results)

    included_files = [item.bundled_path for item in include_results if item.status == "included"]
    missing_includes = [item for item in include_results if item.status != "included"]
    role_files = {
        role: [item.bundled_path for item in results if item.status == "included"]
        for role, results in role_results.items()
    }

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
        "full_output_reports": role_files["full_output_reports"],
        "compressed_summaries": role_files["compressed_summaries"],
        "visual_outputs": role_files["visual_outputs"],
        "generic_includes": role_files["generic_includes"],
        "include_results_by_role": {role: [item.__dict__ for item in results] for role, results in role_results.items()},
        "include_results": [item.__dict__ for item in include_results],
        "missing_includes": [item.__dict__ for item in missing_includes],
        "missing_include_count": len(missing_includes),
        "strict_includes": not allow_missing_includes,
        "report_label_notes": report_label_notes,
        "handoff_output_contract": {
            "full_output_reports": "complete system output / evidence report files needed for deep assistant review",
            "compressed_summaries": "short human-readable summaries or state cards used for fast review",
            "visual_outputs": "figures, SVGs, PNGs, or HTML/cards that support future human-facing output",
            "generic_includes": "other strict evidence includes",
            "local_run_artifacts_are_repo_truth": False,
        },
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
    lines.append("## Output structure")
    lines.append("")
    lines.append("The handoff can carry both the full system output report and a compressed reviewer state. Local run artifacts remain evidence for inspection; they are not repo truth unless deliberately promoted in a later patch.")
    lines.append("")
    for title, key in [
        ("Full output reports", "full_output_reports"),
        ("Compressed summaries", "compressed_summaries"),
        ("Visual outputs", "visual_outputs"),
        ("Generic includes", "generic_includes"),
    ]:
        lines.append(f"### {title}")
        lines.append("")
        items = data[key]
        if items:
            for item in items:
                lines.append(f"- `{item}`")
        else:
            lines.append("- none")
        lines.append("")
    if report_label_notes:
        lines.append("### Report label notes")
        lines.append("")
        for note in report_label_notes:
            lines.append(f"- {note}")
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
    lines.append("Output rule: full reports, compressed summaries, and visuals are labeled separately so a future human-facing display can read the same handoff without flattening the evidence into one blob.")
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
    parser.add_argument("--full-output-report", action="append", type=Path, default=[], help="Strict include for complete system output / evidence report files.")
    parser.add_argument("--compressed-summary", action="append", type=Path, default=[], help="Strict include for compact reviewer summaries or state cards.")
    parser.add_argument("--visual-output", action="append", type=Path, default=[], help="Strict include for visual outputs such as SVG, PNG, HTML, or human-facing cards.")
    parser.add_argument("--report-label-note", action="append", default=[], help="Boundary note for included report labels, e.g. historical internal report-version labels.")
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
        full_output_reports=list(args.full_output_report),
        compressed_summaries=list(args.compressed_summary),
        visual_outputs=list(args.visual_output),
        report_label_notes=list(args.report_label_note),
        zip_name=args.zip_name,
        allow_missing_includes=args.allow_missing_include,
    )
    print("ZeroGateSim assistant test handoff complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
