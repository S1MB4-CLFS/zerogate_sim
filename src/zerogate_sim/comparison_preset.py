from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

from zerogate_sim import __version__
from zerogate_sim.reporting import ensure_dir


@dataclass(frozen=True)
class MatrixPresetRun:
    """One planned matrix run in a cross-logic comparison preset.

    The preset layer writes commands only. It does not execute matrix runs. This
    keeps stronger comparison design separate from expensive simulation work and
    avoids pretending a preset is already evidence.
    """

    run_id: str
    gate: str
    profile: str
    candidate_profile: str
    start_seed: int
    count: int
    steps: int
    description: str


NATIVE_GATE_NAMES = ("distinction", "polarity", "relation", "return")
FOUR_GATE_ADVERSARY_PRESETS = ("adversary_triad27", "wide_adversary_probe")


PRESET_RUNS: dict[str, tuple[MatrixPresetRun, ...]] = {
    "quick_smoke": (
        MatrixPresetRun(
            run_id="quick_alpha12",
            gate="general",
            profile="triad27",
            candidate_profile="alpha12",
            start_seed=0,
            count=1,
            steps=90,
            description="Small baseline matrix for command smoke and report wiring.",
        ),
    ),
    "adversary_triad27": (
        MatrixPresetRun(
            run_id="distinction_triad27",
            gate="distinction",
            profile="triad27",
            candidate_profile="adversary_distinction",
            start_seed=0,
            count=3,
            steps=180,
            description="Distinction-theater pressure with a small trinary matrix.",
        ),
        MatrixPresetRun(
            run_id="polarity_triad27",
            gate="polarity",
            profile="triad27",
            candidate_profile="adversary_polarity",
            start_seed=0,
            count=3,
            steps=180,
            description="Polarity-theater pressure with a small trinary matrix.",
        ),
        MatrixPresetRun(
            run_id="relation_triad27",
            gate="relation",
            profile="triad27",
            candidate_profile="adversary_relation",
            start_seed=0,
            count=3,
            steps=180,
            description="Relation-echo pressure with a small trinary matrix.",
        ),
        MatrixPresetRun(
            run_id="return_triad27",
            gate="return",
            profile="triad27",
            candidate_profile="adversary_return",
            start_seed=0,
            count=3,
            steps=180,
            description="Observed-return pressure with a small trinary matrix.",
        ),
    ),
    "wide_adversary_probe": (
        MatrixPresetRun(
            run_id="distinction_wide243",
            gate="distinction",
            profile="wide243",
            candidate_profile="adversary_distinction",
            start_seed=0,
            count=3,
            steps=240,
            description="Wide weather distinction-adversary probe. Heavier than triad27.",
        ),
        MatrixPresetRun(
            run_id="polarity_wide243",
            gate="polarity",
            profile="wide243",
            candidate_profile="adversary_polarity",
            start_seed=0,
            count=3,
            steps=240,
            description="Wide weather polarity-adversary probe. Heavier than triad27.",
        ),
        MatrixPresetRun(
            run_id="relation_wide243",
            gate="relation",
            profile="wide243",
            candidate_profile="adversary_relation",
            start_seed=0,
            count=3,
            steps=240,
            description="Wide weather relation-adversary probe. Heavier than triad27.",
        ),
        MatrixPresetRun(
            run_id="return_wide243",
            gate="return",
            profile="wide243",
            candidate_profile="adversary_return",
            start_seed=0,
            count=3,
            steps=240,
            description="Wide weather observed-return adversary probe. Heavier than triad27.",
        ),
    ),
}


def preset_names() -> list[str]:
    return sorted(PRESET_RUNS)


def preset_gate_coverage(preset: str) -> tuple[str, ...]:
    """Return the native gate names explicitly covered by a preset."""

    if preset not in PRESET_RUNS:
        raise ValueError(f"Unknown preset {preset!r}. Choose one of: {', '.join(preset_names())}")
    return tuple(sorted({run.gate for run in PRESET_RUNS[preset] if run.gate in NATIVE_GATE_NAMES}))


def missing_native_gates(preset: str) -> tuple[str, ...]:
    coverage = set(preset_gate_coverage(preset))
    return tuple(gate for gate in NATIVE_GATE_NAMES if gate not in coverage)


def assert_four_gate_coverage(preset: str) -> None:
    """Fail if a four-gate adversary preset does not cover every native gate."""

    if preset not in FOUR_GATE_ADVERSARY_PRESETS:
        return
    missing = missing_native_gates(preset)
    if missing:
        raise ValueError(f"Preset {preset!r} is missing native gate coverage: {', '.join(missing)}")



