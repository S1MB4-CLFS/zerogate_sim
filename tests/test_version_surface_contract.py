from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from zerogate_sim import __version__


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_VERSION = "1.8.1-alpha"
PACKAGE_VERSION = "1.8.1a0"
SCIENTIFIC_AUTHORITY = "v1.7.11-alpha"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_current_version_has_one_central_package_authority() -> None:
    pyproject = tomllib.loads(read("pyproject.toml"))
    assert __version__ == DEVELOPMENT_VERSION
    assert pyproject["project"]["version"] == PACKAGE_VERSION
    assert (
        pyproject["project"]["scripts"][
            "zerogate-v1-8-1-lineage-predictor-package"
        ]
        == "zerogate_sim.v1_8_1_lineage_predictor_package:main"
    )


def test_v1_8_required_public_surfaces_are_synchronized() -> None:
    required = {
        "README.md": ("v1.8.1-alpha", "v1.8.0-alpha", SCIENTIFIC_AUTHORITY),
        "ROADMAP.md": ("v1.8.1-alpha", "v1.8.0-alpha", SCIENTIFIC_AUTHORITY),
        "REVIEWER_START_HERE.md": ("v1.8.1-alpha", SCIENTIFIC_AUTHORITY, "0 / HOLD"),
        "AGENTS.md": ("v1.8.1-alpha", SCIENTIFIC_AUTHORITY, "Coding economics"),
        "docs/version_truth.md": ("v1.8.1-alpha", "v1.8.0-alpha", SCIENTIFIC_AUTHORITY),
        "docs/current_evidence_state.md": ("v1.8.1-alpha", SCIENTIFIC_AUTHORITY),
        "docs/current_evidence_index.md": ("v1.8.1-alpha", SCIENTIFIC_AUTHORITY),
        "docs/recent_native_evidence_history.md": (
            "v1.8.0-alpha",
            "v1.8.1-alpha",
            SCIENTIFIC_AUTHORITY,
        ),
        "docs/claim_boundary.md": ("v1.8.1-alpha", SCIENTIFIC_AUTHORITY),
        "docs/v1_8_observable_schema_label_firewall.md": (
            "LOCAL_GREEN_FIREWALL_ONLY",
            "seven",
            "frozen holdout",
        ),
        "docs/release_notes/v1_8_0_alpha.md": (
            "LOCAL_GREEN_FIREWALL_ONLY",
            "Scientific authority remains",
        ),
        "docs/v1_8_1_lineage_predictor_package.md": (
            "LOCAL_GREEN_LINEAGE_PACKAGE_ONLY",
            "early -> witness -> late",
            "selected_threshold_option: null",
        ),
        "docs/release_notes/v1_8_1_alpha.md": (
            "LOCAL_GREEN_LINEAGE_PACKAGE_ONLY",
            "Scientific authority remains",
        ),
        "docs/workflow_research_ledger.md": (
            "v1.8.0-alpha",
            "not_recorded",
            "auto-merge",
        ),
        "docs/manuscript_v2_empirical_readiness_gate.md": (
            "SUPPORTED_BOUNDED",
            "INVALID_EVIDENCE",
            "FALSIFIED",
        ),
        "docs/history_vault/v1_7_authority_map.md": (
            SCIENTIFIC_AUTHORITY,
            "superseded",
        ),
        "PATCH_MANIFEST_v1_8_0_alpha.txt": (
            "LOCAL_GREEN_FIREWALL_ONLY",
            "no scientific thresholds",
        ),
        "PATCH_MANIFEST_v1_8_1_alpha.txt": (
            "Lineage-Bearing Predictor Package",
            "no scientific threshold selected",
        ),
    }
    for relative, anchors in required.items():
        text = read(relative)
        for anchor in anchors:
            assert anchor in text, f"{relative} is missing {anchor!r}"


def test_protocol_v3_workspace_and_repo_copies_are_identical() -> None:
    repo_copy = ROOT / "docs/UNIVERSAL_CODING_WORKFLOW_v3_CODEX_PROJECT.md"
    workspace_copy = ROOT.parent / "UNIVERSAL_CODING_WORKFLOW_v3_CODEX_PROJECT.md"
    text = repo_copy.read_text(encoding="utf-8")
    assert "## 18. Coding economics" in text
    assert "## 19. Version-surface law" in text
    if workspace_copy.is_file():
        assert hashlib.sha256(repo_copy.read_bytes()).digest() == hashlib.sha256(
            workspace_copy.read_bytes()
        ).digest()
