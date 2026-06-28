# Final Visual Witness Branch Cleanup

Branch: `visual-witness-polish`

## Purpose

This branch closes the public-facing visual/readme polish work before merging into `main`.

It keeps the useful visual witness layer and removes premature paper scaffolding.

## Kept

- Accepted public visuals.
- Reader path.
- Visual guide.
- Claim boundary.
- Reviewer guide.
- Quickstart.
- Historical original manuscript lane.
- DREED method note.

## Removed / held

- `paper_argument_map.svg`
- paper scaffold folders under `docs/papers/zenodo_ready/`
- paper-specific branch notes
- future Zenodo paper placeholders

## Reason

The repo is the machine, proof witness, and public entry point.

The paper will be built later in a deliberate paper-mode workflow. Keeping half-formed paper scaffolds in the repo now creates future cleanup debt.

## Merge condition

Merge this branch only if:

- tests pass;
- README reads cleanly as public entry;
- accepted visuals open and make sense;
- no paper-scaffold references remain;
- no generated runs, exports, caches, or large proof bundles are staged.

## Tag condition

After merge, tag only if the merged result is a meaningful public witness upgrade.

Recommended tag:

`v1.1-alpha`

Do not tag tiny cleanup commits. Tag the coherent merged public witness state.
