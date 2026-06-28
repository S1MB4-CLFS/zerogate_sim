# ZeroGateSim local demo runner
# Target repo: C:\dev\zerogate_sim
# GitHub: not used

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Repo = "C:\dev\zerogate_sim"
if (!(Test-Path $Repo)) {
    throw "Repo folder not found: $Repo"
}

Set-Location $Repo

$PythonCmd = $null
foreach ($Candidate in @("python", "python3", "py")) {
    $Found = Get-Command $Candidate -ErrorAction SilentlyContinue
    if ($Found) {
        $PythonCmd = $Candidate
        break
    }
}

if (-not $PythonCmd) {
    throw "Python was not found. Install Python 3.11+ or 3.12+, then reopen PowerShell."
}

if (!(Test-Path ".venv\Scripts\python.exe")) {
    & $PythonCmd -m venv .venv
}

$P = ".\.venv\Scripts\python.exe"
& $P -m pip install --upgrade pip
& $P -m pip install -e ".[dev]"
& $P -m pytest
& $P -m zerogate_sim.demo --seed 42 --out runs\demo_seed_42

Write-Host ""
Write-Host "Open:   C:\dev\zerogate_sim\runs\demo_seed_42\summary.md"
Write-Host "Upload: C:\dev\zerogate_sim\runs\demo_seed_42\run_bundle.zip"
