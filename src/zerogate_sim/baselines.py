from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from zerogate_sim.gates import GateScores, clamp01


@dataclass(frozen=True)
class ModelComparison:
    model: str
    threshold: float
    truth_field: str
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int
    accuracy: float
    precision: float
    recall: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_div(num: int | float, den: int | float) -> float:
    return float(num / den) if den else 0.0


def _score_for_model(row: GateScores, model: str, rng: np.random.Generator) -> float:
    if model == "zero_gate_expression":
        # Full current expression operator: gate coherence plus strength boundary.
        # This is intentionally separate from zero_gate_min, which measures only
        # the four-gate minimum before the final strength cut.
        return row.zero_coherence if row.expressed else 0.0
    if model == "zero_gate_min":
        return row.zero_coherence
    if model == "amplitude_only":
        return row.strength
    if model == "polarity_only":
        return row.polarity
    if model == "relation_only":
        return row.relation
    if model == "return_only":
        return row.return_observed
    if model == "return_potential_dpr":
        return row.return_potential
    if model == "average_gate":
        return clamp01(
            (
                row.distinction
                + row.polarity
                + row.relation
                + row.return_observed
            )
            / 4.0
        )
    if model == "random_pressure":
        return float(rng.random())
    raise ValueError(f"Unknown baseline model: {model}")


def compare_models(
    rows: list[GateScores],
    *,
    threshold: float = 0.55,
    truth_field: str = "designed_stable",
    seed: int = 42,
) -> list[ModelComparison]:
    """Compare zero-gate prediction against baseline rules.

    `zero_gate_expression` uses the full current expression decision, including
    the strength boundary. `zero_gate_min` keeps the raw four-gate minimum visible
    so Z-depth/strength pressure cannot hide.

    `truth_field` may be `designed_stable` for generator labels or
    `observed_stable` for a fully signal-derived provisional target.
    """

    models = [
        "zero_gate_expression",
        "zero_gate_min",
        "amplitude_only",
        "polarity_only",
        "relation_only",
        "return_only",
        "return_potential_dpr",
        "average_gate",
        "random_pressure",
    ]
    rng = np.random.default_rng(seed)
    out: list[ModelComparison] = []

    truths = [bool(getattr(row, truth_field)) for row in rows]

    for model in models:
        tp = tn = fp = fn = 0
        for row, truth in zip(rows, truths):
            score = _score_for_model(row, model, rng)
            pred = score >= threshold
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
            elif not pred and truth:
                fn += 1
            else:
                tn += 1
        total = tp + tn + fp + fn
        out.append(
            ModelComparison(
                model=model,
                threshold=threshold,
                truth_field=truth_field,
                true_positive=tp,
                true_negative=tn,
                false_positive=fp,
                false_negative=fn,
                accuracy=_safe_div(tp + tn, total),
                precision=_safe_div(tp, tp + fp),
                recall=_safe_div(tp, tp + fn),
            )
        )
    return out
