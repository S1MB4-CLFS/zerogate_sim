from __future__ import annotations

import csv
import hashlib
import inspect
import io
import json
from pathlib import Path

import pytest

from zerogate_sim import v1_8_2_prelabel_freeze as prelabel_module
from zerogate_sim.v1_8_lineage_schema import (
    OBSERVABLE_FIELDS,
    canonical_json,
    lineage_input_bytes,
)
from zerogate_sim.v1_8_predictor_package import verify_predictor_package
from zerogate_sim.v1_8_2_prelabel_freeze import (
    PRELABEL_FILE_ALLOWLIST,
    PRELABEL_FILES,
    PrelabelFirewallError,
    freeze_prelabel,
    verify_prelabel,
)
from zerogate_sim.v1_8_2_score_registry import (
    CONSTANT_MODEL_IDS,
    CONTINUOUS_MODEL_IDS,
    THRESHOLD_OPTIONS,
    prediction_cube_rows,
    score_registry_rows,
)


ROOT = Path(__file__).resolve().parents[1]
SPLIT_RECEIPT_SHA256 = "1" * 64
EXTRACTION_SOURCE_MANIFEST_SHA256 = "2" * 64
DEVELOPMENT_FINGERPRINT_SHA256 = "3" * 64


def _frame(value: float, *, echo: float = 0.0) -> dict[str, float]:
    frame = {field: value for field in OBSERVABLE_FIELDS}
    frame["echo_mimic_score"] = echo
    return frame


