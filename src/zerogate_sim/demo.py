from __future__ import annotations

import argparse
from pathlib import Path

from zerogate_sim.baselines import compare_models
from zerogate_sim.config import SimulationConfig
from zerogate_sim.gates import evaluate_run
from zerogate_sim.reporting import write_run_outputs
from zerogate_sim.signals import generate_pressure_field


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the ZeroGateSim alpha demo: generate pressure fields, score gates, and write reports."
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible toy field generation.")
    parser.add_argument("--steps", type=int, default=600, help="Number of simulation steps.")
    parser.add_argument("--dt", type=float, default=0.05, help="Time/order step size.")
    parser.add_argument("--noise-floor", type=float, default=0.12, help="Noise floor used by the first-pass distinction gate.")
    parser.add_argument("--gate-threshold", type=float, default=0.55, help="Gate threshold for zero-depth and expression.")
    parser.add_argument("--strength-threshold", type=float, default=0.40, help="Minimum normalized strength for earned expression.")
    parser.add_argument("--out", type=Path, default=None, help="Output directory for run artifacts.")
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG plot generation.")
    parser.add_argument("--no-bundle", action="store_true", help="Skip creation of run_bundle.zip evidence package.")
    return parser


def run_demo(config: SimulationConfig, *, make_plots: bool = True, make_bundle: bool = True) -> dict[str, Path]:
    run = generate_pressure_field(seed=config.seed, n_steps=config.n_steps, dt=config.dt)
    rows = evaluate_run(
        run,
        noise_floor=config.noise_floor,
        gate_threshold=config.gate_threshold,
        strength_threshold=config.strength_threshold,
    )
    comparisons_designed = compare_models(
        rows,
        threshold=config.gate_threshold,
        truth_field="designed_stable",
        seed=config.seed,
    )
    comparisons_observed = compare_models(
        rows,
        threshold=config.gate_threshold,
        truth_field="observed_stable",
        seed=config.seed + 1,
    )
    return write_run_outputs(
        run=run,
        config=config,
        rows=rows,
        comparisons_designed=comparisons_designed,
        comparisons_observed=comparisons_observed,
        make_plots=make_plots,
        make_bundle=make_bundle,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = args.out or Path(f"runs/demo_seed_{args.seed}")
    config = SimulationConfig(
        seed=args.seed,
        n_steps=args.steps,
        dt=args.dt,
        noise_floor=args.noise_floor,
        gate_threshold=args.gate_threshold,
        strength_threshold=args.strength_threshold,
        output_dir=output_dir,
    )
    paths = run_demo(config, make_plots=not args.no_plots, make_bundle=not args.no_bundle)

    print("ZeroGateSim demo complete.")
    print(f"Seed: {config.seed}")
    print(f"Output directory: {config.output_dir}")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Open summary.md first. Upload run_bundle.zip when asking for review. The primate may inspect the PNGs after the witness has read the table.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
