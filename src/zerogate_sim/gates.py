from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from zerogate_sim.signals import SimulationRun, expected_trinary_for_role, normalize_truth_role

ETA = 1e-9


@dataclass(frozen=True)
class GateScores:
    """Gate and prediction summary for one candidate freedom."""

    candidate_id: str
    kind: str
    description: str
    designed_stable: bool
    truth_role: str
    expected_trinary: int
    strength: float
    distinction: float
    polarity: float
    relation: float
    return_observed: float
    return_potential: float
    echo_mimic_score: float
    echo_mimic_band: str
    zero_coherence: float
    zero_depth: int
    expressed: bool
    trinary_value: int
    trinary_outcome: str
    outcome_reason: str
    latent_score: float
    zero_band_value: int
    zero_band: str
    zero_band_symbol: str
    zero_band_reason: str
    limiting_gate: str
    observed_stability_score: float
    observed_stable: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def clamp01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def _zero_crossing_indices(x: np.ndarray) -> np.ndarray:
    signs = np.signbit(x)
    return np.flatnonzero(signs[1:] != signs[:-1]) + 1


def distinction_score(x: np.ndarray, *, noise_floor: float = 0.12) -> float:
    """Score separation from background noise.

    This first-pass metric treats RMS strength above a configured noise floor as
    distinction. Later versions can replace this with rolling/local background
    estimates. For v0.2, it is intentionally simple and inspectable.
    """

    signal_rms = rms(x)
    return clamp01((signal_rms - noise_floor) / (3.0 * noise_floor + ETA))


def polarity_score(x: np.ndarray) -> float:
    """Score meaningful positive/negative expression around zero."""

    pos_area = float(np.sum(np.maximum(x, 0.0)))
    neg_area = float(np.sum(np.maximum(-x, 0.0)))
    area_total = pos_area + neg_area + ETA
    balance = 1.0 - abs(pos_area - neg_area) / area_total

    crossings = len(_zero_crossing_indices(x))
    crossing_score = 1.0 - np.exp(-crossings / 8.0)

    return clamp01(0.68 * balance + 0.32 * crossing_score)


def relation_score(index: int, signals: np.ndarray) -> float:
    """Score stable relation to other candidates using max absolute correlation."""

    if signals.shape[0] <= 1:
        return 0.0

    x = signals[index]
    x_std = float(np.std(x))
    if x_std < ETA:
        return 0.0

    best = 0.0
    for j, y in enumerate(signals):
        if j == index:
            continue
        y_std = float(np.std(y))
        if y_std < ETA:
            continue
        corr = float(np.corrcoef(x, y)[0, 1])
        if np.isfinite(corr):
            best = max(best, abs(corr))

    # Keep weak accidental correlations from looking meaningful.
    return clamp01((best - 0.18) / 0.72)


def _resample(segment: np.ndarray, n: int = 64) -> np.ndarray:
    if len(segment) <= 1:
        return np.zeros(n, dtype=float)
    old = np.linspace(0.0, 1.0, len(segment))
    new = np.linspace(0.0, 1.0, n)
    out = np.interp(new, old, segment)
    std = float(np.std(out))
    if std < ETA:
        return np.zeros(n, dtype=float)
    return (out - float(np.mean(out))) / (std + ETA)


def field_echo_mimic_score(index: int, signals: np.ndarray) -> float:
    """Score whether a candidate may be riding the field instead of earning one.

    This is a diagnostic only. It does not mutate the core gate. A field echo is
    dangerous because it can look relational and coherent while mostly repeating
    a shared driver. The score rises when a candidate is strongly explained by
    the leave-one-out field average and has low independent residual energy.
    """

    if signals.shape[0] <= 1:
        return 0.0
    x = np.asarray(signals[index], dtype=float)
    others = np.delete(signals, index, axis=0)
    field = np.mean(others, axis=0)
    x0 = x - float(np.mean(x))
    f0 = field - float(np.mean(field))
    nx = float(np.linalg.norm(x0))
    nf = float(np.linalg.norm(f0))
    if nx < ETA or nf < ETA:
        return 0.0
    corr = abs(float(np.dot(x0, f0) / (nx * nf + ETA)))
    beta = float(np.dot(x0, f0) / (np.dot(f0, f0) + ETA))
    residual = x0 - beta * f0
    residual_ratio = rms(residual) / (rms(x0) + ETA)
    explained = clamp01(1.0 - residual_ratio)
    return clamp01(corr * explained)


