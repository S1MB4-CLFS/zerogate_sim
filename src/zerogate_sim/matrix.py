from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean

import numpy as np

from zerogate_sim.baselines import ModelComparison, compare_models
from zerogate_sim.belnap_mirror import write_belnap_mirror_outputs
from zerogate_sim.batch import build_candidate_summary_rows
from zerogate_sim.config import SimulationConfig
from zerogate_sim.echo_independence import write_echo_independence_outputs
from zerogate_sim.earned_one import write_earned_one_outputs
from zerogate_sim.final_output import write_final_output_outputs
from zerogate_sim.fuzzy_mirror import write_fuzzy_mirror_outputs
from zerogate_sim.endurance import build_temporal_rows, write_temporal_outputs
from zerogate_sim.gates import GateScores, evaluate_run
from zerogate_sim.known_logic_closeout import write_known_logic_closeout_outputs
from zerogate_sim.lineage import write_lineage_outputs
from zerogate_sim.paraconsistent_mirror import write_paraconsistent_mirror_outputs
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle, write_run_outputs
from zerogate_sim.signals import CANDIDATE_PROFILES, CandidateSpec, SimulationRun, candidate_specs, default_candidate_specs, generate_pressure_field
from zerogate_sim.three_valued_mirror import write_three_valued_mirror_outputs
from zerogate_sim.truth_roles import write_truth_role_outputs
from zerogate_sim.visual_witness import write_matrix_visual_witness

TRINARY_VALUES = (-1, 0, 1)
TRINARY_LABELS = {-1: "minus", 0: "zero", 1: "plus"}
TRINARY_SHORT = {-1: "M", 0: "Z", 1: "P"}


@dataclass(frozen=True)
class TrinaryScenario:
    """One cell in a trinary stress matrix.

    The axes are not a decimal checklist. They are three-valued pressure controls.
    The triad profile is 3^3 = 27 scenarios. The deep profile adds perturbation
    as a fourth trinary axis for 3^4 = 81 scenarios.
    """

    name: str
    description: str
    noise_axis: int
    relation_axis: int
    expansion_axis: int
    perturbation_axis: int | None
    time_axis: int | None
    noise_factor: float
    noise_floor: float
    relation_factor: float
    stable_amplitude_factor: float
    late_noise_shock: float
    dt_factor: float = 1.0
    gate_threshold: float = 0.55
    strength_threshold: float = 0.40


def _axis_name(value: int) -> str:
    return TRINARY_LABELS[value]


def _scenario_name(*, n: int, r: int, e: int, p: int | None, t: int | None = None) -> str:
    base = f"n{TRINARY_SHORT[n]}_r{TRINARY_SHORT[r]}_e{TRINARY_SHORT[e]}"
    if p is not None:
        base = f"{base}_p{TRINARY_SHORT[p]}"
    if t is not None:
        base = f"{base}_t{TRINARY_SHORT[t]}"
    return base


def _scenario_description(s: TrinaryScenario) -> str:
    parts = [
        f"noise={_axis_name(s.noise_axis)}",
        f"relation={_axis_name(s.relation_axis)}",
        f"expression={_axis_name(s.expansion_axis)}",
    ]
    if s.perturbation_axis is not None:
        parts.append(f"perturbation={_axis_name(s.perturbation_axis)}")
    if s.time_axis is not None:
        parts.append(f"time={_axis_name(s.time_axis)}")
    return "; ".join(parts)


def _noise_params(axis: int) -> tuple[float, float]:
    # minus = calmer field, zero = baseline, plus = noisy field.
    if axis == -1:
        return 0.80, 0.10
    if axis == 0:
        return 1.00, 0.12
    return 1.85, 0.17


def _relation_factor(axis: int) -> float:
    # minus = weak binding, zero = baseline, plus = stronger binding.
    if axis == -1:
        return 0.42
    if axis == 0:
        return 1.00
    return 1.38


def _stable_amplitude_factor(axis: int) -> float:
    # minus = strength dip, zero = baseline, plus = expression boost.
    if axis == -1:
        return 0.72
    if axis == 0:
        return 1.00
    return 1.15


