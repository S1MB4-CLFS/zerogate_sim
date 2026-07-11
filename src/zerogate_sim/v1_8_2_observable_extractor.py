from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import median
from typing import Sequence

from zerogate_sim.v1_8_lineage_schema import OBSERVABLE_FIELDS, write_lineage_inputs
from zerogate_sim.v1_8_2_numeric_contract import (
    FRAME_RANGES,
    SAMPLE_COUNT,
    TRACE_HEADER,
    TRACE_SCALE,
    TOTAL_CASES,
    VERSION,
    DevelopmentDataError,
    generator_contract_sha256,
    load_canonical_json,
    sha256_bytes,
    stable_sha256,
    write_canonical_json_exclusive,
)

EPS = 1e-12
SOURCE_BINDING_FILES = (
    "src/zerogate_sim/v1_8_2_numeric_contract.py",
    "src/zerogate_sim/v1_8_2_development_split.py",
    "src/zerogate_sim/v1_8_2_raw_generators.py",
    "src/zerogate_sim/v1_8_2_observable_extractor.py",
    "contracts/v1_8_2_development_generator.json",
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _rms(values: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else 0.0


def _correlation(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    da = [value - ma for value in a]
    db = [value - mb for value in b]
    denominator = math.sqrt(sum(value * value for value in da) * sum(value * value for value in db))
    return sum(x * y for x, y in zip(da, db, strict=True)) / denominator if denominator > EPS else 0.0


def _crossings(values: Sequence[float]) -> int:
    return sum(1 for a, b in zip(values[:-1], values[1:]) if (a < 0.0 <= b) or (a >= 0.0 > b))


def _persistence(values: Sequence[float]) -> float:
    third = max(1, len(values) // 3)
    early = _rms(values[:third])
    late = _rms(values[-third:])
    return _clamp01(1.0 - abs(early - late) / (early + late + EPS))


def _lag_memory(values: Sequence[float]) -> float:
    centered = [value - sum(values) / len(values) for value in values]
    scores: list[float] = []
    for lag in range(12, min(51, len(values) // 2)):
        score = _correlation(centered[:-lag], centered[lag:])
        if math.isfinite(score):
            scores.append(max(0.0, score))
    return max(scores, default=0.0)


def _boundedness(values: Sequence[float]) -> float:
    ordered = sorted(abs(value) for value in values)
    if not ordered:
        return 0.0
    q50 = ordered[int(0.50 * (len(ordered) - 1))] + EPS
    q95 = ordered[int(0.95 * (len(ordered) - 1))]
    return _clamp01(1.0 - max(0.0, (q95 / q50 - 4.0) / 8.0))


def _frame_observables(channels: Sequence[Sequence[float]]) -> dict[str, float]:
    target, peer_a, peer_b, peer_c = channels
    rms = _rms(target)
    crossings = _crossings(target)
    strength = _clamp01(rms / 0.65)
    distinction = _clamp01((rms - 0.08) / (0.55 - 0.08))
    positive = sum(max(value, 0.0) for value in target)
    negative = sum(max(-value, 0.0) for value in target)
    balance = 1.0 - abs(positive - negative) / (positive + negative + EPS)
    crossing_score = min(1.0, crossings / 8.0)
    polarity = _clamp01(0.70 * balance + 0.30 * crossing_score)
    relation = _clamp01(
        (max(abs(_correlation(target, peer)) for peer in (peer_a, peer_b, peer_c)) - 0.15)
        / 0.75
    )
    persistence = _persistence(target)
    memory = _lag_memory(target)
    return_frequency = min(1.0, crossings / 6.0)
    max_jump = max((abs(b - a) for a, b in zip(target[:-1], target[1:])), default=0.0)
    continuity = _clamp01((1.50 - max_jump / (rms + EPS)) / 1.15)
    return_observed = _clamp01(
        max(0.0, return_frequency * memory * continuity * persistence) ** 0.25
    )
    field = [(a + b + c) / 3.0 for a, b, c in zip(peer_a, peer_b, peer_c, strict=True)]
    target_mean = sum(target) / len(target)
    field_mean = sum(field) / len(field)
    target_centered = [value - target_mean for value in target]
    field_centered = [value - field_mean for value in field]
    denominator = sum(value * value for value in field_centered)
    beta = sum(x * y for x, y in zip(target_centered, field_centered, strict=True)) / (denominator + EPS)
    residual = [x - beta * y for x, y in zip(target_centered, field_centered, strict=True)]
    explained = _clamp01(1.0 - _rms(residual) / (_rms(target_centered) + EPS))
    echo = _clamp01(abs(_correlation(target, field)) * explained)
    stability = _clamp01(0.40 * persistence + 0.30 * _boundedness(target) + 0.30 * memory)
    values = {
        "strength": strength,
        "distinction": distinction,
        "polarity": polarity,
        "relation": relation,
        "return_observed": return_observed,
        "echo_mimic_score": echo,
        "observed_stability_score": stability,
    }
    if tuple(values) != OBSERVABLE_FIELDS or any(not math.isfinite(value) for value in values.values()):
        raise DevelopmentDataError("extractor produced a malformed observable frame")
    return values


def extract_case_frames(
    samples: Sequence[Sequence[int]],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    if len(samples) != SAMPLE_COUNT or any(len(row) != 4 for row in samples):
        raise DevelopmentDataError("extractor requires exactly 1001 four-channel samples")
    output: list[dict[str, float]] = []
    for start, end in FRAME_RANGES.values():
        selected = samples[start : end + 1]
        channels = [
            [float(row[channel]) / TRACE_SCALE for row in selected]
            for channel in range(4)
        ]
        output.append(_frame_observables(channels))
    return tuple(output)  # type: ignore[return-value]


def _read_trace(path: Path) -> tuple[tuple[int, int, int, int], ...]:
    if not path.is_file() or path.is_symlink():
        raise DevelopmentDataError(f"missing or unsafe trace: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise DevelopmentDataError("empty trace") from exc
        if header != list(TRACE_HEADER):
            raise DevelopmentDataError("trace header is not exact")
        rows: list[tuple[int, int, int, int]] = []
        for expected_index, values in enumerate(reader):
            if len(values) != 5 or values[0] != str(expected_index):
                raise DevelopmentDataError("trace indices or row widths are invalid")
            try:
                row = tuple(int(value) for value in values[1:])
            except ValueError as exc:
                raise DevelopmentDataError("trace contains a non-integer channel") from exc
            rows.append(row)  # type: ignore[arg-type]
    if len(rows) != SAMPLE_COUNT:
        raise DevelopmentDataError("trace does not contain exactly 1001 samples")
    return tuple(rows)


def _bound_source_files() -> list[dict[str, object]]:
    repo_root = Path(__file__).resolve().parents[2]
    records: list[dict[str, object]] = []
    for relative in SOURCE_BINDING_FILES:
        source = repo_root / relative
        if not source.is_file() or source.is_symlink():
            raise DevelopmentDataError(f"missing or unsafe bound source file: {relative}")
        data = source.read_bytes()
        records.append(
            {
                "relative_path": relative,
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            }
        )
    return records


def extract_development_observables(
    raw_manifest_path: str | Path,
    out: str | Path,
    *,
    expected_raw_manifest_sha256: str,
) -> dict[str, Path]:
    raw_manifest_source = Path(raw_manifest_path)
    raw_manifest_bytes = raw_manifest_source.read_bytes()
    if sha256_bytes(raw_manifest_bytes) != expected_raw_manifest_sha256:
        raise DevelopmentDataError("raw manifest SHA-256 mismatch")
    raw_manifest = load_canonical_json(raw_manifest_source)
    entries = raw_manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != TOTAL_CASES:
        raise DevelopmentDataError("raw manifest must contain exactly 144 entries")
    raw_root = raw_manifest_source.parent.resolve(strict=True)
    output_dir = Path(out)
    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink() or any(output_dir.iterdir())):
        raise DevelopmentDataError("extractor output must be an empty safe directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    observable_rows: list[object] = []
    extraction_entries: list[dict[str, object]] = []
    for expected_index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("row_index") != expected_index:
            raise DevelopmentDataError("raw manifest entries are not exact ordered rows")
        relative = Path(str(entry.get("trace_relative_path", "")))
        trace_path = (raw_manifest_source.parent / relative).resolve(strict=True)
        try:
            trace_path.relative_to(raw_root)
        except ValueError as exc:
            raise DevelopmentDataError("raw trace escapes manifest root") from exc
        if trace_path.is_symlink() or sha256_bytes(trace_path.read_bytes()) != entry.get("trace_sha256"):
            raise DevelopmentDataError("raw trace hash or path is invalid")
        samples = _read_trace(trace_path)
        frames = extract_case_frames(samples)
        frame_records: dict[str, object] = {}
        for (name, (start, end)), frame in zip(FRAME_RANGES.items(), frames, strict=True):
            raw_slice = [list(row) for row in samples[start : end + 1]]
            frame_records[name] = {
                "end_index_inclusive": end,
                "observable_sha256": stable_sha256(frame),
                "raw_slice_sha256": stable_sha256(raw_slice),
                "start_index": start,
            }
        observable_rows.append(frames)
        extraction_entries.append(
            {
                "backend_code": int(entry["backend_code"]),
                "frames": frame_records,
                "row_index": expected_index,
                "trace_sha256": entry["trace_sha256"],
            }
        )
    observable_path = output_dir / "predictor" / "v1_8_2_observable_inputs.jsonl"
    write_lineage_inputs(observable_path, observable_rows)
    extraction_manifest = {
        "version": VERSION,
        "manifest_state": "LABEL_FREE_OBSERVABLE_EXTRACTION_COMPLETE",
        "generator_contract_sha256": generator_contract_sha256(),
        "raw_manifest_sha256": expected_raw_manifest_sha256,
        "observable_input_sha256": sha256_bytes(observable_path.read_bytes()),
        "row_count": TOTAL_CASES,
        "frame_ranges_inclusive": {
            name: [start, end] for name, (start, end) in FRAME_RANGES.items()
        },
        "entries": extraction_entries,
        "generator_source_is_class_conditioned": True,
        "extractor_received_or_read_labels_ids_groups": False,
        "extractor_input_is_numeric_raw_trace_only": True,
    }
    extraction_path = output_dir / "observable_extraction_manifest.json"
    write_canonical_json_exclusive(extraction_path, extraction_manifest)
    source_manifest = {
        "version": VERSION,
        "manifest_state": "PRELABEL_DEVELOPMENT_SOURCE",
        "raw_manifest_sha256": expected_raw_manifest_sha256,
        "extraction_manifest_sha256": sha256_bytes(extraction_path.read_bytes()),
        "observable_input_sha256": sha256_bytes(observable_path.read_bytes()),
        "bound_source_files": _bound_source_files(),
        "bound_artifacts": [
            {
                "artifact": "raw_manifest",
                "sha256": expected_raw_manifest_sha256,
                "size_bytes": len(raw_manifest_bytes),
            },
            {
                "artifact": "extraction_manifest",
                "sha256": sha256_bytes(extraction_path.read_bytes()),
                "size_bytes": extraction_path.stat().st_size,
            },
            {
                "artifact": "observable_inputs",
                "sha256": sha256_bytes(observable_path.read_bytes()),
                "size_bytes": observable_path.stat().st_size,
            },
        ],
        "row_count": TOTAL_CASES,
        "generator_construction": "class_conditioned_controlled_synthetic",
        "observable_extraction": "label_free_numeric_trace_only",
        "sealed_label_or_group_vault_accessed": False,
        "declarations_are_hash_bound_not_external_history_proof": True,
    }
    source_path = output_dir / "prelabel_source_manifest.json"
    write_canonical_json_exclusive(source_path, source_manifest)
    return {
        "observable_inputs": observable_path,
        "extraction_manifest": extraction_path,
        "source_manifest": source_path,
    }
