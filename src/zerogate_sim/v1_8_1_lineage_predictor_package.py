from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.v1_8_lineage_schema import (
    OBSERVABLE_FIELDS,
    VERSION,
    LineageSchemaError,
    lineage_schema_document,
    read_lineage_inputs,
    sha256_file,
    stable_sha256,
    validate_lineage_frames,
    write_canonical_json,
    write_lineage_inputs,
)
from zerogate_sim.v1_8_predictor_package import (
    PACKAGE_FILE_ALLOWLIST,
    SCORE_HEADER,
    development_plan_document,
    freeze_lineage_scores,
    predictor_package_manifest,
    verify_development_canaries,
    verify_lineage_score_freeze,
    verify_predictor_package,
    write_lineage_source_manifest,
)

DECISION = "LOCAL_GREEN_LINEAGE_PACKAGE_ONLY"
FAILURE_DECISION = "LINEAGE_PACKAGE_LOCAL_FAILURE"
SCIENTIFIC_STATUS = "HOLD_LINEAGE_PACKAGE_DEVELOPMENT_ONLY"
HISTORICAL_NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
PREDICTOR_FORMULA = "lineage_score = min(Q_late, max(Q_early, Q_witness))"
NEXT_GATE = "v1.8.2-alpha - Development Evaluation and Threshold Selection"

OUTPUT_FILES = {
    "schema": "v1_8_1_lineage_schema.json",
    "package": "v1_8_1_predictor_package_manifest.json",
    "inputs": "v1_8_1_canary_lineage_inputs.jsonl",
    "source_manifest": "v1_8_1_canary_source_manifest.json",
    "scores": "v1_8_1_frozen_development_scores.csv",
    "manifest": "v1_8_1_score_freeze_manifest.json",
    "receipt": "v1_8_1_score_freeze_receipt.json",
    "canaries": "v1_8_1_lineage_canary_audit.csv",
    "invariance": "v1_8_1_lineage_invariance_audit.csv",
    "decision": "v1_8_1_lineage_predictor_decision.json",
    "read": "v1_8_1_lineage_predictor_read.md",
    "bundle": "v1_8_1_lineage_predictor_bundle.zip",
}


def _owned_pressure_frame(value: float) -> dict[str, float]:
    frame = {field: value for field in OBSERVABLE_FIELDS}
    frame["echo_mimic_score"] = 0.0
    return frame


def _canary_rows() -> list[list[dict[str, float]]]:
    rows: list[list[dict[str, float]]] = []
    for canary in development_plan_document()["canaries"]:
        if not isinstance(canary, dict) or not isinstance(
            canary.get("owned_pressure_path"), list
        ):
            raise LineageSchemaError("development canary contract is malformed")
        rows.append(
            [_owned_pressure_frame(float(value)) for value in canary["owned_pressure_path"]]
        )
    return rows


def _read_score_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise LineageSchemaError(f"missing or unsafe score table: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(SCORE_HEADER) or len(set(reader.fieldnames)) != len(
            reader.fieldnames
        ):
            raise LineageSchemaError("score table header is not exact")
        rows = [dict(row) for row in reader]
    if not rows:
        raise LineageSchemaError("score table is empty")
    return rows


def _scores_by_observable(input_path: Path, score_path: Path) -> dict[str, tuple[str, ...]]:
    inputs = read_lineage_inputs(input_path)
    scores = _read_score_rows(score_path)
    if len(inputs) != len(scores):
        raise LineageSchemaError("input and score counts differ")
    output: dict[str, tuple[str, ...]] = {}
    for position, (input_row, score_row) in enumerate(zip(inputs, scores, strict=True)):
        if score_row["row_index"] != str(position):
            raise LineageSchemaError("score row index is not the exact ordered sequence")
        key = stable_sha256(input_row["observable_frames"])
        values = tuple(score_row[field] for field in SCORE_HEADER if field != "row_index")
        previous = output.get(key)
        if previous is not None and previous != values:
            raise LineageSchemaError("identical observable path produced different score bytes")
        output[key] = values
    return output


def _rejects_extra_field(rows: Sequence[Sequence[Mapping[str, float]]], field: str) -> bool:
    candidate = [[dict(frame) for frame in row] for row in rows]
    candidate[0][0][field] = 0.0
    try:
        validate_lineage_frames(candidate[0], source=f"negative {field} canary")
    except LineageSchemaError:
        return True
    return False