def _source_bytes() -> bytes:
    return lineage_input_bytes(
        [
            [_frame(0.9), _frame(0.8), _frame(0.85)],
            [_frame(0.2), _frame(0.7, echo=0.1), _frame(0.95, echo=0.8)],
        ]
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@pytest.fixture(scope="module")
def package_contract_sha256() -> str:
    return verify_predictor_package(ROOT).contract_sha256


def _freeze(
    tmp_path: Path,
    package_contract_sha256: str,
    *,
    name: str = "prelabel",
    source: bytes | None = None,
) -> tuple[bytes, Path, dict[str, Path], str]:
    observable_source = _source_bytes() if source is None else source
    output = tmp_path / name
    paths = freeze_prelabel(
        output,
        observable_source_bytes=observable_source,
        expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
        expected_extraction_source_manifest_sha256=(
            EXTRACTION_SOURCE_MANIFEST_SHA256
        ),
        expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
        expected_observable_source_sha256=_sha256(observable_source),
        expected_v1_8_1_package_contract_sha256=package_contract_sha256,
    )
    receipt_sha256 = _sha256(paths["receipt"].read_bytes())
    return observable_source, output, paths, receipt_sha256


def _verify(
    source: bytes,
    output: Path,
    package_contract_sha256: str,
    receipt_sha256: str,
) -> dict[str, object]:
    return verify_prelabel(
        output,
        observable_source_bytes=source,
        expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
        expected_extraction_source_manifest_sha256=(
            EXTRACTION_SOURCE_MANIFEST_SHA256
        ),
        expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
        expected_observable_source_sha256=_sha256(source),
        expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        expected_prelabel_receipt_sha256=receipt_sha256,
    )


def _csv_rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


def test_prelabel_api_has_no_input_root_or_sealed_path_surface() -> None:
    assert set(inspect.signature(freeze_prelabel).parameters) == {
        "out",
        "observable_source_bytes",
        "expected_split_receipt_sha256",
        "expected_extraction_source_manifest_sha256",
        "expected_development_fingerprint_sha256",
        "expected_observable_source_sha256",
        "expected_v1_8_1_package_contract_sha256",
    }
    assert set(inspect.signature(verify_prelabel).parameters) == {
        "out",
        "observable_source_bytes",
        "expected_split_receipt_sha256",
        "expected_extraction_source_manifest_sha256",
        "expected_development_fingerprint_sha256",
        "expected_observable_source_sha256",
        "expected_v1_8_1_package_contract_sha256",
        "expected_prelabel_receipt_sha256",
    }
    assert PRELABEL_FILE_ALLOWLIST == (
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
    forbidden = ("label", "group", "sealed", "holdout", "input_path", "root")
    for function in (freeze_prelabel, verify_prelabel):
        assert not any(
            token in parameter.replace("prelabel", "")
            for parameter in inspect.signature(function).parameters
            for token in forbidden
        )


def test_cli_reads_observables_from_stdin_and_accepts_no_input_path(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = prelabel_module.build_parser()
    destinations = {action.dest for action in parser._actions}
    assert not any(
        token in destination
        for destination in destinations
        for token in ("input_path", "label", "group", "sealed", "holdout", "root")
    )
    source = _source_bytes()

    class BinaryStdin:
        buffer = io.BytesIO(source)

    monkeypatch.setattr(prelabel_module.sys, "stdin", BinaryStdin())
    output = tmp_path / "cli"
    result = prelabel_module.main(
        [
            "--out",
            str(output),
            "--split-receipt-sha256",
            SPLIT_RECEIPT_SHA256,
            "--extraction-source-manifest-sha256",
            EXTRACTION_SOURCE_MANIFEST_SHA256,
            "--development-fingerprint-sha256",
            DEVELOPMENT_FINGERPRINT_SHA256,
            "--observable-source-sha256",
            _sha256(source),
            "--v1-8-1-package-contract-sha256",
            package_contract_sha256,
        ]
    )
    assert result == 0
    assert {path.name for path in output.iterdir()} == {
        relative.name for relative in PRELABEL_FILES.values()
    }
    assert "prelabel receipt sha256:" in capsys.readouterr().out


def test_freezes_every_score_option_and_constant_before_join(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source, output, paths, receipt_sha256 = _freeze(
        tmp_path, package_contract_sha256
    )
    assert paths == {key: output / relative for key, relative in PRELABEL_FILES.items()}
    assert {path.name for path in output.iterdir()} == {
        relative.name for relative in PRELABEL_FILES.values()
    }

    scores = _csv_rows(paths["scores"].read_bytes())
    predictions = _csv_rows(paths["prediction_cube"].read_bytes())
    assert len(scores) == 2 * len(CONTINUOUS_MODEL_IDS) == 18
    assert len(predictions) == 2 * (
        len(CONTINUOUS_MODEL_IDS) * len(THRESHOLD_OPTIONS)
        + len(CONSTANT_MODEL_IDS)
    ) == 60
    for row_index in ("0", "1"):
        score_slice = [row for row in scores if row["row_index"] == row_index]
        prediction_slice = [
            row for row in predictions if row["row_index"] == row_index
        ]
        assert [row["model_id"] for row in score_slice] == list(
            CONTINUOUS_MODEL_IDS
        )
        assert [
            (row["model_id"], row["option_id"])
            for row in prediction_slice
        ] == [
            (model_id, option.option_id)
            for model_id in CONTINUOUS_MODEL_IDS
            for option in THRESHOLD_OPTIONS
        ] + [(model_id, "constant") for model_id in CONSTANT_MODEL_IDS]

    options = json.loads(paths["options"].read_text(encoding="utf-8"))
    assert options["threshold_options"] == [option.to_dict() for option in THRESHOLD_OPTIONS]
    assert options["selected_option_id"] is None
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["caller_retained_split_receipt_sha256"] == SPLIT_RECEIPT_SHA256
    assert (
        manifest["caller_retained_extraction_source_manifest_sha256"]
        == EXTRACTION_SOURCE_MANIFEST_SHA256
    )
    assert (
        manifest["caller_retained_development_fingerprint_sha256"]
        == DEVELOPMENT_FINGERPRINT_SHA256
    )
    assert manifest["observable_source_sha256"] == _sha256(source)
    assert manifest["v1_8_1_package_contract_sha256"] == package_contract_sha256
    assert manifest["semantic_label_or_group_reads"] == 0
    assert manifest["registry_callback_contains_case_identifiers"] is False
    assert manifest["registry_callback_contains_labels_or_groups"] is False
    assert manifest["runtime_loaded_from_verified_source_snapshot"] is True
    assert manifest["decision_rule_selected"] is False
    assert manifest["external_timestamp_proof"] is False
    assert [row["relative_path"] for row in manifest["package_files"]] == list(
        PRELABEL_FILE_ALLOWLIST
    )

    verified = _verify(
        source, output, package_contract_sha256, receipt_sha256
    )
    assert verified["verified"] is True
    assert verified["semantic_label_or_group_reads"] == 0


def test_registry_callbacks_are_observable_only_and_metadata_free() -> None:
    frames = tuple(_frame(value) for value in (0.2, 0.6, 0.9))
    score_rows = score_registry_rows(frames)
    prediction_rows = prediction_cube_rows(frames)
    assert all(set(row) == {"model_id", "score"} for row in score_rows)
    assert all(
        set(row) == {"model_id", "option_id", "score", "proposed_trinary"}
        for row in prediction_rows
    )
    forbidden = {
        "row_index",
        "blind_case_id",
        "generator_lineage_id",
        "evaluation_role",
        "label",
        "group_id",
        "seed",
        "scenario",
    }
    assert all(not (set(row) & forbidden) for row in (*score_rows, *prediction_rows))


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "label",
        "evaluation_role",
        "blind_case_id",
        "generator_lineage_id",
        "seed",
        "scenario",
    ],
)
def test_forbidden_observable_fields_fail_closed(
    tmp_path: Path,
    package_contract_sha256: str,
    forbidden_field: str,
) -> None:
    frames = [_frame(0.5), _frame(0.6), _frame(0.7)]
    frames[0][forbidden_field] = 0.0
    raw = (
        canonical_json({"observable_frames": frames, "row_index": 0}) + "\n"
    ).encode("utf-8")
    with pytest.raises(PrelabelFirewallError, match="observable source is invalid"):
        freeze_prelabel(
            tmp_path / "rejected",
            observable_source_bytes=raw,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(raw),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )


def test_label_permutation_and_holdout_sentinels_are_never_read_or_changed(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_labels = tmp_path / "sealed_label_vault_a.csv"
    permuted_labels = tmp_path / "sealed_label_vault_b.csv"
    holdout_sentinel = tmp_path / "frozen_holdout_DO_NOT_OPEN.bin"
    sentinel_values = {
        first_labels: b"case,role\na,earned\nb,hold\nc,resist\n",
        permuted_labels: b"case,role\na,resist\nb,earned\nc,hold\n",
        holdout_sentinel: b"HOLDOUT-SENTINEL-MUST-REMAIN-UNTOUCHED",
    }
    for path, data in sentinel_values.items():
        path.write_bytes(data)
    watched = {path.resolve() for path in sentinel_values}
    reads: list[Path] = []
    original_open = Path.open

    def observing_open(self: Path, *args: object, **kwargs: object):
        mode = str(args[0] if args else kwargs.get("mode", "r"))
        if self.resolve() in watched and "r" in mode:
            reads.append(self.resolve())
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observing_open)
    source, first_output, first_paths, first_receipt = _freeze(
        tmp_path, package_contract_sha256, name="first"
    )
    _, second_output, second_paths, second_receipt = _freeze(
        tmp_path, package_contract_sha256, name="second", source=source
    )
    _verify(source, first_output, package_contract_sha256, first_receipt)
    _verify(source, second_output, package_contract_sha256, second_receipt)
    assert reads == []
    assert {
        key: first_paths[key].read_bytes() for key in PRELABEL_FILES
    } == {key: second_paths[key].read_bytes() for key in PRELABEL_FILES}
    monkeypatch.undo()
    assert {path: path.read_bytes() for path in sentinel_values} == sentinel_values


def test_in_memory_scorer_and_v181_verifier_monkeypatches_do_not_change_freeze(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, _, reference, _ = _freeze(
        tmp_path, package_contract_sha256, name="reference"
    )
    from zerogate_sim import v1_8_2_score_registry as registry_module
    from zerogate_sim import v1_8_predictor_package as package_module

    def forbidden_call(*args: object, **kwargs: object) -> object:
        raise AssertionError("ordinary imported function must not execute")

    monkeypatch.setattr(registry_module, "score_registry_rows", forbidden_call)
    monkeypatch.setattr(registry_module, "prediction_cube_rows", forbidden_call)
    monkeypatch.setattr(package_module, "verify_predictor_package", forbidden_call)
    _, _, patched, receipt_sha256 = _freeze(
        tmp_path, package_contract_sha256, name="patched", source=source
    )
    assert {
        key: reference[key].read_bytes() for key in PRELABEL_FILES
    } == {key: patched[key].read_bytes() for key in PRELABEL_FILES}
    assert len(receipt_sha256) == 64


@pytest.mark.parametrize("artifact", tuple(PRELABEL_FILES))
def test_every_artifact_tamper_fails_closed(
    tmp_path: Path,
    package_contract_sha256: str,
    artifact: str,
) -> None:
    source, output, paths, receipt_sha256 = _freeze(
        tmp_path, package_contract_sha256
    )
    paths[artifact].write_bytes(paths[artifact].read_bytes() + b"tamper")
    with pytest.raises(PrelabelFirewallError):
        _verify(source, output, package_contract_sha256, receipt_sha256)


def test_noncanonical_receipt_fails_even_with_attacker_supplied_new_hash(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source, output, paths, _ = _freeze(tmp_path, package_contract_sha256)
    receipt = paths["receipt"].read_text(encoding="utf-8").rstrip("\n")
    noncanonical = (receipt[:-1] + ',"version":"v1.8.2-alpha"}\n').encode()
    paths["receipt"].write_bytes(noncanonical)
    with pytest.raises(PrelabelFirewallError, match="duplicate JSON key"):
        _verify(source, output, package_contract_sha256, _sha256(noncanonical))


def test_extra_artifact_and_overwrite_are_refused_without_changing_originals(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source, output, paths, receipt_sha256 = _freeze(
        tmp_path, package_contract_sha256
    )
    originals = {key: path.read_bytes() for key, path in paths.items()}
    with pytest.raises(PrelabelFirewallError, match="existing prelabel output"):
        freeze_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )
    assert {key: path.read_bytes() for key, path in paths.items()} == originals
    (output / "rival.tmp").write_bytes(b"rival")
    with pytest.raises(PrelabelFirewallError, match="exact artifacts"):
        _verify(source, output, package_contract_sha256, receipt_sha256)


def test_all_caller_retained_hashes_are_mandatory_and_bound(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source = _source_bytes()
    base = {
        "observable_source_bytes": source,
        "expected_split_receipt_sha256": SPLIT_RECEIPT_SHA256,
        "expected_extraction_source_manifest_sha256": (
            EXTRACTION_SOURCE_MANIFEST_SHA256
        ),
        "expected_development_fingerprint_sha256": DEVELOPMENT_FINGERPRINT_SHA256,
        "expected_observable_source_sha256": _sha256(source),
        "expected_v1_8_1_package_contract_sha256": package_contract_sha256,
    }
    for index, field in enumerate(base):
        if field == "observable_source_bytes":
            continue
        bad = dict(base)
        bad[field] = "A" * 64
        with pytest.raises(PrelabelFirewallError, match="lowercase SHA-256"):
            freeze_prelabel(tmp_path / f"malformed_{index}", **bad)  # type: ignore[arg-type]

    wrong_source = dict(base)
    wrong_source["expected_observable_source_sha256"] = "0" * 64
    with pytest.raises(PrelabelFirewallError, match="observable source SHA-256 mismatch"):
        freeze_prelabel(tmp_path / "wrong_source", **wrong_source)  # type: ignore[arg-type]
    wrong_package = dict(base)
    wrong_package["expected_v1_8_1_package_contract_sha256"] = "0" * 64
    with pytest.raises(PrelabelFirewallError, match="package verification failed"):
        freeze_prelabel(tmp_path / "wrong_package", **wrong_package)  # type: ignore[arg-type]


def test_wrong_retained_split_or_prelabel_receipt_fails_verification(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source, output, _, receipt_sha256 = _freeze(tmp_path, package_contract_sha256)
    with pytest.raises(PrelabelFirewallError, match="caller-retained prelabel receipt"):
        verify_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
            expected_prelabel_receipt_sha256="0" * 64,
        )
    with pytest.raises(PrelabelFirewallError, match="bytes do not match recomputation"):
        verify_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256="2" * 64,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
            expected_prelabel_receipt_sha256=receipt_sha256,
        )


def test_rival_writer_file_is_refused_and_never_deleted(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_bytes()
    original = prelabel_module._write_owned_file
    injected = False

    def race(path: Path, data: bytes) -> tuple[int, int]:
        nonlocal injected
        if not injected:
            injected = True
            path.write_bytes(b"rival-owner")
        return original(path, data)

    monkeypatch.setattr(prelabel_module, "_write_owned_file", race)
    output = tmp_path / "rival"
    with pytest.raises(PrelabelFirewallError, match="rival writer"):
        freeze_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )
    assert (output / PRELABEL_FILES["scores"]).read_bytes() == b"rival-owner"


def test_output_directory_swap_is_detected_without_deleting_rival_directory(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_bytes()
    output = tmp_path / "swap"
    displaced = tmp_path / "displaced"
    original = prelabel_module._write_owned_file
    injected = False

    def race(path: Path, data: bytes) -> tuple[int, int]:
        nonlocal injected
        if not injected:
            injected = True
            output.rename(displaced)
            output.mkdir()
        return original(path, data)

    monkeypatch.setattr(prelabel_module, "_write_owned_file", race)
    with pytest.raises(PrelabelFirewallError, match="directory changed"):
        freeze_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )
    assert output.is_dir()
    assert displaced.is_dir()


def test_code_toctou_change_is_detected_before_output_creation(
    tmp_path: Path,
    package_contract_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_bytes()
    original = prelabel_module._snapshot_package_files
    calls = 0

    def racing_snapshot() -> tuple[tuple[str, bytes], ...]:
        nonlocal calls
        calls += 1
        snapshot = original()
        if calls == 1:
            return snapshot
        first_path, first_bytes = snapshot[0]
        return ((first_path, first_bytes + b"# raced\n"), *snapshot[1:])

    monkeypatch.setattr(prelabel_module, "_snapshot_package_files", racing_snapshot)
    output = tmp_path / "toctou"
    with pytest.raises(PrelabelFirewallError, match="changed during operation"):
        freeze_prelabel(
            output,
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )
    assert calls == 2
    assert not output.exists()


def test_symlinked_ancestor_is_rejected(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    target = tmp_path / "real"
    nested = target / "nested"
    nested.mkdir(parents=True)
    link = tmp_path / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    source = _source_bytes()
    with pytest.raises(PrelabelFirewallError, match="link or junction"):
        freeze_prelabel(
            link / "nested" / "out",
            observable_source_bytes=source,
            expected_split_receipt_sha256=SPLIT_RECEIPT_SHA256,
            expected_extraction_source_manifest_sha256=(
                EXTRACTION_SOURCE_MANIFEST_SHA256
            ),
            expected_development_fingerprint_sha256=DEVELOPMENT_FINGERPRINT_SHA256,
            expected_observable_source_sha256=_sha256(source),
            expected_v1_8_1_package_contract_sha256=package_contract_sha256,
        )


def test_symlinked_artifact_is_rejected_even_when_bytes_match(
    tmp_path: Path,
    package_contract_sha256: str,
) -> None:
    source, output, paths, receipt_sha256 = _freeze(tmp_path, package_contract_sha256)
    target = tmp_path / "same_score_bytes.csv"
    target.write_bytes(paths["scores"].read_bytes())
    paths["scores"].unlink()
    try:
        paths["scores"].symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    with pytest.raises(PrelabelFirewallError, match="unsafe prelabel artifact"):
        _verify(source, output, package_contract_sha256, receipt_sha256)
