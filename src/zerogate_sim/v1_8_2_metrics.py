from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from zerogate_sim.v1_8_lineage_schema import (
    canonical_json,
    sha256_bytes,
    validate_lineage_frames,
)
from zerogate_sim.v1_8_2_threshold_contract import EvaluationMathError

REQUIRED_ROLES = ("expresser", "latent", "trap")
ROLE_TO_TARGET: Mapping[str, int] = MappingProxyType(
    {"expresser": 1, "latent": 0, "trap": -1}
)
TRINARY_VALUES = (-1, 0, 1)

VALID_METRICS = "VALID_METRICS"
INVALID_MISSING_REQUIRED_ROLE = "INVALID_MISSING_REQUIRED_ROLE"
INVALID_DEAD_SAFE_NO_CROWNS = "INVALID_DEAD_SAFE_NO_CROWNS"

COMPARISON_FIELDS = (
    "worst_fold_minimum_guardrail",
    "mean_fold_minimum_guardrail",
    "negative_worst_fold_trap_crown_rate",
    "negative_macro_latent_crown_rate",
    "negative_macro_expresser_resist_rate",
    "worst_fold_macro_recall",
    "negative_macro_nonlatent_hold_rate",
)


@dataclass(frozen=True, slots=True)
class MetricResult:
    status: str
    effective_case_count: int
    expresser_denominator: int
    latent_denominator: int
    trap_denominator: int
    crown_denominator: int
    expresser_crown_count: int
    expresser_hold_count: int
    expresser_resist_count: int
    latent_crown_count: int
    latent_hold_count: int
    latent_resist_count: int
    trap_crown_count: int
    trap_hold_count: int
    trap_resist_count: int
    crown_precision: float | None
    expresser_crown_recall: float | None
    expresser_resist_rate: float | None
    latent_crown_rate: float | None
    latent_hold_recall: float | None
    trap_crown_rate: float | None
    trap_resist_recall: float | None
    nonlatent_hold_rate: float | None
    macro_recall: float | None
    fold_minimum_guardrail: float | None

    @property
    def role_denominators(self) -> dict[str, int]:
        return {
            "expresser": self.expresser_denominator,
            "latent": self.latent_denominator,
            "trap": self.trap_denominator,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "effective_case_count": self.effective_case_count,
            "role_denominators": self.role_denominators,
            "crown_denominator": self.crown_denominator,
            "counts": {
                "expresser_crown": self.expresser_crown_count,
                "expresser_hold": self.expresser_hold_count,
                "expresser_resist": self.expresser_resist_count,
                "latent_crown": self.latent_crown_count,
                "latent_hold": self.latent_hold_count,
                "latent_resist": self.latent_resist_count,
                "trap_crown": self.trap_crown_count,
                "trap_hold": self.trap_hold_count,
                "trap_resist": self.trap_resist_count,
            },
            "crown_precision": self.crown_precision,
            "expresser_crown_recall": self.expresser_crown_recall,
            "expresser_resist_rate": self.expresser_resist_rate,
            "latent_crown_rate": self.latent_crown_rate,
            "latent_hold_recall": self.latent_hold_recall,
            "trap_crown_rate": self.trap_crown_rate,
            "trap_resist_recall": self.trap_resist_recall,
            "nonlatent_hold_rate": self.nonlatent_hold_rate,
            "macro_recall": self.macro_recall,
            "fold_minimum_guardrail": self.fold_minimum_guardrail,
        }


