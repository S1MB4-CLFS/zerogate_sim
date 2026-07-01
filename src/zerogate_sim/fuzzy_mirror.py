from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable, Iterator, Sequence

from zerogate_sim.gates import GateScores
from zerogate_sim.reporting import write_dict_rows_csv

ETA = 1e-9
GATE_NAMES = ("distinction", "polarity", "relation", "return")


def clamp01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def fuzzy_min(values: Sequence[float]) -> float:
    return clamp01(min(float(v) for v in values)) if values else 0.0


def fuzzy_product(values: Sequence[float]) -> float:
    out = 1.0
    for value in values:
        out *= clamp01(float(value))
    return clamp01(out)


def fuzzy_average(values: Sequence[float]) -> float:
    return clamp01(mean(float(v) for v in values)) if values else 0.0


def fuzzy_lukasiewicz(values: Sequence[float]) -> float:
    """N-ary Lukasiewicz-style conjunction over [0, 1].

    This is a comparison mirror only. ZeroGateSim's native rule remains the
    weakest-gate minimum C_Z = min(D, P, R, B).
    """

    if not values:
        return 0.0
    return clamp01(sum(clamp01(float(v)) for v in values) - (len(values) - 1))


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _threshold_band(value: float, *, threshold: float) -> str:
    if value >= threshold:
        return "passes_threshold"
    if value >= 0.75 * threshold:
        return "near_threshold"
    return "below_threshold"


def _as_gate_values(row: GateScores) -> tuple[float, float, float, float]:
    return (
        float(row.distinction),
        float(row.polarity),
        float(row.relation),
        float(row.return_observed),
    )


def _iter_gate_rows(gate_rows: Iterable[tuple[int, GateScores] | GateScores]) -> Iterator[tuple[str, GateScores]]:
    for item in gate_rows:
        if isinstance(item, tuple) and len(item) == 2:
            seed, row = item
            yield str(seed), row
        else:
            yield "", item  # type: ignore[misc]


def build_fuzzy_mirror_rows(
    gate_rows: Iterable[tuple[int, GateScores] | GateScores],
    *,
    threshold: float = 0.55,
) -> list[dict[str, object]]:
    """Project gate scores into fuzzy/many-valued comparison mirrors.

    This does not replace the native zero-gate law. It compares the native
    weakest-gate rule against alternative continuous conjunction mirrors:
    product, average, and Lukasiewicz-style conjunction.
    """

    rows: list[dict[str, object]] = []
    for seed, row in _iter_gate_rows(gate_rows):
        gates = _as_gate_values(row)
        native_min = fuzzy_min(gates)
        product_gate = fuzzy_product(gates)
        average_gate = fuzzy_average(gates)
        lukasiewicz_gate = fuzzy_lukasiewicz(gates)
        strength_min_native = fuzzy_min((float(row.strength), native_min))
        average_overcrown = average_gate >= threshold and native_min < threshold
        product_stricter = product_gate < native_min - ETA
        rows.append(
            {
                "seed": seed,
                "candidate_id": row.candidate_id,
                "kind": row.kind,
                "truth_role": row.truth_role,
                "strength": row.strength,
                "distinction": row.distinction,
                "polarity": row.polarity,
                "relation": row.relation,
                "return_observed": row.return_observed,
                "native_min_gate": native_min,
                "stored_zero_coherence": row.zero_coherence,
                "product_gate": product_gate,
                "average_gate": average_gate,
                "lukasiewicz_gate": lukasiewicz_gate,
                "strength_min_native": strength_min_native,
                "average_minus_native": average_gate - native_min,
                "native_minus_product": native_min - product_gate,
                "average_overcrown_pressure": int(average_overcrown),
                "product_stricter_than_native": int(product_stricter),
                "native_band": _threshold_band(native_min, threshold=threshold),
                "product_band": _threshold_band(product_gate, threshold=threshold),
                "average_band": _threshold_band(average_gate, threshold=threshold),
                "lukasiewicz_band": _threshold_band(lukasiewicz_gate, threshold=threshold),
                "limiting_gate": row.limiting_gate,
                "native_trinary_value": row.trinary_value,
                "native_zero_band": row.zero_band,
                "native_zero_band_symbol": row.zero_band_symbol,
            }
        )
    return rows


def build_fuzzy_candidate_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["candidate_id"])].append(row)

    out: list[dict[str, object]] = []
    for candidate_id in sorted(grouped):
        subset = grouped[candidate_id]
        first = subset[0]
        limiting = Counter(str(row["limiting_gate"]) for row in subset)
        out.append(
            {
                "candidate_id": candidate_id,
                "kind": first["kind"],
                "truth_role": first["truth_role"],
                "runs": len(subset),
                "mean_native_min_gate": _mean([float(row["native_min_gate"]) for row in subset]),
                "mean_product_gate": _mean([float(row["product_gate"]) for row in subset]),
                "mean_average_gate": _mean([float(row["average_gate"]) for row in subset]),
                "mean_lukasiewicz_gate": _mean([float(row["lukasiewicz_gate"]) for row in subset]),
                "mean_average_minus_native": _mean([float(row["average_minus_native"]) for row in subset]),
                "mean_native_minus_product": _mean([float(row["native_minus_product"]) for row in subset]),
                "average_overcrown_pressure_count": sum(int(row["average_overcrown_pressure"]) for row in subset),
                "product_stricter_count": sum(int(row["product_stricter_than_native"]) for row in subset),
                "native_threshold_pass_count": sum(1 for row in subset if row["native_band"] == "passes_threshold"),
                "average_threshold_pass_count": sum(1 for row in subset if row["average_band"] == "passes_threshold"),
                "product_threshold_pass_count": sum(1 for row in subset if row["product_band"] == "passes_threshold"),
                "lukasiewicz_threshold_pass_count": sum(1 for row in subset if row["lukasiewicz_band"] == "passes_threshold"),
                "dominant_limiting_gate": limiting.most_common(1)[0][0] if limiting else "",
                "dominant_limiting_gate_count": limiting.most_common(1)[0][1] if limiting else 0,
            }
        )
    return out


