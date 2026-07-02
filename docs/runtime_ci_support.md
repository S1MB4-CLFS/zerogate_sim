# ZeroGateSim Runtime and CI Support

**Line:** `v1.3.6-alpha`  
**Status:** release-gate flow repair

ZeroGateSim is intended to stay small and portable, but the release gate must tell the truth.

## Required release/test runtime

```text
Python 3.12
```

`v1.3.5-alpha` tried to re-expand the required GitHub Actions matrix to Python 3.10 / 3.11 / 3.12. GitHub Actions stayed red on Python 3.10 and 3.11.

`v1.3.6-alpha` repairs the flow:

- required CI gate returns to Python 3.12;
- `pyproject.toml` declares `requires-python = ">=3.12"`;
- Python 3.10 / 3.11 move into a manual, non-blocking compatibility probe workflow;
- feature work is no longer held hostage by unresolved legacy-interpreter drift.

## Compatibility probes

The manual workflow is:

```text
.github/workflows/compatibility.yml
```

It can be run deliberately when the project wants to investigate older interpreters. It uses local-source mode rather than package install, because the package itself is not currently declaring 3.10 / 3.11 release support.

## Local development

For normal Marek/Simba update blocks, use local-source mode:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m pytest -q
```

Editable install remains useful for packaging checks and CI, but it is not required for every local patch handoff.

## Failure protocol

If the required 3.12 gate fails:

1. Stop feature work.
2. Read the exact GitHub Actions log.
3. Repair that gate before advancing.

If a manual 3.10 / 3.11 probe fails:

1. Record the failure as compatibility pressure.
2. Do not call those runtimes supported.
3. Repair deliberately only when older-interpreter support becomes a release goal.

## Boundary

CI support is engineering evidence. It does not prove the theory. It only says the software can run its current tests across the declared release runtime.
