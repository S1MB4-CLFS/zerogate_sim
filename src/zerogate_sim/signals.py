from __future__ import annotations

from dataclasses import dataclass, replace
import numpy as np

# The candidate kind is intentionally open. New toy witnesses are allowed
# without turning the type layer into a primate checklist of approved labels.
CandidateKind = str


@dataclass(frozen=True)
class CandidateSpec:
    """Design-time description of one candidate freedom."""

    candidate_id: str
    kind: CandidateKind
    amplitude: float
    frequency: float
    phase: float
    noise: float
    drift: float = 0.0
    bias: float = 0.0
    coupling_group: int | None = None
    relation_weight: float = 0.0
    designed_stable: bool = False
    truth_role: str = ""
    description: str = ""


@dataclass(frozen=True)
class SimulationRun:
    """Generated pressure field."""

    t: np.ndarray
    signals: np.ndarray
    specs: list[CandidateSpec]
    seed: int
    metadata: dict[str, object]

TRUTH_ROLE_EXPRESSER = "expresser"
TRUTH_ROLE_LATENT = "latent"
TRUTH_ROLE_TRAP = "trap"
TRUTH_ROLES = {TRUTH_ROLE_EXPRESSER, TRUTH_ROLE_LATENT, TRUTH_ROLE_TRAP}
CANDIDATE_PROFILES = (
    "alpha12",
    "triad27",
    "adversary_distinction",
    "adversary_polarity",
    "adversary_relation",
)


def normalize_truth_role(role: str, *, designed_stable: bool = False) -> str:
    """Return a safe candidate truth role.

    Truth roles are design-time expectations, not proof. They repair the old
    binary stable/trap label into a trinary candidate grammar:
    expresser / latent / trap.
    """

    role = (role or "").strip().lower()
    if role in TRUTH_ROLES:
        return role
    return TRUTH_ROLE_EXPRESSER if designed_stable else TRUTH_ROLE_TRAP


def expected_trinary_for_role(role: str) -> int:
    role = normalize_truth_role(role)
    if role == TRUTH_ROLE_EXPRESSER:
        return 1
    if role == TRUTH_ROLE_LATENT:
        return 0
    return -1


ALPHA12_TRUTH_ROLES = {
    "F00": TRUTH_ROLE_EXPRESSER,
    "F01": TRUTH_ROLE_EXPRESSER,
    "F02": TRUTH_ROLE_TRAP,
    "F03": TRUTH_ROLE_TRAP,
    "F04": TRUTH_ROLE_TRAP,
    "F05": TRUTH_ROLE_TRAP,
    "F06": TRUTH_ROLE_TRAP,
    "F07": TRUTH_ROLE_TRAP,
    "F08": TRUTH_ROLE_EXPRESSER,
    "F09": TRUTH_ROLE_TRAP,
    "F10": TRUTH_ROLE_LATENT,
    "F11": TRUTH_ROLE_LATENT,
}

TRIAD27_EXTRA_TRUTH_ROLES = {
    "F12": TRUTH_ROLE_EXPRESSER,
    "F13": TRUTH_ROLE_LATENT,
    "F14": TRUTH_ROLE_LATENT,
    "F15": TRUTH_ROLE_LATENT,
    "F16": TRUTH_ROLE_LATENT,
    "F17": TRUTH_ROLE_TRAP,
    "F18": TRUTH_ROLE_TRAP,
    "F19": TRUTH_ROLE_TRAP,
    "F20": TRUTH_ROLE_TRAP,
    "F21": TRUTH_ROLE_TRAP,
    "F22": TRUTH_ROLE_LATENT,
    "F23": TRUTH_ROLE_LATENT,
    "F24": TRUTH_ROLE_LATENT,
    "F25": TRUTH_ROLE_TRAP,
    "F26": TRUTH_ROLE_TRAP,
}


def _apply_truth_roles(specs: list[CandidateSpec], role_map: dict[str, str]) -> list[CandidateSpec]:
    """Attach trinary truth roles while preserving backwards compatibility.

    `designed_stable` remains available for older reports, but is now derived
    from the +1 expresser role. Latent/probe candidates are not failures when
    held; traps are breaches only if crowned as expression.
    """

    out: list[CandidateSpec] = []
    for spec in specs:
        role = normalize_truth_role(role_map.get(spec.candidate_id, spec.truth_role), designed_stable=spec.designed_stable)
        out.append(replace(spec, truth_role=role, designed_stable=(role == TRUTH_ROLE_EXPRESSER)))
    return out