def echo_mimic_band(score: float, *, expressed: bool, truth_role: str) -> str:
    """Human-readable echo diagnostic band.

    Echo is not automatically bad. Stable partners can share field structure.
    It becomes dangerous when a trap/probe is crowned while carrying high echo.
    """

    if score >= 0.55 and expressed and truth_role == "trap":
        return "echo_breach"
    if score >= 0.55:
        return "high_echo_pressure"
    if score >= 0.35:
        return "moderate_echo_pressure"
    return "low_echo_pressure"


def _cycle_memory_score(x: np.ndarray) -> float:
    """Measure whether full return cycles preserve shape.

    This older/full-cycle memory score is still useful for the loose
    signal-health diagnostic. It is not the whole return gate anymore.
    A signal can kiss zero all day and still forget who it is.
    """

    zc = _zero_crossing_indices(x)
    if len(zc) < 5:
        return 0.0

    cycles: list[np.ndarray] = []
    for k in range(0, len(zc) - 2, 2):
        start = int(zc[k])
        end = int(zc[k + 2])
        if end - start >= 8:
            cycles.append(_resample(x[start:end]))

    if len(cycles) < 2:
        return 0.0

    cors: list[float] = []
    for a, b in zip(cycles[:-1], cycles[1:]):
        corr = float(np.corrcoef(a, b)[0, 1])
        if np.isfinite(corr):
            cors.append(max(0.0, corr))

    if not cors:
        return 0.0
    return clamp01(float(np.mean(cors)))


def _half_cycle_memory_score(x: np.ndarray) -> float:
    """Measure repeated return-shape across half-cycles.

    The original return score was too brittle for slow coherent returners because
    it only compared full cycles. This score compares the absolute shape of
    adjacent half-cycles between zero crossings. It lets a slow pulse show memory
    without needing many completed full cycles.
    """

    zc = _zero_crossing_indices(x)
    if len(zc) < 3:
        return 0.0

    half_cycles: list[np.ndarray] = []
    for k in range(len(zc) - 1):
        start = int(zc[k])
        end = int(zc[k + 1])
        if end - start >= 8:
            half_cycles.append(_resample(np.abs(x[start:end])))

    if len(half_cycles) < 2:
        return 0.0

    cors: list[float] = []
    for a, b in zip(half_cycles[:-1], half_cycles[1:]):
        corr = float(np.corrcoef(a, b)[0, 1])
        if np.isfinite(corr):
            cors.append(max(0.0, corr))

    if not cors:
        return 0.0
    return clamp01(float(np.median(cors)))


def _continuity_score(x: np.ndarray) -> float:
    """Penalize discontinuous jumps masquerading as return.

    A memory-reset signal can cross zero and even look cycle-like, but if it
    teleports between phases it is not returning; it is cutting. This score uses
    the largest single-step jump relative to the signal RMS. Smooth returners keep
    this near one. Abrupt reset traps fall toward zero.
    """

    if len(x) < 3:
        return 0.0
    jump_ratio = float(np.max(np.abs(np.diff(x)))) / (rms(x) + ETA)
    # Smooth returners in the alpha field sit below about 0.45. Phase-reset traps
    # and noisy fog often jump above 1.25. Values between are linearly graded.
    return clamp01((1.25 - jump_ratio) / (1.25 - 0.45))


