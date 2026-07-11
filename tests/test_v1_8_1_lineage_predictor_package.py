from __future__ import annotations

import csv
import importlib
import importlib.util
import inspect
import json
import math
import shutil
from pathlib import Path
from types import MappingProxyType

import pytest

from zerogate_sim import v1_8_predictor_package as package_module
from zerogate_sim.v1_8_lineage_predictor import (
    FORMULA_ID,
    PREDICTOR_ID,
    LineageScore,
    lineage_predictor,
    owned_pressure,
    predictor_config_document,
    score_lineage_frames,
)
from zerogate_sim.v1_8_lineage_schema import (
    FRAME_NAMES,
    OBSERVABLE_FIELDS,
    SCHEMA_ID,
    VERSION,
    LineageSchemaError,
    canonical_json,
    canonical_lineage_row,
    immutable_lineage_frames,
    lineage_input_bytes,
    lineage_schema_document,
    lineage_schema_sha256,
    read_lineage_inputs_bytes,
    sha256_bytes,
    stable_sha256,
    validate_lineage_frames,
    validate_observable_frame,
    write_lineage_inputs,
)
from zerogate_sim.v1_8_predictor_package import (
    PACKAGE_FILE_ALLOWLIST,
    SCORE_FILES,
    SCORE_HEADER,
    development_plan_document,
    freeze_lineage_scores,
    lineage_source_manifest_document,
    predictor_package_manifest,
    verify_development_canaries,
    verify_lineage_score_freeze,
    verify_predictor_package,
    write_lineage_source_manifest,
)
from zerogate_sim.v1_8_observable_schema import (
    OBSERVABLE_FIELDS as BASE_OBSERVABLE_FIELDS,
    SCHEMA_ID as BASE_OBSERVABLE_SCHEMA_ID,
    observable_schema_sha256 as base_observable_schema_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OBSERVABLE_FIELDS = (
    "strength",
    "distinction",
    "polarity",
    "relation",
    "return_observed",
    "echo_mimic_score",
    "observed_stability_score",
)
EXPECTED_PACKAGE_ALLOWLIST = (
    "src/zerogate_sim/v1_8_observable_schema.py",
    "src/zerogate_sim/v1_8_lineage_schema.py",
    "src/zerogate_sim/v1_8_lineage_predictor.py",
    "src/zerogate_sim/v1_8_predictor_package.py",
    "contracts/v1_8_1_lineage_predictor.json",
    "contracts/v1_8_1_development_plan_lock.json",
)
SOURCE_PURPOSE = "v1_8_1_test_development"
SOURCE_KIND = "constructed_test_canaries"
CONSTRUCTION_POLICY = "test frames are fixed before score freeze without labels"


class _FloatLike:
    def __float__(self) -> float:
        return 0.5


def _frame(value: float, *, echo: float = 0.0) -> dict[str, float]:
    frame = {field: value for field in OBSERVABLE_FIELDS}
    frame["echo_mimic_score"] = echo
    return frame


def _frames(early: float, witness: float, late: float) -> list[dict[str, float]]:
    return [_frame(early), _frame(witness), _frame(late)]


def _copy_package_repository(tmp_path: Path, *, name: str = "repo") -> Path:
    copied_root = tmp_path / name
    for relative_path in PACKAGE_FILE_ALLOWLIST:
        source = ROOT / relative_path
        destination = copied_root / Path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return copied_root


def _canonical_config(path: Path, value: object) -> None:
    path.write_bytes((canonical_json(value) + "\n").encode("utf-8"))


def _write_source_manifest(
    root: Path,
    observable_path: Path,
    *,
    name: str,
    purpose: str = SOURCE_PURPOSE,
    labels_used: bool = False,
    holdout_material: bool = False,
) -> tuple[Path, str]:
    manifest_path = root / f"{name}_source_manifest.json"
    write_lineage_source_manifest(
        manifest_path,
        observable_input_path=observable_path,
        allowed_input_root=root,
        purpose=purpose,
        source_kind=SOURCE_KIND,
        construction_policy=CONSTRUCTION_POLICY,
        labels_used_to_construct_observables_declared=labels_used,
        holdout_material_declared=holdout_material,
    )
    return manifest_path, sha256_bytes(manifest_path.read_bytes())


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _read_score_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _score_signatures(path: Path) -> list[tuple[float, ...]]:
    return sorted(
        tuple(float(row[field]) for field in SCORE_HEADER if field != "row_index")
        for row in _read_score_rows(path)
    )


def _freeze_fixture(
    tmp_path: Path,
    *,
    rows: list[object] | None = None,
    name: str = "freeze",
    repo_root: Path | None = None,
) -> tuple[Path, dict[str, Path], str]:
    repository = repo_root or _copy_package_repository(tmp_path, name=f"{name}_repo")
    package = verify_predictor_package(repository)
    observable_path = tmp_path / f"{name}_lineage.jsonl"
    write_lineage_inputs(
        observable_path,
        rows or [_frames(0.8, 0.8, 0.8), _frames(0.2, 0.2, 0.9)],
    )
    source_manifest_path, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable_path,
        name=name,
    )
    paths = freeze_lineage_scores(
        tmp_path / f"{name}_out",
        observable_input_path=observable_path,
        source_manifest_path=source_manifest_path,
        expected_source_manifest_sha256=source_manifest_sha,
        allowed_input_root=tmp_path,
        expected_source_purpose=SOURCE_PURPOSE,
        expected_predictor_contract_sha256=package.contract_sha256,
        repo_root=repository,
    )
    return observable_path, paths, package.contract_sha256