def default_candidate_specs() -> list[CandidateSpec]:
    """Return a deliberate mix of stable, unstable, and deceptive candidates.

    These are not truth claims about physics. They are traps and witnesses for the
    first toy model. If every candidate were friendly, the model would win by
    flattery. That is not a simulation; that is a mirror with a marketing budget.
    """

    specs = [
        CandidateSpec(
            "F00",
            "stable_core",
            amplitude=1.00,
            frequency=1.00,
            phase=0.00,
            noise=0.05,
            coupling_group=0,
            relation_weight=0.35,
            designed_stable=True,
            description="balanced, coupled, phase-stable returner",
        ),
        CandidateSpec(
            "F01",
            "stable_partner",
            amplitude=0.92,
            frequency=1.00,
            phase=0.30,
            noise=0.06,
            coupling_group=0,
            relation_weight=0.42,
            designed_stable=True,
            description="partner freedom with stable relation to F00",
        ),
        CandidateSpec(
            "F02",
            "high_amp_no_return",
            amplitude=1.50,
            frequency=0.70,
            phase=0.20,
            noise=0.04,
            bias=1.15,
            designed_stable=False,
            description="loud but biased away from zero; expansion without return",
        ),
        CandidateSpec(
            "F03",
            "polarity_isolated",
            amplitude=0.95,
            frequency=1.73,
            phase=1.20,
            noise=0.05,
            designed_stable=False,
            description="good polarity, poor relation; a free peacock",
        ),
        CandidateSpec(
            "F04",
            "relation_fog",
            amplitude=0.20,
            frequency=1.00,
            phase=0.10,
            noise=0.26,
            coupling_group=0,
            relation_weight=0.90,
            designed_stable=False,
            description="looks relational but weakly distinguished from noise",
        ),
        CandidateSpec(
            "F05",
            "memory_reset",
            amplitude=0.95,
            frequency=1.05,
            phase=0.00,
            noise=0.05,
            designed_stable=False,
            description="crosses zero often but loses cycle memory",
        ),
        CandidateSpec(
            "F06",
            "no_polarity_drift",
            amplitude=0.80,
            frequency=0.85,
            phase=0.40,
            noise=0.05,
            drift=0.018,
            bias=0.55,
            coupling_group=1,
            relation_weight=0.30,
            designed_stable=False,
            description="relation and amplitude, but poor polarity around zero",
        ),
        CandidateSpec(
            "F07",
            "collapse_after_shock",
            amplitude=1.10,
            frequency=0.95,
            phase=2.00,
            noise=0.08,
            coupling_group=1,
            relation_weight=0.35,
            designed_stable=False,
            description="starts strong, then collapses after perturbation",
        ),
        CandidateSpec(
            "F08",
            "returner_deep",
            amplitude=0.85,
            frequency=0.64,
            phase=0.80,
            noise=0.04,
            coupling_group=1,
            relation_weight=0.55,
            designed_stable=True,
            description="slower pulse with coherent return and relation",
        ),
        CandidateSpec(
            "F09",
            "relation_only_offset",
            amplitude=0.55,
            frequency=1.00,
            phase=0.15,
            noise=0.05,
            bias=0.85,
            coupling_group=0,
            relation_weight=0.85,
            designed_stable=False,
            description="relation-looking but offset from zero",
        ),
        CandidateSpec(
            "F10",
            "weak_stable",
            amplitude=0.36,
            frequency=1.00,
            phase=-0.10,
            noise=0.035,
            coupling_group=0,
            relation_weight=0.35,
            designed_stable=False,
            description="coherent but weak; should not count yet",
        ),
        CandidateSpec(
            "F11",
            "ambiguous",
            amplitude=0.70,
            frequency=1.27,
            phase=2.60,
            noise=0.12,
            coupling_group=1,
            relation_weight=0.12,
            designed_stable=False,
            description="mixed signal; useful for failure pressure",
        ),
    ]
    return _apply_truth_roles(specs, ALPHA12_TRUTH_ROLES)


