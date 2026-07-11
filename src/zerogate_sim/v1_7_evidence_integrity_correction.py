from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from zerogate_sim.final_output import build_final_output_rows
from zerogate_sim.gates import GateScores
from zerogate_sim.matrix import build_scenarios
from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle

CURRENT_VERSION = "v1.7.11-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
SCIENTIFIC_STATUS = "HOLD_CONSTRUCTION_BOUND"
ANSWER_SYMBOL = "0/HOLD"

RUNG_ORDER = ("triad27", "deep81", "wide243")
EXPECTED_CANDIDATE_PROFILES = (
    "adversary_distinction",
    "adversary_polarity",
    "adversary_relation",
    "adversary_return",
    "four_gates_debt",
)
CANONICAL_CONTRACT_ID = "zerogate-v1.7.11-evidence-integrity-canonical-v1"
CANONICAL_SEEDS = tuple(range(18, 27))
AXIS_VALUES = {"M": -1, "Z": 0, "P": 1}
SCENARIO_RE = re.compile(
    r"^n(?P<n>[MZP])_r(?P<r>[MZP])_e(?P<e>[MZP])"
    r"(?:_p(?P<p>[MZP]))?(?:_t(?P<t>[MZP]))?$"
)
SEED_RE = re.compile(r"^seed_(?P<seed>-?\d+)$")

COUNT_FIELDS = (
    "raw_expression_pressure",
    "final_earned_one_count",
    "raw_false_one_pressure",
    "false_one_demoted_count",
    "latent_overcrown_pressure",
    "latent_overcrown_demoted_count",
    "relation_debt_count",
    "return_debt_count",
)

PUBLIC_COUNT_NAMES = {
    "raw_expression_pressure": "raw_expression_pressure",
    "final_earned_one_count": "earned_one",
    "raw_false_one_pressure": "false_one_pressure",
    "false_one_demoted_count": "false_one_demoted",
    "latent_overcrown_pressure": "latent_overcrown",
    "latent_overcrown_demoted_count": "latent_overcrown_demoted",
    "relation_debt_count": "relation_debt",
    "return_debt_count": "return_debt",
}

OBSERVABLE_SPEC_FIELDS = (
    "amplitude",
    "frequency",
    "phase",
    "noise",
    "drift",
    "bias",
    "coupling_group",
    "relation_weight",
)

OUTPUT_FILES = {
    "occurrences": "v1_7_atomic_case_occurrences.csv",
    "unique_cases": "v1_7_unique_atomic_cases.csv",
    "overlap": "v1_7_nested_rung_overlap.csv",
    "rates": "v1_7_rung_rates.csv",
    "nested_safe": "v1_7_nested_safe_totals.csv",
    "sources": "v1_7_source_verification.csv",
    "decision": "v1_7_evidence_integrity_decision.json",
    "read": "v1_7_evidence_integrity_correction_read.md",
    "bundle": "v1_7_evidence_integrity_correction_bundle.zip",
}


class EvidenceIntegrityError(ValueError):
    """Raised when an evidence input cannot be verified without guessing."""


