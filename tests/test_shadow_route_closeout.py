from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_truth_surfaces_include_current_and_preserve_shadow_closeout() -> None:
    assert "1.7.4-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.4a0"' in read("pyproject.toml")
    assert "v1.6.28-alpha" in read("README.md")
    assert "v1.6.28-alpha" in read("ROADMAP.md")
    assert "v1.6.14-alpha" in read("docs/version_truth.md")
    assert "v1.6.18-alpha" in read("docs/version_truth.md")
    assert "v1.6.13-alpha" in read("docs/history_vault/shadow_route_history_and_closeout.md")
    assert "v1.6.13-alpha" in read("docs/version_truth.md")


def test_shadow_route_is_closeout_not_active_claim() -> None:
    readme = read("README.md")
    roadmap = read("ROADMAP.md")
    closeout = read("docs/history_vault/shadow_route_history_and_closeout.md")

    assert "docs/history_vault/README.md" in readme
    assert "history vault" in roadmap
    assert "role-blind discovery: not earned" in closeout
    assert "pressure amount != false-one kind" in closeout


def test_readme_no_longer_surfaces_shadow_visual_cards() -> None:
    readme = read("README.md")
    forbidden = [
        "role_blind_shadow_design_card.svg",
        "role_stripped_feature_extraction_card.svg",
        "transparent_shadow_score_card.svg",
        "shadow_baseline_falsifier_card.svg",
    ]
    for needle in forbidden:
        assert needle not in readme


def test_roadmap_blocks_deeper_shadow_trust() -> None:
    roadmap = read("ROADMAP.md")
    assert "stable external-review release package" in roadmap
    assert "No more one-more-feature drift" not in roadmap
    assert "v1.6.20-alpha" in roadmap
    assert "v1.6.22-alpha" in roadmap
    assert "fresh-seed" in roadmap
