from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Callable, Iterable

from zerogate_sim.v1_8_observable_schema import (
    CURRENT_VERSION,
    EVALUATION_ROLES,
    ROLE_TO_TRINARY,
    SCHEMA_ID,
    SPLIT_MANIFEST_FIELDS,
    ObservableFirewallError,
    observable_schema_sha256,
    read_csv_exact,
    read_csv_exact_bytes,
    read_observable_inputs_bytes,
    sha256_bytes,
    stable_sha256,
    strict_json_loads,
    validate_blind_case_id,
    validate_sha256,
)

PREDICTION_HEADER = ("row_index", "prediction_score", "proposed_trinary")
JOIN_KEY_HEADER = ("row_index", "blind_case_id")
LABEL_HEADER = ("blind_case_id", "evaluation_role")
INTEGER_TEXT_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
PREDICTOR_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")

MANIFEST_FIELDS = {
    "version",
    "freeze_state",
    "schema_id",
    "schema_sha256",
    "observable_input_sha256",
    "observable_values_sha256",
    "observable_row_index_sha256",
    "predictor_id",
    "declared_predictor_contract_sha256",
    "predictor_contract_code_binding_verified",
    "prediction_count",
    "prediction_file_sha256",
    "prediction_values_sha256",
    "identifier_fields_in_callback_arguments",
    "label_fields_in_callback_arguments",
    "reverse_order_repeat_consistency_passed",
    "freeze_module_accepts_label_paths",
    "receipt_required_for_join",
    "synthetic_only",
    "scientific_thresholds_selected",
    "scientific_status",
}

RECEIPT_FIELDS = {
    "version",
    "receipt_state",
    "observable_input_sha256",
    "prediction_file_sha256",
    "manifest_sha256",
    "prediction_values_sha256",
    "external_timestamp_proof",
    "scientific_thresholds_selected",
}

LabelReadObserver = Callable[[Path], None]


def _read_artifact_bytes(path: Path, *, kind: str) -> bytes:
    if not path.is_file():
        raise ObservableFirewallError(f"missing {kind}: {path}")
    return path.read_bytes()


def _load_json_object_bytes(
    data: bytes,
    *,
    source: str,
    expected_fields: set[str],
) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ObservableFirewallError(f"{source}: JSON artifact is not UTF-8") from exc
    value = strict_json_loads(text, source=source)
    if not isinstance(value, dict) or set(value) != expected_fields:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise ObservableFirewallError(
            f"{source}: exact JSON fields required; got {actual!r}"
        )
    return value


def _strict_row_index(value: object, *, source: str) -> int:
    if not isinstance(value, str) or INTEGER_TEXT_RE.fullmatch(value) is None:
        raise ObservableFirewallError(f"{source}: row_index must be canonical nonnegative integer")
    return int(value)


def _strict_prediction_score(value: object, *, source: str) -> float:
    if not isinstance(value, str) or not value:
        raise ObservableFirewallError(f"{source}: prediction_score is required")
    try:
        score = float(value)
    except ValueError as exc:
        raise ObservableFirewallError(f"{source}: malformed prediction_score {value!r}") from exc
    if not math.isfinite(score):
        raise ObservableFirewallError(f"{source}: prediction_score must be finite")
    if score == 0.0:
        score = 0.0
    if value != format(score, ".17g"):
        raise ObservableFirewallError(f"{source}: prediction_score is not canonical")
    return score


def _strict_trinary(value: object, *, source: str) -> int:
    if value not in {"-1", "0", "1"}:
        raise ObservableFirewallError(f"{source}: proposed_trinary must be -1, 0, or 1")
    return int(value)


def _load_prediction_rows_bytes(data: bytes, *, source_path: Path) -> list[dict[str, object]]:
    raw_rows = read_csv_exact_bytes(
        data,
        source=str(source_path),
        header=PREDICTION_HEADER,
    )
    out: list[dict[str, object]] = []
    seen: set[int] = set()
    for line_number, row in enumerate(raw_rows, start=2):
        source = f"{source_path}:{line_number}"
        row_index = _strict_row_index(row["row_index"], source=source)
        if row_index in seen:
            raise ObservableFirewallError(f"{source}: duplicate row_index {row_index}")
        seen.add(row_index)
        out.append(
            {
                "row_index": row_index,
                "prediction_score": _strict_prediction_score(
                    row["prediction_score"], source=source
                ),
                "proposed_trinary": _strict_trinary(
                    row["proposed_trinary"], source=source
                ),
            }
        )
    expected = list(range(len(out)))
    actual = [int(row["row_index"]) for row in out]
    if actual != expected:
        raise ObservableFirewallError(
            f"{source_path}: prediction rows must be exact ordered sequence"
        )
    return out


