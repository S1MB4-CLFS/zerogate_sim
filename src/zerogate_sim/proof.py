from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from zerogate_sim.matrix import build_scenarios, run_matrix
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

ADVERSARIAL_CORPORA: tuple[tuple[str, str, str], ...] = (
    (
        "distinction",
        "adversary_distinction",
        "visible/loud/high-contrast candidates try to pass as earned one",
    ),
    (
        "polarity",
        "adversary_polarity",
        "oscillating/zero-crossing/beautiful-pulse candidates try to pass as earned return",
    ),
    (
        "relation",
        "adversary_relation",
        "borrowed-coherence/field-echo candidates try to pass as independent one",
    ),
)


@dataclass(frozen=True)
class ProofCorpusResult:
    axis: str
    candidate_profile: str
    description: str
    matrix_dir: Path
    scenario_count: int
    seed_count: int
    seeded_run_count: int
    candidate_count: int
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
    status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "axis": self.axis,
            "candidate_profile": self.candidate_profile,
            "description": self.description,
            "matrix_dir": str(self.matrix_dir),
            "scenario_count": self.scenario_count,
            "seed_count": self.seed_count,
            "seeded_run_count": self.seeded_run_count,
            "candidate_count": self.candidate_count,
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
            "status": self.status,
            "reason": self.reason,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the trinary adversarial proof harness: distinction, polarity, relation."
    )
    parser.add_argument("--profile", choices=["triad27", "deep81", "wide243"], default="wide243")
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--count", type=int, default=9)
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--plots", action="store_true", help="Generate per-seed plots. Usually keep off; proof weather is already heavy.")
    return parser


def _int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if value in {"", None}:
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _summarize_matrix(
    *,
    axis: str,
    candidate_profile: str,
    description: str,
    matrix_dir: Path,
    scenario_count: int,
    seed_count: int,
) -> ProofCorpusResult:
    final_csv = matrix_dir / "matrix_final_output_summary.csv"
    if not final_csv.exists():
        raise FileNotFoundError(f"Missing final output summary: {final_csv}")
    final_rows = _read_csv(final_csv)

    final_earned = sum(_int(row, "final_earned_one_count") for row in final_rows)
    raw_expression = sum(_int(row, "raw_expression_pressure") for row in final_rows)
    false_pressure = sum(_int(row, "raw_false_one_pressure") for row in final_rows)
    false_demoted = sum(_int(row, "false_one_demoted_count") for row in final_rows)
    latent_pressure = sum(_int(row, "latent_overcrown_pressure") for row in final_rows)
    latent_demoted = sum(_int(row, "latent_overcrown_demoted_count") for row in final_rows)

    expresser_rows = [row for row in final_rows if row.get("truth_role") == "expresser"]
    trap_rows = [row for row in final_rows if row.get("truth_role") == "trap"]
    earned_expressers = [row for row in expresser_rows if _int(row, "final_earned_one_count") > 0]
    trap_final_crowns = [row for row in trap_rows if row.get("final_trinary_symbol") == "+1"]
    final_false_crowns = len(trap_final_crowns)

    if final_false_crowns > 0:
        status = "fail"
        reason = "one or more trap candidates reached final +1; proof harness must not crown false one"
    elif len(earned_expressers) >= 3 and final_earned > 0:
        status = "pass"
        reason = "earned-one final output protected the crown while preserving the core expressers"
    elif final_earned > 0:
        status = "hold"
        reason = "no false crown, but too few core expressers earned one in this adversarial weather"
    else:
        status = "hold"
        reason = "no false crown, but no core expresser earned one under this short or harsh proof weather"

    return ProofCorpusResult(
        axis=axis,
        candidate_profile=candidate_profile,
        description=description,
        matrix_dir=matrix_dir,
        scenario_count=scenario_count,
        seed_count=seed_count,
        seeded_run_count=scenario_count * seed_count,
        candidate_count=len(final_rows),
        final_earned_one_events=final_earned,
        raw_expression_pressure=raw_expression,
        raw_false_one_pressure=false_pressure,
        false_one_demoted_count=false_demoted,
        final_false_one_crowns=final_false_crowns,
        latent_overcrown_pressure=latent_pressure,
        latent_overcrown_demoted_count=latent_demoted,
        expresser_candidate_count=len(expresser_rows),
        earned_expresser_candidate_count=len(earned_expressers),
        trap_candidate_count=len(trap_rows),
        trap_final_crown_count=len(trap_final_crowns),
        status=status,
        reason=reason,
    )


