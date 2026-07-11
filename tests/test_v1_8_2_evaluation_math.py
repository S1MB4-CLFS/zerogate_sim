from __future__ import annotations

import ast
from dataclasses import replace
import math
from pathlib import Path

import pytest

import zerogate_sim.v1_8_2_cluster_bootstrap as bootstrap_module
import zerogate_sim.v1_8_2_metrics as metrics_module
import zerogate_sim.v1_8_2_nested_selection as nested_module
import zerogate_sim.v1_8_2_score_registry as registry_module
from zerogate_sim.v1_8_lineage_schema import LineageSchemaError
from zerogate_sim.v1_8_2_cluster_bootstrap import (
    BOOTSTRAP_LOWER_INDEX,
    BOOTSTRAP_UPPER_INDEX,
    bootstrap_replicates,
    cluster_draw_index,
    cluster_draw_indices,
    cluster_percentile_interval,
    paired_cluster_difference_interval,
    percentile_indices,
)
from zerogate_sim.v1_8_2_metrics import (
    AggregateMetrics,
    DuplicateAuditRecord,
    INVALID_DEAD_SAFE_NO_CROWNS,
    INVALID_MISSING_REQUIRED_ROLE,
    VALID_METRICS,
    aggregate_lineage_metrics,
    audit_observable_duplicates,
    balanced_prediction_guard,
    calculate_metrics,
    constant_prediction_guard,
    failure_capability_passed,
    failure_capability_rows,
    false_crown_guard,
    model_comparison_tuple,
    observable_identity_sha256,
    primary_score_guard,
    primary_strictly_better,
)
from zerogate_sim.v1_8_2_nested_selection import (
    INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR,
    VALID_NESTED_SELECTION,
    ScoredCase,
    evaluate_ablation_frozen,
    evaluate_ablation_retuned,
    frozen_and_retuned_ablation_comparison,
    nested_logo_select,
    observed_boundary_margin,
    select_threshold_option,
    selection_sort_key,
)
from zerogate_sim.v1_8_2_score_registry import (
    CONSTANT_MODEL_IDS,
    CONTINUOUS_MODEL_IDS,
    MODEL_IDS,
    THRESHOLD_OPTIONS,
    EvaluationMathError,
    classify_score,
    prediction_cube_rows,
    score_model,
    score_registry_rows,
)
from zerogate_sim.v1_8_2_threshold_contract import (
    EvaluationMathError as NeutralEvaluationMathError,
    ThresholdOption as NeutralThresholdOption,
    classify_score as neutral_classify_score,
    threshold_option as neutral_threshold_option,
)


def _frame(
    *,
    strength: float,
    distinction: float,
    polarity: float,
    relation: float,
    return_observed: float,
    observed_stability_score: float,
    echo_mimic_score: float,
) -> dict[str, float]:
    return {
        "strength": strength,
        "distinction": distinction,
        "polarity": polarity,
        "relation": relation,
        "return_observed": return_observed,
        "observed_stability_score": observed_stability_score,
        "echo_mimic_score": echo_mimic_score,
    }


def _formula_frames() -> tuple[dict[str, float], ...]:
    return (
        _frame(
            strength=0.91,
            distinction=0.81,
            polarity=0.71,
            relation=0.61,
            return_observed=0.51,
            observed_stability_score=0.41,
            echo_mimic_score=0.21,
        ),
        _frame(
            strength=0.32,
            distinction=0.82,
            polarity=0.72,
            relation=0.62,
            return_observed=0.52,
            observed_stability_score=0.92,
            echo_mimic_score=0.12,
        ),
        _frame(
            strength=0.83,
            distinction=0.53,
            polarity=0.63,
            relation=0.73,
            return_observed=0.83,
            observed_stability_score=0.93,
            echo_mimic_score=0.23,
        ),
    )


def _uniform_frames(value: float) -> tuple[dict[str, float], ...]:
    return tuple(
        _frame(
            strength=value,
            distinction=value,
            polarity=value,
            relation=value,
            return_observed=value,
            observed_stability_score=value,
            echo_mimic_score=1.0 - value,
        )
        for _ in range(3)
    )


