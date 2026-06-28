from pathlib import Path
from zipfile import ZipFile

from zerogate_sim.export_public_repo import write_export


def test_public_export_excludes_local_weather(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "zerogate_sim").mkdir(parents=True)
    (repo / "src" / "zerogate_sim" / "__init__.py").write_text("x=1\n", encoding="utf-8")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    (repo / "runs" / "proof").mkdir(parents=True)
    (repo / "runs" / "proof" / "huge.csv").write_text("weather\n", encoding="utf-8")
    (repo / ".venv" / "Scripts").mkdir(parents=True)
    (repo / ".venv" / "Scripts" / "python.exe").write_text("nope\n", encoding="utf-8")
    (repo / "READMAP.md").write_text("typo\n", encoding="utf-8")

    out = tmp_path / "export.zip"
    manifest = write_export(repo=repo, out_path=out)

    assert manifest["included_file_count"] == 2
    assert out.exists()
    with ZipFile(out) as zf:
        names = set(zf.namelist())
    assert "zerogate_sim/README.md" in names
    assert "zerogate_sim/src/zerogate_sim/__init__.py" in names
    assert "zerogate_sim/PUBLIC_EXPORT_MANIFEST.json" in names
    assert all("runs/" not in name for name in names)
    assert all(".venv/" not in name for name in names)
    assert "zerogate_sim/READMAP.md" not in names


def test_public_export_dry_run_writes_no_zip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    out = tmp_path / "export.zip"
    manifest = write_export(repo=repo, out_path=out, dry_run=True)
    assert manifest["dry_run"] is True
    assert not out.exists()