def _write_proof_read(path: Path, *, profile: str, start_seed: int, count: int, results: list[ProofCorpusResult]) -> None:
    total_cells = sum(row.scenario_count for row in results)
    total_runs = sum(row.seeded_run_count for row in results)
    total_earned = sum(row.final_earned_one_events for row in results)
    total_false_pressure = sum(row.raw_false_one_pressure for row in results)
    total_false_demoted = sum(row.false_one_demoted_count for row in results)
    final_false_crowns = sum(row.final_false_one_crowns for row in results)
    pass_count = sum(1 for row in results if row.status == "pass")
    status = "first_research_alpha_candidate" if pass_count == len(results) and final_false_crowns == 0 else "hold"

    lines: list[str] = []
    lines.append("# ZeroGateSim Trinary Adversarial Proof Harness")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a proof-of-concept harness inside generated toy fields. It does not prove cosmology, physics, or final trinary logic. It tests whether the current earned-one witness can protect +1 expression across three adversarial dependency axes: distinction, polarity, and relation.")
    lines.append("")
    lines.append("## Run shape")
    lines.append("")
    lines.append(f"Profile: `{profile}`")
    lines.append(f"Seed range: `{start_seed}` to `{start_seed + count - 1}`")
    lines.append(f"Adversarial corpora: `{len(results)}`")
    lines.append(f"Scenario cells: `{total_cells}`")
    lines.append(f"Seeded simulation runs: `{total_runs}`")
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(f"Final earned-one events across the harness: `{total_earned}`.")
    lines.append("Earned-one remains the only accepted +1 crown. Raw local expression is pressure, not final truth.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append("The harness is trinary because it pressures three dependency wounds:")
    lines.append("")
    lines.append("- distinction: visibility and contrast pretending to be reality;")
    lines.append("- polarity: pulse and zero-crossing pretending to be return;")
    lines.append("- relation: borrowed coherence pretending to be earned one.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(f"Raw false-one pressure: `{total_false_pressure}`.")
    lines.append(f"False-one events demoted before final crown: `{total_false_demoted}`.")
    lines.append(f"Final false-one crowns: `{final_false_crowns}`.")
    lines.append("")
    lines.append("## Proof posture")
    lines.append("")
    lines.append(f"Status: `{status}`")
    lines.append("")
    if status == "first_research_alpha_candidate":
        lines.append("The earned-one witness passed the current trinary adversarial harness. This is a candidate first-research-alpha proof record, not a cosmic proof. The primate may dance; it may not notarize the universe.")
    else:
        lines.append("The harness remains in HOLD. Read the corpus-level rows below before changing the core gate; the wound may be in candidate design, witness language, or a real breach.")
    lines.append("")
    lines.append("## Corpus table")
    lines.append("")
    lines.append("| axis | profile | status | cells | runs | earned | raw false | demoted false | final false crowns | earned expressers | reason |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in results:
        lines.append(
            f"| {row.axis} | {row.candidate_profile} | {row.status} | {row.scenario_count} | {row.seeded_run_count} | "
            f"{row.final_earned_one_events} | {row.raw_false_one_pressure} | {row.false_one_demoted_count} | "
            f"{row.final_false_one_crowns} | {row.earned_expresser_candidate_count}/{row.expresser_candidate_count} | {row.reason} |"
        )
    lines.append("")
    lines.append("## Final sentence")
    lines.append("")
    lines.append("The first victory boundary is not that every raw expression is accepted. The boundary is that final +1 belongs only to earned-one, while distinction noise, polarity theater, and relation echo are either held or demoted.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_proof_harness(
    *,
    profile: str = "wide243",
    start_seed: int = 0,
    count: int = 9,
    steps: int = 600,
    dt: float = 0.05,
    output_dir: Path | None = None,
    make_plots: bool = False,
) -> dict[str, Path]:
    proof_dir = ensure_dir(output_dir or Path(f"runs/proof_{profile}_{start_seed}_{start_seed + count - 1}"))
    scenario_count = len(build_scenarios(profile))
    results: list[ProofCorpusResult] = []

    for axis, candidate_profile, description in ADVERSARIAL_CORPORA:
        corpus_dir = proof_dir / axis
        print(f"[proof] {axis}: profile={candidate_profile}, scenarios={scenario_count}, seeds={count}", flush=True)
        run_matrix(
            profile=profile,
            candidate_profile=candidate_profile,
            start_seed=start_seed,
            count=count,
            steps=steps,
            dt=dt,
            output_dir=corpus_dir,
            make_plots=make_plots,
        )
        results.append(
            _summarize_matrix(
                axis=axis,
                candidate_profile=candidate_profile,
                description=description,
                matrix_dir=corpus_dir,
                scenario_count=scenario_count,
                seed_count=count,
            )
        )

    summary_csv = proof_dir / "proof_harness_summary.csv"
    read_md = proof_dir / "proof_harness_read.md"
    write_dict_rows_csv(summary_csv, [row.to_dict() for row in results])
    _write_proof_read(read_md, profile=profile, start_seed=start_seed, count=count, results=results)
    bundle = write_evidence_bundle(
        proof_dir,
        bundle_name="proof_bundle.zip",
        bundle_kind="zerogate_trinary_adversarial_proof_bundle",
    )
    return {
        "proof_harness_summary": summary_csv,
        "proof_harness_read": read_md,
        "proof_bundle": bundle,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = run_proof_harness(
        profile=args.profile,
        start_seed=args.start_seed,
        count=args.count,
        steps=args.steps,
        dt=args.dt,
        output_dir=args.out,
        make_plots=args.plots,
    )
    print("ZeroGateSim trinary adversarial proof harness complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Upload proof_bundle.zip for review. This is the proof harness, not a breadcrumb salad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