def test_threshold_contract_is_neutral_and_score_registry_reexports_public_api() -> None:
    assert registry_module.EvaluationMathError is NeutralEvaluationMathError
    assert registry_module.ThresholdOption is NeutralThresholdOption
    assert registry_module.classify_score is neutral_classify_score
    assert registry_module.threshold_option is neutral_threshold_option


@pytest.mark.parametrize(
    "module",
    (metrics_module, nested_module, bootstrap_module),
)
def test_evaluation_math_import_graph_has_no_predictor_or_registry_dependency(module) -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    forbidden = {
        "zerogate_sim.v1_8_2_score_registry",
        "zerogate_sim.v1_8_lineage_predictor",
        "zerogate_sim.v1_8_predictor_package",
    }
    assert imported.isdisjoint(forbidden)


def test_all_twelve_locked_model_formulas_are_literal() -> None:
    frames = _formula_frames()
    expected = {
        "primary_prior_touch": 0.41,
        "no_prior_touch_support": 0.53,
        "no_echo_guard": 0.41,
        "strength_only": 0.83,
        "four_gate_minimum": 0.52,
        "four_gate_mean": 0.67,
        "return_only": 0.52,
        "observed_stability_only": 0.92,
        "echo_guarded_gate_minimum": 0.52,
        "always_hold": 0,
        "always_crown": 1,
        "always_resist": -1,
    }
    assert len(MODEL_IDS) == 12
    assert set(MODEL_IDS) == set(expected)
    for model_id, value in expected.items():
        assert score_model(frames, model_id) == pytest.approx(value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("strength", 0.17),
        ("distinction", 0.17),
        ("polarity", 0.17),
        ("relation", 0.17),
        ("return_observed", 0.17),
        ("observed_stability_score", 0.17),
        ("echo_mimic_score", 0.83),
    ],
)
def test_primary_formula_uses_each_owned_pressure_input(field: str, value: float) -> None:
    frames = [dict(frame) for frame in _uniform_frames(0.9)]
    for frame in frames:
        frame[field] = value
    assert score_model(tuple(frames), "primary_prior_touch") == pytest.approx(0.17)


def test_registry_and_cube_are_semantic_free_exact_and_deterministic() -> None:
    frames = _formula_frames()
    registry = score_registry_rows(frames)
    cube = prediction_cube_rows(frames)
    assert len(registry) == 9
    assert tuple(row["model_id"] for row in registry) == CONTINUOUS_MODEL_IDS
    assert all(set(row) == {"model_id", "score"} for row in registry)
    assert len(cube) == 30
    assert all(
        set(row) == {"model_id", "option_id", "score", "proposed_trinary"}
        for row in cube
    )
    assert sum(row["model_id"] in CONTINUOUS_MODEL_IDS for row in cube) == 27
    constants = tuple(row for row in cube if row["model_id"] in CONSTANT_MODEL_IDS)
    assert len(constants) == 3
    assert all(row["option_id"] == "constant" and row["score"] is None for row in constants)
    assert registry == score_registry_rows(frames)
    assert cube == prediction_cube_rows(frames)
    forbidden = {
        "row_index",
        "blind_case_id",
        "generator_lineage_id",
        "evaluation_role",
        "role",
        "label",
        "target",
    }
    assert all(not (set(row) & forbidden) for row in (*registry, *cube))


@pytest.mark.parametrize("option", THRESHOLD_OPTIONS)
def test_threshold_boundaries_are_inclusive_resist_and_crown_strict_between(option) -> None:
    assert classify_score(option.resist_max, option) == -1
    assert classify_score(math.nextafter(option.resist_max, 1.0), option) == 0
    assert classify_score(math.nextafter(option.crown_min, 0.0), option) == 0
    assert classify_score(option.crown_min, option) == 1


