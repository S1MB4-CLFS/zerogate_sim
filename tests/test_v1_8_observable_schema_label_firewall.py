from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import MappingProxyType

import pytest

import zerogate_sim.v1_8_prediction_freeze as prediction_freeze_module
from zerogate_sim.v1_8_label_join import (
    build_failure_capability_rows,
    evaluate_frozen_predictions,
    evaluate_role_predictions,
    failure_capability_passed,
    load_label_vault,
    verify_frozen_predictions,
)
from zerogate_sim.v1_8_observable_schema import (
    CURRENT_VERSION,
    FORBIDDEN_FIELD_EXAMPLES,
    LabeledSourceRecord,
    OBSERVABLE_FIELDS,
    SCHEMA_ID,
    ObservableFirewallError,
    observable_schema_document,
    observable_schema_sha256,
    read_csv_exact,
    read_observable_inputs,
    sha256_file,
    stable_sha256,
    validate_observables,
    write_canonical_json,
    write_csv_exact,
    write_observable_label_split,
)
from zerogate_sim.v1_8_observable_schema_label_firewall import (
    DECISION,
    OUTPUT_FILES,
    SCIENTIFIC_STATUS,
    build_v1_8_observable_schema_label_firewall,
    main,
)
from zerogate_sim.v1_8_prediction_freeze import (
    PredictionProposal,
    freeze_predictions,
)


FEATURE_ROWS = [
    {
        "strength": 0.9,
        "distinction": 0.8,
        "polarity": 0.7,
        "relation": 0.6,
        "return_observed": 0.5,
        "echo_mimic_score": 0.1,
        "observed_stability_score": 0.85,
    },
    {
        "strength": 0.5,
        "distinction": 0.6,
        "polarity": 0.55,
        "relation": 0.45,
        "return_observed": 0.35,
        "echo_mimic_score": 0.25,
        "observed_stability_score": 0.5,
    },
    {
        "strength": 0.7,
        "distinction": 0.75,
        "polarity": 0.65,
        "relation": 0.7,
        "return_observed": 0.2,
        "echo_mimic_score": 0.8,
        "observed_stability_score": 0.3,
    },
]


def _records(
    *,
    ids: tuple[str, str, str] = ("alpha", "beta", "gamma"),
    roles: tuple[str, str, str] = ("expresser", "latent", "trap"),
) -> list[LabeledSourceRecord]:
    return [
        LabeledSourceRecord(source_id, dict(features), role)
        for source_id, features, role in zip(ids, FEATURE_ROWS, roles, strict=True)
    ]


def _predictor() -> tuple[object, str]:
    proposals = (
        PredictionProposal(0.8, 1),
        PredictionProposal(0.0, 0),
        PredictionProposal(-0.8, -1),
    )
    lookup = {
        stable_sha256(features): proposal
        for features, proposal in zip(FEATURE_ROWS, proposals, strict=True)
    }

    def predictor(values: object) -> PredictionProposal:
        return lookup[stable_sha256(dict(values))]

    return predictor, stable_sha256(
        {
            "id": "test-synthetic-vector",
            "not_scientific": True,
            "values": [proposal.__dict__ for proposal in proposals],
        }
    )


def _frozen_probe(
    root: Path,
    *,
    ids: tuple[str, str, str] = ("alpha", "beta", "gamma"),
    roles: tuple[str, str, str] = ("expresser", "latent", "trap"),
) -> tuple[dict[str, Path], dict[str, Path], str]:
    split = write_observable_label_split(
        root / "split",
        _records(ids=ids, roles=roles),
        namespace="test-v1.8",
    )
    predictor, predictor_hash = _predictor()
    freeze = freeze_predictions(
        root / "freeze",
        observable_input_path=split["observable_inputs"],
        predictor=predictor,
        predictor_id="test-synthetic-vector-v1",
        predictor_contract_sha256=predictor_hash,
    )
    return split, freeze, sha256_file(freeze["receipt"])


def _evaluate(
    split: dict[str, Path],
    freeze: dict[str, Path],
    receipt_sha: str,
    *,
    label_read_observer: object | None = None,
    split_manifest_sha: str | None = None,
) -> dict[str, object]:
    kwargs = {}
    if label_read_observer is not None:
        kwargs["label_read_observer"] = label_read_observer
    return evaluate_frozen_predictions(
        observable_input_path=split["observable_inputs"],
        prediction_path=freeze["predictions"],
        manifest_path=freeze["manifest"],
        receipt_path=freeze["receipt"],
        expected_receipt_sha256=receipt_sha,
        split_manifest_path=split["manifest"],
        expected_split_manifest_sha256=(
            split_manifest_sha or sha256_file(split["manifest"])
        ),
        join_keys_path=split["join_keys"],
        label_vault_path=split["label_vault"],
        **kwargs,
    )


