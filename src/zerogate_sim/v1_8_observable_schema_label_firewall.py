from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.v1_8_label_join import (
    build_failure_capability_rows,
    evaluate_frozen_predictions,
    failure_capability_passed,
    verify_frozen_predictions,
)
from zerogate_sim.v1_8_observable_schema import (
    CURRENT_VERSION,
    FORBIDDEN_FIELD_EXAMPLES,
    LabeledSourceRecord,
    OBSERVABLE_FIELDS,
    SCHEMA_ID,
    ObservableFirewallError,
    observable_schema_document,
    observable_schema_sha256,
    read_csv_exact,
    read_observable_inputs,
    sha256_file,
    stable_sha256,
    validate_observables,
    write_canonical_json,
    write_observable_label_split,
)
from zerogate_sim.v1_8_prediction_freeze import (
    PredictionProposal,
    freeze_predictions,
)

NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
DECISION = "LOCAL_GREEN_FIREWALL_ONLY"
SCIENTIFIC_STATUS = "HOLD_NO_SCIENTIFIC_THRESHOLDS"
NEXT_GATE = (
    "v1.8.1-alpha — Lineage-Bearing Predictor Package and "
    "Development-Only Preregistration"
)

OUTPUT_FILES = {
    "schema": "v1_8_observable_schema.json",
    "forbidden": "v1_8_forbidden_field_rules.csv",
    "invariance": "v1_8_firewall_invariance_audit.csv",
    "failure": "v1_8_failure_capability_audit.csv",
    "decision": "v1_8_label_firewall_decision.json",
    "read": "v1_8_observable_schema_label_firewall_read.md",
    "bundle": "v1_8_observable_schema_label_firewall_bundle.zip",
}


def _synthetic_observables() -> list[dict[str, float]]:
    return [
        {
            "strength": 0.91,
            "distinction": 0.88,
            "polarity": 0.79,
            "relation": 0.83,
            "return_observed": 0.76,
            "echo_mimic_score": 0.12,
            "observed_stability_score": 0.87,
        },
        {
            "strength": 0.54,
            "distinction": 0.67,
            "polarity": 0.62,
            "relation": 0.58,
            "return_observed": 0.41,
            "echo_mimic_score": 0.28,
            "observed_stability_score": 0.57,
        },
        {
            "strength": 0.73,
            "distinction": 0.81,
            "polarity": 0.69,
            "relation": 0.77,
            "return_observed": 0.22,
            "echo_mimic_score": 0.71,
            "observed_stability_score": 0.35,
        },
    ]


def _source_records(
    *,
    source_ids: Iterable[str],
    roles: Iterable[str],
    feature_order: Iterable[int] = (0, 1, 2),
) -> list[LabeledSourceRecord]:
    ids = list(source_ids)
    role_values = list(roles)
    order = list(feature_order)
    observables = [_synthetic_observables()[index] for index in order]
    if len(ids) != len(observables) or len(role_values) != len(observables):
        raise ValueError("synthetic canary requires three IDs and three roles")
    return [
        LabeledSourceRecord(source_id, feature_values, role)
        for source_id, feature_values, role in zip(
            ids,
            observables,
            role_values,
            strict=True,
        )
    ]


def _canary_predictor_contract() -> tuple[object, str]:
    observables = _synthetic_observables()
    proposals = (
        PredictionProposal(0.8, 1),
        PredictionProposal(0.0, 0),
        PredictionProposal(-0.8, -1),
    )
    lookup = {
        stable_sha256(values): proposal
        for values, proposal in zip(observables, proposals, strict=True)
    }

    def predictor(values: Mapping[str, float]) -> PredictionProposal:
        key = stable_sha256(dict(values))
        if key not in lookup:
            raise ValueError("synthetic canary received an unknown observable vector")
        return lookup[key]

    contract = {
        "predictor_id": "synthetic-canary-no-scientific-authority-v1",
        "not_a_scientific_scorer": True,
        "thresholds": None,
        "lookup": {
            key: {
                "prediction_score": proposal.prediction_score,
                "proposed_trinary": proposal.proposed_trinary,
            }
            for key, proposal in sorted(lookup.items())
        },
    }
    return predictor, stable_sha256(contract)


