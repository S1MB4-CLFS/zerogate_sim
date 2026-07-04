from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from zerogate_sim.four_gate_reconciliation_report import (
    SAFE_PUBLIC_CORRECTION_SENTENCE,
    historical_corpus_rows,
    native_gate_rows,
    scan_claim_language,
    write_four_gate_reconciliation_report,
)


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_reconciliation_constants_separate_four_native_gates_from_three_historical_corpora():
    gates = native_gate_rows()
    assert [row["gate"] for row in gates] == ["distinction", "polarity", "relation", "return"]
    assert gates[-1]["symbol"] == "B"
    assert "not dedicated first-alpha corpus" in gates[-1]["historical_status"]

    corpora = historical_corpus_rows()
    dedicated = [row for row in corpora if row["first_alpha_role"] == "dedicated adversarial corpus"]
    assert [row["historical_corpus"] for row in dedicated] == ["distinction", "polarity", "relation"]
    return_row = [row for row in corpora if row["historical_corpus"] == "return"][0]
    assert return_row["counts_as_native_gate"] is True
    assert return_row["counts_as_dedicated_return_corpus"] is False


def test_scan_claim_language_finds_forbidden_backdating_phrase(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("This says first-alpha four-gate proof, which is not earned.", encoding="utf-8")

    hits = scan_claim_language([bad])

    assert hits
    assert hits[0]["phrase"] == "first-alpha four-gate proof"
    assert hits[0]["status"] == "forbidden_claim_language"


def test_write_four_gate_reconciliation_report_outputs_boundary_and_bundle(tmp_path):
    paths = write_four_gate_reconciliation_report(output_dir=tmp_path, repo_root=Path.cwd())

    read = paths["four_gate_reconciliation_read"].read_text(encoding="utf-8")
    note = paths["zenodo_version_correction_note"].read_text(encoding="utf-8")
    audit = json.loads(paths["four_gate_reconciliation_audit"].read_text(encoding="utf-8"))
    native = _csv_rows(paths["four_gate_native_witness"])
    historical = _csv_rows(paths["first_alpha_historical_corpora"])

    assert "three-corpus pre-return adversarial proof" in read
    assert "not independently adversarialized as a fourth first-alpha corpus" in read
    assert SAFE_PUBLIC_CORRECTION_SENTENCE in note
    assert audit["native_gate_count"] == 4
    assert audit["historical_first_alpha_corpus_count"] == 3
    assert audit["return_adversary_profile_present"] is True
    assert audit["four_gate_presets_cover_native_gates"] is True
    assert audit["claim_language_forbidden_hits"] == 0
    assert [row["gate"] for row in native] == ["distinction", "polarity", "relation", "return"]
    assert any(row["historical_corpus"] == "return" and row["counts_as_dedicated_return_corpus"] == "False" for row in historical)
    assert paths["four_gate_reconciliation_bundle"].exists()


def test_reconciliation_report_strict_mode_rejects_forbidden_claim_language(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (repo / "README.md").write_text("first-alpha four-gate proof", encoding="utf-8")

    with pytest.raises(ValueError, match="Forbidden first-alpha/four-gate claim language"):
        write_four_gate_reconciliation_report(output_dir=tmp_path / "out", repo_root=repo)
