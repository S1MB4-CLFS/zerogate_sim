# Public Release Checklist

ZeroGateSim should become public only after the source tree is clean and the proof boundary is explicit.

## Expand — make it reachable

- README explains what ZeroGateSim is and is not.
- Minimal install/test command works from a clean clone.
- `CITATION.cff` exists and points to `https://github.com/S1MB4-CLFS/zerogate_sim`.
- Public export ZIP is small enough to inspect by eye.
- Proof-record summary is included as documentation, not heavy generated weather.

## Witness — make it traceable

- `docs/proof_records/` contains the first-research-alpha record summaries.
- `docs/papers/history/` contains or points to the original pre-simulation paper.
- `docs/papers/zenodo_ready/` is reserved for the simulation-supported manuscript.
- `docs/evidence_handling.md` explains where heavy proof bundles belong.
- The claim boundary is visible: toy-field proof-of-concept, not cosmology proof.

## Resist — keep the repo clean

- No `.venv/` in Git.
- No `runs/` in Git.
- No generated matrix bundles in Git.
- No cache folders in Git.
- No accidental `READMAP.md` typo file.
- No file over 100 MB.
- MIT License is present in `LICENSE.md`; future paper/evidence records may use separate explicit licenses.

## Final local checks

```powershell
Set-Location C:\dev\zerogate_sim
$P = ".\.venv\Scripts\python.exe"
& $P -m pytest
& $P -m zerogate_sim.export_public_repo --repo . --out exports\zerogate_sim_public_repo_v1_0_2_alpha.zip
```

The primate may open GitHub only after the broom has touched the floor.
