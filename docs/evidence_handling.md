# Evidence Handling

Generated proof weather is evidence, not source.

The public repo should include proof-record summaries and reproducibility commands, but not huge generated `runs/` folders by default.

## Keep in Git

- source code;
- tests;
- docs;
- release notes;
- proof summary records;
- tiny example outputs if needed.

## Keep out of Git

- `runs/`;
- `matrix_bundle.zip`;
- `proof_bundle.zip`;
- `.venv/`;
- cache folders;
- local exports.

## Archive separately

Large proof bundles can be attached to GitHub releases or deposited to Zenodo as a data/evidence record.

## Why

The engine should stay small. The weather can be large. A public repo is a machine, not a basement full of storms.
