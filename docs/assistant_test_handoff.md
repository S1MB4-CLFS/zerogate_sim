# Assistant Test Handoff Bundle

**Introduced:** `v1.3.1-alpha`

This tool writes a small assistant-readable bundle after Marek runs local test gates.

It exists because screenshots and terminal fragments are easy to lose. The bundle records:

- requested version;
- package version;
- local test status supplied by Marek / command block;
- notes;
- git status;
- recent git log;
- optional included result files;
- one uploadable ZIP.

## Command

Use local-source mode, not editable install:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.test_handoff --version v1.3.1-alpha --status passed --note "full test suite passed" --out runs\assistant_test_handoff_v1_3_1_alpha
```

Output:

```text
runs/assistant_test_handoff_v1_3_1_alpha/assistant_test_handoff.md
runs/assistant_test_handoff_v1_3_1_alpha/assistant_test_handoff.json
runs/assistant_test_handoff_v1_3_1_alpha/assistant_test_handoff.zip
```

Upload the ZIP when asking the next assistant to inspect the result.

## Boundary

This bundle is a continuation aid, not proof of project truth.

Green tests mean the local gates passed. They do not prove cosmology, physical dimensional genesis, or final theory truth.