def _build_probe(
    out: Path,
    *,
    source_ids: Iterable[str],
    roles: Iterable[str],
    feature_order: Iterable[int] = (0, 1, 2),
) -> dict[str, object]:
    records = _source_records(
        source_ids=source_ids,
        roles=roles,
        feature_order=feature_order,
    )
    split = write_observable_label_split(
        out / "split",
        records,
        namespace="v1.8-synthetic-firewall-canary",
        synthetic_only=True,
    )
    predictor, contract_sha = _canary_predictor_contract()
    freeze = freeze_predictions(
        out / "freeze",
        observable_input_path=split["observable_inputs"],
        predictor=predictor,
        predictor_id="synthetic-canary-no-scientific-authority-v1",
        predictor_contract_sha256=contract_sha,
        synthetic_only=True,
    )
    receipt_sha = sha256_file(freeze["receipt"])
    split_manifest_sha = sha256_file(split["manifest"])
    evaluation = evaluate_frozen_predictions(
        observable_input_path=split["observable_inputs"],
        prediction_path=freeze["predictions"],
        manifest_path=freeze["manifest"],
        receipt_path=freeze["receipt"],
        expected_receipt_sha256=receipt_sha,
        split_manifest_path=split["manifest"],
        expected_split_manifest_sha256=split_manifest_sha,
        join_keys_path=split["join_keys"],
        label_vault_path=split["label_vault"],
    )
    return {
        "split": split,
        "freeze": freeze,
        "receipt_sha256": receipt_sha,
        "split_manifest_sha256": split_manifest_sha,
        "evaluation": evaluation,
    }


def _prediction_by_observable(probe: Mapping[str, object]) -> dict[str, tuple[str, str]]:
    split = probe["split"]
    freeze = probe["freeze"]
    observable_rows = read_observable_inputs(split["observable_inputs"])
    prediction_rows = read_csv_exact(
        freeze["predictions"],
        header=("row_index", "prediction_score", "proposed_trinary"),
    )
    return {
        stable_sha256(observable_rows[int(row["row_index"])]["observables"]): (
            row["prediction_score"],
            row["proposed_trinary"],
        )
        for row in prediction_rows
    }


def _run_negative_canaries(
    output_dir: Path,
    *,
    probe: Mapping[str, object],
) -> dict[str, bool]:
    split = probe["split"]
    freeze = probe["freeze"]
    negative_dir = output_dir / "negative_canaries"
    negative_dir.mkdir(parents=True, exist_ok=False)

    forbidden_rejected = True
    baseline = _synthetic_observables()[0]
    for field in FORBIDDEN_FIELD_EXAMPLES:
        candidate = dict(baseline)
        candidate[field] = 0.0
        try:
            validate_observables(candidate, source=f"forbidden canary {field}")
        except ObservableFirewallError:
            continue
        forbidden_rejected = False
        break

    missing_field_rejected = False
    missing = dict(baseline)
    del missing[OBSERVABLE_FIELDS[0]]
    try:
        validate_observables(missing, source="missing-field canary")
    except ObservableFirewallError:
        missing_field_rejected = True

    nonfinite_rejected = False
    nonfinite = dict(baseline)
    nonfinite[OBSERVABLE_FIELDS[0]] = float("nan")
    try:
        validate_observables(nonfinite, source="nonfinite canary")
    except ObservableFirewallError:
        nonfinite_rejected = True

    calls = 0

    def positional_predictor(_: Mapping[str, float]) -> PredictionProposal:
        nonlocal calls
        values = (1, 0, -1)
        trinary = values[calls % len(values)]
        calls += 1
        return PredictionProposal(float(trinary), trinary)

    position_leak_rejected = False
    try:
        freeze_predictions(
            negative_dir / "position_leak_freeze_must_fail",
            observable_input_path=split["observable_inputs"],
            predictor=positional_predictor,
            predictor_id="position-leak-negative-canary-v1",
            predictor_contract_sha256=stable_sha256(
                "position-leak-negative-canary-v1"
            ),
            synthetic_only=True,
        )
    except ObservableFirewallError:
        position_leak_rejected = True

    tampered_prediction = negative_dir / "tampered_predictions_must_fail.csv"
    tampered_prediction.write_bytes(freeze["predictions"].read_bytes() + b"x")
    prediction_tamper_rejected = False
    try:
        verify_frozen_predictions(
            observable_input_path=split["observable_inputs"],
            prediction_path=tampered_prediction,
            manifest_path=freeze["manifest"],
            receipt_path=freeze["receipt"],
            expected_receipt_sha256=probe["receipt_sha256"],
        )
    except ObservableFirewallError:
        prediction_tamper_rejected = True

    tampered_label = negative_dir / "tampered_label_vault_must_fail.csv"
    tampered_label.write_bytes(split["label_vault"].read_bytes() + b"x")
    label_tamper_rejected = False
    try:
        evaluate_frozen_predictions(
            observable_input_path=split["observable_inputs"],
            prediction_path=freeze["predictions"],
            manifest_path=freeze["manifest"],
            receipt_path=freeze["receipt"],
            expected_receipt_sha256=probe["receipt_sha256"],
            split_manifest_path=split["manifest"],
            expected_split_manifest_sha256=probe["split_manifest_sha256"],
            join_keys_path=split["join_keys"],
            label_vault_path=tampered_label,
        )
    except ObservableFirewallError:
        label_tamper_rejected = True

    return {
        "forbidden_field_negative_canary_passed": forbidden_rejected,
        "missing_field_negative_canary_passed": missing_field_rejected,
        "nonfinite_negative_canary_passed": nonfinite_rejected,
        "position_leak_negative_canary_passed": position_leak_rejected,
        "prediction_tamper_negative_canary_passed": prediction_tamper_rejected,
        "sealed_label_tamper_negative_canary_passed": label_tamper_rejected,
    }


