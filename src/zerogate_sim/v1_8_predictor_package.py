from __future__ import annotations

import csv
import io
import math
import os
import re
import sys
import threading
from types import ModuleType
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping

from zerogate_sim.v1_8_lineage_predictor import (
    FORMULA_ID,
    PREDICTOR_ID,
    LineageScore,
    lineage_predictor,
    predictor_config_document,
)
from zerogate_sim.v1_8_lineage_schema import (
    FRAME_NAMES,
    OBSERVABLE_FIELDS,
    SCHEMA_ID,
    VERSION,
    LineageSchemaError,
    canonical_json,
    immutable_lineage_frames,
    lineage_schema_sha256,
    read_lineage_inputs_bytes,
    sha256_bytes,
    stable_sha256,
    strict_json_loads,
)

PACKAGE_CONTRACT_ID = "zerogate-v1.8.1-lineage-predictor-package-v1"
DEVELOPMENT_PLAN_ID = "zerogate-v1.8.1-development-plan-lock-v1"
SOURCE_MANIFEST_ID = "zerogate-v1.8.1-lineage-source-manifest-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")

# This is deliberately the complete local code/config dependency surface for
# the packaged scorer. Standard-library modules are outside the repository
# contract. The package verifier accepts no caller-supplied expansion.
PACKAGE_FILE_ALLOWLIST = (
    "src/zerogate_sim/v1_8_observable_schema.py",
    "src/zerogate_sim/v1_8_lineage_schema.py",
    "src/zerogate_sim/v1_8_lineage_predictor.py",
    "src/zerogate_sim/v1_8_predictor_package.py",
    "contracts/v1_8_1_lineage_predictor.json",
    "contracts/v1_8_1_development_plan_lock.json",
)

SCORE_HEADER = (
    "row_index",
    "early_owned_pressure",
    "witness_owned_pressure",
    "late_owned_pressure",
    "lineage_support",
    "lineage_score",
    "no_lineage_score",
    "lineage_delta",
)

SCORE_FILES = {
    "scores": Path("v1_8_1_frozen_development_scores.csv"),
    "manifest": Path("v1_8_1_score_freeze_manifest.json"),
    "receipt": Path("v1_8_1_score_freeze_receipt.json"),
}


@dataclass(frozen=True, slots=True)
class PackageFileRecord:
    relative_path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class VerifiedPredictorPackage:
    contract_sha256: str
    files: tuple[PackageFileRecord, ...]
    schema_sha256: str
    predictor_config_sha256: str
    development_plan_sha256: str

    def to_manifest(self) -> dict[str, object]:
        return {
            "version": VERSION,
            "contract_id": PACKAGE_CONTRACT_ID,
            "contract_sha256": self.contract_sha256,
            "schema_id": SCHEMA_ID,
            "schema_sha256": self.schema_sha256,
            "predictor_id": PREDICTOR_ID,
            "formula_id": FORMULA_ID,
            "predictor_config_sha256": self.predictor_config_sha256,
            "development_plan_sha256": self.development_plan_sha256,
            "file_allowlist": [record.to_dict() for record in self.files],
            "predictor_execution_code_and_configuration_binding_verified": True,
            "predictor_execution_loaded_from_verified_source_snapshot": True,
            "verifier_coordinator_trusted_as_invoked": True,
            "in_process_execution_is_os_sandboxed": False,
        }


@dataclass(frozen=True, slots=True)
class _VerifiedState:
    package: VerifiedPredictorPackage
    snapshots: tuple[tuple[str, bytes], ...]
    runtime: _VerifiedRuntime


@dataclass(frozen=True, slots=True)
class _VerifiedRuntime:
    lineage_predictor: Callable[[object], object]
    immutable_lineage_frames: Callable[..., object]
    predictor_config_document: Callable[[], dict[str, object]]
    owned_pressure: Callable[[Mapping[str, object]], float]
    lineage_schema_sha256: Callable[[], str]
    predictor_id: str
    formula_id: str
    schema_id: str
    version: str


_RUNTIME_LOAD_LOCK = threading.RLock()
_RUNTIME_MODULES = (
    (
        "zerogate_sim.v1_8_observable_schema",
        "src/zerogate_sim/v1_8_observable_schema.py",
    ),
    (
        "zerogate_sim.v1_8_lineage_schema",
        "src/zerogate_sim/v1_8_lineage_schema.py",
    ),
    (
        "zerogate_sim.v1_8_lineage_predictor",
        "src/zerogate_sim/v1_8_lineage_predictor.py",
    ),
)


