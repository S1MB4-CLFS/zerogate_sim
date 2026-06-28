from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

from zerogate_sim.baselines import ModelComparison
from zerogate_sim.config import SimulationConfig
from zerogate_sim.gates import GateScores
from zerogate_sim.signals import SimulationRun


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_dict_rows_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_signals(run: SimulationRun, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    offset = 0.0
    for idx, spec in enumerate(run.specs):
        signal = run.signals[idx]
        ax.plot(run.t, signal + offset, linewidth=1.0, label=f"{spec.candidate_id} {spec.kind}")
        offset += 2.6
    ax.axhline(0.0, linewidth=0.8)
    ax.set_title("ZeroGateSim candidate pressure signals")
    ax.set_xlabel("time/order t")
    ax.set_ylabel("pressure + visual offset")
    ax.legend(loc="upper right", fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_gate_scores(rows: list[GateScores], path: Path) -> None:
    labels = [row.candidate_id for row in rows]
    x = np.arange(len(labels))
    width = 0.16
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - 2 * width, [row.distinction for row in rows], width, label="distinction")
    ax.bar(x - width, [row.polarity for row in rows], width, label="polarity")
    ax.bar(x, [row.relation for row in rows], width, label="relation")
    ax.bar(x + width, [row.return_observed for row in rows], width, label="return")
    ax.bar(x + 2 * width, [row.zero_coherence for row in rows], width, label="C_Z min")
    ax.set_title("Gate scores by candidate freedom")
    ax.set_xlabel("candidate")
    ax.set_ylabel("score 0..1")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _best_model(rows: list[ModelComparison]) -> ModelComparison:
    return max(rows, key=lambda item: item.accuracy)


def build_summary_markdown(
    *,
    run: SimulationRun,
    config: SimulationConfig,
    rows: list[GateScores],
    comparisons_designed: list[ModelComparison],
    comparisons_observed: list[ModelComparison],
) -> str:
    expressed = [row for row in rows if row.trinary_value == 1]
    held_latent = [row for row in rows if row.trinary_value == 0]
    rejected = [row for row in rows if row.trinary_value == -1]
    deepest = sorted(rows, key=lambda row: row.zero_depth, reverse=True)[:5]
    best_designed = _best_model(comparisons_designed)
    best_observed = _best_model(comparisons_observed)

    lines: list[str] = []
    lines.append("# ZeroGateSim Demo Summary")
    lines.append("")
    lines.append(f"Seed: `{run.seed}`")
    lines.append(f"Steps: `{config.n_steps}`")
    lines.append(f"dt: `{config.dt}`")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a toy simulation run. It does not prove cosmology, physics, or trinary logic. It only tests whether the current zero-gate operator has useful predictive shape inside this generated field.")
    lines.append("")
    lines.append("## Expressed candidates")
    lines.append("")
    if expressed:
        for row in expressed:
            lines.append(f"- `{row.candidate_id}` `{row.kind}` — C_Z={_fmt(row.zero_coherence)}, zero_depth=Z^{row.zero_depth}, limiting_gate={row.limiting_gate}")
    else:
        lines.append("No candidates crossed the current expression threshold.")
    lines.append("")
    lines.append("## Trinary outcome")
    lines.append("")
    lines.append(f"+1 expressed: `{','.join(row.candidate_id for row in expressed) or 'none'}`")
    lines.append(f"0 held-latent: `{','.join(row.candidate_id for row in held_latent) or 'none'}`")
    lines.append(f"-1 rejected: `{','.join(row.candidate_id for row in rejected) or 'none'}`")
    lines.append("")
    lines.append("Held-latent is not a victory and not a failure. It means the candidate showed credible zero-structure or return-potential, but did not deserve to be counted as one.")
    lines.append("")
    lines.append("## Deepest zero-depth candidates")
    lines.append("")
    for row in deepest:
        lines.append(
            f"- `{row.candidate_id}` `{row.kind}` — Z^{row.zero_depth}, "
            f"D={_fmt(row.distinction)}, P={_fmt(row.polarity)}, R={_fmt(row.relation)}, "
            f"B={_fmt(row.return_observed)}, Gamma={_fmt(row.return_potential)}, C_Z={_fmt(row.zero_coherence)}"
        )
    lines.append("")
    lines.append("## Baseline comparison")
    lines.append("")
    lines.append(f"Best model against designed-stable labels: `{best_designed.model}` accuracy={_fmt(best_designed.accuracy)} precision={_fmt(best_designed.precision)} recall={_fmt(best_designed.recall)}")
    lines.append(f"Best model against observed-stable signal score: `{best_observed.model}` accuracy={_fmt(best_observed.accuracy)} precision={_fmt(best_observed.precision)} recall={_fmt(best_observed.recall)}")
    lines.append("")
    lines.append("## Evidence bundle")
    lines.append("")
    lines.append("This run writes `run_bundle.zip` beside the summary. Send that ZIP when asking for review; it includes the summary, CSVs, metadata, plots when generated, and a manifest. The witness should not have to hunt crumbs across the floor like an underpaid primate.")
    lines.append("")
    lines.append("## Gate table")
    lines.append("")
    lines.append("| candidate | kind | strength | D | P | R | return | Gamma | C_Z | Z-depth | outcome | zero-band | reason | limiting gate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|")
    for row in rows:
        lines.append(
            f"| {row.candidate_id} | {row.kind} | {_fmt(row.strength)} | {_fmt(row.distinction)} | "
            f"{_fmt(row.polarity)} | {_fmt(row.relation)} | {_fmt(row.return_observed)} | "
            f"{_fmt(row.return_potential)} | {_fmt(row.zero_coherence)} | Z^{row.zero_depth} | "
            f"{row.trinary_value}:{row.trinary_outcome} | {row.zero_band_symbol}:{row.zero_band} | "
            f"{row.zero_band_reason} / {row.outcome_reason} | {row.limiting_gate} |"
        )
    lines.append("")
    lines.append("## DREED-style witness note")
    lines.append("")
    lines.append("Mechanism-boundary: the run measures toy signal properties, not physical dimensions.")
    lines.append("")
    lines.append("Integration-modularity: this result belongs in local simulation evidence, not in the theory paper as proof.")
    lines.append("")
    lines.append("Witness-translation: if the run is useful, the justified claim is only that the current zero-gate operator can be compared against baseline emergence rules.")
    lines.append("")
    lines.append("Overdo risk: treating a friendly toy run as cosmic confirmation. The primate may celebrate, but it may not notarize reality.")
    lines.append("")
    return "\n".join(lines)


def _relative_files_for_bundle(root_dir: Path, *, exclude_zip: bool = True) -> list[Path]:
    files: list[Path] = []
    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if exclude_zip and path.suffix.lower() == ".zip":
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root_dir).as_posix())


