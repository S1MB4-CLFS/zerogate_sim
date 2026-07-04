# Role-Blind Shadow Design

**Version:** `v1.6.0-alpha`  
**Status:** design-only / report-only / no engine authority  
**Line:** role-blind shadow design after fresh controlled `deep81` and `wide243` evidence

## Purpose

The role-blind shadow is a side-reader that estimates false-one-like pressure from observable behavior without reading designed truth-role labels.

It is called a shadow because it does not decide final output. It follows the current role-aware witness and asks:

> Does this candidate behave like false-one pressure from observable behavior alone?

It does **not** say:

> This candidate is a trap.

That second sentence would smuggle the answer key back into the detector.

## Why now

The fresh controlled evidence block created enough pressure pattern to design from evidence rather than vibes.

- `deep81` produced `2,916` runs, `402` raw false-one pressures, `639` latent overcrown pressures, and `0` final false-one crowns.
- `wide243` produced `8,748` runs, `1,242` raw false-one pressures, `2,043` latent overcrown pressures, and `0` final false-one crowns.
- Relation pressure dominated the false-one wound in both runs.
- Temporal stretch made the `wide243` field harsher.
- Ablation showed that raw-as-final and no-false-one-demotion variants would crown the false pressure.

That pattern is enough to design the shadow. It is not enough to trust the shadow. This is not role-blind discovery.

## Native witness boundary

The native coherence witness remains unchanged:

```math
C_Z^i(t)=\min(D_i(t),P_i(t),R_i(t),B_i(t))
```

Plain boundary: `C_Z = min(D, P, R, B)`.

Current final earned-one still belongs to the existing final witness stack:

```math
\chi^i_{earned}(t)=\chi^i_{raw}(t)H(k_i(t)-K^*)W^i_{lineage}(t)W^i_{independence}(t)W^i_{role}
```

The role-blind shadow must not use `W_role` as an input. It does not replace the current role-aware witness. During evaluation, role-aware labels may be used only after scoring to measure whether the blind score separated pressure better than baseline.

## Allowed observables

The first design allows only observable pressure fields and derived report metrics.

| signal | meaning | role-blind use |
|---|---|---|
| `C_Z` / weakest gate | candidate coherence floor | pressure baseline, not verdict |
| relation wound `G_R` | relation is weaker than surrounding gate support | main expected false-pressure smell |
| return gap `G_B` | return potential is not matched by observed return | mimic / unfinished-return smell |
| latent hold `L` | positive-looking pressure that remains not-yet | hold pressure, not failure |
| lineage weakness `L_w` | weak inherited path | support signal, not role label |
| independence weakness `I_w` | borrowed / echo-like dependence | support signal, not role label |
| zero-depth instability `Z_v` | unstable return-depth behavior | ambiguity / immature expression signal |
| threshold fragility `T_h` | passes loose threshold but fails stricter witness | overfit / threshold smell |
| temporal fragility `T_f` | worsens under temporal stretch | time-axis stress signal |
| ablation crown risk `A` | would crown under witness-layer removal | mechanism-dependence signal |

## Forbidden inputs

A role-blind shadow must not read:

- `trap` labels;
- `expresser` labels;
- `latent/probe` labels;
- `truth_role` fields;
- `role_label` fields;
- `candidate_profile` as a classification shortcut;
- any designed answer key before scoring.

A future implementation may compare its output against these fields after scoring, but only for evaluation.

## Derived design math

Relation wound:

```math
G_R^i(t)=\max(0,\min(D_i(t),P_i(t),B_i(t))-R_i(t))
```

Return gap:

```math
G_B^i(t)=\max(0,\Gamma_i(t)-B_i(t)),\quad \Gamma_i(t)=D_i(t)P_i(t)R_i(t)
```

Threshold fragility:

```math
T_h^i = \mathbb{1}[pass(	heta_{lo})]\,(1-\mathbb{1}[pass(	heta_{hi})])
```

Temporal fragility for profile-level reports:

```math
T_f = severity(	au_+) - severity(	au_-)
```

Ablation crown risk:

```math
A^i = \mathbb{1}[raw\_as\_final\ crowns_i] + \mathbb{1}[no\_false\_one\_demotion\ crowns_i] + \mathbb{1}[no\_latent\_hold\ promotes_i]
```

Initial transparent shadow score:

```math
S_{shadow}=w_R G_R+w_B G_B+w_L L+w_I I+w_T T_f+w_H T_h+w_A A
```

Weights are not claims. The first implementation should start transparent and report-only, then compare against baselines before any tuning is trusted.

## Report-only output

The shadow may produce:

- `shadow_false_one_risk`;
- `shadow_relation_wound_score`;
- `shadow_return_gap_score`;
- `shadow_latent_hold_pressure`;
- `shadow_temporal_fragility`;
- `shadow_threshold_fragility`;
- `shadow_ablation_crown_risk`;
- `shadow_risk_band`: `low`, `watch`, or `high`.

The shadow must not produce:

- final +1;
- final -1;
- final demotion;
- proof of a trap;
- proof of role-blind discovery.

## First falsifier

The role-blind shadow is not earned if it cannot separate known false-pressure-heavy cases from clean earned-one cases better than trivial baselines.

Minimum baselines:

- random ranking;
- raw-strength-only ranking;
- weakest-gate-only ranking;
- relation-gate-only ranking.

Minimum evaluation rule:

> Score first without role labels. Compare to role-aware labels only after scoring.

If the shadow does not beat these baselines on held-out controlled synthetic-field runs, it remains an interesting failure, not a detector.

## First implementation order

1. `v1.6.1-alpha` — role-stripped feature extraction report.
2. `v1.6.2-alpha` — transparent shadow score prototype, report-only.
3. `v1.6.3-alpha` — baseline comparison and falsifier report.
4. `v1.6.4-alpha` — held-out `deep81` / `wide243` role-stripped evaluation.
5. `v1.6.5-alpha` — visual/report closeout only if evidence deserves it.

## Claim boundary

Allowed:

> ZeroGateSim has a design for a role-blind shadow that will estimate false-one-like pressure from observable behavior without using designed truth-role labels.

Forbidden:

> ZeroGateSim has solved role-blind false-one discovery.

Forbidden:

> Role-blind shadow replaces the native witness.

Forbidden:

> Role-blind shadow proves physical time, gravity, mass, cosmology, or trinary reality.

## Operating sentence

The role-aware witness remains the floor. The role-blind shadow is only a side-reader until it earns trust against baselines without reading the answer key.