def triad27_candidate_specs() -> list[CandidateSpec]:
    """Return the 27-candidate witness corpus.

    The original alpha corpus stays as the default twelve candidates. This wider
    corpus adds fifteen more witnesses/traps so the field has more than one way
    to be stable, held, foggy, loud, weak, or temporally indebted. It is not a
    replacement for the alpha spine; it is a wider weather test.
    """

    specs = default_candidate_specs() + [
        CandidateSpec(
            "F12",
            "late_maturer",
            amplitude=0.82,
            frequency=0.92,
            phase=0.55,
            noise=0.055,
            coupling_group=0,
            relation_weight=0.38,
            designed_stable=True,
            description="starts modest, matures into expression after temporal witness",
        ),
        CandidateSpec(
            "F13",
            "quiet_returner",
            amplitude=0.74,
            frequency=0.78,
            phase=1.05,
            noise=0.035,
            coupling_group=1,
            relation_weight=0.46,
            designed_stable=True,
            description="quiet coherent returner; tests fertile hold versus earned one",
        ),
        CandidateSpec(
            "F14",
            "anti_phase_partner",
            amplitude=0.86,
            frequency=1.00,
            phase=3.14,
            noise=0.052,
            coupling_group=0,
            relation_weight=0.40,
            designed_stable=True,
            description="stable anti-phase partner; relation should survive sign reversal",
        ),
        CandidateSpec(
            "F15",
            "noisy_returner",
            amplitude=0.90,
            frequency=1.12,
            phase=0.95,
            noise=0.18,
            coupling_group=1,
            relation_weight=0.32,
            designed_stable=False,
            description="return-like but noisy; should often hold or quarantine, not crown",
        ),
        CandidateSpec(
            "F16",
            "deep_bridge",
            amplitude=0.84,
            frequency=0.82,
            phase=1.45,
            noise=0.045,
            coupling_group=1,
            relation_weight=0.62,
            designed_stable=True,
            description="deep relational bridge with coherent return pressure",
        ),
        CandidateSpec(
            "F17",
            "one_sided_bloom",
            amplitude=1.05,
            frequency=0.88,
            phase=0.20,
            noise=0.045,
            bias=0.62,
            designed_stable=False,
            description="strong but one-sided; expansion without honest polarity",
        ),
        CandidateSpec(
            "F18",
            "relation_parasite",
            amplitude=0.64,
            frequency=1.00,
            phase=0.10,
            noise=0.055,
            bias=0.70,
            coupling_group=0,
            relation_weight=0.92,
            designed_stable=False,
            description="borrows relation while staying offset from zero",
        ),
        CandidateSpec(
            "F19",
            "late_collapse",
            amplitude=0.98,
            frequency=0.93,
            phase=2.30,
            noise=0.07,
            coupling_group=1,
            relation_weight=0.36,
            designed_stable=False,
            description="begins plausible, then loses temporal name",
        ),
        CandidateSpec(
            "F20",
            "phase_drift",
            amplitude=0.88,
            frequency=0.96,
            phase=0.75,
            noise=0.055,
            coupling_group=0,
            relation_weight=0.30,
            drift=0.012,
            designed_stable=False,
            description="phase drifts; tests return continuity over time",
        ),
        CandidateSpec(
            "F21",
            "zero_chatter",
            amplitude=0.42,
            frequency=3.20,
            phase=0.00,
            noise=0.16,
            designed_stable=False,
            description="many zero crossings without trustworthy memory",
        ),
        CandidateSpec(
            "F22",
            "slow_core",
            amplitude=0.88,
            frequency=0.48,
            phase=0.35,
            noise=0.035,
            coupling_group=1,
            relation_weight=0.58,
            designed_stable=True,
            description="slow coherent core; tests long return under temporal depth",
        ),
        CandidateSpec(
            "F23",
            "weak_relation_seed",
            amplitude=0.52,
            frequency=1.02,
            phase=-0.30,
            noise=0.045,
            coupling_group=0,
            relation_weight=0.22,
            designed_stable=False,
            description="near-structure but relation is underdeveloped",
        ),
        CandidateSpec(
            "F24",
            "delayed_return_debt",
            amplitude=0.76,
            frequency=0.74,
            phase=1.80,
            noise=0.045,
            bias=0.30,
            coupling_group=1,
            relation_weight=0.48,
            designed_stable=False,
            description="return-potential appears before observed return pays its debt",
        ),
        CandidateSpec(
            "F25",
            "harmonic_alias",
            amplitude=0.84,
            frequency=1.18,
            phase=0.40,
            noise=0.050,
            designed_stable=False,
            description="harmonic aliasing can look patterned without stable relation",
        ),
        CandidateSpec(
            "F26",
            "field_echo",
            amplitude=0.58,
            frequency=1.00,
            phase=0.25,
            noise=0.060,
            coupling_group=0,
            relation_weight=0.70,
            designed_stable=False,
            description="echoes the field but should not be mistaken for an independent one",
        ),
    ]
    role_map = dict(ALPHA12_TRUTH_ROLES)
    role_map.update(TRIAD27_EXTRA_TRUTH_ROLES)
    return _apply_truth_roles(specs, role_map)



