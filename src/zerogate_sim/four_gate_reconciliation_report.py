from __future__ import annotations

import argparse
import csv
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from zerogate_sim import __version__
from zerogate_sim.comparison_preset import FOUR_GATE_ADVERSARY_PRESETS, NATIVE_GATE_NAMES, missing_native_gates, preset_gate_coverage
from zerogate_sim.proof import ADVERSARIAL_CORPORA
from zerogate_sim.reporting import ensure_dir
from zerogate_sim.signals import CANDIDATE_PROFILES, candidate_specs

REPORT_FILES = {
    "native_gates": "four_gate_native_witness.csv",
    "historical_corpora": "first_alpha_historical_corpora.csv",
    "followup_coverage": "four_gate_followup_coverage.csv",
    "language_audit": "four_gate_claim_language_audit.csv",
    "read": "four_gate_reconciliation_read.md",
    "zenodo_note": "zenodo_version_correction_note.md",
    "audit": "four_gate_reconciliation_audit.json",
    "bundle": "four_gate_reconciliation_bundle.zip",
}

NATIVE_GATE_ROWS: tuple[dict[str, str], ...] = (
    {
        "gate": "distinction",
        "symbol": "D",
        "native_role": "signal separates from background",
        "historical_status": "dedicated first-alpha adversarial corpus",
        "correction_status": "unchanged",
    },
    {
        "gate": "polarity",
        "symbol": "P",
        "native_role": "signal expresses positive/negative structure around zero",
        "historical_status": "dedicated first-alpha adversarial corpus",
        "correction_status": "unchanged",
    },
    {
        "gate": "relation",
        "symbol": "R",
        "native_role": "candidate binds into relation instead of isolated split",
        "historical_status": "dedicated first-alpha adversarial corpus",
        "correction_status": "unchanged",
    },
    {
        "gate": "return",
        "symbol": "B",
        "native_role": "candidate folds back toward zero with memory, continuity, and persistence",
        "historical_status": "measured native gate / final witness requirement, not dedicated first-alpha corpus",
        "correction_status": "reconciled: dedicated return-adversary coverage is later v1.4.4+ / v1.5 controlled evidence",
    },
)

FORBIDDEN_CLAIM_PHRASES: tuple[str, ...] = (
    "three-gate proof",
    "three gate proof",
    "four-gate first-alpha proof",
    "four gate first-alpha proof",
    "first-alpha four-gate proof",
    "all four gates were independently adversarialized",
    "all four gates were independently adversarialised",
)

SAFE_PUBLIC_CORRECTION_SENTENCE = (
    "The historical first-alpha proof is a three-corpus pre-return adversarial proof "
    "with return measured as a native gate and final witness requirement; later controlled "
    "evidence adds dedicated return-adversary coverage."
)


@dataclass(frozen=True)
class ReconciliationAudit:
    version: str
    native_gate_count: int
    native_gate_names: list[str]
    native_witness_formula: str
    historical_first_alpha_corpus_count: int
    historical_first_alpha_corpora: list[str]
    return_adversary_profile_present: bool
    return_adversary_candidate_count: int
    four_gate_presets_cover_native_gates: bool
    claim_language_forbidden_hits: int
    corrected_public_sentence: str
    boundary: str


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


def native_gate_rows() -> list[dict[str, str]]:
    return [dict(row) for row in NATIVE_GATE_ROWS]


def historical_corpus_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for axis, candidate_profile, description in ADVERSARIAL_CORPORA:
        rows.append(
            {
                "historical_corpus": axis,
                "candidate_profile": candidate_profile,
                "description": description,
                "first_alpha_role": "dedicated adversarial corpus",
                "counts_as_native_gate": axis in NATIVE_GATE_NAMES,
                "counts_as_dedicated_return_corpus": axis == "return",
            }
        )
    rows.append(
        {
            "historical_corpus": "return",
            "candidate_profile": "adversary_return",
            "description": "observed return is present in C_Z and final witness, but was not an independent first-alpha adversarial corpus",
            "first_alpha_role": "native measured gate only in historical first-alpha",
            "counts_as_native_gate": True,
            "counts_as_dedicated_return_corpus": False,
        }
    )
    return rows


def followup_coverage_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for preset in FOUR_GATE_ADVERSARY_PRESETS:
        coverage = preset_gate_coverage(preset)
        missing = missing_native_gates(preset)
        rows.append(
            {
                "coverage_source": preset,
                "coverage_type": "preset",
                "covered_gates": ",".join(coverage),
                "missing_native_gates": ",".join(missing),
                "complete_four_gate_coverage": not missing,
            }
        )
    rows.append(
        {
            "coverage_source": "adversary_return",
            "coverage_type": "candidate_profile",
            "covered_gates": "return",
            "missing_native_gates": "" if "adversary_return" in CANDIDATE_PROFILES else "return",
            "complete_four_gate_coverage": "adversary_return" in CANDIDATE_PROFILES,
        }
    )
    return rows