def _write_fuzzy_read(path: Path, *, trace_rows: list[dict[str, object]], candidate_rows: list[dict[str, object]], threshold: float) -> None:
    total = len(trace_rows)
    avg_overcrown = sum(int(row["average_overcrown_pressure"]) for row in trace_rows)
    product_strict = sum(int(row["product_stricter_than_native"]) for row in trace_rows)
    native_pass = sum(1 for row in trace_rows if row["native_band"] == "passes_threshold")
    average_pass = sum(1 for row in trace_rows if row["average_band"] == "passes_threshold")
    product_pass = sum(1 for row in trace_rows if row["product_band"] == "passes_threshold")
    lukasiewicz_pass = sum(1 for row in trace_rows if row["lukasiewicz_band"] == "passes_threshold")

    ranked = sorted(
        candidate_rows,
        key=lambda row: (
            -int(row["average_overcrown_pressure_count"]),
            -float(row["mean_average_minus_native"]),
            str(row["candidate_id"]),
        ),
    )

    lines: list[str] = []
    lines.append("# ZeroGateSim Fuzzy / Many-Valued Mirror")
    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("This is a projection mirror, not an identity claim. ZeroGateSim is not fuzzy logic. The native rule remains weakest-gate coherence: `C_Z = min(D, P, R, B)`. This report compares that native rule against other continuous conjunction mirrors so the model can see what is preserved, softened, or distorted.")
    lines.append("")
    lines.append("## Mirror posture")
    lines.append("")
    lines.append(f"Rows read: `{total}`")
    lines.append(f"Threshold used for mirror bands: `{threshold:.3f}`")
    lines.append("")
    lines.append("## Native min versus fuzzy mirrors")
    lines.append("")
    lines.append(f"Native min threshold passes: `{native_pass}`")
    lines.append(f"Product mirror threshold passes: `{product_pass}`")
    lines.append(f"Average mirror threshold passes: `{average_pass}`")
    lines.append(f"Lukasiewicz mirror threshold passes: `{lukasiewicz_pass}`")
    lines.append("")
    lines.append(f"Average-overcrown pressure events: `{avg_overcrown}`")
    lines.append(f"Product stricter-than-native events: `{product_strict}`")
    lines.append("")
    lines.append("Average-overcrown pressure means the average of the four gates crosses threshold while the native weakest gate does not. These are the exact cases where a softer fuzzy-style aggregation can hide the missing gate that ZeroGateSim refuses to ignore.")
    lines.append("")
    lines.append("Product stricter-than-native means all gates may be present but multiplicative conjunction punishes distributed weakness more sharply than the native minimum. This is useful pressure, not a replacement rule.")
    lines.append("")
    lines.append("## Candidate summary")
    lines.append("")
    lines.append("| candidate | kind | role | runs | mean min | mean product | mean average | mean Lukasiewicz | avg-overcrown | product-strict | dominant limiter |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in ranked:
        lines.append(
            f"| {row['candidate_id']} | {row['kind']} | {row['truth_role']} | {row['runs']} | "
            f"{float(row['mean_native_min_gate']):.3f} | {float(row['mean_product_gate']):.3f} | "
            f"{float(row['mean_average_gate']):.3f} | {float(row['mean_lukasiewicz_gate']):.3f} | "
            f"{row['average_overcrown_pressure_count']} | {row['product_stricter_count']} | {row['dominant_limiting_gate']} |"
        )
    lines.append("")
    lines.append("## Loss report")
    lines.append("")
    lines.append("The fuzzy mirror sees continuous degrees. It does not see the full earned-one witness stack by itself: return-depth, temporal lineage, echo-independence, and truth-role witness remain native ZeroGateSim layers. A high fuzzy score is therefore pressure, not final +1.")
    lines.append("")
    lines.append("## Witness sentence")
    lines.append("")
    if avg_overcrown:
        lines.append("Resist: the average mirror produced overcrown pressure. This supports the native weakest-gate rule because the softer mirror can make a candidate look better by averaging away a wounded gate.")
    else:
        lines.append("Witness: no average-overcrown pressure appeared in this run. That does not prove equivalence; it only means this field did not expose a min-versus-average wound.")
    lines.append("")
    lines.append("A fuzzy mirror can grade pressure. It cannot crown earned-one without the rest of the ZeroGate witness stack.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_fuzzy_mirror_outputs(
    output_dir: Path,
    gate_rows: Iterable[tuple[int, GateScores] | GateScores],
    *,
    threshold: float = 0.55,
) -> dict[str, Path]:
    trace_rows = build_fuzzy_mirror_rows(gate_rows, threshold=threshold)
    candidate_rows = build_fuzzy_candidate_summary_rows(trace_rows)
    trace_csv = output_dir / "matrix_fuzzy_mirror_trace.csv"
    candidate_csv = output_dir / "matrix_fuzzy_mirror_candidate_summary.csv"
    read_md = output_dir / "matrix_fuzzy_mirror_read.md"
    write_dict_rows_csv(trace_csv, trace_rows)
    write_dict_rows_csv(candidate_csv, candidate_rows)
    _write_fuzzy_read(read_md, trace_rows=trace_rows, candidate_rows=candidate_rows, threshold=threshold)
    return {
        "matrix_fuzzy_mirror_trace": trace_csv,
        "matrix_fuzzy_mirror_candidate_summary": candidate_csv,
        "matrix_fuzzy_mirror_read": read_md,
    }
