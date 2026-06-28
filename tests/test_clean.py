from __future__ import annotations

from pathlib import Path

from zerogate_sim.clean import collect_targets, main


def make_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "zerogate_sim"
    (repo / "src" / "zerogate_sim").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='zerogate-sim'\n", encoding="utf-8")
    return repo


def test_collect_targets_includes_runs_only_when_requested(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    (repo / "runs" / "seed_0").mkdir(parents=True)
    (repo / "src" / "zerogate_sim" / "__pycache__").mkdir(parents=True)
    (repo / "src" / "zerogate_sim" / "__pycache__" / "x.pyc").write_bytes(b"x")

    no_runs = collect_targets(repo, remove_runs=False)
    assert repo / "runs" not in [target.path for target in no_runs]
    assert any(target.path.name == "__pycache__" for target in no_runs)

    with_runs = collect_targets(repo, remove_runs=True)
    assert repo / "runs" in [target.path for target in with_runs]


def test_clean_main_requires_yes_unless_dry_run(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    cache = repo / ".pytest_cache"
    cache.mkdir()

    code = main(["--repo", str(repo)])
    assert code == 2
    assert cache.exists()

    code = main(["--repo", str(repo), "--dry-run"])
    assert code == 0
    assert cache.exists()

    code = main(["--repo", str(repo), "--yes"])
    assert code == 0
    assert not cache.exists()