PROOF_CORE_ROLES = {
    "F00": TRUTH_ROLE_EXPRESSER,
    "F01": TRUTH_ROLE_EXPRESSER,
    "F02": TRUTH_ROLE_TRAP,
    "F03": TRUTH_ROLE_TRAP,
    "F04": TRUTH_ROLE_TRAP,
    "F05": TRUTH_ROLE_TRAP,
    "F06": TRUTH_ROLE_TRAP,
    "F07": TRUTH_ROLE_TRAP,
    "F08": TRUTH_ROLE_EXPRESSER,
    "F09": TRUTH_ROLE_TRAP,
    "F10": TRUTH_ROLE_LATENT,
    "F11": TRUTH_ROLE_LATENT,
    "F12": TRUTH_ROLE_EXPRESSER,
    "F13": TRUTH_ROLE_LATENT,
    "F14": TRUTH_ROLE_LATENT,
    "F15": TRUTH_ROLE_LATENT,
    "F16": TRUTH_ROLE_LATENT,
    "F17": TRUTH_ROLE_TRAP,
    "F18": TRUTH_ROLE_TRAP,
    "F19": TRUTH_ROLE_TRAP,
    "F20": TRUTH_ROLE_TRAP,
    "F21": TRUTH_ROLE_TRAP,
    "F22": TRUTH_ROLE_LATENT,
    "F23": TRUTH_ROLE_LATENT,
    "F24": TRUTH_ROLE_LATENT,
    "F25": TRUTH_ROLE_TRAP,
    "F26": TRUTH_ROLE_TRAP,
}


def _mutate_spec(spec: CandidateSpec, *, kind: str | None = None, role: str | None = None, **kwargs: object) -> CandidateSpec:
    values = dict(kwargs)
    if kind is not None:
        values["kind"] = kind
    if role is not None:
        values["truth_role"] = role
        values["designed_stable"] = role == TRUTH_ROLE_EXPRESSER
    return replace(spec, **values)


def _proof_base_specs() -> list[CandidateSpec]:
    """Return the shared 27-candidate proof corpus skeleton.

    The proof harness keeps the original stable spine visible while changing the
    trap weather around it. Candidate IDs remain F00..F26 so reports can compare
    adversarial corpora without the witness losing the thread.
    """

    return _apply_truth_roles(triad27_candidate_specs(), PROOF_CORE_ROLES)


