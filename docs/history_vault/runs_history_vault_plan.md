# Runs History Vault Plan

This is a no-delete plan for Marek's local `C:\dev\zerogate_sim\runs` folder.

## Canonical folders to keep or archive first

Keep/archive these before deleting anything else:

```text
proof_wide243_0_8_v033
proof_wide243_9_17_repro
first_research_alpha_v1_0_alpha
controlled_deep81_four_gate_v1_5_4
controlled_wide243_four_gate_v1_5_4
native_triad27_v1_6_16
native_deepwide_v1_6_17
four_gates_triad27_debt_v1_6_20
four_gates_deepwide_debt_v1_6_21
four_gates_fresh_seed_debt_v1_6_22
four_gates_fresh_seed_reproduction_v1_6_22
assistant_test_handoff_v1_6_22_fresh_seed_reproduction
```

The shadow route folders can be archived as history, but they do not need to remain in the live `runs/` root once their handoff ZIPs and closeout notes are preserved.

## PowerShell archive pattern

Run this only after checking the folder names exist locally:

```powershell
$ErrorActionPreference = "Stop"
Set-Location C:\dev\zerogate_sim

$VaultZip = "C:\dev\zerogate_simuns\zerogate_history_vault_KEEP_$(Get-Date -Format yyyyMMdd_HHmmss).zip"
$KeepFolders = @(
  "runs\proof_wide243_0_8_v033",
  "runs\proof_wide243_9_17_repro",
  "runsirst_research_alpha_v1_0_alpha",
  "runs\controlled_deep81_four_gate_v1_5_4",
  "runs\controlled_wide243_four_gate_v1_5_4",
  "runs
ative_triad27_v1_6_16",
  "runs
ative_deepwide_v1_6_17",
  "runsour_gates_triad27_debt_v1_6_20",
  "runsour_gates_deepwide_debt_v1_6_21",
  "runsour_gates_fresh_seed_debt_v1_6_22",
  "runsour_gates_fresh_seed_reproduction_v1_6_22",
  "runsssistant_test_handoff_v1_6_22_fresh_seed_reproduction"
)

$Existing = $KeepFolders | Where-Object { Test-Path $_ }
if (!$Existing) { throw "No keep folders found. Stop." }
Compress-Archive -Path $Existing -DestinationPath $VaultZip -Force
Write-Host "History vault ZIP created: $VaultZip"
```

## Delete rule

Do not delete by vibes. After this ZIP exists and opens correctly, old assistant handoff folders may be deleted manually if they are superseded and not referenced by the current evidence route.
