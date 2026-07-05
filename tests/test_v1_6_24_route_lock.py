from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1_6_24_surfaces_how_it_works_and_current_route() -> None:
    readme = read("README.md")
    assert "v1.6.24-alpha" in readme
    assert "## How it works" in readme
    assert readme.index("## Why this exists") < readme.index("## How it works") < readme.index("## First visual spine")
    assert "raw expression is pressure, not truth" in readme
    assert "0 structured zero" in readme
    assert "computational approximation of zero-zone gating" in readme
    assert "anti-tautology audit -> reproduction command package -> manuscript correction package" in readme


def test_v1_6_24_locks_remaining_v1_6_route() -> None:
    roadmap = read("ROADMAP.md")
    for needle in [
        "v1.6.25-alpha",
        "Anti-Tautology Audit / Role-Dependence Check",
        "v1.6.26-alpha",
        "Reproduction Command Package",
        "v1.6.27-alpha",
        "Manuscript Correction Package",
        "v1.6 closeout",
        "earned / partial / demoted decision",
        "v1.7 boundary",
        "The Four Gates witness operationalizes a synthetic zero-zone gating principle",
    ]:
        assert needle in roadmap
    assert "C_Z = min(D, P, R, B)" in roadmap
    assert "observed-universe bridge" in roadmap


def test_v1_6_24_adds_evidence_index_and_audit_plan() -> None:
    evidence = read("docs/current_evidence_index.md")
    audit = read("docs/anti_tautology_audit_plan.md")
    release = read("docs/release_notes/v1_6_24_alpha.md")
    version_truth = read("docs/version_truth.md")
    assert "v1.6.24-alpha" in evidence
    assert "canonical current evidence" in evidence
    assert "latent overcrown did not reproduce" in evidence
    assert "Role dependence" in audit
    assert "Masked evaluation" in audit
    assert "+1 earned audit" in audit
    assert "v1.6.25-alpha" in release
    assert "v1.6.24-alpha" in version_truth
