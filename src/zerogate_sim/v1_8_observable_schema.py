from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

CURRENT_VERSION = "v1.8.0-alpha"
SCHEMA_ID = "zerogate-v1.8-observable-schema-v1"

# Exact pre-verdict numeric measures. Derived verdicts, thresholds, identifiers,
# scenario controls, labels, names, and legacy role-shaped aggregates are not
# part of this boundary. Later versions must explicitly earn any expansion.
OBSERVABLE_FIELDS = (
    "strength",
    "distinction",
    "polarity",
    "relation",
    "return_observed",
    "echo_mimic_score",
    "observed_stability_score",
)

EVALUATION_ROLES = ("expresser", "latent", "trap")
ROLE_TO_TRINARY = {"expresser": 1, "latent": 0, "trap": -1}
BLIND_CASE_ID_RE = re.compile(r"^zg8_[0-9a-f]{24}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

FORBIDDEN_FIELD_EXAMPLES = (
    "candidate_id",
    "kind",
    "description",
    "designed_stable",
    "truth_role",
    "role_label",
    "expected_trinary",
    "candidate_profile",
    "matrix_candidate_profile",
    "matrix_family",
    "source_label",
    "source_profile",
    "profile",
    "scenario",
    "seed",
    "seed_range",
    "boundary",
    "return_potential",
    "zero_coherence",
    "zero_depth",
    "expressed",
    "trinary_value",
    "trinary_outcome",
    "outcome_reason",
    "latent_score",
    "zero_band_value",
    "zero_band",
    "zero_band_symbol",
    "zero_band_reason",
    "limiting_gate",
    "echo_mimic_band",
    "observed_stable",
    "feature_earned_rate",
    "feature_raw_pressure_rate",
    "target_raw_false_one_rate",
    "final_earned_one_count",
    "raw_false_one_pressure",
    "relation_debt_count",
    "return_debt_count",
)

SPLIT_FILES = {
    "observable_inputs": Path("predictor") / "v1_8_observable_inputs.jsonl",
    "join_keys": Path("sealed") / "v1_8_join_keys.csv",
    "label_vault": Path("sealed") / "v1_8_label_vault.csv",
    "manifest": Path("v1_8_observable_split_manifest.json"),
}

SPLIT_MANIFEST_FIELDS = {
    "version",
    "split_state",
    "schema_id",
    "schema_sha256",
    "record_count",
    "observable_input_sha256",
    "join_key_sha256",
    "label_vault_sha256",
    "predictor_callback_arguments_contain_identifiers",
    "predictor_callback_arguments_contain_labels",
    "label_artifact_separate_from_predictor_input",
    "label_access_isolation_verified",
    "split_manifest_hash_required_for_join",
    "synthetic_only",
    "scientific_thresholds_selected",
}


class ObservableFirewallError(ValueError):
    """Raised when v1.8 cannot preserve an exact observable-only boundary."""


@dataclass(frozen=True)
class LabeledSourceRecord:
    source_record_id: str
    observables: Mapping[str, object]
    evaluation_role: str


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
        raise ObservableFirewallError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_sha256(value: object) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json_loads(text: str, *, source: str) -> object:
    def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in pairs:
            if key in out:
                raise ObservableFirewallError(f"{source}: duplicate JSON key {key!r}")
            out[key] = value
        return out

    def no_nonfinite(value: str) -> object:
        raise ObservableFirewallError(f"{source}: non-finite JSON constant {value!r}")

    try:
        return json.loads(
            text,
            object_pairs_hook=no_duplicate_keys,
            parse_constant=no_nonfinite,
        )
    except ObservableFirewallError:
        raise
    except json.JSONDecodeError as exc:
        raise ObservableFirewallError(f"{source}: malformed JSON: {exc}") from exc


def write_canonical_json(path: str | Path, value: object) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")
    return output


def _strict_finite_unit_float(value: object, *, field: str, source: str) -> float:
    if isinstance(value, bool) or value is None or isinstance(value, str) and not value.strip():
        raise ObservableFirewallError(f"{source}: {field!r} must be a finite numeric value")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ObservableFirewallError(f"{source}: malformed numeric field {field!r}: {value!r}") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ObservableFirewallError(
            f"{source}: {field!r} must satisfy 0 <= value <= 1, got {value!r}"
        )
    if number == 0.0:
        number = 0.0
    return number


def validate_observables(
    values: Mapping[str, object],
    *,
    source: str = "observable record",
) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise ObservableFirewallError(f"{source}: observables must be a mapping")
    supplied = set(values)
    expected = set(OBSERVABLE_FIELDS)
    missing = sorted(expected - supplied)
    extras = sorted(supplied - expected)
    if missing or extras:
        raise ObservableFirewallError(
            f"{source}: exact observable schema required; missing={missing}, extras={extras}"
        )
    return {
        field: _strict_finite_unit_float(values[field], field=field, source=source)
        for field in OBSERVABLE_FIELDS
    }


def validate_blind_case_id(value: object, *, source: str = "blind case") -> str:
    if not isinstance(value, str) or BLIND_CASE_ID_RE.fullmatch(value) is None:
        raise ObservableFirewallError(f"{source}: malformed blind_case_id {value!r}")
    return value


def validate_sha256(value: object, *, field: str, source: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ObservableFirewallError(f"{source}: {field} must be lowercase SHA-256")
    return value


def opaque_case_id(namespace: str, source_record_id: str) -> str:
    if not isinstance(namespace, str) or not namespace or namespace != namespace.strip():
        raise ObservableFirewallError("namespace must be a non-empty trimmed string")
    if (
        not isinstance(source_record_id, str)
        or not source_record_id
        or source_record_id != source_record_id.strip()
    ):
        raise ObservableFirewallError("source_record_id must be a non-empty trimmed string")
    digest = stable_sha256({"namespace": namespace, "source_record_id": source_record_id})
    return f"zg8_{digest[:24]}"


def observable_schema_document() -> dict[str, object]:
    return {
        "version": CURRENT_VERSION,
        "schema_id": SCHEMA_ID,
        "field_policy": "exact_allowlist_unknown_fields_fail_closed",
        "identifier_policy": "blind_case_id_and_row_index_are_transport_only_not_predictor_inputs",
        "features": [
            {
                "name": field,
                "type": "finite_float",
                "minimum": 0.0,
                "maximum": 1.0,
                "stage": "pre_verdict_numeric_measure",
            }
            for field in OBSERVABLE_FIELDS
        ],
        "forbidden_examples": list(FORBIDDEN_FIELD_EXAMPLES),
        "scientific_thresholds_selected": False,
        "known_limitations": [
            "an in-process Python callback is not an operating-system sandbox",
            "a local hash proves artifact integrity but not external chronology",
            "this schema is infrastructure and does not define a scientific scorer",
        ],
    }


def observable_schema_sha256() -> str:
    return stable_sha256(observable_schema_document())


def write_csv_exact(
    path: str | Path,
    *,
    header: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(list(header))
        for row in rows:
            values = list(row)
            if len(values) != len(header):
                raise ObservableFirewallError(f"{output}: row width does not match header")
            writer.writerow(values)
    return output


def read_csv_exact(
    path: str | Path,
    *,
    header: Sequence[str],
    require_rows: bool = True,
) -> list[dict[str, str]]:
    source = Path(path)
    if not source.is_file():
        raise ObservableFirewallError(f"missing CSV: {source}")
    return read_csv_exact_bytes(
        source.read_bytes(),
        source=str(source),
        header=header,
        require_rows=require_rows,
    )


def read_csv_exact_bytes(
    data: bytes,
    *,
    source: str,
    header: Sequence[str],
    require_rows: bool = True,
) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ObservableFirewallError(f"{source}: CSV is not UTF-8") from exc
    reader = csv.reader(text.splitlines())
    try:
        actual_header = next(reader)
    except StopIteration as exc:
        raise ObservableFirewallError(f"{source}: empty CSV") from exc
    if len(actual_header) != len(set(actual_header)):
        raise ObservableFirewallError(f"{source}: duplicate CSV header")
    if actual_header != list(header):
        raise ObservableFirewallError(
            f"{source}: exact header required {list(header)!r}, got {actual_header!r}"
        )
    out: list[dict[str, str]] = []
    for line_number, values in enumerate(reader, start=2):
        if len(values) != len(actual_header):
            raise ObservableFirewallError(f"{source}:{line_number}: wrong column count")
        out.append(dict(zip(actual_header, values, strict=True)))
    if require_rows and not out:
        raise ObservableFirewallError(f"{source}: no data rows")
    return out


def read_observable_inputs(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    if not source.is_file():
        raise ObservableFirewallError(f"missing observable input: {source}")
    return read_observable_inputs_bytes(source.read_bytes(), source=str(source))


def read_observable_inputs_bytes(
    data: bytes,
    *,
    source: str,
) -> list[dict[str, object]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ObservableFirewallError(f"{source}: observable JSONL is not UTF-8") from exc
    if not text or not text.endswith("\n"):
        raise ObservableFirewallError(f"{source}: canonical JSONL must end with newline")
    lines = text.splitlines()
    if any(not line for line in lines):
        raise ObservableFirewallError(f"{source}: blank JSONL rows are forbidden")
    out: list[dict[str, object]] = []
    for expected_index, line in enumerate(lines):
        value = strict_json_loads(line, source=f"{source}:{expected_index + 1}")
        if not isinstance(value, dict) or set(value) != {"observables", "row_index"}:
            raise ObservableFirewallError(f"{source}:{expected_index + 1}: invalid row envelope")
        row_index = value["row_index"]
        if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index != expected_index:
            raise ObservableFirewallError(
                f"{source}:{expected_index + 1}: row_index must be exact sequence starting at zero"
            )
        observables = validate_observables(
            value["observables"],
            source=f"{source}:{expected_index + 1}",
        )
        canonical_row = {"row_index": row_index, "observables": observables}
        if line != canonical_json(canonical_row):
            raise ObservableFirewallError(f"{source}:{expected_index + 1}: non-canonical JSONL row")
        out.append(canonical_row)
    if not out:
        raise ObservableFirewallError(f"{source}: no observable rows")
    return out


def write_observable_label_split(
    out: str | Path,
    records: Iterable[LabeledSourceRecord],
    *,
    namespace: str,
    synthetic_only: bool = True,
) -> dict[str, Path]:
    output_dir = Path(out)
    if type(synthetic_only) is not bool:
        raise ObservableFirewallError("synthetic_only must be an exact boolean")
    values = list(records)
    if not values:
        raise ObservableFirewallError("observable split requires at least one record")
    paths = {key: output_dir / relative for key, relative in SPLIT_FILES.items()}
    existing = [str(path) for path in paths.values() if path.exists()]
    if existing:
        raise ObservableFirewallError(f"refusing to overwrite observable split artifacts: {existing}")

    source_ids: set[str] = set()
    blind_ids: set[str] = set()
    observable_rows: list[dict[str, object]] = []
    join_rows: list[tuple[object, ...]] = []
    label_rows: list[tuple[object, ...]] = []
    for row_index, record in enumerate(values):
        source_id = record.source_record_id
        if source_id in source_ids:
            raise ObservableFirewallError(f"duplicate source_record_id {source_id!r}")
        source_ids.add(source_id)
        observables = validate_observables(record.observables, source=f"record {row_index}")
        role = record.evaluation_role
        if role not in EVALUATION_ROLES:
            raise ObservableFirewallError(f"record {row_index}: unsupported evaluation_role {role!r}")
        blind_id = opaque_case_id(namespace, source_id)
        if blind_id in blind_ids:
            raise ObservableFirewallError(f"opaque blind_case_id collision {blind_id}")
        blind_ids.add(blind_id)
        observable_rows.append({"row_index": row_index, "observables": observables})
        join_rows.append((row_index, blind_id))
        label_rows.append((blind_id, role))

    try:
        paths["observable_inputs"].parent.mkdir(parents=True, exist_ok=True)
        paths["observable_inputs"].write_text(
            "".join(canonical_json(row) + "\n" for row in observable_rows),
            encoding="utf-8",
            newline="\n",
        )
        write_csv_exact(
            paths["join_keys"],
            header=("row_index", "blind_case_id"),
            rows=join_rows,
        )
        write_csv_exact(
            paths["label_vault"],
            header=("blind_case_id", "evaluation_role"),
            rows=label_rows,
        )
        manifest = {
            "version": CURRENT_VERSION,
            "split_state": "SEALED_OBSERVABLE_LABEL_SPLIT",
            "schema_id": SCHEMA_ID,
            "schema_sha256": observable_schema_sha256(),
            "record_count": len(values),
            "observable_input_sha256": sha256_file(paths["observable_inputs"]),
            "join_key_sha256": sha256_file(paths["join_keys"]),
            "label_vault_sha256": sha256_file(paths["label_vault"]),
            "predictor_callback_arguments_contain_identifiers": False,
            "predictor_callback_arguments_contain_labels": False,
            "label_artifact_separate_from_predictor_input": True,
            "label_access_isolation_verified": False,
            "split_manifest_hash_required_for_join": True,
            "synthetic_only": synthetic_only,
            "scientific_thresholds_selected": False,
        }
        write_canonical_json(paths["manifest"], manifest)
    except Exception:
        for path in paths.values():
            if path.is_file():
                path.unlink()
        raise
    return paths
