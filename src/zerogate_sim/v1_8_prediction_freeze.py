from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping

from zerogate_sim.v1_8_observable_schema import (
    CURRENT_VERSION,
    SCHEMA_ID,
    ObservableFirewallError,
    canonical_json,
    observable_schema_sha256,
    read_observable_inputs_bytes,
    sha256_bytes,
    sha256_file,
    stable_sha256,
    validate_sha256,
    write_canonical_json,
    write_csv_exact,
)

PREDICTION_HEADER = ("row_index", "prediction_score", "proposed_trinary")
PREDICTOR_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")

FREEZE_FILES = {
    "predictions": Path("v1_8_frozen_predictions.csv"),
    "manifest": Path("v1_8_prediction_freeze_manifest.json"),
    "receipt": Path("v1_8_prediction_freeze_receipt.json"),
}


@dataclass(frozen=True)
class PredictionProposal:
    prediction_score: float
    proposed_trinary: int


ObservablePredictor = Callable[[Mapping[str, float]], PredictionProposal]


def _validate_predictor_id(value: object) -> str:
    if not isinstance(value, str) or PREDICTOR_ID_RE.fullmatch(value) is None:
        raise ObservableFirewallError(f"invalid predictor_id {value!r}")
    return value


def _validate_proposal(value: object, *, row_index: int) -> PredictionProposal:
    if type(value) is not PredictionProposal:
        raise ObservableFirewallError(
            f"prediction row {row_index}: predictor must return PredictionProposal exactly"
        )
    score = value.prediction_score
    if isinstance(score, bool):
        raise ObservableFirewallError(f"prediction row {row_index}: boolean score is forbidden")
    try:
        number = float(score)
    except (TypeError, ValueError) as exc:
        raise ObservableFirewallError(
            f"prediction row {row_index}: malformed prediction_score {score!r}"
        ) from exc
    if not math.isfinite(number):
        raise ObservableFirewallError(
            f"prediction row {row_index}: prediction_score must be finite"
        )
    if number == 0.0:
        number = 0.0
    proposed = value.proposed_trinary
    if isinstance(proposed, bool) or type(proposed) is not int or proposed not in {-1, 0, 1}:
        raise ObservableFirewallError(
            f"prediction row {row_index}: proposed_trinary must be exact -1, 0, or 1"
        )
    return PredictionProposal(number, proposed)


def predict_observable_rows(
    observable_input_path: str | Path,
    predictor: ObservablePredictor,
) -> list[dict[str, object]]:
    if not callable(predictor):
        raise ObservableFirewallError("predictor must be callable")
    source = Path(observable_input_path)
    if not source.is_file():
        raise ObservableFirewallError(f"missing observable input: {source}")
    observable_rows = read_observable_inputs_bytes(source.read_bytes(), source=str(source))
    return _predict_snapshot_rows(observable_rows, predictor)


def _predict_snapshot_rows(
    observable_rows: list[dict[str, object]],
    predictor: ObservablePredictor,
) -> list[dict[str, object]]:
    if not callable(predictor):
        raise ObservableFirewallError("predictor must be callable")
    predictions: list[dict[str, object]] = []
    by_observable: dict[str, PredictionProposal] = {}
    for row in observable_rows:
        row_index = int(row["row_index"])
        observable_copy = dict(row["observables"])
        observable_hash = stable_sha256(observable_copy)
        proposal = _validate_proposal(
            predictor(MappingProxyType(observable_copy)),
            row_index=row_index,
        )
        previous = by_observable.get(observable_hash)
        if previous is not None and previous != proposal:
            raise ObservableFirewallError(
                "identical observable vectors produced inconsistent predictions"
            )
        by_observable[observable_hash] = proposal
        predictions.append(
            {
                "row_index": row_index,
                "prediction_score": proposal.prediction_score,
                "proposed_trinary": proposal.proposed_trinary,
            }
        )

    # A second pass in reverse order rejects ordinary position/state/randomness
    # leakage. This is an executable consistency check, not proof against a
    # malicious callback or a substitute for process isolation.
    for row in reversed(observable_rows):
        row_index = int(row["row_index"])
        observable_copy = dict(row["observables"])
        observable_hash = stable_sha256(observable_copy)
        repeated = _validate_proposal(
            predictor(MappingProxyType(observable_copy)),
            row_index=row_index,
        )
        if repeated != by_observable[observable_hash]:
            raise ObservableFirewallError(
                "predictor failed reverse-order repeat consistency"
            )
    return predictions


