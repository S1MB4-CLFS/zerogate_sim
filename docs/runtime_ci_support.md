# ZeroGateSim Runtime and CI Support

**Line:** `v1.3.5-alpha`  
**Status:** CI compatibility re-expansion

ZeroGateSim is intended to stay small and portable. The active release/test support target is:

```text
Python 3.10
Python 3.11
Python 3.12
```

## Why this exists

During the v1.3 known-logic mirror line, GitHub Actions reported failures on Python 3.10 and 3.11. The repo temporarily narrowed support to Python 3.12 so the build was honest about what was green.

That was a HOLD state, not a destination.

`v1.3.5-alpha` re-expands support deliberately:

- `pyproject.toml` now declares `requires-python = ">=3.10"`;
- classifiers include Python 3.10, 3.11, and 3.12;
- CI runs the full test suite on 3.10 / 3.11 / 3.12;
- dependencies are bounded enough to avoid drifting into unsupported future major versions.

## Local development

For normal Marek/Simba update blocks, use local-source mode instead of mandatory editable install:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m pytest -q
```

Editable install remains useful for packaging checks and CI, but it is no longer required for every local patch handoff.

## Failure protocol

If one interpreter lane fails:

1. Stop feature work.
2. Read the exact GitHub Actions log for that interpreter.
3. Repair the failing lane.
4. Keep the matrix honest.

Do not hide failures by narrowing support unless the roadmap explicitly marks the narrowed state as HOLD.

## Boundary

CI support is engineering evidence. It does not prove the theory. It only says the software can run its current tests across the declared Python support range.
