from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from zerogate_sim import __version__


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_VERSION = "1.8.2-alpha"
PACKAGE_VERSION = "1.8.2a0"
SCIENTIFIC_AUTHORITY = "v1.7.11-alpha"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_current_version_has_one_central_package_authority() -> None:
    pyproject = tomllib.loads(read("pyproject.toml"))
    assert __version__ == DEVELOPMENT_VERSION
    assert pyproject["project"]["version"] == PACKAGE_VERSION
    assert (
        pyproject["project"]["scripts"][
            "zerogate-v1-8-2-development-evaluation"
        ]
        == "zerogate_sim.v1_8_2_development_evaluator:main"
    )
    assert (
        pyproject["project"]["scripts"]["zerogate-v1-8-2-build-development"]
        == "zerogate_sim.v1_8_2_development_split:main"
    )
    assert (
        pyproject["project"]["scripts"]["zerogate-v1-8-2-freeze-prelabel"]
        == "zerogate_sim.v1_8_2_prelabel_freeze:main"
    )


def test_v1_8_required_public_surfaces_are_synchronized() -> None:
    required = {
        "README.md": ("v1.8.2-alpha", "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR", SCIENTIFIC_AUTHORITY),
        "ROADMAP.md": ("v1.8.2-alpha", "piecewise_hysteresis_v1", SCIENTIFIC_AUTHORITY),
        "REVIEWER_START_HERE.md": ("v1.8.2-alpha", SCIENTIFIC_AUTHORITY, "0 / HOLD"),
        "AGENTS.md": ("v1.8.2-alpha", "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR", "Coding economics"),
        "docs/version_truth.md": ("v1.8.2-alpha", "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR", SCIENTIFIC_AUTHORITY),
        "docs/current_evidence_state.md": ("v1.8.2-alpha", "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR", SCIENTIFIC_AUTHORITY),
        "docs/current_evidence_index.md": ("v1.8.2-alpha", "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR", SCIENTIFIC_AUTHORITY),
        "docs/recent_native_evidence_history.md": (
            "v1.8.0-alpha",
            "v1.8.1-alpha",
            "v1.8.2-alpha",
            SCIENTIFIC_AUTHORITY,
        ),
        "docs/claim_boundary.md": ("v1.8.2-alpha", "v1.8.3", SCIENTIFIC_AUTHORITY),
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
        "docs/v1_8_2_failure_capable_development_evaluation.md": (
            "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR",
            "0.58779880167953524",
            "144",
        ),
        "docs/release_notes/v1_8_2_alpha.md": (
            "INVALID_CONSTANT_OR_DEAD_SAFE_PREDICTOR",
            "Scientific authority",
        ),
        "docs/workflow_research_ledger.md": (
            "v1.8.0-alpha",
            "not_recorded",
            "auto-merge",
            "2,000",
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
        "PATCH_MANIFEST_v1_8_2_alpha.txt": (
            "Failure-Capable Development Evaluation",
            "00935943039930113e732ea8f794adce0087458f2fc94d234285b089c440a205",
            "v1.8.3 and v1.8.4 are blocked",
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
    assert "failure-capability fixtures call the same production guard" in text
    assert "spending more cannot buy" in text
    if workspace_copy.is_file():
        assert hashlib.sha256(repo_copy.read_bytes()).digest() == hashlib.sha256(
            workspace_copy.read_bytes()
        ).digest()
