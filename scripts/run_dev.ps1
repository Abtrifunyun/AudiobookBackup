$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv")) {
    py -3.14 -m venv .venv
}

& ".venv\Scripts\Activate.ps1"
pip install -r requirements.txt --quiet
uvicorn app.main:app --reload --port 8000
