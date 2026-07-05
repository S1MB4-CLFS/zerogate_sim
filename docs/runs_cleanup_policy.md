# ZeroGateSim Runs Cleanup Policy

**Version:** `v1.6.10-alpha`  
**Status:** local hygiene protocol  
**Boundary:** classification only; no delete by default

## Why this exists

The `runs/` directory now holds several kinds of evidence at once:

```text
historical proof roots
controlled evidence reports
shadow evidence outputs
assistant handoff ZIP folders
temporary report experiments
```

That is useful during active research, but it becomes noisy. A noisy evidence folder makes it harder to know what matters and easier to delete the wrong thing.

## Core rule

```text
Do not delete by vibes.
```

The first move is inventory and classification, not cleanup by hand.

## What belongs in Git

Usually nothing under `runs/` belongs in Git.

`runs/` is local evidence and continuity memory. It may contain generated reports and handoff ZIPs for future assistants, but those are not repo truth unless a future version explicitly moves a report into tracked docs.

## Protected history examples

Usually keep or archive carefully:

```text
proof_wide243_0_8_v033
proof_wide243_9_17_repro
first_research_alpha_v1_0_alpha
controlled_deep81_four_gate_v1_5_4
controlled_wide243_four_gate_v1_5_4
four_gate_reconciliation_v1_6_4
shadow_triad27_harder_v1_6_8
shadow_discrimination_v1_6_9_triad27
shadow_lane_discrimination_v1_6_10_triad27
```

Assistant handoff folders are continuity shells. They can often be archived or deleted after the version is committed, tagged, CI-green, and no longer needed by the current chat.

## Inventory command

```powershell
$P = ".\.venv\Scripts\python.exe"

& $P -m zerogate_sim.runs_inventory_report `
  --runs-dir runs `
  --out runs\runs_inventory_v1_6_10
```

The report writes:

```text
runs_inventory.csv
runs_cleanup_plan.md
runs_inventory_audit.json
runs_inventory_bundle.zip
```

It does not delete anything.

## Classification states

```text
keep_history
archive_or_delete_after_confirmation
review_then_archive
witness_review_before_action
```

The classification is a starting point for human review, not an automated broom.
