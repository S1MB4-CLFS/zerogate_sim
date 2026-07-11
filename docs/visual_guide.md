# Visual Guide

This guide covers the public visual witness layer for ZeroGateSim.

The purpose of the visuals is not decoration. The purpose is orientation:
a reader should understand the mechanism, the final trinary witness,
and the proof harness before reading long reports or source code.

## Accepted visual format

Use simple, high-contrast SVG diagrams with:

- one clear direction of reading;
- explicit labels;
- no hidden paper-trail promises;
- no decorative arrows without logical meaning;
- no text boxes overlapping other text;
- no release claims beyond the proof record.

## Core visuals

### `docs/assets/zero_gate_cycle.svg`

Explains the mechanism:

Zero-zone -> distinction -> polarity -> relation -> return -> zero-gate coherence -> raw expression -> return-depth -> earned-one.

Use this when introducing the theory.

### `docs/assets/trinary_witness_stack.svg`

Explains the intended final output stack. It is not an exact v1.7.11 code
trace: lineage is report-only in the current implementation.

Raw expression is pressure. Earned-one is final +1.
Zero holds latent, overcrown, relation debt, and quarantine states.
Minus rejects false-one pressure.

Use this when explaining the design target, together with the v1.7.11 caveat.

### `docs/assets/proof_harness_map.svg`

Explains the proof harness:

Distinction adversary, polarity adversary, and relation adversary are tested across wide243 weather and fresh seed reproduction.

Use this when explaining what was actually tested.

### `docs/assets/first_research_alpha_proof_card.svg`

Public proof-card visual.

Use this as the compact sharing image when introducing ZeroGateSim to someone who does not need to read the whole repo first.

### `docs/assets/reader_path_map.svg`

Explains the recommended path through the repository.

Use this for reader onboarding.

## Removed visuals

`paper_argument_map.svg` is intentionally removed from this branch.

The paper will be built deliberately later. Until then, the repo should not carry paper-scaffold diagrams that create future cleanup debt.

## Boundary

These visuals support the public repository. They do not prove cosmology, physical dimensions, or trinary reality.

They explain the software-theory proof-of-concept:

ZeroGateSim met false-one pressure, named it, and refused the crown inside generated toy-field simulations.
