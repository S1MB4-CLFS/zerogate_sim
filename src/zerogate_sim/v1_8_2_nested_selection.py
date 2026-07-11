from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping

from zerogate_sim.v1_8_2_metrics import (
    AggregateMetrics,
    INVALID_MISSING_REQUIRED_ROLE,
    MetricResult,
    REQUIRED_ROLES,
    VALID_METRICS,
    aggregate_lineage_metrics,
    calculate_metrics,
    model_comparison_tuple,
    primary_strictly_better,
)
from zerogate_sim.v1_8_2_threshold_contract import (
    THRESHOLD_OPTIONS,
    EvaluationMathError,
    ThresholdOption,
    classify_score,
    threshold_option,
)

MINIMUM_GENERATOR_LINEAGES = 4
VALID_NESTED_SELECTION = "VALID_NESTED_SELECTION"
INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR = "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR"


@dataclass(frozen=True, slots=True)
class ScoredCase:
    generator_lineage_id: str
    evaluation_role: str
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "generator_lineage_id": self.generator_lineage_id,
            "evaluation_role": self.evaluation_role,
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class PredictionRecord:
    generator_lineage_id: str
    evaluation_role: str
    score: float
    option_id: str
    prediction: int

    def to_dict(self) -> dict[str, object]:
        return {
            "generator_lineage_id": self.generator_lineage_id,
            "evaluation_role": self.evaluation_role,
            "score": self.score,
            "option_id": self.option_id,
            "prediction": self.prediction,
        }


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    option_id: str
    valid: bool
    invalid_statuses: tuple[str, ...]
    boundary_margin: float
    aggregate_metrics: AggregateMetrics | None
    selection_sort_key: tuple[object, ...] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "option_id": self.option_id,
            "valid": self.valid,
            "invalid_statuses": list(self.invalid_statuses),
            "boundary_margin": self.boundary_margin,
            "aggregate_metrics": (
                None if self.aggregate_metrics is None else self.aggregate_metrics.to_dict()
            ),
            "selection_sort_key": (
                None
                if self.selection_sort_key is None
                else list(self.selection_sort_key)
            ),
        }


@dataclass(frozen=True, slots=True)
class ThresholdSelectionResult:
    selected_option_id: str
    candidates: tuple[CandidateEvaluation, ...]

    def selected_candidate(self) -> CandidateEvaluation:
        for candidate in self.candidates:
            if candidate.option_id == self.selected_option_id:
                return candidate
        raise RuntimeError("selected threshold candidate is missing")

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_option_id": self.selected_option_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True, slots=True)
class OuterFoldResult:
    held_lineage_id: str
    selected_option_id: str
    training_selection: ThresholdSelectionResult
    held_metrics: MetricResult

    def to_dict(self) -> dict[str, object]:
        return {
            "held_lineage_id": self.held_lineage_id,
            "selected_option_id": self.selected_option_id,
            "training_selection": self.training_selection.to_dict(),
            "held_metrics": self.held_metrics.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class NestedSelectionResult:
    status: str
    outer_folds: tuple[OuterFoldResult, ...]
    oof_predictions: tuple[PredictionRecord, ...]
    oof_metrics: AggregateMetrics
    full_development_selection: ThresholdSelectionResult

    @property
    def selected_option_id(self) -> str:
        return self.full_development_selection.selected_option_id

    @property
    def outer_option_by_lineage(self) -> dict[str, str]:
        return {
            fold.held_lineage_id: fold.selected_option_id
            for fold in self.outer_folds
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "outer_folds": [fold.to_dict() for fold in self.outer_folds],
            "oof_predictions_frozen_before_full_selection": True,
            "oof_predictions": [row.to_dict() for row in self.oof_predictions],
            "oof_metrics": self.oof_metrics.to_dict(),
            "full_development_selection": self.full_development_selection.to_dict(),
            "selected_option_id": self.selected_option_id,
        }


@dataclass(frozen=True, slots=True)
class FrozenThresholdEvaluation:
    status: str
    outer_option_by_lineage: tuple[tuple[str, str], ...]
    full_option_id: str
    oof_predictions: tuple[PredictionRecord, ...]
    oof_metrics: AggregateMetrics
    full_development_metrics: AggregateMetrics

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "outer_option_by_lineage": dict(self.outer_option_by_lineage),
            "full_option_id": self.full_option_id,
            "oof_predictions": [row.to_dict() for row in self.oof_predictions],
            "oof_metrics": self.oof_metrics.to_dict(),
            "full_development_metrics": self.full_development_metrics.to_dict(),
        }


