from __future__ import annotations

import argparse
import csv
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from zerogate_sim.reporting import write_evidence_bundle, write_dict_rows_csv


@dataclass(frozen=True)
class ProofTotals:
    profile: str
    seed_range: str
    corpus_count: int
    scenario_cells: int
    seeded_runs: int
    final_earned_one_events: int
    raw_expression_pressure: int
    raw_false_one_pressure: int
    false_one_demoted_count: int
    final_false_one_crowns: int
    latent_overcrown_pressure: int
    latent_overcrown_demoted_count: int
    expresser_candidate_count: int
    earned_expresser_candidate_count: int
    trap_candidate_count: int
    trap_final_crown_count: int
    corpora_passed: int
    corpora_hold: int
    corpora_failed: int
    proof_status: str
    proof_claim: str
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "seed_range": self.seed_range,
            "corpus_count": self.corpus_count,
            "scenario_cells": self.scenario_cells,
            "seeded_runs": self.seeded_runs,
            "final_earned_one_events": self.final_earned_one_events,
            "raw_expression_pressure": self.raw_expression_pressure,
            "raw_false_one_pressure": self.raw_false_one_pressure,
            "false_one_demoted_count": self.false_one_demoted_count,
            "final_false_one_crowns": self.final_false_one_crowns,
            "latent_overcrown_pressure": self.latent_overcrown_pressure,
            "latent_overcrown_demoted_count": self.latent_overcrown_demoted_count,
            "expresser_candidate_count": self.expresser_candidate_count,
            "earned_expresser_candidate_count": self.earned_expresser_candidate_count,
            "trap_candidate_count": self.trap_candidate_count,
            "trap_final_crown_count": self.trap_final_crown_count,
            "corpora_passed": self.corpora_passed,
            "corpora_hold": self.corpora_hold,
            "corpora_failed": self.corpora_failed,
            "proof_status": self.proof_status,
            "proof_claim": self.proof_claim,
            "next_action": self.next_action,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze a ZeroGateSim trinary proof harness into an official proof-record candidate."
    )
    parser.add_argument(
        "--proof-dir",
        type=Path,
        required=True,
        help="Directory containing proof_harness_summary.csv and the three corpus folders.",
    )
    parser.add_argument(
        "--no-bundle",
        action="store_true",
        help="Do not rebuild proof_bundle.zip after writing proof record files.",
    )
    return parser


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if value in {"", None}:
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def _extract_profile_and_seed_range(read_path: Path) -> tuple[str, str]:
    if not read_path.exists():
        return "unknown", "unknown"
    text = read_path.read_text(encoding="utf-8")
    profile = "unknown"
    seed_range = "unknown"
    for line in text.splitlines():
        if line.startswith("Profile:"):
            profile = line.split("`", 2)[1] if "`" in line else line.split(":", 1)[1].strip()
        if line.startswith("Seed range:"):
            parts = line.split("`")
            if len(parts) >= 4:
                seed_range = f"{parts[1]}-{parts[3]}"
            else:
                seed_range = line.split(":", 1)[1].strip()
    return profile, seed_range


def _status_for(rows: list[dict[str, str]], totals: dict[str, int]) -> tuple[str, str, str]:
    final_false = totals["final_false_one_crowns"]
    false_pressure = totals["raw_false_one_pressure"]
    false_demoted = totals["false_one_demoted_count"]
    final_earned = totals["final_earned_one_events"]
    passed = sum(1 for row in rows if row.get("status") == "pass")
    failed = sum(1 for row in rows if row.get("status") == "fail")

    if final_false > 0 or failed > 0:
        return (
            "hold_breach",
            "Final false-one crown or failed corpus appeared; do not freeze first-research-alpha.",
            "repair the breach before reproduction",
        )
    if passed == len(rows) and final_earned > 0 and false_pressure > 0 and false_demoted == false_pressure:
        return (
            "proof_record_candidate",
            "Final +1 belongs only to earned-one; false-one pressure was named and fully demoted across the trinary adversarial harness.",
            "rerun the same harness on fresh seeds 9-17 without code mutation",
        )
    if passed == len(rows) and final_earned > 0:
        return (
            "supported_no_false_pressure",
            "Final +1 survived, but this record did not expose enough false-one pressure to count as adversarial confirmation.",
            "add or rerun adversarial pressure before freeze",
        )
    return (
        "hold_insufficient_expression",
        "No false crown appeared, but earned expression was too weak for proof-record posture.",
        "inspect candidate truth roles and expression weather",
    )


