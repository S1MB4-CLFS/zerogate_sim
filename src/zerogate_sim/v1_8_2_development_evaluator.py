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
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from zerogate_sim.v1_8_2_cluster_bootstrap import (
    BOOTSTRAP_CONFIDENCE,
    BOOTSTRAP_LOWER_INDEX,
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    BOOTSTRAP_UPPER_INDEX,
    cluster_draw_matrix,
    cluster_percentile_interval,
    paired_cluster_difference_interval,
)
from zerogate_sim.v1_8_2_metrics import (
    AggregateMetrics,
    DuplicateAuditResult,
    MetricResult,
    REQUIRED_ROLES,
    VALID_METRICS,
    aggregate_lineage_metrics,
    audit_observable_duplicates,
    balanced_prediction_guard,
    calculate_metrics,
    constant_prediction_guard,
    failure_capability_passed,
    failure_capability_rows,
    false_crown_guard,
    primary_score_guard,
    primary_strictly_better,
)
from zerogate_sim.v1_8_2_nested_selection import (
    INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR,
    VALID_NESTED_SELECTION,
    FrozenThresholdEvaluation,
    NestedSelectionResult,
    PredictionRecord,
    ScoredCase,
    evaluate_frozen_thresholds,
    nested_logo_select,
)
from zerogate_sim.v1_8_2_threshold_contract import (
    THRESHOLD_OPTIONS,
    EvaluationMathError,
    classify_score,
)


VERSION = "v1.8.2-alpha"
EVALUATOR_ID = "zerogate-v1.8.2-development-evaluator-v1"
PRELABEL_CONTRACT_ID = "zerogate-v1.8.2-prelabel-firewall-v1"
TOTAL_CASES = 144
CASES_PER_ROLE_PER_LINEAGE = 12
SAMPLE_COUNT = 1001
TRACE_SCALE = 1_000_000_000
GENERATOR_CONTRACT_ID = "zerogate-v1.8.2-development-generators-v1"
FRAME_RANGES = {
    "early": (100, 300),
    "witness": (450, 650),
    "late": (800, 1000),
}
SOURCE_BINDING_FILES = (
    "src/zerogate_sim/v1_8_2_numeric_contract.py",
    "src/zerogate_sim/v1_8_2_development_split.py",
    "src/zerogate_sim/v1_8_2_raw_generators.py",
    "src/zerogate_sim/v1_8_2_observable_extractor.py",
    "contracts/v1_8_2_development_generator.json",
)
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
EVALUATOR_FILE_ALLOWLIST = (
    "src/zerogate_sim/v1_8_observable_schema.py",
    "src/zerogate_sim/v1_8_lineage_schema.py",
    "src/zerogate_sim/v1_8_2_threshold_contract.py",
    "src/zerogate_sim/v1_8_2_metrics.py",
    "src/zerogate_sim/v1_8_2_nested_selection.py",
    "src/zerogate_sim/v1_8_2_cluster_bootstrap.py",
    "src/zerogate_sim/v1_8_2_development_evaluator.py",
    "contracts/v1_8_1_development_plan_lock.json",
)

PRIMARY_MODEL_ID = "primary_prior_touch"
ABLATION_MODEL_IDS = ("no_prior_touch_support", "no_echo_guard")
SIMPLE_BASELINE_MODEL_IDS = (
    "strength_only",
    "four_gate_minimum",
    "four_gate_mean",
    "return_only",
    "observed_stability_only",
    "echo_guarded_gate_minimum",
)
CONTINUOUS_MODEL_IDS = (
    PRIMARY_MODEL_ID,
    *ABLATION_MODEL_IDS,
    *SIMPLE_BASELINE_MODEL_IDS,
)
CONSTANT_MODEL_IDS = ("always_hold", "always_crown", "always_resist")
MODEL_IDS = (*CONTINUOUS_MODEL_IDS, *CONSTANT_MODEL_IDS)
CONSTANT_PREDICTIONS = {
    "always_hold": 0,
    "always_crown": 1,
    "always_resist": -1,
}
GENERATOR_LINEAGES = (
    "ar_recovery_v1",
    "impulse_response_v1",
    "coupled_oscillator_v1",
    "piecewise_hysteresis_v1",
)
BACKEND_LINEAGE_BY_CODE = dict(enumerate(GENERATOR_LINEAGES))

PRELABEL_FILES = {
    "scores": "v1_8_2_continuous_scores.csv",
    "prediction_cube": "v1_8_2_prediction_cube.csv",
    "options": "v1_8_2_threshold_options.json",
    "manifest": "v1_8_2_prelabel_manifest.json",
    "receipt": "v1_8_2_prelabel_receipt.json",
}
EVALUATION_FILES = {
    "join_audit": "v1_8_2_join_audit.json",
    "duplicate_audit": "v1_8_2_duplicate_audit.json",
    "selection": "v1_8_2_threshold_selection.json",
    "comparisons": "v1_8_2_model_comparisons.json",
    "uncertainty": "v1_8_2_uncertainty.json",
    "failure_capability": "v1_8_2_failure_capability.json",
    "result": "v1_8_2_development_result.json",
    "manifest": "v1_8_2_evaluation_manifest.json",
    "receipt": "v1_8_2_evaluation_receipt.json",
}

READY = "READY_FOR_V1_8_3_CONTRACT_ONLY"
HOLD_INSUFFICIENT = "HOLD_INSUFFICIENT_GENERATOR_LINEAGES"
HOLD_BASELINE = "HOLD_BASELINE_EQUIVALENT_OR_DOMINANT"
HOLD_FAILURE = "HOLD_FAILURE_CAPABILITY_NOT_DEMONSTRATED"
INVALID_ARTIFACT = "INVALID_ARTIFACT_OR_RECEIPT"
INVALID_LABEL = "INVALID_LABEL_OR_IDENTIFIER_LEAK"
INVALID_ALIAS = "INVALID_OBSERVATIONAL_ALIASING"
INVALID_OVERLAP = "INVALID_GENERATOR_LINEAGE_OVERLAP"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BLIND_ID_RE = re.compile(r"^zg82_[0-9a-f]{24}$")
ATOMIC_ID_RE = re.compile(r"^za82_[0-9a-f]{24}$")


class DevelopmentEvaluationError(ValueError):
    """Raised when retained authority or immutable evidence fails closed."""


class _SemanticInvalid(ValueError):
    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DevelopmentEvaluationError(f"value is not canonical JSON: {exc}") from exc


