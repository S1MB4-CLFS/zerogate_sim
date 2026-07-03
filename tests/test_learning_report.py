from __future__ import annotations

from pathlib import Path


def test_v1_2_to_v1_4_4_learning_report_has_professional_boundaries() -> None:
    report = Path("docs/reports/v1_2_to_v1_4_4_learning_report.md")
    text = report.read_text(encoding="utf-8")

    assert "v1.4.5-alpha" in text
    assert "Return was already native to the zero-gate cycle" in text
    assert "C_Z = min(D, P, R, B)" in text
    assert "known-logic projection mirrors" in text
    assert "seed-block four-gate adversary report" in text.lower()
    assert "role-blind false-one detection" in text

    lowered = text.lower()
    assert "we missed" not in lowered
    assert "mistake" not in lowered
    assert "apology" not in lowered