def adversary_distinction_candidate_specs() -> list[CandidateSpec]:
    """Corpus targeting the distinction wound.

    These traps try to win by being visible, loud, clean, separated, or high
    contrast. They test whether the final witness confuses signal clarity with
    earned one.
    """

    specs = {spec.candidate_id: spec for spec in _proof_base_specs()}
    updates = {
        "F02": dict(kind="high_amp_no_return", amplitude=1.95, bias=1.45, noise=0.035, relation_weight=0.05, description="distinction adversary: loud offset expansion without return"),
        "F06": dict(kind="no_polarity_drift", amplitude=1.10, bias=0.72, drift=0.024, noise=0.040, relation_weight=0.45, description="distinction adversary: crisp drifting mark with poor zero loyalty"),
        "F09": dict(kind="relation_only_offset", amplitude=0.88, bias=0.95, noise=0.035, relation_weight=0.95, description="distinction adversary: clean relational-looking offset"),
        "F15": dict(kind="one_sided_bloom", amplitude=1.30, bias=0.78, noise=0.040, relation_weight=0.12, description="distinction adversary: strong one-sided bloom"),
        "F17": dict(kind="one_sided_bloom", amplitude=1.45, bias=0.85, noise=0.035, relation_weight=0.08, description="distinction adversary: high-contrast one-sided growth"),
        "F18": dict(kind="high_amp_no_return", amplitude=1.70, bias=1.10, noise=0.035, relation_weight=0.30, description="distinction adversary: high amplitude without honest return"),
        "F20": dict(kind="phase_drift", amplitude=1.05, noise=0.040, drift=0.018, relation_weight=0.16, description="distinction adversary: crisp drifting phase mark"),
        "F21": dict(kind="zero_chatter", amplitude=0.92, noise=0.100, relation_weight=0.03, description="distinction adversary: busy visible chatter"),
        "F25": dict(kind="harmonic_alias", amplitude=1.05, noise=0.035, relation_weight=0.05, description="distinction adversary: clear harmonic alias"),
        "F26": dict(kind="field_echo", amplitude=0.62, noise=0.045, relation_weight=0.38, description="distinction adversary: clear echo pressure, not earned one"),
    }
    out: list[CandidateSpec] = []
    for spec in specs.values():
        patch = updates.get(spec.candidate_id, {})
        out.append(_mutate_spec(spec, **patch) if patch else spec)
    return _apply_truth_roles(out, PROOF_CORE_ROLES)


def adversary_polarity_candidate_specs() -> list[CandidateSpec]:
    """Corpus targeting the polarity wound.

    These traps cross zero, oscillate, mirror, or pulse beautifully without
    earning relation and memory. It protects the theory from crowning rhythm as
    return.
    """

    specs = {spec.candidate_id: spec for spec in _proof_base_specs()}
    updates = {
        "F03": dict(kind="polarity_isolated", amplitude=1.18, frequency=1.90, noise=0.035, relation_weight=0.02, description="polarity adversary: beautiful isolated polarity"),
        "F05": dict(kind="memory_reset", amplitude=1.10, frequency=1.10, noise=0.035, relation_weight=0.02, description="polarity adversary: crosses zero but forgets itself"),
        "F07": dict(kind="collapse_after_shock", amplitude=1.18, frequency=1.04, noise=0.045, relation_weight=0.10, description="polarity adversary: early pulse that loses name"),
        "F14": dict(kind="anti_phase_partner", amplitude=0.92, frequency=1.00, phase=3.14, noise=0.040, relation_weight=0.22, description="polarity adversary/probe: anti-phase needs earned relation"),
        "F19": dict(kind="late_collapse", amplitude=1.08, frequency=0.95, noise=0.040, relation_weight=0.16, description="polarity adversary: plausible pulse with late collapse"),
        "F20": dict(kind="phase_drift", amplitude=1.00, frequency=0.98, noise=0.040, drift=0.018, relation_weight=0.12, description="polarity adversary: drift breaks return continuity"),
        "F21": dict(kind="zero_chatter", amplitude=1.05, frequency=3.40, noise=0.120, relation_weight=0.00, description="polarity adversary: many crossings, little memory"),
        "F24": dict(kind="delayed_return_debt", amplitude=0.92, bias=0.42, noise=0.035, relation_weight=0.28, description="polarity adversary/probe: return debt before stable return"),
        "F25": dict(kind="harmonic_alias", amplitude=1.00, frequency=1.24, noise=0.035, relation_weight=0.02, description="polarity adversary: harmonic alias pretending to be pulse"),
        "F26": dict(kind="memory_reset", amplitude=0.98, frequency=0.88, noise=0.040, relation_weight=0.05, description="polarity adversary: field echo replaced by memory-reset impostor"),
    }
    out: list[CandidateSpec] = []
    for spec in specs.values():
        patch = updates.get(spec.candidate_id, {})
        out.append(_mutate_spec(spec, **patch) if patch else spec)
    return _apply_truth_roles(out, PROOF_CORE_ROLES)