def _prediction_values_sha256(rows: list[dict[str, object]]) -> str:
    return stable_sha256(
        [
            {
                "prediction_score": float(row["prediction_score"]),
                "proposed_trinary": int(row["proposed_trinary"]),
            }
            for row in rows
        ]
    )


def verify_frozen_predictions(
    *,
    observable_input_path: str | Path,
    prediction_path: str | Path,
    manifest_path: str | Path,
    receipt_path: str | Path,
    expected_receipt_sha256: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Verify every pre-join artifact without accepting a label path."""

    observable_source = Path(observable_input_path)
    prediction_source = Path(prediction_path)
    manifest_source = Path(manifest_path)
    receipt_source = Path(receipt_path)
    expected_receipt = validate_sha256(
        expected_receipt_sha256,
        field="expected_receipt_sha256",
        source="label join",
    )
    receipt_bytes = _read_artifact_bytes(receipt_source, kind="receipt")
    if sha256_bytes(receipt_bytes) != expected_receipt:
        raise ObservableFirewallError("pre-label receipt SHA-256 mismatch")

    manifest_bytes = _read_artifact_bytes(manifest_source, kind="freeze manifest")
    observable_bytes = _read_artifact_bytes(observable_source, kind="observable input")
    prediction_bytes = _read_artifact_bytes(prediction_source, kind="prediction file")
    receipt = _load_json_object_bytes(
        receipt_bytes,
        source=str(receipt_source),
        expected_fields=RECEIPT_FIELDS,
    )
    manifest = _load_json_object_bytes(
        manifest_bytes,
        source=str(manifest_source),
        expected_fields=MANIFEST_FIELDS,
    )

    expected_manifest_values = {
        "version": CURRENT_VERSION,
        "freeze_state": "FROZEN_PRE_LABEL_JOIN",
        "schema_id": SCHEMA_ID,
        "schema_sha256": observable_schema_sha256(),
        "predictor_contract_code_binding_verified": False,
        "identifier_fields_in_callback_arguments": False,
        "label_fields_in_callback_arguments": False,
        "reverse_order_repeat_consistency_passed": True,
        "freeze_module_accepts_label_paths": False,
        "receipt_required_for_join": True,
        "scientific_thresholds_selected": False,
        "scientific_status": "HOLD_FIREWALL_INFRASTRUCTURE_ONLY",
    }
    for field, expected in expected_manifest_values.items():
        actual = manifest.get(field)
        if type(actual) is not type(expected) or actual != expected:
            raise ObservableFirewallError(f"freeze manifest field {field!r} is invalid")
    if type(manifest.get("synthetic_only")) is not bool:
        raise ObservableFirewallError("freeze manifest synthetic_only must be boolean")
    count = manifest.get("prediction_count")
    if type(count) is not int or count < 1:
        raise ObservableFirewallError("freeze manifest prediction_count must be a positive integer")
    predictor_id = manifest.get("predictor_id")
    if not isinstance(predictor_id, str) or PREDICTOR_ID_RE.fullmatch(predictor_id) is None:
        raise ObservableFirewallError("freeze manifest predictor_id is invalid")
    if (
        type(receipt.get("version")) is not str
        or receipt.get("version") != CURRENT_VERSION
        or type(receipt.get("receipt_state")) is not str
        or receipt.get("receipt_state") != "PRE_LABEL_JOIN_RECEIPT"
        or receipt.get("external_timestamp_proof") is not False
        or receipt.get("scientific_thresholds_selected") is not False
    ):
        raise ObservableFirewallError("pre-label receipt contract is invalid")

    observable_hash = sha256_bytes(observable_bytes)
    prediction_hash = sha256_bytes(prediction_bytes)
    manifest_hash = sha256_bytes(manifest_bytes)
    for field, actual in (
        ("observable_input_sha256", observable_hash),
        ("prediction_file_sha256", prediction_hash),
        ("manifest_sha256", manifest_hash),
    ):
        if receipt.get(field) != actual:
            raise ObservableFirewallError(f"receipt {field} mismatch")
    if manifest.get("observable_input_sha256") != observable_hash:
        raise ObservableFirewallError("freeze manifest observable hash mismatch")
    if manifest.get("prediction_file_sha256") != prediction_hash:
        raise ObservableFirewallError("freeze manifest prediction hash mismatch")

    for field in (
        "schema_sha256",
        "observable_input_sha256",
        "observable_values_sha256",
        "observable_row_index_sha256",
        "declared_predictor_contract_sha256",
        "prediction_file_sha256",
        "prediction_values_sha256",
    ):
        validate_sha256(manifest.get(field), field=field, source="freeze manifest")
    for field in (
        "observable_input_sha256",
        "prediction_file_sha256",
        "manifest_sha256",
        "prediction_values_sha256",
    ):
        validate_sha256(receipt.get(field), field=field, source="pre-label receipt")

    observable_rows = read_observable_inputs_bytes(
        observable_bytes,
        source=str(observable_source),
    )
    prediction_rows = _load_prediction_rows_bytes(
        prediction_bytes,
        source_path=prediction_source,
    )
    if count != len(prediction_rows):
        raise ObservableFirewallError("freeze manifest prediction count mismatch")
    if len(observable_rows) != len(prediction_rows):
        raise ObservableFirewallError("observable/prediction count mismatch")
    row_hash = stable_sha256([int(row["row_index"]) for row in prediction_rows])
    if manifest.get("observable_row_index_sha256") != row_hash:
        raise ObservableFirewallError("freeze manifest row-index hash mismatch")
    observable_values_hash = stable_sha256(
        [dict(row["observables"]) for row in observable_rows]
    )
    if manifest.get("observable_values_sha256") != observable_values_hash:
        raise ObservableFirewallError("freeze manifest observable-values hash mismatch")
    values_hash = _prediction_values_sha256(prediction_rows)
    if manifest.get("prediction_values_sha256") != values_hash:
        raise ObservableFirewallError("freeze manifest prediction-values hash mismatch")
    if receipt.get("prediction_values_sha256") != values_hash:
        raise ObservableFirewallError("receipt prediction-values hash mismatch")
    return prediction_rows, manifest


def load_label_vault(path: Path) -> list[dict[str, str]]:
    return read_csv_exact(path, header=LABEL_HEADER)


def _load_join_keys_bytes(data: bytes, *, path: Path) -> dict[int, str]:
    rows = read_csv_exact_bytes(data, source=str(path), header=JOIN_KEY_HEADER)
    out: dict[int, str] = {}
    blind_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        source = f"{path}:{line_number}"
        row_index = _strict_row_index(row["row_index"], source=source)
        blind_id = validate_blind_case_id(row["blind_case_id"], source=source)
        if row_index in out:
            raise ObservableFirewallError(f"{source}: duplicate row_index")
        if blind_id in blind_ids:
            raise ObservableFirewallError(f"{source}: duplicate blind_case_id")
        out[row_index] = blind_id
        blind_ids.add(blind_id)
    return out


def _validate_label_rows(rows: Iterable[dict[str, str]], *, source: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line_number, row in enumerate(rows, start=2):
        if set(row) != set(LABEL_HEADER):
            raise ObservableFirewallError(f"{source}:{line_number}: invalid label fields")
        blind_id = validate_blind_case_id(row["blind_case_id"], source=str(source))
        role = row["evaluation_role"]
        if role not in EVALUATION_ROLES:
            raise ObservableFirewallError(f"{source}:{line_number}: invalid evaluation_role")
        if blind_id in out:
            raise ObservableFirewallError(f"{source}:{line_number}: duplicate blind_case_id")
        out[blind_id] = role
    if not out:
        raise ObservableFirewallError(f"{source}: no labels")
    return out


def evaluate_role_predictions(
    evaluation_roles: Iterable[str],
    proposed_trinary: Iterable[int],
) -> dict[str, object]:
    roles = list(evaluation_roles)
    predictions = list(proposed_trinary)
    if not roles or len(roles) != len(predictions):
        raise ObservableFirewallError("evaluation requires equal non-empty role/prediction rows")
    for role in roles:
        if role not in EVALUATION_ROLES:
            raise ObservableFirewallError(f"unsupported evaluation role {role!r}")
    for value in predictions:
        if isinstance(value, bool) or type(value) is not int or value not in {-1, 0, 1}:
            raise ObservableFirewallError(f"invalid proposed trinary value {value!r}")

    confusion = {
        f"{role}_pred_{prediction}": sum(
            1
            for actual_role, actual_prediction in zip(roles, predictions, strict=True)
            if actual_role == role and actual_prediction == prediction
        )
        for role in EVALUATION_ROLES
        for prediction in (-1, 0, 1)
    }
    correct = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if ROLE_TO_TRINARY[role] == prediction
    )
    false_crowns = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if role == "trap" and prediction == 1
    )
    hold_overcrowns = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if role == "latent" and prediction == 1
    )
    missed_earned = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if role == "expresser" and prediction != 1
    )
    earned_resisted = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if role == "expresser" and prediction == -1
    )
    hold_resisted = sum(
        1
        for role, prediction in zip(roles, predictions, strict=True)
        if role == "latent" and prediction == -1
    )
    class_coverage = set(roles) == set(EVALUATION_ROLES)
    unique_predictions = set(predictions)
    if not class_coverage:
        status = "INVALID_INCOMPLETE_ROLE_COVERAGE"
    elif unique_predictions == {0}:
        status = "INVALID_ALWAYS_HOLD"
    elif unique_predictions == {1}:
        status = "INVALID_ALWAYS_CROWN"
    elif unique_predictions == {-1}:
        status = "INVALID_ALWAYS_RESIST"
    elif false_crowns:
        status = "DETECTED_FALSE_CROWN"
    elif hold_overcrowns:
        status = "DETECTED_HOLD_OVERCROWN"
    else:
        status = "EVALUATOR_OPERABLE"

    return {
        "evaluation_status": status,
        "scientific_status": "HOLD_FIREWALL_INFRASTRUCTURE_ONLY",
        "row_count": len(roles),
        "class_coverage_complete": class_coverage,
        "constant_prediction": len(unique_predictions) == 1,
        "correct_count": correct,
        "false_crown_count": false_crowns,
        "hold_overcrown_count": hold_overcrowns,
        "missed_earned_count": missed_earned,
        "earned_resisted_count": earned_resisted,
        "hold_resisted_count": hold_resisted,
        "confusion_count": sum(confusion.values()),
        **confusion,
        "scientific_thresholds_selected": False,
        "core_question_closed": False,
    }


def evaluate_frozen_predictions(
    *,
    observable_input_path: str | Path,
    prediction_path: str | Path,
    manifest_path: str | Path,
    receipt_path: str | Path,
    expected_receipt_sha256: str,
    split_manifest_path: str | Path,
    expected_split_manifest_sha256: str,
    join_keys_path: str | Path,
    label_vault_path: str | Path,
    label_read_observer: LabelReadObserver | None = None,
) -> dict[str, object]:
    prediction_rows, manifest = verify_frozen_predictions(
        observable_input_path=observable_input_path,
        prediction_path=prediction_path,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        expected_receipt_sha256=expected_receipt_sha256,
    )

    split_manifest_source = Path(split_manifest_path)
    expected_split_manifest = validate_sha256(
        expected_split_manifest_sha256,
        field="expected_split_manifest_sha256",
        source="label join",
    )
    split_manifest_bytes = _read_artifact_bytes(
        split_manifest_source,
        kind="split manifest",
    )
    if sha256_bytes(split_manifest_bytes) != expected_split_manifest:
        raise ObservableFirewallError("sealed split manifest SHA-256 mismatch")
    split_manifest = _load_json_object_bytes(
        split_manifest_bytes,
        source=str(split_manifest_source),
        expected_fields=SPLIT_MANIFEST_FIELDS,
    )
    expected_split_values = {
        "version": CURRENT_VERSION,
        "split_state": "SEALED_OBSERVABLE_LABEL_SPLIT",
        "schema_id": SCHEMA_ID,
        "schema_sha256": observable_schema_sha256(),
        "predictor_callback_arguments_contain_identifiers": False,
        "predictor_callback_arguments_contain_labels": False,
        "label_artifact_separate_from_predictor_input": True,
        "label_access_isolation_verified": False,
        "split_manifest_hash_required_for_join": True,
        "scientific_thresholds_selected": False,
    }
    for field, expected in expected_split_values.items():
        actual = split_manifest.get(field)
        if type(actual) is not type(expected) or actual != expected:
            raise ObservableFirewallError(f"split manifest field {field!r} is invalid")
    if type(split_manifest.get("synthetic_only")) is not bool:
        raise ObservableFirewallError("split manifest synthetic_only must be boolean")
    if split_manifest.get("synthetic_only") is not manifest.get("synthetic_only"):
        raise ObservableFirewallError("split/freeze synthetic_only classification mismatch")
    record_count = split_manifest.get("record_count")
    if type(record_count) is not int or record_count < 1:
        raise ObservableFirewallError("split manifest record_count must be a positive integer")
    for field in (
        "schema_sha256",
        "observable_input_sha256",
        "join_key_sha256",
        "label_vault_sha256",
    ):
        validate_sha256(split_manifest.get(field), field=field, source="split manifest")
    if split_manifest.get("observable_input_sha256") != manifest.get(
        "observable_input_sha256"
    ):
        raise ObservableFirewallError("split/freeze observable hash mismatch")

    join_path = Path(join_keys_path)
    join_bytes = _read_artifact_bytes(join_path, kind="sealed join keys")
    if sha256_bytes(join_bytes) != split_manifest.get("join_key_sha256"):
        raise ObservableFirewallError("split manifest join-key hash mismatch")
    join_keys = _load_join_keys_bytes(join_bytes, path=join_path)
    prediction_indices = {int(row["row_index"]) for row in prediction_rows}
    if set(join_keys) != prediction_indices:
        raise ObservableFirewallError("prediction and join-key row indices differ")
    if record_count != len(prediction_rows):
        raise ObservableFirewallError("split/prediction record count mismatch")

    # This is intentionally the first label read in the evaluation path.
    label_path = Path(label_vault_path)
    if label_read_observer is not None:
        label_read_observer(label_path)
    label_bytes = _read_artifact_bytes(label_path, kind="sealed label vault")
    if sha256_bytes(label_bytes) != split_manifest.get("label_vault_sha256"):
        raise ObservableFirewallError("split manifest label-vault hash mismatch")
    label_rows = read_csv_exact_bytes(
        label_bytes,
        source=str(label_path),
        header=LABEL_HEADER,
    )
    labels = _validate_label_rows(label_rows, source=label_path)
    if set(labels) != set(join_keys.values()):
        missing = sorted(set(join_keys.values()) - set(labels))
        extras = sorted(set(labels) - set(join_keys.values()))
        raise ObservableFirewallError(
            f"exact prediction/label ID equality required; missing={missing}, extras={extras}"
        )

    roles = [labels[join_keys[int(row["row_index"])]] for row in prediction_rows]
    predictions = [int(row["proposed_trinary"]) for row in prediction_rows]
    evaluation = evaluate_role_predictions(roles, predictions)
    evaluation.update(
        {
            "prediction_count": len(prediction_rows),
            "unique_prediction_indices": len(prediction_indices),
            "label_count": len(labels),
            "unique_label_ids": len(labels),
            "joined_count": len(roles),
            "prediction_values_sha256": manifest["prediction_values_sha256"],
            "prejoin_receipt_sha256": expected_receipt_sha256,
            "sealed_split_manifest_sha256": expected_split_manifest_sha256,
            "labels_joined_after_freeze_verification": True,
        }
    )
    return evaluation


def build_failure_capability_rows() -> list[dict[str, object]]:
    roles = ["expresser", "expresser", "latent", "latent", "trap", "trap"]
    cases = (
        ("perfect_synthetic_control", [1, 1, 0, 0, -1, -1], "EVALUATOR_OPERABLE"),
        ("injected_false_crown", [1, 1, 0, 0, 1, -1], "DETECTED_FALSE_CROWN"),
        ("injected_hold_overcrown", [1, 1, 1, 0, -1, -1], "DETECTED_HOLD_OVERCROWN"),
        ("always_hold", [0, 0, 0, 0, 0, 0], "INVALID_ALWAYS_HOLD"),
        ("always_crown", [1, 1, 1, 1, 1, 1], "INVALID_ALWAYS_CROWN"),
        ("always_resist", [-1, -1, -1, -1, -1, -1], "INVALID_ALWAYS_RESIST"),
    )
    rows: list[dict[str, object]] = []
    for case, predictions, expected_status in cases:
        result = evaluate_role_predictions(roles, predictions)
        rows.append(
            {
                "case": case,
                "expected_status": expected_status,
                "observed_status": result["evaluation_status"],
                "expected_failure_detected": result["evaluation_status"] == expected_status,
                "false_crown_count": result["false_crown_count"],
                "hold_overcrown_count": result["hold_overcrown_count"],
                "missed_earned_count": result["missed_earned_count"],
                "confusion_count": result["confusion_count"],
                "row_count": result["row_count"],
            }
        )
    return rows


def failure_capability_passed(rows: Iterable[dict[str, object]]) -> bool:
    values = list(rows)
    required = {
        "perfect_synthetic_control",
        "injected_false_crown",
        "injected_hold_overcrown",
        "always_hold",
        "always_crown",
        "always_resist",
    }
    return (
        {str(row.get("case")) for row in values} == required
        and all(row.get("expected_failure_detected") is True for row in values)
        and all(int(row.get("confusion_count", -1)) == int(row.get("row_count", -2)) for row in values)
    )
