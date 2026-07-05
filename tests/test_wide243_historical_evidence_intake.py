from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_wide243_historical_report_preserves_numbers_and_boundary() -> None:
    text = _read("docs/reports/wide243_historical_evidence_intake.md")

    required = [
        "13,122",
        "22,131",
        "2,388",
        "2,442",
        "0 final false-one crowns",
        "historical first-research-alpha",
        "generated toy fields",
        "controlled synthetic-field",
        "not prove cosmology",
        "not role-blind",
    ]

    for needle in required:
        assert needle in text


def test_wide243_report_explains_27_81_243_and_time_axis() -> None:
    text = _read("docs/reports/wide243_historical_evidence_intake.md")

    for needle in [
        "triad27 = 3^3",
        "deep81 = 3^4",
        "wide243 = 3^5",
        "time_axis",
        "temporal-depth",
        "stretched temporal field",
    ]:
        assert needle in text


def test_wide243_report_separates_native_return_from_dedicated_return_adversary() -> None:
    text = _read("docs/reports/wide243_historical_evidence_intake.md")

    assert "C_Z = min(D, P, R, B)" in text
    assert "dedicated return-adversary proof" in text
    assert "historical `wide243` archives as role-blind discovery" in text


def test_readme_and_roadmap_point_to_wide243_intake() -> None:
    readme = _read("docs/history_vault/legacy_evidence_visuals.md")
    roadmap = _read("docs/history_vault/ROADMAP_v1_6_22_snapshot.md")

    assert "`v1.5.4-alpha`" in readme
    assert "docs/reports/wide243_historical_evidence_intake.md" in readme
    assert "### v1.5.4-alpha — Wide243 historical evidence intake" in roadmap
    assert "run fresh controlled `deep81` four-gate evidence" in roadmap