def adversary_relation_candidate_specs() -> list[CandidateSpec]:
    """Corpus targeting the relation wound.

    This is the F26 class: borrowed coherence, parasitic relation, and field
    echo. It tests whether relation is earned or merely ridden like a borrowed
    horse with suspicious paperwork.
    """

    specs = {spec.candidate_id: spec for spec in _proof_base_specs()}
    updates = {
        "F04": dict(kind="relation_fog", amplitude=0.28, noise=0.240, relation_weight=1.05, description="relation adversary: fog with strong coupling"),
        "F09": dict(kind="relation_only_offset", amplitude=0.72, bias=0.88, noise=0.040, relation_weight=1.05, description="relation adversary: relation-looking offset from zero"),
        "F18": dict(kind="relation_parasite", amplitude=0.76, bias=0.72, noise=0.045, relation_weight=1.10, description="relation adversary: parasite riding the field"),
        "F23": dict(kind="weak_relation_seed", amplitude=0.60, noise=0.040, relation_weight=0.35, description="relation adversary/probe: underdeveloped binding"),
        "F24": dict(kind="delayed_return_debt", amplitude=0.82, bias=0.34, noise=0.040, relation_weight=0.70, description="relation adversary/probe: return debt under binding"),
        "F26": dict(kind="field_echo", amplitude=0.62, noise=0.055, relation_weight=0.88, description="relation adversary: field echo attempting false-one crown"),
    }
    out: list[CandidateSpec] = []
    for spec in specs.values():
        patch = updates.get(spec.candidate_id, {})
        out.append(_mutate_spec(spec, **patch) if patch else spec)
    return _apply_truth_roles(out, PROOF_CORE_ROLES)


def candidate_specs(profile: str = "alpha12") -> list[CandidateSpec]:
    """Return a named candidate corpus."""

    if profile == "alpha12":
        return default_candidate_specs()
    if profile == "triad27":
        return triad27_candidate_specs()
    if profile == "adversary_distinction":
        return adversary_distinction_candidate_specs()
    if profile == "adversary_polarity":
        return adversary_polarity_candidate_specs()
    if profile == "adversary_relation":
        return adversary_relation_candidate_specs()
    raise ValueError("candidate profile must be one of: " + ", ".join(CANDIDATE_PROFILES))


def _hidden_drivers(t: np.ndarray) -> dict[int, np.ndarray]:
    return {
        0: np.sin(1.00 * t + 0.05) + 0.18 * np.sin(2.00 * t + 0.30),
        1: np.sin(0.64 * t + 0.80) + 0.16 * np.sin(1.28 * t + 0.10),
    }


def _memory_reset_signal(t: np.ndarray, spec: CandidateSpec, rng: np.random.Generator) -> np.ndarray:
    period = (2.0 * np.pi) / spec.frequency
    cycle_index = np.floor(t / period).astype(int)
    unique_cycles = np.unique(cycle_index)
    cycle_phase = {cycle: rng.uniform(-np.pi, np.pi) for cycle in unique_cycles}
    local_phase = np.array([cycle_phase[c] for c in cycle_index])
    return spec.amplitude * np.sin(spec.frequency * t + local_phase)


