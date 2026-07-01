from __future__ import annotations

import zipfile

from zerogate_sim.test_handoff import build_test_handoff


def test_build_test_handoff_creates_assistant_zip(tmp_path) -> None:
    include = tmp_path / "sample.txt"
    include.write_text("green gates\n", encoding="utf-8")

    paths = build_test_handoff(
        out_dir=tmp_path / "handoff",
        version="v1.3.1-alpha",
        status="passed",
        notes=["unit tests passed"],
        repo_root=tmp_path,
        includes=[include],
    )

    assert paths["assistant_test_handoff_md"].exists()
    assert paths["assistant_test_handoff_json"].exists()
    assert paths["assistant_test_handoff_zip"].exists()

    text = paths["assistant_test_handoff_md"].read_text(encoding="utf-8")
    assert "v1.3.1-alpha" in text
    assert "unit tests passed" in text

    with zipfile.ZipFile(paths["assistant_test_handoff_zip"]) as zf:
        names = set(zf.namelist())
    assert "assistant_test_handoff.md" in names
    assert "assistant_test_handoff.json" in names
    assert "included/sample.txt" in names
