$ErrorActionPreference = "Stop"

Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

& "$venvPath\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
