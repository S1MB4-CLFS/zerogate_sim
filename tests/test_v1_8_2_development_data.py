from __future__ import annotations

import ast
import csv
import inspect
import json
from collections import Counter
from pathlib import Path

import pytest

from zerogate_sim.v1_8_lineage_schema import OBSERVABLE_FIELDS, canonical_json, read_lineage_inputs
from zerogate_sim.v1_8_2_development_fingerprint import build_development_fingerprint
from zerogate_sim.v1_8_2_development_split import (
    ROLES,
    build_development_split,
    build_parser,
    build_recipe_rows,
    main,
)
from zerogate_sim.v1_8_2_numeric_contract import (
    BACKEND_CODES,
    BACKEND_LINEAGES,
    FRAME_RANGES,
    PUBLIC_RECIPE_FIELDS,
    SAMPLE_COUNT,
    TOTAL_CASES,
    TRACE_HEADER,
    TRACE_SCALE,
    DevelopmentDataError,
    generator_contract_document,
    sha256_file,
    stable_sha256,
    strict_json_loads,
    write_exclusive,
)
from zerogate_sim.v1_8_2_observable_extractor import (
    SOURCE_BINDING_FILES,
    extract_case_frames,
    extract_development_observables,
)
from zerogate_sim.v1_8_2_raw_generators import (
    BACKEND_GENERATORS,
    generate_case,
    generate_raw_development_corpus,
)

ROOT = Path(__file__).resolve().parents[1]


def _jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = strict_json_loads(line, source=f"{path}:{line_number}")
        assert isinstance(value, dict)
        assert line == canonical_json(value)
        rows.append(value)
    return rows


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


@pytest.fixture(scope="module")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    root = tmp_path_factory.mktemp("v182-development-data")
    split = build_development_split(root / "split")
    raw = generate_raw_development_corpus(
        split["recipes"],
        root / "rawrun",
        expected_recipe_sha256=sha256_file(split["recipes"]),
    )
    extracted = extract_development_observables(
        raw["manifest"],
        root / "extract",
        expected_raw_manifest_sha256=sha256_file(raw["manifest"]),
    )
    fingerprint = build_development_fingerprint(
        extraction_manifest_path=extracted["extraction_manifest"],
        observable_input_path=extracted["observable_inputs"],
        recipe_path=split["recipes"],
        raw_manifest_path=raw["manifest"],
        source_manifest_path=extracted["source_manifest"],
        out=root / "fingerprint.json",
        expected_extraction_manifest_sha256=sha256_file(extracted["extraction_manifest"]),
        expected_observable_input_sha256=sha256_file(extracted["observable_inputs"]),
        expected_recipe_sha256=sha256_file(split["recipes"]),
        expected_raw_manifest_sha256=sha256_file(raw["manifest"]),
        expected_source_manifest_sha256=sha256_file(extracted["source_manifest"]),
    )
    return {
        "root": root,
        "split": split,
        "raw": raw,
        "extracted": extracted,
        "fingerprint": fingerprint,
    }


def test_generator_contract_is_canonical_and_exact() -> None:
    contract = ROOT / "contracts/v1_8_2_development_generator.json"
    assert contract.read_text(encoding="utf-8") == canonical_json(generator_contract_document()) + "\n"
    document = generator_contract_document()
    assert document["total_cases"] == 144
    assert document["sample_count"] == 1001
    assert document["frame_ranges_inclusive"] == {
        "early": [100, 300],
        "witness": [450, 650],
        "late": [800, 1000],
    }
    assert document["backend_lineages"] == list(BACKEND_LINEAGES)


