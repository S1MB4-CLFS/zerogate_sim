from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_6_24_version_truth_and_public_surface() -> None:
    assert "1.7.5-alpha" in read("src/zerogate_sim/__init__.py")
    assert 'version = "1.7.5a0"' in read("pyproject.toml")
    for path in ["README.md", "ROADMAP.md", "docs/version_truth.md", "docs/release_notes/v1_6_25_alpha.md"]:
        assert "v1.6.25-alpha" in read(path)
    assert "v1.6.23-alpha" in read("docs/release_notes/v1_6_23_alpha.md")


def test_readme_uses_current_evidence_cards_not_legacy_cards() -> None:
    readme = read("README.md")
    for needle in [
        "four_gates_triad27_debt_evidence_card.svg",
        "four_gates_deepwide_debt_evidence_card.svg",
        "four_gates_fresh_seed_debt_reproduction_card.svg",
    ]:
        assert needle in readme
    for needle in [
        "first_research_alpha_proof_card.svg",
        "fresh_controlled_deep81_evidence_card.svg",
        "fresh_controlled_wide243_evidence_card.svg",
        "role_blind_shadow_design_card.svg",
        "shadow_baseline_falsifier_card.svg",
    ]:
        assert needle not in readme


def test_history_vault_preserves_shadow_and_legacy_visuals() -> None:
    vault = read("docs/history_vault/README.md")
    shadow = read("docs/history_vault/shadow_route_history_and_closeout.md")
    legacy = read("docs/history_vault/legacy_evidence_visuals.md")
    assert "historical witness shelf" in vault
    assert "role-blind discovery: not earned" in shadow
    assert "pressure amount != false-one kind" in shadow
    assert "first_research_alpha_proof_card.svg" in legacy
    assert "shadow_baseline_falsifier_card.svg" in legacy


def test_runs_vault_plan_is_no_delete_and_names_canonical_folders() -> None:
    plan = read("docs/history_vault/runs_history_vault_plan.md")
    assert "No-delete" not in plan  # title is lowercase/no-delete elsewhere; avoid accidental shouting-only contract
    assert "no-delete plan" in plan
    assert "four_gates_deepwide_debt_v1_6_21" in plan
    assert "four_gates_fresh_seed_reproduction_v1_6_22" in plan
    assert "Compress-Archive" in plan
    assert "Do not delete by vibes" in plan