@pytest.mark.parametrize("bad", [True, "0.5", None, math.nan, math.inf, -0.1, 1.1])
def test_threshold_score_numeric_contract_fails_closed(bad: object) -> None:
    with pytest.raises(EvaluationMathError):
        classify_score(bad, "medium_hold")


def test_scorers_accept_only_exact_three_frame_numeric_observables() -> None:
    frame = _formula_frames()[0]
    with pytest.raises(LineageSchemaError):
        score_registry_rows({"observable_frames": _formula_frames(), "role": "expresser"})
    extra = dict(frame, truth_role=1)
    with pytest.raises(LineageSchemaError):
        prediction_cube_rows((extra, frame, frame))
    boolean = dict(frame, strength=True)
    with pytest.raises(LineageSchemaError):
        score_model((boolean, frame, frame), "always_hold")
    with pytest.raises(EvaluationMathError):
        score_model(_formula_frames(), "unknown")


def test_exact_metric_definitions_and_denominators() -> None:
    metrics = calculate_metrics(
        [
            *(('expresser', prediction) for prediction in (1, 1, 0, -1)),
            *(('latent', prediction) for prediction in (0, 0, 1, -1)),
            *(('trap', prediction) for prediction in (-1, -1, 0, 1)),
        ]
    )
    assert metrics.status == VALID_METRICS
    assert metrics.effective_case_count == 12
    assert metrics.role_denominators == {"expresser": 4, "latent": 4, "trap": 4}
    assert metrics.crown_denominator == 4
    assert metrics.crown_precision == 0.5
    assert metrics.expresser_crown_recall == 0.5
    assert metrics.expresser_resist_rate == 0.25
    assert metrics.latent_crown_rate == 0.25
    assert metrics.latent_hold_recall == 0.5
    assert metrics.trap_crown_rate == 0.25
    assert metrics.trap_resist_recall == 0.5
    assert metrics.nonlatent_hold_rate == 0.25
    assert metrics.macro_recall == 0.5
    assert metrics.fold_minimum_guardrail == 0.5


def test_metric_undefined_denominators_and_dead_safe_no_crowns_are_invalid() -> None:
    missing = calculate_metrics((role, prediction) for role, prediction in (
        ("expresser", 1),
        ("latent", 0),
    ))
    assert missing.status == INVALID_MISSING_REQUIRED_ROLE
    assert missing.fold_minimum_guardrail is None

    dead_safe = calculate_metrics(
        (("expresser", 0), ("latent", 0), ("trap", -1))
    )
    assert dead_safe.status == INVALID_DEAD_SAFE_NO_CROWNS
    assert dead_safe.crown_precision is None
    assert dead_safe.expresser_crown_recall == 0.0


def test_lineage_aggregation_is_unweighted_macro_and_comparison_is_exact() -> None:
    mixed = calculate_metrics(
        [
            *(('expresser', prediction) for prediction in (1, 1, 0, -1)),
            *(('latent', prediction) for prediction in (0, 0, 1, -1)),
            *(('trap', prediction) for prediction in (-1, -1, 0, 1)),
        ]
    )
    perfect = calculate_metrics((
        ("expresser", 1),
        ("latent", 0),
        ("trap", -1),
    ))
    aggregate = aggregate_lineage_metrics({"z": perfect, "a": mixed})
    assert aggregate == AggregateMetrics(
        lineage_count=2,
        worst_fold_minimum_guardrail=0.5,
        mean_fold_minimum_guardrail=0.75,
        worst_fold_trap_crown_rate=0.25,
        macro_latent_crown_rate=0.125,
        macro_expresser_resist_rate=0.125,
        worst_fold_macro_recall=0.5,
        macro_nonlatent_hold_rate=0.125,
    )
    assert model_comparison_tuple(aggregate) == (
        0.5,
        0.75,
        -0.25,
        -0.125,
        -0.125,
        0.5,
        -0.125,
    )
    better = replace(aggregate, worst_fold_minimum_guardrail=math.nextafter(0.5, 1.0))
    assert primary_strictly_better(better, aggregate) is True
    assert primary_strictly_better(aggregate, aggregate) is False