def _top_false_one_candidates(proof_dir: Path) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for corpus_dir in sorted(p for p in proof_dir.iterdir() if p.is_dir()):
        path = corpus_dir / "matrix_final_output_summary.csv"
        if not path.exists():
            continue
        for row in _read_csv(path):
            false_count = _int(row, "false_one_demoted_count")
            if false_count > 0:
                out.append(
                    {
                        "axis": corpus_dir.name,
                        "candidate_id": row.get("candidate_id", ""),
                        "kind": row.get("kind", ""),
                        "false_one_demoted_count": false_count,
                        "raw_expression_pressure": _int(row, "raw_expression_pressure"),
                        "echo_independence_band": row.get("echo_independence_band", ""),
                    }
                )
    return sorted(out, key=lambda row: (-int(row["false_one_demoted_count"]), str(row["axis"]), str(row["candidate_id"])))


def _conditional_expressers(proof_dir: Path) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for corpus_dir in sorted(p for p in proof_dir.iterdir() if p.is_dir()):
        path = corpus_dir / "matrix_final_output_summary.csv"
        if not path.exists():
            continue
        for row in _read_csv(path):
            if row.get("truth_role") == "expresser" and _int(row, "final_earned_one_count") == 0:
                out.append(
                    {
                        "axis": corpus_dir.name,
                        "candidate_id": row.get("candidate_id", ""),
                        "kind": row.get("kind", ""),
                        "final_band": row.get("final_band", ""),
                        "raw_expression_pressure": _int(row, "raw_expression_pressure"),
                    }
                )
    return out


def summarize_proof_dir(proof_dir: Path) -> tuple[ProofTotals, list[dict[str, str]], list[dict[str, object]], list[dict[str, object]]]:
    proof_dir = Path(proof_dir)
    summary_path = proof_dir / "proof_harness_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing proof harness summary: {summary_path}")
    rows = _read_csv(summary_path)
    if not rows:
        raise ValueError("proof_harness_summary.csv has no rows")

    profile, seed_range = _extract_profile_and_seed_range(proof_dir / "proof_harness_read.md")
    totals = {
        "scenario_cells": sum(_int(row, "scenario_count") for row in rows),
        "seeded_runs": sum(_int(row, "seeded_run_count") for row in rows),
        "final_earned_one_events": sum(_int(row, "final_earned_one_events") for row in rows),
        "raw_expression_pressure": sum(_int(row, "raw_expression_pressure") for row in rows),
        "raw_false_one_pressure": sum(_int(row, "raw_false_one_pressure") for row in rows),
        "false_one_demoted_count": sum(_int(row, "false_one_demoted_count") for row in rows),
        "final_false_one_crowns": sum(_int(row, "final_false_one_crowns") for row in rows),
        "latent_overcrown_pressure": sum(_int(row, "latent_overcrown_pressure") for row in rows),
        "latent_overcrown_demoted_count": sum(_int(row, "latent_overcrown_demoted_count") for row in rows),
        "expresser_candidate_count": sum(_int(row, "expresser_candidate_count") for row in rows),
        "earned_expresser_candidate_count": sum(_int(row, "earned_expresser_candidate_count") for row in rows),
        "trap_candidate_count": sum(_int(row, "trap_candidate_count") for row in rows),
        "trap_final_crown_count": sum(_int(row, "trap_final_crown_count") for row in rows),
    }
    proof_status, proof_claim, next_action = _status_for(rows, totals)
    corpora_passed = sum(1 for row in rows if row.get("status") == "pass")
    corpora_hold = sum(1 for row in rows if row.get("status") == "hold")
    corpora_failed = sum(1 for row in rows if row.get("status") == "fail")
    totals_obj = ProofTotals(
        profile=profile,
        seed_range=seed_range,
        corpus_count=len(rows),
        scenario_cells=totals["scenario_cells"],
        seeded_runs=totals["seeded_runs"],
        final_earned_one_events=totals["final_earned_one_events"],
        raw_expression_pressure=totals["raw_expression_pressure"],
        raw_false_one_pressure=totals["raw_false_one_pressure"],
        false_one_demoted_count=totals["false_one_demoted_count"],
        final_false_one_crowns=totals["final_false_one_crowns"],
        latent_overcrown_pressure=totals["latent_overcrown_pressure"],
        latent_overcrown_demoted_count=totals["latent_overcrown_demoted_count"],
        expresser_candidate_count=totals["expresser_candidate_count"],
        earned_expresser_candidate_count=totals["earned_expresser_candidate_count"],
        trap_candidate_count=totals["trap_candidate_count"],
        trap_final_crown_count=totals["trap_final_crown_count"],
        corpora_passed=corpora_passed,
        corpora_hold=corpora_hold,
        corpora_failed=corpora_failed,
        proof_status=proof_status,
        proof_claim=proof_claim,
        next_action=next_action,
    )
    return totals_obj, rows, _top_false_one_candidates(proof_dir), _conditional_expressers(proof_dir)


