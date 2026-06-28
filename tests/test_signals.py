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