def test_split_has_exact_144_rows_and_sealed_role_group_balance(corpus: dict[str, object]) -> None:
    split = corpus["split"]
    recipes = _jsonl(split["recipes"])
    labels = _csv(split["label_vault"])
    groups = _csv(split["group_vault"])
    joins = _csv(split["join_keys"])
    assert len(recipes) == len(labels) == len(groups) == len(joins) == TOTAL_CASES
    assert [row["row_index"] for row in recipes] == list(range(TOTAL_CASES))
    assert Counter(row["evaluation_role"] for row in labels) == {role: 48 for role in ROLES}
    assert Counter(row["generator_lineage_id"] for row in groups) == {
        lineage: 36 for lineage in BACKEND_LINEAGES
    }
    paired = Counter(
        (groups[index]["generator_lineage_id"], labels[index]["evaluation_role"])
        for index in range(TOTAL_CASES)
    )
    assert set(paired.values()) == {12}
    assert (split["group_vault"].read_text(encoding="utf-8").splitlines()[0]) == (
        "blind_case_id,generator_lineage_id,atomic_case_id"
    )
    atomic_ids = [row["atomic_case_id"] for row in groups]
    assert len(set(atomic_ids)) == TOTAL_CASES
    assert all(value.startswith("za82_") and len(value) == 29 for value in atomic_ids)


def test_split_receipt_is_returned_and_binds_manifest_root(corpus: dict[str, object]) -> None:
    split = corpus["split"]
    receipt = json.loads(split["receipt"].read_text(encoding="utf-8"))
    manifest = json.loads(split["manifest"].read_text(encoding="utf-8"))
    assert receipt["receipt_state"] == "CALLER_RETAINED_DEVELOPMENT_SPLIT_ROOT"
    assert receipt["split_manifest_sha256"] == sha256_file(split["manifest"])
    assert receipt["recipe_sha256"] == manifest["recipe_sha256"]
    assert receipt["label_vault_sha256"] == manifest["label_vault_sha256"]
    assert receipt["group_vault_sha256"] == manifest["group_vault_sha256"]


def test_public_recipes_are_numeric_regimes_without_roles_ids_or_semantic_names(
    corpus: dict[str, object],
) -> None:
    recipes = _jsonl(corpus["split"]["recipes"])
    assert all(set(row) == set(PUBLIC_RECIPE_FIELDS) for row in recipes)
    forbidden = {
        "truth_role",
        "evaluation_role",
        "candidate_id",
        "blind_case_id",
        "generator_lineage_id",
        "archetype",
        "scenario",
        "profile",
        "expected_trinary",
    }
    assert all(not forbidden.intersection(row) for row in recipes)
    assert all(type(row["regime_code"]) is int for row in recipes)
    manifest = json.loads(corpus["split"]["manifest"].read_text(encoding="utf-8"))
    assert manifest["generator_construction"] == "class_conditioned_controlled_synthetic_recipes"
    assert manifest["observable_extractor_is_label_free"] is True


def test_four_distinct_backends_generate_fixed_point_1001_sample_traces(
    corpus: dict[str, object],
) -> None:
    assert set(BACKEND_GENERATORS) == set(BACKEND_CODES)
    assert len({id(function.__code__) for function in BACKEND_GENERATORS.values()}) == 4
    manifest = json.loads(corpus["raw"]["manifest"].read_text(encoding="utf-8"))
    entries = manifest["entries"]
    assert len(entries) == TOTAL_CASES
    assert Counter(row["backend_code"] for row in entries) == {code: 36 for code in BACKEND_CODES}
    first_hashes = [next(row["trace_sha256"] for row in entries if row["backend_code"] == code) for code in BACKEND_CODES]
    assert len(set(first_hashes)) == 4
    first_trace = corpus["raw"]["raw_dir"] / "row_000000.csv"
    with first_trace.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(TRACE_HEADER)
    assert len(rows) == SAMPLE_COUNT + 1
    assert rows[-1][0] == "1000"
    assert all(value.lstrip("-").isdigit() for row in rows[1:] for value in row)


def test_raw_generation_and_extraction_apis_cannot_receive_sealed_vaults() -> None:
    for function in (generate_raw_development_corpus, extract_development_observables, extract_case_frames):
        parameters = set(inspect.signature(function).parameters)
        assert not {"labels", "label_path", "label_vault", "group_vault", "join_keys"}.intersection(parameters)


