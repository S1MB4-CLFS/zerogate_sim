from zerogate_sim.signals import default_candidate_specs, generate_pressure_field


def test_generate_pressure_field_shape() -> None:
    specs = default_candidate_specs()
    run = generate_pressure_field(seed=7, n_steps=120, dt=0.1, specs=specs)
    assert run.signals.shape == (len(specs), 120)
    assert len(run.t) == 120
    assert run.seed == 7


def test_generate_pressure_field_reproducible() -> None:
    a = generate_pressure_field(seed=42, n_steps=80, dt=0.05)
    b = generate_pressure_field(seed=42, n_steps=80, dt=0.05)
    assert (a.signals == b.signals).all()



def test_triad27_candidate_profile_has_27_candidates():
    from zerogate_sim.signals import candidate_specs

    specs = candidate_specs("triad27")
    assert len(specs) == 27
    assert specs[0].candidate_id == "F00"
    assert specs[-1].candidate_id == "F26"



def test_adversary_return_candidate_profile_exists_and_targets_return_gate():
    from zerogate_sim.signals import CANDIDATE_PROFILES, candidate_specs

    assert "adversary_return" in CANDIDATE_PROFILES
    specs = candidate_specs("adversary_return")
    assert len(specs) == 27
    patched = [spec for spec in specs if "return adversary" in spec.description]
    assert len(patched) >= 6
    assert {spec.kind for spec in patched} & {
        "memory_reset",
        "collapse_after_shock",
        "late_collapse",
        "phase_drift",
        "zero_chatter",
        "delayed_return_debt",
    }
