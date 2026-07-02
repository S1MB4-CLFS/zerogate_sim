# Assistant Test Handoff Bundle

**Introduced:** `v1.3.1-alpha`  
**Truth repair:** `v1.4.2-alpha`

This tool writes a small assistant-readable bundle after Marek runs local test gates.

It exists because screenshots and terminal fragments are easy to lose. The bundle records:

- requested version;
- package version;
- local test status supplied by Marek / command block;
- notes;
- git status;
- recent git log;
- included result files;
- include audit;
- one uploadable ZIP.

## Command

Use local-source mode, not editable install:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.test_handoff --version v1.4.2-alpha --status passed --note "full test suite passed" --include runs\some_report.md --out runs\assistant_test_handoff_v1_4_2_alpha
```

Output:

```text
runs/assistant_test_handoff_v1_4_2_alpha/assistant_test_handoff.md
runs/assistant_test_handoff_v1_4_2_alpha/assistant_test_handoff.json
runs/assistant_test_handoff_v1_4_2_alpha/assistant_test_handoff.zip
```

Upload the ZIP when asking the next assistant to inspect the result.

## Truth rule for includes

As of `v1.4.2-alpha`, requested includes are strict by default.

If a command asks the handoff to include a report file and that file is missing, the command fails. This prevents a bundle from saying `passed` while silently omitting the evidence file the next assistant needs.

Allowed only when explicitly intentional:

```powershell
& $P -m zerogate_sim.test_handoff --allow-missing-include --include runs\optional_missing_file.md
```

That records the missing file in `missing_includes` instead of pretending nothing happened.

## Boundary

This bundle is a continuation aid, not proof of project truth.

Green tests mean the local gates passed. They do not prove cosmology, physical dimensional genesis, or final theory truth.

Truth sentence:

> A handoff that says tests passed must either contain the requested evidence files or fail loudly.