def _default_language_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in ["README.md", "ROADMAP.md"]:
        path = repo_root / rel
        if path.exists():
            paths.append(path)
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        paths.extend(sorted(path for path in docs_dir.rglob("*.md") if path.is_file()))
    return paths


def scan_claim_language(paths: Sequence[Path]) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            index = lowered.find(phrase)
            if index >= 0:
                line_number = text[:index].count("\n") + 1
                hits.append(
                    {
                        "path": str(path),
                        "phrase": phrase,
                        "line": line_number,
                        "status": "forbidden_claim_language",
                    }
                )
    return hits


def _validate_reconciliation(language_hits: list[dict[str, object]]) -> None:
    native_names = tuple(row["gate"] for row in NATIVE_GATE_ROWS)
    if native_names != tuple(NATIVE_GATE_NAMES):
        raise ValueError(f"Native gate mismatch: constants={native_names}, preset={NATIVE_GATE_NAMES}")
    if "return" not in native_names:
        raise ValueError("Native gate set must include return")
    first_alpha_axes = tuple(axis for axis, _, _ in ADVERSARIAL_CORPORA)
    if first_alpha_axes != ("distinction", "polarity", "relation"):
        raise ValueError(f"Historical first-alpha corpus set must remain explicit: {first_alpha_axes}")
    if "adversary_return" not in CANDIDATE_PROFILES:
        raise ValueError("Missing adversary_return candidate profile")
    for preset in FOUR_GATE_ADVERSARY_PRESETS:
        missing = missing_native_gates(preset)
        if missing:
            raise ValueError(f"Four-gate preset {preset!r} missing: {', '.join(missing)}")
    if language_hits:
        details = "; ".join(f"{row['path']}:{row['line']}:{row['phrase']}" for row in language_hits[:9])
        raise ValueError(f"Forbidden first-alpha/four-gate claim language found: {details}")