def _unit_score(value: object) -> float:
    if type(value) not in {int, float}:
        raise EvaluationMathError("case score must be an actual int or float")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise EvaluationMathError("case score must satisfy 0 <= score <= 1")
    return 0.0 if number == 0.0 else number


def _scored_case(value: object, *, position: int) -> ScoredCase:
    if isinstance(value, ScoredCase):
        case = value
    elif isinstance(value, Mapping):
        expected = {"generator_lineage_id", "evaluation_role", "score"}
        if set(value) != expected:
            raise EvaluationMathError(
                f"scored case {position} must have exact keys {sorted(expected)}"
            )
        case = ScoredCase(
            generator_lineage_id=value["generator_lineage_id"],  # type: ignore[arg-type]
            evaluation_role=value["evaluation_role"],  # type: ignore[arg-type]
            score=value["score"],  # type: ignore[arg-type]
        )
    else:
        raise EvaluationMathError(f"scored case {position} has invalid type")
    if type(case.generator_lineage_id) is not str or not case.generator_lineage_id:
        raise EvaluationMathError("generator_lineage_id must be a non-empty string")
    if type(case.evaluation_role) is not str or case.evaluation_role not in REQUIRED_ROLES:
        raise EvaluationMathError("evaluation_role must be one of the three locked roles")
    return ScoredCase(
        generator_lineage_id=case.generator_lineage_id,
        evaluation_role=case.evaluation_role,
        score=_unit_score(case.score),
    )


