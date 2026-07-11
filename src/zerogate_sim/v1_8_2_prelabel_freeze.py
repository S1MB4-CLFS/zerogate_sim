from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import stat
import sys
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Callable, Iterable, Mapping, Sequence

VERSION = "v1.8.2-alpha"
PRELABEL_CONTRACT_ID = "zerogate-v1.8.2-prelabel-firewall-v1"
PRELABEL_STATE = "FROZEN_ALL_MODELS_AND_OPTIONS_PRE_LABEL_JOIN"
SCIENTIFIC_STATUS = "HOLD_DEVELOPMENT_PRELABEL_INFRASTRUCTURE_ONLY"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")

# Exact local dependency surface. The registry and every dependency it may use
# are executed from this byte snapshot; ordinary imported scorer functions are
# never called by the freeze or verifier.
PRELABEL_FILE_ALLOWLIST = (
    "src/zerogate_sim/v1_8_observable_schema.py",
    "src/zerogate_sim/v1_8_lineage_schema.py",
    "src/zerogate_sim/v1_8_lineage_predictor.py",
    "src/zerogate_sim/v1_8_predictor_package.py",
    "src/zerogate_sim/v1_8_2_threshold_contract.py",
    "src/zerogate_sim/v1_8_2_score_registry.py",
    "src/zerogate_sim/v1_8_2_prelabel_freeze.py",
    "contracts/v1_8_1_lineage_predictor.json",
    "contracts/v1_8_1_development_plan_lock.json",
)

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
    (
        "zerogate_sim.v1_8_predictor_package",
        "src/zerogate_sim/v1_8_predictor_package.py",
    ),
    (
        "zerogate_sim.v1_8_2_threshold_contract",
        "src/zerogate_sim/v1_8_2_threshold_contract.py",
    ),
    (
        "zerogate_sim.v1_8_2_score_registry",
        "src/zerogate_sim/v1_8_2_score_registry.py",
    ),
)

PRELABEL_FILES = {
    "scores": Path("v1_8_2_continuous_scores.csv"),
    "prediction_cube": Path("v1_8_2_prediction_cube.csv"),
    "options": Path("v1_8_2_threshold_options.json"),
    "manifest": Path("v1_8_2_prelabel_manifest.json"),
    "receipt": Path("v1_8_2_prelabel_receipt.json"),
}

SCORE_HEADER = ("row_index", "model_id", "score")
PREDICTION_HEADER = (
    "row_index",
    "model_id",
    "option_id",
    "score",
    "proposed_trinary",
)

FORBIDDEN_REGISTRY_KEYS = {
    "row_index",
    "source_id",
    "source_record_id",
    "blind_case_id",
    "candidate_id",
    "generator_id",
    "generator_lineage_id",
    "lineage_id",
    "group_id",
    "fold_id",
    "evaluation_role",
    "truth_role",
    "expected_trinary",
    "label",
    "target",
    "seed",
    "scenario",
    "profile",
}

_CONSTANT_PREDICTIONS = {
    "always_hold": 0,
    "always_crown": 1,
    "always_resist": -1,
}

_RUNTIME_LOCK = threading.RLock()


class PrelabelFirewallError(ValueError):
    """Raised when the pre-label score boundary cannot be verified exactly."""


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
class _RegistryRuntime:
    read_lineage_inputs_bytes: Callable[..., list[dict[str, object]]]
    immutable_lineage_frames: Callable[..., object]
    lineage_schema_sha256: Callable[[], str]
    score_registry_rows: Callable[[object], Sequence[Mapping[str, object]]]
    prediction_cube_rows: Callable[[object], Sequence[Mapping[str, object]]]
    development_plan_document: Callable[[], dict[str, object]]
    verify_v1_8_1_package: Callable[..., object]
    model_ids: tuple[str, ...]
    continuous_model_ids: tuple[str, ...]
    constant_model_ids: tuple[str, ...]
    threshold_options: tuple[object, ...]
    schema_id: str
    registry_version: str


@dataclass(frozen=True, slots=True)
class _PreparedArtifacts:
    scores: bytes
    prediction_cube: bytes
    options: bytes
    manifest: bytes
    receipt: bytes
    manifest_document: dict[str, object]
    receipt_document: dict[str, object]


def canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PrelabelFirewallError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_sha256(value: object) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def _validate_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise PrelabelFirewallError(f"{field} must be a lowercase SHA-256")
    return value


