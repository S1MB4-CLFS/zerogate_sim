from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from zerogate_sim.baselines import ModelComparison, compare_models
from zerogate_sim.config import SimulationConfig
from zerogate_sim.gates import GateScores, evaluate_run
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle, write_run_outputs
from zerogate_sim.signals import generate_pressure_field


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a ZeroGateSim seed sweep and write a single uploadable evidence bundle."
    )
    parser.add_argument("--start-seed", type=int, default=0, help="First seed in the sweep.")
    parser.add_argument("--count", type=int, default=10, help="Number of seeds to run.")
    parser.add_argument("--steps", type=int, default=600, help="Number of simulation steps per seed.")
    parser.add_argument("--dt", type=float, default=0.05, help="Time/order step size.")
    parser.add_argument("--noise-floor", type=float, default=0.12, help="Noise floor used by distinction gate.")
    parser.add_argument("--gate-threshold", type=float, default=0.55, help="Gate threshold for expression.")
    parser.add_argument("--strength-threshold", type=float, default=0.40, help="Minimum normalized strength for earned expression.")
    parser.add_argument("--out", type=Path, default=None, help="Batch output directory.")
    parser.add_argument("--plots", action="store_true", help="Generate PNG plots for every seed. Default is off for lean upload bundles.")
    return parser


def _best(rows: list[ModelComparison]) -> ModelComparison:
    return max(rows, key=lambda row: row.accuracy)


def _model_accuracy_map(rows: list[ModelComparison]) -> dict[str, float]:
    return {row.model: row.accuracy for row in rows}


def _seed_summary_row(
    *,
    seed: int,
    rows: list[GateScores],
    comparisons_designed: list[ModelComparison],
    comparisons_observed: list[ModelComparison],
) -> dict[str, object]:
    designed_ids = [row.candidate_id for row in rows if row.designed_stable]
    expressed_ids = [row.candidate_id for row in rows if row.trinary_value == 1]
    held_latent_ids = [row.candidate_id for row in rows if row.trinary_value == 0]
    fertile_hold_ids = [row.candidate_id for row in rows if row.zero_band == "fertile_hold"]
    witness_hold_ids = [row.candidate_id for row in rows if row.zero_band == "witness_hold"]
    quarantine_hold_ids = [row.candidate_id for row in rows if row.zero_band == "quarantine_hold"]
    rejected_ids = [row.candidate_id for row in rows if row.trinary_value == -1]
    z4_ids = [row.candidate_id for row in rows if row.zero_depth == 4]
    false_positive_ids = [row.candidate_id for row in rows if row.expressed and not row.designed_stable]
    false_negative_ids = [row.candidate_id for row in rows if row.designed_stable and not row.expressed]
    designed_held_ids = [row.candidate_id for row in rows if row.designed_stable and row.trinary_value == 0]
    designed_fertile_hold_ids = [row.candidate_id for row in rows if row.designed_stable and row.zero_band == "fertile_hold"]
    designed_witness_hold_ids = [row.candidate_id for row in rows if row.designed_stable and row.zero_band == "witness_hold"]
    designed_quarantine_hold_ids = [row.candidate_id for row in rows if row.designed_stable and row.zero_band == "quarantine_hold"]
    designed_rejected_ids = [row.candidate_id for row in rows if row.designed_stable and row.trinary_value == -1]
    health_only_ids = [row.candidate_id for row in rows if row.observed_stable and not row.expressed]
    best_designed = _best(comparisons_designed)
    best_observed = _best(comparisons_observed)
    return {
        "seed": seed,
        "designed_ids": ",".join(designed_ids),
        "expressed_ids": ",".join(expressed_ids),
        "held_latent_ids": ",".join(held_latent_ids),
        "fertile_hold_ids": ",".join(fertile_hold_ids),
        "witness_hold_ids": ",".join(witness_hold_ids),
        "quarantine_hold_ids": ",".join(quarantine_hold_ids),
        "rejected_ids": ",".join(rejected_ids),
        "z4_ids": ",".join(z4_ids),
        "false_positive_ids": ",".join(false_positive_ids),
        "false_negative_ids": ",".join(false_negative_ids),
        "designed_held_ids": ",".join(designed_held_ids),
        "designed_fertile_hold_ids": ",".join(designed_fertile_hold_ids),
        "designed_witness_hold_ids": ",".join(designed_witness_hold_ids),
        "designed_quarantine_hold_ids": ",".join(designed_quarantine_hold_ids),
        "designed_rejected_ids": ",".join(designed_rejected_ids),
        "health_only_ids": ",".join(health_only_ids),
        "best_designed_model": best_designed.model,
        "best_designed_accuracy": best_designed.accuracy,
        "best_designed_precision": best_designed.precision,
        "best_designed_recall": best_designed.recall,
        "best_observed_model": best_observed.model,
        "best_observed_accuracy": best_observed.accuracy,
        "best_observed_precision": best_observed.precision,
        "best_observed_recall": best_observed.recall,
    }


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _format_model_means(model_scores: dict[str, list[float]]) -> list[str]:
    lines: list[str] = []
    for model, values in sorted(model_scores.items(), key=lambda item: _mean(item[1]), reverse=True):
        lines.append(f"- `{model}` — mean accuracy={_mean(values):.3f}, min={min(values):.3f}, max={max(values):.3f}")
    return lines


