# ZeroGateSim

**Current public line:** `v1.0.2-alpha` with visual-witness polish in branch work  
**Status:** speculative research software / toy-field proof-of-concept  
**Working identity:** zero-gate dimensional emergence simulator  
**Core question:** can a final trinary witness distinguish earned-one from raw expression, latent overcrown, and false-one pressure under adversarial toy-field weather?

ZeroGateSim is a small research software project for testing a speculative theory of dimensional emergence.

It does **not** prove cosmology, physical dimensions, or that reality itself is trinary.

It does test a narrower software-theory claim:

> Inside generated toy fields, final earned-one witness can separate earned expression from raw expression pressure, latent overcrown, and false-one pressure across distinction, polarity, and relation adversaries.

## Why this exists

The usual ladder of dimensional explanation often begins with:

> point, line, plane, cube, then time.

That ladder may work as a classroom drawing. It does not work as a genesis model. It describes completed structures, not how structure becomes expressible.

ZeroGateSim tests a different spine:

> Time is not merely the fourth room in the house of space. Time is the generative ordering condition through which dimensions become expressed.

In this frame:

- a point is the zero-zone of dimensional potential;
- a line is polarity around zero;
- a plane is relation between polarities;
- volume is closed relational freedom;
- a dimension is stabilized freedom that has passed through zero without losing coherence.

The simulator exists because a theory does not earn trust by sounding beautiful. It earns its first bones by meeting pressure.

## First-research-alpha result

ZeroGateSim passed an original proof harness and a fresh-seed reproduction inside generated toy fields.

Combined record:

- `1458` scenario cells;
- `13122` seeded simulation runs;
- `22131` final earned-one events;
- `2388` raw false-one pressures detected and demoted;
- `0` final false-one crowns.

The machine did not prove the universe.

It did something narrower and real:

> it met false one, named it, and refused the crown.

## Core theory

The central hypothesis is:

> Dimensionality emerges when candidate freedoms pass through the zero-gate cycle of distinction, polarity, relation, and return under trinary temporal ordering.

The four gates are:

- **Distinction** — something becomes separable from background.
- **Polarity** — distinction gains meaningful positive and negative expression around zero.
- **Relation** — polarity becomes bound into stable relation rather than split or drift.
- **Return** — expressed structure folds back toward zero while preserving coherence.

Return is not decorative. Distinction separates. Polarity tensions. Relation binds. When binding becomes coherent, expansion curves back as return.

The zero-gate coherence of candidate freedom `i` at time `t` is:

```math
C_Z^i(t)=\min(g_D^i(t),g_P^i(t),g_R^i(t),g_B^i(t))
```

The minimum matters. A candidate does not pass because one gate is beautiful. The weakest gate decides the coherence pressure.

The old raw expression count is treated as pressure, not truth:

```math
d_Z(t)=\sum_i H(\sigma_i(t)-\epsilon)H(C_Z^i(t)-\theta_Z)
```

Raw local expression is not final +1. Final +1 belongs only to **earned-one**.

Core sentence:

> A real one is not the first thing after zero. A real one is what zero can return as without lying.

## Visual route

Start with the visual maps before reading the full machinery.

### Zero-gate cycle

![Zero-gate cycle](docs/assets/zero_gate_cycle.svg)

### Trinary witness stack

![Trinary witness stack](docs/assets/trinary_witness_stack.svg)

### Proof harness map

![Proof harness map](docs/assets/proof_harness_map.svg)

### First-research-alpha proof card

![First-research-alpha proof card](docs/assets/first_research_alpha_proof_card.svg)

Visual guide:

- [`docs/visual_guide.md`](docs/visual_guide.md)
- [`docs/share_ready_reader_path.md`](docs/share_ready_reader_path.md)

## Proof harness

The proof harness pressures three dependency wounds:

- **Distinction adversary:** visibility and contrast pretending to be reality.
- **Polarity adversary:** pulse and zero-crossing pretending to be return.
- **Relation adversary:** borrowed coherence pretending to be earned one.

Run shape for the v1 proof record:

- `3` adversarial corpora;
- `243` weather cells per corpus;
- `9` seeds per proof record;
- `729` scenario cells per proof record;
- `6561` seeded runs per proof record;
- original seeds `0-8` and reproduction seeds `9-17`.

Read the proof card:

- [`docs/proof_records/first_research_alpha/proof_card.md`](docs/proof_records/first_research_alpha/proof_card.md)

## Quickstart

Install/update locally:

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m pip install -e ".[dev]"
& $P -m pytest
```

Run a small demo first:

```powershell
& $P -m zerogate_sim.demo --seed 42 --out runs\demo_seed_42
```

Run the original proof harness:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 0 --count 9 --out runs\proof_wide243_0_8_v033
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_0_8_v033
```

Run the fresh-seed reproduction:

```powershell
& $P -m zerogate_sim.proof --profile wide243 --start-seed 9 --count 9 --out runs\proof_wide243_9_17_repro
& $P -m zerogate_sim.proof_record --proof-dir runs\proof_wide243_9_17_repro
```

Freeze the combined record:

```powershell
& $P -m zerogate_sim.release_record --proof-dir runs\proof_wide243_0_8_v033 --proof-dir runs\proof_wide243_9_17_repro --out runs\first_research_alpha_v1_0_alpha
```

More detailed quickstart:

- [`docs/quickstart.md`](docs/quickstart.md)

## Claim boundary

Supported claim:

> ZeroGateSim's final trinary witness separated earned-one from raw expression, latent overcrown, and false-one pressure across original and fresh-seed trinary adversarial proof records inside generated toy fields.

Unsupported claims:

- this proves physical dimensions;
- this proves cosmology;
- this proves that reality itself is trinary;
- this replaces physics or mathematics.

Read the full boundary:

- [`docs/claim_boundary.md`](docs/claim_boundary.md)

## Paper lineage

Do not overwrite the original theory draft.

The repo preserves two lanes:

- [`docs/papers/history/`](docs/papers/history/) — original pre-simulation manuscript, preserved as historical trace.
- [`docs/papers/zenodo_ready/`](docs/papers/zenodo_ready/) — later simulation-supported manuscript scaffold.

This keeps the lineage honest:

> original seeing → executable simulation → proof-of-concept record → simulation-supported paper.

## For reviewers and interested readers

Recommended route:

1. README top card.
2. Visual route.
3. Claim boundary.
4. Proof card.
5. Quickstart or code.
6. Historical manuscript only after the current proof boundary is understood.

Reviewer guide:

- [`docs/for_reviewers.md`](docs/for_reviewers.md)

## License and citation

The source repository uses the MIT License.

Citation metadata is stored in [`CITATION.cff`](CITATION.cff). The DOI field is intentionally absent until a Zenodo record exists.

Future manuscript and evidence records may use separate explicit licenses.