def _strict_json_object(data: bytes, *, source: str) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PrelabelFirewallError(f"{source}: JSON is not UTF-8") from exc
    if not text.endswith("\n") or text != text.strip("\n") + "\n":
        raise PrelabelFirewallError(f"{source}: canonical JSON needs one final newline")

    def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in pairs:
            if key in out:
                raise PrelabelFirewallError(f"{source}: duplicate JSON key {key!r}")
            out[key] = value
        return out

    def no_nonfinite(value: str) -> object:
        raise PrelabelFirewallError(f"{source}: non-finite JSON constant {value!r}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=no_duplicate_keys,
            parse_constant=no_nonfinite,
        )
    except PrelabelFirewallError:
        raise
    except json.JSONDecodeError as exc:
        raise PrelabelFirewallError(f"{source}: malformed JSON: {exc}") from exc
    if not isinstance(value, dict) or canonical_json(value) + "\n" != text:
        raise PrelabelFirewallError(f"{source}: JSON object is not canonical")
    return value


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _assert_no_link_chain(path: Path, *, field: str) -> None:
    """Reject links/junctions in both lexical and resolved ancestor chains."""

    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.exists() and _is_link_or_junction(candidate):
            raise PrelabelFirewallError(f"{field} contains a link or junction")
    resolved = absolute.resolve(strict=True)
    for candidate in (resolved, *resolved.parents):
        if candidate.exists() and _is_link_or_junction(candidate):
            raise PrelabelFirewallError(f"{field} resolves through a link or junction")


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
        raise PrelabelFirewallError(f"unsafe package path {relative_path!r}")
    candidate = root
    for part in pure.parts:
        candidate = candidate / part
        if _is_link_or_junction(candidate):
            raise PrelabelFirewallError(
                f"package path contains a link or junction: {relative_path}"
            )
    if not candidate.is_file():
        raise PrelabelFirewallError(f"missing package file: {relative_path}")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise PrelabelFirewallError(
            f"package path escapes repository root: {relative_path}"
        ) from exc
    return candidate


def _snapshot_package_files() -> tuple[tuple[str, bytes], ...]:
    root = _repo_root()
    if not root.is_dir() or _is_link_or_junction(root):
        raise PrelabelFirewallError(f"repository root is missing or unsafe: {root}")
    snapshots: list[tuple[str, bytes]] = []
    for relative_path in PRELABEL_FILE_ALLOWLIST:
        source = _safe_package_path(root, relative_path)
        data = source.read_bytes()
        if b"\r" in data:
            raise PrelabelFirewallError(
                f"package text must use LF bytes: {relative_path}"
            )
        snapshots.append((relative_path, data))
    return tuple(snapshots)


def _package_records(
    snapshots: Sequence[tuple[str, bytes]],
) -> tuple[PackageFileRecord, ...]:
    return tuple(
        PackageFileRecord(path, sha256_bytes(data), len(data))
        for path, data in snapshots
    )


def _prelabel_contract_sha256(records: Sequence[PackageFileRecord]) -> str:
    return stable_sha256(
        {
            "version": VERSION,
            "contract_id": PRELABEL_CONTRACT_ID,
            "file_allowlist": [record.to_dict() for record in records],
        }
    )


