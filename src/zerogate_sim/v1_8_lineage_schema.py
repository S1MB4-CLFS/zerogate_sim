from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence, TypeAlias

from zerogate_sim.v1_8_observable_schema import (
    OBSERVABLE_FIELDS as BASE_OBSERVABLE_FIELDS,
    SCHEMA_ID as BASE_OBSERVABLE_SCHEMA_ID,
    observable_schema_sha256 as base_observable_schema_sha256,
)

VERSION = "v1.8.1-alpha"
SCHEMA_ID = "zerogate-v1.8.1-three-frame-observable-schema-v1"

FRAME_NAMES = ("early", "witness", "late")
OBSERVABLE_FIELDS = tuple(BASE_OBSERVABLE_FIELDS)

LineageFrames: TypeAlias = tuple[
    Mapping[str, float],
    Mapping[str, float],
    Mapping[str, float],
]


class LineageSchemaError(ValueError):
    """Raised when a v1.8.1 observable sequence is not exact and safe."""


def canonical_json(value: object) -> str:
    """Return one deterministic, ASCII-only JSON representation."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LineageSchemaError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(value: object) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def strict_json_loads(text: str, *, source: str) -> object:
    """Parse JSON while rejecting duplicate keys and non-finite constants."""

    def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in pairs:
            if key in out:
                raise LineageSchemaError(f"{source}: duplicate JSON key {key!r}")
            out[key] = value
        return out

    def no_nonfinite(value: str) -> object:
        raise LineageSchemaError(f"{source}: non-finite JSON constant {value!r}")

    try:
        return json.loads(
            text,
            object_pairs_hook=no_duplicate_keys,
            parse_constant=no_nonfinite,
        )
    except LineageSchemaError:
        raise
    except json.JSONDecodeError as exc:
        raise LineageSchemaError(f"{source}: malformed JSON: {exc}") from exc


def write_canonical_json(path: str | Path, value: object) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((canonical_json(value) + "\n").encode("utf-8"))
    return output


def _unit_number(value: object, *, field: str, source: str) -> float:
    # JSON numbers are accepted; bool, strings, Decimal-like objects, and custom
    # numeric coercions fail closed. This prevents a permissive parser from
    # silently changing the typed callback contract.
    if type(value) not in {int, float}:
        raise LineageSchemaError(
            f"{source}: {field!r} must be an actual JSON number, got {type(value).__name__}"
        )
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise LineageSchemaError(
            f"{source}: {field!r} must satisfy 0 <= value <= 1, got {value!r}"
        )
    if number == 0.0:
        number = 0.0
    return number


def validate_observable_frame(
    value: object,
    *,
    source: str = "observable frame",
) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise LineageSchemaError(f"{source}: frame must be a mapping")
    supplied = set(value)
    expected = set(OBSERVABLE_FIELDS)
    missing = sorted(expected - supplied)
    extras = sorted(supplied - expected, key=str)
    if missing or extras:
        raise LineageSchemaError(
            f"{source}: exact seven-field schema required; missing={missing}, extras={extras}"
        )
    return {
        field: _unit_number(value[field], field=field, source=source)
        for field in OBSERVABLE_FIELDS
    }


def validate_lineage_frames(
    value: object,
    *,
    source: str = "lineage observable frames",
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise LineageSchemaError(f"{source}: frames must be an ordered sequence")
    if len(value) != len(FRAME_NAMES):
        raise LineageSchemaError(
            f"{source}: exactly three frames are required in early/witness/late order"
        )
    frames = tuple(
        validate_observable_frame(frame, source=f"{source}.{name}")
        for name, frame in zip(FRAME_NAMES, value, strict=True)
    )
    return frames  # type: ignore[return-value]


def immutable_lineage_frames(
    value: object,
    *,
    source: str = "lineage callback",
) -> LineageFrames:
    """Return the exact callback value: a tuple of three read-only mappings."""

    frames = validate_lineage_frames(value, source=source)
    return tuple(MappingProxyType(dict(frame)) for frame in frames)  # type: ignore[return-value]


def canonical_lineage_row(row_index: int, frames: object) -> dict[str, object]:
    if type(row_index) is not int or row_index < 0:
        raise LineageSchemaError("row_index must be an exact nonnegative integer")
    checked = validate_lineage_frames(frames, source=f"row {row_index}")
    return {
        "observable_frames": [dict(frame) for frame in checked],
        "row_index": row_index,
    }


def read_lineage_inputs_bytes(data: bytes, *, source: str) -> list[dict[str, object]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LineageSchemaError(f"{source}: lineage JSONL is not UTF-8") from exc
    if not text or not text.endswith("\n"):
        raise LineageSchemaError(f"{source}: canonical JSONL must end with newline")
    lines = text.splitlines()
    if any(not line for line in lines):
        raise LineageSchemaError(f"{source}: blank JSONL rows are forbidden")

    out: list[dict[str, object]] = []
    for expected_index, line in enumerate(lines):
        row_source = f"{source}:{expected_index + 1}"
        value = strict_json_loads(line, source=row_source)
        if not isinstance(value, dict) or set(value) != {"observable_frames", "row_index"}:
            raise LineageSchemaError(f"{row_source}: invalid row envelope")
        if type(value["row_index"]) is not int or value["row_index"] != expected_index:
            raise LineageSchemaError(
                f"{row_source}: row_index must be the exact ordered sequence starting at zero"
            )
        canonical_row = canonical_lineage_row(expected_index, value["observable_frames"])
        if line != canonical_json(canonical_row):
            raise LineageSchemaError(f"{row_source}: non-canonical JSONL row")
        out.append(canonical_row)
    if not out:
        raise LineageSchemaError(f"{source}: no lineage rows")
    return out


def read_lineage_inputs(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise LineageSchemaError(f"missing or unsafe lineage input: {source}")
    return read_lineage_inputs_bytes(source.read_bytes(), source=str(source))


def lineage_input_bytes(rows: Iterable[object]) -> bytes:
    canonical_rows = [canonical_lineage_row(index, frames) for index, frames in enumerate(rows)]
    if not canonical_rows:
        raise LineageSchemaError("at least one lineage row is required")
    return "".join(canonical_json(row) + "\n" for row in canonical_rows).encode("utf-8")


def _file_identity(value: os.stat_result) -> tuple[int, int]:
    return (value.st_dev, value.st_ino)


def _remove_owned_file(path: Path, identity: tuple[int, int] | None) -> None:
    """Remove only the regular file created by this call.

    In particular, an `xb` failure means another writer owns the path; with no
    captured identity this helper deliberately does nothing.
    """

    if identity is None:
        return
    try:
        current = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISREG(current.st_mode) and _file_identity(current) == identity:
        try:
            path.unlink()
        except OSError:
            pass


def write_lineage_inputs(path: str | Path, rows: Iterable[object]) -> Path:
    output = Path(path)
    if output.exists():
        raise LineageSchemaError(f"refusing to overwrite lineage input: {output}")
    data = lineage_input_bytes(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    owned_identity: tuple[int, int] | None = None
    try:
        with output.open("xb") as handle:
            owned_identity = _file_identity(os.fstat(handle.fileno()))
            handle.write(data)
        if output.read_bytes() != data:
            raise LineageSchemaError("lineage input changed while being written")
    except Exception:
        _remove_owned_file(output, owned_identity)
        raise
    return output


def lineage_schema_document() -> dict[str, object]:
    return {
        "version": VERSION,
        "schema_id": SCHEMA_ID,
        "base_observable_schema_id": BASE_OBSERVABLE_SCHEMA_ID,
        "base_observable_schema_sha256": base_observable_schema_sha256(),
        "frame_fields_derived_from_base_schema": True,
        "row_envelope": ["observable_frames", "row_index"],
        "row_index_is_transport_only": True,
        "frame_count": 3,
        "frame_order": list(FRAME_NAMES),
        "frame_fields": list(OBSERVABLE_FIELDS),
        "field_type": "actual_json_number_finite_unit_interval",
        "unknown_fields_fail_closed": True,
        "callback_value": "tuple_of_three_read_only_exact_field_mappings",
        "scientific_thresholds_selected": False,
    }


def lineage_schema_sha256() -> str:
    return stable_sha256(lineage_schema_document())
