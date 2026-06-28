from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from statistics import mean
from typing import Callable

import numpy as np

from zerogate_sim.baselines import ModelComparison, compare_models
from zerogate_sim.batch import build_candidate_summary_rows
from zerogate_sim.config import SimulationConfig
from zerogate_sim.gates import GateScores, evaluate_run
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle, write_run_outputs
from zerogate_sim.signals import CandidateSpec, SimulationRun, default_candidate_specs, generate_pressure_field


class StressScenario:
    """Named stress profile for alpha robustness sweeps.

    These are not alternate physics. They are controlled ways to ask whether the
    current zero-gate operator only works in the friendly default field, or whether
    its witness shape survives changed pressure.
    """

    def __init__(
        self,
        name: str,
        description: str,
        spec_transform: Callable[[list[CandidateSpec]], list[CandidateSpec]] | None = None,
        signal_transform: Callable[[SimulationRun, int], SimulationRun] | None = None,
        noise_floor: float = 0.12,
        gate_threshold: float = 0.55,
        strength_threshold: float = 0.40,
    ) -> None:
        self.name = name
        self.description = description
        self.spec_transform = spec_transform
        self.signal_transform = signal_transform
        self.noise_floor = noise_floor
        self.gate_threshold = gate_threshold
        self.strength_threshold = strength_threshold


def _scale_noise(factor: float) -> Callable[[list[CandidateSpec]], list[CandidateSpec]]:
    def transform(specs: list[CandidateSpec]) -> list[CandidateSpec]:
        return [replace(spec, noise=spec.noise * factor) for spec in specs]

    return transform


def _scale_relation(factor: float) -> Callable[[list[CandidateSpec]], list[CandidateSpec]]:
    def transform(specs: list[CandidateSpec]) -> list[CandidateSpec]:
        return [replace(spec, relation_weight=spec.relation_weight * factor) for spec in specs]

    return transform


def _stable_strength_dip(factor: float) -> Callable[[list[CandidateSpec]], list[CandidateSpec]]:
    def transform(specs: list[CandidateSpec]) -> list[CandidateSpec]:
        out: list[CandidateSpec] = []
        for spec in specs:
            if spec.designed_stable:
                out.append(replace(spec, amplitude=spec.amplitude * factor))
            else:
                out.append(spec)
        return out

    return transform


def _late_noise_shock(strength: float) -> Callable[[SimulationRun, int], SimulationRun]:
    def transform(run: SimulationRun, seed: int) -> SimulationRun:
        rng = np.random.default_rng(seed + 100_000)
        signals = np.array(run.signals, copy=True)
        n = signals.shape[1]
        start = int(0.72 * n)
        ramp = np.linspace(0.0, 1.0, n - start)
        signals[:, start:] += strength * ramp * rng.normal(0.0, 1.0, size=signals[:, start:].shape)
        metadata = dict(run.metadata)
        metadata["stress_signal_transform"] = f"late_noise_shock:{strength}"
        return SimulationRun(t=run.t, signals=signals, specs=run.specs, seed=run.seed, metadata=metadata)

    return transform


SCENARIOS: dict[str, StressScenario] = {
    "baseline": StressScenario(
        name="baseline",
        description="default v0.2.4 field; friendly control condition",
    ),
    "noisy": StressScenario(
        name="noisy",
        description="candidate noise increased; tests distinction and return resilience",
        spec_transform=_scale_noise(1.65),
        noise_floor=0.16,
    ),
    "weak_relation": StressScenario(
        name="weak_relation",
        description="relation coupling reduced; tests whether relation gate carries real pressure",
        spec_transform=_scale_relation(0.55),
    ),
    "stable_strength_dip": StressScenario(
        name="stable_strength_dip",
        description="designed-stable amplitudes reduced; tests expression strength boundary",
        spec_transform=_stable_strength_dip(0.82),
    ),
    "late_noise_shock": StressScenario(
        name="late_noise_shock",
        description="late stochastic disturbance added after generation; tests return and persistence under stress",
        signal_transform=_late_noise_shock(0.13),
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run ZeroGateSim stress scenarios and write one uploadable evidence bundle."
    )
    parser.add_argument("--start-seed", type=int, default=0, help="First seed in each scenario.")
    parser.add_argument("--count", type=int, default=10, help="Number of seeds per scenario.")
    parser.add_argument("--steps", type=int, default=600, help="Number of simulation steps per seed.")
    parser.add_argument("--dt", type=float, default=0.05, help="Time/order step size.")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS.keys()),
        help="Scenario to run. May be repeated. Defaults to all scenarios.",
    )
    parser.add_argument("--out", type=Path, default=None, help="Stress output directory.")
    parser.add_argument("--plots", action="store_true", help="Generate PNG plots for every scenario seed.")
    return parser