def test_exact_three_by_seven_schema_and_document() -> None:
    assert FRAME_NAMES == ("early", "witness", "late")
    assert OBSERVABLE_FIELDS == EXPECTED_OBSERVABLE_FIELDS
    assert OBSERVABLE_FIELDS == BASE_OBSERVABLE_FIELDS
    checked = validate_lineage_frames(_frames(0.1, 0.5, 0.9))
    assert type(checked) is tuple
    assert len(checked) == 3
    assert all(tuple(frame) == EXPECTED_OBSERVABLE_FIELDS for frame in checked)
    assert all(type(value) is float for frame in checked for value in frame.values())

    schema = lineage_schema_document()
    assert schema["version"] == VERSION
    assert schema["schema_id"] == SCHEMA_ID
    assert schema["base_observable_schema_id"] == BASE_OBSERVABLE_SCHEMA_ID
    assert schema["base_observable_schema_sha256"] == base_observable_schema_sha256()
    assert schema["frame_fields_derived_from_base_schema"] is True
    assert schema["frame_count"] == 3
    assert schema["frame_order"] == list(FRAME_NAMES)
    assert schema["frame_fields"] == list(EXPECTED_OBSERVABLE_FIELDS)
    assert schema["field_type"] == "actual_json_number_finite_unit_interval"
    assert schema["row_index_is_transport_only"] is True
    assert schema["scientific_thresholds_selected"] is False
    assert lineage_schema_sha256() == stable_sha256(schema)


@pytest.mark.parametrize(
    "bad_value",
    [True, False, "0.5", "", None, object(), _FloatLike(), complex(0.5, 0.0)],
    ids=["true", "false", "numeric-string", "empty-string", "none", "object", "float-like", "complex"],
)
def test_observable_values_require_actual_json_numbers(bad_value: object) -> None:
    frame: dict[str, object] = _frame(0.5)
    frame["strength"] = bad_value
    with pytest.raises(LineageSchemaError, match="actual JSON number"):
        validate_observable_frame(frame)


@pytest.mark.parametrize(
    "bad_value",
    [math.nan, math.inf, -math.inf, -0.0001, 1.0001],
    ids=["nan", "positive-infinity", "negative-infinity", "below-zero", "above-one"],
)
def test_observable_values_reject_nonfinite_and_out_of_range(bad_value: float) -> None:
    frame = _frame(0.5)
    frame["relation"] = bad_value
    with pytest.raises(LineageSchemaError, match="0 <= value <= 1"):
        validate_observable_frame(frame)


def test_integer_endpoints_are_accepted_and_negative_zero_is_normalized() -> None:
    frame: dict[str, object] = {field: 0 for field in OBSERVABLE_FIELDS}
    frame["strength"] = 1
    frame["relation"] = -0.0
    checked = validate_observable_frame(frame)
    assert checked["strength"] == 1.0
    assert type(checked["strength"]) is float
    assert checked["relation"] == 0.0
    assert math.copysign(1.0, checked["relation"]) == 1.0


def test_missing_extra_and_nested_fields_fail_closed() -> None:
    missing = _frame(0.5)
    missing.pop("return_observed")
    with pytest.raises(LineageSchemaError, match=r"missing=\['return_observed'\]"):
        validate_observable_frame(missing)

    extra: dict[str, object] = _frame(0.5)
    extra["truth_role"] = "expresser"
    with pytest.raises(LineageSchemaError, match="truth_role"):
        validate_observable_frame(extra)

    nested: dict[str, object] = {"observables": _frame(0.5)}
    with pytest.raises(LineageSchemaError, match="exact seven-field schema"):
        validate_observable_frame(nested)

    nested_forbidden: dict[str, object] = _frame(0.5)
    nested_forbidden["label"] = {"truth_role": "trap"}
    with pytest.raises(LineageSchemaError, match="label"):
        validate_observable_frame(nested_forbidden)


@pytest.mark.parametrize("bad_frames", ["abc", b"abc", bytearray(b"abc"), {}, [_frame(0.5)] * 2, [_frame(0.5)] * 4])
def test_lineage_requires_exact_ordered_three_frame_sequence(bad_frames: object) -> None:
    with pytest.raises(LineageSchemaError, match="ordered sequence|exactly three frames"):
        validate_lineage_frames(bad_frames)


def test_canonical_jsonl_round_trip_and_exact_envelope() -> None:
    raw = lineage_input_bytes([_frames(0.2, 0.8, 0.9), _frames(0.9, 0.8, 0.2)])
    rows = read_lineage_inputs_bytes(raw, source="memory")
    assert [row["row_index"] for row in rows] == [0, 1]
    assert all(set(row) == {"observable_frames", "row_index"} for row in rows)
    assert raw.endswith(b"\n")
    assert raw == b"".join(
        (canonical_json(row) + "\n").encode("utf-8") for row in rows
    )


def test_canonical_jsonl_rejects_duplicate_keys_at_any_depth() -> None:
    row = canonical_json(canonical_lineage_row(0, _frames(0.2, 0.8, 0.9)))
    duplicate_envelope = row.replace('"row_index":0', '"row_index":0,"row_index":0')
    with pytest.raises(LineageSchemaError, match="duplicate JSON key 'row_index'"):
        read_lineage_inputs_bytes((duplicate_envelope + "\n").encode(), source="duplicate")

    duplicate_nested = row.replace('"strength":0.2', '"strength":0.2,"strength":0.2', 1)
    with pytest.raises(LineageSchemaError, match="duplicate JSON key 'strength'"):
        read_lineage_inputs_bytes((duplicate_nested + "\n").encode(), source="duplicate")


