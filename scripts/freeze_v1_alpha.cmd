@echo off
REM ============================================================
REM ZeroGateSim v1.0-alpha first research-alpha release record
REM Target local repo folder: C:\dev\zerogate_sim
REM ============================================================
cd /d C:\dev\zerogate_sim
.\.venv\Scripts\python.exe -m zerogate_sim.release_record --proof-dir runs\proof_wide243_0_8_v033 --proof-dir runs\proof_wide243_9_17_repro --out runs\first_research_alpha_v1_0_alpha
notepad runs\first_research_alpha_v1_0_alpha\first_research_alpha_record.md
explorer runs\first_research_alpha_v1_0_alpha