def _refresh_split_manifest_hashes(split: dict[str, Path]) -> None:
    manifest = json.loads(split["manifest"].read_text(encoding="utf-8"))
    manifest["observable_input_sha256"] = sha256_file(split["observable_inputs"])
    manifest["join_key_sha256"] = sha256_file(split["join_keys"])
    manifest["label_vault_sha256"] = sha256_file(split["label_vault"])
    write_canonical_json(split["manifest"], manifest)


def test_observable_schema_is_an_exact_minimal_allowlist() -> None:
    assert OBSERVABLE_FIELDS == (
        "strength",
        "distinction",
        "polarity",
        "relation",
        "return_observed",
        "echo_mimic_score",
        "observed_stability_score",
    )
    schema = observable_schema_document()
    assert schema["schema_id"] == SCHEMA_ID
    assert schema["field_policy"] == "exact_allowlist_unknown_fields_fail_closed"
    assert schema["scientific_thresholds_selected"] is False
    assert len(observable_schema_sha256()) == 64


@pytest.mark.parametrize(
    "field",
    [
        "truth_role",
        "candidate_id",
        "kind",
        "expected_trinary",
        "semantic_hint",
        "echo_mimic_band",
        "zero_coherence",
        "zero_depth",
        "feature_earned_rate",
        "target_raw_false_one_rate",
        "final_earned_one_count",
    ],
)
def test_forbidden_or_unknown_fields_fail_closed(field: str) -> None:
    values = dict(FEATURE_ROWS[0])
    values[field] = ""
    with pytest.raises(ObservableFirewallError, match="extras"):
        validate_observables(values)


def test_forbidden_examples_cover_known_legacy_leaks() -> None:
    required = {
        "truth_role",
        "candidate_id",
        "candidate_profile",
        "echo_mimic_band",
        "feature_earned_rate",
        "raw_false_one_pressure",
        "relation_debt_count",
    }
    assert required <= set(FORBIDDEN_FIELD_EXAMPLES)


def test_missing_observable_fails_closed() -> None:
    values = dict(FEATURE_ROWS[0])
    del values["relation"]
    with pytest.raises(ObservableFirewallError, match="missing"):
        validate_observables(values)