def test_generator_and_extractor_import_no_legacy_label_or_future_modules() -> None:
    forbidden = {
        "zerogate_sim.signals",
        "zerogate_sim.gates",
        "zerogate_sim.endurance",
        "zerogate_sim.lineage",
        "zerogate_sim.truth_roles",
        "zerogate_sim.earned_one",
        "zerogate_sim.v1_8_label_join",
        "zerogate_sim.v1_8_3_holdout",
    }
    for relative in (
        "src/zerogate_sim/v1_8_2_raw_generators.py",
        "src/zerogate_sim/v1_8_2_observable_extractor.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not forbidden.intersection(imported)


def test_extraction_binds_exact_inclusive_windows_and_raw_slice_hashes(
    corpus: dict[str, object],
) -> None:
    manifest = json.loads(corpus["extracted"]["extraction_manifest"].read_text(encoding="utf-8"))
    assert manifest["frame_ranges_inclusive"] == {
        name: list(bounds) for name, bounds in FRAME_RANGES.items()
    }
    assert manifest["generator_source_is_class_conditioned"] is True
    assert manifest["extractor_received_or_read_labels_ids_groups"] is False
    entries = manifest["entries"]
    assert len(entries) == TOTAL_CASES
    first = entries[0]
    trace_path = corpus["raw"]["raw_dir"] / "row_000000.csv"
    with trace_path.open("r", encoding="utf-8", newline="") as handle:
        raw_rows = [tuple(int(value) for value in row[1:]) for row in list(csv.reader(handle))[1:]]
    for name, (start, end) in FRAME_RANGES.items():
        assert first["frames"][name]["start_index"] == start
        assert first["frames"][name]["end_index_inclusive"] == end
        assert first["frames"][name]["raw_slice_sha256"] == stable_sha256(
            [list(row) for row in raw_rows[start : end + 1]]
        )


def test_extractor_uses_only_locked_windows() -> None:
    recipe = build_recipe_rows()[0][0]
    samples = [list(row) for row in generate_case(recipe)]
    control = extract_case_frames(samples)
    samples[0][0] += TRACE_SCALE
    assert extract_case_frames(samples) == control
    samples[100][0] += TRACE_SCALE
    assert extract_case_frames(samples) != control


def test_observable_inputs_are_exact_three_by_seven_and_finite(corpus: dict[str, object]) -> None:
    rows = read_lineage_inputs(corpus["extracted"]["observable_inputs"])
    assert len(rows) == TOTAL_CASES
    for row in rows:
        assert len(row["observable_frames"]) == 3
        for frame in row["observable_frames"]:
            assert tuple(frame) == OBSERVABLE_FIELDS
            assert all(0.0 <= float(value) <= 1.0 for value in frame.values())


def test_source_manifest_is_explicitly_class_conditioned_but_extractor_label_free(
    corpus: dict[str, object],
) -> None:
    source = json.loads(corpus["extracted"]["source_manifest"].read_text(encoding="utf-8"))
    assert source["generator_construction"] == "class_conditioned_controlled_synthetic"
    assert source["observable_extraction"] == "label_free_numeric_trace_only"
    assert source["sealed_label_or_group_vault_accessed"] is False
    assert source["declarations_are_hash_bound_not_external_history_proof"] is True
    assert [row["relative_path"] for row in source["bound_source_files"]] == list(
        SOURCE_BINDING_FILES
    )
    for row in source["bound_source_files"]:
        bound = ROOT / row["relative_path"]
        assert row["sha256"] == sha256_file(bound)
        assert row["size_bytes"] == bound.stat().st_size
    artifacts = {row["artifact"]: row for row in source["bound_artifacts"]}
    assert artifacts["raw_manifest"]["sha256"] == sha256_file(corpus["raw"]["manifest"])
    assert artifacts["extraction_manifest"]["sha256"] == sha256_file(
        corpus["extracted"]["extraction_manifest"]
    )
    assert artifacts["observable_inputs"]["sha256"] == sha256_file(
        corpus["extracted"]["observable_inputs"]
    )


def test_fingerprint_is_deterministic_and_reports_duplicate_audit(corpus: dict[str, object]) -> None:
    first = corpus["fingerprint"]
    second = corpus["root"] / "fingerprint_second.json"
    build_development_fingerprint(
        extraction_manifest_path=corpus["extracted"]["extraction_manifest"],
        observable_input_path=corpus["extracted"]["observable_inputs"],
        recipe_path=corpus["split"]["recipes"],
        raw_manifest_path=corpus["raw"]["manifest"],
        source_manifest_path=corpus["extracted"]["source_manifest"],
        out=second,
        expected_extraction_manifest_sha256=sha256_file(
            corpus["extracted"]["extraction_manifest"]
        ),
        expected_observable_input_sha256=sha256_file(corpus["extracted"]["observable_inputs"]),
        expected_recipe_sha256=sha256_file(corpus["split"]["recipes"]),
        expected_raw_manifest_sha256=sha256_file(corpus["raw"]["manifest"]),
        expected_source_manifest_sha256=sha256_file(corpus["extracted"]["source_manifest"]),
    )
    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding="utf-8"))
    assert document["row_count"] == TOTAL_CASES
    assert document["cross_backend_duplicate_count"] == 0
    assert document["labels_or_groups_read"] is False
    assert len(document["fingerprints"]) == TOTAL_CASES
    assert document["recipe_sha256"] == sha256_file(corpus["split"]["recipes"])
    assert document["raw_manifest_sha256"] == sha256_file(corpus["raw"]["manifest"])
    assert document["source_manifest_sha256"] == sha256_file(
        corpus["extracted"]["source_manifest"]
    )
    assert document["raw_recipe_count"] == TOTAL_CASES
    assert document["raw_trace_count"] == TOTAL_CASES
    assert document["raw_observable_count"] == TOTAL_CASES
    assert 1 <= document["effective_observable_count"] <= TOTAL_CASES