def _json_bytes(value: object) -> bytes:
    return (_canonical_json(value) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_sha256(value: object, *, field: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise DevelopmentEvaluationError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DevelopmentEvaluationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _strict_json(data: bytes, *, source: str) -> object:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DevelopmentEvaluationError(f"{source} is not UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                DevelopmentEvaluationError(f"{source} contains {token}")
            ),
        )
    except DevelopmentEvaluationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DevelopmentEvaluationError(f"{source} is not strict JSON: {exc}") from exc
    return value


def _strict_canonical_document(data: bytes, *, source: str) -> dict[str, object]:
    value = _strict_json(data, source=source)
    if not isinstance(value, dict) or data != _json_bytes(value):
        raise DevelopmentEvaluationError(f"{source} is not one canonical JSON object")
    return value


def _is_link_or_junction(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def _read_regular(path: str | Path, *, field: str) -> bytes:
    source = Path(path).absolute()
    if not source.is_file() or _is_link_or_junction(source):
        raise DevelopmentEvaluationError(f"{field} is missing or unsafe: {source}")
    for ancestor in (source, *source.parents):
        if ancestor.exists() and _is_link_or_junction(ancestor):
            raise DevelopmentEvaluationError(f"{field} has a linked path component")
    before = os.stat(source, follow_symlinks=False)
    data = source.read_bytes()
    after = os.stat(source, follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise DevelopmentEvaluationError(f"{field} changed while being read")
    return data


def _expect_hash(data: bytes, expected: str, *, field: str) -> None:
    if _sha256(data) != _validate_sha256(expected, field=f"expected_{field}_sha256"):
        raise DevelopmentEvaluationError(f"{field} SHA-256 mismatch")


def _parse_jsonl(data: bytes, *, source: str) -> list[dict[str, object]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DevelopmentEvaluationError(f"{source} is not UTF-8") from exc
    if not text.endswith("\n") or "\r" in text:
        raise DevelopmentEvaluationError(f"{source} is not canonical JSONL")
    lines = text.splitlines()
    if not lines or any(not line for line in lines):
        raise DevelopmentEvaluationError(f"{source} contains empty rows")
    rows: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        value = _strict_json(line.encode("utf-8"), source=f"{source}:{index + 1}")
        if not isinstance(value, dict) or line != _canonical_json(value):
            raise DevelopmentEvaluationError(f"{source}:{index + 1} is not canonical")
        rows.append(value)
    return rows


def _parse_csv(data: bytes, *, header: Sequence[str], source: str) -> list[list[str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DevelopmentEvaluationError(f"{source} is not UTF-8") from exc
    if not text.endswith("\n") or "\r" in text:
        raise DevelopmentEvaluationError(f"{source} is not canonical LF CSV")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        observed = next(reader)
    except StopIteration as exc:
        raise DevelopmentEvaluationError(f"{source} is empty") from exc
    if observed != list(header):
        raise DevelopmentEvaluationError(f"{source} header is not exact")
    rows = list(reader)
    if any(len(row) != len(header) for row in rows):
        raise DevelopmentEvaluationError(f"{source} contains a wrong-width row")
    return rows


def _actual_int(text: str, *, field: str, minimum: int = 0) -> int:
    if not text or (text != "0" and text.startswith("0")) or not text.isascii() or not text.isdigit():
        raise DevelopmentEvaluationError(f"{field} must be a canonical nonnegative integer")
    value = int(text)
    if value < minimum:
        raise DevelopmentEvaluationError(f"{field} is below its minimum")
    return value


def _unit_float(text: str, *, field: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise DevelopmentEvaluationError(f"{field} is not a float") from exc
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise DevelopmentEvaluationError(f"{field} must satisfy 0 <= value <= 1")
    return 0.0 if value == 0.0 else value


def _verify_source_files(source_manifest: Mapping[str, object]) -> None:
    records = source_manifest.get("bound_source_files")
    if not isinstance(records, list):
        raise DevelopmentEvaluationError("source manifest has no bound source files")
    observed_paths = [
        record.get("relative_path") if isinstance(record, dict) else None
        for record in records
    ]
    if observed_paths != list(SOURCE_BINDING_FILES):
        raise DevelopmentEvaluationError("source manifest file allowlist is not exact")
    root = Path(__file__).resolve().parents[2]
    seen: set[str] = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {
            "relative_path",
            "sha256",
            "size_bytes",
        }:
            raise DevelopmentEvaluationError("source manifest source record is malformed")
        relative = record["relative_path"]
        if type(relative) is not str or not relative or relative in seen:
            raise DevelopmentEvaluationError("source manifest source paths are invalid")
        seen.add(relative)
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise DevelopmentEvaluationError("bound source path escapes the repository")
        data = _read_regular(root / candidate, field=f"bound source {position}")
        if _sha256(data) != record["sha256"] or len(data) != record["size_bytes"]:
            raise DevelopmentEvaluationError(f"bound source changed: {relative}")


def _verify_prelabel_package_files(prelabel_manifest: Mapping[str, object]) -> None:
    records = prelabel_manifest.get("package_files")
    if not isinstance(records, list):
        raise DevelopmentEvaluationError("prelabel package file records are missing")
    observed_paths = [
        record.get("relative_path") if isinstance(record, dict) else None
        for record in records
    ]
    if observed_paths != list(PRELABEL_FILE_ALLOWLIST):
        raise DevelopmentEvaluationError("prelabel package allowlist is not exact")
    root = Path(__file__).resolve().parents[2]
    seen: set[str] = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {
            "relative_path",
            "sha256",
            "size_bytes",
        }:
            raise DevelopmentEvaluationError("prelabel package record is malformed")
        relative = record["relative_path"]
        if type(relative) is not str or not relative or relative in seen:
            raise DevelopmentEvaluationError("prelabel package paths are invalid")
        seen.add(relative)
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise DevelopmentEvaluationError("prelabel package path escapes repository")
        data = _read_regular(root / candidate, field=f"prelabel package source {position}")
        if _sha256(data) != record["sha256"] or len(data) != record["size_bytes"]:
            raise DevelopmentEvaluationError(f"prelabel package source changed: {relative}")
    contract = {
        "version": VERSION,
        "contract_id": PRELABEL_CONTRACT_ID,
        "file_allowlist": records,
    }
    if prelabel_manifest.get("prelabel_contract_id") != PRELABEL_CONTRACT_ID or (
        prelabel_manifest.get("prelabel_contract_sha256")
        != _sha256(_canonical_json(contract).encode("utf-8"))
    ):
        raise DevelopmentEvaluationError("prelabel source contract digest changed")


def _evaluator_package() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    records: list[dict[str, object]] = []
    for relative in EVALUATOR_FILE_ALLOWLIST:
        data = _read_regular(root / relative, field=f"evaluator package {relative}")
        records.append(
            {
                "relative_path": relative,
                "sha256": _sha256(data),
                "size_bytes": len(data),
            }
        )
    contract = {
        "version": VERSION,
        "evaluator_id": EVALUATOR_ID,
        "file_allowlist": records,
    }
    return {
        "files": records,
        "contract_sha256": _sha256(_canonical_json(contract).encode("utf-8")),
    }


def _verify_raw_traces(
    raw_manifest_path: Path, raw_manifest: Mapping[str, object]
) -> dict[int, list[list[int]]]:
    entries = raw_manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != TOTAL_CASES:
        raise DevelopmentEvaluationError("raw manifest must bind exactly 144 traces")
    root = raw_manifest_path.absolute().parent.resolve(strict=True)
    samples_by_row: dict[int, list[list[int]]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("row_index") != index:
            raise DevelopmentEvaluationError("raw manifest rows are not exact and ordered")
        if entry.get("sample_count") != SAMPLE_COUNT:
            raise DevelopmentEvaluationError("raw trace sample count is not locked")
        relative_text = entry.get("trace_relative_path")
        if type(relative_text) is not str:
            raise DevelopmentEvaluationError("raw trace path is missing")
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise DevelopmentEvaluationError("raw trace path escapes its manifest root")
        candidate = (root / relative).resolve(strict=True)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise DevelopmentEvaluationError("raw trace resolves outside its root") from exc
        data = _read_regular(candidate, field=f"raw trace {index}")
        if _sha256(data) != entry.get("trace_sha256"):
            raise DevelopmentEvaluationError(f"raw trace {index} SHA-256 mismatch")
        rows = _parse_csv(
            data,
            header=("sample_index", "target_q", "peer_a_q", "peer_b_q", "peer_c_q"),
            source=f"raw trace {index}",
        )
        if len(rows) != SAMPLE_COUNT:
            raise DevelopmentEvaluationError(f"raw trace {index} must have 1001 samples")
        samples: list[list[int]] = []
        for sample_index, row in enumerate(rows):
            if _actual_int(row[0], field="sample_index") != sample_index:
                raise DevelopmentEvaluationError(f"raw trace {index} sample indices changed")
            channels: list[int] = []
            for value in row[1:]:
                try:
                    channels.append(int(value))
                except ValueError as exc:
                    raise DevelopmentEvaluationError(
                        f"raw trace {index} contains a non-integer channel"
                    ) from exc
            samples.append(channels)
        samples_by_row[index] = samples
    return samples_by_row


def _verify_nonsemantic_chain(
    *,
    observable_source_path: Path,
    recipe_path: Path,
    raw_manifest_path: Path,
    extraction_manifest_path: Path,
    extraction_source_manifest_path: Path,
    development_fingerprint_path: Path,
    split_receipt_path: Path,
    split_manifest_path: Path,
    prelabel_dir: Path,
    expected_split_receipt_sha256: str,
    expected_recipe_sha256: str,
    expected_raw_manifest_sha256: str,
    expected_extraction_manifest_sha256: str,
    expected_extraction_source_manifest_sha256: str,
    expected_development_fingerprint_sha256: str,
    expected_observable_source_sha256: str,
    expected_prelabel_receipt_sha256: str,
    expected_v1_8_1_package_contract_sha256: str,
    events: list[str],
) -> dict[str, object]:
    observable_bytes = _read_regular(observable_source_path, field="observable source")
    recipe_bytes = _read_regular(recipe_path, field="numeric recipes")
    raw_manifest_bytes = _read_regular(raw_manifest_path, field="raw manifest")
    extraction_manifest_bytes = _read_regular(
        extraction_manifest_path, field="extraction manifest"
    )
    source_manifest_bytes = _read_regular(
        extraction_source_manifest_path, field="extraction source manifest"
    )
    fingerprint_bytes = _read_regular(
        development_fingerprint_path, field="development fingerprint"
    )
    split_receipt_bytes = _read_regular(split_receipt_path, field="split receipt")
    split_manifest_bytes = _read_regular(split_manifest_path, field="split manifest")

    expected_values = {
        "observable_source": expected_observable_source_sha256,
        "recipe": expected_recipe_sha256,
        "raw_manifest": expected_raw_manifest_sha256,
        "extraction_manifest": expected_extraction_manifest_sha256,
        "extraction_source_manifest": expected_extraction_source_manifest_sha256,
        "development_fingerprint": expected_development_fingerprint_sha256,
        "split_receipt": expected_split_receipt_sha256,
    }
    actual_bytes = {
        "observable_source": observable_bytes,
        "recipe": recipe_bytes,
        "raw_manifest": raw_manifest_bytes,
        "extraction_manifest": extraction_manifest_bytes,
        "extraction_source_manifest": source_manifest_bytes,
        "development_fingerprint": fingerprint_bytes,
        "split_receipt": split_receipt_bytes,
    }
    for key, expected in expected_values.items():
        _expect_hash(actual_bytes[key], expected, field=key)

    split_receipt = _strict_canonical_document(split_receipt_bytes, source="split receipt")
    split_manifest = _strict_canonical_document(split_manifest_bytes, source="split manifest")
    raw_manifest = _strict_canonical_document(raw_manifest_bytes, source="raw manifest")
    extraction_manifest = _strict_canonical_document(
        extraction_manifest_bytes, source="extraction manifest"
    )
    source_manifest = _strict_canonical_document(
        source_manifest_bytes, source="extraction source manifest"
    )
    fingerprint = _strict_canonical_document(
        fingerprint_bytes, source="development fingerprint"
    )

    if split_receipt.get("split_manifest_sha256") != _sha256(split_manifest_bytes):
        raise DevelopmentEvaluationError("split receipt does not bind split manifest")
    if split_receipt.get("row_count") != TOTAL_CASES or split_manifest.get("row_count") != TOTAL_CASES:
        raise DevelopmentEvaluationError("split cardinality is not exactly 144")
    for receipt_key, manifest_key in (
        ("recipe_sha256", "recipe_sha256"),
        ("join_key_sha256", "join_key_sha256"),
        ("label_vault_sha256", "label_vault_sha256"),
        ("group_vault_sha256", "group_vault_sha256"),
        ("generator_contract_sha256", "generator_contract_sha256"),
    ):
        if split_receipt.get(receipt_key) != split_manifest.get(manifest_key):
            raise DevelopmentEvaluationError(f"split receipt does not bind {receipt_key}")
    if split_receipt.get("recipe_sha256") != expected_recipe_sha256:
        raise DevelopmentEvaluationError("split chain does not bind retained recipes")
    generator_contract_sha256 = split_manifest.get("generator_contract_sha256")
    if (
        split_manifest.get("generator_contract_id") != GENERATOR_CONTRACT_ID
        or type(generator_contract_sha256) is not str
        or SHA256_RE.fullmatch(generator_contract_sha256) is None
    ):
        raise DevelopmentEvaluationError("split generator contract is not exact")

    if raw_manifest.get("recipe_sha256") != expected_recipe_sha256:
        raise DevelopmentEvaluationError("raw manifest does not bind retained recipes")
    if raw_manifest.get("generator_contract_sha256") != generator_contract_sha256:
        raise DevelopmentEvaluationError("raw manifest generator contract changed")
    if raw_manifest.get("row_count") != TOTAL_CASES:
        raise DevelopmentEvaluationError("raw manifest cardinality is not 144")
    if raw_manifest.get("sample_count_per_row") != SAMPLE_COUNT or raw_manifest.get("trace_scale") != TRACE_SCALE:
        raise DevelopmentEvaluationError("raw numeric contract changed")
    raw_samples_by_row = _verify_raw_traces(raw_manifest_path, raw_manifest)

    if extraction_manifest.get("raw_manifest_sha256") != expected_raw_manifest_sha256:
        raise DevelopmentEvaluationError("extraction manifest does not bind raw manifest")
    if extraction_manifest.get("generator_contract_sha256") != generator_contract_sha256:
        raise DevelopmentEvaluationError("extraction generator contract changed")
    if extraction_manifest.get("observable_input_sha256") != expected_observable_source_sha256:
        raise DevelopmentEvaluationError("extraction manifest does not bind observables")
    if extraction_manifest.get("frame_ranges_inclusive") != {
        name: [start, end] for name, (start, end) in FRAME_RANGES.items()
    }:
        raise DevelopmentEvaluationError("extraction frame windows changed")
    extraction_entries = extraction_manifest.get("entries")
    raw_entries = raw_manifest.get("entries")
    if not isinstance(extraction_entries, list) or len(extraction_entries) != TOTAL_CASES:
        raise DevelopmentEvaluationError("extraction manifest cardinality is not 144")
    for index, (raw_entry, extraction_entry) in enumerate(
        zip(raw_entries, extraction_entries, strict=True)  # type: ignore[arg-type]
    ):
        if not isinstance(extraction_entry, dict) or extraction_entry.get("row_index") != index:
            raise DevelopmentEvaluationError("extraction entries are not exact and ordered")
        if not isinstance(raw_entry, dict) or extraction_entry.get("trace_sha256") != raw_entry.get("trace_sha256"):
            raise DevelopmentEvaluationError("extraction trace binding mismatch")

    if (
        source_manifest.get("raw_manifest_sha256") != expected_raw_manifest_sha256
        or source_manifest.get("extraction_manifest_sha256")
        != expected_extraction_manifest_sha256
        or source_manifest.get("observable_input_sha256")
        != expected_observable_source_sha256
        or source_manifest.get("row_count") != TOTAL_CASES
    ):
        raise DevelopmentEvaluationError("source manifest artifact bindings changed")
    bound_artifacts = source_manifest.get("bound_artifacts")
    if not isinstance(bound_artifacts, list):
        raise DevelopmentEvaluationError("source manifest bound artifacts are missing")
    expected_artifacts = {
        "raw_manifest": (expected_raw_manifest_sha256, len(raw_manifest_bytes)),
        "extraction_manifest": (
            expected_extraction_manifest_sha256,
            len(extraction_manifest_bytes),
        ),
        "observable_inputs": (
            expected_observable_source_sha256,
            len(observable_bytes),
        ),
    }
    actual_artifacts: dict[str, tuple[object, object]] = {}
    for record in bound_artifacts:
        if not isinstance(record, dict) or set(record) != {
            "artifact",
            "sha256",
            "size_bytes",
        }:
            raise DevelopmentEvaluationError("source manifest artifact record is malformed")
        name = record["artifact"]
        if type(name) is not str or name in actual_artifacts:
            raise DevelopmentEvaluationError("source manifest artifact names are invalid")
        actual_artifacts[name] = (record["sha256"], record["size_bytes"])
    if actual_artifacts != expected_artifacts:
        raise DevelopmentEvaluationError("source manifest does not exactly bind artifacts")
    _verify_source_files(source_manifest)
    bound_source_records = source_manifest["bound_source_files"]
    assert isinstance(bound_source_records, list)
    generator_record = bound_source_records[-1]
    if (
        not isinstance(generator_record, dict)
        or generator_record.get("relative_path")
        != "contracts/v1_8_2_development_generator.json"
    ):
        raise DevelopmentEvaluationError(
            "generator contract root is not linked to the bound contract bytes"
        )
    generator_contract_bytes = _read_regular(
        Path(__file__).resolve().parents[2]
        / "contracts/v1_8_2_development_generator.json",
        field="development generator contract",
    )
    generator_contract_document = _strict_canonical_document(
        generator_contract_bytes, source="development generator contract"
    )
    if (
        generator_record.get("sha256") != _sha256(generator_contract_bytes)
        or generator_contract_sha256
        != _sha256(_canonical_json(generator_contract_document).encode("utf-8"))
    ):
        raise DevelopmentEvaluationError(
            "generator contract semantic root does not match its bound file"
        )

    fingerprint_bindings = {
        "recipe_sha256": expected_recipe_sha256,
        "raw_manifest_sha256": expected_raw_manifest_sha256,
        "extraction_manifest_sha256": expected_extraction_manifest_sha256,
        "source_manifest_sha256": expected_extraction_source_manifest_sha256,
        "observable_input_sha256": expected_observable_source_sha256,
    }
    for key, expected in fingerprint_bindings.items():
        if fingerprint.get(key) != expected:
            raise DevelopmentEvaluationError(f"development fingerprint does not bind {key}")
    if any(
        fingerprint.get(key) != TOTAL_CASES
        for key in ("raw_recipe_count", "raw_trace_count", "raw_observable_count", "row_count")
    ):
        raise DevelopmentEvaluationError("development fingerprint raw counts changed")

    observable_rows = _parse_jsonl(observable_bytes, source="observable source")
    if len(observable_rows) != TOTAL_CASES:
        raise DevelopmentEvaluationError("observable source must contain exactly 144 rows")
    recipe_rows = _parse_jsonl(recipe_bytes, source="numeric recipes")
    if len(recipe_rows) != TOTAL_CASES:
        raise DevelopmentEvaluationError("numeric recipes must contain exactly 144 rows")
    for expected_index, recipe in enumerate(recipe_rows):
        if recipe.get("row_index") != expected_index:
            raise DevelopmentEvaluationError("numeric recipes are not exact and ordered")
        backend = recipe.get("backend_code")
        if type(backend) is not int or backend not in BACKEND_LINEAGE_BY_CODE:
            raise DevelopmentEvaluationError("numeric recipe backend code is invalid")
    observable_by_row: dict[int, object] = {}
    fingerprint_rows = fingerprint.get("fingerprints")
    if not isinstance(fingerprint_rows, list) or len(fingerprint_rows) != TOTAL_CASES:
        raise DevelopmentEvaluationError("development fingerprint rows are missing")
    observables_by_digest: dict[str, list[tuple[int, int]]] = {}
    for expected_index, (row, recipe, fp, extraction_entry) in enumerate(
        zip(observable_rows, recipe_rows, fingerprint_rows, extraction_entries, strict=True)
    ):
        if set(row) != {"row_index", "observable_frames"} or row.get("row_index") != expected_index:
            raise DevelopmentEvaluationError("observable rows are not exact and ordered")
        if not isinstance(fp, dict) or fp.get("row_index") != expected_index:
            raise DevelopmentEvaluationError("fingerprint rows are not exact and ordered")
        digest = _sha256(_canonical_json(row["observable_frames"]).encode("utf-8"))
        if fp.get("observable_sha256") != digest:
            raise DevelopmentEvaluationError("fingerprint observable digest mismatch")
        if fp.get("trace_sha256") != extraction_entry.get("trace_sha256"):
            raise DevelopmentEvaluationError("fingerprint trace digest mismatch")
        backend = recipe["backend_code"]
        if fp.get("backend_code") != backend or extraction_entry.get("backend_code") != backend:
            raise DevelopmentEvaluationError("backend binding changed across development artifacts")
        frames = row["observable_frames"]
        frame_records = extraction_entry.get("frames")
        if not isinstance(frames, list) or len(frames) != 3 or not isinstance(frame_records, dict):
            raise DevelopmentEvaluationError("observable frame binding is malformed")
        for name, frame in zip(("early", "witness", "late"), frames, strict=True):
            record = frame_records.get(name)
            frame_digest = _sha256(_canonical_json(frame).encode("utf-8"))
            start, end = FRAME_RANGES[name]
            raw_slice_digest = _sha256(
                _canonical_json(raw_samples_by_row[expected_index][start : end + 1]).encode(
                    "utf-8"
                )
            )
            if (
                not isinstance(record, dict)
                or set(record)
                != {
                    "start_index",
                    "end_index_inclusive",
                    "observable_sha256",
                    "raw_slice_sha256",
                }
                or record.get("start_index") != start
                or record.get("end_index_inclusive") != end
                or record.get("observable_sha256") != frame_digest
                or record.get("raw_slice_sha256") != raw_slice_digest
            ):
                raise DevelopmentEvaluationError("extraction frame digest mismatch")
        observables_by_digest.setdefault(digest, []).append((expected_index, backend))
        observable_by_row[expected_index] = row["observable_frames"]
    if fingerprint.get("unique_observable_count") != len(observables_by_digest):
        raise DevelopmentEvaluationError("fingerprint unique-observable count changed")
    if fingerprint.get("effective_observable_count") != len(observables_by_digest):
        raise DevelopmentEvaluationError("fingerprint effective-observable count changed")
    # Cross-backend equality is a scientific integrity outcome, not an excuse
    # to open no audit trail. The post-join duplicate audit maps backend codes
    # to sealed lineage IDs and emits INVALID_GENERATOR_LINEAGE_OVERLAP.

    if not prelabel_dir.is_dir() or _is_link_or_junction(prelabel_dir):
        raise DevelopmentEvaluationError("prelabel artifact directory is missing or unsafe")
    if {path.name for path in prelabel_dir.iterdir()} != set(PRELABEL_FILES.values()):
        raise DevelopmentEvaluationError("prelabel artifact set is not exact")
    prelabel_bytes = {
        key: _read_regular(prelabel_dir / filename, field=f"prelabel {key}")
        for key, filename in PRELABEL_FILES.items()
    }
    _expect_hash(
        prelabel_bytes["receipt"],
        expected_prelabel_receipt_sha256,
        field="prelabel_receipt",
    )
    prelabel_receipt = _strict_canonical_document(
        prelabel_bytes["receipt"], source="prelabel receipt"
    )
    prelabel_manifest = _strict_canonical_document(
        prelabel_bytes["manifest"], source="prelabel manifest"
    )
    options_document = _strict_canonical_document(
        prelabel_bytes["options"], source="prelabel threshold options"
    )
    retained = {
        "caller_retained_split_receipt_sha256": expected_split_receipt_sha256,
        "caller_retained_extraction_source_manifest_sha256": (
            expected_extraction_source_manifest_sha256
        ),
        "caller_retained_development_fingerprint_sha256": (
            expected_development_fingerprint_sha256
        ),
        "observable_source_sha256": expected_observable_source_sha256,
        "v1_8_1_package_contract_sha256": _validate_sha256(
            expected_v1_8_1_package_contract_sha256,
            field="expected_v1_8_1_package_contract_sha256",
        ),
    }
    for key, expected in retained.items():
        if prelabel_receipt.get(key) != expected or prelabel_manifest.get(key) != expected:
            raise DevelopmentEvaluationError(f"prelabel artifacts do not retain {key}")
    prelabel_hash_bindings = {
        "scores_sha256": "scores",
        "prediction_cube_sha256": "prediction_cube",
        "threshold_options_sha256": "options",
        "manifest_sha256": "manifest",
    }
    for field, artifact in prelabel_hash_bindings.items():
        if prelabel_receipt.get(field) != _sha256(prelabel_bytes[artifact]):
            raise DevelopmentEvaluationError(f"prelabel receipt does not bind {artifact}")
    if prelabel_manifest.get("observable_row_count") != TOTAL_CASES:
        raise DevelopmentEvaluationError("prelabel observable count is not 144")
    _verify_prelabel_package_files(prelabel_manifest)
    if (
        prelabel_receipt.get("prelabel_contract_sha256")
        != prelabel_manifest.get("prelabel_contract_sha256")
    ):
        raise DevelopmentEvaluationError("prelabel receipt does not bind source contract")
    expected_options = [option.to_dict() for option in THRESHOLD_OPTIONS]
    if (
        options_document.get("threshold_options") != expected_options
        or options_document.get("selected_option_id") is not None
        or prelabel_manifest.get("model_ids") != list(MODEL_IDS)
        or prelabel_manifest.get("continuous_model_ids") != list(CONTINUOUS_MODEL_IDS)
        or prelabel_manifest.get("constant_model_ids") != list(CONSTANT_MODEL_IDS)
    ):
        raise DevelopmentEvaluationError("prelabel registry or threshold options changed")

    score_rows = _parse_csv(
        prelabel_bytes["scores"],
        header=("row_index", "model_id", "score"),
        source="prelabel continuous scores",
    )
    prediction_rows = _parse_csv(
        prelabel_bytes["prediction_cube"],
        header=("row_index", "model_id", "option_id", "score", "proposed_trinary"),
        source="prelabel prediction cube",
    )
    if len(score_rows) != TOTAL_CASES * len(CONTINUOUS_MODEL_IDS):
        raise DevelopmentEvaluationError("prelabel score cardinality changed")
    if len(prediction_rows) != TOTAL_CASES * (
        len(CONTINUOUS_MODEL_IDS) * len(THRESHOLD_OPTIONS) + len(CONSTANT_MODEL_IDS)
    ):
        raise DevelopmentEvaluationError("prelabel prediction cardinality changed")
    scores: dict[tuple[int, str], float] = {}
    for position, row in enumerate(score_rows):
        row_index = _actual_int(row[0], field="score row_index")
        model_id = row[1]
        expected_row = position // len(CONTINUOUS_MODEL_IDS)
        expected_model = CONTINUOUS_MODEL_IDS[position % len(CONTINUOUS_MODEL_IDS)]
        if row_index != expected_row or model_id != expected_model:
            raise DevelopmentEvaluationError("prelabel score rows are not exact and ordered")
        scores[(row_index, model_id)] = _unit_float(row[2], field="continuous score")

    predictions: dict[tuple[int, str, str], int] = {}
    per_row_prediction_count = len(CONTINUOUS_MODEL_IDS) * len(THRESHOLD_OPTIONS) + len(
        CONSTANT_MODEL_IDS
    )
    for position, row in enumerate(prediction_rows):
        row_index = _actual_int(row[0], field="prediction row_index")
        within = position % per_row_prediction_count
        if row_index != position // per_row_prediction_count:
            raise DevelopmentEvaluationError("prediction rows are not grouped by row index")
        if within < len(CONTINUOUS_MODEL_IDS) * len(THRESHOLD_OPTIONS):
            model_id = CONTINUOUS_MODEL_IDS[within // len(THRESHOLD_OPTIONS)]
            option = THRESHOLD_OPTIONS[within % len(THRESHOLD_OPTIONS)]
            if row[1] != model_id or row[2] != option.option_id:
                raise DevelopmentEvaluationError("prediction cube order changed")
            score = _unit_float(row[3], field="prediction score")
            if score.hex() != scores[(row_index, model_id)].hex():
                raise DevelopmentEvaluationError("prediction score differs from frozen score")
            proposed = int(row[4]) if row[4] in {"-1", "0", "1"} else 2
            if proposed != classify_score(score, option):
                raise DevelopmentEvaluationError("prediction cube violates threshold contract")
        else:
            constant_index = within - len(CONTINUOUS_MODEL_IDS) * len(THRESHOLD_OPTIONS)
            model_id = CONSTANT_MODEL_IDS[constant_index]
            if row[1] != model_id or row[2] != "constant" or row[3] != "":
                raise DevelopmentEvaluationError("constant prediction row changed")
            proposed = int(row[4]) if row[4] in {"-1", "0", "1"} else 2
            if proposed != CONSTANT_PREDICTIONS[model_id]:
                raise DevelopmentEvaluationError("constant prediction changed")
        key = (row_index, model_id, row[2])
        if key in predictions:
            raise DevelopmentEvaluationError("duplicate prediction cube key")
        predictions[key] = proposed

    evaluator_package = _evaluator_package()
    events.append("NONSEMANTIC_CHAIN_VERIFIED")
    events.append("PRELABEL_ARTIFACTS_VERIFIED")
    return {
        "observable_bytes": observable_bytes,
        "observable_by_row": observable_by_row,
        "recipe_bytes": recipe_bytes,
        "recipe_rows": recipe_rows,
        "raw_manifest": raw_manifest,
        "extraction_manifest": extraction_manifest,
        "source_manifest": source_manifest,
        "fingerprint": fingerprint,
        "split_receipt": split_receipt,
        "split_manifest": split_manifest,
        "prelabel_receipt": prelabel_receipt,
        "prelabel_manifest": prelabel_manifest,
        "scores": scores,
        "predictions": predictions,
        "evaluator_package": evaluator_package,
        "input_hashes": {
            **{key: _sha256(value) for key, value in actual_bytes.items()},
            "split_manifest": _sha256(split_manifest_bytes),
            "prelabel_receipt": _sha256(prelabel_bytes["receipt"]),
            "prelabel_manifest": _sha256(prelabel_bytes["manifest"]),
            "prelabel_scores": _sha256(prelabel_bytes["scores"]),
            "prelabel_prediction_cube": _sha256(prelabel_bytes["prediction_cube"]),
            "prelabel_threshold_options": _sha256(prelabel_bytes["options"]),
            "evaluator_contract": evaluator_package["contract_sha256"],
        },
    }


def _semantic_join(
    *,
    authority: Mapping[str, object],
    join_keys_path: Path,
    label_vault_path: Path,
    group_vault_path: Path,
    recipe_path: Path,
    events: list[str],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if events[-1] != "PRELABEL_ARTIFACTS_VERIFIED":
        raise DevelopmentEvaluationError("semantic vault read attempted before prelabel verification")
    join_bytes = _read_regular(join_keys_path, field="join keys")
    label_bytes = _read_regular(label_vault_path, field="label vault")
    group_bytes = _read_regular(group_vault_path, field="group vault")
    events.append("SEMANTIC_VAULT_BYTES_READ_AFTER_PRELABEL_VERIFICATION")
    split_manifest = authority["split_manifest"]
    if not isinstance(split_manifest, Mapping):
        raise DevelopmentEvaluationError("internal split manifest type changed")
    expected_hashes = {
        "join keys": split_manifest.get("join_key_sha256"),
        "label vault": split_manifest.get("label_vault_sha256"),
        "group vault": split_manifest.get("group_vault_sha256"),
    }
    for name, data in (
        ("join keys", join_bytes),
        ("label vault", label_bytes),
        ("group vault", group_bytes),
    ):
        if _sha256(data) != expected_hashes[name]:
            raise DevelopmentEvaluationError(f"{name} does not match the retained split")

    try:
        join_rows = _parse_csv(
            join_bytes,
            header=("row_index", "blind_case_id"),
            source="join keys",
        )
        label_rows = _parse_csv(
            label_bytes,
            header=("blind_case_id", "evaluation_role"),
            source="label vault",
        )
        group_rows = _parse_csv(
            group_bytes,
            header=("blind_case_id", "generator_lineage_id", "atomic_case_id"),
            source="group vault",
        )
    except DevelopmentEvaluationError as exc:
        raise _SemanticInvalid(INVALID_LABEL, str(exc)) from exc
    events.append("SEMANTIC_VAULTS_PARSED")

    if not all(len(rows) == TOTAL_CASES for rows in (join_rows, label_rows, group_rows)):
        raise _SemanticInvalid(INVALID_LABEL, "semantic join tables must each have 144 rows")
    row_to_blind: dict[int, str] = {}
    for row in join_rows:
        try:
            row_index = _actual_int(row[0], field="join row_index")
        except DevelopmentEvaluationError as exc:
            raise _SemanticInvalid(INVALID_LABEL, str(exc)) from exc
        blind = row[1]
        if (
            row_index in row_to_blind
            or row_index >= TOTAL_CASES
            or BLIND_ID_RE.fullmatch(blind) is None
            or blind in row_to_blind.values()
        ):
            raise _SemanticInvalid(INVALID_LABEL, "join keys are not a one-to-one opaque mapping")
        row_to_blind[row_index] = blind
    if set(row_to_blind) != set(range(TOTAL_CASES)):
        raise _SemanticInvalid(INVALID_LABEL, "join keys do not cover all observable rows")

    roles: dict[str, str] = {}
    for blind, role in label_rows:
        if blind in roles or BLIND_ID_RE.fullmatch(blind) is None or role not in REQUIRED_ROLES:
            raise _SemanticInvalid(INVALID_LABEL, "label vault contains invalid or duplicate keys")
        roles[blind] = role
    groups: dict[str, tuple[str, str]] = {}
    atomic_ids: set[str] = set()
    for blind, lineage, atomic_id in group_rows:
        if (
            blind in groups
            or BLIND_ID_RE.fullmatch(blind) is None
            or lineage not in GENERATOR_LINEAGES
            or ATOMIC_ID_RE.fullmatch(atomic_id) is None
            or atomic_id in atomic_ids
        ):
            raise _SemanticInvalid(INVALID_LABEL, "group vault contains invalid or duplicate keys")
        groups[blind] = (lineage, atomic_id)
        atomic_ids.add(atomic_id)
    blind_set = set(row_to_blind.values())
    if set(roles) != blind_set or set(groups) != blind_set:
        raise _SemanticInvalid(INVALID_LABEL, "semantic vault key sets do not match join keys")

    recipe_rows = authority["recipe_rows"]
    if not isinstance(recipe_rows, list) or len(recipe_rows) != TOTAL_CASES:
        raise DevelopmentEvaluationError("internal recipe rows changed after verification")
    observable_by_row = authority["observable_by_row"]
    if not isinstance(observable_by_row, Mapping):
        raise DevelopmentEvaluationError("internal observable mapping type changed")
    joined: list[dict[str, object]] = []
    for row_index in range(TOTAL_CASES):
        blind = row_to_blind[row_index]
        lineage, atomic_id = groups[blind]
        recipe = recipe_rows[row_index]
        backend = recipe.get("backend_code")
        if type(backend) is not int or BACKEND_LINEAGE_BY_CODE.get(backend) != lineage:
            raise _SemanticInvalid(INVALID_LABEL, "group lineage disagrees with frozen backend code")
        joined.append(
            {
                "row_index": row_index,
                "blind_case_id": blind,
                "atomic_case_id": atomic_id,
                "evaluation_role": roles[blind],
                "generator_lineage_id": lineage,
                "observable_frames": observable_by_row[row_index],
            }
        )

    by_lineage_role = Counter(
        (row["generator_lineage_id"], row["evaluation_role"]) for row in joined
    )
    if any(
        by_lineage_role[(lineage, role)] != CASES_PER_ROLE_PER_LINEAGE
        for lineage in GENERATOR_LINEAGES
        for role in REQUIRED_ROLES
    ):
        raise _SemanticInvalid(
            INVALID_LABEL,
            "each generator lineage must contain exactly 12 cases of each role",
        )
    join_audit = {
        "version": VERSION,
        "audit_state": "EXACT_POST_FREEZE_SEMANTIC_JOIN_COMPLETE",
        "status": "VALID_EXACT_JOIN",
        "raw_case_count": len(joined),
        "unique_blind_case_id_count": len(blind_set),
        "unique_atomic_case_id_count": len(atomic_ids),
        "generator_lineage_count": len(GENERATOR_LINEAGES),
        "generator_lineages": list(GENERATOR_LINEAGES),
        "role_counts_by_lineage": {
            lineage: {
                role: by_lineage_role[(lineage, role)] for role in REQUIRED_ROLES
            }
            for lineage in GENERATOR_LINEAGES
        },
        "semantic_vault_read_after_prelabel_verification": True,
        "event_order": list(events),
    }
    return joined, join_audit


def _cases_for_model(
    joined: Sequence[Mapping[str, object]],
    effective_indices: set[int],
    scores: Mapping[tuple[int, str], float],
    model_id: str,
) -> tuple[ScoredCase, ...]:
    return tuple(
        ScoredCase(
            generator_lineage_id=str(row["generator_lineage_id"]),
            evaluation_role=str(row["evaluation_role"]),
            score=scores[(int(row["row_index"]), model_id)],
        )
        for row in joined
        if int(row["row_index"]) in effective_indices
    )


def _metrics_by_lineage(predictions: Iterable[PredictionRecord]) -> dict[str, MetricResult]:
    rows = tuple(predictions)
    return {
        lineage: calculate_metrics(
            (row.evaluation_role, row.prediction)
            for row in rows
            if row.generator_lineage_id == lineage
        )
        for lineage in sorted({row.generator_lineage_id for row in rows})
    }


def _metric_values(by_lineage: Mapping[str, MetricResult]) -> dict[str, dict[str, float]]:
    fields = (
        "crown_precision",
        "expresser_crown_recall",
        "expresser_resist_rate",
        "latent_crown_rate",
        "latent_hold_recall",
        "trap_crown_rate",
        "trap_resist_recall",
        "nonlatent_hold_rate",
        "macro_recall",
        "fold_minimum_guardrail",
    )
    output: dict[str, dict[str, float]] = {}
    for field in fields:
        values: dict[str, float] = {}
        for lineage, metric in by_lineage.items():
            value = getattr(metric, field)
            if value is None:
                raise EvaluationMathError(f"undefined bootstrap metric: {field}")
            values[lineage] = float(value)
        output[field] = values
    return output


def _nested_to_dict(value: NestedSelectionResult) -> dict[str, object]:
    return value.to_dict()


def _frozen_to_dict(value: FrozenThresholdEvaluation) -> dict[str, object]:
    return value.to_dict()


def _constant_evaluation(
    *,
    joined: Sequence[Mapping[str, object]],
    effective_indices: set[int],
    model_id: str,
) -> tuple[AggregateMetrics, dict[str, MetricResult], dict[str, object]]:
    prediction = CONSTANT_PREDICTIONS[model_id]
    by_lineage: dict[str, MetricResult] = {}
    for lineage in GENERATOR_LINEAGES:
        by_lineage[lineage] = calculate_metrics(
            (str(row["evaluation_role"]), prediction)
            for row in joined
            if int(row["row_index"]) in effective_indices
            and row["generator_lineage_id"] == lineage
        )
    aggregate = aggregate_lineage_metrics(by_lineage, allow_dead_safe=True)
    status = constant_prediction_guard(
        prediction
        for row in joined
        if int(row["row_index"]) in effective_indices
    )
    if status is None:
        raise EvaluationMathError("locked constant control did not trigger production guard")
    return aggregate, by_lineage, {
        "status": status,
        "constant_prediction": prediction,
        "metrics_by_lineage": {
            lineage: metric.to_dict() for lineage, metric in by_lineage.items()
        },
        "aggregate_metrics": aggregate.to_dict(),
    }


def _empty_documents(
    *,
    status: str,
    reason: str,
    join_audit: Mapping[str, object],
    duplicate_document: Mapping[str, object],
    failure_rows: Sequence[Mapping[str, object]],
    events: Sequence[str],
) -> dict[str, dict[str, object]]:
    return {
        "join_audit": dict(join_audit),
        "duplicate_audit": dict(duplicate_document),
        "selection": {
            "version": VERSION,
            "selection_state": "NOT_EXECUTED_INVALID_INPUT",
            "selected_option_id": None,
            "reason": reason,
        },
        "comparisons": {
            "version": VERSION,
            "comparison_state": "NOT_EXECUTED_INVALID_INPUT",
            "comparison_requirement_passed": False,
            "reason": reason,
        },
        "uncertainty": {
            "version": VERSION,
            "uncertainty_state": "NOT_EXECUTED_INVALID_INPUT",
            "reason": reason,
        },
        "failure_capability": {
            "version": VERSION,
            "failure_capability_state": "EXECUTED",
            "passed": failure_capability_passed(failure_rows),
            "fixtures": list(failure_rows),
        },
        "result": {
            "version": VERSION,
            "evaluator_id": EVALUATOR_ID,
            "decision_status": status,
            "progression_authorized": False,
            "selected_option_id": None,
            "scientific_authority": "v1.7.11-alpha 0 / HOLD",
            "development_only": True,
            "holdout_material_accessed": False,
            "reasons": [reason],
            "event_order": list(events),
        },
    }


def _evaluate_documents(
    *,
    joined: Sequence[Mapping[str, object]],
    join_audit: Mapping[str, object],
    duplicate: DuplicateAuditResult,
    scores: Mapping[tuple[int, str], float],
    events: Sequence[str],
) -> dict[str, dict[str, object]]:
    effective_indices = set(duplicate.effective_row_indices)
    primary_cases = _cases_for_model(joined, effective_indices, scores, PRIMARY_MODEL_ID)
    failure_rows = failure_capability_rows()
    failure_passed = failure_capability_passed(failure_rows)
    primary_score_status = primary_score_guard(case.score for case in primary_cases)
    if primary_score_status == "INVALID_CONSTANT_PRIMARY_SCORE":
        return _empty_documents(
            status=INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR,
            reason="production primary-score guard detected a constant score",
            join_audit=join_audit,
            duplicate_document=duplicate.to_dict(),
            failure_rows=failure_rows,
            events=events,
        )

    try:
        primary = nested_logo_select(primary_cases)
    except EvaluationMathError as exc:
        status = (
            HOLD_INSUFFICIENT
            if HOLD_INSUFFICIENT in str(exc)
            else INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR
        )
        return _empty_documents(
            status=status,
            reason=str(exc),
            join_audit=join_audit,
            duplicate_document=duplicate.to_dict(),
            failure_rows=failure_rows,
            events=events,
        )

    repeated_primary = nested_logo_select(reversed(primary_cases))
    if repeated_primary != primary:
        return _empty_documents(
            status="INVALID_NONDETERMINISTIC_SELECTION",
            reason="primary nested selection changed under row-order reversal",
            join_audit=join_audit,
            duplicate_document=duplicate.to_dict(),
            failure_rows=failure_rows,
            events=events,
        )
    if primary.status != VALID_NESTED_SELECTION:
        return _empty_documents(
            status=INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR,
            reason="primary score is constant or produces a dead-safe OOF result",
            join_audit=join_audit,
            duplicate_document=duplicate.to_dict(),
            failure_rows=failure_rows,
            events=events,
        )

    primary_by_lineage = _metrics_by_lineage(primary.oof_predictions)
    primary_guard_diagnostics = {
        lineage: {
            "false_crown_status": false_crown_guard(metric),
            "balanced_pattern_status": balanced_prediction_guard(
                tuple(
                    row.evaluation_role
                    for row in primary.oof_predictions
                    if row.generator_lineage_id == lineage
                ),
                tuple(
                    row.prediction
                    for row in primary.oof_predictions
                    if row.generator_lineage_id == lineage
                ),
            ),
        }
        for lineage, metric in primary_by_lineage.items()
    }
    selected_option = next(
        option for option in THRESHOLD_OPTIONS if option.option_id == primary.selected_option_id
    )
    selection_document: dict[str, object] = {
        "version": VERSION,
        "selection_state": "DEVELOPMENT_ONLY_THRESHOLD_SELECTED",
        "primary_model_id": PRIMARY_MODEL_ID,
        "selected_option_id": selected_option.option_id,
        "selected_threshold": selected_option.to_dict(),
        "boundary_semantics": {
            "resist": "score <= resist_max",
            "hold": "resist_max < score < crown_min",
            "crown": "score >= crown_min",
        },
        "nested_leave_one_generator_lineage_out": primary.to_dict(),
        "per_lineage_oof_metrics": {
            lineage: metric.to_dict() for lineage, metric in primary_by_lineage.items()
        },
        "production_guard_diagnostics_by_lineage": primary_guard_diagnostics,
        "selected_threshold_contract": {
            "contract_id": "zerogate-v1.8.2-selected-development-threshold-v1",
            "model_id": PRIMARY_MODEL_ID,
            "option": selected_option.to_dict(),
            "development_only": True,
            "retuning_after_holdout_creation_forbidden": True,
        },
    }

    baseline_documents: dict[str, object] = {}
    ablation_documents: dict[str, object] = {}
    constant_documents: dict[str, object] = {}
    comparator_lineage_metrics: dict[str, dict[str, MetricResult]] = {}
    comparison_passes: list[bool] = []

    for model_id in SIMPLE_BASELINE_MODEL_IDS:
        cases = _cases_for_model(joined, effective_indices, scores, model_id)
        try:
            retuned = nested_logo_select(cases)
            retuned_strict = primary_strictly_better(primary.oof_metrics, retuned.oof_metrics)
            passed = (
                retuned.status == VALID_NESTED_SELECTION
                and retuned_strict
            )
            baseline_documents[model_id] = {
                "development_retuned": _nested_to_dict(retuned),
                "primary_strictly_better_retuned": retuned_strict,
                "requirement_passed": passed,
            }
            comparator_lineage_metrics[f"{model_id}:retuned"] = _metrics_by_lineage(
                retuned.oof_predictions
            )
        except EvaluationMathError as exc:
            if str(exc).startswith("no valid locked threshold option;") and (
                "INVALID_DEAD_SAFE_NO_CROWNS" in str(exc)
            ):
                passed = False
                baseline_documents[model_id] = {
                    "status": "INVALID_DEAD_SAFE_NO_CROWNS",
                    "reason": str(exc),
                    "requirement_passed": False,
                    "comparison_not_earned": True,
                }
            else:
                return _empty_documents(
                    status=INVALID_ARTIFACT,
                    reason=f"baseline {model_id} evaluation failed closed: {exc}",
                    join_audit=join_audit,
                    duplicate_document=duplicate.to_dict(),
                    failure_rows=failure_rows,
                    events=events,
                )
        comparison_passes.append(passed)

    for model_id in ABLATION_MODEL_IDS:
        cases = _cases_for_model(joined, effective_indices, scores, model_id)
        try:
            frozen = evaluate_frozen_thresholds(
                cases,
                outer_option_by_lineage=primary.outer_option_by_lineage,
                full_option_id=primary.selected_option_id,
            )
            retuned = nested_logo_select(cases)
            frozen_strict = primary_strictly_better(primary.oof_metrics, frozen.oof_metrics)
            retuned_strict = primary_strictly_better(primary.oof_metrics, retuned.oof_metrics)
            passed = (
                frozen.status == VALID_NESTED_SELECTION
                and retuned.status == VALID_NESTED_SELECTION
                and frozen_strict
                and retuned_strict
            )
            ablation_documents[model_id] = {
                "frozen_primary_thresholds": _frozen_to_dict(frozen),
                "development_retuned": _nested_to_dict(retuned),
                "primary_strictly_better_frozen": frozen_strict,
                "primary_strictly_better_retuned": retuned_strict,
                "necessity_requirement_passed": passed,
            }
            comparator_lineage_metrics[f"{model_id}:retuned"] = _metrics_by_lineage(
                retuned.oof_predictions
            )
        except EvaluationMathError as exc:
            if str(exc).startswith("no valid locked threshold option;") and (
                "INVALID_DEAD_SAFE_NO_CROWNS" in str(exc)
            ):
                passed = False
                ablation_documents[model_id] = {
                    "status": "INVALID_CONSTANT_OR_DEAD_SAFE_ABLATION",
                    "reason": str(exc),
                    "necessity_requirement_passed": False,
                    "locked_valid_frozen_and_retuned_requirement_failed": True,
                }
            else:
                return _empty_documents(
                    status=INVALID_ARTIFACT,
                    reason=f"ablation {model_id} evaluation failed closed: {exc}",
                    join_audit=join_audit,
                    duplicate_document=duplicate.to_dict(),
                    failure_rows=failure_rows,
                    events=events,
                )
        comparison_passes.append(passed)

    for model_id in CONSTANT_MODEL_IDS:
        aggregate, by_lineage, document = _constant_evaluation(
            joined=joined,
            effective_indices=effective_indices,
            model_id=model_id,
        )
        strict = primary_strictly_better(primary.oof_metrics, aggregate)
        document["primary_strictly_better"] = strict
        document["requirement_passed"] = strict
        constant_documents[model_id] = document
        comparator_lineage_metrics[model_id] = by_lineage
        comparison_passes.append(strict)

    comparison_requirement_passed = all(comparison_passes)
    comparison_document = {
        "version": VERSION,
        "comparison_state": "EXACT_ZERO_TOLERANCE_COMPARISONS_COMPLETE",
        "primary_comparison_tuple": list(primary.oof_metrics.comparison_tuple()),
        "simple_baselines": baseline_documents,
        "ablations": ablation_documents,
        "constant_controls": constant_documents,
        "comparison_requirement_passed": comparison_requirement_passed,
        "equivalence_tolerance": 0.0,
    }

    primary_metric_values = _metric_values(primary_by_lineage)
    primary_intervals = {
        field: {
            "values_by_lineage": values,
            "interval": cluster_percentile_interval(values).to_dict(
                include_replicates=False
            ),
        }
        for field, values in primary_metric_values.items()
    }
    paired_intervals: dict[str, object] = {}
    for comparator_id, by_lineage in comparator_lineage_metrics.items():
        comparator_intervals: dict[str, object] = {}
        for field in primary_metric_values:
            values: dict[str, float] = {}
            undefined = False
            for lineage, metric in by_lineage.items():
                value = getattr(metric, field)
                if value is None:
                    undefined = True
                    break
                values[lineage] = float(value)
            comparator_intervals[field] = (
                {
                    "status": "UNDEFINED_COMPARATOR_DENOMINATOR",
                    "interval": None,
                }
                if undefined
                else paired_cluster_difference_interval(
                    primary_metric_values[field], values
                ).to_dict(include_replicates=False)
            )
        paired_intervals[comparator_id] = comparator_intervals
    uncertainty_document = {
        "version": VERSION,
        "uncertainty_state": "DETERMINISTIC_LINEAGE_CLUSTER_BOOTSTRAP_COMPLETE",
        "sampling_unit": "generator_lineage_id",
        "row_resampling_used": False,
        "seed": BOOTSTRAP_SEED,
        "resamples": BOOTSTRAP_RESAMPLES,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "lower_index": BOOTSTRAP_LOWER_INDEX,
        "upper_index": BOOTSTRAP_UPPER_INDEX,
        "lineage_ids": list(sorted(primary_by_lineage)),
        "draw_matrix": [list(row) for row in cluster_draw_matrix(len(primary_by_lineage))],
        "primary_metric_intervals": primary_intervals,
        "paired_primary_minus_comparator_intervals": paired_intervals,
    }

    if not failure_passed:
        decision = HOLD_FAILURE
        reasons = ["one or more locked evaluator failure-capability fixtures failed"]
    elif len(primary_by_lineage) < 4:
        decision = HOLD_INSUFFICIENT
        reasons = ["fewer than four generator lineages remained after duplicate audit"]
    elif not comparison_requirement_passed:
        decision = HOLD_BASELINE
        reasons = [
            "the primary was equivalent to or dominated by a locked baseline or ablation"
        ]
    else:
        decision = READY
        reasons = [
            "development-only selection, failure capability, and strict comparison requirements passed"
        ]
    result_document = {
        "version": VERSION,
        "evaluator_id": EVALUATOR_ID,
        "decision_status": decision,
        "progression_authorized": decision == READY,
        "next_authorized_scope": (
            "v1.8.3 holdout contract construction only" if decision == READY else None
        ),
        "selected_option_id": primary.selected_option_id,
        "selected_threshold": selected_option.to_dict(),
        "scientific_authority": "v1.7.11-alpha 0 / HOLD",
        "development_only": True,
        "controlled_synthetic_generators_are_class_conditioned": True,
        "independent_empirical_data_claimed": False,
        "holdout_material_accessed": False,
        "raw_case_count": duplicate.raw_case_count,
        "effective_case_count": duplicate.effective_case_count,
        "generator_lineage_count": len(primary_by_lineage),
        "duplicate_status": duplicate.status,
        "primary_status": primary.status,
        "failure_capability_passed": failure_passed,
        "comparison_requirement_passed": comparison_requirement_passed,
        "reasons": reasons,
        "event_order": list(events),
    }
    return {
        "join_audit": dict(join_audit),
        "duplicate_audit": duplicate.to_dict(),
        "selection": selection_document,
        "comparisons": comparison_document,
        "uncertainty": uncertainty_document,
        "failure_capability": {
            "version": VERSION,
            "failure_capability_state": "EXECUTED",
            "passed": failure_passed,
            "fixtures": list(failure_rows),
        },
        "result": result_document,
    }


def _safe_write_bundle(
    out: Path,
    *,
    documents: Mapping[str, Mapping[str, object]],
    input_hashes: Mapping[str, object],
    evaluator_package: Mapping[str, object],
    events: Sequence[str],
) -> dict[str, Path]:
    if dict(evaluator_package) != _evaluator_package():
        raise DevelopmentEvaluationError("evaluator package changed during evaluation")
    output = out.absolute()
    parent = output.parent
    if not parent.is_dir() or _is_link_or_junction(parent):
        raise DevelopmentEvaluationError("evaluation output parent is missing or unsafe")
    if output.exists():
        raise DevelopmentEvaluationError(f"refusing existing evaluation output: {output}")
    detail_keys = tuple(
        key for key in EVALUATION_FILES if key not in {"manifest", "receipt"}
    )
    data = {key: _json_bytes(dict(documents[key])) for key in detail_keys}
    manifest = {
        "version": VERSION,
        "evaluator_id": EVALUATOR_ID,
        "manifest_state": "V1_8_2_DEVELOPMENT_EVALUATION_COMPLETE",
        "decision_status": documents["result"]["decision_status"],
        "input_hashes": dict(input_hashes),
        "evaluator_package": dict(evaluator_package),
        "artifacts": {
            key: {
                "filename": EVALUATION_FILES[key],
                "sha256": _sha256(data[key]),
                "size_bytes": len(data[key]),
            }
            for key in detail_keys
        },
        "event_order": list(events),
        "semantic_vault_read_after_prelabel_verification": True,
        "holdout_material_accessed": False,
        "external_timestamp_proof": False,
    }
    data["manifest"] = _json_bytes(manifest)
    receipt = {
        "version": VERSION,
        "receipt_state": "CALLER_RETAIN_V1_8_2_DEVELOPMENT_EVALUATION",
        "decision_status": documents["result"]["decision_status"],
        "manifest_sha256": _sha256(data["manifest"]),
        "result_sha256": _sha256(data["result"]),
        "selection_sha256": _sha256(data["selection"]),
        "caller_retained_split_receipt_sha256": input_hashes["split_receipt"],
        "caller_retained_prelabel_receipt_sha256": input_hashes["prelabel_receipt"],
        "external_timestamp_proof": False,
    }
    data["receipt"] = _json_bytes(receipt)
    paths = {key: output / filename for key, filename in EVALUATION_FILES.items()}
    output.mkdir(exist_ok=False)
    output_stat = os.stat(output, follow_symlinks=False)
    output_identity = (output_stat.st_dev, output_stat.st_ino)
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for key in EVALUATION_FILES:
            current_output = os.stat(output, follow_symlinks=False)
            if (
                _is_link_or_junction(output)
                or (current_output.st_dev, current_output.st_ino) != output_identity
            ):
                raise DevelopmentEvaluationError("evaluation output directory ownership changed")
            with paths[key].open("xb") as handle:
                opened = os.fstat(handle.fileno())
                identity = (opened.st_dev, opened.st_ino)
                handle.write(data[key])
                handle.flush()
                os.fsync(handle.fileno())
            current_file = os.stat(paths[key], follow_symlinks=False)
            if (
                _is_link_or_junction(paths[key])
                or (current_file.st_dev, current_file.st_ino) != identity
            ):
                raise DevelopmentEvaluationError(f"evaluation {key} ownership changed")
            created.append((paths[key], identity))
        if {path.name for path in output.iterdir()} != set(EVALUATION_FILES.values()):
            raise DevelopmentEvaluationError("evaluation artifact set changed while writing")
        for key, path in paths.items():
            if _read_regular(path, field=f"written evaluation {key}") != data[key]:
                raise DevelopmentEvaluationError(f"written evaluation {key} changed")
    except Exception:
        for path, identity in reversed(created):
            try:
                current = os.stat(path, follow_symlinks=False)
                if (
                    path.is_file()
                    and not _is_link_or_junction(path)
                    and (current.st_dev, current.st_ino) == identity
                ):
                    path.unlink()
            except (FileNotFoundError, OSError):
                pass
        try:
            current_output = os.stat(output, follow_symlinks=False)
            if (
                not _is_link_or_junction(output)
                and (current_output.st_dev, current_output.st_ino) == output_identity
            ):
                output.rmdir()
        except (FileNotFoundError, OSError):
            pass
        raise
    return paths


def _preflight_output_path(out: str | Path) -> Path:
    output = Path(out).absolute()
    if output.exists():
        raise DevelopmentEvaluationError(f"refusing existing evaluation output: {output}")
    parent = output.parent
    if not parent.is_dir() or _is_link_or_junction(parent):
        raise DevelopmentEvaluationError("evaluation output parent is missing or unsafe")
    for ancestor in (parent, *parent.parents):
        if ancestor.exists() and _is_link_or_junction(ancestor):
            raise DevelopmentEvaluationError("evaluation output has a linked ancestor")
    return output


def evaluate_development(
    out: str | Path,
    *,
    observable_source_path: str | Path,
    recipe_path: str | Path,
    raw_manifest_path: str | Path,
    extraction_manifest_path: str | Path,
    extraction_source_manifest_path: str | Path,
    development_fingerprint_path: str | Path,
    split_receipt_path: str | Path,
    split_manifest_path: str | Path,
    join_keys_path: str | Path,
    label_vault_path: str | Path,
    group_vault_path: str | Path,
    prelabel_dir: str | Path,
    expected_split_receipt_sha256: str,
    expected_recipe_sha256: str,
    expected_raw_manifest_sha256: str,
    expected_extraction_manifest_sha256: str,
    expected_extraction_source_manifest_sha256: str,
    expected_development_fingerprint_sha256: str,
    expected_observable_source_sha256: str,
    expected_prelabel_receipt_sha256: str,
    expected_v1_8_1_package_contract_sha256: str,
) -> dict[str, Path]:
    """Verify the frozen chain, then perform the first development label join.

    This module deliberately has no import path to generators, extractors,
    scorers, predictor packages, or pre-label freeze code. Frozen scores and
    proposals are verified as retained bytes before semantic vaults are read.
    """

    output = _preflight_output_path(out)
    events: list[str] = ["EVALUATION_STARTED", "OUTPUT_PREFLIGHT_COMPLETE"]
    try:
        authority = _verify_nonsemantic_chain(
            observable_source_path=Path(observable_source_path),
            recipe_path=Path(recipe_path),
            raw_manifest_path=Path(raw_manifest_path),
            extraction_manifest_path=Path(extraction_manifest_path),
            extraction_source_manifest_path=Path(extraction_source_manifest_path),
            development_fingerprint_path=Path(development_fingerprint_path),
            split_receipt_path=Path(split_receipt_path),
            split_manifest_path=Path(split_manifest_path),
            prelabel_dir=Path(prelabel_dir),
            expected_split_receipt_sha256=expected_split_receipt_sha256,
            expected_recipe_sha256=expected_recipe_sha256,
            expected_raw_manifest_sha256=expected_raw_manifest_sha256,
            expected_extraction_manifest_sha256=expected_extraction_manifest_sha256,
            expected_extraction_source_manifest_sha256=(
                expected_extraction_source_manifest_sha256
            ),
            expected_development_fingerprint_sha256=(
                expected_development_fingerprint_sha256
            ),
            expected_observable_source_sha256=expected_observable_source_sha256,
            expected_prelabel_receipt_sha256=expected_prelabel_receipt_sha256,
            expected_v1_8_1_package_contract_sha256=(
                expected_v1_8_1_package_contract_sha256
            ),
            events=events,
        )
    except DevelopmentEvaluationError as exc:
        raise DevelopmentEvaluationError(f"{INVALID_ARTIFACT}: {exc}") from exc

    failure_rows = failure_capability_rows()
    try:
        joined, join_audit = _semantic_join(
            authority=authority,
            join_keys_path=Path(join_keys_path),
            label_vault_path=Path(label_vault_path),
            group_vault_path=Path(group_vault_path),
            recipe_path=Path(recipe_path),
            events=events,
        )
    except _SemanticInvalid as exc:
        join_audit = {
            "version": VERSION,
            "audit_state": "POST_FREEZE_SEMANTIC_JOIN_INVALID",
            "status": exc.status,
            "reason": exc.reason,
            "event_order": list(events),
        }
        documents = _empty_documents(
            status=exc.status,
            reason=exc.reason,
            join_audit=join_audit,
            duplicate_document={
                "version": VERSION,
                "status": "NOT_EXECUTED_INVALID_JOIN",
                "effective_case_count": 0,
            },
            failure_rows=failure_rows,
            events=events,
        )
        return _safe_write_bundle(
            output,
            documents=documents,
            input_hashes=authority["input_hashes"],  # type: ignore[arg-type]
            evaluator_package=authority["evaluator_package"],  # type: ignore[arg-type]
            events=events,
        )
    except DevelopmentEvaluationError as exc:
        raise DevelopmentEvaluationError(f"{INVALID_ARTIFACT}: {exc}") from exc

    duplicate = audit_observable_duplicates(
        {
            "row_index": row["row_index"],
            "generator_lineage_id": row["generator_lineage_id"],
            "evaluation_role": row["evaluation_role"],
            "observable_frames": row["observable_frames"],
        }
        for row in joined
    )
    events.append("DUPLICATE_AUDIT_COMPLETE")
    if duplicate.status != "VALID_DUPLICATE_AUDIT":
        documents = _empty_documents(
            status=duplicate.status,
            reason="observable duplicate audit rejected label aliasing or cross-lineage overlap",
            join_audit=join_audit,
            duplicate_document=duplicate.to_dict(),
            failure_rows=failure_rows,
            events=events,
        )
    else:
        documents = _evaluate_documents(
            joined=joined,
            join_audit=join_audit,
            duplicate=duplicate,
            scores=authority["scores"],  # type: ignore[arg-type]
            events=events,
        )
    events.append("DEVELOPMENT_DECISION_COMPLETE")
    documents["result"]["event_order"] = list(events)
    documents["join_audit"]["event_order"] = list(events)
    return _safe_write_bundle(
        output,
        documents=documents,
        input_hashes=authority["input_hashes"],  # type: ignore[arg-type]
        evaluator_package=authority["evaluator_package"],  # type: ignore[arg-type]
        events=events,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the exact v1.8.2 frozen development chain, then perform "
            "the first label/group join. No holdout path is accepted."
        )
    )
    for name in (
        "out",
        "observable-source",
        "recipe",
        "raw-manifest",
        "extraction-manifest",
        "extraction-source-manifest",
        "development-fingerprint",
        "split-receipt",
        "split-manifest",
        "join-keys",
        "label-vault",
        "group-vault",
        "prelabel-dir",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in (
        "split-receipt-sha256",
        "recipe-sha256",
        "raw-manifest-sha256",
        "extraction-manifest-sha256",
        "extraction-source-manifest-sha256",
        "development-fingerprint-sha256",
        "observable-source-sha256",
        "prelabel-receipt-sha256",
        "v1-8-1-package-contract-sha256",
    ):
        parser.add_argument(f"--{name}", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    paths = evaluate_development(
        args.out,
        observable_source_path=args.observable_source,
        recipe_path=args.recipe,
        raw_manifest_path=args.raw_manifest,
        extraction_manifest_path=args.extraction_manifest,
        extraction_source_manifest_path=args.extraction_source_manifest,
        development_fingerprint_path=args.development_fingerprint,
        split_receipt_path=args.split_receipt,
        split_manifest_path=args.split_manifest,
        join_keys_path=args.join_keys,
        label_vault_path=args.label_vault,
        group_vault_path=args.group_vault,
        prelabel_dir=args.prelabel_dir,
        expected_split_receipt_sha256=args.split_receipt_sha256,
        expected_recipe_sha256=args.recipe_sha256,
        expected_raw_manifest_sha256=args.raw_manifest_sha256,
        expected_extraction_manifest_sha256=args.extraction_manifest_sha256,
        expected_extraction_source_manifest_sha256=(
            args.extraction_source_manifest_sha256
        ),
        expected_development_fingerprint_sha256=args.development_fingerprint_sha256,
        expected_observable_source_sha256=args.observable_source_sha256,
        expected_prelabel_receipt_sha256=args.prelabel_receipt_sha256,
        expected_v1_8_1_package_contract_sha256=(
            args.v1_8_1_package_contract_sha256
        ),
    )
    result = _strict_canonical_document(paths["result"].read_bytes(), source="result")
    print(f"decision_status={result['decision_status']}")
    print(f"selected_option_id={result['selected_option_id']}")
    print(f"evaluation_receipt_sha256={_sha256(paths['receipt'].read_bytes())}")
    return 0


__all__ = [
    "DevelopmentEvaluationError",
    "EVALUATION_FILES",
    "build_parser",
    "evaluate_development",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