def build_candidate_summary_rows(
    all_gate_rows: list[tuple[int, GateScores]],
) -> list[dict[str, object]]:
    """Aggregate candidate behavior across a batch.

    This is the v0.2.2 witness repair. It does not change the engine. It gives the
    human and assistant a clean way to see repeated false positives, false
    negatives, Z-depth without expression, and over-friendly observed-health.
    """

    grouped: dict[str, list[tuple[int, GateScores]]] = defaultdict(list)
    for seed, row in all_gate_rows:
        grouped[row.candidate_id].append((seed, row))

    out: list[dict[str, object]] = []
    for candidate_id in sorted(grouped):
        items = grouped[candidate_id]
        rows = [row for _, row in items]
        n = len(rows)
        first = rows[0]
        limiting_counts = Counter(row.limiting_gate for row in rows)
        false_negative_seeds = [seed for seed, row in items if row.designed_stable and not row.expressed]
        false_positive_seeds = [seed for seed, row in items if row.expressed and not row.designed_stable]
        designed_held_seeds = [seed for seed, row in items if row.designed_stable and row.trinary_value == 0]
        designed_fertile_hold_seeds = [seed for seed, row in items if row.designed_stable and row.zero_band == "fertile_hold"]
        designed_witness_hold_seeds = [seed for seed, row in items if row.designed_stable and row.zero_band == "witness_hold"]
        designed_quarantine_hold_seeds = [seed for seed, row in items if row.designed_stable and row.zero_band == "quarantine_hold"]
        designed_rejected_seeds = [seed for seed, row in items if row.designed_stable and row.trinary_value == -1]
        held_latent_seeds = [seed for seed, row in items if row.trinary_value == 0]
        fertile_hold_seeds = [seed for seed, row in items if row.zero_band == "fertile_hold"]
        witness_hold_seeds = [seed for seed, row in items if row.zero_band == "witness_hold"]
        quarantine_hold_seeds = [seed for seed, row in items if row.zero_band == "quarantine_hold"]
        rejected_seeds = [seed for seed, row in items if row.trinary_value == -1]
        z4_not_expressed_seeds = [seed for seed, row in items if row.zero_depth == 4 and not row.expressed]
        health_only_seeds = [seed for seed, row in items if row.observed_stable and not row.expressed]
        outcome_counts = Counter(row.trinary_outcome for row in rows)
        reason_counts = Counter(row.outcome_reason for row in rows)
        zero_band_counts = Counter(row.zero_band for row in rows)
        zero_band_reason_counts = Counter(row.zero_band_reason for row in rows)

        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first.kind,
                "designed_stable": first.designed_stable,
                "runs": n,
                "expressed_count": sum(1 for row in rows if row.trinary_value == 1),
                "expressed_rate": sum(1 for row in rows if row.trinary_value == 1) / n,
                "held_latent_count": len(held_latent_seeds),
                "held_latent_rate": len(held_latent_seeds) / n,
                "fertile_hold_count": len(fertile_hold_seeds),
                "fertile_hold_rate": len(fertile_hold_seeds) / n,
                "witness_hold_count": len(witness_hold_seeds),
                "witness_hold_rate": len(witness_hold_seeds) / n,
                "quarantine_hold_count": len(quarantine_hold_seeds),
                "quarantine_hold_rate": len(quarantine_hold_seeds) / n,
                "rejected_count": len(rejected_seeds),
                "rejected_rate": len(rejected_seeds) / n,
                "designed_held_count": len(designed_held_seeds),
                "designed_held_seeds": ",".join(str(seed) for seed in designed_held_seeds),
                "designed_fertile_hold_count": len(designed_fertile_hold_seeds),
                "designed_fertile_hold_seeds": ",".join(str(seed) for seed in designed_fertile_hold_seeds),
                "designed_witness_hold_count": len(designed_witness_hold_seeds),
                "designed_witness_hold_seeds": ",".join(str(seed) for seed in designed_witness_hold_seeds),
                "designed_quarantine_hold_count": len(designed_quarantine_hold_seeds),
                "designed_quarantine_hold_seeds": ",".join(str(seed) for seed in designed_quarantine_hold_seeds),
                "designed_rejected_count": len(designed_rejected_seeds),
                "designed_rejected_seeds": ",".join(str(seed) for seed in designed_rejected_seeds),
                "z4_count": sum(1 for row in rows if row.zero_depth == 4),
                "z4_rate": sum(1 for row in rows if row.zero_depth == 4) / n,
                "observed_health_count": sum(1 for row in rows if row.observed_stable),
                "observed_health_rate": sum(1 for row in rows if row.observed_stable) / n,
                "false_negative_count": len(false_negative_seeds),
                "false_negative_seeds": ",".join(str(seed) for seed in false_negative_seeds),
                "false_positive_count": len(false_positive_seeds),
                "false_positive_seeds": ",".join(str(seed) for seed in false_positive_seeds),
                "z4_not_expressed_count": len(z4_not_expressed_seeds),
                "z4_not_expressed_seeds": ",".join(str(seed) for seed in z4_not_expressed_seeds),
                "health_only_count": len(health_only_seeds),
                "health_only_seeds": ",".join(str(seed) for seed in health_only_seeds),
                "mean_latent_score": _mean([row.latent_score for row in rows]),
                "outcome_counts": ";".join(f"{name}:{count}" for name, count in sorted(outcome_counts.items())),
                "outcome_reason_counts": ";".join(f"{name}:{count}" for name, count in sorted(reason_counts.items())),
                "zero_band_counts": ";".join(f"{name}:{count}" for name, count in sorted(zero_band_counts.items())),
                "zero_band_reason_counts": ";".join(f"{name}:{count}" for name, count in sorted(zero_band_reason_counts.items())),
                "mean_strength": _mean([row.strength for row in rows]),
                "mean_D": _mean([row.distinction for row in rows]),
                "mean_P": _mean([row.polarity for row in rows]),
                "mean_R": _mean([row.relation for row in rows]),
                "mean_return": _mean([row.return_observed for row in rows]),
                "mean_Gamma": _mean([row.return_potential for row in rows]),
                "mean_C_Z": _mean([row.zero_coherence for row in rows]),
                "mean_observed_health": _mean([row.observed_stability_score for row in rows]),
                "limiting_gate_counts": ";".join(f"{gate}:{count}" for gate, count in sorted(limiting_counts.items())),
            }
        )
    return out


