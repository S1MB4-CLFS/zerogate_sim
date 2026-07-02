# ZeroGateSim v1.4.2-alpha — Truth-Safe Handoff and Preset Path Repair

## Purpose

Repair the test-continuation layer so local handoffs tell the truth only.

This release is infrastructure repair. It does not change the native zero-gate engine, add a new known-logic mirror, or alter the theory claim boundary.

## Fixed

- `zerogate_sim.test_handoff` now treats missing requested include files as a hard failure by default.
- `--allow-missing-include` exists only for explicitly optional missing files; such files are recorded in `missing_includes`.
- Handoff Markdown/JSON now include an include audit, missing-include count, and strictness flag.
- Generated comparison preset scripts check the exact cross-logic report path before building the handoff.
- Generated comparison preset scripts print the exact `assistant_test_handoff.zip` path to upload.
- Docs explain that the generated preset script is the path authority.

## Why this matters

A previous manual follow-up command looked for the cross-logic comparison report in the wrong folder. The preset had completed, but the handoff could silently skip the missing include. That made the bundle look greener than it was.

That is now forbidden by default.

## Claim boundary

This release does not prove stronger simulation behavior. It makes the local test evidence harder to misread.

> A handoff that says tests passed must either contain the requested evidence files or fail loudly.