def test_observable_duplicate_audit_deduplicates_only_same_lineage_same_role() -> None:
    first = _formula_frames()
    second = _uniform_frames(0.4)
    audit = audit_observable_duplicates(
        (
            DuplicateAuditRecord(3, "lineage_a", "expresser", first),
            DuplicateAuditRecord(1, "lineage_a", "expresser", first),
            DuplicateAuditRecord(2, "lineage_a", "latent", second),
        )
    )
    assert audit.status == "VALID_DUPLICATE_AUDIT"
    assert audit.raw_case_count == 3
    assert audit.unique_observable_count == 2
    assert audit.duplicate_representation_count == 1
    assert audit.effective_row_indices == (1, 2)
    assert audit.effective_case_count == 2


def test_duplicate_audit_rejects_conflicting_labels_before_cross_lineage_overlap() -> None:
    frames = _formula_frames()
    aliasing = audit_observable_duplicates(
        (
            DuplicateAuditRecord(0, "lineage_a", "expresser", frames),
            DuplicateAuditRecord(1, "lineage_b", "trap", frames),
        )
    )
    assert aliasing.status == "INVALID_OBSERVATIONAL_ALIASING"
    assert aliasing.effective_row_indices == ()

    overlap = audit_observable_duplicates(
        (
            DuplicateAuditRecord(0, "lineage_a", "expresser", frames),
            DuplicateAuditRecord(1, "lineage_b", "expresser", frames),
        )
    )
    assert overlap.status == "INVALID_GENERATOR_LINEAGE_OVERLAP"
    assert overlap.effective_case_count == 0


def test_observable_identity_uses_values_only_and_is_mapping_order_invariant() -> None:
    frames = _formula_frames()
    reversed_frames = tuple(dict(reversed(tuple(frame.items()))) for frame in frames)
    assert observable_identity_sha256(frames) == observable_identity_sha256(reversed_frames)
    changed = tuple(dict(frame) for frame in frames)
    changed[0]["strength"] = math.nextafter(changed[0]["strength"], 0.0)
    assert observable_identity_sha256(frames) != observable_identity_sha256(changed)


def test_all_six_failure_capability_fixtures_are_exact_and_tamper_sensitive() -> None:
    rows = failure_capability_rows()
    assert tuple(row["fixture_name"] for row in rows) == (
        "balanced_fixture",
        "injected_false_crown",
        "always_hold",
        "always_crown",
        "always_resist",
        "constant_primary_score",
    )
    assert failure_capability_passed(rows) is True
    false_crown = next(row for row in rows if row["fixture_name"] == "injected_false_crown")
    assert false_crown["trap_crown_count"] == 1
    tampered = [dict(row) for row in rows]
    tampered[1]["trap_crown_count"] = 0
    assert failure_capability_passed(tampered) is False


def test_failure_capability_drives_shared_production_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    originals = {
        "constant_prediction_guard": metrics_module.constant_prediction_guard,
        "primary_score_guard": metrics_module.primary_score_guard,
        "false_crown_guard": metrics_module.false_crown_guard,
        "balanced_prediction_guard": metrics_module.balanced_prediction_guard,
    }
    calls = {name: 0 for name in originals}

    for name, original in originals.items():
        def wrapper(*args: object, _name: str = name, _original: object = original) -> object:
            calls[_name] += 1
            return _original(*args)  # type: ignore[operator]

        monkeypatch.setattr(metrics_module, name, wrapper)

    assert metrics_module.failure_capability_passed(
        metrics_module.failure_capability_rows()
    )
    assert calls == {
        "constant_prediction_guard": 6,
        "primary_score_guard": 3,
        "false_crown_guard": 2,
        "balanced_prediction_guard": 1,
    }