def _shock_strength(axis: int | None) -> float:
    # deep profile only: minus = calm, zero = mild late disturbance, plus = rough late disturbance.
    if axis is None or axis == -1:
        return 0.00
    if axis == 0:
        return 0.13
    return 0.24


def _dt_factor(axis: int | None) -> float:
    # wide profile only: minus = compressed temporal field, zero = baseline,
    # plus = stretched temporal field. This is a time-depth pressure, not a new
    # physical time claim. It asks whether posture survives fewer/more return
    # opportunities inside the same step budget.
    if axis is None or axis == 0:
        return 1.00
    if axis == -1:
        return 0.78
    return 1.32


def build_scenarios(profile: str = "triad27") -> list[TrinaryScenario]:
    """Build trinary matrix scenarios.

    `triad27` varies noise, relation, and expression pressure: 3^3.
    `deep81` adds perturbation pressure: 3^4.
    `wide243` adds temporal-depth pressure: 3^5.
    """

    if profile not in {"triad27", "deep81", "wide243"}:
        raise ValueError("profile must be 'triad27', 'deep81', or 'wide243'")

    if profile in {"deep81", "wide243"}:
        perturbation_values: tuple[int | None, ...] = (-1, 0, 1)
    else:
        perturbation_values = (None,)

    if profile == "wide243":
        time_values: tuple[int | None, ...] = (-1, 0, 1)
    else:
        time_values = (None,)

    out: list[TrinaryScenario] = []
    for n in TRINARY_VALUES:
        noise_factor, noise_floor = _noise_params(n)
        for r in TRINARY_VALUES:
            relation_factor = _relation_factor(r)
            for e in TRINARY_VALUES:
                stable_factor = _stable_amplitude_factor(e)
                for p in perturbation_values:
                    for t_axis in time_values:
                        scenario = TrinaryScenario(
                            name=_scenario_name(n=n, r=r, e=e, p=p, t=t_axis),
                            description="",  # filled below so the object fields are available.
                            noise_axis=n,
                            relation_axis=r,
                            expansion_axis=e,
                            perturbation_axis=p,
                            time_axis=t_axis,
                            noise_factor=noise_factor,
                            noise_floor=noise_floor,
                            relation_factor=relation_factor,
                            stable_amplitude_factor=stable_factor,
                            late_noise_shock=_shock_strength(p),
                            dt_factor=_dt_factor(t_axis),
                        )
                        scenario = replace(scenario, description=_scenario_description(scenario))
                        out.append(scenario)
    return out

def apply_spec_pressure(specs: list[CandidateSpec], scenario: TrinaryScenario) -> list[CandidateSpec]:
    """Apply trinary scenario pressure to candidate specs."""

    out: list[CandidateSpec] = []
    for spec in specs:
        amplitude = spec.amplitude
        if spec.designed_stable:
            amplitude *= scenario.stable_amplitude_factor
        out.append(
            replace(
                spec,
                amplitude=amplitude,
                noise=spec.noise * scenario.noise_factor,
                relation_weight=spec.relation_weight * scenario.relation_factor,
            )
        )
    return out


def apply_signal_pressure(run: SimulationRun, scenario: TrinaryScenario, seed: int) -> SimulationRun:
    """Apply late perturbation pressure when the deep matrix asks for it."""

    if scenario.late_noise_shock <= 0:
        return run
    rng = np.random.default_rng(seed + 300_000)
    signals = np.array(run.signals, copy=True)
    n = signals.shape[1]
    start = int(0.72 * n)
    ramp = np.linspace(0.0, 1.0, n - start)
    signals[:, start:] += scenario.late_noise_shock * ramp * rng.normal(0.0, 1.0, size=signals[:, start:].shape)
    metadata = dict(run.metadata)
    metadata["matrix_late_noise_shock"] = scenario.late_noise_shock
    return SimulationRun(t=run.t, signals=signals, specs=run.specs, seed=run.seed, metadata=metadata)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a trinary ZeroGateSim matrix sweep and write one uploadable evidence bundle."
    )
    parser.add_argument("--profile", choices=["triad27", "deep81", "wide243"], default="triad27", help="Trinary scenario profile.")
    parser.add_argument("--candidate-profile", choices=list(CANDIDATE_PROFILES), default="alpha12", help="Candidate corpus: alpha12, triad27, or adversarial proof corpora.")
    parser.add_argument("--start-seed", type=int, default=0, help="First seed in each scenario.")
    parser.add_argument("--count", type=int, default=9, help="Number of seeds per scenario. Default 9 keeps the first matrix at 27*9=243 runs.")
    parser.add_argument("--steps", type=int, default=600, help="Number of simulation steps per seed.")
    parser.add_argument("--dt", type=float, default=0.05, help="Time/order step size.")
    parser.add_argument("--out", type=Path, default=None, help="Matrix output directory.")
    parser.add_argument("--plots", action="store_true", help="Generate PNG plots for every matrix seed. Default is off.")
    return parser