def test_same_root_seed_rebuilds_identical_public_and_sealed_split(tmp_path: Path) -> None:
    first = build_development_split(tmp_path / "first")
    second = build_development_split(tmp_path / "second")
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()


def test_exclusive_writer_never_overwrites_or_removes_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "owned.txt"
    target.write_bytes(b"rival")
    with pytest.raises(FileExistsError):
        write_exclusive(target, b"ours")
    assert target.read_bytes() == b"rival"


def test_wrong_recipe_or_raw_hash_fails_closed(corpus: dict[str, object], tmp_path: Path) -> None:
    with pytest.raises(DevelopmentDataError, match="recipe SHA-256 mismatch"):
        generate_raw_development_corpus(
            corpus["split"]["recipes"],
            tmp_path / "raw",
            expected_recipe_sha256="0" * 64,
        )
    with pytest.raises(DevelopmentDataError, match="raw manifest SHA-256 mismatch"):
        extract_development_observables(
            corpus["raw"]["manifest"],
            tmp_path / "extract",
            expected_raw_manifest_sha256="0" * 64,
        )


def test_stdin_free_cli_runs_once_and_prints_retained_roots(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parameters = set(inspect.signature(build_parser).parameters)
    assert parameters == set()
    output = tmp_path / "cli"
    assert main(["--out", str(output)]) == 0
    printed = capsys.readouterr().out
    for token in (
        "split_receipt=",
        "observable_inputs=",
        "source_manifest=",
        "development_fingerprint=",
        "v1_8_1_package_contract_sha256=",
        "v1_8_1_schema_sha256=",
        "v1_8_1_predictor_config_sha256=",
        "v1_8_1_development_plan_sha256=",
    ):
        assert token in printed
    assert "sha256=" in printed
    assert (output / "split/development_split_receipt.json").is_file()
    assert (output / "development_fingerprint.json").is_file()
    with pytest.raises(DevelopmentDataError, match="must not already exist"):
        main(["--out", str(output)])
    assert "seed" not in build_parser().format_help().lower()
