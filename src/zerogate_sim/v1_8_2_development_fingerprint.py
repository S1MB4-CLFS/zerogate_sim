from __future__ import annotations

from pathlib import Path

from zerogate_sim.v1_8_lineage_schema import read_lineage_inputs_bytes
from zerogate_sim.v1_8_2_numeric_contract import (
    TOTAL_CASES,
    VERSION,
    DevelopmentDataError,
    load_canonical_json,
    sha256_bytes,
    stable_sha256,
    write_canonical_json_exclusive,
)


def build_development_fingerprint(
    *,
    extraction_manifest_path: str | Path,
    observable_input_path: str | Path,
    recipe_path: str | Path,
    raw_manifest_path: str | Path,
    source_manifest_path: str | Path,
    out: str | Path,
    expected_extraction_manifest_sha256: str,
    expected_observable_input_sha256: str,
    expected_recipe_sha256: str,
    expected_raw_manifest_sha256: str,
    expected_source_manifest_sha256: str,
) -> Path:
    extraction_path = Path(extraction_manifest_path)
    observable_path = Path(observable_input_path)
    recipe_source = Path(recipe_path)
    raw_manifest_source = Path(raw_manifest_path)
    source_manifest_source = Path(source_manifest_path)
    extraction_bytes = extraction_path.read_bytes()
    observable_bytes = observable_path.read_bytes()
    recipe_bytes = recipe_source.read_bytes()
    raw_manifest_bytes = raw_manifest_source.read_bytes()
    source_manifest_bytes = source_manifest_source.read_bytes()
    if sha256_bytes(extraction_bytes) != expected_extraction_manifest_sha256:
        raise DevelopmentDataError("extraction manifest SHA-256 mismatch")
    if sha256_bytes(observable_bytes) != expected_observable_input_sha256:
        raise DevelopmentDataError("observable input SHA-256 mismatch")
    if sha256_bytes(recipe_bytes) != expected_recipe_sha256:
        raise DevelopmentDataError("recipe SHA-256 mismatch")
    if sha256_bytes(raw_manifest_bytes) != expected_raw_manifest_sha256:
        raise DevelopmentDataError("raw manifest SHA-256 mismatch")
    if sha256_bytes(source_manifest_bytes) != expected_source_manifest_sha256:
        raise DevelopmentDataError("source manifest SHA-256 mismatch")
    extraction = load_canonical_json(extraction_path)
    raw_manifest = load_canonical_json(raw_manifest_source)
    source_manifest = load_canonical_json(source_manifest_source)
    entries = extraction.get("entries")
    rows = read_lineage_inputs_bytes(observable_bytes, source=str(observable_path))
    raw_entries = raw_manifest.get("entries")
    recipe_rows = recipe_bytes.decode("utf-8").splitlines()
    if (
        not isinstance(entries, list)
        or not isinstance(raw_entries, list)
        or len(entries) != TOTAL_CASES
        or len(raw_entries) != TOTAL_CASES
        or len(recipe_rows) != TOTAL_CASES
        or len(rows) != TOTAL_CASES
    ):
        raise DevelopmentDataError("fingerprint requires exactly 144 extraction and observable rows")
    if (
        source_manifest.get("raw_manifest_sha256") != expected_raw_manifest_sha256
        or source_manifest.get("extraction_manifest_sha256")
        != expected_extraction_manifest_sha256
        or source_manifest.get("observable_input_sha256")
        != expected_observable_input_sha256
    ):
        raise DevelopmentDataError("source manifest does not bind the supplied development artifacts")

    fingerprints: list[dict[str, object]] = []
    by_hash: dict[str, list[tuple[int, int]]] = {}
    for index, (entry, row) in enumerate(zip(entries, rows, strict=True)):
        if not isinstance(entry, dict) or entry.get("row_index") != index:
            raise DevelopmentDataError("extraction entries are not exact ordered rows")
        frame_hashes = entry.get("frames")
        if not isinstance(frame_hashes, dict):
            raise DevelopmentDataError("extraction frame hashes are missing")
        for name, frame in zip(("early", "witness", "late"), row["observable_frames"], strict=True):
            record = frame_hashes.get(name)
            if not isinstance(record, dict) or record.get("observable_sha256") != stable_sha256(frame):
                raise DevelopmentDataError("extraction observable hash mismatch")
        observable_hash = stable_sha256(row["observable_frames"])
        backend = int(entry.get("backend_code", -1))
        fingerprints.append(
            {
                "backend_code": backend,
                "observable_sha256": observable_hash,
                "row_index": index,
                "trace_sha256": entry.get("trace_sha256"),
            }
        )
        by_hash.setdefault(observable_hash, []).append((index, backend))

    duplicate_groups: list[dict[str, object]] = []
    for observable_hash, members in sorted(by_hash.items()):
        backends = sorted({backend for _, backend in members})
        if len(backends) > 1:
            raise DevelopmentDataError("INVALID_GENERATOR_LINEAGE_OVERLAP")
        if len(members) > 1:
            duplicate_groups.append(
                {
                    "backend_code": backends[0],
                    "observable_sha256": observable_hash,
                    "row_indices": [index for index, _ in members],
                }
            )
    document = {
        "version": VERSION,
        "manifest_state": "PRELABEL_DEVELOPMENT_FINGERPRINT_COMPLETE",
        "extraction_manifest_sha256": expected_extraction_manifest_sha256,
        "observable_input_sha256": expected_observable_input_sha256,
        "recipe_sha256": expected_recipe_sha256,
        "raw_manifest_sha256": expected_raw_manifest_sha256,
        "source_manifest_sha256": expected_source_manifest_sha256,
        "raw_recipe_count": len(recipe_rows),
        "raw_trace_count": len(raw_entries),
        "raw_observable_count": len(rows),
        "effective_observable_count": len(by_hash),
        "row_count": TOTAL_CASES,
        "unique_observable_count": len(by_hash),
        "within_backend_duplicate_groups": duplicate_groups,
        "cross_backend_duplicate_count": 0,
        "observable_identity": (
            "sha256_of_canonical_three_frame_observables_excluding_ids_labels_and_groups"
        ),
        "fingerprints": fingerprints,
        "labels_or_groups_read": False,
    }
    output = Path(out)
    if output.exists():
        raise DevelopmentDataError(f"refusing to overwrite fingerprint: {output}")
    return write_canonical_json_exclusive(output, document)
