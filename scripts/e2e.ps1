$ErrorActionPreference = "Stop"

Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

& "$venvPath\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m pytest -m e2e --collect-only
if ($LASTEXITCODE -eq 5) {
    Write-Host "No e2e tests collected yet. Skipping."
    exit 0
}

python -m pytest -m e2e
