from __future__ import annotations

from typing import Mapping

FEATURE_IMPLEMENTATION_VERSION = "v1.6.12-alpha"

# These columns are observable, role-stripped feature candidates. They are not
# target fields and must be computed before evaluation targets are loaded.
SHADOW_ENGINEERED_FEATURE_COLUMNS: dict[str, str] = {
    "feature_density_residual_proxy_rate": "raw pressure that remains after raw-strength pressure is accounted for",
    "feature_relation_ownership_gap_rate": "relation pressure that is high while earned expression is low or relation is limiting",
    "feature_relation_echo_pressure_rate": "relation debt / echo-dependence pressure from observable relation-debt and echo-style fields",
    "feature_relation_return_divergence_rate": "absolute divergence between relation gate and return gate observables",
    "feature_return_integrity_gap_rate": "return gate weakness relative to relation/weakest-gate pressure",
    "feature_return_strength_mismatch_rate": "raw strength pressure not matched by return-gate coherence",
    "feature_return_memory_pressure_rate": "return-limiting and zero-hold pressure without earned expression",
    "feature_demotion_trajectory_proxy_rate": "observable refusal-pressure proxy from raw pressure, gate imbalance, and demotion-dependence fields",
    "feature_zero_hold_ambiguity_proxy_rate": "structured-zero / not-yet proxy from latent hold, relation debt, and low earned expression",
    "feature_gate_imbalance_rate": "spread between observable strength, weakest-gate, relation-gate, and return-gate pressures",
    "feature_pressure_kind_contrast_rate": "relation/return/gate-shape contrast normalized by raw pressure",
}

ENGINEERED_FEATURE_BOUNDARY = (
    "v1.6.12 engineered shadow features are computed from role-stripped observable "
    "features before targets are loaded; they are not truth-role labels, not targets, "
    "not detector closeout, and not native witness mutation"
)


def _to_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clip(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def _rate_text(value: float) -> str:
    return f"{_clip(value):.6f}"


def engineered_shadow_feature_values(row: Mapping[str, object]) -> dict[str, str]:
    """Return v1.6.12 observable, role-stripped shadow feature candidates.

    These formulas intentionally use only already role-stripped feature columns.
    They do not read native gate labels, truth roles, target rates, answer keys,
    family order, or post-score evaluation outcomes.
    """

    raw_pressure = _to_float(row.get("feature_raw_pressure_rate"))
    raw_strength = _to_float(row.get("feature_raw_strength_pressure_rate"))
    weakest_gate = _to_float(row.get("feature_weakest_gate_pressure_rate"))
    relation_gate = _to_float(row.get("feature_relation_gate_rate"))
    return_gate = _to_float(row.get("feature_return_gate_rate"))
    relation_limiting = _to_float(row.get("feature_relation_limiting_rate"))
    return_limiting = _to_float(row.get("feature_return_limiting_rate"))
    earned = _to_float(row.get("feature_earned_rate"))
    latent_hold = _to_float(row.get("feature_latent_hold_rate"))
    relation_debt = _to_float(row.get("feature_relation_debt_rate"))
    mirror_secondary = _to_float(row.get("feature_mirror_secondary_rate"))
    echo_dependence = _to_float(row.get("feature_ablation_echo_independence_rate"))
    demotion_dependence = _to_float(row.get("feature_ablation_demotion_dependence_rate"))

    values = [raw_strength, weakest_gate, relation_gate, return_gate]
    gate_imbalance = max(values) - min(values)
    relation_return_divergence = abs(relation_gate - return_gate)
    density_residual = max(0.0, raw_pressure - raw_strength)
    relation_ownership_gap = max(0.0, relation_gate - earned) + relation_limiting + relation_debt
    relation_echo = relation_debt + mirror_secondary + echo_dependence
    return_integrity_gap = max(0.0, max(relation_gate, weakest_gate) - return_gate) + return_limiting
    return_strength_mismatch = max(0.0, raw_strength - return_gate)
    return_memory_pressure = return_limiting + max(0.0, latent_hold - earned) + max(0.0, 1.0 - min(1.0, return_gate))
    demotion_trajectory = demotion_dependence + raw_pressure * (gate_imbalance + relation_limiting + return_limiting) / 3.0
    zero_hold_ambiguity = latent_hold + relation_debt + max(0.0, weakest_gate - earned)
    pressure_kind_contrast = (relation_return_divergence + gate_imbalance + relation_limiting + return_limiting) / (1.0 + max(0.0, raw_pressure))

    return {
        "feature_density_residual_proxy_rate": _rate_text(density_residual),
        "feature_relation_ownership_gap_rate": _rate_text(relation_ownership_gap),
        "feature_relation_echo_pressure_rate": _rate_text(relation_echo),
        "feature_relation_return_divergence_rate": _rate_text(relation_return_divergence),
        "feature_return_integrity_gap_rate": _rate_text(return_integrity_gap),
        "feature_return_strength_mismatch_rate": _rate_text(return_strength_mismatch),
        "feature_return_memory_pressure_rate": _rate_text(return_memory_pressure),
        "feature_demotion_trajectory_proxy_rate": _rate_text(demotion_trajectory),
        "feature_zero_hold_ambiguity_proxy_rate": _rate_text(zero_hold_ambiguity),
        "feature_gate_imbalance_rate": _rate_text(gate_imbalance),
        "feature_pressure_kind_contrast_rate": _rate_text(pressure_kind_contrast),
    }


def with_engineered_shadow_features(row: Mapping[str, object]) -> dict[str, object]:
    out: dict[str, object] = dict(row)
    out.update(engineered_shadow_feature_values(row))
    out["feature_design_boundary"] = ENGINEERED_FEATURE_BOUNDARY
    return out
