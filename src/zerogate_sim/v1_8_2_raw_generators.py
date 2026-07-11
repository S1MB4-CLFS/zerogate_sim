from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path
from typing import Callable, Mapping

from zerogate_sim.v1_8_2_numeric_contract import (
    SAMPLE_COUNT,
    TRACE_HEADER,
    TRACE_SCALE,
    TOTAL_CASES,
    VERSION,
    DevelopmentDataError,
    canonical_json,
    generator_contract_sha256,
    sha256_bytes,
    strict_json_loads,
    validate_recipe,
    write_canonical_json_exclusive,
    write_exclusive,
)


def _u01(seed: int, stream: str, index: int) -> float:
    digest = hashlib.sha256(f"{seed}:{stream}:{index}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def _noise(seed: int, stream: str, index: int) -> float:
    return sum(_u01(seed, f"{stream}:{slot}", index) for slot in range(12)) - 6.0


def _q(value: float) -> float:
    bounded = max(-2.0, min(2.0, value))
    return round(bounded * TRACE_SCALE) / TRACE_SCALE


def _smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _envelope(index: int, values: list[float]) -> float:
    early, witness, late = values
    t = index / 1000.0
    if t < 0.10:
        return early * _smoothstep(t / 0.10)
    if t <= 0.30:
        return early
    if t < 0.45:
        mix = _smoothstep((t - 0.30) / 0.15)
        return early + mix * (witness - early)
    if t <= 0.65:
        return witness
    if t < 0.80:
        mix = _smoothstep((t - 0.65) / 0.15)
        return witness + mix * (late - witness)
    return late


def _ar_recovery(recipe: Mapping[str, object]) -> list[float]:
    rho = float(recipe["backend_parameters"][0])
    frequency = float(recipe["frequency"])
    phase = float(recipe["phase"])
    sigma = float(recipe["noise_scale"])
    seed = int(recipe["seed_u64"])
    envelope = [float(value) for value in recipe["envelope"]]
    state = 0.0
    out: list[float] = []
    for index in range(SAMPLE_COUNT):
        t = index / 1000.0
        drive = _envelope(index, envelope) * (
            math.sin(2.0 * math.pi * frequency * t + phase)
            + 0.35 * math.sin(2.0 * math.pi * 1.7 * frequency * t + 0.4 * phase)
        )
        state = _q(rho * state + (1.0 - rho) * drive + sigma * _noise(seed, "ar", index))
        out.append(state)
    return out


def _impulse_response(recipe: Mapping[str, object]) -> list[float]:
    decay = float(recipe["backend_parameters"][0])
    frequency = float(recipe["frequency"])
    phase = float(recipe["phase"])
    sigma = float(recipe["noise_scale"])
    seed = int(recipe["seed_u64"])
    envelope = [float(value) for value in recipe["envelope"]]
    omega = 2.0 * math.pi * frequency / 1000.0
    coefficient = 2.0 * decay * math.cos(omega)
    previous = 0.0
    before_previous = 0.0
    period = max(12, int(round(1000.0 / (2.0 * frequency))))
    out: list[float] = []
    for index in range(SAMPLE_COUNT):
        impulse = 0.0
        if index % period == 0:
            impulse = _envelope(index, envelope) * (1.0 if (index // period) % 2 == 0 else -1.0)
        value = _q(
            coefficient * previous
            - decay * decay * before_previous
            + 0.35 * impulse
            + sigma * _noise(seed, "impulse", index)
        )
        out.append(value)
        before_previous, previous = previous, value
    return out


def _coupled_oscillator(recipe: Mapping[str, object]) -> list[float]:
    coupling = float(recipe["backend_parameters"][0])
    frequency = float(recipe["frequency"])
    phase = float(recipe["phase"])
    sigma = float(recipe["noise_scale"])
    seed = int(recipe["seed_u64"])
    envelope = [float(value) for value in recipe["envelope"]]
    theta = phase
    peer_theta = phase + 0.37
    out: list[float] = []
    for index in range(SAMPLE_COUNT):
        theta = round((
            theta
            + (2.0 * math.pi * frequency + coupling * math.sin(peer_theta - theta)) / 1000.0
            + 0.02 * sigma * _noise(seed, "coupled", index)
        ) % (2.0 * math.pi) * TRACE_SCALE) / TRACE_SCALE
        peer_theta = (
            peer_theta + 2.0 * math.pi * (frequency * 0.97) / 1000.0
        ) % (2.0 * math.pi)
        out.append(_q(_envelope(index, envelope) * math.sin(theta)))
    return out


def _piecewise_hysteresis(recipe: Mapping[str, object]) -> list[float]:
    threshold = float(recipe["backend_parameters"][0])
    tau = float(recipe["backend_parameters"][1])
    frequency = float(recipe["frequency"])
    phase = float(recipe["phase"])
    sigma = float(recipe["noise_scale"])
    seed = int(recipe["seed_u64"])
    envelope = [float(value) for value in recipe["envelope"]]
    discrete_state = -1.0
    relaxed = -1.0
    out: list[float] = []
    for index in range(SAMPLE_COUNT):
        t = index / 1000.0
        driver = math.sin(2.0 * math.pi * frequency * t + phase)
        if driver >= threshold:
            discrete_state = 1.0
        elif driver <= -threshold:
            discrete_state = -1.0
        relaxed = _q(relaxed + (0.001 / tau) * (discrete_state - relaxed))
        auto = _envelope(index, envelope) * (0.65 * relaxed + 0.35 * driver)
        out.append(_q(auto + sigma * _noise(seed, "hysteresis", index)))
    return out


BACKEND_GENERATORS: dict[int, Callable[[Mapping[str, object]], list[float]]] = {
    0: _ar_recovery,
    1: _impulse_response,
    2: _coupled_oscillator,
    3: _piecewise_hysteresis,
}


def generate_case(recipe: Mapping[str, object]) -> tuple[tuple[int, int, int, int], ...]:
    checked = validate_recipe(recipe, source="raw generator recipe")
    backend = int(checked["backend_code"])
    auto = BACKEND_GENERATORS[backend](checked)
    frequency = float(checked["frequency"])
    phase = float(checked["phase"])
    seed = int(checked["seed_u64"])
    relation_mix = float(checked["relation_mix"])
    echo_mix = float(checked["echo_mix"])
    coherence = float(checked["peer_coherence"])
    sigma = float(checked["noise_scale"])
    rows: list[tuple[int, int, int, int]] = []
    for index, autonomous in enumerate(auto):
        t = index / 1000.0
        common = math.sin(2.0 * math.pi * frequency * t + phase + 0.2)
        independent_b = math.sin(2.0 * math.pi * 0.91 * frequency * t + phase + 1.3)
        independent_c = math.sin(2.0 * math.pi * 1.11 * frequency * t + phase + 2.1)
        peer_a = _q(common)
        peer_b = _q((2.0 * coherence - 1.0) * common + (1.0 - coherence) * 0.35 * independent_b)
        peer_c = _q(coherence * common + (1.0 - coherence) * independent_c)
        peer_mean = (peer_a + peer_b + peer_c) / 3.0
        remaining = 1.0 - relation_mix - echo_mix
        target = _q(
            remaining * autonomous
            + relation_mix * peer_a
            + echo_mix * peer_mean
            + sigma * _noise(seed, "final", index)
        )
        rows.append(
            (
                int(round(target * TRACE_SCALE)),
                int(round(peer_a * TRACE_SCALE)),
                int(round(peer_b * TRACE_SCALE)),
                int(round(peer_c * TRACE_SCALE)),
            )
        )
    if len(rows) != SAMPLE_COUNT:
        raise DevelopmentDataError("raw generator did not produce exactly 1001 samples")
    return tuple(rows)


def _trace_bytes(rows: tuple[tuple[int, int, int, int], ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(TRACE_HEADER)
    for index, row in enumerate(rows):
        writer.writerow((index, *row))
    return buffer.getvalue().encode("utf-8")


def _read_recipes(path: Path) -> list[dict[str, object]]:
    if not path.is_file() or path.is_symlink():
        raise DevelopmentDataError(f"missing or unsafe recipe file: {path}")
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DevelopmentDataError("recipe file is not UTF-8") from exc
    if not text.endswith("\n") or any(not line for line in text.splitlines()):
        raise DevelopmentDataError("recipe JSONL is not canonical")
    rows: list[dict[str, object]] = []
    for index, line in enumerate(text.splitlines()):
        value = strict_json_loads(line, source=f"{path}:{index + 1}")
        checked = validate_recipe(value, source=f"recipe {index}")
        if checked["row_index"] != index or line != canonical_json(checked):
            raise DevelopmentDataError("recipe rows are not canonical ordered rows")
        rows.append(checked)
    if len(rows) != TOTAL_CASES:
        raise DevelopmentDataError("raw generation requires exactly 144 recipe rows")
    return rows


def generate_raw_development_corpus(
    recipe_path: str | Path,
    out: str | Path,
    *,
    expected_recipe_sha256: str,
) -> dict[str, Path]:
    source = Path(recipe_path)
    if sha256_bytes(source.read_bytes()) != expected_recipe_sha256:
        raise DevelopmentDataError("recipe SHA-256 mismatch")
    recipes = _read_recipes(source)
    output_dir = Path(out)
    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink() or any(output_dir.iterdir())):
        raise DevelopmentDataError("raw output must be an empty safe directory")
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for recipe in recipes:
        row_index = int(recipe["row_index"])
        relative = Path("raw") / f"row_{row_index:06d}.csv"
        data = _trace_bytes(generate_case(recipe))
        write_exclusive(output_dir / relative, data)
        entries.append(
            {
                "backend_code": int(recipe["backend_code"]),
                "row_index": row_index,
                "sample_count": SAMPLE_COUNT,
                "trace_relative_path": relative.as_posix(),
                "trace_sha256": sha256_bytes(data),
            }
        )
    manifest = {
        "version": VERSION,
        "manifest_state": "RAW_DEVELOPMENT_CORPUS_GENERATED_FROM_NUMERIC_RECIPES",
        "generator_contract_sha256": generator_contract_sha256(),
        "recipe_sha256": expected_recipe_sha256,
        "row_count": len(entries),
        "sample_count_per_row": SAMPLE_COUNT,
        "trace_scale": TRACE_SCALE,
        "entries": entries,
        "generator_input_is_class_conditioned_numeric_recipe": True,
        "generator_reads_sealed_labels_or_groups": False,
        "observable_extractor_policy": "label_free_numeric_trace_only",
    }
    manifest_path = output_dir / "raw_trace_manifest.json"
    write_canonical_json_exclusive(manifest_path, manifest)
    return {"raw_dir": raw_dir, "manifest": manifest_path}