def _best(rows: list[ModelComparison]) -> ModelComparison:
    return max(rows, key=lambda row: row.accuracy)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _join_ids(rows: list[GateScores], predicate) -> str:
    return ",".join(row.candidate_id for row in rows if predicate(row))


def _seed_row(
    *,
    scenario: TrinaryScenario,
    seed: int,
    rows: list[GateScores],
    comparisons_designed: list[ModelComparison],
    comparisons_observed: list[ModelComparison],
) -> dict[str, object]:
    best_designed = _best(comparisons_designed)
    best_observed = _best(comparisons_observed)
    return {
        "scenario": scenario.name,
        "seed": seed,
        "noise_axis": scenario.noise_axis,
        "relation_axis": scenario.relation_axis,
        "expansion_axis": scenario.expansion_axis,
        "perturbation_axis": "" if scenario.perturbation_axis is None else scenario.perturbation_axis,
        "time_axis": "" if scenario.time_axis is None else scenario.time_axis,
        "designed_ids": _join_ids(rows, lambda row: row.designed_stable),
        "expressed_ids": _join_ids(rows, lambda row: row.trinary_value == 1),
        "held_latent_ids": _join_ids(rows, lambda row: row.trinary_value == 0),
        "fertile_hold_ids": _join_ids(rows, lambda row: row.zero_band == "fertile_hold"),
        "witness_hold_ids": _join_ids(rows, lambda row: row.zero_band == "witness_hold"),
        "quarantine_hold_ids": _join_ids(rows, lambda row: row.zero_band == "quarantine_hold"),
        "rejected_ids": _join_ids(rows, lambda row: row.trinary_value == -1),
        "z4_ids": _join_ids(rows, lambda row: row.zero_depth == 4),
        "false_positive_ids": _join_ids(rows, lambda row: row.expressed and not row.designed_stable),
        "false_negative_ids": _join_ids(rows, lambda row: row.designed_stable and not row.expressed),
        "designed_held_ids": _join_ids(rows, lambda row: row.designed_stable and row.trinary_value == 0),
        "designed_fertile_hold_ids": _join_ids(rows, lambda row: row.designed_stable and row.zero_band == "fertile_hold"),
        "designed_witness_hold_ids": _join_ids(rows, lambda row: row.designed_stable and row.zero_band == "witness_hold"),
        "designed_quarantine_hold_ids": _join_ids(rows, lambda row: row.designed_stable and row.zero_band == "quarantine_hold"),
        "designed_rejected_ids": _join_ids(rows, lambda row: row.designed_stable and row.trinary_value == -1),
        "health_only_ids": _join_ids(rows, lambda row: row.observed_stable and not row.expressed),
        "best_designed_model": best_designed.model,
        "best_designed_accuracy": best_designed.accuracy,
        "best_designed_precision": best_designed.precision,
        "best_designed_recall": best_designed.recall,
        "best_signal_health_model": best_observed.model,
        "best_signal_health_accuracy": best_observed.accuracy,
        "best_signal_health_precision": best_observed.precision,
        "best_signal_health_recall": best_observed.recall,
    }