@pytest.mark.parametrize("bad", [True, "", "not-a-number", float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_observable_never_becomes_zero(bad: object) -> None:
    values = dict(FEATURE_ROWS[0])
    values["strength"] = bad
    with pytest.raises(ObservableFirewallError):
        validate_observables(values)


def test_negative_zero_observable_is_canonicalized() -> None:
    values = dict(FEATURE_ROWS[0])
    values["strength"] = -0.0
    validated = validate_observables(values)
    assert "-0.0" not in json.dumps(validated)


def test_synthetic_classification_requires_exact_boolean(tmp_path: Path) -> None:
    with pytest.raises(ObservableFirewallError, match="exact boolean"):
        write_observable_label_split(
            tmp_path / "split",
            _records(),
            namespace="test-v1.8",
            synthetic_only="false",
        )


def test_split_physically_removes_identifiers_and_labels_from_predictor_input(tmp_path: Path) -> None:
    split = write_observable_label_split(
        tmp_path / "split",
        _records(),
        namespace="test-v1.8",
    )
    predictor_text = split["observable_inputs"].read_text(encoding="utf-8")
    assert "alpha" not in predictor_text
    assert "zg8_" not in predictor_text
    assert "expresser" not in predictor_text
    assert "trap" not in predictor_text
    assert "truth_role" not in predictor_text
    assert read_observable_inputs(split["observable_inputs"])[0]["observables"] == FEATURE_ROWS[0]


def test_duplicate_source_ids_fail_before_artifacts_are_written(tmp_path: Path) -> None:
    records = _records(ids=("same", "same", "third"))
    with pytest.raises(ObservableFirewallError, match="duplicate source_record_id"):
        write_observable_label_split(tmp_path / "split", records, namespace="test-v1.8")


def test_noncanonical_or_duplicate_json_keys_fail(tmp_path: Path) -> None:
    path = tmp_path / "observables.jsonl"
    path.write_text(
        '{"row_index":0,"row_index":0,"observables":{}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ObservableFirewallError, match="duplicate JSON key"):
        read_observable_inputs(path)

    row = {"row_index": 0, "observables": FEATURE_ROWS[0]}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ObservableFirewallError, match="non-canonical"):
        read_observable_inputs(path)


def test_predictor_receives_only_immutable_typed_observables(tmp_path: Path) -> None:
    split = write_observable_label_split(
        tmp_path / "split",
        _records(),
        namespace="test-v1.8",
    )
    received: list[object] = []

    def spy(values: object) -> PredictionProposal:
        received.append(values)
        assert type(values) is MappingProxyType
        assert tuple(values) == OBSERVABLE_FIELDS
        assert all(type(value) is float for value in values.values())
        assert "blind_case_id" not in values
        with pytest.raises(TypeError):
            values["candidate_id"] = "leak"
        return PredictionProposal(0.0, 0)

    freeze_predictions(
        tmp_path / "freeze",
        observable_input_path=split["observable_inputs"],
        predictor=spy,
        predictor_id="immutable-spy-v1",
        predictor_contract_sha256=stable_sha256("immutable-spy-v1"),
    )
    assert len(received) == 6


def test_observable_snapshot_change_during_callback_fails_closed(tmp_path: Path) -> None:
    split = write_observable_label_split(
        tmp_path / "split",
        _records(),
        namespace="test-v1.8",
    )
    predictor, predictor_hash = _predictor()
    changed = False

    def mutating_predictor(values: object) -> PredictionProposal:
        nonlocal changed
        proposal = predictor(values)
        if not changed:
            changed = True
            path = split["observable_inputs"]
            path.write_bytes(path.read_bytes() + b" ")
        return proposal

    with pytest.raises(ObservableFirewallError, match="changed during prediction freeze"):
        freeze_predictions(
            tmp_path / "freeze",
            observable_input_path=split["observable_inputs"],
            predictor=mutating_predictor,
            predictor_id="observable-mutation-canary-v1",
            predictor_contract_sha256=predictor_hash,
        )


def test_position_dependent_predictor_fails_reverse_order_repeat(tmp_path: Path) -> None:
    split = write_observable_label_split(
        tmp_path / "split",
        _records(),
        namespace="test-v1.8",
    )
    calls = 0

    def positional_predictor(_: object) -> PredictionProposal:
        nonlocal calls
        values = (1, 0, -1)
        trinary = values[calls % 3]
        calls += 1
        return PredictionProposal(float(trinary), trinary)

    with pytest.raises(ObservableFirewallError, match="reverse-order repeat"):
        freeze_predictions(
            tmp_path / "freeze",
            observable_input_path=split["observable_inputs"],
            predictor=positional_predictor,
            predictor_id="position-leak-canary-v1",
            predictor_contract_sha256=stable_sha256("position-leak-canary-v1"),
        )


def test_prediction_stage_has_no_label_argument_or_label_join_import() -> None:
    assert all("label" not in name for name in inspect.signature(freeze_predictions).parameters)
    source = inspect.getsource(prediction_freeze_module)
    assert "v1_8_label_join" not in source


@pytest.mark.parametrize(
    "proposal",
    [
        {"prediction_score": 0.0, "proposed_trinary": 0},
        PredictionProposal(float("nan"), 0),
        PredictionProposal(0.0, 2),
        PredictionProposal(0.0, True),
    ],
)
def test_invalid_predictor_output_fails_closed(tmp_path: Path, proposal: object) -> None:
    split = write_observable_label_split(
        tmp_path / "split",
        _records(),
        namespace="test-v1.8",
    )

    def bad_predictor(_: object) -> object:
        return proposal

    with pytest.raises(ObservableFirewallError):
        freeze_predictions(
            tmp_path / "freeze",
            observable_input_path=split["observable_inputs"],
            predictor=bad_predictor,
            predictor_id="invalid-output-v1",
            predictor_contract_sha256=stable_sha256("invalid-output-v1"),
        )


def test_freeze_manifest_binds_every_prejoin_artifact(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    predictions, manifest = verify_frozen_predictions(
        observable_input_path=split["observable_inputs"],
        prediction_path=freeze["predictions"],
        manifest_path=freeze["manifest"],
        receipt_path=freeze["receipt"],
        expected_receipt_sha256=receipt_sha,
    )
    assert len(predictions) == 3
    assert manifest["observable_input_sha256"] == sha256_file(split["observable_inputs"])
    assert manifest["prediction_file_sha256"] == sha256_file(freeze["predictions"])
    assert manifest["schema_sha256"] == observable_schema_sha256()
    assert manifest["label_fields_in_callback_arguments"] is False
    assert manifest["identifier_fields_in_callback_arguments"] is False
    assert manifest["reverse_order_repeat_consistency_passed"] is True
    assert manifest["predictor_contract_code_binding_verified"] is False


def test_freeze_refuses_overwrite(tmp_path: Path) -> None:
    split, _, _ = _frozen_probe(tmp_path)
    predictor, predictor_hash = _predictor()
    with pytest.raises(ObservableFirewallError, match="overwrite"):
        freeze_predictions(
            tmp_path / "freeze",
            observable_input_path=split["observable_inputs"],
            predictor=predictor,
            predictor_id="test-synthetic-vector-v1",
            predictor_contract_sha256=predictor_hash,
        )


def test_prediction_tamper_fails_before_label_loader_runs(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    original = freeze["predictions"].read_bytes()
    freeze["predictions"].write_bytes(original + b"tamper")
    called = False

    def forbidden_label_read(_: Path) -> None:
        nonlocal called
        called = True

    with pytest.raises(ObservableFirewallError, match="prediction_file_sha256|prediction hash"):
        _evaluate(split, freeze, receipt_sha, label_read_observer=forbidden_label_read)
    assert called is False


def test_manifest_tamper_is_rejected_by_prejoin_receipt(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    value = json.loads(freeze["manifest"].read_text(encoding="utf-8"))
    value["prediction_count"] = 99
    freeze["manifest"].write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ObservableFirewallError, match="manifest_sha256"):
        _evaluate(split, freeze, receipt_sha)


def test_split_manifest_tamper_is_rejected_before_label_read(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    expected_split_sha = sha256_file(split["manifest"])
    manifest = json.loads(split["manifest"].read_text(encoding="utf-8"))
    manifest["record_count"] = 99
    write_canonical_json(split["manifest"], manifest)
    called = False

    def forbidden_label_read(_: Path) -> None:
        nonlocal called
        called = True

    with pytest.raises(ObservableFirewallError, match="split manifest SHA-256"):
        _evaluate(
            split,
            freeze,
            receipt_sha,
            split_manifest_sha=expected_split_sha,
            label_read_observer=forbidden_label_read,
        )
    assert called is False


def test_label_vault_tamper_is_rejected_by_sealed_split_manifest(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    original = split["label_vault"].read_bytes()
    split["label_vault"].write_bytes(original.replace(b"trap", b"latent"))
    with pytest.raises(ObservableFirewallError, match="label-vault hash mismatch"):
        _evaluate(split, freeze, receipt_sha)


def test_label_permutation_changes_evaluation_not_prediction_bytes(tmp_path: Path) -> None:
    first_split, first_freeze, first_receipt = _frozen_probe(tmp_path / "first")
    second_split, second_freeze, second_receipt = _frozen_probe(
        tmp_path / "second",
        roles=("trap", "expresser", "latent"),
    )
    assert first_split["observable_inputs"].read_bytes() == second_split["observable_inputs"].read_bytes()
    assert first_freeze["predictions"].read_bytes() == second_freeze["predictions"].read_bytes()
    assert first_receipt == second_receipt
    first = _evaluate(first_split, first_freeze, first_receipt)
    second = _evaluate(second_split, second_freeze, second_receipt)
    assert first["correct_count"] == 3
    assert second["correct_count"] == 0
    assert second["false_crown_count"] == 1
    assert second["missed_earned_count"] == 1
    assert second["hold_resisted_count"] == 1
    assert first["prediction_values_sha256"] == second["prediction_values_sha256"]


def test_identifier_renaming_changes_only_sealed_join_keys(tmp_path: Path) -> None:
    first_split, first_freeze, first_receipt = _frozen_probe(tmp_path / "first")
    renamed_split, renamed_freeze, renamed_receipt = _frozen_probe(
        tmp_path / "renamed",
        ids=("renamed-one", "renamed-two", "renamed-three"),
    )
    assert first_split["observable_inputs"].read_bytes() == renamed_split["observable_inputs"].read_bytes()
    assert first_freeze["predictions"].read_bytes() == renamed_freeze["predictions"].read_bytes()
    assert first_receipt == renamed_receipt
    assert first_split["join_keys"].read_bytes() != renamed_split["join_keys"].read_bytes()
    assert _evaluate(first_split, first_freeze, first_receipt)["correct_count"] == 3
    assert _evaluate(renamed_split, renamed_freeze, renamed_receipt)["correct_count"] == 3


@pytest.mark.parametrize("mode", ["duplicate", "missing", "extra"])
def test_exact_label_join_rejects_duplicate_missing_or_extra_ids(tmp_path: Path, mode: str) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    rows = load_label_vault(split["label_vault"])
    if mode == "duplicate":
        rows.append(dict(rows[0]))
    elif mode == "missing":
        rows.pop()
    else:
        rows.append({"blind_case_id": "zg8_000000000000000000000000", "evaluation_role": "trap"})
    write_csv_exact(
        split["label_vault"],
        header=("blind_case_id", "evaluation_role"),
        rows=((row["blind_case_id"], row["evaluation_role"]) for row in rows),
    )
    _refresh_split_manifest_hashes(split)
    with pytest.raises(ObservableFirewallError, match="duplicate|equality"):
        _evaluate(split, freeze, receipt_sha)


def test_shuffled_label_rows_join_by_exact_id_not_position(tmp_path: Path) -> None:
    split, freeze, receipt_sha = _frozen_probe(tmp_path)
    before = _evaluate(split, freeze, receipt_sha)
    rows = list(reversed(load_label_vault(split["label_vault"])))
    write_csv_exact(
        split["label_vault"],
        header=("blind_case_id", "evaluation_role"),
        rows=((row["blind_case_id"], row["evaluation_role"]) for row in rows),
    )
    _refresh_split_manifest_hashes(split)
    after = _evaluate(split, freeze, receipt_sha)
    assert {
        key: value
        for key, value in before.items()
        if key != "sealed_split_manifest_sha256"
    } == {
        key: value
        for key, value in after.items()
        if key != "sealed_split_manifest_sha256"
    }


def test_duplicate_csv_header_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("row_index,row_index\n0,0\n", encoding="utf-8")
    with pytest.raises(ObservableFirewallError, match="duplicate CSV header"):
        read_csv_exact(path, header=("row_index", "blind_case_id"))


def test_failure_capability_exposes_false_crowns_and_dead_safe_baselines() -> None:
    rows = build_failure_capability_rows()
    assert failure_capability_passed(rows) is True
    by_case = {str(row["case"]): row for row in rows}
    assert by_case["injected_false_crown"]["false_crown_count"] == 1
    assert by_case["always_hold"]["false_crown_count"] == 0
    assert by_case["always_hold"]["observed_status"] == "INVALID_ALWAYS_HOLD"
    assert by_case["always_crown"]["observed_status"] == "INVALID_ALWAYS_CROWN"
    assert by_case["always_resist"]["observed_status"] == "INVALID_ALWAYS_RESIST"


def test_even_perfect_synthetic_evaluation_has_no_scientific_authority() -> None:
    result = evaluate_role_predictions(
        ["expresser", "latent", "trap"],
        [1, 0, -1],
    )
    assert result["evaluation_status"] == "EVALUATOR_OPERABLE"
    assert result["scientific_status"] == "HOLD_FIREWALL_INFRASTRUCTURE_ONLY"
    assert result["scientific_thresholds_selected"] is False
    assert result["core_question_closed"] is False


def test_v1_8_report_is_local_green_but_scientifically_held(tmp_path: Path) -> None:
    paths = build_v1_8_observable_schema_label_firewall(tmp_path / "out")
    for key, filename in OUTPUT_FILES.items():
        assert paths[key].exists(), filename
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    assert decision["version"] == CURRENT_VERSION
    assert decision["decision"] == DECISION
    assert decision["scientific_status"] == SCIENTIFIC_STATUS
    assert decision["label_permutation_prediction_invariant"] is True
    assert decision["identifier_renaming_prediction_invariant"] is True
    assert decision["row_permutation_prediction_equivariant"] is True
    assert decision["forbidden_field_negative_canary_passed"] is True
    assert decision["missing_field_negative_canary_passed"] is True
    assert decision["nonfinite_negative_canary_passed"] is True
    assert decision["position_leak_negative_canary_passed"] is True
    assert decision["prediction_tamper_negative_canary_passed"] is True
    assert decision["sealed_label_tamper_negative_canary_passed"] is True
    assert decision["failure_capability_passed"] is True
    assert decision["scientific_scorer_implemented"] is False
    assert decision["scientific_thresholds_selected"] is False
    assert decision["frozen_holdout_revealed"] is False
    assert decision["manuscript_v2_started"] is False
    assert decision["dta_transfer_go"] is False
    assert decision["release_go"] is False


def test_v1_8_cli(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["--out", str(out)]) == 0
    assert (out / OUTPUT_FILES["decision"]).exists()
    assert (out / OUTPUT_FILES["bundle"]).exists()