@dataclass(frozen=True, slots=True)
class AggregateMetrics:
    lineage_count: int
    worst_fold_minimum_guardrail: float
    mean_fold_minimum_guardrail: float
    worst_fold_trap_crown_rate: float
    macro_latent_crown_rate: float
    macro_expresser_resist_rate: float
    worst_fold_macro_recall: float
    macro_nonlatent_hold_rate: float

    def comparison_tuple(self) -> tuple[float, float, float, float, float, float, float]:
        return (
            self.worst_fold_minimum_guardrail,
            self.mean_fold_minimum_guardrail,
            -self.worst_fold_trap_crown_rate,
            -self.macro_latent_crown_rate,
            -self.macro_expresser_resist_rate,
            self.worst_fold_macro_recall,
            -self.macro_nonlatent_hold_rate,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "lineage_count": self.lineage_count,
            "worst_fold_minimum_guardrail": self.worst_fold_minimum_guardrail,
            "mean_fold_minimum_guardrail": self.mean_fold_minimum_guardrail,
            "worst_fold_trap_crown_rate": self.worst_fold_trap_crown_rate,
            "macro_latent_crown_rate": self.macro_latent_crown_rate,
            "macro_expresser_resist_rate": self.macro_expresser_resist_rate,
            "worst_fold_macro_recall": self.worst_fold_macro_recall,
            "macro_nonlatent_hold_rate": self.macro_nonlatent_hold_rate,
            "comparison_tuple": list(self.comparison_tuple()),
        }


