# ZeroGateSim

**Current:** `v1.1-alpha` share-ready public witness pack  
**Status:** speculative research software / toy-field proof-of-concept  
**Working identity:** zero-gate dimensional emergence simulator  
**Core question:** can a final trinary witness distinguish earned-one from raw expression, latent overcrown, and false-one pressure under adversarial toy-field weather?

ZeroGateSim is a small research software project for testing a speculative theory of dimensional emergence.

It does **not** prove cosmology, physics, or that reality itself is trinary.

It does test a narrower software-theory claim:

> In generated toy fields, a final trinary witness can separate **earned-one** from raw expression pressure, latent overcrown, and false-one pressure across distinction, polarity, and relation adversaries.

## First-research-alpha proof card

Across the original proof harness and fresh-seed reproduction:

| Measure | Result |
|---|---:|
| Scenario cells | `1458` |
| Seeded toy-field runs | `13122` |
| Final earned-one events | `22131` |
| Raw false-one pressures detected | `2388` |
| Raw false-one pressures demoted | `2388` |
| Final false-one crowns | `0` |

The machine did not prove the universe. It did something narrower and real:

> It met false one, named it, and refused the crown.

## Visual map

Start with the three visual witnesses:

- [Zero-Gate Cycle](docs/assets/zero_gate_cycle.svg)
- [Trinary Witness Stack](docs/assets/trinary_witness_stack.svg)
- [Proof Harness Map](docs/assets/proof_harness_map.svg)

Reader guide: [docs/visual_guide.md](docs/visual_guide.md)

## Core theory

The theory begins by refusing the common dead-shape ladder:

> point, line, plane, cube, then time.

That ladder may work as a classroom drawing. It does not work as a genesis model. It describes completed structures, not how structure becomes expressible.

ZeroGateSim tests a different spine:

> Time is not merely the fourth room in the house of space. Time is the generative ordering condition through which dimensions become expressed.

A point is not the first dimension. A point is the zero-zone of dimensional potential.

A line is not merely extension. A line is polarity around zero.

A plane is not merely a flat surface. A plane is relation between polarities.

Volume is not a box. Volume is closed relational freedom.

A dimension is not merely an axis. A dimension is stabilized freedom that has passed through zero without losing coherence.

## The four-gate operator

The central hypothesis is:

> Dimensionality emerges when candidate freedoms pass through the zero-gate cycle of distinction, polarity, relation, and return under trinary temporal ordering.

The four gates are:

- **Distinction** — something becomes separable from background.
- **Polarity** — the distinction gains meaningful positive and negative expression around zero.
- **Relation** — polarity becomes bound into stable relation rather than split or drift.
- **Return** — the expressed structure folds back toward zero while preserving coherence.

The zero-gate coherence of candidate freedom `i` at time `t` is:

```math
C_Z^i(t)=\min(g_D^i(t),g_P^i(t),g_R^i(t),g_B^i(t))
```

The minimum matters. A candidate does not pass because one gate is beautiful. The weakest gate decides the coherence pressure.

The old raw expression count is now treated as pressure, not final truth:

```math
d_Z(t)=\sum_i H(\sigma_i(t)-\epsilon)H(C_Z^i(t)-\theta_Z)
```

Raw local expression is not final +1. Final +1 belongs only to **earned-one**.

## Trinary witness stack

ZeroGateSim distinguishes:

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

## Quickstart

Install/update locally:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m pip install -e ".[dev]"
& $P -m pytest
```

Small demo:

```powershell
& $P -m zerogate_sim.demo --seed 42 --out runs\demo_seed_42
notepad runs\demo_seed_42\summary.md
```

Small proof smoke test:

```powershell
& $P -m zerogate_sim.proof --profile triad27 --start-seed 0 --count 1 --out runs\proof_smoke
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_smoke
notepad runs\proof_smoke\proof_record.md
```

Full proof harnesses are heavy. Read [docs/quickstart.md](docs/quickstart.md) before running them.

## Reading order

For a fast but honest orientation:

1. [Claim boundary](docs/claim_boundary.md)
2. [Visual guide](docs/visual_guide.md)
3. [Proof card](docs/proof_records/first_research_alpha/proof_card.md)
4. [Reviewer guide](docs/for_reviewers.md)
5. [DREED method note](docs/methods/dreed_active_inference_review_lens_v0.md)
6. [Original historical manuscript](docs/papers/history/zero_gate_dimensional_genesis_original_pre_simulation/)

## Paper lineage

Do not overwrite the original theory draft.

The repo reserves two paper lanes:

- `docs/papers/history/` — the original pre-simulation paper, preserved as historical trace.
- `docs/papers/zenodo_ready/` — the later simulation-supported manuscript prepared after repo publication.

This keeps the lineage honest:

> original seeing -> executable simulation -> proof record -> upgraded paper.

## Repository rule

Generated runs are evidence, not source. Keep them local or bundled for review. Do not store heavy proof weather in the repo by default.

> Small engine. Large weather. Clear witness.

## DREED-style discipline

Evidence is what the simulation produced.

Logic is what follows from the model.

Inference is what may be suggested.

Metaphor is how we explain it.

Speculation is what remains unproven.

DREED is not the judge. It is the pressure lantern.

The primate may dance. It may not notarize the universe.