def prediction_values_sha256(rows: list[dict[str, object]]) -> str:
    values = [
        {
            "prediction_score": float(row["prediction_score"]),
            "proposed_trinary": int(row["proposed_trinary"]),
        }
        for row in rows
    ]
    return stable_sha256(values)


def _score_text(value: object) -> str:
    number = float(value)
    if number == 0.0:
        number = 0.0
    return format(number, ".17g")


def freeze_predictions(
    out: str | Path,
    *,
    observable_input_path: str | Path,
    predictor: ObservablePredictor,
    predictor_id: str,
    predictor_contract_sha256: str,
    synthetic_only: bool = True,
) -> dict[str, Path]:
    """Freeze predictions without accepting, importing, or reading any labels.

    The predictor callback receives an immutable mapping containing only the
    exact v1.8 observable allowlist. Row indices and blind identifiers remain
    outside the callback.
    """

    output_dir = Path(out)
    paths = {key: output_dir / relative for key, relative in FREEZE_FILES.items()}
    existing = [str(path) for path in paths.values() if path.exists()]
    if existing:
        raise ObservableFirewallError(f"refusing to overwrite frozen artifacts: {existing}")
    if type(synthetic_only) is not bool:
        raise ObservableFirewallError("synthetic_only must be an exact boolean")
    predictor_name = _validate_predictor_id(predictor_id)
    predictor_hash = validate_sha256(
        predictor_contract_sha256,
        field="predictor_contract_sha256",
        source="prediction freeze",
    )
    observable_path = Path(observable_input_path)
    if not observable_path.is_file():
        raise ObservableFirewallError(f"missing observable input: {observable_path}")
    observable_bytes = observable_path.read_bytes()
    observable_hash = sha256_bytes(observable_bytes)
    observable_rows = read_observable_inputs_bytes(
        observable_bytes,
        source=str(observable_path),
    )
    prediction_rows = _predict_snapshot_rows(observable_rows, predictor)
    if not observable_path.is_file() or observable_path.read_bytes() != observable_bytes:
        raise ObservableFirewallError("observable input changed during prediction freeze")

    try:
        write_csv_exact(
            paths["predictions"],
            header=PREDICTION_HEADER,
            rows=(
                (
                    row["row_index"],
                    _score_text(row["prediction_score"]),
                    row["proposed_trinary"],
                )
                for row in prediction_rows
            ),
        )
        prediction_hash = sha256_file(paths["predictions"])
        manifest = {
            "version": CURRENT_VERSION,
            "freeze_state": "FROZEN_PRE_LABEL_JOIN",
            "schema_id": SCHEMA_ID,
            "schema_sha256": observable_schema_sha256(),
            "observable_input_sha256": observable_hash,
            "observable_values_sha256": stable_sha256(
                [dict(row["observables"]) for row in observable_rows]
            ),
            "observable_row_index_sha256": stable_sha256(
                [int(row["row_index"]) for row in prediction_rows]
            ),
            "predictor_id": predictor_name,
            "declared_predictor_contract_sha256": predictor_hash,
            "predictor_contract_code_binding_verified": False,
            "prediction_count": len(prediction_rows),
            "prediction_file_sha256": prediction_hash,
            "prediction_values_sha256": prediction_values_sha256(prediction_rows),
            "identifier_fields_in_callback_arguments": False,
            "label_fields_in_callback_arguments": False,
            "reverse_order_repeat_consistency_passed": True,
            "freeze_module_accepts_label_paths": False,
            "receipt_required_for_join": True,
            "synthetic_only": synthetic_only,
            "scientific_thresholds_selected": False,
            "scientific_status": "HOLD_FIREWALL_INFRASTRUCTURE_ONLY",
        }
        write_canonical_json(paths["manifest"], manifest)
        receipt = {
            "version": CURRENT_VERSION,
            "receipt_state": "PRE_LABEL_JOIN_RECEIPT",
            "observable_input_sha256": observable_hash,
            "prediction_file_sha256": prediction_hash,
            "manifest_sha256": sha256_file(paths["manifest"]),
            "prediction_values_sha256": manifest["prediction_values_sha256"],
            "external_timestamp_proof": False,
            "scientific_thresholds_selected": False,
        }
        write_canonical_json(paths["receipt"], receipt)
    except Exception:
        for path in paths.values():
            if path.is_file():
                path.unlink()
        raise

    # Parse what was written through the canonical serializer before returning.
    canonical_json(manifest)
    canonical_json(receipt)
    return paths