def _role_prediction_pairs(
    values: Iterable[tuple[object, object]],
) -> tuple[tuple[str, int], ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise EvaluationMathError("role/prediction values must be an iterable of pairs")
    out: list[tuple[str, int]] = []
    for index, value in enumerate(values):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise EvaluationMathError(f"metric row {index} must be a two-item pair")
        role, prediction = value
        if type(role) is not str or role not in ROLE_TO_TARGET:
            raise EvaluationMathError(f"metric row {index} has unknown role {role!r}")
        if type(prediction) is not int or prediction not in TRINARY_VALUES:
            raise EvaluationMathError(
                f"metric row {index} prediction must be exact trinary int"
            )
        out.append((role, prediction))
    if not out:
        raise EvaluationMathError("at least one role/prediction row is required")
    return tuple(out)


def calculate_metrics(values: Iterable[tuple[object, object]]) -> MetricResult:
    """Calculate every locked class-specific metric with exact denominators."""

    pairs = _role_prediction_pairs(values)
    counts = {
        (role, prediction): sum(
            1 for observed_role, observed_prediction in pairs
            if observed_role == role and observed_prediction == prediction
        )
        for role in REQUIRED_ROLES
        for prediction in TRINARY_VALUES
    }
    denominators = {
        role: sum(counts[(role, prediction)] for prediction in TRINARY_VALUES)
        for role in REQUIRED_ROLES
    }
    crown_denominator = sum(counts[(role, 1)] for role in REQUIRED_ROLES)
    missing_role = any(denominators[role] == 0 for role in REQUIRED_ROLES)

    expresser_crown_recall = (
        None
        if denominators["expresser"] == 0
        else counts[("expresser", 1)] / denominators["expresser"]
    )
    expresser_resist_rate = (
        None
        if denominators["expresser"] == 0
        else counts[("expresser", -1)] / denominators["expresser"]
    )
    latent_crown_rate = (
        None
        if denominators["latent"] == 0
        else counts[("latent", 1)] / denominators["latent"]
    )
    latent_hold_recall = (
        None
        if denominators["latent"] == 0
        else counts[("latent", 0)] / denominators["latent"]
    )
    trap_crown_rate = (
        None
        if denominators["trap"] == 0
        else counts[("trap", 1)] / denominators["trap"]
    )
    trap_resist_recall = (
        None
        if denominators["trap"] == 0
        else counts[("trap", -1)] / denominators["trap"]
    )
    nonlatent_denominator = denominators["expresser"] + denominators["trap"]
    nonlatent_hold_rate = (
        None
        if nonlatent_denominator == 0
        else (counts[("expresser", 0)] + counts[("trap", 0)])
        / nonlatent_denominator
    )
    crown_precision = (
        None
        if crown_denominator == 0
        else counts[("expresser", 1)] / crown_denominator
    )

    if missing_role:
        status = INVALID_MISSING_REQUIRED_ROLE
        macro_recall = None
        guardrail = None
    else:
        assert expresser_crown_recall is not None
        assert expresser_resist_rate is not None
        assert latent_crown_rate is not None
        assert latent_hold_recall is not None
        assert trap_crown_rate is not None
        assert trap_resist_recall is not None
        assert nonlatent_hold_rate is not None
        macro_recall = (
            expresser_crown_recall + latent_hold_recall + trap_resist_recall
        ) / 3.0
        guardrail = min(
            expresser_crown_recall,
            latent_hold_recall,
            trap_resist_recall,
            1.0 - trap_crown_rate,
            1.0 - latent_crown_rate,
            1.0 - expresser_resist_rate,
        )
        status = VALID_METRICS if crown_denominator else INVALID_DEAD_SAFE_NO_CROWNS

    return MetricResult(
        status=status,
        effective_case_count=len(pairs),
        expresser_denominator=denominators["expresser"],
        latent_denominator=denominators["latent"],
        trap_denominator=denominators["trap"],
        crown_denominator=crown_denominator,
        expresser_crown_count=counts[("expresser", 1)],
        expresser_hold_count=counts[("expresser", 0)],
        expresser_resist_count=counts[("expresser", -1)],
        latent_crown_count=counts[("latent", 1)],
        latent_hold_count=counts[("latent", 0)],
        latent_resist_count=counts[("latent", -1)],
        trap_crown_count=counts[("trap", 1)],
        trap_hold_count=counts[("trap", 0)],
        trap_resist_count=counts[("trap", -1)],
        crown_precision=crown_precision,
        expresser_crown_recall=expresser_crown_recall,
        expresser_resist_rate=expresser_resist_rate,
        latent_crown_rate=latent_crown_rate,
        latent_hold_recall=latent_hold_recall,
        trap_crown_rate=trap_crown_rate,
        trap_resist_recall=trap_resist_recall,
        nonlatent_hold_rate=nonlatent_hold_rate,
        macro_recall=macro_recall,
        fold_minimum_guardrail=guardrail,
    )


def calculate_metrics_from_predictions(
    roles: Sequence[object], predictions: Sequence[object]
) -> MetricResult:
    if len(roles) != len(predictions):
        raise EvaluationMathError("roles and predictions must have equal length")
    return calculate_metrics(zip(roles, predictions, strict=True))


def aggregate_lineage_metrics(
    by_lineage: Mapping[str, MetricResult],
    *,
    allow_dead_safe: bool = False,
) -> AggregateMetrics:
    """Macro-average lineage rates; never pool cases across lineages."""

    if not isinstance(by_lineage, Mapping) or not by_lineage:
        raise EvaluationMathError("at least one generator lineage metric is required")
    ordered: list[MetricResult] = []
    for lineage_id in sorted(by_lineage):
        if type(lineage_id) is not str or not lineage_id:
            raise EvaluationMathError("generator lineage IDs must be non-empty strings")
        metric = by_lineage[lineage_id]
        if not isinstance(metric, MetricResult):
            raise EvaluationMathError("lineage metric values must be MetricResult")
        if metric.status == INVALID_MISSING_REQUIRED_ROLE:
            raise EvaluationMathError(INVALID_MISSING_REQUIRED_ROLE)
        if metric.status != VALID_METRICS and not allow_dead_safe:
            raise EvaluationMathError(metric.status)
        ordered.append(metric)

    guardrails = [float(metric.fold_minimum_guardrail) for metric in ordered]
    trap_crowns = [float(metric.trap_crown_rate) for metric in ordered]
    latent_crowns = [float(metric.latent_crown_rate) for metric in ordered]
    expresser_resists = [float(metric.expresser_resist_rate) for metric in ordered]
    macro_recalls = [float(metric.macro_recall) for metric in ordered]
    nonlatent_holds = [float(metric.nonlatent_hold_rate) for metric in ordered]
    count = len(ordered)
    return AggregateMetrics(
        lineage_count=count,
        worst_fold_minimum_guardrail=min(guardrails),
        mean_fold_minimum_guardrail=sum(guardrails) / count,
        worst_fold_trap_crown_rate=max(trap_crowns),
        macro_latent_crown_rate=sum(latent_crowns) / count,
        macro_expresser_resist_rate=sum(expresser_resists) / count,
        worst_fold_macro_recall=min(macro_recalls),
        macro_nonlatent_hold_rate=sum(nonlatent_holds) / count,
    )


def model_comparison_tuple(
    value: AggregateMetrics,
) -> tuple[float, float, float, float, float, float, float]:
    if not isinstance(value, AggregateMetrics):
        raise EvaluationMathError("comparison input must be AggregateMetrics")
    return value.comparison_tuple()


def primary_strictly_better(
    primary: AggregateMetrics, comparator: AggregateMetrics
) -> bool:
    """Use Python's exact binary64 lexicographic comparison, with zero tolerance."""

    return model_comparison_tuple(primary) > model_comparison_tuple(comparator)


def observable_identity_sha256(frames: object) -> str:
    """Hash canonical three-frame values, excluding every ID, label, and group."""

    checked = validate_lineage_frames(frames, source="duplicate observable identity")
    value = [dict(frame) for frame in checked]
    return sha256_bytes(canonical_json(value).encode("utf-8"))


@dataclass(frozen=True, slots=True)
class DuplicateAuditRecord:
    row_index: int
    generator_lineage_id: str
    evaluation_role: str
    observable_frames: object


@dataclass(frozen=True, slots=True)
class DuplicateAuditResult:
    status: str
    raw_case_count: int
    unique_observable_count: int
    effective_case_count: int
    duplicate_representation_count: int
    effective_row_indices: tuple[int, ...]
    observable_sha256_by_row: tuple[tuple[int, str], ...]
    conflicting_observable_sha256: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "raw_case_count": self.raw_case_count,
            "unique_observable_count": self.unique_observable_count,
            "effective_case_count": self.effective_case_count,
            "duplicate_representation_count": self.duplicate_representation_count,
            "effective_row_indices": list(self.effective_row_indices),
            "observable_sha256_by_row": [
                {"row_index": row_index, "observable_sha256": digest}
                for row_index, digest in self.observable_sha256_by_row
            ],
            "conflicting_observable_sha256": list(self.conflicting_observable_sha256),
        }


