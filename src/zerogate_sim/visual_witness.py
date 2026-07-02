from __future__ import annotations

from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv

TRI_LEVELS = (-1, 0, 1)
TRI_LABELS = {-1: "minus", 0: "zero", 1: "plus"}
TRI_SHORT = {-1: "M", 0: "Z", 1: "P"}


def _float(row: dict[str, object], key: str) -> float:
    try:
        return float(row.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _int(row: dict[str, object], key: str) -> int:
    try:
        return int(float(row.get(key, 0)))
    except (TypeError, ValueError):
        return 0


def scenario_glyph(row: dict[str, object]) -> str:
    """Return a compact trinary glyph for one matrix scenario.

    v0.2.9 changes the witness layer from binary false-negative reading to
    trinary outcome reading. Held-latent pressure is a witness state, not a
    simple wound. Breach still overrides everything because false expression is
    the dangerous failure.
    """

    false_pos = _int(row, "false_positive_runs")
    designed_rejected = _int(row, "designed_rejected_runs")
    designed_quarantine = _int(row, "designed_quarantine_hold_runs")
    designed_witness = _int(row, "designed_witness_hold_runs")
    designed_fertile = _int(row, "designed_fertile_hold_runs")
    acc = _float(row, "mean_designed_accuracy")
    if false_pos > 0:
        return "✕"  # wrong admission: strongest danger
    if designed_rejected > 0:
        return "△"  # true conservative wound: designed stable rejected, not held
    if designed_quarantine > 0:
        return "◍"  # 0- quarantine: latent but unsafe
    if designed_witness > 0:
        return "◌"  # 0 witness: held and undecided
    if designed_fertile > 0:
        return "◎"  # 0+ fertile: near expression, not yet one
    if acc >= 0.999:
        return "●"  # clean expression boundary
    return "◐"  # mixed/edge pressure not otherwise classified

def _scenario_lookup(scenario_rows: list[dict[str, object]]) -> dict[tuple[int, int, int, str], dict[str, object]]:
    out: dict[tuple[int, int, int, str], dict[str, object]] = {}
    for row in scenario_rows:
        p = str(row.get("perturbation_axis", ""))
        if p.lower() == "nan":
            p = ""
        out[(int(row["noise_axis"]), int(row["relation_axis"]), int(row["expansion_axis"]), p)] = row
    return out


def _cell(row: dict[str, object] | None) -> str:
    if row is None:
        return ""
    glyph = scenario_glyph(row)
    acc = _float(row, "mean_designed_accuracy")
    fertile = _int(row, "designed_fertile_hold_runs")
    witness = _int(row, "designed_witness_hold_runs")
    quarantine = _int(row, "designed_quarantine_hold_runs")
    rejected = _int(row, "designed_rejected_runs")
    fp = _int(row, "false_positive_runs")
    if fp:
        return f"{glyph} acc={acc:.3f} FP={fp}"
    if rejected:
        return f"{glyph} acc={acc:.3f} -1={rejected}"
    if quarantine:
        return f"{glyph} acc={acc:.3f} 0-={quarantine}"
    if witness:
        return f"{glyph} acc={acc:.3f} 0={witness}"
    if fertile:
        return f"{glyph} acc={acc:.3f} 0+={fertile}"
    return f"{glyph} acc={acc:.3f}"


def _axis_pressure_notes(scenario_rows: list[dict[str, object]]) -> list[str]:
    notes: list[str] = []
    axes = ["noise_axis", "relation_axis", "expansion_axis", "perturbation_axis"]
    for axis in axes:
        rows = [row for row in scenario_rows if str(row.get(axis, "")) not in {"", "nan", "None"}]
        if not rows:
            continue
        grouped: list[tuple[int, int, int, float]] = []
        for level in TRI_LEVELS:
            level_rows = [row for row in rows if int(row[axis]) == level]
            if not level_rows:
                continue
            grouped.append(
                (
                    level,
                    sum(_int(row, "designed_fertile_hold_runs") + _int(row, "designed_witness_hold_runs") + _int(row, "designed_quarantine_hold_runs") for row in level_rows),
                    sum(_int(row, "designed_rejected_runs") for row in level_rows),
                    mean(_float(row, "mean_designed_accuracy") for row in level_rows),
                )
            )
        if not grouped:
            continue
        weakest = max(grouped, key=lambda item: (item[2], item[1], -item[3]))
        strongest = min(grouped, key=lambda item: (item[2], item[1], -item[3]))
        notes.append(
            f"- `{axis}`: strongest hold/reject pressure at `{TRI_LABELS[weakest[0]]}` "
            f"(0-holds {weakest[1]}, -1-rejections {weakest[2]}, mean accuracy {weakest[3]:.3f}); "
            f"cleanest support at `{TRI_LABELS[strongest[0]]}` "
            f"(0-holds {strongest[1]}, -1-rejections {strongest[2]}, mean accuracy {strongest[3]:.3f})."
        )
    return notes

def write_matrix_glyph_map(path: Path, scenario_rows: list[dict[str, object]], *, profile: str) -> None:
    lookup = _scenario_lookup(scenario_rows)
    perturbation_layers = sorted({key[3] for key in lookup})
    if perturbation_layers == [""]:
        perturbation_layers = [""]

    lines: list[str] = []
    lines.append("# ZeroGateSim Matrix Glyph Map")
    lines.append("")
    lines.append(f"Profile: `{profile}`")
    lines.append("")
    lines.append("This file is the visual witness for humans who hear geometry better than raw numbers. It does not replace the CSVs; it gives the matrix a shape.")
    lines.append("")
    lines.append("## Glyph legend")
    lines.append("")
    lines.append("- `●` clean: designed stable candidates earned +1 expression.")
    lines.append("- `◎` 0+ fertile hold: designed stable candidates are near expression, not yet one.")
    lines.append("- `◌` 0 witness hold: designed stable candidates are held for more pressure/return.")
    lines.append("- `◍` 0- quarantine hold: designed stable candidates fell into unsafe latent pressure.")
    lines.append("- `△` rejected: designed stable candidates fell to -1; this is the true conservative wound.")
    lines.append("- `✕` breach: false-positive pressure; this is more dangerous than a hold.")
    lines.append("- `◐` edge: mixed pressure that needs inspection.")
    lines.append("")
    lines.append("Rows are relation pressure. Columns are expansion pressure. Each panel is one noise layer. `M/Z/P` mean minus, zero, plus.")
    lines.append("")

    for p in perturbation_layers:
        if p != "":
            lines.append(f"## Perturbation layer `{TRI_LABELS[int(p)]}`")
            lines.append("")
        for noise in TRI_LEVELS:
            lines.append(f"### Noise `{TRI_LABELS[noise]}`")
            lines.append("")
            lines.append("| relation \\ expansion | M | Z | P |")
            lines.append("|---|---|---|---|")
            for relation in TRI_LEVELS:
                cells = []
                for expansion in TRI_LEVELS:
                    row = lookup.get((noise, relation, expansion, p))
                    cells.append(_cell(row))
                lines.append(f"| {TRI_LABELS[relation]} | {cells[0]} | {cells[1]} | {cells[2]} |")
            lines.append("")

    lines.append("## Shape read")
    lines.append("")
    lines.extend(_axis_pressure_notes(scenario_rows))
    lines.append("")
    lines.append("Witness translation: the glyph map shows where the field bends. `0+`, `0`, and `0-` are not the same hold. Fertile hold asks for retest, witness hold asks for more pressure, quarantine hold asks for caution before any theory repair.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _matrix_rows(scenario_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in scenario_rows:
        out.append(
            {
                "scenario": row["scenario"],
                "glyph": scenario_glyph(row),
                "noise_axis": row["noise_axis"],
                "relation_axis": row["relation_axis"],
                "expansion_axis": row["expansion_axis"],
                "perturbation_axis": row.get("perturbation_axis", ""),
                "mean_designed_accuracy": row["mean_designed_accuracy"],
                "false_positive_runs": row["false_positive_runs"],
                "false_negative_runs": row.get("false_negative_runs", 0),
                "designed_held_runs": row.get("designed_held_runs", 0),
                "designed_fertile_hold_runs": row.get("designed_fertile_hold_runs", 0),
                "designed_witness_hold_runs": row.get("designed_witness_hold_runs", 0),
                "designed_quarantine_hold_runs": row.get("designed_quarantine_hold_runs", 0),
                "designed_rejected_runs": row.get("designed_rejected_runs", 0),
                "expressed_sets": row["expressed_sets"],
                "z4_sets": row["z4_sets"],
            }
        )
    return out


def write_matrix_heatmaps(root_dir: Path, scenario_rows: list[dict[str, object]]) -> list[Path]:
    """Write one simple heatmap per noise/perturbation layer.

    The image is a witness surface, not a scientific proof. It is intentionally
    spare: relation by expansion, with accuracy as the field height and glyphs
    printed into cells.
    """

    root_dir = ensure_dir(root_dir)
    lookup = _scenario_lookup(scenario_rows)
    perturbation_layers = sorted({key[3] for key in lookup})
    if perturbation_layers == [""]:
        perturbation_layers = [""]
    paths: list[Path] = []
    for p in perturbation_layers:
        for noise in TRI_LEVELS:
            values = np.zeros((3, 3), dtype=float)
            labels: list[list[str]] = [["" for _ in TRI_LEVELS] for _ in TRI_LEVELS]
            for r_idx, relation in enumerate(TRI_LEVELS):
                for e_idx, expansion in enumerate(TRI_LEVELS):
                    row = lookup.get((noise, relation, expansion, p))
                    if row is None:
                        values[r_idx, e_idx] = np.nan
                        labels[r_idx][e_idx] = ""
                    else:
                        values[r_idx, e_idx] = _float(row, "mean_designed_accuracy")
                        labels[r_idx][e_idx] = (
                            f"{scenario_glyph(row)}\n"
                            f"0+ {_int(row, 'designed_fertile_hold_runs')} / "
                            f"0 {_int(row, 'designed_witness_hold_runs')} / "
                            f"0- {_int(row, 'designed_quarantine_hold_runs')}"
                        )
            fig, ax = plt.subplots(figsize=(5.8, 4.8))
            image = ax.imshow(values, vmin=0.0, vmax=1.0)
            ax.set_xticks(range(3), [TRI_LABELS[v] for v in TRI_LEVELS])
            ax.set_yticks(range(3), [TRI_LABELS[v] for v in TRI_LEVELS])
            ax.set_xlabel("expansion pressure")
            ax.set_ylabel("relation pressure")
            title = f"Noise {TRI_LABELS[noise]}"
            if p != "":
                title += f" / Perturbation {TRI_LABELS[int(p)]}"
            ax.set_title(title)
            for r_idx in range(3):
                for e_idx in range(3):
                    ax.text(e_idx, r_idx, labels[r_idx][e_idx], ha="center", va="center")
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="mean designed accuracy")
            fig.tight_layout()
            suffix = f"noise_{TRI_SHORT[noise]}"
            if p != "":
                suffix += f"_perturb_{TRI_SHORT[int(p)]}"
            path = root_dir / f"matrix_glyph_heatmap_{suffix}.png"
            fig.savefig(path, dpi=160)
            plt.close(fig)
            paths.append(path)
    return paths




def _shape_pressure_summary(scenario_rows: list[dict[str, object]]) -> dict[str, object]:
    false_pos = sum(_int(row, "false_positive_runs") for row in scenario_rows)
    false_neg = sum(_int(row, "false_negative_runs") for row in scenario_rows)
    designed_held = sum(_int(row, "designed_held_runs") for row in scenario_rows)
    designed_fertile = sum(_int(row, "designed_fertile_hold_runs") for row in scenario_rows)
    designed_witness = sum(_int(row, "designed_witness_hold_runs") for row in scenario_rows)
    designed_quarantine = sum(_int(row, "designed_quarantine_hold_runs") for row in scenario_rows)
    designed_rejected = sum(_int(row, "designed_rejected_runs") for row in scenario_rows)
    clean = sum(1 for row in scenario_rows if scenario_glyph(row) == "●")
    fertile = sum(1 for row in scenario_rows if scenario_glyph(row) == "◎")
    held = sum(1 for row in scenario_rows if scenario_glyph(row) == "◌")
    quarantine = sum(1 for row in scenario_rows if scenario_glyph(row) == "◍")
    edge = sum(1 for row in scenario_rows if scenario_glyph(row) == "◐")
    wounded = sum(1 for row in scenario_rows if scenario_glyph(row) == "△")
    breach = sum(1 for row in scenario_rows if scenario_glyph(row) == "✕")
    return {
        "false_pos": false_pos,
        "false_neg": false_neg,
        "designed_held": designed_held,
        "designed_fertile": designed_fertile,
        "designed_witness": designed_witness,
        "designed_quarantine": designed_quarantine,
        "designed_rejected": designed_rejected,
        "clean": clean,
        "fertile": fertile,
        "held": held,
        "quarantine": quarantine,
        "edge": edge,
        "wounded": wounded,
        "breach": breach,
        "total": len(scenario_rows),
    }


def _axis_outcome_totals(scenario_rows: list[dict[str, object]], axis: str) -> list[tuple[int, int, int, float]]:
    rows = [row for row in scenario_rows if str(row.get(axis, "")) not in {"", "nan", "None"}]
    out: list[tuple[int, int, int, float]] = []
    for level in TRI_LEVELS:
        level_rows = [row for row in rows if int(row[axis]) == level]
        if not level_rows:
            continue
        held = (
            sum(_int(row, "designed_fertile_hold_runs") for row in level_rows)
            + sum(_int(row, "designed_witness_hold_runs") for row in level_rows)
            + sum(_int(row, "designed_quarantine_hold_runs") for row in level_rows)
        )
        rejected = sum(_int(row, "designed_rejected_runs") for row in level_rows)
        acc = mean(_float(row, "mean_designed_accuracy") for row in level_rows)
        out.append((level, held, rejected, acc))
    return out

def write_matrix_shape_read(path: Path, scenario_rows: list[dict[str, object]], *, profile: str) -> None:
    """Write a speakable field reading for the matrix.

    This is intentionally not a decimal checklist. It is a trinary witness:
    what expands, what holds, what resists.
    """

    summary = _shape_pressure_summary(scenario_rows)
    relation = _axis_outcome_totals(scenario_rows, "relation_axis")
    expansion = _axis_outcome_totals(scenario_rows, "expansion_axis")
    noise = _axis_outcome_totals(scenario_rows, "noise_axis")
    perturb = _axis_outcome_totals(scenario_rows, "perturbation_axis")

    def line_for(axis_name: str, rows: list[tuple[int, int, int, float]]) -> str:
        if not rows:
            return f"`{axis_name}` is not active in this profile."
        worst = max(rows, key=lambda item: (item[2], item[1], -item[3]))
        best = min(rows, key=lambda item: (item[2], item[1], -item[3]))
        return (
            f"`{axis_name}` holds hardest at `{TRI_LABELS[worst[0]]}` "
            f"(0-holds {worst[1]}, -1-rejections {worst[2]}), and opens cleanest at "
            f"`{TRI_LABELS[best[0]]}` (0-holds {best[1]}, -1-rejections {best[2]})."
        )

    lines: list[str] = []
    lines.append("# ZeroGateSim Matrix Shape Read")
    lines.append("")
    lines.append(f"Profile: `{profile}`")
    lines.append("")
    lines.append("This is the speakable witness layer. The CSVs keep the bones; this file reads the posture of the field.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    if summary["false_pos"] == 0:
        lines.append("No breach appeared. The current gate did not admit wrong candidates anywhere in this matrix.")
    else:
        lines.append(f"Breach pressure appeared: {summary['false_pos']} false-positive scenario-runs. That would be the dangerous wound.")
    lines.append("")
    lines.append(
        f"The field produced {summary['clean']} clean scenarios, {summary['fertile']} fertile-hold scenarios, "
        f"{summary['held']} witness-hold scenarios, {summary['quarantine']} quarantine-hold scenarios, "
        f"{summary['edge']} edge scenarios, and {summary['wounded']} rejected/wounded scenarios "
        f"across {summary['total']} scenario cells."
    )
    lines.append("")
    lines.append("## Expand")
    lines.append("")
    lines.append(line_for("expansion_axis", expansion))
    lines.append("Expansion-minus is not a failure of the theory by itself. It means stable candidates may have coherence but not enough expressed strength to deserve one.")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append(line_for("relation_axis", relation))
    lines.append("Relation-plus is the clearest healing pressure. When binding strengthens, the field stops treating coherence as a private pulse and lets it become expression.")
    lines.append("")
    lines.append("## Resist")
    lines.append("")
    lines.append(line_for("noise_axis", noise))
    if perturb:
        lines.append(line_for("perturbation_axis", perturb))
    lines.append("Noise is not automatically the enemy. In this toy field, rougher weather can sometimes clarify the boundary instead of destroying it.")
    lines.append("")
    lines.append("## Shape verdict")
    lines.append("")
    lines.append("The current witness separates +1 expression, 0+ fertile hold, 0 witness hold, 0- quarantine hold, and -1 rejection. A 0-state hold is no longer one flat bucket. The real wound is either false expression or a designed stable candidate falling to -1; quarantine hold is warning weather, not verdict.")
    lines.append("")
    lines.append("That is the trinary repair. A held-back truth can return. A rejected designed stable candidate needs mechanism repair. A false expression can poison the field.")
    lines.append("")
    lines.append("Next pressure: inspect the distribution of 0+, 0, and 0-. Do not mutate the core gate until the zero-zone taxonomy has survived repeated matrix weather.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_matrix_field_atlas(root_dir: Path, scenario_rows: list[dict[str, object]], *, profile: str) -> Path:
    """Write one combined atlas image for the matrix geometry."""

    root_dir = ensure_dir(root_dir)
    lookup = _scenario_lookup(scenario_rows)
    perturbation_layers = sorted({key[3] for key in lookup})
    if perturbation_layers == [""]:
        perturbation_layers = [""]

    n_rows = len(perturbation_layers)
    n_cols = len(TRI_LEVELS)
    fig_width = 5.2 * n_cols
    fig_height = 4.8 * n_rows
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height), squeeze=False)

    for row_idx, p in enumerate(perturbation_layers):
        for col_idx, noise in enumerate(TRI_LEVELS):
            ax = axes[row_idx][col_idx]
            values = np.zeros((3, 3), dtype=float)
            labels: list[list[str]] = [["" for _ in TRI_LEVELS] for _ in TRI_LEVELS]
            for r_idx, relation in enumerate(TRI_LEVELS):
                for e_idx, expansion in enumerate(TRI_LEVELS):
                    row = lookup.get((noise, relation, expansion, p))
                    if row is None:
                        values[r_idx, e_idx] = np.nan
                        labels[r_idx][e_idx] = ""
                    else:
                        values[r_idx, e_idx] = _float(row, "mean_designed_accuracy")
                        labels[r_idx][e_idx] = (
                            f"{scenario_glyph(row)}\n"
                            f"0+ {_int(row, 'designed_fertile_hold_runs')} / "
                            f"0 {_int(row, 'designed_witness_hold_runs')} / "
                            f"0- {_int(row, 'designed_quarantine_hold_runs')}"
                        )
            image = ax.imshow(values, vmin=0.0, vmax=1.0)
            ax.set_xticks(range(3), [TRI_SHORT[v] for v in TRI_LEVELS])
            ax.set_yticks(range(3), [TRI_SHORT[v] for v in TRI_LEVELS])
            ax.set_xlabel("expansion")
            ax.set_ylabel("relation")
            title = f"noise {TRI_SHORT[noise]}"
            if p != "":
                title += f" / perturb {TRI_SHORT[int(p)]}"
            ax.set_title(title)
            for r_idx in range(3):
                for e_idx in range(3):
                    ax.text(e_idx, r_idx, labels[r_idx][e_idx], ha="center", va="center")
    fig.suptitle(f"ZeroGateSim field atlas: {profile}", y=0.995)
    fig.tight_layout()
    path = root_dir / "matrix_field_atlas.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path

def write_matrix_visual_witness(root_dir: Path, scenario_rows: list[dict[str, object]], *, profile: str) -> dict[str, Path | list[Path]]:
    root_dir = ensure_dir(root_dir)
    glyph_md = root_dir / "matrix_glyph_map.md"
    glyph_csv = root_dir / "matrix_glyph_map.csv"
    shape_md = root_dir / "matrix_shape_read.md"
    write_matrix_glyph_map(glyph_md, scenario_rows, profile=profile)
    write_dict_rows_csv(glyph_csv, _matrix_rows(scenario_rows))
    heatmaps = write_matrix_heatmaps(root_dir, scenario_rows)
    atlas = write_matrix_field_atlas(root_dir, scenario_rows, profile=profile)
    write_matrix_shape_read(shape_md, scenario_rows, profile=profile)
    return {
        "matrix_glyph_map": glyph_md,
        "matrix_glyph_csv": glyph_csv,
        "matrix_glyph_heatmaps": heatmaps,
        "matrix_field_atlas": atlas,
        "matrix_shape_read": shape_md,
    }