def _candidate_pressure_lines(candidate_rows: list[dict[str, object]]) -> list[str]:
    designed_held = [row for row in candidate_rows if int(row.get("designed_held_count", 0)) > 0]
    designed_rejected = [row for row in candidate_rows if int(row.get("designed_rejected_count", 0)) > 0]
    false_pos = [row for row in candidate_rows if int(row["false_positive_count"]) > 0]
    z4_held = [row for row in candidate_rows if int(row["z4_not_expressed_count"]) > 0]
    health_only = [row for row in candidate_rows if int(row["health_only_count"]) > 0 and not bool(row["designed_stable"])]

    lines: list[str] = []
    lines.append("## Candidate-level witness")
    lines.append("")
    lines.append("| candidate | kind | designed | +1 expr | 0+ fertile | 0 witness | 0- quarantine | -1 rejected | designed 0+ | designed 0 | designed 0- | Z^4 held | mean latent | mean C_Z | mean return |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in candidate_rows:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['designed_stable']} | "
            f"{float(row['expressed_rate']):.2f} | {float(row['fertile_hold_rate']):.2f} | "
            f"{float(row['witness_hold_rate']):.2f} | {float(row['quarantine_hold_rate']):.2f} | "
            f"{float(row['rejected_rate']):.2f} | {row['designed_fertile_hold_count']} | "
            f"{row['designed_witness_hold_count']} | {row['designed_quarantine_hold_count']} | "
            f"{row['z4_not_expressed_count']} | {float(row['mean_latent_score']):.3f} | "
            f"{float(row['mean_C_Z']):.3f} | {float(row['mean_return']):.3f} |"
        )
    lines.append("")
    lines.append("## Repair pressure")
    lines.append("")
    if designed_held:
        items = ", ".join(
            f"`{row['candidate_id']}`(0+ {row.get('designed_fertile_hold_count', 0)}, 0 {row.get('designed_witness_hold_count', 0)}, 0- {row.get('designed_quarantine_hold_count', 0)})"
            for row in designed_held
        )
        lines.append(f"- 0-state designed hold: {items}. The hold is now split into fertile, witness, and quarantine pressure.")
    else:
        lines.append("- 0-state designed hold: none.")

    if designed_rejected:
        items = ", ".join(f"`{row['candidate_id']}`({row['designed_rejected_count']})" for row in designed_rejected)
        lines.append(f"- -1 designed rejection pressure: {items}. These are the true conservative wound.")
    else:
        lines.append("- -1 designed rejection pressure: none.")

    if false_pos:
        items = ", ".join(f"`{row['candidate_id']}`({row['false_positive_count']})" for row in false_pos)
        lines.append(f"- False-positive pressure: {items}. Trap freedoms sometimes pass current expression.")
    else:
        lines.append("- False-positive pressure: none against designed-stable labels.")

    if z4_held:
        items = ", ".join(f"`{row['candidate_id']}`({row['z4_not_expressed_count']})" for row in z4_held)
        lines.append(f"- Z-depth/strength boundary pressure: {items}. These reached Z^4 but were held back, usually by strength or expression threshold.")
    else:
        lines.append("- Z-depth/strength boundary pressure: none.")

    if health_only:
        items = ", ".join(f"`{row['candidate_id']}`({row['health_only_count']})" for row in health_only)
        lines.append(f"- Observed-health overfriendliness: {items}. These look signal-healthy without earning expression; do not use observed-health as proof.")
    else:
        lines.append("- Observed-health overfriendliness: none.")
    lines.append("")
    return lines