def normalize_scored_cases(values: Iterable[object]) -> tuple[ScoredCase, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise EvaluationMathError("scored cases must be an iterable")
    cases = tuple(_scored_case(value, position=index) for index, value in enumerate(values))
    if not cases:
        raise EvaluationMathError("at least one scored case is required")
    return tuple(
        sorted(
            cases,
            key=lambda case: (
                case.generator_lineage_id,
                case.evaluation_role,
                case.score.hex(),
            ),
        )
    )


def _by_lineage(cases: tuple[ScoredCase, ...]) -> dict[str, tuple[ScoredCase, ...]]:
    lineage_ids = sorted({case.generator_lineage_id for case in cases})
    return {
        lineage_id: tuple(case for case in cases if case.generator_lineage_id == lineage_id)
        for lineage_id in lineage_ids
    }


def _assert_all_roles(by_lineage: Mapping[str, tuple[ScoredCase, ...]]) -> None:
    expected = set(REQUIRED_ROLES)
    for lineage_id, cases in by_lineage.items():
        observed = {case.evaluation_role for case in cases}
        if observed != expected:
            raise EvaluationMathError(
                f"{INVALID_MISSING_REQUIRED_ROLE}: {lineage_id!r} has roles {sorted(observed)}"
            )


def observed_boundary_margin(
    cases: Iterable[object], option: str | ThresholdOption
) -> float:
    checked = normalize_scored_cases(cases)
    locked = threshold_option(option)
    return min(
        min(
            abs(case.score - locked.resist_max),
            abs(case.score - locked.crown_min),
        )
        for case in checked
    )


def selection_sort_key(
    aggregate: AggregateMetrics,
    boundary_margin: float,
    option_id: str,
) -> tuple[float, float, float, float, float, float, float, float, str]:
    """Return the exact ascending key for the nine locked objective tiers."""

    if not isinstance(aggregate, AggregateMetrics):
        raise EvaluationMathError("selection aggregate must be AggregateMetrics")
    margin = _unit_score(boundary_margin)
    locked = threshold_option(option_id)
    return (
        -aggregate.worst_fold_minimum_guardrail,
        -aggregate.mean_fold_minimum_guardrail,
        aggregate.worst_fold_trap_crown_rate,
        aggregate.macro_latent_crown_rate,
        aggregate.macro_expresser_resist_rate,
        -aggregate.worst_fold_macro_recall,
        aggregate.macro_nonlatent_hold_rate,
        -margin,
        locked.option_id,
    )


def _predictions_for_option(
    cases: tuple[ScoredCase, ...], option_id: str
) -> tuple[PredictionRecord, ...]:
    return tuple(
        PredictionRecord(
            generator_lineage_id=case.generator_lineage_id,
            evaluation_role=case.evaluation_role,
            score=case.score,
            option_id=option_id,
            prediction=classify_score(case.score, option_id),
        )
        for case in cases
    )


def _metrics_by_lineage(
    predictions: tuple[PredictionRecord, ...],
) -> dict[str, MetricResult]:
    lineage_ids = sorted({row.generator_lineage_id for row in predictions})
    return {
        lineage_id: calculate_metrics(
            (row.evaluation_role, row.prediction)
            for row in predictions
            if row.generator_lineage_id == lineage_id
        )
        for lineage_id in lineage_ids
    }


def evaluate_threshold_candidate(
    cases: Iterable[object], option: str | ThresholdOption
) -> CandidateEvaluation:
    checked = normalize_scored_cases(cases)
    locked = threshold_option(option)
    by_lineage = _by_lineage(checked)
    _assert_all_roles(by_lineage)
    predictions = _predictions_for_option(checked, locked.option_id)
    metrics = _metrics_by_lineage(predictions)
    invalid_statuses = tuple(
        f"{lineage_id}:{metrics[lineage_id].status}"
        for lineage_id in sorted(metrics)
        if metrics[lineage_id].status != VALID_METRICS
    )
    margin = observed_boundary_margin(checked, locked)
    if invalid_statuses:
        return CandidateEvaluation(
            option_id=locked.option_id,
            valid=False,
            invalid_statuses=invalid_statuses,
            boundary_margin=margin,
            aggregate_metrics=None,
            selection_sort_key=None,
        )
    aggregate = aggregate_lineage_metrics(metrics)
    return CandidateEvaluation(
        option_id=locked.option_id,
        valid=True,
        invalid_statuses=(),
        boundary_margin=margin,
        aggregate_metrics=aggregate,
        selection_sort_key=selection_sort_key(aggregate, margin, locked.option_id),
    )


def select_threshold_option(cases: Iterable[object]) -> ThresholdSelectionResult:
    checked = normalize_scored_cases(cases)
    candidates = tuple(
        evaluate_threshold_candidate(checked, option) for option in THRESHOLD_OPTIONS
    )
    valid = tuple(candidate for candidate in candidates if candidate.valid)
    if not valid:
        statuses = sorted(
            {status for candidate in candidates for status in candidate.invalid_statuses}
        )
        raise EvaluationMathError(
            "no valid locked threshold option; " + ", ".join(statuses)
        )
    selected = min(valid, key=lambda candidate: candidate.selection_sort_key)
    return ThresholdSelectionResult(
        selected_option_id=selected.option_id,
        candidates=candidates,
    )


def nested_logo_select(cases: Iterable[object]) -> NestedSelectionResult:
    """Run deterministic nested leave-one-generator-lineage-out selection."""

    checked = normalize_scored_cases(cases)
    by_lineage = _by_lineage(checked)
    _assert_all_roles(by_lineage)
    lineage_ids = tuple(sorted(by_lineage))
    if len(lineage_ids) < MINIMUM_GENERATOR_LINEAGES:
        raise EvaluationMathError("HOLD_INSUFFICIENT_GENERATOR_LINEAGES")

    outer_folds: list[OuterFoldResult] = []
    oof_predictions: list[PredictionRecord] = []
    for held_lineage_id in lineage_ids:
        training_cases = tuple(
            case for case in checked if case.generator_lineage_id != held_lineage_id
        )
        training_selection = select_threshold_option(training_cases)
        selected_option_id = training_selection.selected_option_id
        held_predictions = _predictions_for_option(
            by_lineage[held_lineage_id], selected_option_id
        )
        held_metrics = calculate_metrics(
            (row.evaluation_role, row.prediction) for row in held_predictions
        )
        outer_folds.append(
            OuterFoldResult(
                held_lineage_id=held_lineage_id,
                selected_option_id=selected_option_id,
                training_selection=training_selection,
                held_metrics=held_metrics,
            )
        )
        oof_predictions.extend(held_predictions)

    # This immutable tuple is the frozen OOF result. Full-development selection
    # is deliberately performed only after it exists.
    frozen_oof = tuple(oof_predictions)
    oof_by_lineage = _metrics_by_lineage(frozen_oof)
    oof_metrics = aggregate_lineage_metrics(oof_by_lineage, allow_dead_safe=True)
    status = (
        VALID_NESTED_SELECTION
        if all(metric.status == VALID_METRICS for metric in oof_by_lineage.values())
        else INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR
    )
    full_selection = select_threshold_option(checked)
    return NestedSelectionResult(
        status=status,
        outer_folds=tuple(outer_folds),
        oof_predictions=frozen_oof,
        oof_metrics=oof_metrics,
        full_development_selection=full_selection,
    )


def evaluate_frozen_thresholds(
    cases: Iterable[object],
    *,
    outer_option_by_lineage: Mapping[str, str],
    full_option_id: str,
) -> FrozenThresholdEvaluation:
    """Evaluate another model with the primary model's thresholds unchanged."""

    checked = normalize_scored_cases(cases)
    by_lineage = _by_lineage(checked)
    _assert_all_roles(by_lineage)
    lineage_ids = tuple(sorted(by_lineage))
    if set(outer_option_by_lineage) != set(lineage_ids):
        raise EvaluationMathError("frozen outer threshold lineage set mismatch")
    outer_options = tuple(
        (lineage_id, threshold_option(outer_option_by_lineage[lineage_id]).option_id)
        for lineage_id in lineage_ids
    )
    locked_full = threshold_option(full_option_id).option_id

    oof_predictions = tuple(
        prediction
        for lineage_id, option_id in outer_options
        for prediction in _predictions_for_option(by_lineage[lineage_id], option_id)
    )
    oof_by_lineage = _metrics_by_lineage(oof_predictions)
    oof_metrics = aggregate_lineage_metrics(oof_by_lineage, allow_dead_safe=True)
    full_predictions = _predictions_for_option(checked, locked_full)
    full_by_lineage = _metrics_by_lineage(full_predictions)
    full_metrics = aggregate_lineage_metrics(full_by_lineage, allow_dead_safe=True)
    status = (
        VALID_NESTED_SELECTION
        if all(
            metric.status == VALID_METRICS
            for metric in (*oof_by_lineage.values(), *full_by_lineage.values())
        )
        else INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR
    )
    return FrozenThresholdEvaluation(
        status=status,
        outer_option_by_lineage=outer_options,
        full_option_id=locked_full,
        oof_predictions=oof_predictions,
        oof_metrics=oof_metrics,
        full_development_metrics=full_metrics,
    )


def evaluate_ablation_frozen(
    primary: NestedSelectionResult,
    ablation_cases: Iterable[object],
) -> FrozenThresholdEvaluation:
    if not isinstance(primary, NestedSelectionResult):
        raise EvaluationMathError("primary result must be NestedSelectionResult")
    return evaluate_frozen_thresholds(
        ablation_cases,
        outer_option_by_lineage=primary.outer_option_by_lineage,
        full_option_id=primary.selected_option_id,
    )


def evaluate_ablation_retuned(ablation_cases: Iterable[object]) -> NestedSelectionResult:
    return nested_logo_select(ablation_cases)


def frozen_and_retuned_ablation_comparison(
    primary: NestedSelectionResult,
    ablation_cases: Iterable[object],
) -> dict[str, object]:
    """Require strict primary superiority for both frozen and retuned ablations."""

    frozen = evaluate_ablation_frozen(primary, ablation_cases)
    retuned = evaluate_ablation_retuned(ablation_cases)
    primary_tuple = model_comparison_tuple(primary.oof_metrics)
    frozen_tuple = model_comparison_tuple(frozen.oof_metrics)
    retuned_tuple = model_comparison_tuple(retuned.oof_metrics)
    frozen_strict = primary_strictly_better(primary.oof_metrics, frozen.oof_metrics)
    retuned_strict = primary_strictly_better(primary.oof_metrics, retuned.oof_metrics)
    return {
        "primary_tuple": primary_tuple,
        "frozen_ablation": frozen,
        "frozen_ablation_tuple": frozen_tuple,
        "primary_strictly_better_frozen": frozen_strict,
        "retuned_ablation": retuned,
        "retuned_ablation_tuple": retuned_tuple,
        "primary_strictly_better_retuned": retuned_strict,
        "necessity_requirement_passed": (
            primary.status == VALID_NESTED_SELECTION
            and frozen.status == VALID_NESTED_SELECTION
            and retuned.status == VALID_NESTED_SELECTION
            and frozen_strict
            and retuned_strict
        ),
    }