def test_shared_production_guards_expose_constants_false_crowns_and_operability() -> None:
    assert constant_prediction_guard((0, 0, 0)) == "INVALID_ALWAYS_HOLD"
    assert constant_prediction_guard((1, 1, 1)) == "INVALID_ALWAYS_CROWN"
    assert constant_prediction_guard((-1, -1, -1)) == "INVALID_ALWAYS_RESIST"
    assert constant_prediction_guard((1, 0, -1)) is None
    assert primary_score_guard((0.5, 0.5, 0.5)) == "INVALID_CONSTANT_PRIMARY_SCORE"
    assert primary_score_guard((0.9, 0.5, 0.1)) == "VARIABLE_PRIMARY_SCORE"
    injected = calculate_metrics((("expresser", 1), ("latent", 0), ("trap", 1)))
    assert false_crown_guard(injected) == "DETECTED_FALSE_CROWN"
    assert balanced_prediction_guard(
        ("expresser", "latent", "trap"), (1, 0, -1)
    ) == "EVALUATOR_OPERABLE"


def test_exact_sha256_cluster_draw_prefix_and_locked_percentile_indices() -> None:
    assert cluster_draw_indices(4, 0) == (0, 3, 0, 3)
    assert cluster_draw_indices(4, 1) == (2, 0, 1, 0)
    assert cluster_draw_index(4, 0, 0) == 0
    assert percentile_indices() == (49, 1950)
    assert BOOTSTRAP_LOWER_INDEX == 49
    assert BOOTSTRAP_UPPER_INDEX == 1950