def _duplicate_record(value: object, *, position: int) -> DuplicateAuditRecord:
    if isinstance(value, DuplicateAuditRecord):
        record = value
    elif isinstance(value, Mapping):
        expected = {
            "row_index",
            "generator_lineage_id",
            "evaluation_role",
            "observable_frames",
        }
        if set(value) != expected:
            raise EvaluationMathError(
                f"duplicate audit row {position} must have exact keys {sorted(expected)}"
            )
        record = DuplicateAuditRecord(
            row_index=value["row_index"],  # type: ignore[arg-type]
            generator_lineage_id=value["generator_lineage_id"],  # type: ignore[arg-type]
            evaluation_role=value["evaluation_role"],  # type: ignore[arg-type]
            observable_frames=value["observable_frames"],
        )
    else:
        raise EvaluationMathError(f"duplicate audit row {position} has invalid type")
    if type(record.row_index) is not int or record.row_index < 0:
        raise EvaluationMathError("duplicate audit row_index must be a nonnegative exact int")
    if type(record.generator_lineage_id) is not str or not record.generator_lineage_id:
        raise EvaluationMathError("generator_lineage_id must be a non-empty string")
    if type(record.evaluation_role) is not str or record.evaluation_role not in ROLE_TO_TARGET:
        raise EvaluationMathError("evaluation_role must be one of the three locked roles")
    # Validate now; the digest is calculated again only from the returned exact values.
    validate_lineage_frames(record.observable_frames, source=f"duplicate row {record.row_index}")
    return record


