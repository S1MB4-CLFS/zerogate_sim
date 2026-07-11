from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from zerogate_sim.v1_8_lineage_schema import validate_lineage_frames
from zerogate_sim.v1_8_2_threshold_contract import (
    THRESHOLD_BY_ID,
    THRESHOLD_OPTION_IDS,
    THRESHOLD_OPTIONS,
    EvaluationMathError,
    ThresholdOption,
    classify_score,
    threshold_option,
)

VERSION = "v1.8.2-alpha"

PRIMARY_MODEL_ID = "primary_prior_touch"
NO_PRIOR_TOUCH_MODEL_ID = "no_prior_touch_support"
NO_ECHO_GUARD_MODEL_ID = "no_echo_guard"

# The order is part of the deterministic pre-label registry surface. It follows
# the v1.8.1 method lock: primary, its two ablations, simple baselines, and then
# the three deliberately dead-safe constant controls.
CONTINUOUS_MODEL_IDS = (
    PRIMARY_MODEL_ID,
    NO_PRIOR_TOUCH_MODEL_ID,
    NO_ECHO_GUARD_MODEL_ID,
    "strength_only",
    "four_gate_minimum",
    "four_gate_mean",
    "return_only",
    "observed_stability_only",
    "echo_guarded_gate_minimum",
)
CONSTANT_MODEL_IDS = (
    "always_hold",
    "always_crown",
    "always_resist",
)
MODEL_IDS = CONTINUOUS_MODEL_IDS + CONSTANT_MODEL_IDS

CONSTANT_PREDICTIONS: Mapping[str, int] = MappingProxyType(
    {
        "always_hold": 0,
        "always_crown": 1,
        "always_resist": -1,
    }
)


def _frame_values(frames: object) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    return validate_lineage_frames(frames, source="v1.8.2 score registry")


def _primary_frame_score(frame: Mapping[str, float]) -> float:
    return min(
        frame["strength"],
        frame["distinction"],
        frame["polarity"],
        frame["relation"],
        frame["return_observed"],
        frame["observed_stability_score"],
        1.0 - frame["echo_mimic_score"],
    )


def _no_echo_frame_score(frame: Mapping[str, float]) -> float:
    return min(
        frame["strength"],
        frame["distinction"],
        frame["polarity"],
        frame["relation"],
        frame["return_observed"],
        frame["observed_stability_score"],
    )


def _prior_touch(values: tuple[float, float, float]) -> float:
    early, witness, late = values
    return min(late, max(early, witness))


def _continuous_scores(frames: object) -> dict[str, float]:
    early, witness, late = _frame_values(frames)
    ordered_frames = (early, witness, late)

    primary_frames = tuple(_primary_frame_score(frame) for frame in ordered_frames)
    no_echo_frames = tuple(_no_echo_frame_score(frame) for frame in ordered_frames)
    strength_frames = tuple(frame["strength"] for frame in ordered_frames)
    four_gate_minimum_frames = tuple(
        min(
            frame["distinction"],
            frame["polarity"],
            frame["relation"],
            frame["return_observed"],
        )
        for frame in ordered_frames
    )
    four_gate_mean_frames = tuple(
        (
            frame["distinction"]
            + frame["polarity"]
            + frame["relation"]
            + frame["return_observed"]
        )
        / 4.0
        for frame in ordered_frames
    )
    return_frames = tuple(frame["return_observed"] for frame in ordered_frames)
    stability_frames = tuple(frame["observed_stability_score"] for frame in ordered_frames)
    echo_guarded_gate_frames = tuple(
        min(
            frame["distinction"],
            frame["polarity"],
            frame["relation"],
            frame["return_observed"],
            1.0 - frame["echo_mimic_score"],
        )
        for frame in ordered_frames
    )

    scores = {
        PRIMARY_MODEL_ID: _prior_touch(primary_frames),
        NO_PRIOR_TOUCH_MODEL_ID: primary_frames[2],
        NO_ECHO_GUARD_MODEL_ID: _prior_touch(no_echo_frames),
        "strength_only": _prior_touch(strength_frames),
        "four_gate_minimum": _prior_touch(four_gate_minimum_frames),
        "four_gate_mean": _prior_touch(four_gate_mean_frames),
        "return_only": _prior_touch(return_frames),
        "observed_stability_only": _prior_touch(stability_frames),
        "echo_guarded_gate_minimum": _prior_touch(echo_guarded_gate_frames),
    }
    return {
        model_id: 0.0 if scores[model_id] == 0.0 else float(scores[model_id])
        for model_id in CONTINUOUS_MODEL_IDS
    }


def score_model(frames: object, model_id: str) -> float | int:
    """Score one locked model from observables alone.

    Even constant controls validate the exact three-frame observable callback,
    preventing an alternate identifier- or label-bearing scorer surface.
    """

    if type(model_id) is not str or model_id not in MODEL_IDS:
        raise EvaluationMathError(f"unknown locked model: {model_id!r}")
    scores = _continuous_scores(frames)
    if model_id in CONSTANT_PREDICTIONS:
        return CONSTANT_PREDICTIONS[model_id]
    return scores[model_id]


def score_registry_rows(frames: object) -> tuple[dict[str, object], ...]:
    """Return the nine continuous pre-label scores and nothing semantic."""

    scores = _continuous_scores(frames)
    return tuple(
        {"model_id": model_id, "score": scores[model_id]}
        for model_id in CONTINUOUS_MODEL_IDS
    )


def prediction_cube_rows(frames: object) -> tuple[dict[str, object], ...]:
    """Return all locked proposals without case identifiers, groups, or labels.

    Continuous models contribute one row for each of the three threshold
    options. Each constant control contributes exactly one ``constant`` row.
    """

    scores = _continuous_scores(frames)
    rows: list[dict[str, object]] = []
    for model_id in CONTINUOUS_MODEL_IDS:
        score = scores[model_id]
        for option in THRESHOLD_OPTIONS:
            rows.append(
                {
                    "model_id": model_id,
                    "option_id": option.option_id,
                    "score": score,
                    "proposed_trinary": classify_score(score, option),
                }
            )
    for model_id in CONSTANT_MODEL_IDS:
        rows.append(
            {
                "model_id": model_id,
                "option_id": "constant",
                "score": None,
                "proposed_trinary": CONSTANT_PREDICTIONS[model_id],
            }
        )
    return tuple(rows)