def _persistence_score(x: np.ndarray) -> float:
    """Score survival from early expression to late expression.

    Return is not collapse. If a candidate starts strong and dies after the shared
    perturbation, it should not pass merely because the early part looked alive.
    """

    n = len(x)
    if n < 12:
        return 0.0
    early = rms(x[: n // 3])
    late = rms(x[-n // 3 :])
    if early < ETA and late < ETA:
        return 0.0
    return clamp01(1.0 - abs(late - early) / (early + late + ETA))


def return_score(x: np.ndarray) -> float:
    """Score coherent return: compression + memory + continuity + survival.

    v0.2.3 repair: return is no longer just zero-crossing plus full-cycle memory.
    The gate now requires four pieces:

    1. the signal repeatedly comes near/crosses zero,
    2. adjacent half-cycles preserve shape,
    3. the motion is continuous rather than a phase-reset jump,
    4. expression survives from early to late windows.

    In theory language: return is not merely coming back. It is coming back
    without lying, teleporting, or dying.
    """

    crossings = len(_zero_crossing_indices(x))
    crossing_score = 1.0 - np.exp(-crossings / 7.0)
    memory = _half_cycle_memory_score(x)
    continuity = _continuity_score(x)
    persistence = _persistence_score(x)

    base_return = float(np.sqrt(max(0.0, crossing_score) * max(0.0, memory)))
    return clamp01(base_return * continuity * persistence)


def observed_stability_score(x: np.ndarray) -> float:
    """A provisional stability score independent enough for alpha testing.

    This score is not the zero-gate score. It uses persistence and boundedness plus
    cycle memory. It is still toy-level, but it gives the model something to
    compare against besides its own reflection.
    """

    n = len(x)
    if n < 12:
        return 0.0
    early = rms(x[: n // 3])
    late = rms(x[-n // 3 :])
    if early < ETA and late < ETA:
        persistence = 0.0
    else:
        persistence = 1.0 - abs(late - early) / (early + late + ETA)

    q95 = float(np.quantile(np.abs(x), 0.95))
    q50 = float(np.quantile(np.abs(x), 0.50)) + ETA
    boundedness = clamp01(1.0 - max(0.0, (q95 / q50 - 4.0) / 8.0))
    memory = _cycle_memory_score(x)

    return clamp01(0.40 * persistence + 0.25 * boundedness + 0.35 * memory)


def zero_depth_from_gates(
    *,
    distinction: float,
    polarity: float,
    relation: float,
    return_observed: float,
    threshold: float,
) -> int:
    """Assign zero-depth state Z^(0)..Z^(4).

    Z1: distinction survived return.
    Z2: polarity survived return.
    Z3: relation survived return.
    Z4: the whole four-gate cycle survived return.
    """

    if return_observed < threshold:
        return 0
    depth = 0
    if distinction >= threshold:
        depth = 1
    if depth >= 1 and polarity >= threshold:
        depth = 2
    if depth >= 2 and relation >= threshold:
        depth = 3
    if depth >= 3 and min(distinction, polarity, relation, return_observed) >= threshold:
        depth = 4
    return depth


def limiting_gate_name(scores: dict[str, float]) -> str:
    return min(scores.items(), key=lambda item: item[1])[0]


def trinary_outcome_from_scores(
    *,
    expressed: bool,
    strength: float,
    distinction: float,
    polarity: float,
    relation: float,
    return_observed: float,
    return_potential: float,
    zero_coherence: float,
    zero_depth: int,
    gate_threshold: float,
    strength_threshold: float,
) -> tuple[int, str, str, float]:
    """Classify expression as +1 / 0 / -1 without mutating the gate law.

    +1 expressed: the candidate passed both strength and zero-gate coherence.
    0 held_latent: the candidate did not earn expression, but it carries
       credible zero-structure or return-potential and should be witnessed rather
       than thrown into the rejected bin.
    -1 rejected: the candidate failed the active witness test.

    This is the v0.2.9 repair: the old witness layer was too binary. A held
    candidate is not proof. It is a zero-state: do not count it as one, but do
    not pretend it is dead either.
    """

    if expressed:
        return 1, "expressed", "earned_expression", 1.0

    # Zero-depth hold: the cycle survived all four gates but lacked enough
    # expressed pressure to deserve one. This catches weak-stable whispers and
    # strength-dip stable candidates without calling them failures.
    if zero_depth >= 4 and zero_coherence >= gate_threshold:
        latent_score = clamp01(0.60 * zero_coherence + 0.40 * min(1.0, strength / (strength_threshold + ETA)))
        if strength < strength_threshold:
            return 0, "held_latent", "strength_hold_z4", latent_score
        return 0, "held_latent", "z4_unexpressed_hold", latent_score

    # Return-debt hold: distinction, polarity, and relation predict an attractor,
    # but observed return did not survive the current weather. This is where the
    # deep81 matrix showed that DPR can see latent return-shape before the full
    # return gate permits expression.
    dpr_floor = gate_threshold
    if (
        return_potential >= dpr_floor
        and distinction >= gate_threshold
        and polarity >= gate_threshold
        and relation >= gate_threshold
        and strength >= 0.60 * strength_threshold
    ):
        return_gap = max(0.0, gate_threshold - return_observed)
        latent_score = clamp01(0.55 * return_potential + 0.25 * strength + 0.20 * (1.0 - return_gap / (gate_threshold + ETA)))
        return 0, "held_latent", "return_debt_dpr_hold", latent_score

    # Partial-depth hold: not a full zero-depth, but enough of the cycle survived
    # to deserve a witness hold rather than binary rejection. Keep this strict so
    # noisy single-gate sparks do not get ceremonial robes.
    if zero_depth >= 2 and return_potential >= 0.75 * gate_threshold and strength >= 0.60 * strength_threshold:
        latent_score = clamp01(0.45 * (zero_depth / 4.0) + 0.35 * return_potential + 0.20 * strength)
        return 0, "held_latent", "partial_zero_depth_hold", latent_score

    latent_score = clamp01(0.35 * return_potential + 0.25 * zero_coherence + 0.20 * strength + 0.20 * (zero_depth / 4.0))
    return -1, "rejected", "insufficient_zero_gate_coherence", latent_score


def zero_band_from_scores(
    *,
    trinary_value: int,
    trinary_outcome: str,
    outcome_reason: str,
    strength: float,
    distinction: float,
    polarity: float,
    relation: float,
    return_observed: float,
    return_potential: float,
    zero_coherence: float,
    zero_depth: int,
    gate_threshold: float,
    strength_threshold: float,
) -> tuple[int, str, str, str]:
    """Refine the 0-state into true trinary zero bands.

    v0.2.10 keeps the core expression law unchanged. It only gives the
    witness layer a deeper zero grammar:

    +1 expressed: earned one.
    0+ fertile_hold: not one yet, but close and likely recoverable.
    0  witness_hold: real ambiguity; hold and re-test.
    0- quarantine_hold: interesting pressure, but probably fog/trap/debt.
    -1 rejected: failed active witness.

    This prevents the old flat 0 from becoming a polite trash can. Zero is a
    witness zone, not a broom closet for everything that did not pass.
    """

    if trinary_value == 1:
        return 1, "expressed", "+1", "earned_one"
    if trinary_value == -1:
        return -1, "rejected", "-1", "active_rejection"

    strength_ratio = strength / (strength_threshold + ETA)
    return_ratio = return_observed / (gate_threshold + ETA)
    coherence_ratio = zero_coherence / (gate_threshold + ETA)

    # Fertile hold: the candidate is near expression and the missing piece looks
    # like weather/pressure debt rather than mechanism failure. It is not counted
    # as one, but it deserves priority retest before repair temptation.
    if (
        zero_depth >= 4
        and zero_coherence >= gate_threshold
        and strength_ratio >= 0.85
        and return_ratio >= 0.85
    ):
        return 1, "fertile_hold", "0+", "near_expression_z4"

    if (
        return_potential >= gate_threshold
        and distinction >= gate_threshold
        and polarity >= gate_threshold
        and relation >= gate_threshold
        and strength_ratio >= 0.80
        and return_ratio >= 0.65
    ):
        return 1, "fertile_hold", "0+", "return_debt_near_expression"

    # Quarantine hold: the candidate has enough pressure to avoid clean rejection
    # but its zero-state is unsafe. Do not count, do not trust, do not build on it
    # until the missing mechanism is repaired.
    if strength_ratio < 0.55:
        return -1, "quarantine_hold", "0-", "under_strength_quarantine"

    if return_ratio < 0.65 and return_potential >= gate_threshold:
        return -1, "quarantine_hold", "0-", "return_gap_quarantine"

    if relation < 0.75 * gate_threshold and return_potential < gate_threshold:
        return -1, "quarantine_hold", "0-", "relation_gap_quarantine"

    # Witness hold: the candidate has enough coherent pressure to keep watching,
    # but not enough to call fertile. This is the proper middle zero.
    if zero_depth >= 2 or return_potential >= 0.75 * gate_threshold or coherence_ratio >= 0.75:
        return 0, "witness_hold", "0", "needs_more_return_pressure"

    return -1, "quarantine_hold", "0-", "weak_latent_pressure"


def evaluate_run(
    run: SimulationRun,
    *,
    noise_floor: float = 0.12,
    gate_threshold: float = 0.55,
    strength_threshold: float = 0.30,
) -> list[GateScores]:
    """Evaluate gate scores for all candidate freedoms."""

    raw_strengths = np.array([rms(row) for row in run.signals], dtype=float)
    max_strength = float(np.max(raw_strengths)) if len(raw_strengths) else 1.0
    strength_scores = raw_strengths / (max_strength + ETA)

    results: list[GateScores] = []
    for i, spec in enumerate(run.specs):
        x = run.signals[i]
        distinction = distinction_score(x, noise_floor=noise_floor)
        polarity = polarity_score(x)
        relation = relation_score(i, run.signals)
        observed_return = return_score(x)
        return_potential = clamp01(distinction * polarity * relation)
        truth_role = normalize_truth_role(spec.truth_role, designed_stable=spec.designed_stable)
        expected_trinary = expected_trinary_for_role(truth_role)
        echo_score = field_echo_mimic_score(i, run.signals)
        echo_band = echo_mimic_band(echo_score, expressed=False, truth_role=truth_role)
        gates = {
            "distinction": distinction,
            "polarity": polarity,
            "relation": relation,
            "return": observed_return,
        }
        zero_coherence = min(gates.values())
        strength = clamp01(float(strength_scores[i]))
        expressed = bool(strength >= strength_threshold and zero_coherence >= gate_threshold)
        echo_band = echo_mimic_band(echo_score, expressed=expressed, truth_role=truth_role)
        zero_depth = zero_depth_from_gates(
            distinction=distinction,
            polarity=polarity,
            relation=relation,
            return_observed=observed_return,
            threshold=gate_threshold,
        )
        trinary_value, trinary_outcome, outcome_reason, latent_score = trinary_outcome_from_scores(
            expressed=expressed,
            strength=strength,
            distinction=distinction,
            polarity=polarity,
            relation=relation,
            return_observed=observed_return,
            return_potential=return_potential,
            zero_coherence=zero_coherence,
            zero_depth=zero_depth,
            gate_threshold=gate_threshold,
            strength_threshold=strength_threshold,
        )
        zero_band_value, zero_band, zero_band_symbol, zero_band_reason = zero_band_from_scores(
            trinary_value=trinary_value,
            trinary_outcome=trinary_outcome,
            outcome_reason=outcome_reason,
            strength=strength,
            distinction=distinction,
            polarity=polarity,
            relation=relation,
            return_observed=observed_return,
            return_potential=return_potential,
            zero_coherence=zero_coherence,
            zero_depth=zero_depth,
            gate_threshold=gate_threshold,
            strength_threshold=strength_threshold,
        )
        stability = observed_stability_score(x)
        results.append(
            GateScores(
                candidate_id=spec.candidate_id,
                kind=spec.kind,
                description=spec.description,
                designed_stable=spec.designed_stable,
                truth_role=truth_role,
                expected_trinary=expected_trinary,
                strength=strength,
                distinction=distinction,
                polarity=polarity,
                relation=relation,
                return_observed=observed_return,
                return_potential=return_potential,
                echo_mimic_score=echo_score,
                echo_mimic_band=echo_band,
                zero_coherence=zero_coherence,
                zero_depth=zero_depth,
                expressed=expressed,
                trinary_value=trinary_value,
                trinary_outcome=trinary_outcome,
                outcome_reason=outcome_reason,
                latent_score=latent_score,
                zero_band_value=zero_band_value,
                zero_band=zero_band,
                zero_band_symbol=zero_band_symbol,
                zero_band_reason=zero_band_reason,
                limiting_gate=limiting_gate_name(gates),
                observed_stability_score=stability,
                observed_stable=bool(stability >= gate_threshold),
            )
        )
    return results


def rows_to_dicts(rows: Iterable[GateScores]) -> list[dict[str, object]]:
    return [row.to_dict() for row in rows]