@pytest.mark.parametrize(
    "mutator",
    [
        lambda row: json.dumps(row) + "\n",
        lambda row: canonical_json(row),
        lambda row: canonical_json(row) + "\n\n",
        lambda row: canonical_json({**row, "unexpected": 1}) + "\n",
    ],
    ids=["spaced-json", "missing-final-newline", "blank-row", "extra-envelope-field"],
)
def test_canonical_jsonl_rejects_noncanonical_or_wrong_envelope(mutator) -> None:
    row = canonical_lineage_row(0, _frames(0.2, 0.8, 0.9))
    with pytest.raises(LineageSchemaError):
        read_lineage_inputs_bytes(mutator(row).encode("utf-8"), source="noncanonical")


def test_canonical_jsonl_rejects_nonfinite_constants_negative_zero_and_row_reordering() -> None:
    canonical = canonical_json(canonical_lineage_row(0, _frames(0.2, 0.8, 0.9)))
    nonfinite = canonical.replace('"strength":0.2', '"strength":NaN', 1)
    with pytest.raises(LineageSchemaError, match="non-finite JSON constant"):
        read_lineage_inputs_bytes((nonfinite + "\n").encode(), source="nonfinite")

    negative_zero = canonical.replace('"strength":0.2', '"strength":-0.0', 1)
    with pytest.raises(LineageSchemaError, match="non-canonical"):
        read_lineage_inputs_bytes((negative_zero + "\n").encode(), source="negative-zero")

    first = canonical_json(canonical_lineage_row(0, _frames(0.2, 0.8, 0.9)))
    duplicate_index = canonical_json(canonical_lineage_row(0, _frames(0.3, 0.7, 0.8)))
    with pytest.raises(LineageSchemaError, match="exact ordered sequence"):
        read_lineage_inputs_bytes(f"{first}\n{duplicate_index}\n".encode(), source="order")


def test_immutable_callback_contains_only_three_read_only_frames() -> None:
    immutable = immutable_lineage_frames(_frames(0.2, 0.8, 0.9))
    assert type(immutable) is tuple
    assert all(type(frame) is MappingProxyType for frame in immutable)
    assert all(tuple(frame) == OBSERVABLE_FIELDS for frame in immutable)
    with pytest.raises(TypeError):
        immutable[0]["strength"] = 1.0  # type: ignore[index]
    with pytest.raises(TypeError, match="immutable tuple"):
        lineage_predictor(tuple(dict(frame) for frame in immutable))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="immutable tuple"):
        lineage_predictor(_frames(0.2, 0.8, 0.9))  # type: ignore[arg-type]

    parameters = tuple(inspect.signature(lineage_predictor).parameters)
    assert parameters == ("frames",)
    assert not any(token in inspect.getsource(lineage_predictor) for token in ("truth_role", "label_vault", "row_index"))


def test_formula_uses_owned_pressure_two_touch_support_and_late_frame() -> None:
    frame = _frame(0.9, echo=0.35)
    frame["relation"] = 0.6
    assert owned_pressure(frame) == pytest.approx(0.6)

    result = score_lineage_frames(_frames(0.2, 0.8, 0.9))
    assert result == LineageScore(
        early_owned_pressure=0.2,
        witness_owned_pressure=0.8,
        late_owned_pressure=0.9,
        lineage_support=0.8,
        lineage_score=0.8,
        no_lineage_score=0.9,
        lineage_delta=pytest.approx(0.1),
    )
    reversed_result = score_lineage_frames(_frames(0.9, 0.8, 0.2))
    assert reversed_result.lineage_score == pytest.approx(0.2)
    assert result.lineage_score != reversed_result.lineage_score


@pytest.mark.parametrize(
    "bottleneck",
    [
        "strength",
        "distinction",
        "polarity",
        "relation",
        "return_observed",
        "observed_stability_score",
    ],
)
def test_each_positive_observable_is_an_independent_owned_pressure_bottleneck(
    bottleneck: str,
) -> None:
    frame = _frame(1.0, echo=0.0)
    frame[bottleneck] = 0.17
    assert owned_pressure(frame) == pytest.approx(0.17)


def test_echo_complement_is_an_independent_owned_pressure_bottleneck() -> None:
    frame = _frame(1.0, echo=0.83)
    assert owned_pressure(frame) == pytest.approx(0.17)


def test_formula_configuration_is_continuous_and_threshold_free() -> None:
    config = predictor_config_document()
    assert config["version"] == VERSION
    assert config["schema_id"] == SCHEMA_ID
    assert config["predictor_id"] == PREDICTOR_ID
    assert config["formula_id"] == FORMULA_ID
    assert config["frame_order"] == list(FRAME_NAMES)
    assert config["observable_fields"] == list(OBSERVABLE_FIELDS)
    assert config["selected_threshold_option"] is None
    assert config["scientific_thresholds_selected"] is False
    assert config["output_kind"] == "continuous_development_scores_only"
    assert "trinary" not in canonical_json(config).lower()


