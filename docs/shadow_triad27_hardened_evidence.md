# ZeroGateSim Shadow Triad27 Hardened Evidence

## Claim boundary

`v1.6.8-alpha` builds the harder triad27 battlefield that the shadow line needed after the first triad27 audit showed a trivial baseline tie.

This is not role-blind discovery, not detector closeout, not a score repair, and not a replacement for the native four-gate witness. It does not retune the transparent shadow score. It makes the evidence surface harder before any score repair is allowed.

The native witness remains:

```text
C_Z = min(D, P, R, B)
```

## Weather rung

```text
triad27 = 3^3 local expression weather
deep81  = 3^4 perturbation / late-shock bridge
wide243 = 3^5 temporal-depth / time-axis stress
```

`v1.6.8-alpha` works only on `triad27`. It turns completed four-gate triad27 matrix runs into cell-level role-stripped family rows, then immediately runs the `v1.6.7-alpha` weather hardening judge on the generated evidence base.

## Why this exists

The earlier triad27 shadow result was not a scientific pass. The score ranked the four gate families correctly, but dumb baselines tied it. A score that is right for the same reason as a trivial baseline has not earned trust.

The repair is not to tune the score. The repair is to harden the battlefield:

- evaluate cell-level weather rows instead of one profile row and four family rows;
- expose exact baseline fields for raw strength, weakest gate, relation gate, and return gate;
- keep gate labels and truth-role labels out of feature inputs;
- keep native gate/scenario identity only in evaluation targets after scoring;
- let the hardening judge say ugly things when the shadow is trivial or under baseline.

## Generated base shape

The report writes a standard evidence base that can be passed to `zerogate-shadow-weather-hardening`:

```text
<out>/
  seed_block/
  role_stripped/
  shadow_score/
  weather_hardening/
  cell_evidence/
  triad27_hardened_evidence_read.md
  triad27_hardened_evidence_audit.json
```

The role-stripped family file has one row per native-gate/weather-cell evidence slice, but the feature row does not expose the native gate label. The target row may contain `evaluation_family_label` because targets are joined only after scores are already written.

## Command shape

```powershell
python -m zerogate_sim.shadow_triad27_hardened_evidence_report `
  --matrix-dir runs\shadow_triad27_harder_v1_6_8\matrix\distinction_triad27 `
  --matrix-dir runs\shadow_triad27_harder_v1_6_8\matrix\polarity_triad27 `
  --matrix-dir runs\shadow_triad27_harder_v1_6_8\matrix\relation_triad27 `
  --matrix-dir runs\shadow_triad27_harder_v1_6_8\matrix\return_triad27 `
  --out runs\shadow_triad27_hardened_evidence_v1_6_8
```

## Interpretation

If the hardening result says `witness_shadow_trivial_under_hardened_weather` or `resist_shadow_under_hardened_weather`, do not advance to deep81 / wide243. The next move would be shadow discrimination repair.

If it says `expand_shadow_nontrivial_hardened_weather_not_detector`, that only earns readiness for deeper weather. It still does not prove role-blind discovery.