def write_evidence_bundle(
    root_dir: Path,
    *,
    bundle_name: str = "run_bundle.zip",
    bundle_kind: str = "zerogate_run_evidence_bundle",
) -> Path:
    """Write a review-ready ZIP containing all non-ZIP files under `root_dir`.

    This is intentionally small and boring. Every run should produce one thing the
    human can upload back into chat: summary, metadata, tables, plots, and a
    manifest. No breadcrumb hunting. No screenshot archaeology unless the graph
    itself is the point.
    """

    root_dir = ensure_dir(root_dir)
    manifest_path = root_dir / "bundle_manifest.json"
    bundle_path = root_dir / bundle_name

    files_before_manifest = _relative_files_for_bundle(root_dir)
    manifest = {
        "bundle_kind": bundle_kind,
        "root_dir": str(root_dir),
        "bundle_name": bundle_name,
        "file_count_excluding_manifest": len(files_before_manifest),
        "files": [
            {
                "path": path.relative_to(root_dir).as_posix(),
                "size_bytes": path.stat().st_size,
            }
            for path in files_before_manifest
            if path != manifest_path
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    files = _relative_files_for_bundle(root_dir)
    if bundle_path.exists():
        bundle_path.unlink()
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            if path == bundle_path:
                continue
            zf.write(path, arcname=path.relative_to(root_dir).as_posix())
    return bundle_path


def write_run_outputs(
    *,
    run: SimulationRun,
    config: SimulationConfig,
    rows: list[GateScores],
    comparisons_designed: list[ModelComparison],
    comparisons_observed: list[ModelComparison],
    make_plots: bool = True,
    make_bundle: bool = True,
) -> dict[str, Path]:
    out_dir = ensure_dir(config.output_dir)
    gate_csv = out_dir / "gate_scores.csv"
    designed_csv = out_dir / "model_comparison_designed.csv"
    observed_csv = out_dir / "model_comparison_observed.csv"
    metadata_json = out_dir / "metadata.json"
    summary_md = out_dir / "summary.md"
    signals_png = out_dir / "signals.png"
    gates_png = out_dir / "gate_scores.png"

    write_dict_rows_csv(gate_csv, [row.to_dict() for row in rows])
    write_dict_rows_csv(designed_csv, [row.to_dict() for row in comparisons_designed])
    write_dict_rows_csv(observed_csv, [row.to_dict() for row in comparisons_observed])

    metadata = {
        "config": config.to_dict(),
        "run": run.metadata,
        "candidate_specs": [spec.__dict__ for spec in run.specs],
    }
    metadata_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    summary_md.write_text(
        build_summary_markdown(
            run=run,
            config=config,
            rows=rows,
            comparisons_designed=comparisons_designed,
            comparisons_observed=comparisons_observed,
        ),
        encoding="utf-8",
    )

    paths = {
        "summary": summary_md,
        "gate_scores": gate_csv,
        "comparison_designed": designed_csv,
        "comparison_observed": observed_csv,
        "metadata": metadata_json,
    }

    if make_plots:
        plot_signals(run, signals_png)
        plot_gate_scores(rows, gates_png)
        paths["signals_plot"] = signals_png
        paths["gate_plot"] = gates_png

    if make_bundle:
        paths["evidence_bundle"] = write_evidence_bundle(out_dir)

    return paths