def _load_verified_runtime(
    snapshots: Mapping[str, bytes],
) -> _RegistryRuntime:
    missing = [path for _, path in _RUNTIME_MODULES if path not in snapshots]
    if missing:
        raise PrelabelFirewallError(f"verified runtime snapshot is incomplete: {missing}")
    sentinel = object()
    previous: dict[str, object] = {}
    loaded: dict[str, ModuleType] = {}
    with _RUNTIME_LOCK:
        try:
            for module_name, relative_path in _RUNTIME_MODULES:
                previous[module_name] = sys.modules.get(module_name, sentinel)
                module = ModuleType(module_name)
                module.__file__ = f"<verified-prelabel:{relative_path}>"
                module.__package__ = module_name.rpartition(".")[0]
                module.__loader__ = None
                sys.modules[module_name] = module
                try:
                    source = snapshots[relative_path].decode("utf-8")
                    code = compile(source, module.__file__, "exec", dont_inherit=True)
                    exec(code, module.__dict__)
                except Exception as exc:
                    raise PrelabelFirewallError(
                        f"verified runtime failed to load {relative_path}: {exc}"
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
    package = loaded["zerogate_sim.v1_8_predictor_package"]
    registry = loaded["zerogate_sim.v1_8_2_score_registry"]
    required = {
        "read_lineage_inputs_bytes": getattr(schema, "read_lineage_inputs_bytes", None),
        "immutable_lineage_frames": getattr(schema, "immutable_lineage_frames", None),
        "lineage_schema_sha256": getattr(schema, "lineage_schema_sha256", None),
        "score_registry_rows": getattr(registry, "score_registry_rows", None),
        "prediction_cube_rows": getattr(registry, "prediction_cube_rows", None),
        "development_plan_document": getattr(
            package, "development_plan_document", None
        ),
        "verify_predictor_package": getattr(package, "verify_predictor_package", None),
    }
    missing_api = sorted(name for name, value in required.items() if not callable(value))
    if missing_api:
        raise PrelabelFirewallError(f"verified runtime API is incomplete: {missing_api}")

    def exact_tokens(name: str) -> tuple[str, ...]:
        value = getattr(registry, name, None)
        if type(value) is not tuple or not value:
            raise PrelabelFirewallError(f"registry {name} must be a nonempty tuple")
        tokens = tuple(value)
        if any(type(token) is not str or SAFE_TOKEN_RE.fullmatch(token) is None for token in tokens):
            raise PrelabelFirewallError(f"registry {name} contains an invalid token")
        if len(tokens) != len(set(tokens)):
            raise PrelabelFirewallError(f"registry {name} contains duplicates")
        return tokens

    model_ids = exact_tokens("MODEL_IDS")
    continuous = exact_tokens("CONTINUOUS_MODEL_IDS")
    constants = exact_tokens("CONSTANT_MODEL_IDS")
    if model_ids != continuous + constants or set(continuous) & set(constants):
        raise PrelabelFirewallError("registry model partitions are inconsistent")
    if constants != tuple(_CONSTANT_PREDICTIONS):
        raise PrelabelFirewallError("registry constant controls are not exact")
    threshold_options = getattr(registry, "THRESHOLD_OPTIONS", None)
    if type(threshold_options) is not tuple or len(threshold_options) != 3:
        raise PrelabelFirewallError("registry must expose exactly three threshold options")
    registry_version = str(getattr(registry, "VERSION", ""))
    if registry_version != VERSION:
        raise PrelabelFirewallError("registry version does not match prelabel version")

    return _RegistryRuntime(
        read_lineage_inputs_bytes=required["read_lineage_inputs_bytes"],  # type: ignore[arg-type]
        immutable_lineage_frames=required["immutable_lineage_frames"],  # type: ignore[arg-type]
        lineage_schema_sha256=required["lineage_schema_sha256"],  # type: ignore[arg-type]
        score_registry_rows=required["score_registry_rows"],  # type: ignore[arg-type]
        prediction_cube_rows=required["prediction_cube_rows"],  # type: ignore[arg-type]
        development_plan_document=required["development_plan_document"],  # type: ignore[arg-type]
        verify_v1_8_1_package=required["verify_predictor_package"],  # type: ignore[arg-type]
        model_ids=model_ids,
        continuous_model_ids=continuous,
        constant_model_ids=constants,
        threshold_options=tuple(threshold_options),
        schema_id=str(getattr(schema, "SCHEMA_ID", "")),
        registry_version=registry_version,
    )


def _option_rows(runtime: _RegistryRuntime) -> tuple[dict[str, object], ...]:
    out: list[dict[str, object]] = []
    for option in runtime.threshold_options:
        try:
            option_id = option.option_id
            resist_max = option.resist_max
            crown_min = option.crown_min
        except AttributeError as exc:
            raise PrelabelFirewallError("threshold option API is malformed") from exc
        if type(option_id) is not str or SAFE_TOKEN_RE.fullmatch(option_id) is None:
            raise PrelabelFirewallError("threshold option_id is invalid")
        resist = _unit_float(resist_max, field=f"{option_id}.resist_max")
        crown = _unit_float(crown_min, field=f"{option_id}.crown_min")
        if not resist < crown:
            raise PrelabelFirewallError("threshold option must satisfy resist_max < crown_min")
        out.append(
            {"option_id": option_id, "resist_max": resist, "crown_min": crown}
        )
    if len({row["option_id"] for row in out}) != 3:
        raise PrelabelFirewallError("threshold option IDs must be unique")

    plan = runtime.development_plan_document()
    plan_options = plan.get("threshold_options")
    if plan_options != out:
        raise PrelabelFirewallError("registry options differ from v1.8.1 method lock")
    if (
        plan.get("selected_threshold_option") is not None
        or plan.get("scientific_thresholds_selected") is not False
    ):
        raise PrelabelFirewallError("v1.8.1 method lock selected a threshold prematurely")
    return tuple(out)


def _unit_float(value: object, *, field: str) -> float:
    if type(value) not in {int, float}:
        raise PrelabelFirewallError(f"{field} must be an actual int or float")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise PrelabelFirewallError(f"{field} must satisfy 0 <= value <= 1")
    return 0.0 if number == 0.0 else number


def _strict_trinary(value: object, *, field: str) -> int:
    if type(value) is not int or value not in {-1, 0, 1}:
        raise PrelabelFirewallError(f"{field} must be exact -1, 0, or 1")
    return value


def _normalize_score_rows(
    rows: object,
    runtime: _RegistryRuntime,
) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise PrelabelFirewallError("score registry rows must be an ordered sequence")
    normalized: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {"model_id", "score"}:
            raise PrelabelFirewallError(f"score registry row {index} has non-exact keys")
        if set(row) & FORBIDDEN_REGISTRY_KEYS:
            raise PrelabelFirewallError(f"score registry row {index} leaks metadata")
        model_id = row["model_id"]
        if type(model_id) is not str:
            raise PrelabelFirewallError(f"score registry row {index} model_id is invalid")
        normalized.append(
            {
                "model_id": model_id,
                "score": _unit_float(row["score"], field=f"score[{model_id}]"),
            }
        )
    if tuple(row["model_id"] for row in normalized) != runtime.continuous_model_ids:
        raise PrelabelFirewallError("score registry rows do not match locked model order")
    return tuple(normalized)


def _normalize_prediction_rows(
    rows: object,
    runtime: _RegistryRuntime,
    scores: Sequence[Mapping[str, object]],
    options: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise PrelabelFirewallError("prediction cube rows must be an ordered sequence")
    score_by_model = {str(row["model_id"]): float(row["score"]) for row in scores}
    option_by_id = {str(row["option_id"]): row for row in options}
    expected_keys = {"model_id", "option_id", "score", "proposed_trinary"}
    normalized: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != expected_keys:
            raise PrelabelFirewallError(f"prediction row {index} has non-exact keys")
        if set(row) & FORBIDDEN_REGISTRY_KEYS:
            raise PrelabelFirewallError(f"prediction row {index} leaks metadata")
        model_id = row["model_id"]
        option_id = row["option_id"]
        if type(model_id) is not str or type(option_id) is not str:
            raise PrelabelFirewallError(f"prediction row {index} IDs are invalid")
        proposed = _strict_trinary(
            row["proposed_trinary"], field=f"prediction[{index}]"
        )
        if model_id in runtime.continuous_model_ids:
            if option_id not in option_by_id:
                raise PrelabelFirewallError("continuous prediction uses unknown option")
            score = _unit_float(row["score"], field=f"prediction score[{index}]")
            if score != score_by_model[model_id]:
                raise PrelabelFirewallError("prediction score differs from registry score")
            option = option_by_id[option_id]
            expected = (
                -1
                if score <= float(option["resist_max"])
                else 1
                if score >= float(option["crown_min"])
                else 0
            )
            if proposed != expected:
                raise PrelabelFirewallError("prediction violates locked threshold semantics")
            normalized_score: float | None = score
        elif model_id in runtime.constant_model_ids:
            if option_id != "constant" or row["score"] is not None:
                raise PrelabelFirewallError("constant control row is malformed")
            if proposed != _CONSTANT_PREDICTIONS[model_id]:
                raise PrelabelFirewallError("constant control prediction is wrong")
            normalized_score = None
        else:
            raise PrelabelFirewallError("prediction uses unknown model")
        normalized.append(
            {
                "model_id": model_id,
                "option_id": option_id,
                "score": normalized_score,
                "proposed_trinary": proposed,
            }
        )

    expected_order = [
        (model_id, str(option["option_id"]))
        for model_id in runtime.continuous_model_ids
        for option in options
    ] + [(model_id, "constant") for model_id in runtime.constant_model_ids]
    actual_order = [(str(row["model_id"]), str(row["option_id"])) for row in normalized]
    if actual_order != expected_order:
        raise PrelabelFirewallError("prediction cube does not match locked cardinality/order")
    return tuple(normalized)


def _score_text(value: object) -> str:
    number = _unit_float(value, field="serialized score")
    return format(number, ".17g")


def _score_csv_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SCORE_HEADER)
    for row in rows:
        writer.writerow((row["row_index"], row["model_id"], _score_text(row["score"])))
    return buffer.getvalue().encode("utf-8")


def _prediction_csv_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(PREDICTION_HEADER)
    for row in rows:
        score = "" if row["score"] is None else _score_text(row["score"])
        writer.writerow(
            (
                row["row_index"],
                row["model_id"],
                row["option_id"],
                score,
                row["proposed_trinary"],
            )
        )
    return buffer.getvalue().encode("utf-8")


def _prepare_artifacts(
    *,
    observable_source_bytes: bytes,
    expected_split_receipt_sha256: str,
    expected_extraction_source_manifest_sha256: str,
    expected_development_fingerprint_sha256: str,
    expected_observable_source_sha256: str,
    expected_v1_8_1_package_contract_sha256: str,
    snapshots: tuple[tuple[str, bytes], ...],
) -> _PreparedArtifacts:
    if type(observable_source_bytes) is not bytes:
        raise PrelabelFirewallError("observable_source_bytes must be exact bytes")
    split_receipt = _validate_sha256(
        expected_split_receipt_sha256,
        field="expected_split_receipt_sha256",
    )
    extraction_source_manifest = _validate_sha256(
        expected_extraction_source_manifest_sha256,
        field="expected_extraction_source_manifest_sha256",
    )
    development_fingerprint = _validate_sha256(
        expected_development_fingerprint_sha256,
        field="expected_development_fingerprint_sha256",
    )
    expected_source = _validate_sha256(
        expected_observable_source_sha256,
        field="expected_observable_source_sha256",
    )
    expected_v181 = _validate_sha256(
        expected_v1_8_1_package_contract_sha256,
        field="expected_v1_8_1_package_contract_sha256",
    )
    if sha256_bytes(observable_source_bytes) != expected_source:
        raise PrelabelFirewallError("observable source SHA-256 mismatch")

    snapshot_map = dict(snapshots)
    if len(snapshot_map) != len(snapshots):
        raise PrelabelFirewallError("prelabel package allowlist contains duplicates")
    runtime = _load_verified_runtime(snapshot_map)
    try:
        verified_v181 = runtime.verify_v1_8_1_package(
            _repo_root(),
            expected_contract_sha256=expected_v181,
        )
    except Exception as exc:
        raise PrelabelFirewallError(f"v1.8.1 package verification failed: {exc}") from exc
    if getattr(verified_v181, "contract_sha256", None) != expected_v181:
        raise PrelabelFirewallError("v1.8.1 package verifier returned the wrong contract")

    options = _option_rows(runtime)
    try:
        observable_rows = runtime.read_lineage_inputs_bytes(
            observable_source_bytes,
            source="caller-supplied observable source bytes",
        )
    except Exception as exc:
        raise PrelabelFirewallError(f"observable source is invalid: {exc}") from exc
    if not observable_rows:
        raise PrelabelFirewallError("observable source contains no rows")

    score_rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []
    by_observable: dict[str, tuple[object, object]] = {}
    normalized_by_index: dict[int, tuple[object, object]] = {}
    for row in observable_rows:
        row_index = row.get("row_index")
        if type(row_index) is not int or row_index < 0:
            raise PrelabelFirewallError("observable row index is invalid")
        try:
            frames = runtime.immutable_lineage_frames(
                row["observable_frames"], source=f"prelabel row {row_index}"
            )
            scores = _normalize_score_rows(runtime.score_registry_rows(frames), runtime)
            predictions = _normalize_prediction_rows(
                runtime.prediction_cube_rows(frames), runtime, scores, options
            )
        except PrelabelFirewallError:
            raise
        except Exception as exc:
            raise PrelabelFirewallError(f"registry failed for row {row_index}: {exc}") from exc
        observable_hash = stable_sha256(row["observable_frames"])
        semantic = (scores, predictions)
        prior = by_observable.get(observable_hash)
        if prior is not None and prior != semantic:
            raise PrelabelFirewallError(
                "identical observable paths produced different registry outputs"
            )
        by_observable[observable_hash] = semantic
        normalized_by_index[row_index] = semantic
        score_rows.extend(
            {"row_index": row_index, **dict(score)} for score in scores
        )
        prediction_rows.extend(
            {"row_index": row_index, **dict(prediction)} for prediction in predictions
        )

    for row in reversed(observable_rows):
        row_index = int(row["row_index"])
        frames = runtime.immutable_lineage_frames(
            row["observable_frames"], source="reverse prelabel row"
        )
        scores = _normalize_score_rows(runtime.score_registry_rows(frames), runtime)
        predictions = _normalize_prediction_rows(
            runtime.prediction_cube_rows(frames), runtime, scores, options
        )
        if (scores, predictions) != normalized_by_index[row_index]:
            raise PrelabelFirewallError("registry failed reverse-order consistency")

    scores_bytes = _score_csv_bytes(score_rows)
    predictions_bytes = _prediction_csv_bytes(prediction_rows)
    options_document = {
        "version": VERSION,
        "option_state": "FROZEN_CANDIDATE_OPTIONS_PRE_LABEL_JOIN",
        "option_count": len(options),
        "threshold_options": list(options),
        "selected_option_id": None,
        "source": "v1.8.1 byte-bound development method lock",
    }
    options_bytes = (canonical_json(options_document) + "\n").encode("utf-8")
    records = _package_records(snapshots)
    prelabel_contract = _prelabel_contract_sha256(records)
    score_values = [
        {"model_id": row["model_id"], "score": row["score"]} for row in score_rows
    ]
    prediction_values = [
        {
            "model_id": row["model_id"],
            "option_id": row["option_id"],
            "score": row["score"],
            "proposed_trinary": row["proposed_trinary"],
        }
        for row in prediction_rows
    ]
    manifest = {
        "version": VERSION,
        "freeze_state": PRELABEL_STATE,
        "scientific_status": SCIENTIFIC_STATUS,
        "caller_retained_split_receipt_sha256": split_receipt,
        "caller_retained_extraction_source_manifest_sha256": (
            extraction_source_manifest
        ),
        "caller_retained_development_fingerprint_sha256": development_fingerprint,
        "observable_source_sha256": expected_source,
        "observable_source_transport": "caller_supplied_bytes_only_no_input_path",
        "observable_row_count": len(observable_rows),
        "lineage_schema_id": runtime.schema_id,
        "lineage_schema_sha256": runtime.lineage_schema_sha256(),
        "v1_8_1_package_contract_sha256": expected_v181,
        "prelabel_contract_id": PRELABEL_CONTRACT_ID,
        "prelabel_contract_sha256": prelabel_contract,
        "package_files": [record.to_dict() for record in records],
        "model_ids": list(runtime.model_ids),
        "continuous_model_ids": list(runtime.continuous_model_ids),
        "constant_model_ids": list(runtime.constant_model_ids),
        "continuous_scores_per_row": len(runtime.continuous_model_ids),
        "predictions_per_row": (
            len(runtime.continuous_model_ids) * len(options)
            + len(runtime.constant_model_ids)
        ),
        "continuous_score_row_count": len(score_rows),
        "prediction_cube_row_count": len(prediction_rows),
        "scores_sha256": sha256_bytes(scores_bytes),
        "score_values_sha256": stable_sha256(score_values),
        "prediction_cube_sha256": sha256_bytes(predictions_bytes),
        "prediction_values_sha256": stable_sha256(prediction_values),
        "threshold_options_sha256": sha256_bytes(options_bytes),
        "threshold_option_values_sha256": stable_sha256(list(options)),
        "registry_callback_contains_case_identifiers": False,
        "registry_callback_contains_labels_or_groups": False,
        "sealed_artifact_path_parameters_accepted": False,
        "holdout_path_parameters_accepted": False,
        "semantic_label_or_group_reads": 0,
        "runtime_loaded_from_verified_source_snapshot": True,
        "reverse_order_repeat_consistency_passed": True,
        "decision_rule_selected": False,
        "external_timestamp_proof": False,
    }
    manifest_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    receipt = {
        "version": VERSION,
        "receipt_state": "CALLER_RETAIN_PRE_LABEL_JOIN_RECEIPT",
        "caller_retained_split_receipt_sha256": split_receipt,
        "caller_retained_extraction_source_manifest_sha256": (
            extraction_source_manifest
        ),
        "caller_retained_development_fingerprint_sha256": development_fingerprint,
        "observable_source_sha256": expected_source,
        "v1_8_1_package_contract_sha256": expected_v181,
        "prelabel_contract_sha256": prelabel_contract,
        "scores_sha256": manifest["scores_sha256"],
        "prediction_cube_sha256": manifest["prediction_cube_sha256"],
        "threshold_options_sha256": manifest["threshold_options_sha256"],
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "semantic_label_or_group_reads": 0,
        "external_timestamp_proof": False,
    }
    receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
    return _PreparedArtifacts(
        scores=scores_bytes,
        prediction_cube=predictions_bytes,
        options=options_bytes,
        manifest=manifest_bytes,
        receipt=receipt_bytes,
        manifest_document=manifest,
        receipt_document=receipt,
    )


def _file_identity(stat_result: os.stat_result) -> tuple[int, int]:
    return (int(stat_result.st_dev), int(stat_result.st_ino))


def _assert_owned_directory(path: Path, identity: tuple[int, int]) -> None:
    try:
        current = os.lstat(path)
    except FileNotFoundError as exc:
        raise PrelabelFirewallError("prelabel output directory disappeared") from exc
    if (
        not stat.S_ISDIR(current.st_mode)
        or _is_link_or_junction(path)
        or _file_identity(current) != identity
    ):
        raise PrelabelFirewallError("prelabel output directory changed during operation")


def _assert_owned_file(path: Path, identity: tuple[int, int]) -> None:
    try:
        current = os.lstat(path)
    except FileNotFoundError as exc:
        raise PrelabelFirewallError(f"artifact disappeared while writing: {path.name}") from exc
    if (
        not stat.S_ISREG(current.st_mode)
        or _is_link_or_junction(path)
        or _file_identity(current) != identity
    ):
        raise PrelabelFirewallError(f"artifact ownership changed: {path.name}")


def _unlink_owned(path: Path, identity: tuple[int, int]) -> None:
    try:
        current = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return
    if _is_link_or_junction(path) or _file_identity(current) != identity:
        return
    try:
        path.unlink()
    except OSError:
        pass


def _write_owned_file(path: Path, data: bytes) -> tuple[int, int]:
    identity: tuple[int, int] | None = None
    try:
        with path.open("xb") as handle:
            identity = _file_identity(os.fstat(handle.fileno()))
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _assert_owned_file(path, identity)
        if path.read_bytes() != data:
            raise PrelabelFirewallError(f"artifact changed while writing: {path.name}")
        _assert_owned_file(path, identity)
        return identity
    except FileExistsError as exc:
        raise PrelabelFirewallError(
            f"rival writer already owns artifact: {path.name}"
        ) from exc
    except Exception:
        if identity is not None:
            _unlink_owned(path, identity)
        raise


def _safe_output_parent(output: Path) -> None:
    parent = output.absolute().parent
    if not parent.is_dir() or _is_link_or_junction(parent):
        raise PrelabelFirewallError(f"output parent is missing or unsafe: {parent}")
    _assert_no_link_chain(parent, field="output parent chain")


def _assert_code_unchanged(expected: tuple[tuple[str, bytes], ...]) -> None:
    if _snapshot_package_files() != expected:
        raise PrelabelFirewallError("prelabel package changed during operation")


def freeze_prelabel(
    out: str | Path,
    *,
    observable_source_bytes: bytes,
    expected_split_receipt_sha256: str,
    expected_extraction_source_manifest_sha256: str,
    expected_development_fingerprint_sha256: str,
    expected_observable_source_sha256: str,
    expected_v1_8_1_package_contract_sha256: str,
) -> dict[str, Path]:
    """Freeze every locked score and option without accepting any data path.

    The split receipt is an opaque caller-retained hash. This function neither
    accepts nor opens its artifact, join keys, labels, groups, or holdout paths.
    """

    output = Path(out).absolute()
    _safe_output_parent(output)
    if output.exists():
        raise PrelabelFirewallError(f"refusing existing prelabel output: {output}")
    snapshots = _snapshot_package_files()
    artifacts = _prepare_artifacts(
        observable_source_bytes=observable_source_bytes,
        expected_split_receipt_sha256=expected_split_receipt_sha256,
        expected_extraction_source_manifest_sha256=(
            expected_extraction_source_manifest_sha256
        ),
        expected_development_fingerprint_sha256=(
            expected_development_fingerprint_sha256
        ),
        expected_observable_source_sha256=expected_observable_source_sha256,
        expected_v1_8_1_package_contract_sha256=(
            expected_v1_8_1_package_contract_sha256
        ),
        snapshots=snapshots,
    )
    _assert_code_unchanged(snapshots)

    paths = {key: output / relative for key, relative in PRELABEL_FILES.items()}
    output.mkdir(exist_ok=False)
    output_identity = _file_identity(output.stat(follow_symlinks=False))
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for key, data in (
            ("scores", artifacts.scores),
            ("prediction_cube", artifacts.prediction_cube),
            ("options", artifacts.options),
            ("manifest", artifacts.manifest),
            ("receipt", artifacts.receipt),
        ):
            _assert_owned_directory(output, output_identity)
            identity = _write_owned_file(paths[key], data)
            created.append((paths[key], identity))
        _assert_owned_directory(output, output_identity)
        if {path.name for path in output.iterdir()} != {
            relative.name for relative in PRELABEL_FILES.values()
        }:
            raise PrelabelFirewallError("rival writer changed the prelabel artifact set")
        for path, identity in created:
            _assert_owned_file(path, identity)
        _assert_code_unchanged(snapshots)
    except Exception:
        for path, identity in reversed(created):
            _unlink_owned(path, identity)
        try:
            if (
                output.is_dir()
                and not _is_link_or_junction(output)
                and _file_identity(output.stat(follow_symlinks=False)) == output_identity
            ):
                output.rmdir()
        except OSError:
            pass
        raise
    return paths


def _read_exact_artifacts(output: Path) -> dict[str, bytes]:
    if not output.is_dir() or _is_link_or_junction(output):
        raise PrelabelFirewallError(f"missing or unsafe prelabel output: {output}")
    _assert_no_link_chain(output, field="prelabel output chain")
    expected_names = {relative.name for relative in PRELABEL_FILES.values()}
    actual_names = {path.name for path in output.iterdir()}
    if actual_names != expected_names:
        raise PrelabelFirewallError(
            f"prelabel output must contain exact artifacts; extras={sorted(actual_names - expected_names)}, "
            f"missing={sorted(expected_names - actual_names)}"
        )
    data: dict[str, bytes] = {}
    for key, relative in PRELABEL_FILES.items():
        path = output / relative
        if not path.is_file() or _is_link_or_junction(path):
            raise PrelabelFirewallError(f"missing or unsafe prelabel artifact: {path}")
        data[key] = path.read_bytes()
    return data


def verify_prelabel(
    out: str | Path,
    *,
    observable_source_bytes: bytes,
    expected_split_receipt_sha256: str,
    expected_extraction_source_manifest_sha256: str,
    expected_development_fingerprint_sha256: str,
    expected_observable_source_sha256: str,
    expected_v1_8_1_package_contract_sha256: str,
    expected_prelabel_receipt_sha256: str,
) -> dict[str, object]:
    """Recompute the entire pre-label freeze before any semantic label read."""

    expected_receipt = _validate_sha256(
        expected_prelabel_receipt_sha256,
        field="expected_prelabel_receipt_sha256",
    )
    output = Path(out).absolute()
    stored = _read_exact_artifacts(output)
    if sha256_bytes(stored["receipt"]) != expected_receipt:
        raise PrelabelFirewallError("caller-retained prelabel receipt SHA-256 mismatch")
    # Parse the retained authority artifacts before recomputation so duplicate
    # keys and noncanonical representations fail explicitly.
    _strict_json_object(stored["receipt"], source="prelabel receipt")
    _strict_json_object(stored["manifest"], source="prelabel manifest")
    _strict_json_object(stored["options"], source="threshold options")

    snapshots = _snapshot_package_files()
    expected = _prepare_artifacts(
        observable_source_bytes=observable_source_bytes,
        expected_split_receipt_sha256=expected_split_receipt_sha256,
        expected_extraction_source_manifest_sha256=(
            expected_extraction_source_manifest_sha256
        ),
        expected_development_fingerprint_sha256=(
            expected_development_fingerprint_sha256
        ),
        expected_observable_source_sha256=expected_observable_source_sha256,
        expected_v1_8_1_package_contract_sha256=(
            expected_v1_8_1_package_contract_sha256
        ),
        snapshots=snapshots,
    )
    expected_bytes = {
        "scores": expected.scores,
        "prediction_cube": expected.prediction_cube,
        "options": expected.options,
        "manifest": expected.manifest,
        "receipt": expected.receipt,
    }
    for key in PRELABEL_FILES:
        if stored[key] != expected_bytes[key]:
            raise PrelabelFirewallError(f"prelabel {key} bytes do not match recomputation")
    _assert_code_unchanged(snapshots)
    return {
        "verified": True,
        "receipt_sha256": expected_receipt,
        "manifest": expected.manifest_document,
        "receipt": expected.receipt_document,
        "semantic_label_or_group_reads": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze the v1.8.2 observable-only score and prediction cube. "
            "Canonical observable JSONL is read only from standard input; no "
            "input, sealed-vault, label, group, or holdout path is accepted."
        )
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--split-receipt-sha256", required=True)
    parser.add_argument("--extraction-source-manifest-sha256", required=True)
    parser.add_argument("--development-fingerprint-sha256", required=True)
    parser.add_argument("--observable-source-sha256", required=True)
    parser.add_argument("--v1-8-1-package-contract-sha256", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    observable_source_bytes = sys.stdin.buffer.read()
    paths = freeze_prelabel(
        args.out,
        observable_source_bytes=observable_source_bytes,
        expected_split_receipt_sha256=args.split_receipt_sha256,
        expected_extraction_source_manifest_sha256=(
            args.extraction_source_manifest_sha256
        ),
        expected_development_fingerprint_sha256=(
            args.development_fingerprint_sha256
        ),
        expected_observable_source_sha256=args.observable_source_sha256,
        expected_v1_8_1_package_contract_sha256=(
            args.v1_8_1_package_contract_sha256
        ),
    )
    print(f"prelabel receipt sha256: {sha256_bytes(paths['receipt'].read_bytes())}")
    print(f"prelabel output: {args.out}")
    return 0


__all__ = [
    "PRELABEL_FILE_ALLOWLIST",
    "PRELABEL_FILES",
    "PrelabelFirewallError",
    "build_parser",
    "freeze_prelabel",
    "main",
    "verify_prelabel",
]


if __name__ == "__main__":
    raise SystemExit(main())