def build_preset_runs(
    preset: str,
    *,
    start_seed: int | None = None,
    count: int | None = None,
    steps: int | None = None,
) -> list[MatrixPresetRun]:
    """Return planned runs for a named preset with optional safe overrides."""

    if preset not in PRESET_RUNS:
        raise ValueError(f"Unknown preset {preset!r}. Choose one of: {', '.join(preset_names())}")
    assert_four_gate_coverage(preset)
    runs = list(PRESET_RUNS[preset])
    if start_seed is None and count is None and steps is None:
        return runs
    out: list[MatrixPresetRun] = []
    for run in runs:
        out.append(
            replace(
                run,
                start_seed=run.start_seed if start_seed is None else start_seed,
                count=run.count if count is None else count,
                steps=run.steps if steps is None else steps,
            )
        )
    return out


def _ps_path(path: Path) -> str:
    return str(path).replace("/", "\\")


def matrix_output_dir(base_dir: Path, preset: str, run: MatrixPresetRun) -> Path:
    return Path(base_dir) / preset / run.run_id


def report_output_dir(base_dir: Path, preset: str) -> Path:
    return Path(base_dir) / preset / "cross_logic_report"


def build_matrix_command(run: MatrixPresetRun, output_dir: Path) -> str:
    return (
        f"& $P -m zerogate_sim.matrix --profile {run.profile} "
        f"--candidate-profile {run.candidate_profile} --start-seed {run.start_seed} "
        f"--count {run.count} --steps {run.steps} --out {_ps_path(output_dir)}"
    )


def build_report_command(matrix_dirs: Iterable[Path], output_dir: Path) -> str:
    matrix_args = " ".join(f"--matrix-dir {_ps_path(path)}" for path in matrix_dirs)
    return f"& $P -m zerogate_sim.cross_logic_report {matrix_args} --out {_ps_path(output_dir)}"


def _version_label() -> str:
    return __version__ if __version__.startswith("v") else f"v{__version__}"


def handoff_output_dir(preset: str, *, version: str | None = None) -> Path:
    label = version or _version_label()
    safe_label = label.replace("-", "_").replace(".", "_")
    return Path("runs") / f"assistant_test_handoff_{safe_label}_{preset}"


def handoff_zip_path(preset: str, *, version: str | None = None) -> Path:
    return handoff_output_dir(preset, version=version) / "assistant_test_handoff.zip"


def build_handoff_command(preset: str, report_dir: Path, *, version: str | None = None) -> str:
    label = version or _version_label()
    read_path = report_dir / "cross_logic_comparison_read.md"
    out_dir = handoff_output_dir(preset, version=label)
    return (
        f"& $P -m zerogate_sim.test_handoff --version {label} --status passed "
        f"--note \"{preset} preset completed locally\" "
        f"--include {_ps_path(read_path)} --out {_ps_path(out_dir)}"
    )


def build_powershell_lines(preset: str, runs: list[MatrixPresetRun], *, base_dir: Path) -> list[str]:
    matrix_dirs = [matrix_output_dir(base_dir, preset, run) for run in runs]
    report_dir = report_output_dir(base_dir, preset)
    lines = [
        '$ErrorActionPreference = "Stop"',
        "",
        "Set-Location C:\\dev\\zerogate_sim",
        '$P = ".\\.venv\\Scripts\\python.exe"',
        'if (!(Test-Path $P)) { throw "Python venv not found: $P" }',
        '$env:PYTHONPATH = (Join-Path (Get-Location) "src")',
        "",
    ]
    for run, out_dir in zip(runs, matrix_dirs):
        lines.append(f'Write-Host "`n=== matrix {run.run_id} ===" -ForegroundColor Cyan')
        lines.append(build_matrix_command(run, out_dir))
        lines.append("")
    report_read = report_dir / "cross_logic_comparison_read.md"
    handoff_zip = handoff_zip_path(preset)

    lines.append('Write-Host "`n=== cross logic report ===" -ForegroundColor Cyan')
    lines.append(build_report_command(matrix_dirs, report_dir))
    lines.append(f'$Report = "{_ps_path(report_read)}"')
    lines.append('if (!(Test-Path $Report)) { throw "Expected cross-logic report missing: $Report" }')
    lines.append('Write-Host "`nCross-logic report:" -ForegroundColor Green')
    lines.append('Write-Host (Join-Path (Get-Location) $Report)')
    lines.append('Get-Content $Report -TotalCount 120')
    lines.append("")
    lines.append('Write-Host "`n=== assistant handoff ===" -ForegroundColor Cyan')
    lines.append(build_handoff_command(preset, report_dir))
    lines.append(f'$HandoffZip = "{_ps_path(handoff_zip)}"')
    lines.append('if (!(Test-Path $HandoffZip)) { throw "Expected assistant handoff ZIP missing: $HandoffZip" }')
    lines.append('Write-Host "`nPreset complete. Upload this ZIP:" -ForegroundColor Green')
    lines.append('Write-Host (Join-Path (Get-Location) $HandoffZip)')
    return lines