def write_batch_summary(
    *,
    path: Path,
    start_seed: int,
    count: int,
    seed_rows: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
    designed_model_scores: dict[str, list[float]],
    observed_model_scores: dict[str, list[float]],
) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Batch Summary")
    lines.append("")
    lines.append(f"Seeds: `{start_seed}` through `{start_seed + count - 1}`")
    lines.append(f"Count: `{count}`")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a toy seed sweep. It checks whether the current operator behaves consistently across generated fields. It does not prove cosmology, physics, or final trinary logic.")
    lines.append("")
    lines.append("## Designed-stable aggregate")
    lines.append("")
    lines.extend(_format_model_means(designed_model_scores))
    lines.append("")
    lines.append("## Observed signal-health aggregate — diagnostic only")
    lines.append("")
    lines.append("This target is deliberately marked as signal-health, not earned dimensional expression. If it rewards polarity, average gates, or relation more than zero-gate, that is mechanism-boundary pressure on the witness target, not disproof of the zero-gate operator.")
    lines.append("")
    lines.extend(_format_model_means(observed_model_scores))
    lines.append("")
    lines.append("## Seed-level witness")
    lines.append("")
    lines.append("| seed | expressed | Z^4 | false positives | false negatives | health-only | best designed | best signal-health |")
    lines.append("|---:|---|---|---|---|---|---|---|")
    for row in seed_rows:
        lines.append(
            f"| {row['seed']} | {row['expressed_ids']} | {row['z4_ids']} | "
            f"{row['false_positive_ids']} | {row['false_negative_ids']} | {row['health_only_ids']} | "
            f"{row['best_designed_model']} ({float(row['best_designed_accuracy']):.3f}) | "
            f"{row['best_observed_model']} ({float(row['best_observed_accuracy']):.3f}) |"
        )
    lines.append("")
    lines.extend(_candidate_pressure_lines(candidate_rows))
    lines.append("## DREED-style witness note")
    lines.append("")
    lines.append("Mechanism-boundary: designed-stable labels test whether the operator matches the toy generator's intended traps; observed-stable labels currently test loose signal health and may not represent earned dimensional expression.")
    lines.append("")
    lines.append("Integration-modularity: this report belongs in the batch witness layer. It shows whether the current gate engine and expression boundary behave consistently across seeds before any larger theory claim is allowed.")
    lines.append("")
    lines.append("Witness-translation: upload `batch_bundle.zip` when asking for review. It contains all run summaries, CSVs, metadata, aggregate tables, candidate diagnostics, and the manifest. No crumb-hunting ritual required.")
    lines.append("")
    lines.append("Overdo risk: a friendly sweep is still toy evidence. The primate may grin. It may not notarize reality.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_batch(
    *,
    start_seed: int = 0,
    count: int = 10,
    steps: int = 600,
    dt: float = 0.05,
    noise_floor: float = 0.12,
    gate_threshold: float = 0.55,
    strength_threshold: float = 0.30,
    output_dir: Path | None = None,
    make_plots: bool = False,
) -> dict[str, Path]:
    if count <= 0:
        raise ValueError("count must be positive")

    end_seed = start_seed + count - 1
    batch_dir = ensure_dir(output_dir or Path(f"runs/sweep_{start_seed}_{end_seed}"))

    seed_rows: list[dict[str, object]] = []
    all_gate_rows: list[tuple[int, GateScores]] = []
    designed_model_scores: dict[str, list[float]] = defaultdict(list)
    observed_model_scores: dict[str, list[float]] = defaultdict(list)

    for seed in range(start_seed, start_seed + count):
        run_dir = batch_dir / f"seed_{seed}"
        config = SimulationConfig(
            seed=seed,
            n_steps=steps,
            dt=dt,
            noise_floor=noise_floor,
            gate_threshold=gate_threshold,
            strength_threshold=strength_threshold,
            output_dir=run_dir,
        )
        run = generate_pressure_field(seed=seed, n_steps=steps, dt=dt)
        rows = evaluate_run(
            run,
            noise_floor=noise_floor,
            gate_threshold=gate_threshold,
            strength_threshold=strength_threshold,
        )
        comparisons_designed = compare_models(rows, threshold=gate_threshold, truth_field="designed_stable", seed=seed)
        comparisons_observed = compare_models(rows, threshold=gate_threshold, truth_field="observed_stable", seed=seed + 1)
        write_run_outputs(
            run=run,
            config=config,
            rows=rows,
            comparisons_designed=comparisons_designed,
            comparisons_observed=comparisons_observed,
            make_plots=make_plots,
            make_bundle=True,
        )
        seed_rows.append(
            _seed_summary_row(
                seed=seed,
                rows=rows,
                comparisons_designed=comparisons_designed,
                comparisons_observed=comparisons_observed,
            )
        )
        all_gate_rows.extend((seed, row) for row in rows)
        for model, accuracy in _model_accuracy_map(comparisons_designed).items():
            designed_model_scores[model].append(accuracy)
        for model, accuracy in _model_accuracy_map(comparisons_observed).items():
            observed_model_scores[model].append(accuracy)

    candidate_rows = build_candidate_summary_rows(all_gate_rows)

    seed_csv = batch_dir / "batch_seed_summary.csv"
    candidate_csv = batch_dir / "batch_candidate_summary.csv"
    summary_md = batch_dir / "batch_summary.md"
    write_dict_rows_csv(seed_csv, seed_rows)
    write_dict_rows_csv(candidate_csv, candidate_rows)
    write_batch_summary(
        path=summary_md,
        start_seed=start_seed,
        count=count,
        seed_rows=seed_rows,
        candidate_rows=candidate_rows,
        designed_model_scores=dict(designed_model_scores),
        observed_model_scores=dict(observed_model_scores),
    )
    bundle = write_evidence_bundle(
        batch_dir,
        bundle_name="batch_bundle.zip",
        bundle_kind="zerogate_batch_evidence_bundle",
    )

    return {
        "batch_summary": summary_md,
        "batch_seed_summary": seed_csv,
        "batch_candidate_summary": candidate_csv,
        "batch_bundle": bundle,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = run_batch(
        start_seed=args.start_seed,
        count=args.count,
        steps=args.steps,
        dt=args.dt,
        noise_floor=args.noise_floor,
        gate_threshold=args.gate_threshold,
        strength_threshold=args.strength_threshold,
        output_dir=args.out,
        make_plots=args.plots,
    )

    print("ZeroGateSim batch complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Upload batch_bundle.zip when asking for review. The witness now gets one clean package, not a breadcrumb salad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
