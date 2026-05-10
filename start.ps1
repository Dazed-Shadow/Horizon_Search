# Horizon Search - Windows Startup Script
# Run this in VS Code's PowerShell terminal, or double-click from Explorer

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host ""
Write-Host "=== Horizon Search ===" -ForegroundColor Cyan
Write-Host ""

# ── Resolve python executable (handles PATH gaps) ─────────────────────────────
$pythonExe = $null
foreach ($candidate in @("python", "py", "python3")) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($found) { $pythonExe = $candidate; break }
}

if (-not $pythonExe) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host "  Download the official installer from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  During install check 'Add python.exe to PATH', then restart VS Code." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

# ── Detect Microsoft Store Python (broken venv support) ───────────────────────
$pythonPath = (Get-Command $pythonExe).Source
if ($pythonPath -like "*WindowsApps*") {
    Write-Host "ERROR: Microsoft Store Python detected." -ForegroundColor Red
    Write-Host "  Store Python cannot create virtual environments." -ForegroundColor Yellow
    Write-Host "  Fix:" -ForegroundColor Yellow
    Write-Host "    1. Settings -> Apps -> search 'Python' -> Uninstall" -ForegroundColor Yellow
    Write-Host "    2. Download from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "    3. During install check 'Add python.exe to PATH'" -ForegroundColor Yellow
    Write-Host "    4. Restart VS Code and run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

$hasNode = Get-Command node -ErrorAction SilentlyContinue
$hasNpm  = Get-Command npm  -ErrorAction SilentlyContinue
if (-not $hasNode -or -not $hasNpm) {
    Write-Host "ERROR: Node.js / npm not found." -ForegroundColor Red
    Write-Host "  Download from https://nodejs.org (LTS version)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

Write-Host "Python: $(&$pythonExe --version)  [$pythonPath]" -ForegroundColor Green
Write-Host "Node:   $(node --version)" -ForegroundColor Green
Write-Host "npm:    $(npm --version)"  -ForegroundColor Green
Write-Host ""

# ── Backend setup ─────────────────────────────────────────────────────────────
$backendDir = Join-Path $root "backend"
Set-Location $backendDir

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created backend\.env — add your SAM_GOV_API_KEY before searching!" -ForegroundColor Yellow
    Write-Host ""
}

# Recreate venv if missing or broken (pip.exe absent)
$pipExe    = Join-Path $backendDir ".venv\Scripts\pip.exe"
$uvicornExe = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path $pipExe)) {
    Write-Host "[1/2] Creating Python virtual environment..." -ForegroundColor Cyan
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force ".venv"
        Write-Host "  Removed incomplete .venv, rebuilding..." -ForegroundColor Gray
    }
    & $pythonExe -m venv .venv
    if (-not (Test-Path $pipExe)) {
        Write-Host "ERROR: venv created but pip.exe is missing." -ForegroundColor Red
        Write-Host "  Try running: $pythonExe -m ensurepip --upgrade" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"; exit 1
    }
}

Write-Host "[1/2] Installing backend dependencies..." -ForegroundColor Cyan
& $pipExe install -q -r requirements.txt

# Launch backend in a new terminal window
$backendCmd = "Set-Location '$backendDir'; & '$uvicornExe' main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Write-Host "  Backend started  ->  http://localhost:8000" -ForegroundColor Green
Write-Host "  API docs         ->  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

# ── Frontend setup ────────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "frontend"
Set-Location $frontendDir

Write-Host "[2/2] Installing frontend dependencies..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules")) { npm install }

$frontendCmd = "Set-Location '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "  Frontend started ->  http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "=== Both servers are running ===" -ForegroundColor Cyan
Write-Host "  Open http://localhost:5173 in your browser." -ForegroundColor White
Write-Host "  Close the two terminal windows to stop the servers." -ForegroundColor Gray
Write-Host ""
