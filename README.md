# ZeroGateSim

**Current:** `v1.0.1-alpha` public-repo hygiene / release-prep pack  
**Status:** local-first speculative research software / toy-field proof-of-concept  
**Working identity:** zero-gate dimensional emergence simulator  
**Core question:** can a final trinary witness distinguish earned-one from raw expression, latent overcrown, and false-one pressure under adversarial toy-field weather?

ZeroGateSim is a small research software project for testing a speculative theory of dimensional emergence.

The theory begins with a refusal of the usual dead-shape ladder:

> point, line, plane, cube, then time.

That ladder may work as a classroom drawing. It does not work as a genesis model. It describes completed structures, not how structure becomes expressible.

ZeroGateSim tests a different spine:

> Time is not merely the fourth room in the house of space. Time is the generative ordering condition through which dimensions become expressed.

A point is not the first dimension. A point is the zero-zone of dimensional potential.

A line is not merely extension. A line is polarity around zero.

A plane is not merely a flat surface. A plane is relation between polarities.

Volume is not a box. Volume is closed relational freedom.

A dimension is not merely an axis. A dimension is stabilized freedom that has passed through zero without losing coherence.



## Public repository posture

ZeroGateSim is now being prepared for a public GitHub repository.

The public repo should contain the **source machine**: code, tests, docs, proof-record tools, release notes, small examples, and the first-research-alpha record.

The public repo should **not** contain the heavy weather: `.venv/`, `runs/`, generated proof matrices, cache folders, local exports, or large ZIP evidence bundles.

The working rule is:

> Small engine. Large weather. Clear witness.

Use the export command before GitHub publication:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m zerogate_sim.export_public_repo --repo . --out exports\zerogate_sim_public_repo_v1_0_1_alpha.zip
```

Then inspect the export ZIP before creating or pushing a public repository.

## Paper lineage

Do not overwrite the original theory draft.

The repo reserves two paper lanes:

- `docs/papers/history/` — the original pre-simulation paper, preserved as historical trace.
- `docs/papers/zenodo_ready/` — the later simulation-supported manuscript prepared after repo publication.

This keeps the lineage honest: original seeing, executable simulation, proof record, upgraded paper.

## What v1.0-alpha means

v1.0-alpha means the first proof-shaped software instrument stood up inside generated toy fields.

It does **not** mean cosmology is proven.

It means the current simulation grammar passed an original and fresh-seed trinary adversarial proof harness:

- `1458` scenario cells;
- `13122` seeded simulation runs;
- `22131` final earned-one events;
- `2388` raw false-one pressures detected and demoted;
- `0` final false-one crowns.

The supported claim is narrow:

> ZeroGateSim's final trinary witness separated earned-one from raw expression, latent overcrown, and false-one pressure across original and fresh-seed trinary adversarial proof records.

The unsupported claim is everything larger:

> This does not prove physical dimensions, cosmology, or that reality itself is trinary.

The machine did not prove the universe. It did something narrower and real: it met false one, named it, and refused the crown.

## Core theory

The central hypothesis is:

> Dimensionality emerges when candidate freedoms pass through the zero-gate cycle of distinction, polarity, relation, and return under trinary temporal ordering.

The four gates are:

- **Distinction** — something becomes separable from background.
- **Polarity** — the distinction gains meaningful positive and negative expression around zero.
- **Relation** — polarity becomes bound into stable relation rather than split or drift.
- **Return** — the expressed structure folds back toward zero while preserving coherence.

The return gate is not decorative. Return is prompted by the first three gates. Distinction separates. Polarity tensions. Relation binds. When binding becomes coherent, expansion curves back as return.

The zero-gate coherence of candidate freedom `i` at time `t` is:

```math
C_Z^i(t)=\min(g_D^i(t),g_P^i(t),g_R^i(t),g_B^i(t))
```

The minimum matters. A candidate does not pass because one gate is beautiful. The weakest gate decides the coherence pressure.

The old raw expression count is now treated as pressure, not truth:

```math
d_Z(t)=\sum_i H(\sigma_i(t)-\epsilon)H(C_Z^i(t)-\theta_Z)
```

Raw local expression is not final +1. Final +1 belongs only to **earned-one**.

## Trinary witness stack

ZeroGateSim now distinguishes:

**Expand / +1:** earned-one, final expression.

**Witness / 0:** structured zero-state, including fertile hold, witness hold, quarantine hold, latent overcrown, and relation debt.

**Resist / −1:** rejection, false-one demotion, trap containment.

The core sentence:

> A real one is not the first thing after zero. A real one is what zero can return as without lying.

## Proof harness

The proof harness pressures three dependency wounds:

**Distinction adversary:** visibility and contrast pretending to be reality.

**Polarity adversary:** pulse and zero-crossing pretending to be return.

**Relation adversary:** borrowed coherence pretending to be earned one.

Run shape for the v1 proof record:

- `3` adversarial corpora;
- `243` weather cells per corpus;
- `9` seeds per proof record;
- `729` scenario cells per proof record;
- `6561` seeded runs per proof record;
- original seeds `0-8` and reproduction seeds `9-17`.

## Main commands

Install/update locally:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m pip install -e ".[dev]"
& $P -m pytest
```

Run the proof harness:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 0 --count 9 --out runs\proof_wide243_0_8_v033
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_0_8_v033
```

Run the fresh-seed reproduction:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 9 --count 9 --out runs\proof_wide243_9_17_repro
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_9_17_repro
```

Freeze the v1.0-alpha combined record:

```powershell
& $P -m zerogate_sim.release_record --proof-dir runs\proof_wide243_0_8_v033 --proof-dir runs\proof_wide243_9_17_repro --out runs\first_research_alpha_v1_0_alpha
```

Read first:

- `runs\first_research_alpha_v1_0_alpha\first_research_alpha_record.md`
- `docs\v1_0_alpha_first_research_alpha.md`
- `docs\release_notes\v1_0_alpha.md`
- `ROADMAP.md`

## Repository rule

Generated runs are evidence, not source. Keep them local or bundled for review. Do not store heavy proof weather in the repo by default.

Small engine. Large weather. Clear witness.

## DREED-style discipline

Evidence is what the simulation produced.

Logic is what follows from the model.

Inference is what may be suggested.

Metaphor is how we explain it.

Speculation is what remains unproven.

The primate may dance. It may not notarize the universe.
