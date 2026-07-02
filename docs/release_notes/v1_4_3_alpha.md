# ZeroGateSim v1.4.3-alpha — Unique Handoff Include Path Repair

## Purpose

Repair the second handoff truth wound found during adversary-triad27 result review.

`v1.4.2-alpha` made missing includes fail loudly, but bundled files were still flattened by basename. Three different matrix closeout reports named `matrix_known_logic_closeout_read.md` could collapse into one bundled file.

## Changed

- Handoff includes now preserve source-relative paths under `included/`.
- Include audit records `source_relative_path`.
- Same-named files from different run folders remain distinct in the ZIP.
- Tests verify that distinction / polarity / relation closeout reports with the same basename keep separate contents.

## Claim boundary

This is infrastructure truth repair only.

It does not change the native gate, add a mirror, or make a new simulation claim.

## Witness sentence

A result bundle must not flatten separate evidence files into one shared basename. If three runs produce three reports with the same filename, the handoff must preserve three distinct paths.


## Platform test correction

The corrected update package also fixes two test-truth gremlins found on Windows before commit:

- the same-basename include test writes fixture files as bytes so expected LF content is stable across Windows and Unix line-ending translation;
- the visual witness module forces Matplotlib's non-interactive `Agg` backend so matrix visual tests do not depend on a working Tk/Tcl GUI install.

These are test-environment truth repairs, not native gate changes and not new simulation claims.
