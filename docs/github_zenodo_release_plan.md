# GitHub and Zenodo Release Plan

## Stage 1 — Clean public GitHub repository

Create the public repository from the clean source tree, not from the whole working folder.

Include:

- source code;
- tests;
- docs;
- proof-record summaries;
- small examples;
- citation metadata;
- release notes.

Exclude:

- `.venv/`;
- generated `runs/`;
- caches;
- heavy matrix bundles;
- local export ZIPs.

## Stage 2 — GitHub release

After a clean clone installs and tests, create a GitHub release.

Recommended release identity:

`v1.0-alpha` or `v1.0.1-alpha`, depending on whether the public-hygiene changes are included in the first public release tag.

## Stage 3 — Zenodo software DOI

Archive the GitHub release through Zenodo once metadata and license are settled.

The software DOI should cite the source release.

## Stage 4 — Evidence/data archive

Heavy proof bundles may be deposited separately as a Zenodo data/evidence record.

This keeps Git history small while preserving the proof weather.

## Stage 5 — Paper record

Prepare the simulation-supported paper after the code and proof record are citable.

The paper should cite:

- the GitHub/Zenodo software release;
- the evidence/data archive, if deposited;
- the original historical pre-simulation draft, if included or referenced.

## Boundary sentence

ZeroGateSim does not prove cosmology. It provides an executable toy-field proof-of-concept for earned-one witnessing under trinary adversarial pressure.