def test_development_canaries_and_required_rank_reversal_execute() -> None:
    results = verify_development_canaries()
    assert {row["name"] for row in results} == {
        "sustained",
        "late_spike",
        "matured",
        "collapsed",
        "dormant_reappearance",
    }
    assert all(row["passed"] is True for row in results)
    by_name = {str(row["name"]): row for row in results}
    assert by_name["sustained"]["lineage_score"] > by_name["late_spike"]["lineage_score"]
    assert by_name["sustained"]["no_lineage_score"] < by_name["late_spike"]["no_lineage_score"]
    assert by_name["matured"]["lineage_score"] == pytest.approx(0.8)
    assert by_name["collapsed"]["lineage_score"] == pytest.approx(0.2)
    assert by_name["dormant_reappearance"]["lineage_score"] == pytest.approx(0.9)
    assert by_name["dormant_reappearance"]["no_lineage_score"] == pytest.approx(0.9)

    plan = development_plan_document()
    assert plan["selected_threshold_option"] is None
    assert plan["scientific_thresholds_selected"] is False
    assert plan["trinary_predictions_emitted"] is False
    assert plan["target_data_access_policy"] == "v1_8_3_and_later_forbidden"
    assert plan["frozen_holdout_access_policy"] == "forbidden"


def test_v1_8_2_method_lock_defines_every_result_changing_calculation() -> None:
    plan = development_plan_document()
    registry = plan["score_registry"]
    assert set(registry) == {
        "primary_prior_touch",
        "no_prior_touch_support",
        "no_echo_guard",
        "strength_only",
        "four_gate_minimum",
        "four_gate_mean",
        "return_only",
        "observed_stability_only",
        "echo_guarded_gate_minimum",
        "always_hold",
        "always_crown",
        "always_resist",
    }
    assert registry["primary_prior_touch"]["temporal_aggregation"] == (
        "min(late,max(early,witness))"
    )
    assert registry["no_prior_touch_support"]["temporal_aggregation"] == "late"
    assert registry["always_hold"]["constant_prediction"] == 0
    assert registry["always_crown"]["constant_prediction"] == 1
    assert registry["always_resist"]["constant_prediction"] == -1

    metrics = plan["metric_definitions"]
    assert metrics["role_to_target"] == {"expresser": 1, "latent": 0, "trap": -1}
    assert metrics["undefined_denominator_rule"] == "INVALID_MISSING_REQUIRED_ROLE"
    assert metrics["zero_crown_precision_rule"] == "INVALID_DEAD_SAFE_NO_CROWNS"

    selection = plan["selection_calculation"]
    assert selection["candidate_set"] == "the_three_locked_threshold_options_only"
    assert selection["rate_aggregation"] == (
        "unweighted_arithmetic_mean_of_per_generator_lineage_rates"
    )
    assert selection["observed_score_boundary_margin"] == (
        "minimum_over_training_rows_of_min(abs(score-resist_max),abs(score-crown_min))"
    )
    assert selection["floating_comparison"] == (
        "unrounded_binary64_values_with_exact_lexicographic_comparison"
    )

    comparison = plan["model_comparison_rule"]
    assert comparison["equivalence_tolerance"] == 0.0
    assert comparison["comparison"] == "exact_lexicographic_higher_is_better"
    assert "frozen_and_retuned" in comparison["prior_touch_necessity_requires"]

    uncertainty = plan["uncertainty"]
    assert uncertainty["method"] == (
        "deterministic_sha256_generator_lineage_cluster_percentile_bootstrap"
    )
    assert uncertainty["resamples"] == 2000
    assert uncertainty["sampling_algorithm"].startswith("for replicate b and slot j")
    assert uncertainty["lower_index"] == "floor(0.025*(resamples-1))"
    assert uncertainty["upper_index"] == "ceil(0.975*(resamples-1))"

    failure = plan["failure_capability_contract"]
    assert failure["pass_rule"] == "all_six_fixture_requirements_hold_exactly"
    assert set(failure) == {
        "injected_false_crown",
        "always_hold",
        "always_crown",
        "always_resist",
        "constant_primary_score",
        "balanced_fixture",
        "pass_rule",
    }


def test_predictor_package_is_deterministic_and_uses_exact_allowlist(tmp_path: Path) -> None:
    assert PACKAGE_FILE_ALLOWLIST == EXPECTED_PACKAGE_ALLOWLIST
    repo = _copy_package_repository(tmp_path)
    first = verify_predictor_package(repo)
    second = verify_predictor_package(repo, expected_contract_sha256=first.contract_sha256)
    assert first == second
    assert tuple(record.relative_path for record in first.files) == EXPECTED_PACKAGE_ALLOWLIST
    assert all(len(record.sha256) == 64 and record.size_bytes > 0 for record in first.files)

    manifest = predictor_package_manifest(repo, expected_contract_sha256=first.contract_sha256)
    assert manifest == first.to_manifest()
    assert manifest["predictor_execution_code_and_configuration_binding_verified"] is True
    assert manifest["predictor_execution_loaded_from_verified_source_snapshot"] is True
    assert manifest["verifier_coordinator_trusted_as_invoked"] is True
    assert manifest["in_process_execution_is_os_sandboxed"] is False
    assert [row["relative_path"] for row in manifest["file_allowlist"]] == list(EXPECTED_PACKAGE_ALLOWLIST)
    assert set(inspect.signature(verify_predictor_package).parameters) == {
        "repo_root",
        "expected_contract_sha256",
    }