def _write_read(
    path: Path,
    *,
    decision: Mapping[str, object],
    failure_rows: list[dict[str, object]],
) -> None:
    lines = [
        "# v1.8.0-alpha — Observable Schema and Label Firewall",
        "",
        f"**Decision:** `{decision['decision']}`",
        "",
        f"**Scientific status:** `{decision['scientific_status']}`",
        "",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        "v1.8.0 is infrastructure, not a scorer result. It freezes a seven-number",
        "observable input contract, keeps identifiers outside the predictor callback,",
        "writes predictions and a pre-label receipt, then verifies every hash before",
        "the evaluation module is allowed to read labels.",
        "",
        "## Exact observable allowlist",
        "",
        "```text",
        *OBSERVABLE_FIELDS,
        "```",
        "",
        "Every extra or missing field fails closed. Legacy role-stripped tables are",
        "not trusted because they contain role-derived aggregates and identifier",
        "proxies.",
        "",
        "## Executable invariance",
        "",
        f"- Label permutation leaves observable and prediction bytes unchanged: `{decision['label_permutation_prediction_invariant']}`.",
        f"- Identifier renaming leaves observable and prediction bytes unchanged: `{decision['identifier_renaming_prediction_invariant']}`.",
        f"- Identifier renaming changes the sealed join-key artifact: `{decision['identifier_renaming_changes_join_keys']}`.",
        f"- Row permutation is prediction-equivariant by observable hash: `{decision['row_permutation_prediction_equivariant']}`.",
        f"- Prediction receipt is required before label join: `{decision['prejoin_receipt_required']}`.",
        f"- Sealed split manifest rejects label-vault tampering: `{decision['sealed_split_manifest_required']}`.",
        f"- Forbidden-field negative canary passes: `{decision['forbidden_field_negative_canary_passed']}`.",
        f"- Missing/non-finite values fail closed: `{decision['missing_field_negative_canary_passed'] and decision['nonfinite_negative_canary_passed']}`.",
        f"- Position-dependent callback canary is rejected: `{decision['position_leak_negative_canary_passed']}`.",
        "",
        "## Failure capability",
        "",
        "| canary | expected | observed | false crowns | hold overcrowns | missed earned |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in failure_rows:
        lines.append(
            f"| {row['case']} | {row['expected_status']} | {row['observed_status']} | "
            f"{row['false_crown_count']} | {row['hold_overcrown_count']} | "
            f"{row['missed_earned_count']} |"
        )
    lines.extend(
        [
            "",
            "Zero false crowns cannot pass by itself: always-HOLD is explicitly invalid,",
            "and an injected trap crown remains visible to the evaluator.",
            "",
            "## Honest limitations",
            "",
            "- The canaries are synthetic and deliberately constructed; they are not evidence of discrimination.",
            "- An in-process Python callback is not an operating-system sandbox.",
            "- A local SHA proves artifact integrity, not external timestamped chronology.",
            "- The predictor-contract hash is caller-declared; binding it to packaged code belongs to v1.8.1.",
            "- No scientific score threshold, abstention rule, or frozen holdout was selected or revealed.",
            "- Manuscript v2 and DTA transfer remain on HOLD.",
            "",
            "## Next gate",
            "",
            f"`{NEXT_GATE}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_v1_8_observable_schema_label_firewall(out: str | Path) -> dict[str, Path]:
    output_dir = ensure_dir(Path(out))
    paths = {key: output_dir / filename for key, filename in OUTPUT_FILES.items()}
    occupied = [str(path) for key, path in paths.items() if key != "bundle" and path.exists()]
    if occupied:
        raise ValueError(f"refusing to overwrite v1.8 artifacts: {occupied}")

    original = _build_probe(
        output_dir / "original_labels",
        source_ids=("semantic-alpha", "semantic-beta", "semantic-gamma"),
        roles=("expresser", "latent", "trap"),
    )
    permuted = _build_probe(
        output_dir / "permuted_labels",
        source_ids=("semantic-alpha", "semantic-beta", "semantic-gamma"),
        roles=("trap", "expresser", "latent"),
    )
    renamed = _build_probe(
        output_dir / "renamed_identifiers",
        source_ids=("renamed-one", "renamed-two", "renamed-three"),
        roles=("expresser", "latent", "trap"),
    )
    row_permuted = _build_probe(
        output_dir / "permuted_rows",
        source_ids=("semantic-gamma", "semantic-alpha", "semantic-beta"),
        roles=("trap", "expresser", "latent"),
        feature_order=(2, 0, 1),
    )

    original_split = original["split"]
    permuted_split = permuted["split"]
    renamed_split = renamed["split"]
    original_freeze = original["freeze"]
    permuted_freeze = permuted["freeze"]
    renamed_freeze = renamed["freeze"]

    label_permutation_invariant = (
        sha256_file(original_split["observable_inputs"])
        == sha256_file(permuted_split["observable_inputs"])
        and sha256_file(original_freeze["predictions"])
        == sha256_file(permuted_freeze["predictions"])
        and original["receipt_sha256"] == permuted["receipt_sha256"]
    )
    identifier_renaming_invariant = (
        sha256_file(original_split["observable_inputs"])
        == sha256_file(renamed_split["observable_inputs"])
        and sha256_file(original_freeze["predictions"])
        == sha256_file(renamed_freeze["predictions"])
        and original["receipt_sha256"] == renamed["receipt_sha256"]
    )
    identifier_changes_join_keys = (
        sha256_file(original_split["join_keys"])
        != sha256_file(renamed_split["join_keys"])
    )
    labels_change_evaluation = (
        original["evaluation"]["correct_count"]
        != permuted["evaluation"]["correct_count"]
        and original["evaluation"]["prediction_values_sha256"]
        == permuted["evaluation"]["prediction_values_sha256"]
    )
    row_permutation_equivariant = (
        _prediction_by_observable(original) == _prediction_by_observable(row_permuted)
    )
    negative_canaries = _run_negative_canaries(output_dir, probe=original)

    failure_rows = build_failure_capability_rows()
    failure_passed = failure_capability_passed(failure_rows)
    local_green = all(
        (
            label_permutation_invariant,
            identifier_renaming_invariant,
            identifier_changes_join_keys,
            labels_change_evaluation,
            row_permutation_equivariant,
            failure_passed,
            *negative_canaries.values(),
        )
    )

    write_canonical_json(paths["schema"], observable_schema_document())
    write_dict_rows_csv(
        paths["forbidden"],
        [
            {
                "field": field,
                "decision": "forbidden_exact_allowlist_rejects",
                "reason": "not one of the seven pre-verdict numeric observables",
            }
            for field in FORBIDDEN_FIELD_EXAMPLES
        ],
    )
    invariance_rows = [
        {
            "audit": "label_permutation",
            "observable_bytes_identical": str(label_permutation_invariant).lower(),
            "prediction_bytes_identical": str(label_permutation_invariant).lower(),
            "evaluation_changes_after_label_join": str(labels_change_evaluation).lower(),
            "boundary": "labels affect evaluation only",
        },
        {
            "audit": "identifier_renaming",
            "observable_bytes_identical": str(identifier_renaming_invariant).lower(),
            "prediction_bytes_identical": str(identifier_renaming_invariant).lower(),
            "evaluation_changes_after_label_join": "false",
            "boundary": "identifiers stay outside predictor callback",
        },
        {
            "audit": "row_permutation",
            "observable_bytes_identical": "false",
            "prediction_bytes_identical": "false",
            "evaluation_changes_after_label_join": "false",
            "boundary": (
                "predictions remain equivariant by observable hash when row order changes: "
                f"{str(row_permutation_equivariant).lower()}"
            ),
        },
    ]
    write_dict_rows_csv(paths["invariance"], invariance_rows)
    write_dict_rows_csv(paths["failure"], failure_rows)

    decision = {
        "version": CURRENT_VERSION,
        "decision": DECISION if local_green else "FIREWALL_LOCAL_FAILURE",
        "scientific_status": SCIENTIFIC_STATUS,
        "native_witness": NATIVE_WITNESS,
        "native_math_mutated": False,
        "schema_id": SCHEMA_ID,
        "schema_sha256": observable_schema_sha256(),
        "observable_field_count": len(OBSERVABLE_FIELDS),
        "exact_allowlist_enforced": negative_canaries[
            "forbidden_field_negative_canary_passed"
        ],
        "label_permutation_prediction_invariant": label_permutation_invariant,
        "identifier_renaming_prediction_invariant": identifier_renaming_invariant,
        "identifier_renaming_changes_join_keys": identifier_changes_join_keys,
        "row_permutation_prediction_equivariant": row_permutation_equivariant,
        "labels_change_evaluation_only_after_join": labels_change_evaluation,
        "prejoin_receipt_required": negative_canaries[
            "prediction_tamper_negative_canary_passed"
        ],
        "sealed_split_manifest_required": negative_canaries[
            "sealed_label_tamper_negative_canary_passed"
        ],
        **negative_canaries,
        "failure_capability_passed": failure_passed,
        "original_synthetic_evaluation_status": original["evaluation"]["evaluation_status"],
        "permuted_synthetic_evaluation_status": permuted["evaluation"]["evaluation_status"],
        "original_prediction_values_sha256": original["evaluation"]["prediction_values_sha256"],
        "original_prejoin_receipt_sha256": original["receipt_sha256"],
        "synthetic_canary_only": True,
        "in_process_callback_is_os_sandboxed": False,
        "callback_argument_and_order_controls_passed": negative_canaries[
            "position_leak_negative_canary_passed"
        ],
        "reverse_order_repeat_consistency_enforced": True,
        "predictor_contract_code_binding_verified": False,
        "external_timestamp_proof": False,
        "scientific_scorer_implemented": False,
        "scientific_thresholds_selected": False,
        "frozen_holdout_revealed": False,
        "core_question_closed": False,
        "manuscript_v2_started": False,
        "dta_transfer_go": False,
        "release_go": False,
        "next_gate": NEXT_GATE,
    }
    write_canonical_json(paths["decision"], decision)
    _write_read(paths["read"], decision=decision, failure_rows=failure_rows)
    paths["bundle"] = write_evidence_bundle(
        output_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="zerogate_v1_8_observable_schema_label_firewall_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the v1.8 observable-schema and label-firewall infrastructure canary."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/v1_8_observable_schema_label_firewall_local"),
    )
    args = parser.parse_args(argv)
    paths = build_v1_8_observable_schema_label_firewall(args.out)
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['decision']}")
    print(f"Wrote {paths['bundle']}")
    print(f"Pre-label receipt SHA-256: {decision['original_prejoin_receipt_sha256']}")
    return 0 if decision["decision"] == DECISION else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