def build_manifest_rows(preset: str, runs: list[MatrixPresetRun], *, base_dir: Path) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for run in runs:
        out.append(
            {
                "preset": preset,
                "run_id": run.run_id,
                "gate": run.gate,
                "profile": run.profile,
                "candidate_profile": run.candidate_profile,
                "start_seed": run.start_seed,
                "count": run.count,
                "steps": run.steps,
                "matrix_output_dir": _ps_path(matrix_output_dir(base_dir, preset, run)),
                "description": run.description,
            }
        )
    return out


def write_manifest_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_preset_read(path: Path, *, preset: str, runs: list[MatrixPresetRun], base_dir: Path) -> None:
    report_dir = report_output_dir(base_dir, preset)
    lines: list[str] = []
    lines.append("# ZeroGateSim Cross-Logic Comparison Preset")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a run-plan preset, not evidence by itself. It writes commands for completed matrix runs and a cross-logic comparison report. The preset does not mutate the native gate and does not claim identity with any external logic.")
    lines.append("")
    lines.append("## Preset")
    lines.append("")
    lines.append(f"Preset: `{preset}`")
    lines.append(f"Planned matrix runs: `{len(runs)}`")
    lines.append(f"Report output: `{_ps_path(report_dir)}`")
    lines.append("")
    lines.append("## Planned runs")
    lines.append("")
    lines.append("| run | native gate | profile | candidate profile | seeds | steps | output | purpose |")
    lines.append("|---|---|---|---|---:|---:|---|---|")
    for run in runs:
        out_dir = matrix_output_dir(base_dir, preset, run)
        seed_range = f"{run.start_seed}-{run.start_seed + run.count - 1}"
        lines.append(
            f"| {run.run_id} | {run.gate} | {run.profile} | {run.candidate_profile} | {seed_range} | {run.steps} | `{_ps_path(out_dir)}` | {run.description} |"
        )
    lines.append("")
    lines.append("## How to use")
    lines.append("")
    lines.append("Run the generated `run_preset.ps1` from the repo root after local tests are green. Generated run folders and handoff ZIPs are local artifacts and must not be committed.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    lines.append("The preset helps compare mirrors across stronger toy-field pressure. It is not a proof of physical dimensional genesis and not borrowed authority from known logic.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_preset(
    *,
    preset: str,
    output_dir: Path,
    base_dir: Path = Path("runs/cross_logic_presets"),
    start_seed: int | None = None,
    count: int | None = None,
    steps: int | None = None,
) -> dict[str, Path]:
    runs = build_preset_runs(preset, start_seed=start_seed, count=count, steps=steps)
    output_dir = ensure_dir(output_dir)
    read_path = output_dir / "comparison_preset_read.md"
    manifest_path = output_dir / "comparison_preset_manifest.csv"
    commands_path = output_dir / "run_preset.ps1"

    write_preset_read(read_path, preset=preset, runs=runs, base_dir=base_dir)
    write_manifest_csv(manifest_path, build_manifest_rows(preset, runs, base_dir=base_dir))
    commands_path.write_text("\n".join(build_powershell_lines(preset, runs, base_dir=base_dir)) + "\n", encoding="utf-8")

    return {
        "comparison_preset_read": read_path,
        "comparison_preset_manifest": manifest_path,
        "comparison_preset_commands": commands_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a cross-logic comparison run preset without executing it.")
    parser.add_argument("--preset", choices=preset_names(), default="adversary_triad27")
    parser.add_argument("--out", type=Path, default=Path("runs/comparison_preset_plan"))
    parser.add_argument("--base-dir", type=Path, default=Path("runs/cross_logic_presets"))
    parser.add_argument("--start-seed", type=int, default=None, help="Override start seed for every run in the preset.")
    parser.add_argument("--count", type=int, default=None, help="Override seed count for every run in the preset.")
    parser.add_argument("--steps", type=int, default=None, help="Override step count for every run in the preset.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = write_comparison_preset(
        preset=args.preset,
        output_dir=args.out,
        base_dir=args.base_dir,
        start_seed=args.start_seed,
        count=args.count,
        steps=args.steps,
    )
    print("ZeroGateSim cross-logic comparison preset written.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    print("")
    print("Read run_preset.ps1 before execution. A preset is a run plan, not evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