def test_packaged_configs_are_canonical_and_match_implemented_documents(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    expected = {
        "contracts/v1_8_1_lineage_predictor.json": predictor_config_document(),
        "contracts/v1_8_1_development_plan_lock.json": development_plan_document(),
    }
    for relative_path, document in expected.items():
        data = (repo / relative_path).read_bytes()
        assert data == (canonical_json(document) + "\n").encode("utf-8")
    package = verify_predictor_package(repo)
    assert package.predictor_config_sha256 == sha256_bytes(
        (repo / "contracts/v1_8_1_lineage_predictor.json").read_bytes()
    )
    assert package.development_plan_sha256 == sha256_bytes(
        (repo / "contracts/v1_8_1_development_plan_lock.json").read_bytes()
    )


@pytest.mark.parametrize(
    "relative_path",
    [
        "contracts/v1_8_1_lineage_predictor.json",
        "contracts/v1_8_1_development_plan_lock.json",
    ],
)
def test_predictor_package_rejects_configuration_tamper(tmp_path: Path, relative_path: str) -> None:
    repo = _copy_package_repository(tmp_path)
    path = repo / relative_path
    document = json.loads(path.read_text(encoding="utf-8"))
    document["selected_threshold_option"] = "wide_hold"
    _canonical_config(path, document)
    with pytest.raises(LineageSchemaError, match="configuration does not match|development plan does not match"):
        verify_predictor_package(repo)


def test_predictor_package_expected_hash_detects_source_tamper(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    contract = verify_predictor_package(repo).contract_sha256
    source = repo / "src/zerogate_sim/v1_8_lineage_predictor.py"
    source.write_bytes(source.read_bytes() + b"\n# tamper\n")
    with pytest.raises(LineageSchemaError, match="contract SHA-256 mismatch"):
        verify_predictor_package(repo, expected_contract_sha256=contract)


@pytest.mark.parametrize("bad_hash", ["", "A" * 64, "0" * 63, "g" * 64, 0])
def test_predictor_package_rejects_malformed_expected_hash(tmp_path: Path, bad_hash: object) -> None:
    repo = _copy_package_repository(tmp_path)
    with pytest.raises(LineageSchemaError, match="lowercase SHA-256"):
        verify_predictor_package(repo, expected_contract_sha256=bad_hash)  # type: ignore[arg-type]


def test_predictor_package_rejects_wrong_expected_hash(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    actual = verify_predictor_package(repo).contract_sha256
    wrong = ("0" if actual[0] != "0" else "1") + actual[1:]
    with pytest.raises(LineageSchemaError, match="contract SHA-256 mismatch"):
        verify_predictor_package(repo, expected_contract_sha256=wrong)


def test_predictor_package_rejects_missing_allowlisted_file(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    (repo / PACKAGE_FILE_ALLOWLIST[0]).unlink()
    with pytest.raises(LineageSchemaError, match="missing package file"):
        verify_predictor_package(repo)


def test_predictor_package_rejects_symlinked_allowlisted_file(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    package_path = repo / PACKAGE_FILE_ALLOWLIST[0]
    external = tmp_path / "external.py"
    external.write_bytes(package_path.read_bytes())
    package_path.unlink()
    try:
        package_path.symlink_to(external)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    with pytest.raises(LineageSchemaError, match="symlink"):
        verify_predictor_package(repo)


@pytest.mark.parametrize(
    "unsafe",
    [
        "../outside.py",
        "src/../outside.py",
        "/absolute.py",
        "./local.py",
        "src/./local.py",
        "src//local.py",
        r"src\..\outside.py",
        r"C:\absolute.py",
        "",
    ],
)
def test_predictor_package_rejects_traversal_and_unsafe_paths(tmp_path: Path, unsafe: str) -> None:
    repo = _copy_package_repository(tmp_path)
    with pytest.raises(LineageSchemaError, match="unsafe package path"):
        package_module._safe_package_path(repo, unsafe)


def test_lineage_source_manifest_binds_input_schema_and_provenance_declarations(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "inputs"
    observable = allowed_root / "nested" / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    document = lineage_source_manifest_document(
        observable_input_path=observable,
        allowed_input_root=allowed_root,
        purpose=SOURCE_PURPOSE,
        source_kind=SOURCE_KIND,
        construction_policy=CONSTRUCTION_POLICY,
        labels_used_to_construct_observables_declared=False,
        holdout_material_declared=False,
    )
    assert document["version"] == VERSION
    assert document["schema_id"] == SCHEMA_ID
    assert document["schema_sha256"] == lineage_schema_sha256()
    assert document["purpose"] == SOURCE_PURPOSE
    assert document["source_kind"] == SOURCE_KIND
    assert document["construction_policy"] == CONSTRUCTION_POLICY
    assert document["observable_input_relative_path"] == "nested/observable.jsonl"
    assert document["observable_input_sha256"] == sha256_bytes(observable.read_bytes())
    assert document["row_count"] == 1
    assert document["frame_order"] == list(FRAME_NAMES)
    assert document["observable_fields"] == list(OBSERVABLE_FIELDS)
    assert document["labels_used_to_construct_observables_declared"] is False
    assert document["holdout_material_declared"] is False
    assert document["declarations_are_content_hash_bound_not_external_proof"] is True


def test_source_manifest_builder_rejects_observable_outside_allowed_root(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside = tmp_path / "outside.jsonl"
    write_lineage_inputs(outside, [_frames(0.2, 0.8, 0.9)])
    with pytest.raises(LineageSchemaError, match="outside the allowed input root"):
        lineage_source_manifest_document(
            observable_input_path=outside,
            allowed_input_root=allowed_root,
            purpose=SOURCE_PURPOSE,
            source_kind=SOURCE_KIND,
            construction_policy=CONSTRUCTION_POLICY,
            labels_used_to_construct_observables_declared=False,
            holdout_material_declared=False,
        )


def test_score_freeze_rejects_source_manifest_outside_allowed_root(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    observable = allowed_root / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    outside_manifest = tmp_path / "outside_source_manifest.json"
    write_lineage_source_manifest(
        outside_manifest,
        observable_input_path=observable,
        allowed_input_root=tmp_path,
        purpose=SOURCE_PURPOSE,
        source_kind=SOURCE_KIND,
        construction_policy=CONSTRUCTION_POLICY,
        labels_used_to_construct_observables_declared=False,
        holdout_material_declared=False,
    )
    with pytest.raises(LineageSchemaError, match="source manifest is outside"):
        freeze_lineage_scores(
            tmp_path / "out",
            observable_input_path=observable,
            source_manifest_path=outside_manifest,
            expected_source_manifest_sha256=sha256_bytes(outside_manifest.read_bytes()),
            allowed_input_root=allowed_root,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )


@pytest.mark.parametrize(
    ("labels_used", "holdout_material", "message"),
    [
        (True, False, "label-informed observable construction is forbidden"),
        (False, True, "holdout material is forbidden"),
    ],
)
def test_score_freeze_rejects_forbidden_source_declarations(
    tmp_path: Path,
    labels_used: bool,
    holdout_material: bool,
    message: str,
) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    allowed_root = tmp_path / "inputs"
    allowed_root.mkdir()
    observable = allowed_root / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        allowed_root,
        observable,
        name="forbidden",
        labels_used=labels_used,
        holdout_material=holdout_material,
    )
    with pytest.raises(LineageSchemaError, match=message):
        freeze_lineage_scores(
            tmp_path / "out",
            observable_input_path=observable,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=allowed_root,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )


def test_score_freeze_binds_every_hash_and_emits_continuous_scores_only(tmp_path: Path) -> None:
    observable_path, paths, contract_sha = _freeze_fixture(tmp_path)
    source_manifest_path = tmp_path / "freeze_source_manifest.json"
    source_manifest_sha = sha256_bytes(source_manifest_path.read_bytes())
    manifest_bytes = paths["manifest"].read_bytes()
    receipt_bytes = paths["receipt"].read_bytes()
    manifest = _read_json(paths["manifest"])
    receipt = _read_json(paths["receipt"])
    score_rows = _read_score_rows(paths["scores"])

    assert manifest_bytes == (canonical_json(manifest) + "\n").encode()
    assert receipt_bytes == (canonical_json(receipt) + "\n").encode()
    assert tuple(score_rows[0]) == SCORE_HEADER
    assert manifest["observable_input_sha256"] == sha256_bytes(observable_path.read_bytes())
    assert manifest["source_manifest_sha256"] == source_manifest_sha
    assert receipt["source_manifest_sha256"] == source_manifest_sha
    assert manifest["score_file_sha256"] == sha256_bytes(paths["scores"].read_bytes())
    assert manifest["predictor_contract_sha256"] == contract_sha
    assert manifest["score_count"] == len(score_rows) == 2
    assert receipt["manifest_sha256"] == sha256_bytes(manifest_bytes)
    assert receipt["score_file_sha256"] == manifest["score_file_sha256"]
    assert receipt["score_values_sha256"] == manifest["score_values_sha256"]
    score_values = [
        {field: float(row[field]) for field in SCORE_HEADER if field != "row_index"}
        for row in score_rows
    ]
    assert manifest["score_values_sha256"] == stable_sha256(score_values)

    assert manifest["callback_frame_count"] == 3
    assert manifest["callback_fields_per_frame"] == 7
    assert manifest["predictor_execution_loaded_from_verified_source_snapshot"] is True
    assert manifest["verifier_coordinator_trusted_as_invoked"] is True
    assert manifest["identifier_fields_in_callback_arguments"] is False
    assert manifest["target_fields_in_callback_arguments"] is False
    assert manifest["decision_rule_selected"] is False
    assert manifest["selected_threshold_option"] is None
    assert manifest["scientific_thresholds_selected"] is False
    assert manifest["trinary_predictions_emitted"] is False
    assert manifest["source_labels_used_to_construct_observables_declared"] is False
    assert manifest["source_holdout_material_declared"] is False
    assert manifest["synthetic_only_declared"] is True
    assert manifest["holdout_access_not_inferred_by_generic_freezer"] is True
    assert receipt["scientific_thresholds_selected"] is False
    assert receipt["external_timestamp_proof"] is False
    assert not any("label" in field.lower() or "trinary" in field.lower() for field in score_rows[0])

    verified = verify_lineage_score_freeze(
        paths["scores"].parent,
        observable_input_path=observable_path,
        source_manifest_path=source_manifest_path,
        expected_source_manifest_sha256=source_manifest_sha,
        allowed_input_root=tmp_path,
        expected_source_purpose=SOURCE_PURPOSE,
        expected_predictor_contract_sha256=contract_sha,
        expected_receipt_sha256=sha256_bytes(receipt_bytes),
        repo_root=tmp_path / "freeze_repo",
    )
    assert verified["verified"] is True
    assert verified["receipt_sha256"] == sha256_bytes(receipt_bytes)


def test_score_freeze_artifacts_are_byte_deterministic(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    rows = [_frames(0.1, 0.2, 0.3), _frames(0.4, 0.5, 0.6), _frames(0.7, 0.8, 0.9)]
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    _, first, _ = _freeze_fixture(first_root, rows=rows, name="freeze", repo_root=repo)
    _, second, _ = _freeze_fixture(second_root, rows=rows, name="freeze", repo_root=repo)
    for key in SCORE_FILES:
        assert first[key].read_bytes() == second[key].read_bytes()


def test_score_freeze_is_row_permutation_equivariant(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    rows = [_frames(0.1, 0.2, 0.3), _frames(0.4, 0.5, 0.6), _frames(0.7, 0.8, 0.9)]
    _, original, _ = _freeze_fixture(tmp_path, rows=rows, name="original", repo_root=repo)
    _, permuted, _ = _freeze_fixture(
        tmp_path,
        rows=[rows[2], rows[0], rows[1]],
        name="permuted",
        repo_root=repo,
    )
    assert _score_signatures(original["scores"]) == _score_signatures(permuted["scores"])
    assert [int(row["row_index"]) for row in _read_score_rows(permuted["scores"])] == [0, 1, 2]


def test_score_freeze_refuses_overwrite(tmp_path: Path) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="overwrite",
    )
    out = tmp_path / "out"
    kwargs = {
        "observable_input_path": observable,
        "source_manifest_path": source_manifest,
        "expected_source_manifest_sha256": source_manifest_sha,
        "allowed_input_root": tmp_path,
        "expected_source_purpose": SOURCE_PURPOSE,
        "expected_predictor_contract_sha256": package.contract_sha256,
        "repo_root": repo,
    }
    freeze_lineage_scores(out, **kwargs)
    with pytest.raises(LineageSchemaError, match="refusing to overwrite"):
        freeze_lineage_scores(out, **kwargs)


def test_score_freeze_cleanup_preserves_rival_writer_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="rival_writer",
    )
    out = tmp_path / "out"
    rival_bytes = b"rival-writer-owned-bytes"
    original = package_module._write_exact
    injected = False

    def rival_wins(path: Path, data: bytes):
        nonlocal injected
        if not injected:
            injected = True
            path.write_bytes(rival_bytes)
        return original(path, data)

    monkeypatch.setattr(package_module, "_write_exact", rival_wins)
    with pytest.raises(FileExistsError):
        freeze_lineage_scores(
            out,
            observable_input_path=observable,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=tmp_path,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )
    rival_path = out / SCORE_FILES["scores"]
    assert rival_path.read_bytes() == rival_bytes


def test_score_freeze_detects_observable_tamper_during_scoring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="observable_tamper",
    )
    original = package_module._score_rows

    def tampering_score_rows(rows, runtime):
        result = original(rows, runtime)
        observable.write_bytes(observable.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(package_module, "_score_rows", tampering_score_rows)
    with pytest.raises(LineageSchemaError, match="observable input changed"):
        freeze_lineage_scores(
            tmp_path / "out",
            observable_input_path=observable,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=tmp_path,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )
    assert not (tmp_path / "out").exists()


def test_score_freeze_detects_package_tamper_during_scoring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="package_tamper",
    )
    source = repo / "src/zerogate_sim/v1_8_lineage_predictor.py"
    original = package_module._score_rows

    def tampering_score_rows(rows, runtime):
        result = original(rows, runtime)
        source.write_bytes(source.read_bytes() + b"\n# changed during freeze\n")
        return result

    monkeypatch.setattr(package_module, "_score_rows", tampering_score_rows)
    with pytest.raises(LineageSchemaError, match="package changed during score freeze"):
        freeze_lineage_scores(
            tmp_path / "out",
            observable_input_path=observable,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=tmp_path,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )
    assert not (tmp_path / "out").exists()


def test_score_freeze_does_not_execute_unbound_in_memory_predictor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    frames = _frames(0.31, 0.47, 0.73)
    expected = score_lineage_frames(frames)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [frames])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="rogue",
    )
    original = package_module.lineage_predictor

    def rogue_predictor(callback_frames):
        legitimate = original(callback_frames)
        path = tuple(legitimate.to_dict()[f"{name}_owned_pressure"] for name in FRAME_NAMES)
        if path in {
            (0.8, 0.8, 0.8),
            (0.2, 0.2, 0.9),
            (0.2, 0.8, 0.9),
            (0.9, 0.8, 0.2),
            (0.9, 0.0, 0.9),
        }:
            return legitimate
        return LineageScore(
            early_owned_pressure=legitimate.early_owned_pressure,
            witness_owned_pressure=legitimate.witness_owned_pressure,
            late_owned_pressure=legitimate.late_owned_pressure,
            lineage_support=legitimate.lineage_support,
            lineage_score=0.999,
            no_lineage_score=legitimate.no_lineage_score,
            lineage_delta=legitimate.lineage_delta,
        )

    monkeypatch.setattr(package_module, "lineage_predictor", rogue_predictor)
    try:
        paths = freeze_lineage_scores(
            tmp_path / "out",
            observable_input_path=observable,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=tmp_path,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=package.contract_sha256,
            repo_root=repo,
        )
    except LineageSchemaError:
        return

    score_row = _read_score_rows(paths["scores"])[0]
    assert float(score_row["lineage_score"]) == pytest.approx(expected.lineage_score)
    assert float(score_row["lineage_score"]) != pytest.approx(0.999)


def test_score_file_tamper_breaks_frozen_hash(tmp_path: Path) -> None:
    _, paths, _ = _freeze_fixture(tmp_path)
    manifest = _read_json(paths["manifest"])
    original = paths["scores"].read_bytes()
    paths["scores"].write_bytes(original + b"tamper")
    assert sha256_bytes(paths["scores"].read_bytes()) != manifest["score_file_sha256"]


@pytest.mark.parametrize(
    "tamper_target",
    ["scores", "manifest", "receipt", "observable", "source_manifest", "package"],
)
def test_score_freeze_verifier_rejects_bound_artifact_tamper(
    tmp_path: Path,
    tamper_target: str,
) -> None:
    repo = _copy_package_repository(tmp_path, name="bound_repo")
    observable_path, paths, contract_sha = _freeze_fixture(
        tmp_path,
        name="bound",
        repo_root=repo,
    )
    receipt_sha = sha256_bytes(paths["receipt"].read_bytes())
    source_manifest = tmp_path / "bound_source_manifest.json"
    source_manifest_sha = sha256_bytes(source_manifest.read_bytes())
    if tamper_target in {"scores", "manifest", "receipt"}:
        target = paths[tamper_target]
    elif tamper_target == "observable":
        target = observable_path
    elif tamper_target == "source_manifest":
        target = source_manifest
    else:
        target = repo / "src/zerogate_sim/v1_8_lineage_predictor.py"
    target.write_bytes(target.read_bytes() + b"tamper")

    with pytest.raises(LineageSchemaError):
        verify_lineage_score_freeze(
            paths["scores"].parent,
            observable_input_path=observable_path,
            source_manifest_path=source_manifest,
            expected_source_manifest_sha256=source_manifest_sha,
            allowed_input_root=tmp_path,
            expected_source_purpose=SOURCE_PURPOSE,
            expected_predictor_contract_sha256=contract_sha,
            expected_receipt_sha256=receipt_sha,
            repo_root=repo,
        )


@pytest.mark.parametrize("bad_value", [False, 0, 1, "true", None])
def test_score_freeze_synthetic_only_is_exact_boolean(tmp_path: Path, bad_value: object) -> None:
    repo = _copy_package_repository(tmp_path)
    package = verify_predictor_package(repo)
    observable = tmp_path / "observable.jsonl"
    write_lineage_inputs(observable, [_frames(0.2, 0.8, 0.9)])
    source_manifest, source_manifest_sha = _write_source_manifest(
        tmp_path,
        observable,
        name="synthetic_declaration",
    )
    kwargs = {
        "observable_input_path": observable,
        "source_manifest_path": source_manifest,
        "expected_source_manifest_sha256": source_manifest_sha,
        "allowed_input_root": tmp_path,
        "expected_source_purpose": SOURCE_PURPOSE,
        "expected_predictor_contract_sha256": package.contract_sha256,
        "repo_root": repo,
    }
    if bad_value is False:
        # False is a valid exact classification: not every future input must be synthetic.
        paths = freeze_lineage_scores(
            tmp_path / "out",
            **kwargs,
            synthetic_only=False,
        )
        assert _read_json(paths["manifest"])["synthetic_only_declared"] is False
        return

    with pytest.raises(LineageSchemaError, match="exact boolean"):
        freeze_lineage_scores(
            tmp_path / "out",
            **kwargs,
            synthetic_only=bad_value,  # type: ignore[arg-type]
        )


def test_v1_8_1_facade_when_present(tmp_path: Path) -> None:
    module_name = "zerogate_sim.v1_8_1_lineage_predictor_package"
    if importlib.util.find_spec(module_name) is None:
        pytest.skip("v1.8.1 facade is not present in this implementation snapshot")
    facade = importlib.import_module(module_name)
    assert callable(getattr(facade, "main"))
    public_builder = getattr(facade, "build_v1_8_1_lineage_predictor_package", None)
    assert callable(public_builder)
    paths = public_builder(tmp_path / "facade")
    decision = _read_json(paths["decision"])
    assert decision["decision"] == facade.DECISION
    assert decision["scientific_status"] == facade.SCIENTIFIC_STATUS
    assert decision["historical_native_witness"] == "C_Z = min(D, P, R, B)"
    assert decision["predictor_formula"].startswith("lineage_score =")
    assert "native_witness" not in decision
    assert decision["native_math_mutated"] is False
    assert decision["package_binding_verified"] is True
    assert decision["predictor_execution_loaded_from_verified_source_snapshot"] is True
    assert decision["score_freeze_verified"] is True
    assert decision["required_rank_reversal_passed"] is True
    assert decision["row_permutation_equivariant"] is True
    assert decision["identifier_field_rejected"] is True
    assert decision["label_field_rejected"] is True
    assert decision["package_tamper_rejected"] is True
    assert decision["score_tamper_rejected"] is True
    assert decision["decision_rule_selected"] is False
    assert decision["selected_threshold_option"] is None
    assert decision["scientific_thresholds_selected"] is False
    assert decision["trinary_predictions_emitted"] is False
    assert decision["dta_transfer_go"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["release_go"] is False
    assert paths["bundle"].is_file()