def test_cluster_bootstrap_is_deterministic_order_invariant_and_lineage_only() -> None:
    values = {"a": 0.0, "b": 1.0, "c": 2.0, "d": 3.0}
    replicates = bootstrap_replicates(values, resamples=3)
    assert replicates[:2] == (1.5, 0.75)
    assert replicates == bootstrap_replicates(dict(reversed(tuple(values.items()))), resamples=3)
    constant = cluster_percentile_interval(
        {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    )
    assert constant.lower_index == 49
    assert constant.upper_index == 1950
    assert constant.lower == constant.upper == constant.observed_mean == 0.25


def test_paired_bootstrap_uses_identical_lineage_draws() -> None:
    primary = {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
    comparator = {"a": 0.4, "b": 0.3, "c": 0.2, "d": 0.1}
    interval = paired_cluster_difference_interval(primary, comparator)
    assert interval.observed_mean == pytest.approx(0.5)
    assert interval.lower == pytest.approx(0.5)
    assert interval.upper == pytest.approx(0.5)
    with pytest.raises(EvaluationMathError, match="identical lineage"):
        paired_cluster_difference_interval(primary, {"a": 0.4})


def _development_cases(
    *, latent_score: float = 0.5, expresser_score: float = 0.9, trap_score: float = 0.1
) -> tuple[ScoredCase, ...]:
    return tuple(
        ScoredCase(lineage_id, role, score)
        for lineage_id in ("lineage_d", "lineage_b", "lineage_a", "lineage_c")
        for role, score in (
            ("expresser", expresser_score),
            ("latent", latent_score),
            ("trap", trap_score),
        )
    )


def test_nested_logo_selects_on_remaining_lineages_then_freezes_oof() -> None:
    cases = _development_cases()
    result = nested_logo_select(cases)
    assert result.status == VALID_NESTED_SELECTION
    assert tuple(fold.held_lineage_id for fold in result.outer_folds) == (
        "lineage_a",
        "lineage_b",
        "lineage_c",
        "lineage_d",
    )
    assert all(fold.selected_option_id == "medium_hold" for fold in result.outer_folds)
    assert result.selected_option_id == "medium_hold"
    assert result.outer_option_by_lineage == {
        "lineage_a": "medium_hold",
        "lineage_b": "medium_hold",
        "lineage_c": "medium_hold",
        "lineage_d": "medium_hold",
    }
    assert result.oof_metrics.worst_fold_minimum_guardrail == 1.0
    assert len(result.oof_predictions) == len(cases)
    assert result.to_dict()["oof_predictions_frozen_before_full_selection"] is True


def test_nested_selection_is_row_permutation_deterministic() -> None:
    cases = _development_cases()
    forward = nested_logo_select(cases)
    reverse = nested_logo_select(reversed(cases))
    assert forward == reverse
    assert select_threshold_option(cases) == select_threshold_option(reversed(cases))


def test_boundary_margin_is_minimum_over_all_training_rows() -> None:
    cases = _development_cases()
    assert observed_boundary_margin(cases, "wide_hold") == pytest.approx(0.1)
    assert observed_boundary_margin(cases, "medium_hold") == pytest.approx(0.2)
    assert observed_boundary_margin(cases, "narrow_hold") == pytest.approx(0.1)


@pytest.mark.parametrize("tier", range(9))
def test_every_lexicographic_selection_tier_dominates_all_later_tiers(tier: int) -> None:
    fields = (
        ("worst_fold_minimum_guardrail", True),
        ("mean_fold_minimum_guardrail", True),
        ("worst_fold_trap_crown_rate", False),
        ("macro_latent_crown_rate", False),
        ("macro_expresser_resist_rate", False),
        ("worst_fold_macro_recall", True),
        ("macro_nonlatent_hold_rate", False),
    )
    a_values = {field: 0.5 for field, _ in fields}
    b_values = dict(a_values)
    a_margin = b_margin = 0.5
    a_option = b_option = "wide_hold"

    for index in range(tier + 1, 8):
        if index == 7:
            a_margin, b_margin = 0.0, 1.0
        else:
            field, beneficial = fields[index]
            a_values[field], b_values[field] = ((0.0, 1.0) if beneficial else (1.0, 0.0))
    if tier < 7:
        field, beneficial = fields[tier]
        a_values[field], b_values[field] = ((0.6, 0.5) if beneficial else (0.4, 0.5))
    elif tier == 7:
        a_margin, b_margin = 0.6, 0.5
    else:
        a_option, b_option = "medium_hold", "wide_hold"

    a = AggregateMetrics(lineage_count=4, **a_values)
    b = AggregateMetrics(lineage_count=4, **b_values)
    assert selection_sort_key(a, a_margin, a_option) < selection_sort_key(
        b, b_margin, b_option
    )


def test_nested_logo_refuses_too_few_lineages_and_all_dead_safe_options() -> None:
    with pytest.raises(EvaluationMathError, match="HOLD_INSUFFICIENT"):
        nested_logo_select(_development_cases()[:9])
    with pytest.raises(EvaluationMathError, match="no valid locked threshold"):
        nested_logo_select(
            _development_cases(expresser_score=0.5, latent_score=0.5, trap_score=0.1)
        )


def test_frozen_and_retuned_ablation_helpers_require_strict_superiority() -> None:
    primary = nested_logo_select(_development_cases())
    ablation_cases = _development_cases(latent_score=0.85)
    frozen = evaluate_ablation_frozen(primary, ablation_cases)
    retuned = evaluate_ablation_retuned(ablation_cases)
    assert frozen.status == VALID_NESTED_SELECTION
    assert retuned.status == VALID_NESTED_SELECTION
    assert frozen.outer_option_by_lineage == tuple(sorted(primary.outer_option_by_lineage.items()))

    comparison = frozen_and_retuned_ablation_comparison(primary, ablation_cases)
    assert comparison["primary_strictly_better_frozen"] is True
    assert comparison["primary_strictly_better_retuned"] is True
    assert comparison["necessity_requirement_passed"] is True

    equivalent = frozen_and_retuned_ablation_comparison(primary, _development_cases())
    assert equivalent["primary_strictly_better_frozen"] is False
    assert equivalent["primary_strictly_better_retuned"] is False
    assert equivalent["necessity_requirement_passed"] is False


def test_oof_dead_safe_result_carries_invalid_status_instead_of_passing() -> None:
    primary = nested_logo_select(_development_cases())
    frozen = evaluate_ablation_frozen(
        primary,
        _development_cases(expresser_score=0.5, latent_score=0.5, trap_score=0.1),
    )
    assert frozen.status == INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR
