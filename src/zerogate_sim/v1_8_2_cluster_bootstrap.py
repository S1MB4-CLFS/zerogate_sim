from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Mapping

from zerogate_sim.v1_8_2_threshold_contract import EvaluationMathError

BOOTSTRAP_SEED = 18122001
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_LOWER_INDEX = 49
BOOTSTRAP_UPPER_INDEX = 1950


@dataclass(frozen=True, slots=True)
class BootstrapInterval:
    lineage_ids: tuple[str, ...]
    observed_mean: float
    confidence: float
    resamples: int
    seed: int
    lower_index: int
    upper_index: int
    lower: float
    upper: float
    replicate_values: tuple[float, ...]

    def to_dict(self, *, include_replicates: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "lineage_ids": list(self.lineage_ids),
            "observed_mean": self.observed_mean,
            "confidence": self.confidence,
            "resamples": self.resamples,
            "seed": self.seed,
            "lower_index": self.lower_index,
            "upper_index": self.upper_index,
            "lower": self.lower,
            "upper": self.upper,
        }
        if include_replicates:
            value["replicate_values"] = list(self.replicate_values)
        return value


def _exact_nonnegative_int(value: object, *, field: str, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise EvaluationMathError(f"{field} must be an exact {qualifier} int")
    return value


def _finite_number(value: object, *, field: str) -> float:
    if type(value) not in {int, float}:
        raise EvaluationMathError(f"{field} must be an actual int or float")
    number = float(value)
    if not math.isfinite(number):
        raise EvaluationMathError(f"{field} must be finite")
    return 0.0 if number == 0.0 else number


def cluster_draw_index(
    lineage_count: int,
    replicate: int,
    slot: int,
    *,
    seed: int = BOOTSTRAP_SEED,
) -> int:
    """Return uint64_be(SHA256(UTF8(seed:b:j))[0:8]) modulo lineage count."""

    count = _exact_nonnegative_int(lineage_count, field="lineage_count", positive=True)
    b = _exact_nonnegative_int(replicate, field="replicate")
    j = _exact_nonnegative_int(slot, field="slot")
    locked_seed = _exact_nonnegative_int(seed, field="seed")
    digest = hashlib.sha256(f"{locked_seed}:{b}:{j}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) % count


def cluster_draw_indices(
    lineage_count: int,
    replicate: int,
    *,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[int, ...]:
    count = _exact_nonnegative_int(lineage_count, field="lineage_count", positive=True)
    return tuple(
        cluster_draw_index(count, replicate, slot, seed=seed)
        for slot in range(count)
    )


def cluster_draw_matrix(
    lineage_count: int,
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[tuple[int, ...], ...]:
    count = _exact_nonnegative_int(lineage_count, field="lineage_count", positive=True)
    repetitions = _exact_nonnegative_int(resamples, field="resamples", positive=True)
    return tuple(
        cluster_draw_indices(count, replicate, seed=seed)
        for replicate in range(repetitions)
    )


def percentile_indices(
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    confidence: float = BOOTSTRAP_CONFIDENCE,
) -> tuple[int, int]:
    repetitions = _exact_nonnegative_int(resamples, field="resamples", positive=True)
    level = _finite_number(confidence, field="confidence")
    if not 0.0 < level < 1.0:
        raise EvaluationMathError("confidence must satisfy 0 < confidence < 1")
    tail = (1.0 - level) / 2.0
    lower = math.floor(tail * (repetitions - 1))
    upper = math.ceil((1.0 - tail) * (repetitions - 1))
    return lower, upper


def _ordered_lineage_values(
    metric_by_lineage: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    if not isinstance(metric_by_lineage, Mapping) or not metric_by_lineage:
        raise EvaluationMathError("bootstrap requires at least one generator lineage")
    lineage_ids = tuple(sorted(metric_by_lineage))
    if any(type(lineage_id) is not str or not lineage_id for lineage_id in lineage_ids):
        raise EvaluationMathError("bootstrap lineage IDs must be non-empty strings")
    values = tuple(
        _finite_number(metric_by_lineage[lineage_id], field=f"metric[{lineage_id!r}]")
        for lineage_id in lineage_ids
    )
    return lineage_ids, values


def bootstrap_replicates(
    metric_by_lineage: Mapping[str, object],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, ...]:
    """Bootstrap generator-lineage clusters; rows are never resampled."""

    _, values = _ordered_lineage_values(metric_by_lineage)
    repetitions = _exact_nonnegative_int(resamples, field="resamples", positive=True)
    locked_seed = _exact_nonnegative_int(seed, field="seed")
    count = len(values)
    return tuple(
        sum(values[index] for index in cluster_draw_indices(count, b, seed=locked_seed))
        / count
        for b in range(repetitions)
    )


def cluster_percentile_interval(
    metric_by_lineage: Mapping[str, object],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    confidence: float = BOOTSTRAP_CONFIDENCE,
    seed: int = BOOTSTRAP_SEED,
) -> BootstrapInterval:
    lineage_ids, values = _ordered_lineage_values(metric_by_lineage)
    repetitions = _exact_nonnegative_int(resamples, field="resamples", positive=True)
    locked_seed = _exact_nonnegative_int(seed, field="seed")
    level = _finite_number(confidence, field="confidence")
    replicates = bootstrap_replicates(
        dict(zip(lineage_ids, values, strict=True)),
        resamples=repetitions,
        seed=locked_seed,
    )
    lower_index, upper_index = percentile_indices(
        resamples=repetitions,
        confidence=level,
    )
    ordered_replicates = sorted(replicates)
    return BootstrapInterval(
        lineage_ids=lineage_ids,
        observed_mean=sum(values) / len(values),
        confidence=level,
        resamples=repetitions,
        seed=locked_seed,
        lower_index=lower_index,
        upper_index=upper_index,
        lower=ordered_replicates[lower_index],
        upper=ordered_replicates[upper_index],
        replicate_values=replicates,
    )


def paired_cluster_difference_interval(
    primary_by_lineage: Mapping[str, object],
    comparator_by_lineage: Mapping[str, object],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    confidence: float = BOOTSTRAP_CONFIDENCE,
    seed: int = BOOTSTRAP_SEED,
) -> BootstrapInterval:
    """Use the same cluster draw for primary and comparator in every slot."""

    primary_ids, primary_values = _ordered_lineage_values(primary_by_lineage)
    comparator_ids, comparator_values = _ordered_lineage_values(comparator_by_lineage)
    if primary_ids != comparator_ids:
        raise EvaluationMathError("paired bootstrap requires identical lineage ID sets")
    differences = {
        lineage_id: primary_values[index] - comparator_values[index]
        for index, lineage_id in enumerate(primary_ids)
    }
    return cluster_percentile_interval(
        differences,
        resamples=resamples,
        confidence=confidence,
        seed=seed,
    )


if percentile_indices() != (BOOTSTRAP_LOWER_INDEX, BOOTSTRAP_UPPER_INDEX):
    raise RuntimeError("locked 2000-replicate percentile indices changed")
