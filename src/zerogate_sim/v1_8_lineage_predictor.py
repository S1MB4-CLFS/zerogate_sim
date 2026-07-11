from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from zerogate_sim.v1_8_lineage_schema import (
    FRAME_NAMES,
    OBSERVABLE_FIELDS,
    SCHEMA_ID,
    VERSION,
    LineageFrames,
    validate_lineage_frames,
    validate_observable_frame,
)

PREDICTOR_ID = "zerogate-v1.8.1-two-touch-lineage-v1"
# Keep the stable machine identifier because it is already bound by the
# development-plan lock. The human-facing name below states the narrower and
# exact semantics: this is prior-touch support, not continuous persistence.
FORMULA_ID = "owned-pressure-min__prior-support-max__late-support-min-v1"
FORMULA_NAME = "prior-touch temporal support"
DORMANT_REAPPEARANCE_BEHAVIOR = (
    "allowed: an early touch can support late reappearance across a lower witness frame"
)


@dataclass(frozen=True, slots=True)
class LineageScore:
    early_owned_pressure: float
    witness_owned_pressure: float
    late_owned_pressure: float
    lineage_support: float
    lineage_score: float
    no_lineage_score: float
    lineage_delta: float

    def to_dict(self) -> dict[str, float]:
        return {
            "early_owned_pressure": self.early_owned_pressure,
            "witness_owned_pressure": self.witness_owned_pressure,
            "late_owned_pressure": self.late_owned_pressure,
            "lineage_support": self.lineage_support,
            "lineage_score": self.lineage_score,
            "no_lineage_score": self.no_lineage_score,
            "lineage_delta": self.lineage_delta,
        }


def owned_pressure(frame: Mapping[str, object]) -> float:
    """Compute observable-owned pressure for one temporal frame.

    This continuous quantity contains no decision boundary. Echo pressure enters
    only through its observable complement, so high borrowed coherence can lower
    rather than strengthen the score.
    """

    values = validate_observable_frame(frame, source="predictor frame")
    score = min(
        values["strength"],
        values["distinction"],
        values["polarity"],
        values["relation"],
        values["return_observed"],
        values["observed_stability_score"],
        1.0 - values["echo_mimic_score"],
    )
    return 0.0 if score == 0.0 else float(score)


def score_lineage_frames(frames: LineageFrames | object) -> LineageScore:
    """Score exact early/witness/late observables without assigning a class.

    The control is prior-touch temporal support: late owned pressure is capped by
    the stronger of the early and witness touches. It is intentionally not a
    continuity rule. A strong early touch, lower witness frame, and strong late
    frame is treated as dormant reappearance and may retain the early support.
    The ablation removes only the prior-touch term.
    """

    early, witness, late = validate_lineage_frames(frames, source="predictor callback")
    early_owned = owned_pressure(early)
    witness_owned = owned_pressure(witness)
    late_owned = owned_pressure(late)
    support = max(early_owned, witness_owned)
    control = min(late_owned, support)
    ablation = late_owned
    delta = max(0.0, ablation - control)
    return LineageScore(
        early_owned_pressure=early_owned,
        witness_owned_pressure=witness_owned,
        late_owned_pressure=late_owned,
        lineage_support=support,
        lineage_score=control,
        no_lineage_score=ablation,
        lineage_delta=delta,
    )


def lineage_predictor(frames: LineageFrames) -> LineageScore:
    """Callback entry point for immutable three-frame observable tuples."""

    if type(frames) is not tuple or len(frames) != 3 or any(
        type(frame) is not MappingProxyType for frame in frames
    ):
        raise TypeError(
            "lineage_predictor requires the immutable tuple returned by "
            "immutable_lineage_frames"
        )
    return score_lineage_frames(frames)


def predictor_config_document() -> dict[str, object]:
    """Return the exact inspectable configuration bound into the package."""

    return {
        "version": VERSION,
        "predictor_id": PREDICTOR_ID,
        "formula_id": FORMULA_ID,
        "formula_name": FORMULA_NAME,
        "formula_description": (
            "late owned pressure capped by maximum owned pressure at either prior touch"
        ),
        "dormant_reappearance_behavior": DORMANT_REAPPEARANCE_BEHAVIOR,
        "continuous_persistence_claimed": False,
        "schema_id": SCHEMA_ID,
        "frame_order": list(FRAME_NAMES),
        "observable_fields": list(OBSERVABLE_FIELDS),
        "owned_pressure": {
            "operator": "minimum",
            "inputs": [
                "strength",
                "distinction",
                "polarity",
                "relation",
                "return_observed",
                "observed_stability_score",
                "one_minus_echo_mimic_score",
            ],
        },
        "lineage_support": {
            "operator": "maximum",
            "inputs": ["early_owned_pressure", "witness_owned_pressure"],
        },
        "lineage_score": {
            "operator": "minimum",
            "inputs": ["late_owned_pressure", "lineage_support"],
        },
        "no_lineage_score": "late_owned_pressure",
        "lineage_delta": "maximum(0,no_lineage_score-lineage_score)",
        "output_kind": "continuous_development_scores_only",
        "selected_threshold_option": None,
        "scientific_thresholds_selected": False,
    }


# Short aliases make the intended public surface explicit without creating a
# second implementation path.
score_lineage = score_lineage_frames


def score_no_lineage(frames: LineageFrames | object) -> float:
    return score_lineage_frames(frames).no_lineage_score