def development_plan_document() -> dict[str, object]:
    """Return the exact v1.8.2 development method without selecting an option."""

    canaries = [
        {
            "name": "sustained",
            "owned_pressure_path": [0.8, 0.8, 0.8],
            "required_lineage_score": 0.8,
            "required_no_lineage_score": 0.8,
        },
        {
            "name": "late_spike",
            "owned_pressure_path": [0.2, 0.2, 0.9],
            "required_lineage_score": 0.2,
            "required_no_lineage_score": 0.9,
        },
        {
            "name": "matured",
            "owned_pressure_path": [0.2, 0.8, 0.9],
            "required_lineage_score": 0.8,
            "required_no_lineage_score": 0.9,
        },
        {
            "name": "collapsed",
            "owned_pressure_path": [0.9, 0.8, 0.2],
            "required_lineage_score": 0.2,
            "required_no_lineage_score": 0.2,
        },
        {
            "name": "dormant_reappearance",
            "owned_pressure_path": [0.9, 0.0, 0.9],
            "required_lineage_score": 0.9,
            "required_no_lineage_score": 0.9,
        },
    ]
    formula_input_canaries = [
        {"field": field, "value": 0.17, "required_owned_pressure": 0.17}
        for field in (
            "strength",
            "distinction",
            "polarity",
            "relation",
            "return_observed",
            "observed_stability_score",
        )
    ] + [
        {
            "field": "echo_mimic_score",
            "value": 0.83,
            "required_owned_pressure": 0.17,
        }
    ]
    return {
        "version": VERSION,
        "plan_id": DEVELOPMENT_PLAN_ID,
        "scope": "v1_8_2_controlled_synthetic_development_selection_only",
        "predictor_id": PREDICTOR_ID,
        "formula_id": FORMULA_ID,
        "formula_semantics": "prior_touch_support_not_continuous_persistence",
        "score_output": "continuous_only_in_v1_8_1",
        "threshold_options": [
            {"option_id": "wide_hold", "resist_max": 0.2, "crown_min": 0.8},
            {"option_id": "medium_hold", "resist_max": 0.3, "crown_min": 0.7},
            {"option_id": "narrow_hold", "resist_max": 0.4, "crown_min": 0.6},
        ],
        "threshold_boundary_semantics": {
            "resist": "score <= resist_max",
            "hold": "resist_max < score < crown_min",
            "crown": "score >= crown_min",
        },
        "score_registry": {
            "primary_prior_touch": {
                "frame_score": "min(strength,distinction,polarity,relation,return_observed,observed_stability_score,1-echo_mimic_score)",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "no_prior_touch_support": {
                "frame_score": "same_as_primary_prior_touch",
                "temporal_aggregation": "late",
            },
            "no_echo_guard": {
                "frame_score": "min(strength,distinction,polarity,relation,return_observed,observed_stability_score)",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "strength_only": {
                "frame_score": "strength",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "four_gate_minimum": {
                "frame_score": "min(distinction,polarity,relation,return_observed)",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "four_gate_mean": {
                "frame_score": "(distinction+polarity+relation+return_observed)/4",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "return_only": {
                "frame_score": "return_observed",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "observed_stability_only": {
                "frame_score": "observed_stability_score",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "echo_guarded_gate_minimum": {
                "frame_score": "min(distinction,polarity,relation,return_observed,1-echo_mimic_score)",
                "temporal_aggregation": "min(late,max(early,witness))",
            },
            "always_hold": {"constant_prediction": 0},
            "always_crown": {"constant_prediction": 1},
            "always_resist": {"constant_prediction": -1},
        },
        "selected_threshold_option": None,
        "scientific_thresholds_selected": False,
        "trinary_predictions_emitted": False,
        "target_data_access_policy": "v1_8_3_and_later_forbidden",
        "identifier_fields_in_callback": False,
        "frozen_holdout_access_policy": "forbidden",
        "development_data_contract": {
            "source_kind": "controlled_synthetic_raw_trace_generators",
            "root_seed": 1812001,
            "generator_lineages": [
                "ar_recovery_v1",
                "impulse_response_v1",
                "coupled_oscillator_v1",
                "piecewise_hysteresis_v1",
            ],
            "minimum_generator_lineages": 4,
            "required_roles_per_lineage": ["expresser", "latent", "trap"],
            "cases_per_role_per_lineage": 12,
            "frame_windows": {
                "early": [0.1, 0.3],
                "witness": [0.45, 0.65],
                "late": [0.8, 1.0],
                "interval_semantics": "normalized_time_left_closed_right_closed",
            },
            "observable_extraction_must_not_import": [
                "labels",
                "threshold_selector",
                "v1_8_3_holdout",
            ],
            "labels_enter_only_after_raw_scores_and_threshold_options_are_frozen": True,
            "legacy_triad27_is_not_an_independent_generator_lineage": True,
        },
        "split_contract": {
            "outer": "leave_one_generator_lineage_out",
            "inner": "leave_one_remaining_generator_lineage_out",
            "random_row_splits_forbidden": True,
            "split_and_bootstrap_unit": "generator_lineage_id",
            "profile_id_is_not_an_independent_split_unit": True,
        },
        "selection_objective": [
            "maximize_worst_fold_minimum_guardrail",
            "maximize_mean_fold_minimum_guardrail",
            "minimize_worst_fold_trap_crown_rate",
            "minimize_latent_crown_rate",
            "minimize_expresser_resist_rate",
            "maximize_worst_fold_macro_recall",
            "minimize_nonlatent_hold_rate",
            "maximize_observed_score_boundary_margin",
            "lexicographic_option_id",
        ],
        "selection_calculation": {
            "candidate_set": "the_three_locked_threshold_options_only",
            "outer_oof": "for_each_held_lineage_select_on_all_other_lineages_then_predict_held_lineage",
            "inner_validation": "each_remaining_generator_lineage_is_one_validation_fold_no_row_resampling",
            "rate_aggregation": "unweighted_arithmetic_mean_of_per_generator_lineage_rates",
            "worst_fold_beneficial": "minimum_across_generator_lineages",
            "worst_fold_harmful": "maximum_across_generator_lineages",
            "observed_score_boundary_margin": "minimum_over_training_rows_of_min(abs(score-resist_max),abs(score-crown_min))",
            "option_tie_break": "ascending_option_id_ascii",
            "full_development_selection": "repeat_identical_objective_on_all_generator_lineages_after_oof_is_frozen",
            "floating_comparison": "unrounded_binary64_values_with_exact_lexicographic_comparison",
        },
        "fold_minimum_guardrail": [
            "expresser_crown_recall",
            "latent_hold_recall",
            "trap_resist_recall",
            "one_minus_trap_crown_rate",
            "one_minus_latent_crown_rate",
            "one_minus_expresser_resist_rate",
        ],
        "metric_definitions": {
            "role_to_target": {"expresser": 1, "latent": 0, "trap": -1},
            "expresser_crown_recall": "count(role=expresser,prediction=1)/count(role=expresser)",
            "latent_hold_recall": "count(role=latent,prediction=0)/count(role=latent)",
            "trap_resist_recall": "count(role=trap,prediction=-1)/count(role=trap)",
            "trap_crown_rate": "count(role=trap,prediction=1)/count(role=trap)",
            "latent_crown_rate": "count(role=latent,prediction=1)/count(role=latent)",
            "expresser_resist_rate": "count(role=expresser,prediction=-1)/count(role=expresser)",
            "macro_recall": "(expresser_crown_recall+latent_hold_recall+trap_resist_recall)/3",
            "nonlatent_hold_rate": "(count(role=expresser,prediction=0)+count(role=trap,prediction=0))/(count(role=expresser)+count(role=trap))",
            "crown_precision": "count(role=expresser,prediction=1)/count(prediction=1)",
            "zero_crown_precision_rule": "INVALID_DEAD_SAFE_NO_CROWNS",
            "fold_minimum_guardrail": "minimum_of_the_six_named_guardrail_components",
            "undefined_denominator_rule": "INVALID_MISSING_REQUIRED_ROLE",
        },
        "primary_denominators": "exact_class_specific_counts_and_generator_lineage_macro_rates",
        "uncertainty": {
            "method": "deterministic_sha256_generator_lineage_cluster_percentile_bootstrap",
            "seed": 18122001,
            "resamples": 2000,
            "confidence": 0.95,
            "row_wilson_is_descriptive_only": True,
            "sampling_algorithm": "for replicate b and slot j choose uint64_be(sha256(utf8(seed:b:j))[0:8]) modulo generator_lineage_count",
            "sample_size": "generator_lineage_count_with_replacement",
            "statistic": "unweighted_mean_of_sampled_per_lineage_metric_values",
            "paired_difference": "sample_identical_lineage_indices_then_mean(primary_metric-baseline_metric)",
            "lower_index": "floor(0.025*(resamples-1))",
            "upper_index": "ceil(0.975*(resamples-1))",
            "interval_values": "sorted_replicate_values_at_inclusive_lower_and_upper_indices",
        },
        "baselines": [
            "always_hold",
            "always_crown",
            "always_resist",
            "strength_only",
            "four_gate_minimum",
            "four_gate_mean",
            "return_only",
            "observed_stability_only",
            "echo_guarded_gate_minimum",
        ],
        "ablations": [
            "no_prior_touch_support",
            "no_echo_guard",
        ],
        "ablation_evaluation": [
            "primary_thresholds_frozen",
            "development_thresholds_retuned",
        ],
        "model_comparison_rule": {
            "tuple": [
                "worst_fold_minimum_guardrail",
                "mean_fold_minimum_guardrail",
                "negative_worst_fold_trap_crown_rate",
                "negative_macro_latent_crown_rate",
                "negative_macro_expresser_resist_rate",
                "worst_fold_macro_recall",
                "negative_macro_nonlatent_hold_rate",
            ],
            "comparison": "exact_lexicographic_higher_is_better",
            "equivalence_tolerance": 0.0,
            "baseline_or_retuned_ablation_equal_or_dominant": "HOLD_BASELINE_EQUIVALENT_OR_DOMINANT",
            "prior_touch_necessity_requires": "primary_tuple_strictly_greater_than_no_prior_touch_tuple_for_frozen_and_retuned_evaluations",
        },
        "duplicate_policy": {
            "exact_observable_duplicates_count_once_per_generator_lineage": True,
            "conflicting_labels_for_exact_observables": "INVALID_OBSERVATIONAL_ALIASING",
            "observable_identity": "sha256_of_canonical_three_frame_observable_values_excluding_ids_labels_and_groups",
            "same_observables_same_role_same_lineage": "retain_lowest_row_index_as_one_effective_case",
            "same_observables_across_generator_lineages": "INVALID_GENERATOR_LINEAGE_OVERLAP",
            "denominators_use_effective_cases_after_duplicate_audit": True,
            "development_fingerprint_manifest_required": True,
        },
        "permutation_policy": {
            "raw_scores_and_threshold_options_must_be_label_permutation_invariant": True,
            "selected_threshold_may_change_after_label_join": True,
            "identifier_and_row_permutation_equivariance_required": True,
        },
        "failure_capability_contract": {
            "injected_false_crown": "exactly_one_trap_crown_is_counted_and_status_is_DETECTED_FALSE_CROWN",
            "always_hold": "status_is_INVALID_ALWAYS_HOLD",
            "always_crown": "status_is_INVALID_ALWAYS_CROWN",
            "always_resist": "status_is_INVALID_ALWAYS_RESIST",
            "constant_primary_score": "status_is_INVALID_CONSTANT_PRIMARY_SCORE",
            "balanced_fixture": "one_correct_prediction_per_required_role_and_status_is_EVALUATOR_OPERABLE",
            "pass_rule": "all_six_fixture_requirements_hold_exactly",
        },
        "canaries": canaries,
        "formula_input_canaries": formula_input_canaries,
        "required_ablation_effect": (
            "sustained_ranks_above_late_spike_with_support_and_below_it_without_support"
        ),
        "failure_statuses": [
            "HOLD_INSUFFICIENT_GENERATOR_LINEAGES",
            "INVALID_OBSERVATIONAL_ALIASING",
            "INVALID_GENERATOR_LINEAGE_OVERLAP",
            "INVALID_ARTIFACT_OR_RECEIPT",
            "INVALID_LABEL_OR_IDENTIFIER_LEAK",
            "INVALID_NONDETERMINISTIC_SELECTION",
            "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR",
            "HOLD_BASELINE_EQUIVALENT_OR_DOMINANT",
            "HOLD_FAILURE_CAPABILITY_NOT_DEMONSTRATED",
        ],
        "v1_8_2_success_status": "READY_FOR_V1_8_3_CONTRACT_ONLY",
        "failure_rule": "any_integrity_failure_invalidates_and_any_unresolved_guardrail_holds",
        "scientific_status": "HOLD_LINEAGE_PACKAGE_DEVELOPMENT_ONLY",
    }


def _owned_pressure_frame(value: float) -> dict[str, float]:
    frame = {field: value for field in OBSERVABLE_FIELDS}
    frame["echo_mimic_score"] = 0.0
    return frame


def _execute_development_canaries(
    runtime: _VerifiedRuntime,
    plan: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    results: list[dict[str, object]] = []
    canaries = plan.get("canaries")
    if not isinstance(canaries, list):
        raise LineageSchemaError("development canary contract is malformed")
    for canary in canaries:
        if not isinstance(canary, dict):  # pragma: no cover - canonical internal contract
            raise LineageSchemaError("development canary contract is malformed")
        path = canary["owned_pressure_path"]
        if not isinstance(path, list):  # pragma: no cover - canonical internal contract
            raise LineageSchemaError("development canary path is malformed")
        score = runtime.lineage_predictor(
            runtime.immutable_lineage_frames(
                [_owned_pressure_frame(float(value)) for value in path]
            )
        )
        expected_control = float(canary["required_lineage_score"])
        expected_ablation = float(canary["required_no_lineage_score"])
        if score.lineage_score != expected_control or score.no_lineage_score != expected_ablation:
            raise LineageSchemaError(f"development canary failed: {canary['name']}")
        results.append(
            {
                "name": canary["name"],
                "lineage_score": score.lineage_score,
                "no_lineage_score": score.no_lineage_score,
                "passed": True,
            }
        )

    by_name = {str(row["name"]): row for row in results}
    if not (
        float(by_name["sustained"]["lineage_score"])
        > float(by_name["late_spike"]["lineage_score"])
        and float(by_name["sustained"]["no_lineage_score"])
        < float(by_name["late_spike"]["no_lineage_score"])
    ):
        raise LineageSchemaError("lineage ablation did not produce the required rank reversal")

    sensitivity = plan.get("formula_input_canaries")
    if not isinstance(sensitivity, list):
        raise LineageSchemaError("formula-input canary contract is malformed")
    for canary in sensitivity:
        if not isinstance(canary, dict):
            raise LineageSchemaError("formula-input canary contract is malformed")
        field = canary.get("field")
        value = canary.get("value")
        expected = canary.get("required_owned_pressure")
        if not isinstance(field, str) or type(value) not in {int, float} or type(
            expected
        ) not in {int, float}:
            raise LineageSchemaError("formula-input canary values are malformed")
        frame = _owned_pressure_frame(1.0)
        frame[field] = float(value)
        if not math.isclose(
            runtime.owned_pressure(frame),
            float(expected),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise LineageSchemaError(f"formula-input canary failed: {field}")
    return tuple(results)


def verify_development_canaries(
    repo_root: str | Path | None = None,
    *,
    expected_contract_sha256: str | None = None,
) -> tuple[dict[str, object], ...]:
    """Execute canaries through a runtime loaded from the verified source bytes."""

    root = _default_repo_root() if repo_root is None else Path(repo_root).absolute()
    state = _verify_predictor_package_state(
        root,
        expected_contract_sha256=expected_contract_sha256,
    )
    snapshot_map = dict(state.snapshots)
    plan = _canonical_config_object(
        snapshot_map["contracts/v1_8_1_development_plan_lock.json"],
        source="contracts/v1_8_1_development_plan_lock.json",
    )
    if plan != development_plan_document():
        raise LineageSchemaError("development plan does not match the implemented plan lock")
    return _execute_development_canaries(state.runtime, plan)


def _validate_expected_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise LineageSchemaError(f"{field} must be a lowercase SHA-256")
    return value


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_package_path(root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or ":" in relative_path
        or pure.as_posix() != relative_path
        or pure.is_absolute()
        or not pure.parts
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise LineageSchemaError(f"unsafe package path {relative_path!r}")

    candidate = root
    for part in pure.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise LineageSchemaError(f"package path contains a symlink: {relative_path}")
    if not candidate.is_file():
        raise LineageSchemaError(f"missing package file: {relative_path}")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise LineageSchemaError(f"package path escapes repository root: {relative_path}") from exc
    return candidate


def _snapshot_package_files(root: Path) -> tuple[tuple[str, bytes], ...]:
    if not root.is_dir() or root.is_symlink():
        raise LineageSchemaError(f"repository root is missing or unsafe: {root}")
    snapshots: list[tuple[str, bytes]] = []
    for relative_path in PACKAGE_FILE_ALLOWLIST:
        source = _safe_package_path(root, relative_path)
        data = source.read_bytes()
        if b"\r" in data:
            raise LineageSchemaError(
                f"package text must use repository-normalized LF bytes: {relative_path}"
            )
        snapshots.append((relative_path, data))
    return tuple(snapshots)


def _load_verified_runtime(snapshots: Mapping[str, bytes]) -> _VerifiedRuntime:
    """Load scorer code from the exact verified bytes, not mutable imports.

    The canonical module names are replaced only while the three snapshot
    modules execute under a process-wide lock. Returned functions retain their
    isolated globals after the normal application modules are restored.
    """

    missing = [relative for _, relative in _RUNTIME_MODULES if relative not in snapshots]
    if missing:
        raise LineageSchemaError(f"verified runtime snapshot is incomplete: {missing}")
    sentinel = object()
    previous: dict[str, object] = {}
    loaded: dict[str, ModuleType] = {}
    with _RUNTIME_LOAD_LOCK:
        try:
            for module_name, relative_path in _RUNTIME_MODULES:
                previous[module_name] = sys.modules.get(module_name, sentinel)
                # Insert the module before execution because dataclasses and
                # absolute imports consult sys.modules during class creation.
                module = ModuleType(module_name)
                module.__file__ = f"<verified-package:{relative_path}>"
                module.__package__ = module_name.rpartition(".")[0]
                module.__loader__ = None
                sys.modules[module_name] = module
                try:
                    source = snapshots[relative_path].decode("utf-8")
                    code = compile(source, module.__file__, "exec", dont_inherit=True)
                    exec(code, module.__dict__)
                except Exception as exc:
                    raise LineageSchemaError(
                        f"verified runtime source failed to load: {relative_path}: {exc}"
                    ) from exc
                loaded[module_name] = module
        finally:
            for module_name in reversed(tuple(previous)):
                prior = previous[module_name]
                if prior is sentinel:
                    sys.modules.pop(module_name, None)
                else:
                    sys.modules[module_name] = prior  # type: ignore[assignment]

    schema = loaded["zerogate_sim.v1_8_lineage_schema"]
    predictor = loaded["zerogate_sim.v1_8_lineage_predictor"]
    required = {
        "lineage_predictor": getattr(predictor, "lineage_predictor", None),
        "immutable_lineage_frames": getattr(schema, "immutable_lineage_frames", None),
        "predictor_config_document": getattr(
            predictor, "predictor_config_document", None
        ),
        "owned_pressure": getattr(predictor, "owned_pressure", None),
        "lineage_schema_sha256": getattr(schema, "lineage_schema_sha256", None),
    }
    missing_api = sorted(name for name, value in required.items() if not callable(value))
    if missing_api:
        raise LineageSchemaError(f"verified runtime API is incomplete: {missing_api}")
    runtime = _VerifiedRuntime(
        lineage_predictor=required["lineage_predictor"],  # type: ignore[arg-type]
        immutable_lineage_frames=required["immutable_lineage_frames"],  # type: ignore[arg-type]
        predictor_config_document=required["predictor_config_document"],  # type: ignore[arg-type]
        owned_pressure=required["owned_pressure"],  # type: ignore[arg-type]
        lineage_schema_sha256=required["lineage_schema_sha256"],  # type: ignore[arg-type]
        predictor_id=str(getattr(predictor, "PREDICTOR_ID", "")),
        formula_id=str(getattr(predictor, "FORMULA_ID", "")),
        schema_id=str(getattr(schema, "SCHEMA_ID", "")),
        version=str(getattr(schema, "VERSION", "")),
    )
    if (
        runtime.predictor_id != PREDICTOR_ID
        or runtime.formula_id != FORMULA_ID
        or runtime.schema_id != SCHEMA_ID
        or runtime.version != VERSION
    ):
        raise LineageSchemaError("verified runtime identifiers do not match package identifiers")
    return runtime


def _canonical_config_object(data: bytes, *, source: str) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LineageSchemaError(f"{source}: configuration is not UTF-8") from exc
    if not text.endswith("\n") or text != text.strip("\n") + "\n":
        raise LineageSchemaError(f"{source}: configuration must have one final newline")
    value = strict_json_loads(text, source=source)
    if not isinstance(value, dict):
        raise LineageSchemaError(f"{source}: configuration must be a JSON object")
    if text != canonical_json(value) + "\n":
        raise LineageSchemaError(f"{source}: configuration is not canonical JSON")
    return value


def _verify_contract_configs(
    snapshots: Mapping[str, bytes],
    runtime: _VerifiedRuntime,
) -> None:
    predictor_path = "contracts/v1_8_1_lineage_predictor.json"
    plan_path = "contracts/v1_8_1_development_plan_lock.json"
    predictor_config = _canonical_config_object(snapshots[predictor_path], source=predictor_path)
    development_plan = _canonical_config_object(snapshots[plan_path], source=plan_path)
    if predictor_config != runtime.predictor_config_document():
        raise LineageSchemaError("predictor configuration does not match the implemented formula")
    if development_plan != development_plan_document():
        raise LineageSchemaError("development plan does not match the implemented plan lock")
    _execute_development_canaries(runtime, development_plan)


def _package_contract_payload(
    records: Iterable[PackageFileRecord],
    runtime: _VerifiedRuntime,
) -> dict[str, object]:
    return {
        "version": VERSION,
        "contract_id": PACKAGE_CONTRACT_ID,
        "schema_id": SCHEMA_ID,
        "schema_sha256": runtime.lineage_schema_sha256(),
        "predictor_id": PREDICTOR_ID,
        "formula_id": FORMULA_ID,
        "file_allowlist": [record.to_dict() for record in records],
    }


def _verify_predictor_package_state(
    repo_root: str | Path | None = None,
    *,
    expected_contract_sha256: str | None = None,
) -> _VerifiedState:
    root = _default_repo_root() if repo_root is None else Path(repo_root).absolute()
    snapshots = _snapshot_package_files(root)
    snapshot_map = dict(snapshots)
    runtime = _load_verified_runtime(snapshot_map)
    _verify_contract_configs(snapshot_map, runtime)
    records = tuple(
        PackageFileRecord(relative_path=path, sha256=sha256_bytes(data), size_bytes=len(data))
        for path, data in snapshots
    )
    contract_sha = stable_sha256(_package_contract_payload(records, runtime))
    if expected_contract_sha256 is not None:
        expected = _validate_expected_sha256(
            expected_contract_sha256,
            field="expected_contract_sha256",
        )
        if contract_sha != expected:
            raise LineageSchemaError("predictor package contract SHA-256 mismatch")
    package = VerifiedPredictorPackage(
        contract_sha256=contract_sha,
        files=records,
        schema_sha256=runtime.lineage_schema_sha256(),
        predictor_config_sha256=sha256_bytes(
            snapshot_map["contracts/v1_8_1_lineage_predictor.json"]
        ),
        development_plan_sha256=sha256_bytes(
            snapshot_map["contracts/v1_8_1_development_plan_lock.json"]
        ),
    )
    return _VerifiedState(package=package, snapshots=snapshots, runtime=runtime)


def verify_predictor_package(
    repo_root: str | Path | None = None,
    *,
    expected_contract_sha256: str | None = None,
) -> VerifiedPredictorPackage:
    """Verify the exact code/config allowlist and optionally a prior receipt."""

    return _verify_predictor_package_state(
        repo_root,
        expected_contract_sha256=expected_contract_sha256,
    ).package


def predictor_package_manifest(
    repo_root: str | Path | None = None,
    *,
    expected_contract_sha256: str | None = None,
) -> dict[str, object]:
    return verify_predictor_package(
        repo_root,
        expected_contract_sha256=expected_contract_sha256,
    ).to_manifest()


def _assert_package_unchanged(root: Path, state: _VerifiedState) -> None:
    if _snapshot_package_files(root) != state.snapshots:
        raise LineageSchemaError("predictor package changed during score freeze")


def _score_rows(
    observable_rows: list[dict[str, object]],
    runtime: _VerifiedRuntime,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_observables: dict[str, LineageScore] = {}
    for row in observable_rows:
        row_index = int(row["row_index"])
        frames = runtime.immutable_lineage_frames(
            row["observable_frames"],
            source=f"score row {row_index}",
        )
        observable_hash = stable_sha256([dict(frame) for frame in frames])
        score = runtime.lineage_predictor(frames)
        previous = by_observables.get(observable_hash)
        if previous is not None and previous != score:
            raise LineageSchemaError("identical observable sequences produced different scores")
        by_observables[observable_hash] = score
        rows.append({"row_index": row_index, **score.to_dict()})

    # Repeat in reverse order so ordinary state, position, and random dependence
    # cannot silently enter the supposedly pure callback.
    for row in reversed(observable_rows):
        frames = runtime.immutable_lineage_frames(
            row["observable_frames"], source="reverse score row"
        )
        observable_hash = stable_sha256([dict(frame) for frame in frames])
        if runtime.lineage_predictor(frames) != by_observables[observable_hash]:
            raise LineageSchemaError("predictor failed reverse-order repeat consistency")
    return rows


def _score_text(value: object) -> str:
    number = float(value)
    if number == 0.0:
        number = 0.0
    return format(number, ".17g")


def _score_csv_bytes(rows: Iterable[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SCORE_HEADER)
    for row in rows:
        writer.writerow(
            [row["row_index"]]
            + [_score_text(row[field]) for field in SCORE_HEADER if field != "row_index"]
        )
    return buffer.getvalue().encode("utf-8")


def _assert_input_unchanged(path: Path, expected: bytes) -> None:
    if not path.is_file() or path.is_symlink() or path.read_bytes() != expected:
        raise LineageSchemaError("lineage observable input changed during score freeze")


def _safe_input_file(root: Path, path: str | Path, *, kind: str) -> Path:
    if not root.is_dir() or root.is_symlink():
        raise LineageSchemaError(f"allowed input root is missing or unsafe: {root}")
    root_resolved = root.resolve(strict=True)
    candidate = Path(path).absolute()
    try:
        relative = candidate.relative_to(root.absolute())
    except ValueError as exc:
        raise LineageSchemaError(f"{kind} is outside the allowed input root") from exc
    checked = root.absolute()
    for part in relative.parts:
        checked = checked / part
        if checked.is_symlink():
            raise LineageSchemaError(f"{kind} path contains a symlink")
    if not candidate.is_file():
        raise LineageSchemaError(f"missing {kind}: {candidate}")
    try:
        candidate.resolve(strict=True).relative_to(root_resolved)
    except (OSError, ValueError) as exc:
        raise LineageSchemaError(f"{kind} escapes the allowed input root") from exc
    return candidate


def lineage_source_manifest_document(
    *,
    observable_input_path: str | Path,
    allowed_input_root: str | Path,
    purpose: str,
    source_kind: str,
    construction_policy: str,
    labels_used_to_construct_observables_declared: bool,
    holdout_material_declared: bool,
) -> dict[str, object]:
    root = Path(allowed_input_root).absolute()
    observable_path = _safe_input_file(
        root,
        observable_input_path,
        kind="lineage observable input",
    )
    for field, value in (("purpose", purpose), ("source_kind", source_kind)):
        if not isinstance(value, str) or SAFE_TOKEN_RE.fullmatch(value) is None:
            raise LineageSchemaError(f"{field} must be a canonical safe token")
    if not isinstance(construction_policy, str) or not construction_policy.strip():
        raise LineageSchemaError("construction_policy must be nonempty text")
    if type(labels_used_to_construct_observables_declared) is not bool or type(
        holdout_material_declared
    ) is not bool:
        raise LineageSchemaError("source-manifest declarations must be exact booleans")
    observable_bytes = observable_path.read_bytes()
    rows = read_lineage_inputs_bytes(observable_bytes, source=str(observable_path))
    return {
        "version": VERSION,
        "manifest_id": SOURCE_MANIFEST_ID,
        "schema_id": SCHEMA_ID,
        "schema_sha256": lineage_schema_sha256(),
        "purpose": purpose,
        "source_kind": source_kind,
        "construction_policy": construction_policy,
        "observable_input_relative_path": observable_path.relative_to(root).as_posix(),
        "observable_input_sha256": sha256_bytes(observable_bytes),
        "observable_values_sha256": stable_sha256(
            [row["observable_frames"] for row in rows]
        ),
        "row_count": len(rows),
        "frame_order": list(FRAME_NAMES),
        "observable_fields": list(OBSERVABLE_FIELDS),
        "labels_used_to_construct_observables_declared": (
            labels_used_to_construct_observables_declared
        ),
        "holdout_material_declared": holdout_material_declared,
        "declarations_are_content_hash_bound_not_external_proof": True,
    }


def write_lineage_source_manifest(
    path: str | Path,
    *,
    observable_input_path: str | Path,
    allowed_input_root: str | Path,
    purpose: str,
    source_kind: str,
    construction_policy: str,
    labels_used_to_construct_observables_declared: bool,
    holdout_material_declared: bool,
) -> Path:
    output = Path(path)
    document = lineage_source_manifest_document(
        observable_input_path=observable_input_path,
        allowed_input_root=allowed_input_root,
        purpose=purpose,
        source_kind=source_kind,
        construction_policy=construction_policy,
        labels_used_to_construct_observables_declared=(
            labels_used_to_construct_observables_declared
        ),
        holdout_material_declared=holdout_material_declared,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_exact(output, (canonical_json(document) + "\n").encode("utf-8"))
    return output


def _verify_source_manifest(
    *,
    source_manifest_path: str | Path,
    expected_source_manifest_sha256: str,
    observable_input_path: str | Path,
    allowed_input_root: str | Path,
    expected_source_purpose: str,
) -> tuple[dict[str, object], bytes]:
    expected_sha = _validate_expected_sha256(
        expected_source_manifest_sha256,
        field="expected_source_manifest_sha256",
    )
    if SAFE_TOKEN_RE.fullmatch(expected_source_purpose) is None:
        raise LineageSchemaError("expected_source_purpose must be a canonical safe token")
    root = Path(allowed_input_root).absolute()
    observable_path = _safe_input_file(
        root,
        observable_input_path,
        kind="lineage observable input",
    )
    manifest_path = _safe_input_file(
        root,
        source_manifest_path,
        kind="lineage source manifest",
    )
    data = manifest_path.read_bytes()
    if sha256_bytes(data) != expected_sha:
        raise LineageSchemaError("lineage source manifest SHA-256 mismatch")
    value = _canonical_config_object(data, source=str(manifest_path))
    if value.get("purpose") != expected_source_purpose:
        raise LineageSchemaError("lineage source purpose mismatch")
    if value.get("labels_used_to_construct_observables_declared") is not False:
        raise LineageSchemaError("label-informed observable construction is forbidden")
    if value.get("holdout_material_declared") is not False:
        raise LineageSchemaError("holdout material is forbidden in this development freeze")
    expected_document = lineage_source_manifest_document(
        observable_input_path=observable_path,
        allowed_input_root=root,
        purpose=expected_source_purpose,
        source_kind=str(value.get("source_kind", "")),
        construction_policy=str(value.get("construction_policy", "")),
        labels_used_to_construct_observables_declared=False,
        holdout_material_declared=False,
    )
    if value != expected_document:
        raise LineageSchemaError("lineage source manifest does not match its bound input")
    return value, data


def _unlink_if_same_file(path: Path, identity: tuple[int, int]) -> None:
    try:
        stat = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return
    if path.is_symlink() or (stat.st_dev, stat.st_ino) != identity:
        return
    path.unlink()


def _write_exact(path: Path, data: bytes) -> tuple[int, int]:
    identity: tuple[int, int] | None = None
    try:
        with path.open("xb") as handle:
            identity_stat = os.fstat(handle.fileno())
            identity = (identity_stat.st_dev, identity_stat.st_ino)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_bytes() != data:
            raise LineageSchemaError(f"artifact changed while being written: {path.name}")
        return identity
    except Exception:
        if identity is not None:
            _unlink_if_same_file(path, identity)
        raise


def _score_freeze_manifest(
    *,
    observable_bytes: bytes,
    observable_rows: list[dict[str, object]],
    score_rows: list[dict[str, object]],
    scores_bytes: bytes,
    package: VerifiedPredictorPackage,
    source_manifest: Mapping[str, object],
    source_manifest_sha256: str,
    synthetic_only: bool,
) -> dict[str, object]:
    score_values = [
        {field: row[field] for field in SCORE_HEADER if field != "row_index"}
        for row in score_rows
    ]
    return {
        "version": VERSION,
        "freeze_state": "FROZEN_DEVELOPMENT_SCORES_PRE_DECISION_RULE",
        "schema_id": SCHEMA_ID,
        "schema_sha256": package.schema_sha256,
        "observable_input_sha256": sha256_bytes(observable_bytes),
        "observable_values_sha256": stable_sha256(
            [row["observable_frames"] for row in observable_rows]
        ),
        "observable_row_index_sha256": stable_sha256(
            [row["row_index"] for row in observable_rows]
        ),
        "source_manifest_sha256": source_manifest_sha256,
        "source_purpose": source_manifest["purpose"],
        "source_kind": source_manifest["source_kind"],
        "source_labels_used_to_construct_observables_declared": source_manifest[
            "labels_used_to_construct_observables_declared"
        ],
        "source_holdout_material_declared": source_manifest[
            "holdout_material_declared"
        ],
        "predictor_id": PREDICTOR_ID,
        "formula_id": FORMULA_ID,
        "predictor_contract_sha256": package.contract_sha256,
        "predictor_execution_loaded_from_verified_source_snapshot": True,
        "verifier_coordinator_trusted_as_invoked": True,
        "predictor_config_sha256": package.predictor_config_sha256,
        "development_plan_sha256": package.development_plan_sha256,
        "package_files": [record.to_dict() for record in package.files],
        "score_count": len(score_rows),
        "score_file_sha256": sha256_bytes(scores_bytes),
        "score_values_sha256": stable_sha256(score_values),
        "callback_frame_count": 3,
        "callback_fields_per_frame": len(OBSERVABLE_FIELDS),
        "identifier_fields_in_callback_arguments": False,
        "target_fields_in_callback_arguments": False,
        "reverse_order_repeat_consistency_passed": True,
        "decision_rule_selected": False,
        "selected_threshold_option": None,
        "scientific_thresholds_selected": False,
        "trinary_predictions_emitted": False,
        "synthetic_only_declared": synthetic_only,
        "holdout_access_not_inferred_by_generic_freezer": True,
        "scientific_status": "HOLD_LINEAGE_PACKAGE_DEVELOPMENT_ONLY",
    }


def _score_freeze_receipt(manifest: Mapping[str, object], manifest_bytes: bytes) -> dict[str, object]:
    return {
        "version": VERSION,
        "receipt_state": "PRE_DECISION_RULE_SCORE_FREEZE_RECEIPT",
        "observable_input_sha256": manifest["observable_input_sha256"],
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "predictor_contract_sha256": manifest["predictor_contract_sha256"],
        "score_file_sha256": manifest["score_file_sha256"],
        "score_values_sha256": manifest["score_values_sha256"],
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "scientific_thresholds_selected": False,
        "external_timestamp_proof": False,
    }


def freeze_lineage_scores(
    out: str | Path,
    *,
    observable_input_path: str | Path,
    source_manifest_path: str | Path,
    expected_source_manifest_sha256: str,
    allowed_input_root: str | Path,
    expected_source_purpose: str,
    expected_predictor_contract_sha256: str,
    repo_root: str | Path | None = None,
    synthetic_only: bool = True,
) -> dict[str, Path]:
    """Freeze continuous lineage and ablation scores without a decision rule."""

    if type(synthetic_only) is not bool:
        raise LineageSchemaError("synthetic_only must be an exact boolean")
    expected_contract = _validate_expected_sha256(
        expected_predictor_contract_sha256,
        field="expected_predictor_contract_sha256",
    )
    root = _default_repo_root() if repo_root is None else Path(repo_root).absolute()
    package_state = _verify_predictor_package_state(
        root,
        expected_contract_sha256=expected_contract,
    )

    observable_path = _safe_input_file(
        Path(allowed_input_root).absolute(),
        observable_input_path,
        kind="lineage observable input",
    )
    source_manifest, source_manifest_bytes = _verify_source_manifest(
        source_manifest_path=source_manifest_path,
        expected_source_manifest_sha256=expected_source_manifest_sha256,
        observable_input_path=observable_path,
        allowed_input_root=allowed_input_root,
        expected_source_purpose=expected_source_purpose,
    )
    observable_bytes = observable_path.read_bytes()
    observable_rows = read_lineage_inputs_bytes(observable_bytes, source=str(observable_path))
    score_rows = _score_rows(observable_rows, package_state.runtime)
    _assert_input_unchanged(observable_path, observable_bytes)
    _assert_package_unchanged(root, package_state)

    output_dir = Path(out)
    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink()):
        raise LineageSchemaError(f"unsafe score output directory: {output_dir}")
    paths = {key: output_dir / relative for key, relative in SCORE_FILES.items()}
    existing = [str(path) for path in paths.values() if path.exists()]
    if existing:
        raise LineageSchemaError(f"refusing to overwrite score artifacts: {existing}")

    scores_bytes = _score_csv_bytes(score_rows)
    manifest = _score_freeze_manifest(
        observable_bytes=observable_bytes,
        observable_rows=observable_rows,
        score_rows=score_rows,
        scores_bytes=scores_bytes,
        package=package_state.package,
        source_manifest=source_manifest,
        source_manifest_sha256=sha256_bytes(source_manifest_bytes),
        synthetic_only=synthetic_only,
    )
    manifest_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    receipt = _score_freeze_receipt(manifest, manifest_bytes)
    receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")

    output_created = False
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=False)
            output_created = True
        for key, data in (
            ("scores", scores_bytes),
            ("manifest", manifest_bytes),
            ("receipt", receipt_bytes),
        ):
            identity = _write_exact(paths[key], data)
            created.append((paths[key], identity))
        _assert_input_unchanged(observable_path, observable_bytes)
        _, source_manifest_after = _verify_source_manifest(
            source_manifest_path=source_manifest_path,
            expected_source_manifest_sha256=expected_source_manifest_sha256,
            observable_input_path=observable_path,
            allowed_input_root=allowed_input_root,
            expected_source_purpose=expected_source_purpose,
        )
        if source_manifest_after != source_manifest_bytes:
            raise LineageSchemaError("lineage source manifest changed during score freeze")
        _assert_package_unchanged(root, package_state)
    except Exception:
        for path, identity in reversed(created):
            _unlink_if_same_file(path, identity)
        if output_created and output_dir.is_dir():
            try:
                output_dir.rmdir()
            except OSError:
                pass
        raise
    return paths


def verify_lineage_score_freeze(
    out: str | Path,
    *,
    observable_input_path: str | Path,
    source_manifest_path: str | Path,
    expected_source_manifest_sha256: str,
    allowed_input_root: str | Path,
    expected_source_purpose: str,
    expected_predictor_contract_sha256: str,
    expected_receipt_sha256: str,
    repo_root: str | Path | None = None,
    synthetic_only: bool = True,
) -> dict[str, object]:
    """Recompute and verify a score freeze before any downstream use.

    Both expected hashes must come from a caller-controlled checkpoint. Passing
    hashes read from the artifacts being checked would not establish an
    independent integrity boundary.
    """

    if type(synthetic_only) is not bool:
        raise LineageSchemaError("synthetic_only must be an exact boolean")
    expected_contract = _validate_expected_sha256(
        expected_predictor_contract_sha256,
        field="expected_predictor_contract_sha256",
    )
    expected_receipt = _validate_expected_sha256(
        expected_receipt_sha256,
        field="expected_receipt_sha256",
    )
    root = _default_repo_root() if repo_root is None else Path(repo_root).absolute()
    package_state = _verify_predictor_package_state(
        root,
        expected_contract_sha256=expected_contract,
    )

    observable_path = _safe_input_file(
        Path(allowed_input_root).absolute(),
        observable_input_path,
        kind="lineage observable input",
    )
    source_manifest, source_manifest_bytes = _verify_source_manifest(
        source_manifest_path=source_manifest_path,
        expected_source_manifest_sha256=expected_source_manifest_sha256,
        observable_input_path=observable_path,
        allowed_input_root=allowed_input_root,
        expected_source_purpose=expected_source_purpose,
    )
    observable_bytes = observable_path.read_bytes()
    observable_rows = read_lineage_inputs_bytes(observable_bytes, source=str(observable_path))
    score_rows = _score_rows(observable_rows, package_state.runtime)
    scores_bytes = _score_csv_bytes(score_rows)

    output_dir = Path(out)
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise LineageSchemaError(f"missing or unsafe score output directory: {output_dir}")
    paths = {key: output_dir / relative for key, relative in SCORE_FILES.items()}
    for key, path in paths.items():
        if not path.is_file() or path.is_symlink():
            raise LineageSchemaError(f"missing or unsafe score {key} artifact: {path}")

    stored_scores = paths["scores"].read_bytes()
    manifest_bytes = paths["manifest"].read_bytes()
    receipt_bytes = paths["receipt"].read_bytes()
    if sha256_bytes(receipt_bytes) != expected_receipt:
        raise LineageSchemaError("score freeze receipt SHA-256 mismatch")
    manifest = _canonical_config_object(manifest_bytes, source=str(paths["manifest"]))
    receipt = _canonical_config_object(receipt_bytes, source=str(paths["receipt"]))

    expected_manifest = _score_freeze_manifest(
        observable_bytes=observable_bytes,
        observable_rows=observable_rows,
        score_rows=score_rows,
        scores_bytes=scores_bytes,
        package=package_state.package,
        source_manifest=source_manifest,
        source_manifest_sha256=sha256_bytes(source_manifest_bytes),
        synthetic_only=synthetic_only,
    )
    expected_manifest_bytes = (canonical_json(expected_manifest) + "\n").encode("utf-8")
    expected_receipt_document = _score_freeze_receipt(
        expected_manifest,
        expected_manifest_bytes,
    )
    if stored_scores != scores_bytes:
        raise LineageSchemaError("frozen score bytes do not match recomputed scores")
    if manifest != expected_manifest or manifest_bytes != expected_manifest_bytes:
        raise LineageSchemaError("score freeze manifest does not match recomputed state")
    if receipt != expected_receipt_document:
        raise LineageSchemaError("score freeze receipt does not match recomputed state")
    _assert_input_unchanged(observable_path, observable_bytes)
    _assert_package_unchanged(root, package_state)
    return {
        "manifest": manifest,
        "receipt": receipt,
        "receipt_sha256": expected_receipt,
        "score_file_sha256": sha256_bytes(stored_scores),
        "verified": True,
    }