def audit_observable_duplicates(values: Iterable[object]) -> DuplicateAuditResult:
    records = tuple(_duplicate_record(value, position=index) for index, value in enumerate(values))
    if not records:
        raise EvaluationMathError("duplicate audit requires at least one row")
    row_indices = [record.row_index for record in records]
    if len(row_indices) != len(set(row_indices)):
        raise EvaluationMathError("duplicate audit row_index values must be unique")

    by_digest: dict[str, list[DuplicateAuditRecord]] = {}
    digests_by_row: list[tuple[int, str]] = []
    for record in records:
        digest = observable_identity_sha256(record.observable_frames)
        by_digest.setdefault(digest, []).append(record)
        digests_by_row.append((record.row_index, digest))

    aliasing = tuple(
        sorted(
            digest
            for digest, group in by_digest.items()
            if len({record.evaluation_role for record in group}) > 1
        )
    )
    overlap = tuple(
        sorted(
            digest
            for digest, group in by_digest.items()
            if len({record.generator_lineage_id for record in group}) > 1
        )
    )
    if aliasing:
        status = "INVALID_OBSERVATIONAL_ALIASING"
        conflicts = aliasing
        effective_indices: tuple[int, ...] = ()
    elif overlap:
        status = "INVALID_GENERATOR_LINEAGE_OVERLAP"
        conflicts = overlap
        effective_indices = ()
    else:
        status = "VALID_DUPLICATE_AUDIT"
        conflicts = ()
        effective_indices = tuple(
            sorted(min(record.row_index for record in group) for group in by_digest.values())
        )
    return DuplicateAuditResult(
        status=status,
        raw_case_count=len(records),
        unique_observable_count=len(by_digest),
        effective_case_count=len(effective_indices),
        duplicate_representation_count=len(records) - len(by_digest),
        effective_row_indices=effective_indices,
        observable_sha256_by_row=tuple(sorted(digests_by_row)),
        conflicting_observable_sha256=conflicts,
    )


_FAILURE_EXPECTED: Mapping[str, str] = MappingProxyType(
    {
        "balanced_fixture": "EVALUATOR_OPERABLE",
        "injected_false_crown": "DETECTED_FALSE_CROWN",
        "always_hold": "INVALID_ALWAYS_HOLD",
        "always_crown": "INVALID_ALWAYS_CROWN",
        "always_resist": "INVALID_ALWAYS_RESIST",
        "constant_primary_score": "INVALID_CONSTANT_PRIMARY_SCORE",
    }
)


def constant_prediction_guard(predictions: Iterable[object]) -> str | None:
    """Production guard for constant trinary controls and accidental collapse."""

    checked = tuple(predictions)
    if not checked or any(type(value) is not int or value not in TRINARY_VALUES for value in checked):
        raise EvaluationMathError("constant guard requires exact trinary predictions")
    unique = set(checked)
    if unique == {0}:
        return "INVALID_ALWAYS_HOLD"
    if unique == {1}:
        return "INVALID_ALWAYS_CROWN"
    if unique == {-1}:
        return "INVALID_ALWAYS_RESIST"
    return None


def primary_score_guard(scores: Iterable[object]) -> str:
    """Production guard that prevents a constant primary score from passing."""

    checked: list[float] = []
    for value in scores:
        if type(value) not in {int, float}:
            raise EvaluationMathError("primary score guard requires numeric scores")
        number = float(value)
        if not 0.0 <= number <= 1.0:
            raise EvaluationMathError("primary score guard requires unit scores")
        checked.append(0.0 if number == 0.0 else number)
    if not checked:
        raise EvaluationMathError("primary score guard requires scores")
    return (
        "INVALID_CONSTANT_PRIMARY_SCORE"
        if len({value.hex() for value in checked}) == 1
        else "VARIABLE_PRIMARY_SCORE"
    )


def false_crown_guard(metrics: MetricResult) -> str:
    """Production diagnostic proving that a trap crown cannot remain invisible."""

    if not isinstance(metrics, MetricResult):
        raise EvaluationMathError("false-crown guard requires MetricResult")
    return "DETECTED_FALSE_CROWN" if metrics.trap_crown_count > 0 else "NO_FALSE_CROWN"


def balanced_prediction_guard(
    roles: Sequence[object], predictions: Sequence[object]
) -> str:
    """Production operability check for one correct prediction per required role."""

    if len(roles) != len(predictions):
        raise EvaluationMathError("balanced guard inputs must have equal length")
    metrics = calculate_metrics_from_predictions(roles, predictions)
    targets = tuple(ROLE_TO_TARGET.get(role) for role in roles)
    return (
        "EVALUATOR_OPERABLE"
        if (
            tuple(predictions) == targets
            and metrics.expresser_crown_count > 0
            and metrics.latent_hold_count > 0
            and metrics.trap_resist_count > 0
        )
        else "EVALUATOR_NONIDEAL_VISIBLE"
    )


def failure_capability_rows() -> tuple[dict[str, object], ...]:
    """Drive the same production guards used by the development evaluator."""

    roles = ("expresser", "latent", "trap")
    fixtures = (
        ("balanced_fixture", (1, 0, -1), (0.9, 0.5, 0.1)),
        ("injected_false_crown", (1, 0, 1), (0.9, 0.5, 0.9)),
        ("always_hold", (0, 0, 0), (0.5, 0.5, 0.5)),
        ("always_crown", (1, 1, 1), (0.9, 0.9, 0.9)),
        ("always_resist", (-1, -1, -1), (0.1, 0.1, 0.1)),
        ("constant_primary_score", (1, 0, -1), (0.5, 0.5, 0.5)),
    )
    rows: list[dict[str, object]] = []
    for fixture_name, predictions, scores in fixtures:
        metrics = calculate_metrics_from_predictions(roles, predictions)
        constant_status = constant_prediction_guard(predictions)
        if constant_status is not None:
            observed = constant_status
        elif primary_score_guard(scores) == "INVALID_CONSTANT_PRIMARY_SCORE":
            observed = "INVALID_CONSTANT_PRIMARY_SCORE"
        elif false_crown_guard(metrics) == "DETECTED_FALSE_CROWN":
            observed = "DETECTED_FALSE_CROWN"
        else:
            observed = balanced_prediction_guard(roles, predictions)
        expected = _FAILURE_EXPECTED[fixture_name]
        rows.append(
            {
                "fixture_name": fixture_name,
                "expected_status": expected,
                "observed_status": observed,
                "trap_crown_count": metrics.trap_crown_count,
                "passed": observed == expected,
            }
        )
    return tuple(rows)


def failure_capability_passed(rows: Iterable[Mapping[str, object]] | None = None) -> bool:
    checked = failure_capability_rows() if rows is None else tuple(rows)
    if len(checked) != len(_FAILURE_EXPECTED):
        return False
    seen: set[str] = set()
    for row in checked:
        if set(row) != {
            "fixture_name",
            "expected_status",
            "observed_status",
            "trap_crown_count",
            "passed",
        }:
            return False
        name = row["fixture_name"]
        if type(name) is not str or name in seen or name not in _FAILURE_EXPECTED:
            return False
        seen.add(name)
        expected = _FAILURE_EXPECTED[name]
        if (
            row["expected_status"] != expected
            or row["observed_status"] != expected
            or row["passed"] is not True
        ):
            return False
        if name == "injected_false_crown" and row["trap_crown_count"] != 1:
            return False
    return seen == set(_FAILURE_EXPECTED)