def _write_record(path: Path, totals: ProofTotals, rows: list[dict[str, str]], false_candidates: list[dict[str, object]], conditional: list[dict[str, object]]) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Proof Record Freeze")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"Proof record status: `{totals.proof_status}`")
    lines.append("")
    lines.append(totals.proof_claim)
    lines.append("")
    lines.append("This is a first-research-alpha candidate record inside generated toy fields. It does not prove cosmology, physics, or final trinary mathematics.")
    lines.append("")
    lines.append("## Run shape")
    lines.append("")
    lines.append(f"Profile: `{totals.profile}`")
    lines.append(f"Seed range: `{totals.seed_range}`")
    lines.append(f"Adversarial corpora: `{totals.corpus_count}`")
    lines.append(f"Scenario cells: `{totals.scenario_cells}`")
    lines.append(f"Seeded simulation runs: `{totals.seeded_runs}`")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Final earned-one events: `{totals.final_earned_one_events}`.")
    lines.append("Earned-one is the only final +1 crown. Raw expression remains visible as pressure, not truth.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(f"Latent overcrown pressure held in zero: `{totals.latent_overcrown_demoted_count}` of `{totals.latent_overcrown_pressure}`.")
    lines.append("This means the zero-zone is active: it does not force latent pressure into binary success/failure.")
    if conditional:
        lines.append("")
        lines.append("Conditional expresser pressure remains visible:")
        for row in conditional[:9]:
            lines.append(f"- `{row['axis']}` `{row['candidate_id']}` `{row['kind']}` stayed `{row['final_band']}`.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Raw false-one pressure: `{totals.raw_false_one_pressure}`.")
    lines.append(f"False-one events demoted before final crown: `{totals.false_one_demoted_count}`.")
    lines.append(f"Final false-one crowns: `{totals.final_false_one_crowns}`.")
    if false_candidates:
        lines.append("")
        lines.append("Top demoted false-one candidates:")
        for row in false_candidates[:9]:
            lines.append(
                f"- `{row['axis']}` `{row['candidate_id']}` `{row['kind']}`: "
                f"{row['false_one_demoted_count']} demoted, echo band `{row['echo_independence_band']}`."
            )
    lines.append("")
    lines.append("## Corpus table")
    lines.append("")
    lines.append("| axis | status | cells | runs | earned | raw false | demoted false | final false crowns | earned expressers |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row.get('axis','')} | {row.get('status','')} | {row.get('scenario_count','')} | {row.get('seeded_run_count','')} | "
            f"{row.get('final_earned_one_events','')} | {row.get('raw_false_one_pressure','')} | "
            f"{row.get('false_one_demoted_count','')} | {row.get('final_false_one_crowns','')} | "
            f"{row.get('earned_expresser_candidate_count','')}/{row.get('expresser_candidate_count','')} |"
        )
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("Supported claim: ZeroGateSim's final trinary witness separated earned-one from raw expression, latent overcrown, and false-one pressure across a trinary adversarial toy-field harness.")
    lines.append("")
    lines.append("Not supported: that physical dimensions, cosmology, or reality itself have been proven trinary.")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(totals.next_action + ".")
    lines.append("")
    lines.append("If the same posture repeats on fresh seeds without code mutation, freeze v1.0-alpha as the first research-alpha release candidate. If final-output breaches reappear, hold the core gate and repair the witness or candidate ecology first.")
    lines.append("")
    lines.append("## Final sentence")
    lines.append("")
    lines.append("The machine did not prove the universe. It did something narrower and real: it met false one, named it, and refused the crown.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def freeze_proof_record(proof_dir: Path, *, make_bundle: bool = True) -> dict[str, Path]:
    proof_dir = Path(proof_dir)
    totals, rows, false_candidates, conditional = summarize_proof_dir(proof_dir)
    record_md = proof_dir / "proof_record.md"
    record_csv = proof_dir / "proof_record_summary.csv"
    record_json = proof_dir / "proof_record_summary.json"
    _write_record(record_md, totals, rows, false_candidates, conditional)
    write_dict_rows_csv(record_csv, [totals.to_dict()])
    record_json.write_text(json.dumps(totals.to_dict(), indent=2), encoding="utf-8")
    paths = {
        "proof_record": record_md,
        "proof_record_summary": record_csv,
        "proof_record_json": record_json,
    }
    if make_bundle:
        paths["proof_bundle"] = write_evidence_bundle(
            proof_dir,
            bundle_name="proof_bundle.zip",
            bundle_kind="zerogate_frozen_proof_record_bundle",
        )
    return paths


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = freeze_proof_record(args.proof_dir, make_bundle=not args.no_bundle)
    print("ZeroGateSim proof record freeze complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
