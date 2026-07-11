from __future__ import annotations

import ast
import builtins
import csv
import hashlib
import inspect
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import pytest

from zerogate_sim import v1_8_2_development_evaluator as evaluator_module
from zerogate_sim.v1_8_lineage_schema import (
    canonical_json,
    lineage_input_bytes,
    stable_sha256,
)
from zerogate_sim.v1_8_predictor_package import verify_predictor_package
from zerogate_sim.v1_8_2_development_evaluator import (
    DevelopmentEvaluationError,
    build_parser,
    evaluate_development,
    main,
)
from zerogate_sim.v1_8_2_development_split import build_recipe_rows
from zerogate_sim.v1_8_2_numeric_contract import (
    BACKEND_LINEAGES,
    FRAME_RANGES,
    SAMPLE_COUNT,
    TRACE_HEADER,
    TRACE_SCALE,
    VERSION,
    generator_contract_sha256,
)
from zerogate_sim.v1_8_2_prelabel_freeze import PRELABEL_FILES, freeze_prelabel
from zerogate_sim.v1_8_2_score_registry import MODEL_IDS


ROOT = Path(__file__).resolve().parents[1]
ROLES = ("expresser", "latent", "trap")
ROLE_COUNTS = {role: 48 for role in ROLES}
ARTIFACTS = {
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
SOURCE_BINDING_FILES = (
    "src/zerogate_sim/v1_8_2_numeric_contract.py",
    "src/zerogate_sim/v1_8_2_development_split.py",
    "src/zerogate_sim/v1_8_2_raw_generators.py",
    "src/zerogate_sim/v1_8_2_observable_extractor.py",
    "contracts/v1_8_2_development_generator.json",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _write_json(path: Path, value: object) -> Path:
    return _write_bytes(path, (canonical_json(value) + "\n").encode("utf-8"))


def _csv_bytes(header: Sequence[str], rows: Sequence[Sequence[object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    value = json.loads(text)
    assert isinstance(value, dict)
    assert text == canonical_json(value) + "\n"
    return value


def _blind_id(original: str, *, renamed: bool) -> str:
    if not renamed:
        return original
    return "zg82_" + hashlib.sha256(f"renamed:{original}".encode()).hexdigest()[:24]


def _base_frame(*, strength: float, echo: float, distinction: float) -> dict[str, float]:
    return {
        "strength": strength,
        "distinction": distinction,
        "polarity": 0.95,
        "relation": 0.95,
        "return_observed": 0.95,
        "echo_mimic_score": echo,
        "observed_stability_score": 0.95,
    }


def _observable_frames(role: str, original_index: int) -> list[dict[str, float]]:
    distinction = 0.92 + original_index / 2000.0
    if role == "expresser":
        return [
            _base_frame(strength=0.9, echo=0.1, distinction=distinction)
            for _ in range(3)
        ]
    score = 0.5 if role == "latent" else 0.1
    if original_index % 2 == 0:
        early = _base_frame(strength=score, echo=0.1, distinction=distinction)
    else:
        early = _base_frame(
            strength=0.9,
            echo=1.0 - score,
            distinction=distinction,
        )
    late = _base_frame(strength=0.9, echo=0.1, distinction=distinction)
    return [dict(early), dict(early), late]


def _trace_bytes(original_index: int) -> bytes:
    header = ",".join(TRACE_HEADER) + "\n"
    rows = "".join(
        f"{sample},{original_index},0,0,0\n" for sample in range(SAMPLE_COUNT)
    )
    return (header + rows).encode("utf-8")


def _source_file_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative in SOURCE_BINDING_FILES:
        data = (ROOT / relative).read_bytes()
        records.append(
            {
                "relative_path": relative,
                "sha256": _sha256(data),
                "size_bytes": len(data),
            }
        )
    return records


@dataclass(frozen=True)
class DevelopmentChain:
    root: Path
    observable_source: Path
    recipe: Path
    raw_manifest: Path
    extraction_manifest: Path
    extraction_source_manifest: Path
    development_fingerprint: Path
    split_receipt: Path
    split_manifest: Path
    join_keys: Path
    label_vault: Path
    group_vault: Path
    prelabel_dir: Path
    prelabel_paths: Mapping[str, Path]
    expected_split_receipt_sha256: str
    expected_recipe_sha256: str
    expected_raw_manifest_sha256: str
    expected_extraction_manifest_sha256: str
    expected_extraction_source_manifest_sha256: str
    expected_development_fingerprint_sha256: str
    expected_observable_source_sha256: str
    expected_prelabel_receipt_sha256: str
    expected_v1_8_1_package_contract_sha256: str

    def kwargs(self) -> dict[str, object]:
        return {
            "observable_source_path": self.observable_source,
            "recipe_path": self.recipe,
            "raw_manifest_path": self.raw_manifest,
            "extraction_manifest_path": self.extraction_manifest,
            "extraction_source_manifest_path": self.extraction_source_manifest,
            "development_fingerprint_path": self.development_fingerprint,
            "split_receipt_path": self.split_receipt,
            "split_manifest_path": self.split_manifest,
            "join_keys_path": self.join_keys,
            "label_vault_path": self.label_vault,
            "group_vault_path": self.group_vault,
            "prelabel_dir": self.prelabel_dir,
            "expected_split_receipt_sha256": self.expected_split_receipt_sha256,
            "expected_recipe_sha256": self.expected_recipe_sha256,
            "expected_raw_manifest_sha256": self.expected_raw_manifest_sha256,
            "expected_extraction_manifest_sha256": (
                self.expected_extraction_manifest_sha256
            ),
            "expected_extraction_source_manifest_sha256": (
                self.expected_extraction_source_manifest_sha256
            ),
            "expected_development_fingerprint_sha256": (
                self.expected_development_fingerprint_sha256
            ),
            "expected_observable_source_sha256": (
                self.expected_observable_source_sha256
            ),
            "expected_prelabel_receipt_sha256": (
                self.expected_prelabel_receipt_sha256
            ),
            "expected_v1_8_1_package_contract_sha256": (
                self.expected_v1_8_1_package_contract_sha256
            ),
        }


def _build_chain(
    root: Path,
    *,
    package_contract_sha256: str,
    order: Sequence[int] | None = None,
    rename_ids: bool = False,
    role_transform: Mapping[str, str] | None = None,
    observable_aliases: Mapping[int, int] | None = None,
    join_mode: str = "exact",
) -> DevelopmentChain:
    root.mkdir(parents=True, exist_ok=False)
    base_recipes, base_sealed = build_recipe_rows()
    ordered = tuple(range(144)) if order is None else tuple(order)
    assert sorted(ordered) == list(range(144))
    transforms = dict(role_transform or {})
    aliases = dict(observable_aliases or {})

    recipe_rows: list[dict[str, object]] = []
    observable_rows: list[list[dict[str, float]]] = []
    join_rows: list[tuple[object, ...]] = []
    label_rows: list[tuple[object, ...]] = []
    group_rows: list[tuple[object, ...]] = []
    raw_entries: list[dict[str, object]] = []
    extraction_entries: list[dict[str, object]] = []
    fingerprint_rows: list[dict[str, object]] = []
    fingerprints_by_hash: dict[str, list[tuple[int, int]]] = {}
    raw_root = root / "raw_generation"

    for row_index, original_index in enumerate(ordered):
        original_recipe = base_recipes[original_index]
        original_blind, original_role, lineage, atomic_id = base_sealed[original_index]
        recipe = dict(original_recipe)
        recipe["row_index"] = row_index
        recipe_rows.append(recipe)
        blind_id = _blind_id(original_blind, renamed=rename_ids)
        evaluation_role = transforms.get(original_role, original_role)
        join_rows.append((row_index, blind_id))
        label_rows.append((blind_id, evaluation_role))
        group_rows.append((blind_id, lineage, atomic_id))

        source_index = aliases.get(original_index, original_index)
        source_role = base_sealed[source_index][1]
        frames = _observable_frames(source_role, source_index)
        observable_rows.append(frames)

        trace_data = _trace_bytes(original_index)
        trace_relative = Path("raw") / f"row_{row_index:06d}.csv"
        trace_path = _write_bytes(raw_root / trace_relative, trace_data)
        trace_sha256 = _sha256(trace_data)
        backend_code = int(original_recipe["backend_code"])
        raw_entries.append(
            {
                "backend_code": backend_code,
                "row_index": row_index,
                "sample_count": SAMPLE_COUNT,
                "trace_relative_path": trace_relative.as_posix(),
                "trace_sha256": trace_sha256,
            }
        )
        raw_slice = [[original_index, 0, 0, 0] for _ in range(201)]
        frame_records = {
            name: {
                "end_index_inclusive": end,
                "observable_sha256": stable_sha256(frame),
                "raw_slice_sha256": stable_sha256(raw_slice),
                "start_index": start,
            }
            for (name, (start, end)), frame in zip(
                FRAME_RANGES.items(), frames, strict=True
            )
        }
        extraction_entries.append(
            {
                "backend_code": backend_code,
                "frames": frame_records,
                "row_index": row_index,
                "trace_sha256": trace_sha256,
            }
        )
        observable_sha256 = stable_sha256(frames)
        fingerprint_rows.append(
            {
                "backend_code": backend_code,
                "observable_sha256": observable_sha256,
                "row_index": row_index,
                "trace_sha256": trace_sha256,
            }
        )
        fingerprints_by_hash.setdefault(observable_sha256, []).append(
            (row_index, backend_code)
        )
        assert trace_path.is_file()

    if join_mode == "duplicate_blind_id":
        join_rows[1] = (1, join_rows[0][1])
    elif join_mode == "short":
        join_rows.pop()
    elif join_mode != "exact":
        raise AssertionError(f"unknown join mode: {join_mode}")

    recipe_data = "".join(canonical_json(row) + "\n" for row in recipe_rows).encode()
    recipe_path = _write_bytes(root / "split/public/development_numeric_recipes.jsonl", recipe_data)
    join_path = _write_bytes(
        root / "split/sealed/development_join_keys.csv",
        _csv_bytes(("row_index", "blind_case_id"), join_rows),
    )
    label_path = _write_bytes(
        root / "split/sealed/development_label_vault.csv",
        _csv_bytes(("blind_case_id", "evaluation_role"), label_rows),
    )
    group_path = _write_bytes(
        root / "split/sealed/development_group_vault.csv",
        _csv_bytes(
            ("blind_case_id", "generator_lineage_id", "atomic_case_id"), group_rows
        ),
    )
    split_manifest_document = {
        "version": VERSION,
        "manifest_state": "SEALED_CLASS_CONDITIONED_DEVELOPMENT_SPLIT",
        "generator_contract_id": "zerogate-v1.8.2-development-generators-v1",
        "generator_contract_sha256": generator_contract_sha256(),
        "row_count": 144,
        "cases_per_backend": 36,
        "recipe_sha256": _sha256(recipe_data),
        "join_key_sha256": _sha256(join_path.read_bytes()),
        "label_vault_sha256": _sha256(label_path.read_bytes()),
        "group_vault_sha256": _sha256(group_path.read_bytes()),
        "generator_construction": "class_conditioned_controlled_synthetic_recipes",
        "public_recipes_contain_roles_ids_or_semantic_archetype_names": False,
        "raw_generator_reads_sealed_vaults": False,
        "observable_extractor_is_label_free": True,
        "sealed_vaults_must_not_be_opened_before_score_freeze": True,
    }
    split_manifest_path = _write_json(
        root / "split/development_split_manifest.json", split_manifest_document
    )
    split_receipt_document = {
        "version": VERSION,
        "receipt_state": "CALLER_RETAINED_DEVELOPMENT_SPLIT_ROOT",
        "split_manifest_sha256": _sha256(split_manifest_path.read_bytes()),
        "recipe_sha256": split_manifest_document["recipe_sha256"],
        "join_key_sha256": split_manifest_document["join_key_sha256"],
        "label_vault_sha256": split_manifest_document["label_vault_sha256"],
        "group_vault_sha256": split_manifest_document["group_vault_sha256"],
        "generator_contract_sha256": generator_contract_sha256(),
        "row_count": 144,
        "external_timestamp_proof": False,
    }
    split_receipt_path = _write_json(
        root / "split/development_split_receipt.json", split_receipt_document
    )

    observable_data = lineage_input_bytes(observable_rows)
    observable_path = _write_bytes(
        root / "extraction/predictor/v1_8_2_observable_inputs.jsonl",
        observable_data,
    )
    raw_manifest_document = {
        "version": VERSION,
        "manifest_state": "RAW_DEVELOPMENT_CORPUS_GENERATED_FROM_NUMERIC_RECIPES",
        "generator_contract_sha256": generator_contract_sha256(),
        "recipe_sha256": _sha256(recipe_data),
        "row_count": 144,
        "sample_count_per_row": SAMPLE_COUNT,
        "trace_scale": TRACE_SCALE,
        "entries": raw_entries,
        "generator_input_is_class_conditioned_numeric_recipe": True,
        "generator_reads_sealed_labels_or_groups": False,
        "observable_extractor_policy": "label_free_numeric_trace_only",
    }
    raw_manifest_path = _write_json(
        raw_root / "raw_trace_manifest.json", raw_manifest_document
    )
    raw_manifest_sha256 = _sha256(raw_manifest_path.read_bytes())
    extraction_manifest_document = {
        "version": VERSION,
        "manifest_state": "LABEL_FREE_OBSERVABLE_EXTRACTION_COMPLETE",
        "generator_contract_sha256": generator_contract_sha256(),
        "raw_manifest_sha256": raw_manifest_sha256,
        "observable_input_sha256": _sha256(observable_data),
        "row_count": 144,
        "frame_ranges_inclusive": {
            name: [start, end] for name, (start, end) in FRAME_RANGES.items()
        },
        "entries": extraction_entries,
        "generator_source_is_class_conditioned": True,
        "extractor_received_or_read_labels_ids_groups": False,
        "extractor_input_is_numeric_raw_trace_only": True,
    }
    extraction_manifest_path = _write_json(
        root / "extraction/observable_extraction_manifest.json",
        extraction_manifest_document,
    )
    extraction_manifest_sha256 = _sha256(extraction_manifest_path.read_bytes())
    extraction_source_document = {
        "version": VERSION,
        "manifest_state": "PRELABEL_DEVELOPMENT_SOURCE",
        "raw_manifest_sha256": raw_manifest_sha256,
        "extraction_manifest_sha256": extraction_manifest_sha256,
        "observable_input_sha256": _sha256(observable_data),
        "bound_source_files": _source_file_records(),
        "bound_artifacts": [
            {
                "artifact": "raw_manifest",
                "sha256": raw_manifest_sha256,
                "size_bytes": raw_manifest_path.stat().st_size,
            },
            {
                "artifact": "extraction_manifest",
                "sha256": extraction_manifest_sha256,
                "size_bytes": extraction_manifest_path.stat().st_size,
            },
            {
                "artifact": "observable_inputs",
                "sha256": _sha256(observable_data),
                "size_bytes": len(observable_data),
            },
        ],
        "row_count": 144,
        "generator_construction": "class_conditioned_controlled_synthetic",
        "observable_extraction": "label_free_numeric_trace_only",
        "sealed_label_or_group_vault_accessed": False,
        "declarations_are_hash_bound_not_external_history_proof": True,
    }
    extraction_source_path = _write_json(
        root / "extraction/prelabel_source_manifest.json", extraction_source_document
    )
    extraction_source_sha256 = _sha256(extraction_source_path.read_bytes())

    duplicate_groups = []
    cross_backend_duplicate_count = 0
    for observable_sha256, members in sorted(fingerprints_by_hash.items()):
        backends = sorted({backend for _, backend in members})
        if len(backends) > 1:
            cross_backend_duplicate_count += 1
        elif len(members) > 1:
            duplicate_groups.append(
                {
                    "backend_code": backends[0],
                    "observable_sha256": observable_sha256,
                    "row_indices": [row_index for row_index, _ in members],
                }
            )
    fingerprint_document = {
        "version": VERSION,
        "manifest_state": "PRELABEL_DEVELOPMENT_FINGERPRINT_COMPLETE",
        "extraction_manifest_sha256": extraction_manifest_sha256,
        "observable_input_sha256": _sha256(observable_data),
        "recipe_sha256": _sha256(recipe_data),
        "raw_manifest_sha256": raw_manifest_sha256,
        "source_manifest_sha256": extraction_source_sha256,
        "raw_recipe_count": 144,
        "raw_trace_count": 144,
        "raw_observable_count": 144,
        "effective_observable_count": len(fingerprints_by_hash),
        "row_count": 144,
        "unique_observable_count": len(fingerprints_by_hash),
        "within_backend_duplicate_groups": duplicate_groups,
        "cross_backend_duplicate_count": cross_backend_duplicate_count,
        "observable_identity": (
            "sha256_of_canonical_three_frame_observables_excluding_ids_labels_and_groups"
        ),
        "fingerprints": fingerprint_rows,
        "labels_or_groups_read": False,
    }
    fingerprint_path = _write_json(
        root / "development_fingerprint.json", fingerprint_document
    )
    fingerprint_sha256 = _sha256(fingerprint_path.read_bytes())

    prelabel_dir = root / "prelabel"
    prelabel_paths = freeze_prelabel(
        prelabel_dir,
        observable_source_bytes=observable_data,
        expected_split_receipt_sha256=_sha256(split_receipt_path.read_bytes()),
        expected_extraction_source_manifest_sha256=extraction_source_sha256,
        expected_development_fingerprint_sha256=fingerprint_sha256,
        expected_observable_source_sha256=_sha256(observable_data),
        expected_v1_8_1_package_contract_sha256=package_contract_sha256,
    )
    return DevelopmentChain(
        root=root,
        observable_source=observable_path,
        recipe=recipe_path,
        raw_manifest=raw_manifest_path,
        extraction_manifest=extraction_manifest_path,
        extraction_source_manifest=extraction_source_path,
        development_fingerprint=fingerprint_path,
        split_receipt=split_receipt_path,
        split_manifest=split_manifest_path,
        join_keys=join_path,
        label_vault=label_path,
        group_vault=group_path,
        prelabel_dir=prelabel_dir,
        prelabel_paths=prelabel_paths,
        expected_split_receipt_sha256=_sha256(split_receipt_path.read_bytes()),
        expected_recipe_sha256=_sha256(recipe_data),
        expected_raw_manifest_sha256=raw_manifest_sha256,
        expected_extraction_manifest_sha256=extraction_manifest_sha256,
        expected_extraction_source_manifest_sha256=extraction_source_sha256,
        expected_development_fingerprint_sha256=fingerprint_sha256,
        expected_observable_source_sha256=_sha256(observable_data),
        expected_prelabel_receipt_sha256=_sha256(
            prelabel_paths["receipt"].read_bytes()
        ),
        expected_v1_8_1_package_contract_sha256=package_contract_sha256,
    )


@pytest.fixture(scope="module")
def package_contract_sha256() -> str:
    return verify_predictor_package(ROOT).contract_sha256


@pytest.fixture(scope="module")
def happy_chain(
    tmp_path_factory: pytest.TempPathFactory,
    package_contract_sha256: str,
) -> DevelopmentChain:
    return _build_chain(
        tmp_path_factory.mktemp("v182-evaluator") / "chain",
        package_contract_sha256=package_contract_sha256,
    )


@pytest.fixture(scope="module")
def happy_evaluation(
    tmp_path_factory: pytest.TempPathFactory,
    happy_chain: DevelopmentChain,
) -> dict[str, Path]:
    return evaluate_development(
        tmp_path_factory.mktemp("v182-evaluator-result") / "evaluation",
        **happy_chain.kwargs(),
    )


def _assert_artifact_set(paths: Mapping[str, Path]) -> None:
    assert set(paths) == set(ARTIFACTS)
    assert {key: path.name for key, path in paths.items()} == ARTIFACTS
    output = next(iter(paths.values())).parent
    assert {path.name for path in output.iterdir()} == set(ARTIFACTS.values())
    for path in paths.values():
        _read_json(path)


def _semantic_text_read_observer(
    monkeypatch: pytest.MonkeyPatch,
    chain: DevelopmentChain,
) -> list[Path]:
    watched = {chain.label_vault.resolve(), chain.group_vault.resolve()}
    reads: list[Path] = []
    original_path_open = Path.open
    original_builtin_open = builtins.open
    original_parse_csv = evaluator_module._parse_csv

    def record(path_value: object, mode: object) -> None:
        if "r" not in str(mode) or "b" in str(mode):
            return
        try:
            candidate = Path(path_value).resolve()  # type: ignore[arg-type]
        except (TypeError, OSError):
            return
        if candidate in watched:
            reads.append(candidate)

    def observing_path_open(self: Path, *args: object, **kwargs: object):
        mode = args[0] if args else kwargs.get("mode", "r")
        record(self, mode)
        return original_path_open(self, *args, **kwargs)

    def observing_builtin_open(
        file: object,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ):
        record(file, mode)
        return original_builtin_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observing_path_open)
    monkeypatch.setattr(builtins, "open", observing_builtin_open)

    def observing_parse_csv(
        data: bytes,
        *,
        header: Sequence[str],
        source: str,
    ) -> list[list[str]]:
        if source in {"label vault", "group vault"}:
            reads.append(Path(source))
        return original_parse_csv(data, header=header, source=source)

    monkeypatch.setattr(evaluator_module, "_parse_csv", observing_parse_csv)
    return reads


def test_root_api_and_cli_have_exact_authority_surface_and_no_holdout() -> None:
    expected = {
        "out",
        "observable_source_path",
        "recipe_path",
        "raw_manifest_path",
        "extraction_manifest_path",
        "extraction_source_manifest_path",
        "development_fingerprint_path",
        "split_receipt_path",
        "split_manifest_path",
        "join_keys_path",
        "label_vault_path",
        "group_vault_path",
        "prelabel_dir",
        "expected_split_receipt_sha256",
        "expected_recipe_sha256",
        "expected_raw_manifest_sha256",
        "expected_extraction_manifest_sha256",
        "expected_extraction_source_manifest_sha256",
        "expected_development_fingerprint_sha256",
        "expected_observable_source_sha256",
        "expected_prelabel_receipt_sha256",
        "expected_v1_8_1_package_contract_sha256",
    }
    assert set(inspect.signature(evaluate_development).parameters) == expected
    assert "holdout" not in " ".join(expected).lower()
    actions = build_parser()._actions
    assert all("holdout" not in action.dest.lower() for action in actions)
    assert all(
        "holdout" not in option.lower()
        for action in actions
        for option in action.option_strings
    )


def test_evaluator_ast_import_firewall() -> None:
    source = ROOT / "src/zerogate_sim/v1_8_2_development_evaluator.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "zerogate_sim.v1_8_2_development_split",
        "zerogate_sim.v1_8_2_raw_generators",
        "zerogate_sim.v1_8_2_observable_extractor",
        "zerogate_sim.v1_8_2_development_fingerprint",
        "zerogate_sim.v1_8_2_prelabel_freeze",
        "zerogate_sim.v1_8_2_score_registry",
        "zerogate_sim.v1_8_lineage_predictor",
        "zerogate_sim.v1_8_predictor_package",
    }
    assert imported.isdisjoint(forbidden)


def test_happy_evaluation_has_exact_join_selection_and_progression(
    happy_evaluation: Mapping[str, Path],
) -> None:
    _assert_artifact_set(happy_evaluation)
    join = _read_json(happy_evaluation["join_audit"])
    assert join["status"] == "VALID_EXACT_JOIN"
    assert join["raw_case_count"] == 144
    assert join["generator_lineage_count"] == 4
    assert join["unique_blind_case_id_count"] == 144
    assert join["unique_atomic_case_id_count"] == 144
    assert join["role_counts_by_lineage"] == {
        lineage: {role: 12 for role in ROLES} for lineage in sorted(BACKEND_LINEAGES)
    }

    duplicate = _read_json(happy_evaluation["duplicate_audit"])
    assert duplicate["status"] == "VALID_DUPLICATE_AUDIT"
    assert duplicate["raw_case_count"] == duplicate["unique_observable_count"] == 144
    assert duplicate["effective_case_count"] == 144
    selection = _read_json(happy_evaluation["selection"])
    assert selection["selected_option_id"] == "medium_hold"
    assert selection["selected_threshold"] == {
        "option_id": "medium_hold",
        "resist_max": 0.3,
        "crown_min": 0.7,
    }
    assert selection["boundary_semantics"] == {
        "resist": "score <= resist_max",
        "hold": "resist_max < score < crown_min",
        "crown": "score >= crown_min",
    }
    assert selection["selected_threshold_contract"]["option"] == selection[
        "selected_threshold"
    ]
    assert selection["selected_threshold_contract"]["development_only"] is True
    assert (
        selection["nested_leave_one_generator_lineage_out"]["status"]
        == "VALID_NESTED_SELECTION"
    )
    assert set(selection["per_lineage_oof_metrics"]) == set(BACKEND_LINEAGES)

    result = _read_json(happy_evaluation["result"])
    assert result["decision_status"] == "READY_FOR_V1_8_3_CONTRACT_ONLY"
    assert result["progression_authorized"] is True
    assert result["selected_option_id"] == "medium_hold"
    assert result["raw_case_count"] == result["effective_case_count"] == 144
    assert result["generator_lineage_count"] == 4
    assert result["holdout_material_accessed"] is False
    assert result["development_only"] is True
    assert result["independent_empirical_data_claimed"] is False
    assert result["failure_capability_passed"] is True
    assert result["comparison_requirement_passed"] is True


def test_all_baselines_ablations_constants_uncertainty_and_failure_fixtures_reported(
    happy_evaluation: Mapping[str, Path],
) -> None:
    comparisons = _read_json(happy_evaluation["comparisons"])
    assert len(comparisons["simple_baselines"]) == 6
    assert len(comparisons["ablations"]) == 2
    assert len(comparisons["constant_controls"]) == 3
    assert comparisons["comparison_requirement_passed"] is True
    text = canonical_json(comparisons)
    assert all(model_id in text for model_id in MODEL_IDS if model_id != "primary_prior_touch")
    assert (
        _read_json(happy_evaluation["selection"])["primary_model_id"]
        == "primary_prior_touch"
    )
    assert all(
        row["primary_strictly_better_retuned"] is True
        and row["requirement_passed"] is True
        and "frozen_primary_thresholds" not in row
        for row in comparisons["simple_baselines"].values()
    )
    assert all(
        row["primary_strictly_better_frozen"] is True
        and row["primary_strictly_better_retuned"] is True
        and row["necessity_requirement_passed"] is True
        for row in comparisons["ablations"].values()
    )
    assert all(
        str(row["status"]).startswith("INVALID_ALWAYS_")
        and row["primary_strictly_better"] is True
        and row["requirement_passed"] is True
        for row in comparisons["constant_controls"].values()
    )

    uncertainty = _read_json(happy_evaluation["uncertainty"])
    assert uncertainty["sampling_unit"] == "generator_lineage_id"
    assert uncertainty["resamples"] == 2000
    assert uncertainty["seed"] == 18122001
    assert all(
        row["interval"]["lower_index"] == 49
        and row["interval"]["upper_index"] == 1950
        for row in uncertainty["primary_metric_intervals"].values()
    )
    failure = _read_json(happy_evaluation["failure_capability"])
    assert failure["passed"] is True
    assert len(failure["fixtures"]) == 6
    assert all(row["passed"] is True for row in failure["fixtures"])
    assert {row["fixture_name"] for row in failure["fixtures"]} == {
        "balanced_fixture",
        "injected_false_crown",
        "always_hold",
        "always_crown",
        "always_resist",
        "constant_primary_score",
    }


def test_manifest_and_receipt_transitively_bind_all_nine_artifacts(
    happy_evaluation: Mapping[str, Path],
) -> None:
    manifest = _read_json(happy_evaluation["manifest"])
    receipt = _read_json(happy_evaluation["receipt"])
    bound = manifest["artifacts"]
    assert set(bound) == {
        "join_audit",
        "duplicate_audit",
        "selection",
        "comparisons",
        "uncertainty",
        "failure_capability",
        "result",
    }
    for key, record in bound.items():
        assert record["filename"] == ARTIFACTS[key]
        assert record["sha256"] == _sha256(happy_evaluation[key].read_bytes())
        assert record["size_bytes"] == happy_evaluation[key].stat().st_size
    assert receipt["manifest_sha256"] == _sha256(
        happy_evaluation["manifest"].read_bytes()
    )
    assert receipt["result_sha256"] == _sha256(happy_evaluation["result"].read_bytes())
    assert receipt["selection_sha256"] == _sha256(
        happy_evaluation["selection"].read_bytes()
    )


@pytest.mark.parametrize(
    "field",
    [
        "expected_split_receipt_sha256",
        "expected_recipe_sha256",
        "expected_raw_manifest_sha256",
        "expected_extraction_manifest_sha256",
        "expected_extraction_source_manifest_sha256",
        "expected_development_fingerprint_sha256",
        "expected_observable_source_sha256",
        "expected_prelabel_receipt_sha256",
        "expected_v1_8_1_package_contract_sha256",
    ],
)
def test_wrong_authority_hash_fails_before_semantic_vault_parse_and_writes_nothing(
    tmp_path: Path,
    happy_chain: DevelopmentChain,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    reads = _semantic_text_read_observer(monkeypatch, happy_chain)
    kwargs = happy_chain.kwargs()
    kwargs[field] = "0" * 64
    output = tmp_path / "rejected"
    with pytest.raises(DevelopmentEvaluationError, match="INVALID_ARTIFACT_OR_RECEIPT"):
        evaluate_development(output, **kwargs)
    assert reads == []
    assert not output.exists()


@pytest.mark.parametrize(
    "artifact",
    ["split_manifest", "join_keys", "label_vault", "raw_trace", "prelabel_scores"],
)
def test_artifact_tamper_fails_before_semantic_vault_parse_and_writes_nothing(
    tmp_path: Path,
    happy_chain: DevelopmentChain,
    monkeypatch: pytest.MonkeyPatch,
    artifact: str,
) -> None:
    paths = {
        "split_manifest": happy_chain.split_manifest,
        "join_keys": happy_chain.join_keys,
        "label_vault": happy_chain.label_vault,
        "raw_trace": happy_chain.raw_manifest.parent / "raw/row_000000.csv",
        "prelabel_scores": happy_chain.prelabel_paths["scores"],
    }
    target = paths[artifact]
    original = target.read_bytes()
    target.write_bytes(original + b"tamper")
    reads = _semantic_text_read_observer(monkeypatch, happy_chain)
    output = tmp_path / "rejected"
    try:
        with pytest.raises(
            DevelopmentEvaluationError, match="INVALID_ARTIFACT_OR_RECEIPT"
        ):
            evaluate_development(output, **happy_chain.kwargs())
        assert reads == []
        assert not output.exists()
    finally:
        monkeypatch.undo()
        target.write_bytes(original)


@pytest.mark.parametrize(
    ("join_mode", "expected_token"),
    [("duplicate_blind_id", "INVALID"), ("short", "INVALID")],
)
def test_parseable_join_key_or_cardinality_failure_writes_invalid_nine_file_decision(
    tmp_path: Path,
    package_contract_sha256: str,
    join_mode: str,
    expected_token: str,
) -> None:
    chain = _build_chain(
        tmp_path / "chain",
        package_contract_sha256=package_contract_sha256,
        join_mode=join_mode,
    )
    paths = evaluate_development(tmp_path / "evaluation", **chain.kwargs())
    _assert_artifact_set(paths)
    assert expected_token in str(_read_json(paths["join_audit"])["status"])
    result = _read_json(paths["result"])
    assert result["progression_authorized"] is False
    assert "INVALID" in str(result["decision_status"])


def test_benign_duplicate_is_deduplicated_but_conflicting_alias_is_invalid(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    duplicate = _build_chain(
        tmp_path / "duplicate_chain",
        package_contract_sha256=package_contract_sha256,
        observable_aliases={1: 0},
    )
    duplicate_paths = evaluate_development(
        tmp_path / "duplicate_evaluation", **duplicate.kwargs()
    )
    duplicate_audit = _read_json(duplicate_paths["duplicate_audit"])
    assert duplicate_audit["status"] == "VALID_DUPLICATE_AUDIT"
    assert duplicate_audit["duplicate_representation_count"] == 1
    assert duplicate_audit["effective_case_count"] == 143

    alias = _build_chain(
        tmp_path / "alias_chain",
        package_contract_sha256=package_contract_sha256,
        observable_aliases={12: 0},
    )
    alias_paths = evaluate_development(tmp_path / "alias_evaluation", **alias.kwargs())
    _assert_artifact_set(alias_paths)
    assert (
        _read_json(alias_paths["duplicate_audit"])["status"]
        == "INVALID_OBSERVATIONAL_ALIASING"
    )
    assert _read_json(alias_paths["result"])["progression_authorized"] is False


def test_cross_generator_lineage_overlap_is_an_artifact_generated_invalid_decision(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    chain = _build_chain(
        tmp_path / "chain",
        package_contract_sha256=package_contract_sha256,
        observable_aliases={36: 0},
    )
    paths = evaluate_development(tmp_path / "evaluation", **chain.kwargs())
    _assert_artifact_set(paths)
    assert (
        _read_json(paths["duplicate_audit"])["status"]
        == "INVALID_GENERATOR_LINEAGE_OVERLAP"
    )
    assert _read_json(paths["result"])["progression_authorized"] is False


def test_row_and_identifier_permutations_preserve_semantic_reports(
    tmp_path: Path,
    package_contract_sha256: str,
    happy_evaluation: Mapping[str, Path],
) -> None:
    variants = (
        _build_chain(
            tmp_path / "row_chain",
            package_contract_sha256=package_contract_sha256,
            order=tuple(reversed(range(144))),
        ),
        _build_chain(
            tmp_path / "id_chain",
            package_contract_sha256=package_contract_sha256,
            rename_ids=True,
        ),
    )
    for index, chain in enumerate(variants):
        paths = evaluate_development(tmp_path / f"evaluation_{index}", **chain.kwargs())
        for key in ("selection", "comparisons", "uncertainty", "failure_capability"):
            assert paths[key].read_bytes() == happy_evaluation[key].read_bytes()


def test_label_permutation_changes_evaluation_but_not_frozen_scores_or_predictions(
    tmp_path: Path,
    package_contract_sha256: str,
    happy_chain: DevelopmentChain,
    happy_evaluation: Mapping[str, Path],
) -> None:
    permuted = _build_chain(
        tmp_path / "permuted_chain",
        package_contract_sha256=package_contract_sha256,
        role_transform={"expresser": "trap", "trap": "expresser", "latent": "latent"},
    )
    assert permuted.prelabel_paths["scores"].read_bytes() == happy_chain.prelabel_paths[
        "scores"
    ].read_bytes()
    assert permuted.prelabel_paths[
        "prediction_cube"
    ].read_bytes() == happy_chain.prelabel_paths["prediction_cube"].read_bytes()
    paths = evaluate_development(tmp_path / "evaluation", **permuted.kwargs())
    assert paths["selection"].read_bytes() != happy_evaluation["selection"].read_bytes()
    assert _read_json(paths["result"])["progression_authorized"] is False


def test_output_overwrite_is_refused_without_changing_existing_artifacts(
    tmp_path: Path,
    happy_chain: DevelopmentChain,
) -> None:
    output = tmp_path / "evaluation"
    paths = evaluate_development(output, **happy_chain.kwargs())
    originals = {key: path.read_bytes() for key, path in paths.items()}
    with pytest.raises(DevelopmentEvaluationError, match="overwrite|existing|empty"):
        evaluate_development(output, **happy_chain.kwargs())
    assert {key: path.read_bytes() for key, path in paths.items()} == originals


def test_cli_runs_exact_evaluation_without_holdout(
    tmp_path: Path,
    happy_chain: DevelopmentChain,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "cli"
    args = [
        "--out",
        str(output),
        "--observable-source",
        str(happy_chain.observable_source),
        "--recipe",
        str(happy_chain.recipe),
        "--raw-manifest",
        str(happy_chain.raw_manifest),
        "--extraction-manifest",
        str(happy_chain.extraction_manifest),
        "--extraction-source-manifest",
        str(happy_chain.extraction_source_manifest),
        "--development-fingerprint",
        str(happy_chain.development_fingerprint),
        "--split-receipt",
        str(happy_chain.split_receipt),
        "--split-manifest",
        str(happy_chain.split_manifest),
        "--join-keys",
        str(happy_chain.join_keys),
        "--label-vault",
        str(happy_chain.label_vault),
        "--group-vault",
        str(happy_chain.group_vault),
        "--prelabel-dir",
        str(happy_chain.prelabel_dir),
    ]
    for field, value in happy_chain.kwargs().items():
        if field.startswith("expected_"):
            option = field.removeprefix("expected_").replace("_", "-")
            args.extend(("--" + option, str(value)))
    assert main(args) == 0
    assert {path.name for path in output.iterdir()} == set(ARTIFACTS.values())
    printed = capsys.readouterr().out
    assert "decision_status=READY_FOR_V1_8_3_CONTRACT_ONLY" in printed
    assert "evaluation_receipt_sha256=" in printed
    assert "holdout" not in printed.lower()
