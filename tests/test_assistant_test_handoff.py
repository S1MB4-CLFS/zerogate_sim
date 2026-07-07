from __future__ import annotations

import json
import zipfile

import pytest

from zerogate_sim.test_handoff import build_test_handoff


def test_build_test_handoff_creates_assistant_zip(tmp_path) -> None:
    include = tmp_path / "sample.txt"
    include.write_text("green gates\n", encoding="utf-8")

    paths = build_test_handoff(
        out_dir=tmp_path / "handoff",
        version="v1.4.3-alpha",
        status="passed",
        notes=["unit tests passed"],
        repo_root=tmp_path,
        includes=[include],
    )

    assert paths["assistant_test_handoff_md"].exists()
    assert paths["assistant_test_handoff_json"].exists()
    assert paths["assistant_test_handoff_zip"].exists()

    text = paths["assistant_test_handoff_md"].read_text(encoding="utf-8")
    assert "v1.4.3-alpha" in text
    assert "unit tests passed" in text
    assert "Missing include count: `0`" in text
    assert "included/sample.txt" in text

    data = json.loads(paths["assistant_test_handoff_json"].read_text(encoding="utf-8"))
    assert data["missing_include_count"] == 0
    assert data["strict_includes"] is True
    assert data["included_files"] == ["included/sample.txt"]
    assert data["include_results"][0]["source_relative_path"] == "sample.txt"

    with zipfile.ZipFile(paths["assistant_test_handoff_zip"]) as zf:
        names = set(zf.namelist())
    assert "assistant_test_handoff.md" in names
    assert "assistant_test_handoff.json" in names
    assert "included/sample.txt" in names


def test_build_test_handoff_fails_on_missing_include_by_default(tmp_path) -> None:
    missing = tmp_path / "missing_report.md"

    with pytest.raises(FileNotFoundError) as exc:
        build_test_handoff(
            out_dir=tmp_path / "handoff",
            version="v1.4.3-alpha",
            status="passed",
            repo_root=tmp_path,
            includes=[missing],
        )

    assert "missing_report.md" in str(exc.value)
    assert "path does not exist" in str(exc.value)


def test_build_test_handoff_can_record_missing_include_when_explicitly_allowed(tmp_path) -> None:
    missing = tmp_path / "optional_report.md"

    paths = build_test_handoff(
        out_dir=tmp_path / "handoff",
        version="v1.4.3-alpha",
        status="partial",
        repo_root=tmp_path,
        includes=[missing],
        allow_missing_includes=True,
    )

    data = json.loads(paths["assistant_test_handoff_json"].read_text(encoding="utf-8"))
    assert data["missing_include_count"] == 1
    assert data["strict_includes"] is False
    assert data["missing_includes"][0]["source"].endswith("optional_report.md")

    text = paths["assistant_test_handoff_md"].read_text(encoding="utf-8")
    assert "Missing include count: `1`" in text
    assert "optional_report.md" in text


