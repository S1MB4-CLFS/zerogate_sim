from __future__ import annotations

import csv
import zipfile

from zerogate_sim import proof
from zerogate_sim.proof import ADVERSARIAL_CORPORA, run_proof_harness
from zerogate_sim.signals import CANDIDATE_PROFILES, candidate_specs


def test_adversarial_candidate_profiles_exist() -> None:
    assert "adversary_distinction" in CANDIDATE_PROFILES
    assert "adversary_polarity" in CANDIDATE_PROFILES
    assert "adversary_relation" in CANDIDATE_PROFILES
    for _, profile, _ in ADVERSARIAL_CORPORA:
        specs = candidate_specs(profile)
        assert len(specs) == 27
        assert specs[0].candidate_id == "F00"
        assert specs[-1].candidate_id == "F26"
        assert {spec.truth_role for spec in specs} == {"expresser", "latent", "trap"}


def _fake_matrix(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "candidate_id": "F00",
            "kind": "stable_core",
            "truth_role": "expresser",
            "runs": "3",
            "raw_expression_pressure": "3",
            "final_earned_one_count": "3",
            "raw_false_one_pressure": "0",
            "false_one_demoted_count": "0",
            "latent_overcrown_pressure": "0",
            "latent_overcrown_demoted_count": "0",
            "final_trinary_value": "1",
            "final_trinary_symbol": "+1",
            "final_band": "earned_one",
        },
        {
            "candidate_id": "F01",
            "kind": "stable_partner",
            "truth_role": "expresser",
            "runs": "3",
            "raw_expression_pressure": "3",
            "final_earned_one_count": "3",
            "raw_false_one_pressure": "0",
            "false_one_demoted_count": "0",
            "latent_overcrown_pressure": "0",
            "latent_overcrown_demoted_count": "0",
            "final_trinary_value": "1",
            "final_trinary_symbol": "+1",
            "final_band": "earned_one",
        },
        {
            "candidate_id": "F08",
            "kind": "returner_deep",
            "truth_role": "expresser",
            "runs": "3",
            "raw_expression_pressure": "3",
            "final_earned_one_count": "3",
            "raw_false_one_pressure": "0",
            "false_one_demoted_count": "0",
            "latent_overcrown_pressure": "0",
            "latent_overcrown_demoted_count": "0",
            "final_trinary_value": "1",
            "final_trinary_symbol": "+1",
            "final_band": "earned_one",
        },
        {
            "candidate_id": "F26",
            "kind": "field_echo",
            "truth_role": "trap",
            "runs": "3",
            "raw_expression_pressure": "2",
            "final_earned_one_count": "0",
            "raw_false_one_pressure": "2",
            "false_one_demoted_count": "2",
            "latent_overcrown_pressure": "0",
            "latent_overcrown_demoted_count": "0",
            "final_trinary_value": "-1",
            "final_trinary_symbol": "-1",
            "final_band": "false_one_demoted",
        },
    ]
    path = output_dir / "matrix_final_output_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "matrix_final_output_read.md").write_text("# fake final output\n", encoding="utf-8")
    (output_dir / "matrix_theory_confirmation_read.md").write_text("# fake confirmation\n", encoding="utf-8")


def test_proof_harness_smoke(tmp_path, monkeypatch) -> None:
    def fake_run_matrix(**kwargs):
        _fake_matrix(kwargs["output_dir"])
        return {"matrix_final_output_summary": kwargs["output_dir"] / "matrix_final_output_summary.csv"}

    monkeypatch.setattr(proof, "run_matrix", fake_run_matrix)
    paths = run_proof_harness(
        profile="triad27",
        start_seed=0,
        count=1,
        steps=24,
        output_dir=tmp_path / "proof",
        make_plots=False,
    )
    assert paths["proof_harness_read"].exists()
    assert paths["proof_harness_summary"].exists()
    assert paths["proof_bundle"].exists()

    with paths["proof_harness_summary"].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert {row["axis"] for row in rows} == {"distinction", "polarity", "relation"}
    assert {row["status"] for row in rows} == {"pass"}

    text = paths["proof_harness_read"].read_text(encoding="utf-8")
    assert "Trinary Adversarial Proof Harness" in text
    assert "first_research_alpha_candidate" in text

    with zipfile.ZipFile(paths["proof_bundle"]) as zf:
        names = set(zf.namelist())
    assert "proof_harness_read.md" in names
    assert "proof_harness_summary.csv" in names
    assert "distinction/matrix_final_output_read.md" in names
    assert "polarity/matrix_final_output_read.md" in names
    assert "relation/matrix_final_output_read.md" in names
