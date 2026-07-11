from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Mapping

from zerogate_sim.v1_8_lineage_schema import canonical_json, strict_json_loads

VERSION = "v1.8.2-alpha"
GENERATOR_CONTRACT_ID = "zerogate-v1.8.2-development-generators-v1"
ROOT_SEED = 1_812_001
SAMPLE_COUNT = 1001
TRACE_SCALE = 1_000_000_000
BACKEND_CODES = (0, 1, 2, 3)
BACKEND_LINEAGES = (
    "ar_recovery_v1",
    "impulse_response_v1",
    "coupled_oscillator_v1",
    "piecewise_hysteresis_v1",
)
REGIMES_PER_BACKEND = 12
REPLICATES_PER_REGIME = 3
CASES_PER_BACKEND = REGIMES_PER_BACKEND * REPLICATES_PER_REGIME
TOTAL_CASES = len(BACKEND_CODES) * CASES_PER_BACKEND
FRAME_RANGES = {
    "early": (100, 300),
    "witness": (450, 650),
    "late": (800, 1000),
}
TRACE_HEADER = (
    "sample_index",
    "target_q",
    "peer_a_q",
    "peer_b_q",
    "peer_c_q",
)
PUBLIC_RECIPE_FIELDS = (
    "backend_code",
    "backend_parameters",
    "echo_mix",
    "envelope",
    "frequency",
    "noise_scale",
    "peer_coherence",
    "phase",
    "regime_code",
    "relation_mix",
    "replicate_code",
    "row_index",
    "seed_u64",
)


class DevelopmentDataError(ValueError):
    """Raised when the v1.8.2 development-data boundary fails closed."""


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


def write_exclusive(path: str | Path, data: bytes) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    identity: tuple[int, int] | None = None
    try:
        with output.open("xb") as handle:
            info = os.fstat(handle.fileno())
            identity = (info.st_dev, info.st_ino)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if output.read_bytes() != data:
            raise DevelopmentDataError(f"artifact changed while being written: {output}")
    except Exception:
        if identity is not None:
            try:
                current = output.stat(follow_symlinks=False)
                if not output.is_symlink() and (current.st_dev, current.st_ino) == identity:
                    output.unlink()
            except OSError:
                pass
        raise
    return output


def write_canonical_json_exclusive(path: str | Path, value: object) -> Path:
    return write_exclusive(path, (canonical_json(value) + "\n").encode("utf-8"))


def load_canonical_json(path: str | Path) -> dict[str, object]:
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise DevelopmentDataError(f"missing or unsafe JSON artifact: {source}")
    data = source.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DevelopmentDataError(f"JSON artifact is not UTF-8: {source}") from exc
    value = strict_json_loads(text, source=str(source))
    if not isinstance(value, dict) or text != canonical_json(value) + "\n":
        raise DevelopmentDataError(f"JSON artifact is not one canonical object: {source}")
    return value


def generator_contract_document() -> dict[str, object]:
    return {
        "version": VERSION,
        "contract_id": GENERATOR_CONTRACT_ID,
        "root_seed": ROOT_SEED,
        "sample_count": SAMPLE_COUNT,
        "trace_scale": TRACE_SCALE,
        "trace_header": list(TRACE_HEADER),
        "backend_codes": list(BACKEND_CODES),
        "backend_lineages": list(BACKEND_LINEAGES),
        "regimes_per_backend": REGIMES_PER_BACKEND,
        "replicates_per_regime": REPLICATES_PER_REGIME,
        "cases_per_backend": CASES_PER_BACKEND,
        "total_cases": TOTAL_CASES,
        "frame_ranges_inclusive": {
            name: [start, end] for name, (start, end) in FRAME_RANGES.items()
        },
        "public_recipe_fields": list(PUBLIC_RECIPE_FIELDS),
        "public_recipe_policy": (
            "row_index_and_numeric_regime_only_no_roles_ids_or_semantic_archetype_names"
        ),
        "raw_generation_policy": "numeric_recipes_only_never_reads_sealed_vaults",
        "extractor_policy": "numeric_raw_traces_only_label_free",
        "quantization": "round_binary64_to_signed_integer_at_trace_scale_after_each_state_update",
    }


def generator_contract_sha256() -> str:
    return stable_sha256(generator_contract_document())


def validate_recipe(value: object, *, source: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != set(PUBLIC_RECIPE_FIELDS):
        raise DevelopmentDataError(f"{source}: exact public numeric recipe fields required")
    ints = ("backend_code", "regime_code", "replicate_code", "row_index", "seed_u64")
    for field in ints:
        if type(value[field]) is not int or int(value[field]) < 0:
            raise DevelopmentDataError(f"{source}: {field} must be a nonnegative integer")
    if int(value["backend_code"]) not in BACKEND_CODES:
        raise DevelopmentDataError(f"{source}: unsupported backend_code")
    if int(value["regime_code"]) >= REGIMES_PER_BACKEND:
        raise DevelopmentDataError(f"{source}: unsupported regime_code")
    if int(value["replicate_code"]) >= REPLICATES_PER_REGIME:
        raise DevelopmentDataError(f"{source}: unsupported replicate_code")
    envelope = value["envelope"]
    params = value["backend_parameters"]
    if not isinstance(envelope, list) or len(envelope) != 3:
        raise DevelopmentDataError(f"{source}: envelope must contain three numbers")
    if not isinstance(params, list) or not params:
        raise DevelopmentDataError(f"{source}: backend_parameters must be a nonempty list")
    for field in ("envelope", "backend_parameters"):
        for number in value[field]:
            if type(number) not in {int, float}:
                raise DevelopmentDataError(f"{source}: {field} values must be numeric")
    for field in ("echo_mix", "frequency", "noise_scale", "peer_coherence", "phase", "relation_mix"):
        if type(value[field]) not in {int, float}:
            raise DevelopmentDataError(f"{source}: {field} must be numeric")
    if float(value["relation_mix"]) + float(value["echo_mix"]) > 0.85:
        raise DevelopmentDataError(f"{source}: relation and echo mix exceed 0.85")
    return dict(value)