def _package_tamper_rejected(repo_root: Path, expected_contract_sha256: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="zerogate-v181-package-") as temporary:
        copy_root = Path(temporary)
        for relative in PACKAGE_FILE_ALLOWLIST:
            source = repo_root / Path(relative)
            target = copy_root / Path(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        verify_predictor_package(
            copy_root,
            expected_contract_sha256=expected_contract_sha256,
        )
        target = copy_root / "src/zerogate_sim/v1_8_lineage_predictor.py"
        target.write_bytes(target.read_bytes() + b"\n# tamper canary\n")
        try:
            verify_predictor_package(
                copy_root,
                expected_contract_sha256=expected_contract_sha256,
            )
        except LineageSchemaError:
            return True
    return False


def _score_tamper_rejected(
    output_dir: Path,
    *,
    input_path: Path,
    source_manifest_path: Path,
    source_manifest_sha256: str,
    allowed_input_root: Path,
    contract_sha256: str,
    receipt_sha256: str,
    repo_root: Path,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="zerogate-v181-score-") as temporary:
        copied = Path(temporary) / "freeze"
        copied.mkdir()
        for key in ("scores", "manifest", "receipt"):
            shutil.copyfile(output_dir / OUTPUT_FILES[key], copied / OUTPUT_FILES[key])
        score_path = copied / OUTPUT_FILES["scores"]
        score_path.write_bytes(score_path.read_bytes() + b"tamper")
        try:
            verify_lineage_score_freeze(
                copied,
                observable_input_path=input_path,
                source_manifest_path=source_manifest_path,
                expected_source_manifest_sha256=source_manifest_sha256,
                allowed_input_root=allowed_input_root,
                expected_source_purpose="v1_8_1_formula_canaries",
                expected_predictor_contract_sha256=contract_sha256,
                expected_receipt_sha256=receipt_sha256,
                repo_root=repo_root,
                synthetic_only=True,
            )
        except LineageSchemaError:
            return True
    return False


def _write_read(path: Path, decision: Mapping[str, object]) -> None:
    lines = [
        "# v1.8.1-alpha - Lineage-Bearing Predictor Package",
        "",
        f"**Development decision:** `{decision['decision']}`",
        "",
        f"**Scientific status:** `{decision['scientific_status']}`",
        "",
        f"**Historical native witness:** `{HISTORICAL_NATIVE_WITNESS}`",
        "",
        f"**v1.8.1 predictor formula:** `{PREDICTOR_FORMULA}`",
        "",
        "This version implements an inspectable temporal-support function over exactly",
        "three ordered observable frames. Each frame has the v1.8.0 seven-number",
        "allowlist; identifiers, labels, generator names, seeds, and scenarios are not",
        "callback arguments.",
        "",
        "```text",
        "Q_t = min(strength, distinction, polarity, relation, return_observed,",
        "          observed_stability_score, 1 - echo_mimic_score)",
        "lineage_score = min(Q_late, max(Q_early, Q_witness))",
        "no_lineage_score = Q_late",
        "```",
        "",
        "## Executed safeguards",
        "",
        f"- Exact package code/config binding verified: `{decision['package_binding_verified']}`.",
        f"- Frozen scores recomputed and receipt-verified: `{decision['score_freeze_verified']}`.",
        f"- Required lineage/no-lineage rank reversal observed: `{decision['required_rank_reversal_passed']}`.",
        f"- Row permutation is equivariant by observable hash: `{decision['row_permutation_equivariant']}`.",
        f"- Identifier and label fields fail the callback schema: `{decision['identifier_field_rejected'] and decision['label_field_rejected']}`.",
        f"- Package and score tamper canaries fail closed: `{decision['package_tamper_rejected'] and decision['score_tamper_rejected']}`.",
        "",
        "## Honest boundary",
        "",
        "These are synthetic mechanism canaries, not a discrimination result. No",
        "trinary decision rule or scientific threshold is selected, and no frozen",
        "holdout is generated or revealed. The scientific authority therefore remains",
        "v1.7.11-alpha at 0 / HOLD. DTA transfer and manuscript v2 remain on HOLD.",
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_v1_8_1_lineage_predictor_package(out: str | Path) -> dict[str, Path]:
    output_dir = Path(out)
    if output_dir.exists() and (
        not output_dir.is_dir() or output_dir.is_symlink() or any(output_dir.iterdir())
    ):
        raise LineageSchemaError(f"refusing nonempty or unsafe output directory: {output_dir}")
    ensure_dir(output_dir)
    paths = {key: output_dir / filename for key, filename in OUTPUT_FILES.items()}
    repo_root = Path(__file__).resolve().parents[2]

    package = verify_predictor_package(repo_root)
    package_manifest = predictor_package_manifest(
        repo_root,
        expected_contract_sha256=package.contract_sha256,
    )
    write_canonical_json(paths["schema"], lineage_schema_document())
    write_canonical_json(paths["package"], package_manifest)

    canary_rows = _canary_rows()
    write_lineage_inputs(paths["inputs"], canary_rows)
    write_lineage_source_manifest(
        paths["source_manifest"],
        observable_input_path=paths["inputs"],
        allowed_input_root=output_dir,
        purpose="v1_8_1_formula_canaries",
        source_kind="constructed_formula_canaries",
        construction_policy=(
            "exact paths and expected scores are fixed in the byte-bound development plan"
        ),
        labels_used_to_construct_observables_declared=False,
        holdout_material_declared=False,
    )
    source_manifest_sha256 = sha256_file(paths["source_manifest"])
    frozen = freeze_lineage_scores(
        output_dir,
        observable_input_path=paths["inputs"],
        source_manifest_path=paths["source_manifest"],
        expected_source_manifest_sha256=source_manifest_sha256,
        allowed_input_root=output_dir,
        expected_source_purpose="v1_8_1_formula_canaries",
        expected_predictor_contract_sha256=package.contract_sha256,
        repo_root=repo_root,
        synthetic_only=True,
    )
    if frozen != {key: paths[key] for key in ("scores", "manifest", "receipt")}:
        raise LineageSchemaError("score freeze returned an unexpected artifact surface")
    receipt_sha256 = sha256_file(paths["receipt"])
    verified_freeze = verify_lineage_score_freeze(
        output_dir,
        observable_input_path=paths["inputs"],
        source_manifest_path=paths["source_manifest"],
        expected_source_manifest_sha256=source_manifest_sha256,
        allowed_input_root=output_dir,
        expected_source_purpose="v1_8_1_formula_canaries",
        expected_predictor_contract_sha256=package.contract_sha256,
        expected_receipt_sha256=receipt_sha256,
        repo_root=repo_root,
        synthetic_only=True,
    )

    canary_results = list(
        verify_development_canaries(
            repo_root,
            expected_contract_sha256=package.contract_sha256,
        )
    )
    by_name = {str(row["name"]): row for row in canary_results}
    rank_reversal = (
        float(by_name["sustained"]["lineage_score"])
        > float(by_name["late_spike"]["lineage_score"])
        and float(by_name["sustained"]["no_lineage_score"])
        < float(by_name["late_spike"]["no_lineage_score"])
    )

    probe_dir = output_dir / "row_permutation_probe"
    probe_dir.mkdir()
    permutation = (4, 3, 2, 0, 1)
    permuted_rows = [canary_rows[index] for index in permutation]
    permuted_input = probe_dir / "permuted_inputs.jsonl"
    write_lineage_inputs(permuted_input, permuted_rows)
    permuted_source_manifest = probe_dir / "permuted_source_manifest.json"
    write_lineage_source_manifest(
        permuted_source_manifest,
        observable_input_path=permuted_input,
        allowed_input_root=probe_dir,
        purpose="v1_8_1_formula_canaries",
        source_kind="constructed_formula_canaries_permuted",
        construction_policy=(
            "row permutation of exact paths fixed in the byte-bound development plan"
        ),
        labels_used_to_construct_observables_declared=False,
        holdout_material_declared=False,
    )
    permuted_source_manifest_sha256 = sha256_file(permuted_source_manifest)
    permuted_freeze = freeze_lineage_scores(
        probe_dir,
        observable_input_path=permuted_input,
        source_manifest_path=permuted_source_manifest,
        expected_source_manifest_sha256=permuted_source_manifest_sha256,
        allowed_input_root=probe_dir,
        expected_source_purpose="v1_8_1_formula_canaries",
        expected_predictor_contract_sha256=package.contract_sha256,
        repo_root=repo_root,
        synthetic_only=True,
    )
    permuted_receipt_sha256 = sha256_file(permuted_freeze["receipt"])
    verify_lineage_score_freeze(
        probe_dir,
        observable_input_path=permuted_input,
        source_manifest_path=permuted_source_manifest,
        expected_source_manifest_sha256=permuted_source_manifest_sha256,
        allowed_input_root=probe_dir,
        expected_source_purpose="v1_8_1_formula_canaries",
        expected_predictor_contract_sha256=package.contract_sha256,
        expected_receipt_sha256=permuted_receipt_sha256,
        repo_root=repo_root,
        synthetic_only=True,
    )
    row_permutation_equivariant = _scores_by_observable(
        paths["inputs"], paths["scores"]
    ) == _scores_by_observable(permuted_input, permuted_freeze["scores"])

    identifier_rejected = _rejects_extra_field(canary_rows, "blind_case_id")
    label_rejected = _rejects_extra_field(canary_rows, "evaluation_role")
    package_tamper_rejected = _package_tamper_rejected(
        repo_root, package.contract_sha256
    )
    score_tamper_rejected = _score_tamper_rejected(
        output_dir,
        input_path=paths["inputs"],
        source_manifest_path=paths["source_manifest"],
        source_manifest_sha256=source_manifest_sha256,
        allowed_input_root=output_dir,
        contract_sha256=package.contract_sha256,
        receipt_sha256=receipt_sha256,
        repo_root=repo_root,
    )

    plan = development_plan_document()
    no_decision_rule = (
        plan["selected_threshold_option"] is None
        and plan["scientific_thresholds_selected"] is False
        and plan["trinary_predictions_emitted"] is False
    )
    local_green = all(
        (
            package_manifest[
                "predictor_execution_code_and_configuration_binding_verified"
            ]
            is True,
            verified_freeze["verified"] is True,
            all(result["passed"] is True for result in canary_results),
            rank_reversal,
            row_permutation_equivariant,
            identifier_rejected,
            label_rejected,
            package_tamper_rejected,
            score_tamper_rejected,
            no_decision_rule,
        )
    )

    write_dict_rows_csv(paths["canaries"], canary_results)
    invariance_rows = [
        {
            "audit": "row_permutation",
            "passed": str(row_permutation_equivariant).lower(),
            "boundary": "scores equal by observable hash; row_index is transport only",
        },
        {
            "audit": "identifier_field_injection",
            "passed": str(identifier_rejected).lower(),
            "boundary": "blind identifiers are outside the exact callback schema",
        },
        {
            "audit": "label_field_injection",
            "passed": str(label_rejected).lower(),
            "boundary": "evaluation labels are outside the exact callback schema",
        },
        {
            "audit": "package_tamper",
            "passed": str(package_tamper_rejected).lower(),
            "boundary": "retained package contract hash rejects changed bound bytes",
        },
        {
            "audit": "score_tamper",
            "passed": str(score_tamper_rejected).lower(),
            "boundary": "retained receipt plus recomputation rejects changed score bytes",
        },
    ]
    write_dict_rows_csv(paths["invariance"], invariance_rows)

    decision = {
        "version": VERSION,
        "decision": DECISION if local_green else FAILURE_DECISION,
        "scientific_status": SCIENTIFIC_STATUS,
        "scientific_authority_version": "v1.7.11-alpha",
        "scientific_authority_result": "0/HOLD",
        "historical_native_witness": HISTORICAL_NATIVE_WITNESS,
        "predictor_formula": PREDICTOR_FORMULA,
        "native_math_mutated": False,
        "package_contract_sha256": package.contract_sha256,
        "package_binding_verified": package_manifest[
            "predictor_execution_code_and_configuration_binding_verified"
        ],
        "predictor_execution_loaded_from_verified_source_snapshot": package_manifest[
            "predictor_execution_loaded_from_verified_source_snapshot"
        ],
        "score_freeze_receipt_sha256": receipt_sha256,
        "score_freeze_verified": verified_freeze["verified"],
        "canary_count": len(canary_results),
        "all_canaries_passed": all(row["passed"] is True for row in canary_results),
        "required_rank_reversal_passed": rank_reversal,
        "row_permutation_equivariant": row_permutation_equivariant,
        "identifier_field_rejected": identifier_rejected,
        "label_field_rejected": label_rejected,
        "package_tamper_rejected": package_tamper_rejected,
        "score_tamper_rejected": score_tamper_rejected,
        "decision_rule_selected": False,
        "selected_threshold_option": None,
        "scientific_thresholds_selected": False,
        "trinary_predictions_emitted": False,
        "development_labels_accessed": False,
        "frozen_holdout_generated": False,
        "frozen_holdout_revealed": False,
        "dta_transfer_go": False,
        "manuscript_v2_started": False,
        "release_go": False,
        "next_gate": NEXT_GATE,
    }
    write_canonical_json(paths["decision"], decision)
    _write_read(paths["read"], decision)
    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_8_1_lineage_predictor_package",
    )
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the v1.8.1 lineage-bearing predictor package evidence bundle."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/v1_8_1_lineage_predictor_package"),
        help="Empty output directory for the local evidence bundle.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    paths = build_v1_8_1_lineage_predictor_package(args.out)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    print(f"v1.8.1 decision: {decision['decision']}")
    print(f"scientific status: {decision['scientific_status']}")
    print(f"bundle: {paths['bundle']}")
    return 0 if decision["decision"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
