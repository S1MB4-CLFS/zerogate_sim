from __future__ import annotations

from pathlib import Path

from zerogate_sim.comparison_preset import (
    build_powershell_lines,
    build_preset_runs,
    handoff_zip_path,
    report_output_dir,
    preset_names,
    write_comparison_preset,
)


def test_preset_names_include_expected_comparison_presets() -> None:
    names = preset_names()
    assert "quick_smoke" in names
    assert "adversary_triad27" in names
    assert "wide_adversary_probe" in names


def test_adversary_triad27_preset_has_three_dependency_wounds() -> None:
    runs = build_preset_runs("adversary_triad27")
    assert [run.candidate_profile for run in runs] == [
        "adversary_distinction",
        "adversary_polarity",
        "adversary_relation",
    ]
    assert {run.profile for run in runs} == {"triad27"}


def test_preset_overrides_seed_count_and_steps() -> None:
    runs = build_preset_runs("adversary_triad27", start_seed=9, count=2, steps=120)
    assert all(run.start_seed == 9 for run in runs)
    assert all(run.count == 2 for run in runs)
    assert all(run.steps == 120 for run in runs)


def test_powershell_plan_contains_matrix_report_and_handoff_commands() -> None:
    runs = build_preset_runs("quick_smoke")
    text = "\n".join(build_powershell_lines("quick_smoke", runs, base_dir=Path("runs/cross_logic_presets")))
    assert "zerogate_sim.matrix" in text
    assert "zerogate_sim.cross_logic_report" in text
    assert "zerogate_sim.test_handoff" in text
    assert "quick_alpha12" in text


def test_write_comparison_preset_outputs_plan_files(tmp_path) -> None:
    paths = write_comparison_preset(
        preset="quick_smoke",
        output_dir=tmp_path / "plan",
        base_dir=Path("runs/cross_logic_presets"),
    )
    assert paths["comparison_preset_read"].exists()
    assert paths["comparison_preset_manifest"].exists()
    assert paths["comparison_preset_commands"].exists()

    read_text = paths["comparison_preset_read"].read_text(encoding="utf-8")
    commands_text = paths["comparison_preset_commands"].read_text(encoding="utf-8")
    manifest_text = paths["comparison_preset_manifest"].read_text(encoding="utf-8")

    assert "A preset is not proof" in read_text or "not evidence" in read_text
    assert "zerogate_sim.matrix" in commands_text
    assert "cross_logic_report" in commands_text
    assert "quick_alpha12" in manifest_text


def test_powershell_plan_prints_and_checks_truth_files() -> None:
    runs = build_preset_runs("quick_smoke")
    text = "\n".join(build_powershell_lines("quick_smoke", runs, base_dir=Path("runs/cross_logic_presets")))
    assert 'Expected cross-logic report missing' in text
    assert 'Expected assistant handoff ZIP missing' in text
    assert 'Upload this ZIP' in text
    assert 'cross_logic_comparison_read.md' in text
    assert str(handoff_zip_path("quick_smoke")).replace("/", "\\") in text


def test_report_and_handoff_paths_match_generated_preset_truth() -> None:
    base_dir = Path("runs/cross_logic_presets")
    report = report_output_dir(base_dir, "adversary_triad27") / "cross_logic_comparison_read.md"
    handoff = handoff_zip_path("adversary_triad27")
    assert str(report).replace("/", "\\") == "runs\\cross_logic_presets\\adversary_triad27\\cross_logic_report\\cross_logic_comparison_read.md"
    assert str(handoff).endswith("adversary_triad27/assistant_test_handoff.zip") or str(handoff).endswith("adversary_triad27\\assistant_test_handoff.zip")