def _write_read(path: Path, *, audit: ReconciliationAudit) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Four-Gate Reconciliation Read")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a correction and reconciliation report. It does not run a new proof harness, change native math, change the final witness, or claim role-blind discovery.")
    lines.append("")
    lines.append("## What was wrong")
    lines.append("")
    lines.append("The native mechanism has four gates: distinction, polarity, relation, and return.")
    lines.append("")
    lines.append("The historical first-alpha proof record used three dedicated adversarial corpora: distinction, polarity, and relation. Return was still measured inside the native witness as `B` in `C_Z = min(D, P, R, B)`, but it was not independently adversarialized as a fourth first-alpha corpus.")
    lines.append("")
    lines.append("## Correct public sentence")
    lines.append("")
    lines.append(f"> {SAFE_PUBLIC_CORRECTION_SENTENCE}")
    lines.append("")
    lines.append("## What must not be said")
    lines.append("")
    lines.append("Do not say the historical first-alpha proof independently adversarialized all four gates. Do not backdate the later return-adversary profile into the original proof record. Do not call the old record a role-blind discovery result.")
    lines.append("")
    lines.append("## What later work repaired")
    lines.append("")
    lines.append("The repo already has the dedicated `adversary_return` profile and four-gate adversary presets. The v1.5 controlled synthetic-field reports then preserve fresh `deep81` and `wide243` evidence across dedicated distinction, polarity, relation, and return corpora.")
    lines.append("")
    lines.append("## Audit")
    lines.append("")
    lines.append(f"Native gate count: `{audit.native_gate_count}`")
    lines.append(f"Historical first-alpha corpus count: `{audit.historical_first_alpha_corpus_count}`")
    lines.append(f"Historical corpora: `{', '.join(audit.historical_first_alpha_corpora)}`")
    lines.append(f"Return adversary profile present: `{audit.return_adversary_profile_present}`")
    lines.append(f"Return adversary candidate count: `{audit.return_adversary_candidate_count}`")
    lines.append(f"Four-gate presets cover native gates: `{audit.four_gate_presets_cover_native_gates}`")
    lines.append(f"Forbidden claim-language hits: `{audit.claim_language_forbidden_hits}`")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append("Status: `reconciled_no_backdating`")
    lines.append("")
    lines.append("The honest move is additive correction: preserve the old three-corpus proof as historical first-alpha, name its return-corpus limitation, and point future papers/Zenodo versions to the later four-gate controlled evidence.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_zenodo_note(path: Path) -> None:
    lines: list[str] = []
    lines.append("# Zenodo Version Correction Note — ZeroGateSim Four-Gate Reconciliation")
    lines.append("")
    lines.append("Use this as source language for a future corrected Zenodo version or public correction note. Do not silently overwrite historical claims.")
    lines.append("")
    lines.append("## Correction")
    lines.append("")
    lines.append(SAFE_PUBLIC_CORRECTION_SENTENCE)
    lines.append("")
    lines.append("The older first-alpha PDF remains useful as historical proof-floor documentation, but its proof record should be read as three dedicated adversarial corpora plus a measured return gate, not as a four-corpus return-adversary proof.")
    lines.append("")
    lines.append("## Updated evidence lane")
    lines.append("")
    lines.append("Later repository versions add the `adversary_return` candidate profile, four-gate adversary presets, and controlled synthetic-field `deep81` / `wide243` reports with dedicated distinction, polarity, relation, and return coverage.")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("This correction does not claim cosmology, physical dimensional genesis, physical gravity, trinary reality, or role-blind false-one discovery.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bundle(output_dir: Path) -> Path:
    manifest_path = output_dir / "bundle_manifest.json"
    bundle_path = output_dir / REPORT_FILES["bundle"]
    files = sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() != ".zip")
    manifest = {
        "bundle_kind": "zerogate_four_gate_reconciliation_bundle",
        "package_version": __version__,
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


def write_four_gate_reconciliation_report(
    *,
    output_dir: Path,
    repo_root: Path | None = None,
    strict_language: bool = True,
) -> dict[str, Path]:
    output_dir = ensure_dir(Path(output_dir))
    repo_root = Path(repo_root) if repo_root else Path.cwd()
    language_paths = _default_language_paths(repo_root)
    language_hits = scan_claim_language(language_paths)
    if strict_language:
        _validate_reconciliation(language_hits)
    else:
        _validate_reconciliation([])

    return_specs = candidate_specs("adversary_return")
    native_rows = native_gate_rows()
    historical_rows = historical_corpus_rows()
    followup_rows = followup_coverage_rows()

    audit = ReconciliationAudit(
        version="v1.6.4-alpha",
        native_gate_count=len(native_rows),
        native_gate_names=[row["gate"] for row in native_rows],
        native_witness_formula="C_Z = min(D, P, R, B)",
        historical_first_alpha_corpus_count=len(ADVERSARIAL_CORPORA),
        historical_first_alpha_corpora=[axis for axis, _, _ in ADVERSARIAL_CORPORA],
        return_adversary_profile_present="adversary_return" in CANDIDATE_PROFILES,
        return_adversary_candidate_count=len(return_specs),
        four_gate_presets_cover_native_gates=all(not missing_native_gates(preset) for preset in FOUR_GATE_ADVERSARY_PRESETS),
        claim_language_forbidden_hits=len(language_hits),
        corrected_public_sentence=SAFE_PUBLIC_CORRECTION_SENTENCE,
        boundary="reconciles historical first-alpha language; does not mutate native witness or backdate evidence",
    )

    native_path = output_dir / REPORT_FILES["native_gates"]
    historical_path = output_dir / REPORT_FILES["historical_corpora"]
    followup_path = output_dir / REPORT_FILES["followup_coverage"]
    language_path = output_dir / REPORT_FILES["language_audit"]
    read_path = output_dir / REPORT_FILES["read"]
    zenodo_path = output_dir / REPORT_FILES["zenodo_note"]
    audit_path = output_dir / REPORT_FILES["audit"]

    _write_csv(native_path, native_rows)
    _write_csv(historical_path, historical_rows)
    _write_csv(followup_path, followup_rows)
    _write_csv(language_path, language_hits or [{"path": "", "phrase": "", "line": "", "status": "clean"}])
    _write_read(read_path, audit=audit)
    _write_zenodo_note(zenodo_path)
    audit_path.write_text(json.dumps(asdict(audit), indent=2), encoding="utf-8")
    bundle_path = _write_bundle(output_dir)

    return {
        "four_gate_native_witness": native_path,
        "first_alpha_historical_corpora": historical_path,
        "four_gate_followup_coverage": followup_path,
        "four_gate_claim_language_audit": language_path,
        "four_gate_reconciliation_read": read_path,
        "zenodo_version_correction_note": zenodo_path,
        "four_gate_reconciliation_audit": audit_path,
        "four_gate_reconciliation_bundle": bundle_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write the ZeroGateSim v1.6.4 four-gate reconciliation / Zenodo correction source report.")
    parser.add_argument("--out", type=Path, default=Path("runs/four_gate_reconciliation_v1_6_4"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allow-language-hits", action="store_true", help="Record forbidden phrase hits instead of failing. Use only for deliberate audits.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_four_gate_reconciliation_report(
        output_dir=args.out,
        repo_root=args.repo_root,
        strict_language=not args.allow_language_hits,
    )
    print("ZeroGateSim four-gate reconciliation report complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