@dataclass(frozen=True)
class AtomicOccurrence:
    rung: str
    case_id: str
    payload_sha256: str
    matrix_family: str
    scenario: str
    effective_scenario: str
    seed: int
    candidate_id: str
    source_path: str
    source_sha256: str
    metadata_sha256: str
    case_identity_json: str
    canonical_payload_json: str
    gate_score: GateScores

    def as_row(self) -> dict[str, object]:
        return {
            "rung": self.rung,
            "case_id": self.case_id,
            "payload_sha256": self.payload_sha256,
            "matrix_family": self.matrix_family,
            "scenario": self.scenario,
            "effective_scenario": self.effective_scenario,
            "seed": self.seed,
            "candidate_id": self.candidate_id,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "metadata_sha256": self.metadata_sha256,
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_hash(value: object) -> str:
    data = _stable_json(value)
    return _sha256_bytes(data.encode("utf-8"))


def _stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _strict_int(value: object, *, field: str, source: Path) -> int:
    if value is None or str(value).strip() == "":
        raise EvidenceIntegrityError(f"{source}: missing required numeric field {field!r}")
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise EvidenceIntegrityError(f"{source}: malformed numeric field {field!r}: {value!r}") from exc
    if not number.is_integer():
        raise EvidenceIntegrityError(f"{source}: non-integral count field {field!r}: {value!r}")
    return int(number)


def _strict_float(value: object, *, field: str, source: Path, positive: bool = False) -> float:
    if value is None or str(value).strip() == "":
        raise EvidenceIntegrityError(f"{source}: missing required numeric field {field!r}")
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise EvidenceIntegrityError(f"{source}: malformed numeric field {field!r}: {value!r}") from exc
    if not math.isfinite(number) or (positive and number <= 0):
        qualifier = "positive finite" if positive else "finite"
        raise EvidenceIntegrityError(f"{source}: {field!r} must be {qualifier}, got {value!r}")
    return number


def _strict_bool(value: object, *, field: str, source: Path) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise EvidenceIntegrityError(f"{source}: malformed boolean field {field!r}: {value!r}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise EvidenceIntegrityError(f"missing CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    if not rows:
        raise EvidenceIntegrityError(f"empty CSV: {path}")
    return rows


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise EvidenceIntegrityError(f"missing metadata: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceIntegrityError(f"invalid JSON metadata: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceIntegrityError(f"metadata root must be an object: {path}")
    return value


def _scenario_axes(scenario: str) -> tuple[dict[str, int | None], dict[str, int]]:
    match = SCENARIO_RE.fullmatch(scenario)
    if match is None:
        raise EvidenceIntegrityError(f"unrecognized matrix scenario {scenario!r}")
    groups = match.groupdict()
    raw: dict[str, int | None] = {
        "noise": AXIS_VALUES[str(groups["n"])],
        "relation": AXIS_VALUES[str(groups["r"])],
        "expression": AXIS_VALUES[str(groups["e"])],
        "perturbation": AXIS_VALUES[str(groups["p"])] if groups["p"] else None,
        "time": AXIS_VALUES[str(groups["t"])] if groups["t"] else None,
    }
    effective = {
        **raw,
        # In matrix.py, absent perturbation is operationally the minus/calm arm.
        "perturbation": -1 if raw["perturbation"] is None else int(raw["perturbation"]),
        # In matrix.py, absent time pressure is operationally the zero/baseline arm.
        "time": 0 if raw["time"] is None else int(raw["time"]),
    }
    return raw, {key: int(value) for key, value in effective.items()}


def _effective_axes(scenario: str) -> dict[str, int]:
    return _scenario_axes(scenario)[1]


def _validate_rung_scenario_shape(rung: str, scenario: str) -> None:
    match = SCENARIO_RE.fullmatch(scenario)
    if match is None:
        raise EvidenceIntegrityError(f"unrecognized matrix scenario {scenario!r}")
    p_present = match.group("p") is not None
    t_present = match.group("t") is not None
    valid = {
        "triad27": not p_present and not t_present,
        "deep81": p_present and not t_present,
        "wide243": p_present and t_present,
    }[rung]
    if not valid:
        raise EvidenceIntegrityError(f"{rung}: scenario shape does not match rung: {scenario}")


def _effective_scenario_text(axes: Mapping[str, int]) -> str:
    return "|".join(f"{name}={axes[name]}" for name in ("noise", "relation", "expression", "perturbation", "time"))


def _canonical_family(parts: tuple[str, ...], rung: str) -> str:
    cleaned: list[str] = []
    for part in parts:
        value = part.replace(f"_{rung}", "").replace(f"{rung}_", "")
        if value == rung:
            continue
        cleaned.append(value)
    if not cleaned:
        raise EvidenceIntegrityError("matrix family cannot be empty")
    return "/".join(cleaned)


def _locate_scenario_and_seed(relative: Path) -> tuple[int, str, int]:
    parts = relative.parts
    for index, part in enumerate(parts):
        if SCENARIO_RE.fullmatch(part) is None:
            continue
        if index + 1 >= len(parts):
            break
        seed_match = SEED_RE.fullmatch(parts[index + 1])
        if seed_match is None:
            break
        return index, part, int(seed_match.group("seed"))
    raise EvidenceIntegrityError(f"cannot derive scenario/seed from {relative}")


def _candidate_spec(metadata: Mapping[str, object], candidate_id: str, *, source: Path) -> dict[str, object]:
    specs = metadata.get("candidate_specs")
    if not isinstance(specs, list):
        raise EvidenceIntegrityError(f"{source}: candidate_specs missing from metadata")
    ids = [str(item.get("candidate_id", "")) for item in specs if isinstance(item, dict)]
    if len(ids) != len(specs) or any(not value for value in ids) or len(set(ids)) != len(ids):
        raise EvidenceIntegrityError(f"{source}: candidate_specs must have unique non-empty candidate_id values")
    for index, raw_spec in enumerate(specs):
        if not isinstance(raw_spec, dict) or str(raw_spec.get("candidate_id", "")) != candidate_id:
            continue
        observable = {
            field: _strict_float(raw_spec.get(field), field=f"candidate_specs.{candidate_id}.{field}", source=source)
            for field in OBSERVABLE_SPEC_FIELDS
            if field != "coupling_group"
        }
        raw_coupling_group = raw_spec.get("coupling_group")
        observable["coupling_group"] = (
            None
            if raw_coupling_group is None
            else _strict_int(
                raw_coupling_group,
                field=f"candidate_specs.{candidate_id}.coupling_group",
                source=source,
            )
        )
        return {
            "candidate_index": index,
            **observable,
        }
    raise EvidenceIntegrityError(f"{source}: no candidate spec for {candidate_id!r}")


def _case_identity(
    *,
    metadata: Mapping[str, object],
    matrix_family: str,
    axes: Mapping[str, int],
    seed: int,
    candidate_id: str,
    source: Path,
) -> dict[str, object]:
    config = metadata.get("config")
    run = metadata.get("run")
    if not isinstance(config, dict) or not isinstance(run, dict):
        raise EvidenceIntegrityError(f"{source}: config/run metadata missing")
    metadata_seed = _strict_int(config.get("seed"), field="config.seed", source=source)
    if metadata_seed != seed:
        raise EvidenceIntegrityError(f"{source}: path seed {seed} != metadata seed {metadata_seed}")
    generator = str(run.get("generator", "")).strip()
    candidate_profile = str(run.get("matrix_candidate_profile", "")).strip()
    if not generator or not candidate_profile:
        raise EvidenceIntegrityError(f"{source}: generator and matrix_candidate_profile are required")
    # matrix.py stores the already-scaled dt in config.dt. Do not apply
    # matrix_dt_factor a second time.
    effective_dt = _strict_float(config.get("dt"), field="config.dt", source=source, positive=True)
    n_steps = _strict_int(config.get("n_steps"), field="config.n_steps", source=source)
    if n_steps <= 0:
        raise EvidenceIntegrityError(f"{source}: config.n_steps must be positive")
    return {
        "generator": generator,
        "matrix_family": candidate_profile,
        "seed": seed,
        "n_steps": n_steps,
        "effective_dt": effective_dt,
        "noise_floor": _strict_float(config.get("noise_floor"), field="config.noise_floor", source=source),
        "near_zero_ratio": _strict_float(config.get("near_zero_ratio"), field="config.near_zero_ratio", source=source),
        "gate_threshold": _strict_float(config.get("gate_threshold"), field="config.gate_threshold", source=source),
        "strength_threshold": _strict_float(config.get("strength_threshold"), field="config.strength_threshold", source=source),
        "axes": dict(axes),
        "candidate": _candidate_spec(metadata, candidate_id, source=source),
    }


GATE_STRING_FIELDS = {
    "candidate_id",
    "kind",
    "description",
    "truth_role",
    "echo_mimic_band",
    "trinary_outcome",
    "outcome_reason",
    "zero_band",
    "zero_band_symbol",
    "zero_band_reason",
    "limiting_gate",
}
GATE_BOOL_FIELDS = {"designed_stable", "expressed", "observed_stable"}
GATE_INT_FIELDS = {"expected_trinary", "zero_depth", "trinary_value", "zero_band_value"}


def _gate_score_from_row(row: Mapping[str, object], *, scenario: str, source: Path) -> GateScores:
    values: dict[str, object] = {}
    for field_name in GateScores.__dataclass_fields__:
        value = row.get(field_name)
        if field_name in GATE_STRING_FIELDS:
            if value is None:
                raise EvidenceIntegrityError(f"{source}: missing gate field {field_name!r}")
            values[field_name] = str(value)
        elif field_name in GATE_BOOL_FIELDS:
            values[field_name] = _strict_bool(value, field=field_name, source=source)
        elif field_name in GATE_INT_FIELDS:
            values[field_name] = _strict_int(value, field=field_name, source=source)
        else:
            values[field_name] = _strict_float(value, field=field_name, source=source)
    values["candidate_id"] = f"{scenario}:{values['candidate_id']}"
    return GateScores(**values)


def _scan_rung(
    rung: str,
    root: Path,
) -> tuple[list[AtomicOccurrence], list[dict[str, object]], dict[Path, str]]:
    if rung not in RUNG_ORDER:
        raise EvidenceIntegrityError(f"unsupported rung {rung!r}")
    root = root.resolve()
    gate_files = sorted(root.rglob("gate_scores.csv"))
    if not gate_files:
        raise EvidenceIntegrityError(f"{rung}: no gate_scores.csv files under {root}")

    occurrences: list[AtomicOccurrence] = []
    sources: list[dict[str, object]] = []
    matrix_profile_by_dir: dict[Path, str] = {}
    for gate_path in gate_files:
        relative = gate_path.relative_to(root)
        scenario_index, scenario, seed = _locate_scenario_and_seed(relative)
        _validate_rung_scenario_shape(rung, scenario)
        path_family = _canonical_family(tuple(relative.parts[:scenario_index]), rung)
        raw_axes, axes = _scenario_axes(scenario)
        effective_scenario = _effective_scenario_text(axes)
        metadata_path = gate_path.parent / "metadata.json"
        metadata = _read_json(metadata_path)
        run = metadata.get("run")
        specs = metadata.get("candidate_specs")
        if not isinstance(run, dict) or not isinstance(specs, list):
            raise EvidenceIntegrityError(f"{metadata_path}: run/candidate_specs metadata missing")
        if str(run.get("matrix_profile", "")) != rung:
            raise EvidenceIntegrityError(f"{metadata_path}: matrix_profile does not match {rung}")
        if str(run.get("matrix_scenario", "")) != scenario:
            raise EvidenceIntegrityError(f"{metadata_path}: matrix_scenario does not match path")
        candidate_profile = str(run.get("matrix_candidate_profile", "")).strip()
        if not candidate_profile:
            raise EvidenceIntegrityError(f"{metadata_path}: matrix_candidate_profile is required")
        metadata_axes = run.get("matrix_axes")
        expected_metadata_axes = {
            "noise_axis": raw_axes["noise"],
            "relation_axis": raw_axes["relation"],
            "expansion_axis": raw_axes["expression"],
            "perturbation_axis": raw_axes["perturbation"],
            "time_axis": raw_axes["time"],
        }
        if metadata_axes != expected_metadata_axes:
            raise EvidenceIntegrityError(f"{metadata_path}: matrix_axes do not match scenario path")
        source_sha256 = _sha256_file(gate_path)
        metadata_sha256 = _sha256_file(metadata_path)
        rows = _read_csv(gate_path)
        expected_candidates = {
            str(item.get("candidate_id", "")) for item in specs if isinstance(item, dict)
        }
        row_candidates = {str(row.get("candidate_id", "")) for row in rows}
        if "" in expected_candidates or len(expected_candidates) != len(specs):
            raise EvidenceIntegrityError(f"{metadata_path}: candidate_specs IDs must be unique and non-empty")
        if row_candidates != expected_candidates or len(row_candidates) != len(rows):
            raise EvidenceIntegrityError(f"{gate_path}: gate rows do not match metadata candidate_specs")
        n_candidates = _strict_int(run.get("n_candidates"), field="run.n_candidates", source=metadata_path)
        if n_candidates != len(specs):
            raise EvidenceIntegrityError(f"{metadata_path}: run.n_candidates does not match candidate_specs")
        matrix_dir = gate_path.parents[2].resolve()
        prior_profile = matrix_profile_by_dir.get(matrix_dir)
        if prior_profile is not None and prior_profile != candidate_profile:
            raise EvidenceIntegrityError(f"{matrix_dir}: conflicting matrix_candidate_profile metadata")
        matrix_profile_by_dir[matrix_dir] = candidate_profile
        sources.append(
            {
                "source_kind": "gate_scores",
                "rung": rung,
                "matrix_profile": candidate_profile,
                "path_family": path_family,
                "path": f"{rung}/{relative.as_posix()}",
                "sha256": source_sha256,
                "metadata_sha256": metadata_sha256,
                "record_count": len(rows),
                "duplicate_content": "false",
            }
        )
        for row in rows:
            candidate_id = str(row.get("candidate_id", "")).strip()
            if not candidate_id:
                raise EvidenceIntegrityError(f"{gate_path}: candidate_id is required")
            identity = _case_identity(
                metadata=metadata,
                matrix_family=candidate_profile,
                axes=axes,
                seed=seed,
                candidate_id=candidate_id,
                source=metadata_path,
            )
            gate_score = _gate_score_from_row(row, scenario=scenario, source=gate_path)
            canonical_payload = gate_score.to_dict()
            canonical_payload["candidate_id"] = candidate_id
            occurrences.append(
                AtomicOccurrence(
                    rung=rung,
                    case_id=_stable_hash(identity),
                    payload_sha256=_stable_hash(canonical_payload),
                    matrix_family=candidate_profile,
                    scenario=scenario,
                    effective_scenario=effective_scenario,
                    seed=seed,
                    candidate_id=candidate_id,
                    source_path=f"{rung}/{relative.as_posix()}",
                    source_sha256=source_sha256,
                    metadata_sha256=metadata_sha256,
                    case_identity_json=_stable_json(identity),
                    canonical_payload_json=_stable_json(canonical_payload),
                    gate_score=gate_score,
                )
            )
    return occurrences, sources, matrix_profile_by_dir


def _recompute_final_rows(
    occurrences: Iterable[AtomicOccurrence],
) -> dict[tuple[str, str], dict[str, object]]:
    grouped: dict[str, list[tuple[int, GateScores]]] = defaultdict(list)
    for item in occurrences:
        grouped[item.matrix_family].append((item.seed, item.gate_score))
    out: dict[tuple[str, str], dict[str, object]] = {}
    for profile, gate_rows in grouped.items():
        for row in build_final_output_rows(gate_rows):
            key = (profile, str(row["candidate_id"]))
            if key in out:
                raise EvidenceIntegrityError(f"duplicate recomputed final row: {key}")
            out[key] = row
    return out


def _aggregate_final_outputs(
    rung: str,
    root: Path,
    *,
    matrix_profile_by_dir: Mapping[Path, str],
    recomputed_rows: Mapping[tuple[str, str], Mapping[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    paths = sorted(root.resolve().rglob("matrix_final_output_summary.csv"))
    if not paths:
        raise EvidenceIntegrityError(f"{rung}: no matrix_final_output_summary.csv files under {root}")

    seen_keys: set[tuple[str, str]] = set()
    duplicate_semantic_rows = 0
    summary_mismatch_count = 0
    sources: list[dict[str, object]] = []

    for path in paths:
        matrix_profile = matrix_profile_by_dir.get(path.parent.resolve())
        if matrix_profile is None:
            raise EvidenceIntegrityError(f"{path}: no verified matrix profile from gate metadata")
        source_hash = _sha256_file(path)
        rows = _read_csv(path)
        sources.append(
            {
                "source_kind": "matrix_final_output_summary",
                "rung": rung,
                "matrix_profile": matrix_profile,
                "path_family": path.parent.name,
                "path": f"{rung}/{path.relative_to(root.resolve()).as_posix()}",
                "sha256": source_hash,
                "metadata_sha256": "not_applicable",
                "record_count": len(rows),
                "duplicate_content": "false",
            }
        )
        file_candidate_ids: set[str] = set()
        for row in rows:
            candidate_id = str(row.get("candidate_id", "")).strip()
            if not candidate_id:
                raise EvidenceIntegrityError(f"{path}: candidate_id is required")
            if candidate_id in file_candidate_ids:
                raise EvidenceIntegrityError(f"{path}: duplicate candidate_id {candidate_id!r}")
            file_candidate_ids.add(candidate_id)
            key = (matrix_profile, candidate_id)
            if key in seen_keys:
                duplicate_semantic_rows += 1
                continue
            seen_keys.add(key)
            runs = _strict_int(row.get("runs"), field="runs", source=path)
            if runs <= 0:
                raise EvidenceIntegrityError(f"{path}: runs must be positive")
            counts: dict[str, int] = {}
            for field in COUNT_FIELDS:
                count = _strict_int(row.get(field), field=field, source=path)
                if count < 0 or count > runs:
                    raise EvidenceIntegrityError(f"{path}: {field} must satisfy 0 <= count <= runs")
                counts[field] = count
            if counts["false_one_demoted_count"] != counts["raw_false_one_pressure"]:
                raise EvidenceIntegrityError(f"{path}: false-one pressure/demotion counts disagree")
            if counts["latent_overcrown_demoted_count"] != counts["latent_overcrown_pressure"]:
                raise EvidenceIntegrityError(f"{path}: latent pressure/demotion counts disagree")
            partition = (
                counts["final_earned_one_count"]
                + counts["raw_false_one_pressure"]
                + counts["latent_overcrown_pressure"]
                + counts["relation_debt_count"]
                + counts["return_debt_count"]
            )
            if partition != counts["raw_expression_pressure"]:
                raise EvidenceIntegrityError(f"{path}: final lane counts do not partition raw expression")
            expected = recomputed_rows.get(key)
            if expected is None:
                summary_mismatch_count += 1
                continue
            numeric_mismatch = runs != int(expected["runs"]) or any(
                counts[field] != int(expected[field]) for field in COUNT_FIELDS
            )
            final_value = _strict_int(
                row.get("final_trinary_value"),
                field="final_trinary_value",
                source=path,
            )
            text_mismatch = any(
                str(row.get(field, "")).strip() != str(expected.get(field, "")).strip()
                for field in ("final_trinary_symbol", "truth_role", "kind")
            )
            if numeric_mismatch or final_value != int(expected["final_trinary_value"]) or text_mismatch:
                summary_mismatch_count += 1

    missing_recomputed_rows = len(set(recomputed_rows) - seen_keys)
    extra_summary_rows = len(seen_keys - set(recomputed_rows))
    summary_mismatch_count += missing_recomputed_rows + extra_summary_rows

    totals = {field: sum(int(row[field]) for row in recomputed_rows.values()) for field in COUNT_FIELDS}
    opportunities = sum(int(row["runs"]) for row in recomputed_rows.values())
    final_false_crowns = sum(
        int(row["raw_false_one_pressure"])
        for row in recomputed_rows.values()
        if str(row["truth_role"]) == "trap" and int(row["final_trinary_value"]) == 1
    )
    if opportunities <= 0:
        raise EvidenceIntegrityError(f"{rung}: recomputed opportunity denominator must be positive")
    metrics: dict[str, object] = {
        "weather_rung": rung,
        "opportunities": opportunities,
        "matrix_artifact_count": len(paths),
        "unique_matrix_artifact_count": len(matrix_profile_by_dir),
        "duplicate_matrix_artifact_count": duplicate_semantic_rows,
        "candidate_summary_rows": len(seen_keys),
        "recomputed_candidate_rows": len(recomputed_rows),
        "summary_mismatch_count": summary_mismatch_count,
        "final_false_one_crowns": final_false_crowns,
        "final_false_one_crown_rate": final_false_crowns / opportunities,
    }
    for source_name, public_name in PUBLIC_COUNT_NAMES.items():
        count = totals[source_name]
        metrics[public_name] = count
        metrics[f"{public_name}_rate"] = count / opportunities
    return metrics, sources


def _default_scenario_contract() -> dict[str, set[str]]:
    return {
        rung: {scenario.name for scenario in build_scenarios(rung)}
        for rung in RUNG_ORDER
    }


def _contract_payload(
    candidate_profiles: Iterable[str],
    scenarios: Mapping[str, set[str]],
    seeds: Iterable[int],
) -> dict[str, object]:
    return {
        "contract_id": CANONICAL_CONTRACT_ID,
        "candidate_profiles": sorted(str(value) for value in candidate_profiles),
        "scenarios": {rung: sorted(scenarios[rung]) for rung in RUNG_ORDER},
        "seeds": sorted(int(value) for value in seeds),
    }


def canonical_contract_payload() -> dict[str, object]:
    return _contract_payload(EXPECTED_CANDIDATE_PROFILES, _default_scenario_contract(), CANONICAL_SEEDS)


def canonical_contract_sha256() -> str:
    return _stable_hash(canonical_contract_payload())


def _coverage_check(
    by_rung: Mapping[str, list[AtomicOccurrence]],
    *,
    expected_candidate_profiles: set[str],
    expected_scenarios: Mapping[str, set[str]],
    expected_seeds: set[int],
) -> tuple[bool, dict[str, object]]:
    if not expected_seeds:
        raise EvidenceIntegrityError("expected_seeds cannot be empty")
    failures: list[str] = []
    all_seed_sets: list[frozenset[int]] = []
    candidate_sets_by_profile: dict[str, set[frozenset[str]]] = defaultdict(set)
    coverage_rows: list[dict[str, object]] = []

    for rung in RUNG_ORDER:
        occurrences = by_rung[rung]
        profiles = {item.matrix_family for item in occurrences}
        if profiles != expected_candidate_profiles:
            failures.append(f"{rung}:candidate_profiles")
        for profile in sorted(expected_candidate_profiles):
            profile_rows = [item for item in occurrences if item.matrix_family == profile]
            scenarios = {item.scenario for item in profile_rows}
            if scenarios != expected_scenarios[rung]:
                failures.append(f"{rung}:{profile}:scenarios")
            cells: dict[tuple[str, int], set[str]] = defaultdict(set)
            for item in profile_rows:
                cells[(item.scenario, item.seed)].add(item.candidate_id)
            seed_sets = {
                scenario: frozenset(seed for cell_scenario, seed in cells if cell_scenario == scenario)
                for scenario in scenarios
            }
            for seed_set in seed_sets.values():
                all_seed_sets.append(seed_set)
                if seed_set != frozenset(expected_seeds):
                    failures.append(f"{rung}:{profile}:seed_set")
            candidate_sets = {frozenset(value) for value in cells.values()}
            candidate_sets_by_profile[profile].update(candidate_sets)
            if len(candidate_sets) != 1:
                failures.append(f"{rung}:{profile}:candidate_set")
            coverage_rows.append(
                {
                    "rung": rung,
                    "candidate_profile": profile,
                    "scenario_count": len(scenarios),
                    "expected_scenario_count": len(expected_scenarios[rung]),
                    "seed_count": len(next(iter(seed_sets.values()))) if seed_sets else 0,
                    "candidate_count": len(next(iter(candidate_sets))) if candidate_sets else 0,
                }
            )

    if not all_seed_sets or len(set(all_seed_sets)) != 1:
        failures.append("cross_rung_or_cell_seed_set")
    for profile, candidate_sets in candidate_sets_by_profile.items():
        if len(candidate_sets) != 1:
            failures.append(f"{profile}:cross_rung_candidate_set")
    return not failures, {"failures": sorted(set(failures)), "rows": coverage_rows}


def _pair_overlap(name: str, left: set[str], right: set[str]) -> dict[str, object]:
    overlap = left & right
    return {
        "comparison": name,
        "left_cases": len(left),
        "right_cases": len(right),
        "overlap_cases": len(overlap),
        "left_subset_of_right": left <= right,
        "left_only_cases": len(left - right),
        "right_only_cases": len(right - left),
    }


def _write_read(path: Path, decision: Mapping[str, object], rates: list[dict[str, object]]) -> None:
    lines = [
        "# v1.7.11-alpha — Evidence Integrity Correction",
        "",
        f"**Scientific status:** `{decision['scientific_status']}`",
        f"**Answer:** `{decision['answer_symbol']}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "v1.7.10-alpha remains reproducible history, but its closeout is superseded as construction-bound. The current final path uses truth role, and the old audit did not execute a frozen role-free scorer.",
        "",
        "## Corrected accounting",
        "",
        "| rung | opportunities | earned | earned rate | raw | raw rate | false pressure | false-pressure rate | final false crowns |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rates:
        lines.append(
            f"| {row['weather_rung']} | {row['opportunities']} | {row['earned_one']} | "
            f"{float(row['earned_one_rate']):.6%} | {row['raw_expression_pressure']} | "
            f"{float(row['raw_expression_pressure_rate']):.6%} | {row['false_one_pressure']} | "
            f"{float(row['false_one_pressure_rate']):.6%} | {row['final_false_one_crowns']} |"
        )
    if decision["accounting_integrity_passed"]:
        union_lines = [
            f"Verified unique atomic union: `{decision['unique_atomic_cases']}`.",
            "The unique-union descriptive counts are recomputed from deduplicated gate rows and match wide243. They remain role-aware construction output, not evidence of blind discrimination.",
        ]
    else:
        union_lines = [
            f"Candidate distinct case IDs observed: `{decision['unique_atomic_cases']}`.",
            "Accounting integrity failed. No authoritative unique-union counts are issued; the widest-view counts are diagnostic only.",
        ]
    lines.extend(
        [
            "",
            f"Naive nested opportunity sum: `{decision['legacy_pooled_opportunities']}`.",
            *union_lines,
            f"Duplicate representations observed: `{decision['duplicate_atomic_representations']}`.",
            "",
            "## Holds",
            "",
            "- Manuscript v2: HOLD.",
            "- DTA transfer or integration: HOLD.",
            "- Scientific threshold selection: HOLD until the label firewall and blind witness exist.",
            "- Release / Zenodo: HOLD unless separately authorized after the corrective line is complete.",
            "",
            "## Next coded boundary",
            "",
            "`v1.8.0-alpha — Observable Schema and Label Firewall`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_v1_7_evidence_integrity_correction(
    out: str | Path,
    *,
    triad_root: str | Path,
    deep_root: str | Path,
    wide_root: str | Path,
    expected_candidate_profiles: Iterable[str] = EXPECTED_CANDIDATE_PROFILES,
    expected_scenarios: Mapping[str, set[str]] | None = None,
    expected_seeds: Iterable[int] = CANONICAL_SEEDS,
) -> dict[str, Path]:
    roots = {
        "triad27": Path(triad_root).resolve(),
        "deep81": Path(deep_root).resolve(),
        "wide243": Path(wide_root).resolve(),
    }
    if len(set(roots.values())) != len(RUNG_ORDER):
        raise EvidenceIntegrityError("triad, deep, and wide roots must be distinct")
    expected_profile_set = {str(value) for value in expected_candidate_profiles}
    if not expected_profile_set:
        raise EvidenceIntegrityError("expected_candidate_profiles cannot be empty")
    scenario_contract = (
        {rung: set(values) for rung, values in expected_scenarios.items()}
        if expected_scenarios is not None
        else _default_scenario_contract()
    )
    if set(scenario_contract) != set(RUNG_ORDER):
        raise EvidenceIntegrityError("expected_scenarios must define triad27, deep81, and wide243")
    expected_seed_set = {int(value) for value in expected_seeds}
    if not expected_seed_set:
        raise EvidenceIntegrityError("expected_seeds cannot be empty")
    requested_contract = _contract_payload(expected_profile_set, scenario_contract, expected_seed_set)
    requested_contract_sha256 = _stable_hash(requested_contract)
    expected_contract_sha256 = canonical_contract_sha256()
    contract_matches_canonical_definition = requested_contract_sha256 == expected_contract_sha256
    out_dir = ensure_dir(Path(out))
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}

    by_rung: dict[str, list[AtomicOccurrence]] = {}
    source_rows: list[dict[str, object]] = []
    rate_rows: list[dict[str, object]] = []
    for rung in RUNG_ORDER:
        occurrences, gate_sources, matrix_profile_by_dir = _scan_rung(rung, roots[rung])
        recomputed_rows = _recompute_final_rows(occurrences)
        metrics, summary_sources = _aggregate_final_outputs(
            rung,
            roots[rung],
            matrix_profile_by_dir=matrix_profile_by_dir,
            recomputed_rows=recomputed_rows,
        )
        metrics["atomic_gate_records"] = len(occurrences)
        metrics["gate_records_match_opportunities"] = len(occurrences) == metrics["opportunities"]
        by_rung[rung] = occurrences
        source_rows.extend(gate_sources)
        source_rows.extend(summary_sources)
        rate_rows.append(metrics)

    coverage_complete, coverage = _coverage_check(
        by_rung,
        expected_candidate_profiles=expected_profile_set,
        expected_scenarios=scenario_contract,
        expected_seeds=expected_seed_set,
    )
    canonical_contract_passed = coverage_complete and contract_matches_canonical_definition

    all_occurrences = [item for rung in RUNG_ORDER for item in by_rung[rung]]
    case_groups: dict[str, list[AtomicOccurrence]] = defaultdict(list)
    for item in all_occurrences:
        case_groups[item.case_id].append(item)

    rung_ids = {rung: {item.case_id for item in by_rung[rung]} for rung in RUNG_ORDER}
    within_rung_duplicate_count = sum(len(by_rung[rung]) - len(rung_ids[rung]) for rung in RUNG_ORDER)
    payload_mismatch_count = sum(
        1 for group in case_groups.values() if len({item.payload_sha256 for item in group}) > 1
    )
    overlap_rows = [
        _pair_overlap("triad27_in_deep81", rung_ids["triad27"], rung_ids["deep81"]),
        _pair_overlap("deep81_in_wide243", rung_ids["deep81"], rung_ids["wide243"]),
        _pair_overlap("triad27_in_wide243", rung_ids["triad27"], rung_ids["wide243"]),
    ]
    nested_consistent = (
        rung_ids["triad27"] <= rung_ids["deep81"] <= rung_ids["wide243"]
        and payload_mismatch_count == 0
    )
    union_ids = set().union(*rung_ids.values())
    unique_union_rung = "wide243" if union_ids == rung_ids["wide243"] else "none"
    duplicate_representations = len(all_occurrences) - len(union_ids)

    file_hash_counts = Counter(
        str(row["sha256"]) for row in source_rows if row["source_kind"] == "gate_scores"
    )
    duplicate_file_representations = sum(count - 1 for count in file_hash_counts.values())
    matrix_duplicate_count = sum(int(row["duplicate_matrix_artifact_count"]) for row in rate_rows)
    opportunities_match = all(bool(row["gate_records_match_opportunities"]) for row in rate_rows)
    summaries_match_recomputed = all(int(row["summary_mismatch_count"]) == 0 for row in rate_rows)
    structural_accounting_passed = (
        within_rung_duplicate_count == 0
        and payload_mismatch_count == 0
        and nested_consistent
        and unique_union_rung == "wide243"
        and matrix_duplicate_count == 0
        and opportunities_match
        and summaries_match_recomputed
        and coverage_complete
    )

    selected_by_case: list[dict[str, object]] = []
    selected_occurrences: list[AtomicOccurrence] = []
    rung_rank = {rung: index for index, rung in enumerate(RUNG_ORDER)}
    for case_id, group in case_groups.items():
        selected = max(group, key=lambda item: rung_rank[item.rung])
        selected_occurrences.append(selected)
        selected_row = selected.as_row()
        selected_row["representation_count"] = len(group)
        selected_row["represented_rungs"] = ",".join(
            rung for rung in RUNG_ORDER if any(item.rung == rung for item in group)
        )
        selected_row["payloads_match"] = len({item.payload_sha256 for item in group}) == 1
        selected_row["case_identity_json"] = selected.case_identity_json
        selected_row["canonical_gate_payload_json"] = selected.canonical_payload_json
        selected_by_case.append(selected_row)

    rate_by_rung = {str(row["weather_rung"]): row for row in rate_rows}
    wide_metrics = rate_by_rung["wide243"]
    unique_final_rows = _recompute_final_rows(selected_occurrences)
    unique_candidate_metrics: dict[str, int] = {
        "opportunities": sum(int(row["runs"]) for row in unique_final_rows.values()),
        "final_false_one_crowns": sum(
            int(row["raw_false_one_pressure"])
            for row in unique_final_rows.values()
            if str(row["truth_role"]) == "trap" and int(row["final_trinary_value"]) == 1
        ),
    }
    for source_name, public_name in PUBLIC_COUNT_NAMES.items():
        unique_candidate_metrics[public_name] = sum(
            int(row[source_name]) for row in unique_final_rows.values()
        )
    unique_recompute_matches_wide = all(
        int(unique_candidate_metrics[name]) == int(wide_metrics[name])
        for name in unique_candidate_metrics
    )
    structural_accounting_passed = structural_accounting_passed and unique_recompute_matches_wide
    accounting_integrity_passed = structural_accounting_passed and canonical_contract_passed
    legacy_pooled: dict[str, int] = {
        "opportunities": sum(int(row["opportunities"]) for row in rate_rows),
        "final_false_one_crowns": sum(int(row["final_false_one_crowns"]) for row in rate_rows),
    }
    for public_name in PUBLIC_COUNT_NAMES.values():
        legacy_pooled[public_name] = sum(int(row[public_name]) for row in rate_rows)

    nested_safe_rows = []
    for aggregation, source, valid in (
        (
            "unique_atomic_union" if accounting_integrity_passed else "candidate_widest_view_invalid",
            unique_candidate_metrics,
            accounting_integrity_passed,
        ),
        ("legacy_nested_arithmetic_sum", legacy_pooled, False),
    ):
        row: dict[str, object] = {
            "aggregation": aggregation,
            "valid_as_unique_evidence": str(valid).lower(),
            "opportunities": source["opportunities"],
            "final_false_one_crowns": source["final_false_one_crowns"],
        }
        for public_name in PUBLIC_COUNT_NAMES.values():
            row[public_name] = source[public_name]
            row[f"{public_name}_rate"] = int(source[public_name]) / int(source["opportunities"])
        nested_safe_rows.append(row)

    reason_codes = [
        "CONSTRUCTION_BOUND_FALSE_CROWNS",
        "SELF_ATTESTED_PROVENANCE_SUPERSEDED",
        "NESTED_RUNG_POOLING_CORRECTED",
        "ROLE_FREE_WITNESS_NOT_IMPLEMENTED",
        "LINEAGE_NOT_IN_FINAL_PATH",
    ]
    if not canonical_contract_passed:
        reason_codes.append("CANONICAL_EVIDENCE_CONTRACT_NOT_SATISFIED")

    decision = {
        "version": CURRENT_VERSION,
        "decision": "evidence_integrity_correction_hold",
        "answer_symbol": ANSWER_SYMBOL,
        "scientific_status": SCIENTIFIC_STATUS,
        "evidence_status": "INVALID_FOR_BLIND_EMPIRICAL_DISCRIMINATION",
        "native_witness": NATIVE_WITNESS,
        "native_math_mutated": False,
        "v1_7_10_status": "superseded_as_construction_bound",
        "core_question_closed": False,
        "accounting_integrity_passed": accounting_integrity_passed,
        "structural_accounting_passed": structural_accounting_passed,
        "canonical_contract_id": CANONICAL_CONTRACT_ID,
        "canonical_contract_sha256": expected_contract_sha256,
        "requested_contract_sha256": requested_contract_sha256,
        "contract_matches_canonical_definition": contract_matches_canonical_definition,
        "canonical_contract_passed": canonical_contract_passed,
        "canonical_seed_set": list(CANONICAL_SEEDS),
        "coverage_complete": coverage_complete,
        "coverage_failures": coverage["failures"],
        "final_summaries_match_recomputed_gate_rows": summaries_match_recomputed,
        "unique_recompute_matches_wide": unique_recompute_matches_wide,
        "scoring_label_firewall": "failed_current_gate_rows_and_final_path_are_role_aware",
        "false_crown_failure_capability": "not_demonstrated",
        "lineage_final_path_status": "report_only_not_consumed_by_final_verdict",
        "expected_manifest_status": "not_verifiable_from_current_run_metadata",
        "independent_generator_status": "not_tested",
        "legacy_pooled_totals_valid": False,
        "legacy_pooled_opportunities": legacy_pooled["opportunities"],
        "unique_atomic_cases": len(union_ids),
        "duplicate_atomic_representations": duplicate_representations,
        "declared_atomic_representations": len(all_occurrences),
        "gate_score_files": sum(1 for row in source_rows if row["source_kind"] == "gate_scores"),
        "unique_gate_score_file_hashes": len(file_hash_counts),
        "duplicate_gate_score_file_representations": duplicate_file_representations,
        "within_rung_duplicate_cases": within_rung_duplicate_count,
        "payload_mismatch_cases": payload_mismatch_count,
        "nested_rungs_consistent": nested_consistent,
        "unique_union_rung": unique_union_rung,
        "unique_union_counts": unique_candidate_metrics if accounting_integrity_passed else None,
        "candidate_widest_view_counts": unique_candidate_metrics,
        "legacy_non_independent_pooled_counts": legacy_pooled,
        "reason_codes": reason_codes,
        "manuscript_v2_go": False,
        "dta_transfer_go": False,
        "scientific_thresholds_selected": False,
        "release_go": False,
        "next_gate": "v1.8.0-alpha — Observable Schema and Label Firewall",
    }

    write_dict_rows_csv(paths["occurrences"], [item.as_row() for item in all_occurrences])
    write_dict_rows_csv(paths["unique_cases"], sorted(selected_by_case, key=lambda row: str(row["case_id"])))
    write_dict_rows_csv(paths["overlap"], overlap_rows)
    write_dict_rows_csv(paths["rates"], rate_rows)
    write_dict_rows_csv(paths["nested_safe"], nested_safe_rows)
    write_dict_rows_csv(paths["sources"], source_rows)
    paths["decision"].write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    _write_read(paths["read"], decision, rate_rows)
    paths["bundle"] = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="v1_7_11_evidence_integrity_correction_bundle",
    )
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit v1.7 evidence provenance, nesting, denominators, and current claim authority.")
    parser.add_argument("--triad-root", type=Path, required=True)
    parser.add_argument("--deep-root", type=Path, required=True)
    parser.add_argument("--wide-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = build_v1_7_evidence_integrity_correction(
        args.out,
        triad_root=args.triad_root,
        deep_root=args.deep_root,
        wide_root=args.wide_root,
    )
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['decision']}")
    print(f"Wrote {paths['bundle']}")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    return 0 if decision.get("accounting_integrity_passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
