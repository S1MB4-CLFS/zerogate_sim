from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_controlled_synthetic_field_language_doc_defines_allowed_ladder() -> None:
    text = _read("docs/controlled_synthetic_field_language.md")
    assert "generated toy field" in text
    assert "controlled synthetic field" in text
    assert "adversarial synthetic benchmark" in text
    assert "wide243 = 3^5" in text
    assert "temporal-depth / time-axis pressure" in text
    assert "does not mean" in text
    assert "physics proof" in text


def test_readme_and_roadmap_link_language_doc() -> None:
    readme = _read("README.md")
    roadmap = _read("ROADMAP.md")
    assert "docs/controlled_synthetic_field_language.md" in readme
    assert "controlled synthetic-field language boundary" in readme
    assert "controlled synthetic-field language boundary" in roadmap
    assert "generated toy-field proof record" in roadmap


def test_runtime_history_bloat_stays_out_of_readme_and_roadmap() -> None:
    readme = _read("README.md")
    roadmap = _read("ROADMAP.md")
    combined = readme + "\n" + roadmap
    assert "GitHub Actions showed" not in combined
    assert "Python 3.10 / 3.11 / 3.12" not in combined
    assert "3.10 / 3.11" not in combined
    assert "docs/runtime_ci_support.md" in combined


def test_controlled_synthetic_field_boundary_does_not_claim_physics() -> None:
    text = _read("docs/controlled_synthetic_field_language.md")
    forbidden = [
        "proves cosmology",
        "proves physical dimensional genesis",
        "proves that reality itself is trinary",
    ]
    for phrase in forbidden:
        assert phrase not in text.lower()
