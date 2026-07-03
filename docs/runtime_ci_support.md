# ZeroGateSim Runtime Support

**Current release/test runtime:** Python 3.12  
**Archive note:** detailed runtime history moved here in `v1.5.3-alpha` so README and ROADMAP stay readable.

ZeroGateSim uses Python 3.12 as the required release/test runtime. This is an engineering boundary, not a theory claim.

## Why this note exists

The known-logic mirror line temporarily exposed older-interpreter compatibility pressure. That history is useful for maintainers, but it is not central research language and should not clutter the README or ROADMAP.

## Runtime history

During the v1.3 line, the project tested whether the required runtime support could be widened beyond Python 3.12. The attempt showed that older interpreter lanes were not ready to serve as release gates. The project therefore kept Python 3.12 as the required runtime and moved older-interpreter investigation into manual compatibility pressure rather than blocking the active research line.

## Required release/test runtime

```text
Python 3.12
```

The package metadata declares this boundary. Normal release gates and local handoff checks should treat Python 3.12 as the supported runtime unless a later version deliberately reopens compatibility work.

## Local development

For normal Marek/Simba update blocks, prefer local-source mode:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
& $P -m pytest -q
```

Editable install remains useful for packaging checks, but it is not required for every local patch handoff.

## Failure protocol

If the required Python 3.12 gate fails:

1. Stop feature work.
2. Read the exact failure log.
3. Repair that gate before advancing.

If an older-interpreter probe fails:

1. Record it as compatibility pressure.
2. Do not call that interpreter supported.
3. Repair it only when compatibility becomes an explicit release goal.

## Boundary

Runtime support is engineering evidence. It says whether the software can run its declared tests on the declared runtime. It does not prove the ZeroGateSim theory.