def test_build_test_handoff_preserves_same_basename_includes(tmp_path) -> None:
    repo = tmp_path / "repo"
    distinction = repo / "runs" / "cross_logic_presets" / "adversary_triad27" / "distinction_triad27" / "matrix_known_logic_closeout_read.md"
    polarity = repo / "runs" / "cross_logic_presets" / "adversary_triad27" / "polarity_triad27" / "matrix_known_logic_closeout_read.md"
    relation = repo / "runs" / "cross_logic_presets" / "adversary_triad27" / "relation_triad27" / "matrix_known_logic_closeout_read.md"
    distinction.parent.mkdir(parents=True)
    polarity.parent.mkdir(parents=True)
    relation.parent.mkdir(parents=True)
    distinction.write_bytes(b"distinction result\n")
    polarity.write_bytes(b"polarity result\n")
    relation.write_bytes(b"relation result\n")

    paths = build_test_handoff(
        out_dir=repo / "handoff",
        version="v1.4.3-alpha",
        status="passed",
        repo_root=repo,
        includes=[distinction, polarity, relation],
    )

    data = json.loads(paths["assistant_test_handoff_json"].read_text(encoding="utf-8"))
    assert data["missing_include_count"] == 0
    assert data["included_files"] == [
        "included/runs/cross_logic_presets/adversary_triad27/distinction_triad27/matrix_known_logic_closeout_read.md",
        "included/runs/cross_logic_presets/adversary_triad27/polarity_triad27/matrix_known_logic_closeout_read.md",
        "included/runs/cross_logic_presets/adversary_triad27/relation_triad27/matrix_known_logic_closeout_read.md",
    ]

    with zipfile.ZipFile(paths["assistant_test_handoff_zip"]) as zf:
        names = set(zf.namelist())
        assert data["included_files"][0] in names
        assert data["included_files"][1] in names
        assert data["included_files"][2] in names
        assert zf.read(data["included_files"][0]).decode("utf-8") == "distinction result\n"
        assert zf.read(data["included_files"][1]).decode("utf-8") == "polarity result\n"
        assert zf.read(data["included_files"][2]).decode("utf-8") == "relation result\n"

    text = paths["assistant_test_handoff_md"].read_text(encoding="utf-8")
    assert "distinction_triad27/matrix_known_logic_closeout_read.md" in text
    assert "polarity_triad27/matrix_known_logic_closeout_read.md" in text
    assert "relation_triad27/matrix_known_logic_closeout_read.md" in text


def test_build_test_handoff_classifies_full_compressed_and_visual_outputs(tmp_path) -> None:
    repo = tmp_path / "repo"
    full = repo / "runs" / "v1_7_6" / "reports" / "full" / "system_output_report.md"
    compressed = repo / "runs" / "v1_7_6" / "reports" / "summary" / "compressed_state.md"
    visual = repo / "runs" / "v1_7_6" / "reports" / "visuals" / "holdout_card.svg"
    generic = repo / "runs" / "v1_7_6" / "reports" / "machine" / "decision.json"
    for path, content in [
        (full, "full output\n"),
        (compressed, "compressed state\n"),
        (visual, "<svg></svg>\n"),
        (generic, "{}\n"),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    paths = build_test_handoff(
        out_dir=repo / "handoff",
        version="v1.7.7-alpha",
        status="passed",
        repo_root=repo,
        notes=["triad27 rung inspected before deeper weather"],
        full_output_reports=[full],
        compressed_summaries=[compressed],
        visual_outputs=[visual],
        includes=[generic],
        report_label_notes=["Included historical debt-evidence reports may retain internal report-version labels; active package boundary remains v1.7.7-alpha."],
    )

    data = json.loads(paths["assistant_test_handoff_json"].read_text(encoding="utf-8"))
    assert data["missing_include_count"] == 0
    assert data["handoff_output_contract"]["local_run_artifacts_are_repo_truth"] is False
    assert data["full_output_reports"] == ["included/runs/v1_7_6/reports/full/system_output_report.md"]
    assert data["compressed_summaries"] == ["included/runs/v1_7_6/reports/summary/compressed_state.md"]
    assert data["visual_outputs"] == ["included/runs/v1_7_6/reports/visuals/holdout_card.svg"]
    assert data["generic_includes"] == ["included/runs/v1_7_6/reports/machine/decision.json"]
    assert data["report_label_notes"]

    text = paths["assistant_test_handoff_md"].read_text(encoding="utf-8")
    assert "Full output reports" in text
    assert "Compressed summaries" in text
    assert "Visual outputs" in text
    assert "Report label notes" in text
    assert "historical debt-evidence reports" in text

    with zipfile.ZipFile(paths["assistant_test_handoff_zip"]) as zf:
        names = set(zf.namelist())
    assert data["full_output_reports"][0] in names
    assert data["compressed_summaries"][0] in names
    assert data["visual_outputs"][0] in names
    assert data["generic_includes"][0] in names
