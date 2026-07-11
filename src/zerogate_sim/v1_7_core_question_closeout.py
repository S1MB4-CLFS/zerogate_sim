from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from zerogate_sim.reporting import ensure_dir, write_dict_rows_csv, write_evidence_bundle
from zerogate_sim.v1_7_evidence_integrity_correction import (
    CANONICAL_CONTRACT_ID,
    canonical_contract_sha256,
)

CURRENT_VERSION = "v1.7.11-alpha"
HISTORICAL_VERSION = "v1.7.10-alpha"
NATIVE_WITNESS = "C_Z = min(D, P, R, B)"
CORE_QUESTION = (
    "Can a final trinary witness distinguish earned-one from raw expression pressure, "
    "latent overcrown, relation debt, return debt, and false-one pressure under "
    "controlled synthetic-field adversarial weather?"
)
DECISION = "evidence_integrity_correction_hold"
ANSWER_SYMBOL = "0/HOLD"
ANSWER_STATUS = "construction_bound_closeout_reopened"
NEXT_GATE = "v1.8.0-alpha — Observable Schema and Label Firewall"

OUTPUT_FILES = {
    "read": "v1_7_core_question_closeout_read.md",
    "decision": "v1_7_core_question_closeout_decision.json",
    "answer_status": "v1_7_answer_status_card.csv",
    "condition_status": "v1_7_full_answer_conditions.csv",
    "boundary": "v1_7_closeout_claim_boundary.csv",
    "go_no_go": "v1_7_go_no_go_for_manuscript_v2.csv",
    "evidence": "v1_7_closeout_evidence_snapshot.csv",
    "bundle": "v1_7_core_question_closeout_bundle.zip",
}

COUNT_KEYS = (
    "opportunities",
    "raw_expression_pressure",
    "earned_one",
    "false_one_pressure",
    "false_one_demoted",
    "latent_overcrown",
    "latent_overcrown_demoted",
    "relation_debt",
    "return_debt",
    "final_false_one_crowns",
)

BOUNDARY_ROWS = [
    {
        "lane": "allowed",
        "claim": "The legacy role-aware harness reproducibly partitions its designed controlled lanes.",
        "reason": "The simulations and generated artifacts remain reproducible historical software behavior.",
    },
    {
        "lane": "allowed",
        "claim": "v1.7.11 corrects nested-rung accounting and reopens the core question at 0/HOLD.",
        "reason": "The three weather rungs are nested views and the current final path uses truth role.",
    },
    {
        "lane": "forbidden",
        "claim": "Zero final false crowns demonstrate blind empirical discrimination.",
        "reason": "The current path demotes traps using truth_role before final evaluation.",
    },
    {
        "lane": "forbidden",
        "claim": "Manuscript v2 or DTA transfer is earned.",
        "reason": "Both wait for a frozen role-free witness, exact lineage path, and unseen-family holdout.",
    },
]

GO_NO_GO_ROWS = [
    {"target": "manuscript_v2_upgrade", "decision": "hold", "reason": "v1.7.10 closeout is superseded as construction-bound"},
    {"target": "v1.8_observable_schema_label_firewall", "decision": "go_local_coding_only", "reason": "this is the next corrective implementation boundary"},
    {"target": "dta_transfer", "decision": "hold", "reason": "ZeroGate has not earned blind synthetic transfer testing"},
    {"target": "role_blind_discovery_language", "decision": "resist", "reason": "role-free scorer not implemented"},
    {"target": "physics_or_cosmology_language", "decision": "resist", "reason": "outside the evidence boundary"},
    {"target": "zenodo_or_release", "decision": "hold", "reason": "requires separate release authority after corrective evidence"},
]