def _best(rows: list[ModelComparison]) -> ModelComparison:
    return max(rows, key=lambda row: row.accuracy)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _scenario_seed_row(
    *,
    scenario: StressScenario,
    seed: int,
    rows: list[GateScores],
    comparisons_designed: list[ModelComparison],
    comparisons_observed: list[ModelComparison],
) -> dict[str, object]:
    designed_ids = [row.candidate_id for row in rows if row.designed_stable]
    expressed_ids = [row.candidate_id for row in rows if row.trinary_value == 1]
    held_latent_ids = [row.candidate_id for row in rows if row.trinary_value == 0]
    rejected_ids = [row.candidate_id for row in rows if row.trinary_value == -1]
    z4_ids = [row.candidate_id for row in rows if row.zero_depth == 4]
    false_positive_ids = [row.candidate_id for row in rows if row.expressed and not row.designed_stable]
    false_negative_ids = [row.candidate_id for row in rows if row.designed_stable and not row.expressed]
    designed_held_ids = [row.candidate_id for row in rows if row.designed_stable and row.trinary_value == 0]
    designed_rejected_ids = [row.candidate_id for row in rows if row.designed_stable and row.trinary_value == -1]
    health_only_ids = [row.candidate_id for row in rows if row.observed_stable and not row.expressed]
    best_designed = _best(comparisons_designed)
    best_observed = _best(comparisons_observed)
    return {
        "scenario": scenario.name,
        "seed": seed,
        "designed_ids": ",".join(designed_ids),
        "expressed_ids": ",".join(expressed_ids),
        "held_latent_ids": ",".join(held_latent_ids),
        "rejected_ids": ",".join(rejected_ids),
        "z4_ids": ",".join(z4_ids),
        "false_positive_ids": ",".join(false_positive_ids),
        "false_negative_ids": ",".join(false_negative_ids),
        "designed_held_ids": ",".join(designed_held_ids),
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


def _scenario_summary_rows(seed_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    scenarios = sorted({str(row["scenario"]) for row in seed_rows})
    out: list[dict[str, object]] = []
    for scenario in scenarios:
        rows = [row for row in seed_rows if row["scenario"] == scenario]
        false_pos = [str(row["false_positive_ids"]) for row in rows if str(row["false_positive_ids"])]
        false_neg = [str(row["false_negative_ids"]) for row in rows if str(row["false_negative_ids"])]
        designed_held = [str(row["designed_held_ids"]) for row in rows if str(row["designed_held_ids"])]
        designed_rejected = [str(row["designed_rejected_ids"]) for row in rows if str(row["designed_rejected_ids"])]
        expressed_sets = sorted({str(row["expressed_ids"]) for row in rows})
        held_sets = sorted({str(row["held_latent_ids"]) for row in rows})
        z4_sets = sorted({str(row["z4_ids"]) for row in rows})
        out.append(
            {
                "scenario": scenario,
                "runs": len(rows),
                "mean_designed_accuracy": _mean([float(row["best_designed_accuracy"]) for row in rows]),
                "mean_signal_health_accuracy": _mean([float(row["best_observed_accuracy"]) for row in rows]),
                "false_positive_runs": len(false_pos),
                "false_negative_runs": len(false_neg),
                "designed_held_runs": len(designed_held),
                "designed_rejected_runs": len(designed_rejected),
                "expressed_sets": " | ".join(expressed_sets),
                "held_sets": " | ".join(held_sets),
                "z4_sets": " | ".join(z4_sets),
                "best_designed_models": ";".join(
                    f"{model}:{sum(1 for row in rows if row['best_designed_model'] == model)}"
                    for model in sorted({str(row["best_designed_model"]) for row in rows})
                ),
                "best_signal_health_models": ";".join(
                    f"{model}:{sum(1 for row in rows if row['best_observed_model'] == model)}"
                    for model in sorted({str(row["best_observed_model"]) for row in rows})
                ),
            }
        )
    return out


def write_stress_summary(
    *,
    path: Path,
    scenarios: list[StressScenario],
    start_seed: int,
    count: int,
    scenario_rows: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
) -> None:
    lines: list[str] = []
    lines.append("# ZeroGateSim Stress Summary")
    lines.append("")
    lines.append(f"Seeds per scenario: `{start_seed}` through `{start_seed + count - 1}`")
    lines.append(f"Count per scenario: `{count}`")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a toy stress sweep. It does not prove cosmology, physics, or final trinary logic. It asks whether the current zero-gate operator survives controlled changes in noise, relation, strength, and perturbation.")
    lines.append("")
    lines.append("## Scenarios")
    lines.append("")
    for scenario in scenarios:
        lines.append(f"- `{scenario.name}` — {scenario.description}")
    lines.append("")
    lines.append("## Scenario-level witness")
    lines.append("")
    lines.append("| scenario | runs | mean designed accuracy | breach | designed held | designed rejected | +1 sets | 0 sets | best designed models |")
    lines.append("|---|---:|---:|---:|---:|---:|---|---|---|")
    for row in scenario_rows:
        lines.append(
            f"| {row['scenario']} | {row['runs']} | {float(row['mean_designed_accuracy']):.3f} | "
            f"{row['false_positive_runs']} | {row['designed_held_runs']} | {row['designed_rejected_runs']} | "
            f"{row['expressed_sets']} | {row['held_sets']} | {row['best_designed_models']} |"
        )
    lines.append("")
    lines.append("## Candidate-level pressure across stress")
    lines.append("")
    lines.append("| scenario:candidate | kind | designed | +1 expr | 0 held | -1 rejected | designed held | designed rejected | Z^4 held | mean latent | mean C_Z | mean return |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in candidate_rows:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['designed_stable']} | "
            f"{float(row['expressed_rate']):.2f} | {float(row['held_latent_rate']):.2f} | "
            f"{float(row['rejected_rate']):.2f} | {row['designed_held_count']} | "
            f"{row['designed_rejected_count']} | {row['z4_not_expressed_count']} | "
            f"{float(row['mean_latent_score']):.3f} | {float(row['mean_C_Z']):.3f} | {float(row['mean_return']):.3f} |"
        )
    lines.append("")
    lines.append("## DREED-style witness note")
    lines.append("")
    lines.append("Mechanism-boundary: stress scenarios test robustness inside the toy generator. They still do not measure physical dimensions.")
    lines.append("")
    lines.append("Integration-modularity: use this report before changing gates. If a scenario fails, inspect whether the failure is a gate problem, a threshold problem, or an intentionally harsh condition.")
    lines.append("")
    lines.append("Witness-translation: upload `stress_bundle.zip` for review. It contains scenario summaries, seed summaries, candidate diagnostics, all per-run evidence, and a manifest.")
    lines.append("")
    lines.append("Overdo risk: robustness under toy stress is still not cosmic confirmation. The primate may grin, but it may not issue passports to reality.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_stress(
    *,
    start_seed: int = 0,
    count: int = 10,
    steps: int = 600,
    dt: float = 0.05,
    scenario_names: list[str] | None = None,
    output_dir: Path | None = None,
    make_plots: bool = False,
) -> dict[str, Path]:
    if count <= 0:
        raise ValueError("count must be positive")

    selected = [SCENARIOS[name] for name in (scenario_names or sorted(SCENARIOS.keys()))]
    stress_dir = ensure_dir(output_dir or Path(f"runs/stress_{start_seed}_{start_seed + count - 1}"))

    seed_rows: list[dict[str, object]] = []
    all_gate_rows: list[tuple[int, GateScores]] = []

    for scenario in selected:
        specs = default_candidate_specs()
        if scenario.spec_transform is not None:
            specs = scenario.spec_transform(specs)
        for seed in range(start_seed, start_seed + count):
            run_dir = stress_dir / scenario.name / f"seed_{seed}"
            config = SimulationConfig(
                seed=seed,
                n_steps=steps,
                dt=dt,
                noise_floor=scenario.noise_floor,
                gate_threshold=scenario.gate_threshold,
                strength_threshold=scenario.strength_threshold,
                output_dir=run_dir,
            )
            run = generate_pressure_field(seed=seed, n_steps=steps, dt=dt, specs=specs)
            if scenario.signal_transform is not None:
                run = scenario.signal_transform(run, seed)
            metadata = dict(run.metadata)
            metadata["stress_scenario"] = scenario.name
            metadata["stress_description"] = scenario.description
            run = SimulationRun(t=run.t, signals=run.signals, specs=run.specs, seed=run.seed, metadata=metadata)
            rows = evaluate_run(
                run,
                noise_floor=scenario.noise_floor,
                gate_threshold=scenario.gate_threshold,
                strength_threshold=scenario.strength_threshold,
            )
            comparisons_designed = compare_models(rows, threshold=scenario.gate_threshold, truth_field="designed_stable", seed=seed)
            comparisons_observed = compare_models(rows, threshold=scenario.gate_threshold, truth_field="observed_stable", seed=seed + 1)
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
                _scenario_seed_row(
                    scenario=scenario,
                    seed=seed,
                    rows=rows,
                    comparisons_designed=comparisons_designed,
                    comparisons_observed=comparisons_observed,
                )
            )
            # Use a synthetic seed id that preserves scenario in candidate id summary.
            all_gate_rows.extend((seed, replace_gate_candidate_id(row, scenario.name)) for row in rows)

    scenario_rows = _scenario_summary_rows(seed_rows)
    candidate_rows = build_candidate_summary_rows(all_gate_rows)

    seed_csv = stress_dir / "stress_seed_summary.csv"
    scenario_csv = stress_dir / "stress_scenario_summary.csv"
    candidate_csv = stress_dir / "stress_candidate_summary.csv"
    summary_md = stress_dir / "stress_summary.md"
    write_dict_rows_csv(seed_csv, seed_rows)
    write_dict_rows_csv(scenario_csv, scenario_rows)
    write_dict_rows_csv(candidate_csv, candidate_rows)
    write_stress_summary(
        path=summary_md,
        scenarios=selected,
        start_seed=start_seed,
        count=count,
        scenario_rows=scenario_rows,
        candidate_rows=candidate_rows,
    )
    bundle = write_evidence_bundle(
        stress_dir,
        bundle_name="stress_bundle.zip",
        bundle_kind="zerogate_stress_evidence_bundle",
    )
    return {
        "stress_summary": summary_md,
        "stress_seed_summary": seed_csv,
        "stress_scenario_summary": scenario_csv,
        "stress_candidate_summary": candidate_csv,
        "stress_bundle": bundle,
    }


def replace_gate_candidate_id(row: GateScores, scenario_name: str) -> GateScores:
    """Prefix candidate IDs in stress candidate aggregation without changing per-run files."""

    return GateScores(
        candidate_id=f"{scenario_name}:{row.candidate_id}",
        kind=row.kind,
        description=row.description,
        designed_stable=row.designed_stable,
        truth_role=row.truth_role,
        expected_trinary=row.expected_trinary,
        strength=row.strength,
        distinction=row.distinction,
        polarity=row.polarity,
        relation=row.relation,
        return_observed=row.return_observed,
        return_potential=row.return_potential,
        echo_mimic_score=row.echo_mimic_score,
        echo_mimic_band=row.echo_mimic_band,
        zero_coherence=row.zero_coherence,
        zero_depth=row.zero_depth,
        expressed=row.expressed,
        trinary_value=row.trinary_value,
        trinary_outcome=row.trinary_outcome,
        outcome_reason=row.outcome_reason,
        latent_score=row.latent_score,
        zero_band_value=row.zero_band_value,
        zero_band=row.zero_band,
        zero_band_symbol=row.zero_band_symbol,
        zero_band_reason=row.zero_band_reason,
        limiting_gate=row.limiting_gate,
        observed_stability_score=row.observed_stability_score,
        observed_stable=row.observed_stable,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = run_stress(
        start_seed=args.start_seed,
        count=args.count,
        steps=args.steps,
        dt=args.dt,
        scenario_names=args.scenario,
        output_dir=args.out,
        make_plots=args.plots,
    )
    print("ZeroGateSim stress sweep complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Upload stress_bundle.zip when asking for review. This is the harder witness: same creature, rougher weather.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
