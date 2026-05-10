# Horizon Search - Windows Startup Script
# Run this in VS Code's PowerShell terminal, or double-click from Explorer

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host ""
Write-Host "=== Horizon Search ===" -ForegroundColor Cyan
Write-Host ""

# ── Prerequisites check ──────────────────────────────────────────────────────
$hasPython = Get-Command python -ErrorAction SilentlyContinue
$hasNode   = Get-Command node   -ErrorAction SilentlyContinue
$hasNpm    = Get-Command npm    -ErrorAction SilentlyContinue

if (-not $hasPython) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host "  Download from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not $hasNode -or -not $hasNpm) {
    Write-Host "ERROR: Node.js / npm not found." -ForegroundColor Red
    Write-Host "  Download from https://nodejs.org (LTS version)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python: $(python --version)"  -ForegroundColor Green
Write-Host "Node:   $(node --version)"    -ForegroundColor Green
Write-Host "npm:    $(npm --version)"     -ForegroundColor Green
Write-Host ""

# ── Backend setup ─────────────────────────────────────────────────────────────
$backendDir = Join-Path $root "backend"
Set-Location $backendDir

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created backend\.env from example." -ForegroundColor Yellow
    Write-Host "  Add your SAM_GOV_API_KEY to backend\.env before searching!" -ForegroundColor Yellow
    Write-Host ""
}

if (-not (Test-Path ".venv")) {
    Write-Host "[1/2] Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "[1/2] Installing backend dependencies..." -ForegroundColor Cyan
& ".venv\Scripts\pip.exe" install -q -r requirements.txt

# Launch backend in a new PowerShell window
$backendCmd = "Set-Location '$backendDir'; & '.venv\Scripts\uvicorn.exe' main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Write-Host "  Backend started  ->  http://localhost:8000" -ForegroundColor Green
Write-Host "  API docs         ->  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

# ── Frontend setup ────────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "frontend"
Set-Location $frontendDir

Write-Host "[2/2] Installing frontend dependencies..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules")) {
    npm install
}

# Launch frontend in a new PowerShell window
$frontendCmd = "Set-Location '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "  Frontend started ->  http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "=== Both servers are running ===" -ForegroundColor Cyan
Write-Host "  Open http://localhost:5173 in your browser." -ForegroundColor White
Write-Host "  Close the two terminal windows to stop the servers." -ForegroundColor Gray
Write-Host ""
