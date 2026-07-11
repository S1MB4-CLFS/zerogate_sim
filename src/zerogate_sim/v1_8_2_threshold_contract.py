from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


class EvaluationMathError(ValueError):
    """Raised when a pure v1.8.2 calculation is outside the locked contract."""


@dataclass(frozen=True, slots=True)
class ThresholdOption:
    option_id: str
    resist_max: float
    crown_min: float

    def to_dict(self) -> dict[str, object]:
        return {
            "option_id": self.option_id,
            "resist_max": self.resist_max,
            "crown_min": self.crown_min,
        }


THRESHOLD_OPTIONS = (
    ThresholdOption(option_id="wide_hold", resist_max=0.2, crown_min=0.8),
    ThresholdOption(option_id="medium_hold", resist_max=0.3, crown_min=0.7),
    ThresholdOption(option_id="narrow_hold", resist_max=0.4, crown_min=0.6),
)
THRESHOLD_OPTION_IDS = tuple(option.option_id for option in THRESHOLD_OPTIONS)
THRESHOLD_BY_ID: Mapping[str, ThresholdOption] = MappingProxyType(
    {option.option_id: option for option in THRESHOLD_OPTIONS}
)


def _unit_float(value: object, *, field: str) -> float:
    if type(value) not in {int, float}:
        raise EvaluationMathError(
            f"{field} must be an actual int or float, got {type(value).__name__}"
        )
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise EvaluationMathError(f"{field} must satisfy 0 <= value <= 1")
    return 0.0 if number == 0.0 else number


def threshold_option(value: str | ThresholdOption) -> ThresholdOption:
    if isinstance(value, ThresholdOption):
        locked = THRESHOLD_BY_ID.get(value.option_id)
        if locked != value:
            raise EvaluationMathError(
                "only the three exact locked threshold options are allowed"
            )
        return locked
    if type(value) is not str or value not in THRESHOLD_BY_ID:
        raise EvaluationMathError(f"unknown locked threshold option: {value!r}")
    return THRESHOLD_BY_ID[value]


def classify_score(score: object, option: str | ThresholdOption) -> int:
    """Apply the exact inclusive RESIST/CROWN and strict HOLD boundaries."""

    number = _unit_float(score, field="score")
    locked = threshold_option(option)
    if number <= locked.resist_max:
        return -1
    if number >= locked.crown_min:
        return 1
    return 0