def _scenario_rows(seed_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for scenario in sorted({str(row["scenario"]) for row in seed_rows}):
        rows = [row for row in seed_rows if row["scenario"] == scenario]
        designed_held = [row for row in rows if str(row.get("designed_held_ids", ""))]
        designed_fertile = [row for row in rows if str(row.get("designed_fertile_hold_ids", ""))]
        designed_witness = [row for row in rows if str(row.get("designed_witness_hold_ids", ""))]
        designed_quarantine = [row for row in rows if str(row.get("designed_quarantine_hold_ids", ""))]
        designed_rejected = [row for row in rows if str(row.get("designed_rejected_ids", ""))]
        held_sets = sorted({str(row.get("held_latent_ids", "")) for row in rows})
        fertile_sets = sorted({str(row.get("fertile_hold_ids", "")) for row in rows})
        witness_sets = sorted({str(row.get("witness_hold_ids", "")) for row in rows})
        quarantine_sets = sorted({str(row.get("quarantine_hold_ids", "")) for row in rows})
        rejected_sets = sorted({str(row.get("rejected_ids", "")) for row in rows})
        out.append(
            {
                "scenario": scenario,
                "runs": len(rows),
                "noise_axis": rows[0]["noise_axis"],
                "relation_axis": rows[0]["relation_axis"],
                "expansion_axis": rows[0]["expansion_axis"],
                "perturbation_axis": rows[0]["perturbation_axis"],
                "time_axis": rows[0].get("time_axis", ""),
                "mean_designed_accuracy": _mean([float(row["best_designed_accuracy"]) for row in rows]),
                "mean_signal_health_accuracy": _mean([float(row["best_signal_health_accuracy"]) for row in rows]),
                "false_positive_runs": sum(1 for row in rows if str(row["false_positive_ids"])),
                "false_negative_runs": sum(1 for row in rows if str(row["false_negative_ids"])),
                "designed_held_runs": len(designed_held),
                "designed_fertile_hold_runs": len(designed_fertile),
                "designed_witness_hold_runs": len(designed_witness),
                "designed_quarantine_hold_runs": len(designed_quarantine),
                "designed_rejected_runs": len(designed_rejected),
                "expressed_sets": " | ".join(sorted({str(row["expressed_ids"]) for row in rows})),
                "held_sets": " | ".join(held_sets),
                "fertile_hold_sets": " | ".join(fertile_sets),
                "witness_hold_sets": " | ".join(witness_sets),
                "quarantine_hold_sets": " | ".join(quarantine_sets),
                "rejected_sets": " | ".join(rejected_sets),
                "z4_sets": " | ".join(sorted({str(row["z4_ids"]) for row in rows})),
                "best_designed_models": ";".join(
                    f"{model}:{sum(1 for row in rows if row['best_designed_model'] == model)}"
                    for model in sorted({str(row["best_designed_model"]) for row in rows})
                ),
            }
        )
    return out


def _axis_rows(scenario_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    axes = ["noise_axis", "relation_axis", "expansion_axis", "perturbation_axis", "time_axis"]
    for axis in axes:
        rows_with_axis = [row for row in scenario_rows if str(row.get(axis, "")) != ""]
        if not rows_with_axis:
            continue
        for level in sorted({int(row[axis]) for row in rows_with_axis}):
            rows = [row for row in rows_with_axis if int(row[axis]) == level]
            out.append(
                {
                    "axis": axis,
                    "level": level,
                    "level_name": TRINARY_LABELS[level],
                    "scenarios": len(rows),
                    "runs": sum(int(row["runs"]) for row in rows),
                    "mean_designed_accuracy": _mean([float(row["mean_designed_accuracy"]) for row in rows]),
                    "false_positive_runs": sum(int(row["false_positive_runs"]) for row in rows),
                    "false_negative_runs": sum(int(row["false_negative_runs"]) for row in rows),
                    "designed_held_runs": sum(int(row.get("designed_held_runs", 0)) for row in rows),
                    "designed_fertile_hold_runs": sum(int(row.get("designed_fertile_hold_runs", 0)) for row in rows),
                    "designed_witness_hold_runs": sum(int(row.get("designed_witness_hold_runs", 0)) for row in rows),
                    "designed_quarantine_hold_runs": sum(int(row.get("designed_quarantine_hold_runs", 0)) for row in rows),
                    "designed_rejected_runs": sum(int(row.get("designed_rejected_runs", 0)) for row in rows),
                }
            )
    return out


def _prefix_candidate_id(row: GateScores, scenario_name: str) -> GateScores:
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


def _write_matrix_summary(
    *,
    path: Path,
    profile: str,
    start_seed: int,
    count: int,
    candidate_profile: str,
    scenarios: list[TrinaryScenario],
    scenario_rows: list[dict[str, object]],
    axis_rows: list[dict[str, object]],
) -> None:
    total_runs = len(scenarios) * count
    false_pos = sum(int(row["false_positive_runs"]) for row in scenario_rows)
    false_neg = sum(int(row["false_negative_runs"]) for row in scenario_rows)
    designed_held = sum(int(row.get("designed_held_runs", 0)) for row in scenario_rows)
    designed_fertile = sum(int(row.get("designed_fertile_hold_runs", 0)) for row in scenario_rows)
    designed_witness = sum(int(row.get("designed_witness_hold_runs", 0)) for row in scenario_rows)
    designed_quarantine = sum(int(row.get("designed_quarantine_hold_runs", 0)) for row in scenario_rows)
    designed_rejected = sum(int(row.get("designed_rejected_runs", 0)) for row in scenario_rows)
    mean_acc = _mean([float(row["mean_designed_accuracy"]) for row in scenario_rows])

    lines: list[str] = []
    lines.append("# ZeroGateSim Trinary Matrix Summary")
    lines.append("")
    lines.append(f"Profile: `{profile}`")
    lines.append(f"Scenarios: `{len(scenarios)}`")
    lines.append(f"Candidate profile: `{candidate_profile}`")
    lines.append(f"Seeds per scenario: `{start_seed}` through `{start_seed + count - 1}`")
    lines.append(f"Total runs: `{total_runs}`")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a trinary combination sweep. It does not prove physics. It asks whether the current zero-gate expression rule survives a structured pressure matrix instead of one friendly or hand-picked stress path.")
    lines.append("")
    lines.append("## Witness verdict")
    lines.append("")
    lines.append(f"Mean designed-label accuracy across scenarios: `{mean_acc:.3f}`")
    lines.append(f"False-positive scenario-runs: `{false_pos}`")
    lines.append(f"Designed held-latent scenario-runs: `{designed_held}`")
    lines.append(f"Designed 0+ fertile-hold presence-runs: `{designed_fertile}`")
    lines.append(f"Designed 0 witness-hold presence-runs: `{designed_witness}`")
    lines.append(f"Designed 0- quarantine-hold presence-runs: `{designed_quarantine}`")
    lines.append("")
    lines.append("Zero-band presence-runs can overlap: one seed/scenario can contain one designed candidate in 0+ and another in 0-. This is not a sum-of-parts scoreboard; it is a zero-zone posture map.")
    lines.append(f"Designed rejected scenario-runs: `{designed_rejected}`")
    lines.append(f"Binary false-negative scenario-runs retained for trace: `{false_neg}`")
    lines.append("")
    lines.append("## Trinary axes")
    lines.append("")
    lines.append("- `noise_axis`: minus=calmer field, zero=baseline field, plus=noisy field")
    lines.append("- `relation_axis`: minus=weaker binding, zero=baseline binding, plus=stronger binding")
    lines.append("- `expansion_axis`: minus=stable-freedom strength dip, zero=baseline strength, plus=stable-freedom boost")
    if profile in {"deep81", "wide243"}:
        lines.append("- `perturbation_axis`: minus=calm late field, zero=mild late shock, plus=rough late shock")
    if profile == "wide243":
        lines.append("- `time_axis`: minus=compressed temporal field, zero=baseline temporal field, plus=stretched temporal field")
    lines.append("")
    lines.append("## Axis-level witness")
    lines.append("")
    lines.append("| axis | level | scenarios | runs | mean designed accuracy | breach | designed 0+ | designed 0 | designed 0- | designed -1 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in axis_rows:
        lines.append(
            f"| {row['axis']} | {row['level_name']} | {row['scenarios']} | {row['runs']} | "
            f"{float(row['mean_designed_accuracy']):.3f} | {row['false_positive_runs']} | "
            f"{row.get('designed_fertile_hold_runs', 0)} | {row.get('designed_witness_hold_runs', 0)} | "
            f"{row.get('designed_quarantine_hold_runs', 0)} | {row.get('designed_rejected_runs', 0)} |"
        )
    lines.append("")
    lines.append("## How to read the CSVs")
    lines.append("")
    lines.append("`matrix_final_output_read.md` is the primary crown witness: raw expression is pressure, earned-one is final +1. `matrix_theory_confirmation_read.md` states whether the toy-domain software theory is confirmed in this run. `matrix_scenario_summary.csv` is the scenario-level map. `matrix_seed_summary.csv` is the seed-level trace. `matrix_candidate_summary.csv` is the pressure table for each scenario/candidate pair. `matrix_axis_summary.csv` is the trinary witness view. `matrix_glyph_map.md` is the human geometry view, `matrix_shape_read.md` is the speakable field reading, `matrix_field_atlas.png` is the one-image atlas, and `matrix_temporal_read.md` is the test-of-time witness. `matrix_lineage_read.md` reads how early/witness/late postures move instead of flattening time into final posture. `matrix_truth_role_read.md` repairs the candidate truth layer, `matrix_echo_mimic_report.md` focuses on signal echo pressure, and `matrix_echo_independence_read.md` checks whether expression survives relation-weather changes or depends only on relation-plus. `matrix_fuzzy_mirror_read.md`, `matrix_belnap_mirror_read.md`, `matrix_paraconsistent_mirror_read.md`, and `matrix_three_valued_mirror_read.md` are projection mirrors for known-logic comparison; they are not native truth engines. `matrix_known_logic_closeout_read.md` summarizes what each mirror preserves, exposes, and collapses before the v1.3 line closes.")
    lines.append("")
    lines.append("## Witness note")
    lines.append("")
    lines.append("Mechanism-boundary: this matrix varies toy generator pressures, not physical reality.")
    lines.append("")
    lines.append("Integration-modularity: use this before changing gates. If a region fails, inspect that region first; do not rewrite the engine from one dramatic wound.")
    lines.append("")
    lines.append("Witness-translation: upload `matrix_bundle.zip` for review. It contains the summaries, per-run evidence, and manifest. No breadcrumb salad.")
    lines.append("")
    lines.append("Overdo risk: a clean trinary matrix is still not cosmic confirmation. The primate may admire the grid; it may not crown it reality.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_matrix(
    *,
    profile: str = "triad27",
    candidate_profile: str = "alpha12",
    start_seed: int = 0,
    count: int = 9,
    steps: int = 600,
    dt: float = 0.05,
    output_dir: Path | None = None,
    make_plots: bool = False,
) -> dict[str, Path]:
    if count <= 0:
        raise ValueError("count must be positive")

    scenarios = build_scenarios(profile)
    matrix_dir = ensure_dir(output_dir or Path(f"runs/matrix_{profile}_{start_seed}_{start_seed + count - 1}"))

    seed_rows: list[dict[str, object]] = []
    all_gate_rows: list[tuple[int, GateScores]] = []
    temporal_rows: list[dict[str, object]] = []

    progress_step = max(1, len(scenarios) // 27)
    for scenario_index, scenario in enumerate(scenarios):
        if scenario_index == 0 or (scenario_index + 1) % progress_step == 0 or scenario_index == len(scenarios) - 1:
            print(f"[matrix] scenario {scenario_index + 1}/{len(scenarios)}: {scenario.name}", flush=True)
        specs = apply_spec_pressure(candidate_specs(candidate_profile), scenario)
        for seed in range(start_seed, start_seed + count):
            run_dir = matrix_dir / scenario.name / f"seed_{seed}"
            config = SimulationConfig(
                seed=seed,
                n_steps=steps,
                dt=dt * scenario.dt_factor,
                noise_floor=scenario.noise_floor,
                gate_threshold=scenario.gate_threshold,
                strength_threshold=scenario.strength_threshold,
                output_dir=run_dir,
            )
            run = generate_pressure_field(seed=seed, n_steps=steps, dt=dt * scenario.dt_factor, specs=specs)
            run = apply_signal_pressure(run, scenario, seed)
            metadata = dict(run.metadata)
            metadata["matrix_profile"] = profile
            metadata["matrix_scenario"] = scenario.name
            metadata["matrix_candidate_profile"] = candidate_profile
            metadata["matrix_dt_factor"] = scenario.dt_factor
            metadata["matrix_description"] = scenario.description
            metadata["matrix_axes"] = {
                "noise_axis": scenario.noise_axis,
                "relation_axis": scenario.relation_axis,
                "expansion_axis": scenario.expansion_axis,
                "perturbation_axis": scenario.perturbation_axis,
                "time_axis": scenario.time_axis,
            }
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
                make_bundle=False,
            )
            seed_rows.append(
                _seed_row(
                    scenario=scenario,
                    seed=seed,
                    rows=rows,
                    comparisons_designed=comparisons_designed,
                    comparisons_observed=comparisons_observed,
                )
            )
            temporal_rows.extend(
                build_temporal_rows(
                    run=run,
                    scenario=scenario.name,
                    seed=seed,
                    noise_axis=scenario.noise_axis,
                    relation_axis=scenario.relation_axis,
                    expansion_axis=scenario.expansion_axis,
                    perturbation_axis=scenario.perturbation_axis,
                    time_axis=scenario.time_axis,
                    noise_floor=scenario.noise_floor,
                    gate_threshold=scenario.gate_threshold,
                    strength_threshold=scenario.strength_threshold,
                )
            )
            synthetic_seed = scenario_index * 1_000_000 + seed
            all_gate_rows.extend((synthetic_seed, _prefix_candidate_id(row, scenario.name)) for row in rows)

    scenario_rows = _scenario_rows(seed_rows)
    axis_rows = _axis_rows(scenario_rows)
    candidate_rows = build_candidate_summary_rows(all_gate_rows)

    seed_csv = matrix_dir / "matrix_seed_summary.csv"
    scenario_csv = matrix_dir / "matrix_scenario_summary.csv"
    axis_csv = matrix_dir / "matrix_axis_summary.csv"
    candidate_csv = matrix_dir / "matrix_candidate_summary.csv"
    summary_md = matrix_dir / "matrix_summary.md"
    write_dict_rows_csv(seed_csv, seed_rows)
    write_dict_rows_csv(scenario_csv, scenario_rows)
    write_dict_rows_csv(axis_csv, axis_rows)
    write_dict_rows_csv(candidate_csv, candidate_rows)
    _write_matrix_summary(
        path=summary_md,
        profile=profile,
        start_seed=start_seed,
        count=count,
        candidate_profile=candidate_profile,
        scenarios=scenarios,
        scenario_rows=scenario_rows,
        axis_rows=axis_rows,
    )
    visual_paths = write_matrix_visual_witness(matrix_dir, scenario_rows, profile=profile)
    temporal_paths = write_temporal_outputs(matrix_dir, temporal_rows)
    lineage_paths = write_lineage_outputs(matrix_dir, temporal_rows)
    truth_role_paths = write_truth_role_outputs(matrix_dir, all_gate_rows)
    echo_independence_paths = write_echo_independence_outputs(matrix_dir, all_gate_rows)
    earned_one_paths = write_earned_one_outputs(matrix_dir, all_gate_rows)
    final_output_paths = write_final_output_outputs(matrix_dir, all_gate_rows)
    fuzzy_mirror_paths = write_fuzzy_mirror_outputs(matrix_dir, all_gate_rows)
    belnap_mirror_paths = write_belnap_mirror_outputs(matrix_dir, gate_rows=all_gate_rows)
    paraconsistent_mirror_paths = write_paraconsistent_mirror_outputs(matrix_dir, gate_rows=all_gate_rows)
    three_valued_mirror_paths = write_three_valued_mirror_outputs(matrix_dir, gate_rows=all_gate_rows)
    known_logic_closeout_paths = write_known_logic_closeout_outputs(matrix_dir, all_gate_rows)
    bundle = write_evidence_bundle(
        matrix_dir,
        bundle_name="matrix_bundle.zip",
        bundle_kind="zerogate_trinary_matrix_evidence_bundle",
    )
    return {
        "matrix_summary": summary_md,
        "matrix_seed_summary": seed_csv,
        "matrix_scenario_summary": scenario_csv,
        "matrix_axis_summary": axis_csv,
        "matrix_candidate_summary": candidate_csv,
        "matrix_glyph_map": visual_paths["matrix_glyph_map"],
        "matrix_glyph_csv": visual_paths["matrix_glyph_csv"],
        "matrix_shape_read": visual_paths["matrix_shape_read"],
        "matrix_field_atlas": visual_paths["matrix_field_atlas"],
        "matrix_temporal_trace": temporal_paths["matrix_temporal_trace"],
        "matrix_temporal_scenario_summary": temporal_paths["matrix_temporal_scenario_summary"],
        "matrix_temporal_candidate_summary": temporal_paths["matrix_temporal_candidate_summary"],
        "matrix_temporal_read": temporal_paths["matrix_temporal_read"],
        "matrix_lineage_transitions": lineage_paths["matrix_lineage_transitions"],
        "matrix_lineage_candidate_summary": lineage_paths["matrix_lineage_candidate_summary"],
        "matrix_lineage_read": lineage_paths["matrix_lineage_read"],
        "matrix_truth_role_candidate_summary": truth_role_paths["matrix_truth_role_candidate_summary"],
        "matrix_truth_role_summary": truth_role_paths["matrix_truth_role_summary"],
        "matrix_truth_role_read": truth_role_paths["matrix_truth_role_read"],
        "matrix_echo_mimic_report": truth_role_paths["matrix_echo_mimic_report"],
        "matrix_echo_independence_summary": echo_independence_paths["matrix_echo_independence_summary"],
        "matrix_echo_independence_read": echo_independence_paths["matrix_echo_independence_read"],
        "matrix_earned_one_summary": earned_one_paths["matrix_earned_one_summary"],
        "matrix_earned_one_read": earned_one_paths["matrix_earned_one_read"],
        "matrix_final_output_summary": final_output_paths["matrix_final_output_summary"],
        "matrix_final_output_read": final_output_paths["matrix_final_output_read"],
        "matrix_theory_confirmation_read": final_output_paths["matrix_theory_confirmation_read"],
        "matrix_fuzzy_mirror_trace": fuzzy_mirror_paths["matrix_fuzzy_mirror_trace"],
        "matrix_fuzzy_mirror_candidate_summary": fuzzy_mirror_paths["matrix_fuzzy_mirror_candidate_summary"],
        "matrix_fuzzy_mirror_read": fuzzy_mirror_paths["matrix_fuzzy_mirror_read"],
        "matrix_belnap_mirror_summary": belnap_mirror_paths["matrix_belnap_mirror_summary"],
        "matrix_belnap_mirror_read": belnap_mirror_paths["matrix_belnap_mirror_read"],
        "matrix_paraconsistent_mirror_summary": paraconsistent_mirror_paths["matrix_paraconsistent_mirror_summary"],
        "matrix_paraconsistent_mirror_read": paraconsistent_mirror_paths["matrix_paraconsistent_mirror_read"],
        "matrix_three_valued_mirror_summary": three_valued_mirror_paths["matrix_three_valued_mirror_summary"],
        "matrix_three_valued_mirror_read": three_valued_mirror_paths["matrix_three_valued_mirror_read"],
        "matrix_known_logic_closeout_summary": known_logic_closeout_paths["matrix_known_logic_closeout_summary"],
        "matrix_known_logic_closeout_read": known_logic_closeout_paths["matrix_known_logic_closeout_read"],
        "matrix_bundle": bundle,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = run_matrix(
        profile=args.profile,
        candidate_profile=args.candidate_profile,
        start_seed=args.start_seed,
        count=args.count,
        steps=args.steps,
        dt=args.dt,
        output_dir=args.out,
        make_plots=args.plots,
    )
    print("ZeroGateSim trinary matrix complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Upload matrix_bundle.zip when asking for review. This is the wider trinary weather map, not a decimal checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