def _load_integrity_decision(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evidence-integrity decision must be a JSON object")
    required = {
        "version",
        "decision",
        "answer_symbol",
        "scientific_status",
        "evidence_status",
        "core_question_closed",
        "accounting_integrity_passed",
        "canonical_contract_id",
        "canonical_contract_sha256",
        "canonical_contract_passed",
        "legacy_pooled_totals_valid",
        "unique_union_counts",
        "legacy_non_independent_pooled_counts",
        "reason_codes",
        "manuscript_v2_go",
        "dta_transfer_go",
        "release_go",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"evidence-integrity decision missing fields: {', '.join(missing)}")
    if value["version"] != CURRENT_VERSION:
        raise ValueError(f"expected integrity decision version {CURRENT_VERSION}, got {value['version']!r}")
    expected_exact = {
        "decision": "evidence_integrity_correction_hold",
        "answer_symbol": "0/HOLD",
        "scientific_status": "HOLD_CONSTRUCTION_BOUND",
        "evidence_status": "INVALID_FOR_BLIND_EMPIRICAL_DISCRIMINATION",
        "core_question_closed": False,
        "legacy_pooled_totals_valid": False,
        "manuscript_v2_go": False,
        "dta_transfer_go": False,
        "release_go": False,
    }
    for field, expected in expected_exact.items():
        if value.get(field) != expected:
            raise ValueError(f"integrity decision field {field!r} must be {expected!r}")
    if not isinstance(value.get("accounting_integrity_passed"), bool):
        raise ValueError("accounting_integrity_passed must be boolean")
    if value.get("canonical_contract_id") != CANONICAL_CONTRACT_ID:
        raise ValueError("integrity decision has the wrong canonical_contract_id")
    if value.get("canonical_contract_sha256") != canonical_contract_sha256():
        raise ValueError("integrity decision has the wrong canonical_contract_sha256")
    if value.get("canonical_contract_passed") is not True:
        raise ValueError("integrity decision did not satisfy the canonical evidence contract")
    reason_codes = value.get("reason_codes")
    required_reasons = {
        "CONSTRUCTION_BOUND_FALSE_CROWNS",
        "NESTED_RUNG_POOLING_CORRECTED",
        "ROLE_FREE_WITNESS_NOT_IMPLEMENTED",
        "LINEAGE_NOT_IN_FINAL_PATH",
    }
    if not isinstance(reason_codes, list) or not required_reasons <= set(reason_codes):
        raise ValueError("integrity decision is missing required reason codes")

    def validate_counts(block: object, *, name: str) -> None:
        if not isinstance(block, dict):
            raise ValueError(f"{name} must be an object")
        required_counts = set(COUNT_KEYS)
        if set(block) != required_counts:
            raise ValueError(f"{name} must contain exactly the authorized count fields")
        opportunities = block["opportunities"]
        if not isinstance(opportunities, int) or isinstance(opportunities, bool) or opportunities <= 0:
            raise ValueError(f"{name}.opportunities must be a positive integer")
        for field in required_counts - {"opportunities"}:
            count = block[field]
            if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > opportunities:
                raise ValueError(f"{name}.{field} must satisfy 0 <= count <= opportunities")

    validate_counts(value["legacy_non_independent_pooled_counts"], name="legacy_non_independent_pooled_counts")
    accounting_passed = value["accounting_integrity_passed"] is True
    if accounting_passed:
        validate_counts(value["unique_union_counts"], name="unique_union_counts")
    elif value["unique_union_counts"] is not None:
        raise ValueError("failed accounting must not issue unique_union_counts")
    return value


def _condition_rows(integrity: Mapping[str, object] | None) -> list[dict[str, object]]:
    accounting_passed = bool(integrity and integrity.get("accounting_integrity_passed") is True)
    return [
        {
            "condition": "evidence_integrity_artifact",
            "status": "pass_accounting_only" if accounting_passed else ("hold_failed" if integrity else "hold_missing"),
            "evidence": (
                "v1.7.11 integrity decision supplied and accounting passed"
                if accounting_passed
                else ("supplied integrity decision failed accounting" if integrity else "no integrity decision supplied")
            ),
            "boundary": "artifact presence does not establish blind discrimination",
        },
        {
            "condition": "nested_rung_accounting",
            "status": "pass_accounting_only" if accounting_passed else "hold",
            "evidence": "unique atomic union computed" if accounting_passed else "unique-union accounting not verified",
            "boundary": "corrected accounting only",
        },
        {
            "condition": "role_free_scoring",
            "status": "fail",
            "evidence": "current earned-one/final path consumes truth role",
            "boundary": "construction-bound zero false crowns cannot close the question",
        },
        {
            "condition": "false_crown_failure_capability",
            "status": "hold",
            "evidence": "deliberate post-prediction false-crown injection is not implemented",
            "boundary": "zero errors alone cannot pass",
        },
        {
            "condition": "lineage_in_final_path",
            "status": "hold",
            "evidence": "lineage is emitted beside rather than consumed by final verdict",
            "boundary": "manuscript lineage claim not implemented",
        },
        {
            "condition": "independent_generator_holdout",
            "status": "hold",
            "evidence": "current rungs use one controlled generator family line",
            "boundary": "new seeds are not independent generator validation",
        },
    ]


def _evidence_rows(integrity: Mapping[str, object] | None) -> list[dict[str, object]]:
    if integrity is None:
        return [
            {
                "aggregation": "not_available",
                "valid_as_unique_evidence": "false",
                "reason": "no v1.7.11 evidence-integrity decision supplied",
            }
        ]
    accounting_passed = integrity.get("accounting_integrity_passed") is True
    unique = integrity["unique_union_counts"]
    legacy = integrity["legacy_non_independent_pooled_counts"]
    if not isinstance(legacy, dict):
        raise ValueError("legacy count block must be a JSON object")
    count_fields = list(COUNT_KEYS)
    rows: list[dict[str, object]] = []
    if accounting_passed and isinstance(unique, dict):
        rows.append(
            {
                "aggregation": "unique_atomic_union_descriptive",
                "valid_as_unique_evidence": "true",
                **{field: unique.get(field, "") for field in count_fields},
                "reason": "deduplicated accounting; still role-aware construction output",
            }
        )
    else:
        rows.append(
            {
                "aggregation": "unique_atomic_union_not_issued",
                "valid_as_unique_evidence": "false",
                **{field: "" for field in count_fields},
                "reason": "accounting integrity did not pass",
            }
        )
    rows.append(
        {
            "aggregation": "legacy_nested_arithmetic_sum",
            "valid_as_unique_evidence": "false",
            **{field: legacy.get(field, "") for field in count_fields},
            "reason": "triad/deep/wide are nested views and cannot be pooled as independent evidence",
        }
    )
    return rows


def _answer_status_row(integrity: Mapping[str, object] | None) -> dict[str, object]:
    return {
        "version": CURRENT_VERSION,
        "historical_version": HISTORICAL_VERSION,
        "answer_symbol": ANSWER_SYMBOL,
        "answer_status": ANSWER_STATUS,
        "decision": DECISION,
        "native_witness": NATIVE_WITNESS,
        "integrity_artifact_supplied": str(integrity is not None).lower(),
        "core_question_closed": "false",
        "manuscript_v2_go": "false",
        "dta_transfer_go": "false",
        "next_gate": NEXT_GATE,
    }


def _write_read(path: Path, integrity: Mapping[str, object] | None, conditions: list[dict[str, object]]) -> None:
    if integrity and integrity.get("accounting_integrity_passed") is True:
        unique = integrity["unique_union_counts"]
        legacy = integrity["legacy_non_independent_pooled_counts"]
        if not isinstance(unique, dict) or not isinstance(legacy, dict):
            raise ValueError("validated integrity count blocks are missing")
        accounting = (
            f"Unique union opportunities: `{unique['opportunities']}`; "
            f"legacy nested arithmetic opportunities: `{legacy['opportunities']}`."
        )
    elif integrity:
        accounting = "The supplied integrity artifact failed accounting; no unique-union counts are authorized."
    else:
        accounting = "No v1.7.11 evidence-integrity artifact was supplied; accounting remains unverified."
    lines = [
        "# v1.7.11-alpha — Core Question Reopened",
        "",
        f"**Answer:** `{ANSWER_SYMBOL}`",
        f"**Status:** `{ANSWER_STATUS}`",
        f"**Native witness:** `{NATIVE_WITNESS}`",
        "",
        f"> {CORE_QUESTION}",
        "",
        "The current answer is HOLD. v1.7.10-alpha remains reproducible historical release state, but its +1 closeout is superseded because zero false crowns were construction-bound and the three rungs were pooled despite nesting.",
        "",
        accounting,
        "",
        "## Current conditions",
        "",
        "| condition | status | evidence | boundary |",
        "|---|---|---|---|",
    ]
    for row in conditions:
        lines.append(f"| {row['condition']} | {row['status']} | {row['evidence']} | {row['boundary']} |")
    lines.extend(
        [
            "",
            "## Holds",
            "",
            "- Manuscript v2: HOLD.",
            "- DTA transfer: HOLD.",
            "- Scientific thresholds and frozen holdout: HOLD until the role-free scorer exists.",
            "- Release / Zenodo: HOLD pending separate authority.",
            "",
            "## Next movement",
            "",
            f"`{NEXT_GATE}`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_v1_7_core_question_closeout(
    out_dir: Path,
    *,
    evidence_integrity_decision: Path | None = None,
) -> dict[str, Path]:
    out_dir = ensure_dir(out_dir)
    paths = {key: out_dir / name for key, name in OUTPUT_FILES.items()}
    integrity = _load_integrity_decision(evidence_integrity_decision)
    conditions = _condition_rows(integrity)
    evidence = _evidence_rows(integrity)

    _write_read(paths["read"], integrity, conditions)
    write_dict_rows_csv(paths["answer_status"], [_answer_status_row(integrity)])
    write_dict_rows_csv(paths["condition_status"], conditions)
    write_dict_rows_csv(paths["boundary"], BOUNDARY_ROWS)
    write_dict_rows_csv(paths["go_no_go"], GO_NO_GO_ROWS)
    write_dict_rows_csv(paths["evidence"], evidence)

    decision = {
        "version": CURRENT_VERSION,
        "historical_version": HISTORICAL_VERSION,
        "historical_status": "superseded_as_construction_bound",
        "decision": DECISION,
        "answer_symbol": ANSWER_SYMBOL,
        "answer_status": ANSWER_STATUS,
        "core_question": CORE_QUESTION,
        "core_question_closed": False,
        "native_witness_unchanged": NATIVE_WITNESS,
        "native_math_mutated": False,
        "evidence_integrity_artifact_supplied": integrity is not None,
        "accounting_integrity_passed": bool(integrity and integrity.get("accounting_integrity_passed") is True),
        "full_answer_conditions_passed": False,
        "manuscript_v2_go": "hold",
        "dta_transfer_go": "hold",
        "role_blind_discovery_claimed": False,
        "independent_generator_validation_claimed": False,
        "physics_or_cosmology_claimed": False,
        "next_gate": NEXT_GATE,
    }
    if integrity and integrity.get("accounting_integrity_passed") is True:
        decision["unique_union_counts"] = integrity["unique_union_counts"]
        decision["legacy_non_independent_pooled_counts"] = integrity["legacy_non_independent_pooled_counts"]
    elif integrity:
        decision["unique_union_counts"] = None
        decision["legacy_non_independent_pooled_counts"] = integrity["legacy_non_independent_pooled_counts"]
    paths["decision"].write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    paths["bundle"] = write_evidence_bundle(
        out_dir,
        bundle_name=OUTPUT_FILES["bundle"],
        bundle_kind="v1_7_11_core_question_reopened_bundle",
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the v1.7.11 corrected HOLD closeout report.")
    parser.add_argument("--evidence-integrity-decision", type=Path)
    parser.add_argument("--out", type=Path, default=Path("runs/v1_7_11_core_question_reopened"))
    args = parser.parse_args(argv)
    paths = build_v1_7_core_question_closeout(
        args.out,
        evidence_integrity_decision=args.evidence_integrity_decision,
    )
    print(f"Wrote {paths['read']}")
    print(f"Wrote {paths['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
