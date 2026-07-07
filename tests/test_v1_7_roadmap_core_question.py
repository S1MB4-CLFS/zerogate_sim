from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_7_roadmap_is_question_first_and_native_witness_locked() -> None:
    roadmap = read("ROADMAP.md")
    assert "## v1.7 boundary" in roadmap
    assert (
        "Can a final trinary witness distinguish earned-one from raw expression pressure, "
        "latent overcrown, relation debt, return debt, and false-one pressure under "
        "controlled synthetic-field adversarial weather?"
    ) in roadmap
    assert "C_Z = min(D, P, R, B)" in roadmap
    assert "No `v1.7` step may mutate the native witness" in roadmap
    assert "v1.7 answer grammar" in roadmap
    assert "v1.7 full-answer conditions" in roadmap


def test_v1_7_roadmap_names_all_answer_gates_and_closeout() -> None:
    roadmap = read("ROADMAP.md")
    for needle in [
        "Lane visibility",
        "Earned-one preservation",
        "False-one safety",
        "Structured zero",
        "Return specificity",
        "Baseline superiority",
        "Role-dependence audit",
        "Fresh / holdout pressure",
        "Reviewer path",
        "v1.7.7-alpha",
        "Anti-Tautology Audit / Role-Dependence Check",
        "v1.7.8-alpha",
        "Reviewer Start Here / Reproduction Package",
        "v1.7.9-alpha",
        "Core Question Closeout",
    ]:
        assert needle in roadmap


def test_manuscript_v2_is_before_v1_8_and_is_not_software_v2_0() -> None:
    roadmap = read("ROADMAP.md")
    manuscript_gate = roadmap.index("## Manuscript v2 upgrade gate")
    v18_boundary = roadmap.index("## v1.8 boundary")
    software_v20 = roadmap.index("## v2.0 boundary")
    assert manuscript_gate < v18_boundary < software_v20
    assert "This is **manuscript v2**, not software `v2.0`." in roadmap
    assert "manuscript v2 has been drafted or deliberately frozen" in roadmap


def test_later_roadmap_keeps_role_blind_and_external_claims_bounded() -> None:
    roadmap = read("ROADMAP.md")
    assert "role-stripped features -> transparent score -> baseline/falsifier -> holdout -> maybe shadow closeout" in roadmap
    assert "Never skip from score to discovery." in roadmap
    assert "Stable external-review release package" in roadmap
    assert "Permanent HOLD / RESIST lanes" in roadmap
    assert "observed-universe bridge" in roadmap
    assert "No science without falsifier." in roadmap