def _base_signal(t: np.ndarray, spec: CandidateSpec, rng: np.random.Generator) -> np.ndarray:
    envelope = 1.0 - 0.12 * np.exp(-0.20 * t)
    base = spec.amplitude * envelope * np.sin(spec.frequency * t + spec.phase)
    harmonic = 0.10 * spec.amplitude * np.sin(2.0 * spec.frequency * t + spec.phase / 2.0)
    signal = base + harmonic

    if spec.kind == "high_amp_no_return":
        signal = spec.bias + spec.amplitude * (0.35 + 0.65 * np.sin(spec.frequency * t + spec.phase))
    elif spec.kind == "memory_reset":
        signal = _memory_reset_signal(t, spec, rng)
    elif spec.kind == "collapse_after_shock":
        collapse_center = t[int(0.58 * len(t))]
        collapse = 1.0 / (1.0 + np.exp(5.0 * (t - collapse_center)))
        signal = signal * collapse
    elif spec.kind == "relation_fog":
        signal = 0.35 * signal
    elif spec.kind == "no_polarity_drift":
        signal = spec.bias + signal + spec.drift * t
    elif spec.kind == "relation_only_offset":
        signal = spec.bias + 0.60 * signal
    elif spec.kind == "weak_stable":
        signal = 0.75 * signal
    elif spec.kind == "late_maturer":
        center = t[int(0.46 * len(t))]
        growth = 1.0 / (1.0 + np.exp(-1.15 * (t - center)))
        signal = signal * (0.40 + 0.82 * growth)
    elif spec.kind == "quiet_returner":
        signal = 0.88 * signal
    elif spec.kind == "deep_bridge":
        signal = signal + 0.10 * spec.amplitude * np.sin(0.50 * spec.frequency * t + spec.phase / 3.0)
    elif spec.kind == "one_sided_bloom":
        bloom = 0.55 + 0.45 * (1.0 / (1.0 + np.exp(-0.60 * (t - t[int(0.45 * len(t))]))))
        signal = spec.bias + bloom * np.abs(signal)
    elif spec.kind == "relation_parasite":
        signal = spec.bias + 0.55 * signal
    elif spec.kind == "late_collapse":
        collapse_center = t[int(0.70 * len(t))]
        collapse = 1.0 / (1.0 + np.exp(5.5 * (t - collapse_center)))
        signal = signal * collapse
    elif spec.kind == "phase_drift":
        signal = spec.amplitude * np.sin((spec.frequency + spec.drift * t) * t + spec.phase)
        signal = signal + 0.08 * spec.amplitude * np.sin(2.2 * spec.frequency * t)
    elif spec.kind == "zero_chatter":
        signal = 0.45 * spec.amplitude * np.sin(spec.frequency * t + spec.phase)
        signal = signal + 0.18 * np.sin(7.0 * t + 0.3)
    elif spec.kind == "weak_relation_seed":
        signal = 0.62 * signal
    elif spec.kind == "delayed_return_debt":
        debt = spec.bias * np.exp(-0.08 * t)
        signal = debt + 0.78 * signal
    elif spec.kind == "harmonic_alias":
        signal = spec.amplitude * (0.62 * np.sin(spec.frequency * t + spec.phase) + 0.56 * np.sin(3.03 * spec.frequency * t + 0.2))
    elif spec.kind == "field_echo":
        signal = 0.50 * signal
    elif spec.kind == "ambiguous":
        signal = signal + 0.25 * np.sin(0.31 * t + 0.4)

    return signal


def generate_pressure_field(
    *,
    seed: int = 42,
    n_steps: int = 600,
    dt: float = 0.05,
    specs: list[CandidateSpec] | None = None,
) -> SimulationRun:
    """Generate the first toy pressure field.

    The field is deliberate: some candidates are true-ish, some are traps, and some
    are ambiguous. This lets ZeroGateSim compare zero-gate predictions against
    simpler rules without giving the theory a padded room to win inside.
    """

    rng = np.random.default_rng(seed)
    specs = specs or default_candidate_specs()
    t = np.arange(n_steps, dtype=float) * dt
    drivers = _hidden_drivers(t)

    rows: list[np.ndarray] = []
    for spec in specs:
        signal = _base_signal(t, spec, rng)
        if spec.coupling_group is not None and spec.relation_weight:
            signal = signal + spec.relation_weight * drivers[spec.coupling_group]

        # Shared perturbation: the world kicks the field once. Stable candidates
        # should recover structure; shallow candidates should betray themselves.
        shock_center = t[int(0.66 * len(t))]
        shock = np.exp(-((t - shock_center) ** 2) / (2.0 * 0.18**2))
        if spec.kind in {"stable_core", "stable_partner", "returner_deep", "weak_stable", "late_maturer", "quiet_returner", "anti_phase_partner", "deep_bridge", "slow_core"}:
            signal = signal + 0.12 * shock * np.sin(spec.frequency * t + spec.phase)
        elif spec.kind == "collapse_after_shock":
            signal = signal - 0.50 * shock
        else:
            signal = signal + 0.18 * shock * rng.normal(0.0, 1.0, size=len(t))

        signal = signal + spec.noise * rng.normal(0.0, 1.0, size=len(t))
        rows.append(signal.astype(float))

    signals = np.vstack(rows)
    metadata = {
        "generator": "zerogate_sim.signals.generate_pressure_field",
        "description": "candidate pressure freedoms with traps, perturbation, and relation drivers",
        "n_candidates": len(specs),
        "n_steps": n_steps,
        "dt": dt,
    }
    return SimulationRun(t=t, signals=signals, specs=specs, seed=seed, metadata=metadata)
