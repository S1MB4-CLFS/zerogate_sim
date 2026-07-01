# ZeroGateSim v1.3.1-alpha — Belnap Evidence-State Mirror

## Purpose

Add the second known-logic mirror: Belnap-style evidence-state projection.

This follows the v1.3.0 fuzzy / many-valued mirror. The fuzzy mirror compares continuous score aggregation. The Belnap mirror compares whether final-output evidence is for final +1, against final +1, both, or neither.

## Changed files

- `src/zerogate_sim/belnap_mirror.py`
- `src/zerogate_sim/test_handoff.py`
- `src/zerogate_sim/matrix.py`
- `tests/test_belnap_mirror.py`
- `tests/test_assistant_test_handoff.py`
- `tests/test_matrix.py`
- `docs/belnap_mirror.md`
- `docs/assistant_test_handoff.md`
- `docs/release_notes/v1_3_1_alpha.md`
- version / README / ROADMAP metadata

## New matrix outputs

```text
matrix_belnap_mirror_summary.csv
matrix_belnap_mirror_read.md
```

## New continuation aid

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m zerogate_sim.test_handoff --version v1.3.1-alpha --status passed --note "full test suite passed" --out runs\assistant_test_handoff_v1_3_1_alpha
```

This writes `assistant_test_handoff.zip` for upload into future chats.

## Claim boundary

This version does not claim ZeroGateSim is Belnap-Dunn logic. It adds a projection mirror only.

A Belnap `B` / both state means positive-looking expression pressure and contrary witness coexist. It does not mean final +1 is accepted.

Raw expression remains pressure. Earned-one remains final +1.
