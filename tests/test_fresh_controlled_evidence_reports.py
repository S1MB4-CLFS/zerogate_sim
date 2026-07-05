from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_fresh_controlled_reports_preserve_deep81_and_wide243_numbers() -> None:
    deep = _read("docs/reports/fresh_controlled_deep81_four_gate_evidence_report.md")
    wide = _read("docs/reports/fresh_controlled_wide243_four_gate_evidence_report.md")

    for needle in ["2,916", "5,155", "402", "639", "0 final false-one crowns", "relation adversary"]:
        assert needle in deep

    for needle in ["8,748", "16,217", "1,242", "2,043", "0 final false-one crowns", "stretched temporal field"]:
        assert needle in wide


def test_readme_links_fresh_controlled_visuals_and_reports() -> None:
    readme = _read("docs/history_vault/legacy_evidence_visuals.md")

    for needle in [
        "`v1.5.5-alpha`",
        "docs/assets/fresh_controlled_deep81_evidence_card.svg",
        "docs/assets/fresh_controlled_wide243_evidence_card.svg",
        "docs/reports/fresh_controlled_deep81_four_gate_evidence_report.md",
        "docs/reports/fresh_controlled_wide243_four_gate_evidence_report.md",
        "docs/reports/fresh_controlled_81_243_visual_source.csv",
    ]:
        assert needle in readme


def test_fresh_controlled_assets_exist_and_name_the_boundary() -> None:
    for rel in [
        "docs/assets/fresh_controlled_deep81_evidence_card.svg",
        "docs/assets/fresh_controlled_wide243_evidence_card.svg",
    ]:
        text = _read(rel)
        assert "Controlled synthetic-field evidence" in text
        assert "not physics proof" in text
        assert "C_Z = min(D, P, R, B)" in text


def test_native_math_boundary_survives_v1_5_5() -> None:
    readme = _read("docs/history_vault/legacy_evidence_visuals.md")
    roadmap = _read("docs/history_vault/ROADMAP_v1_6_22_snapshot.md")
    deep = _read("docs/reports/fresh_controlled_deep81_four_gate_evidence_report.md")
    wide = _read("docs/reports/fresh_controlled_wide243_four_gate_evidence_report.md")

    for text in [readme, roadmap, deep, wide]:
        assert "C_Z = min(D, P, R, B)" in text
        assert "not new native gates" in text or "No new native gate" in text


def test_visual_source_csv_contains_both_profiles() -> None:
    text = _read("docs/reports/fresh_controlled_81_243_visual_source.csv")
    assert "deep81_vs_wide243_rates,deep81,raw_false_per_run" in text
    assert "deep81_vs_wide243_rates,wide243,raw_false_per_run" in text
    assert "wide243_time_axis_pressure,plus,breach,1041" in text
