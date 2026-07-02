# Assistant Test Handoff Bundle

**Introduced:** `v1.3.1-alpha`  
**Truth repair:** `v1.4.2-alpha` / `v1.4.3-alpha`

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
- source-relative bundle paths for included files;
- one uploadable ZIP.

## Command

Use local-source mode, not editable install:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.test_handoff --version v1.4.3-alpha --status passed --note "full test suite passed" --include runs\some_report.md --out runs\assistant_test_handoff_v1_4_3_alpha
```

Output:

```text
runs/assistant_test_handoff_v1_4_3_alpha/assistant_test_handoff.md
runs/assistant_test_handoff_v1_4_3_alpha/assistant_test_handoff.json
runs/assistant_test_handoff_v1_4_3_alpha/assistant_test_handoff.zip
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


## Truth rule for same-named reports

As of `v1.4.3-alpha`, included files preserve source-relative paths under `included/`.

This matters because matrix result folders often contain files with the same basename, for example:

```text
runs\cross_logic_presets\adversary_triad27\distinction_triad27\matrix_known_logic_closeout_read.md
runs\cross_logic_presets\adversary_triad27\polarity_triad27\matrix_known_logic_closeout_read.md
runs\cross_logic_presets\adversary_triad27\relation_triad27\matrix_known_logic_closeout_read.md
```

The handoff ZIP must preserve those as three separate evidence files. Flattening all includes to `included/matrix_known_logic_closeout_read.md` is a false witness because later files overwrite earlier ones.

## Boundary

This bundle is a continuation aid, not proof of project truth.

Green tests mean the local gates passed. They do not prove cosmology, physical dimensional genesis, or final theory truth.

Truth sentence:

> A handoff that says tests passed must contain the requested evidence files, preserve same-named files from different run folders separately, or fail loudly.
