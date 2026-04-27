param(
    [switch]$SkipPlaywright
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "== AI News Agent installer =="
Write-Host "Project: $ProjectRoot"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Please install Python 3.11+ and rerun this script."
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python was not found: $Python"
}

Write-Host "Upgrading pip..."
& $Python -m pip install --upgrade pip

Write-Host "Installing dependencies..."
& $Python -m pip install -r requirements.txt

if (-not $SkipPlaywright) {
    Write-Host "Installing Playwright Chromium..."
    & $Python -m playwright install chromium
}

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path "config\douyin_accounts.local.yaml")) {
    Write-Host "Creating config\douyin_accounts.local.yaml from template..."
    Copy-Item "config\douyin_accounts.yaml" "config\douyin_accounts.local.yaml"
}

Write-Host "Initializing SQLite database..."
& $Python run.py init-db

Write-Host ""
Write-Host "Install complete."
Write-Host "Next steps:"
Write-Host "1. Edit .env"
Write-Host "2. Edit config\douyin_accounts.local.yaml"
Write-Host "3. Run scripts\healthcheck.ps1"
