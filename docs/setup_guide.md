# Horizon Search — Setup Guide

Horizon Search is a government contract search tool built for veteran-owned LLCs. It pulls live
opportunities from SAM.gov and surfaces them with veteran-specific set-aside filters (SDVOSB, VOSB,
etc.). The backend is a Python FastAPI service; the frontend is a React + Vite + Tailwind app.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Configure Your SAM.gov API Key](#3-configure-your-samgov-api-key)
4. [Backend Setup](#4-backend-setup)
5. [Frontend Setup](#5-frontend-setup)
6. [Verify It's Working](#6-verify-its-working)
7. [Running the Test Suite](#7-running-the-test-suite)
8. [Filter Guide](#8-filter-guide)
9. [Getting Future Updates](#9-getting-future-updates)
10. [Troubleshooting](#10-troubleshooting)
11. [Coming Next](#11-coming-next)

---

## 1. Prerequisites

Install each of the following before proceeding.

| Tool | Version | Download |
|------|---------|----------|
| **Git** | Any recent | https://git-scm.com/downloads |
| **Python** | 3.11 or higher | https://www.python.org/downloads/ |
| **Node.js** | 18 LTS or higher | https://nodejs.org |
| **VS Code** | Any recent | https://code.visualstudio.com |

> **Important — Python source matters.**
> Download Python from **python.org**, not the Microsoft Store. The Microsoft Store version ships
> without `pip` and cannot create virtual environments. During the python.org installer, check the
> box labelled **"Add python.exe to PATH"** before clicking Install.

After installing, open a new PowerShell terminal and confirm:

```powershell
python --version
node --version
npm --version
git --version
```

All four commands should print version numbers without errors.

---

## 2. Clone the Repository

```powershell
git clone https://github.com/dazed-shadow/horizon_search.git
cd horizon_search
git checkout claude/military-contract-search-tool-9hm2D
```

The repository contains two top-level directories:

- `backend/` — FastAPI application (Python)
- `frontend/` — React/Vite application (JavaScript)

---

## 3. Configure Your SAM.gov API Key

Horizon Search pulls live contract data from the SAM.gov Opportunities API. A free API key is
required.

**Get your key:**

1. Go to https://sam.gov/profile/details
2. Log in (or register for a free account — takes about 15 minutes).
3. Scroll to the **API Keys** section and click **Generate New Key**.
4. The key activates within 24 hours of generation.

**Add the key to the project:**

```powershell
cd backend
Copy-Item .env.example .env
```

Open `backend\.env` in VS Code and replace the placeholder:

```
SAM_GOV_API_KEY=your_actual_key_here
```

> The `.env` file is listed in `.gitignore` and will never be committed to the repository.

---

## 4. Backend Setup

From the `backend\` directory:

**Create a virtual environment:**

```powershell
python -m venv .venv
```

**Activate it:**

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, see [Troubleshooting — Execution Policy](#10-troubleshooting).

**Install dependencies:**

```powershell
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, httpx, pydantic, and python-dotenv.

**Start the backend server:**

```powershell
uvicorn main:app --reload --port 8000
```

The `--reload` flag automatically restarts the server whenever you save a Python file. Leave this
terminal open; the backend runs here.

---

## 5. Frontend Setup

Open a **second** PowerShell terminal and navigate to the `frontend\` directory:

```powershell
cd path\to\horizon_search\frontend
```

**Install Node dependencies:**

```powershell
npm install
```

**Start the development server:**

```powershell
npm run dev
```

Vite will print a local URL — typically `http://localhost:5173`. Leave this terminal open.

---

## 6. Verify It's Working

With both servers running, open your browser and check:

| URL | Expected result |
|-----|-----------------|
| `http://localhost:5173` | Horizon Search UI loads with a search bar |
| `http://localhost:8000/health` | JSON: `{"status": "ok"}` |
| `http://localhost:8000/docs` | FastAPI interactive API documentation |

If the yellow banner **"SAM.gov API key not configured"** appears on the search page, your `.env`
file is missing or the key value is still the placeholder. Edit `backend\.env` and restart the
backend server.

---

## 7. Running the Test Suite

The backend ships with 31 automated tests. Install the dev dependencies first (once):

```powershell
cd backend
pip install -r requirements-dev.txt
```

Run the full suite:

```powershell
python -m pytest -v
```

All 31 tests should pass. The tests use mocked SAM.gov responses so they do not require a live API
key or internet connection.

To run a specific test file:

```powershell
python -m pytest tests/test_contracts.py -v
python -m pytest tests/test_parsing.py -v
python -m pytest tests/test_health.py -v
```

---

## 8. Filter Guide

The filter panel lives in the left sidebar of the search page. All filters are optional and combine
with AND logic. Click **Apply Filters** after making selections.

### Open Solicitations Only

A toggle switch, on by default. When enabled, award notices (type `a`) are excluded from results
so you only see contracts that are still open for bids. Turn it off if you want to research
recently awarded contracts for market intelligence.

### Veteran & Small Business Set-Aside

A grouped dropdown. This is the most important filter for a veteran-owned LLC.

**Veteran-Owned group:**

| Code | Name | What it means |
|------|------|---------------|
| `SDVOSBC` | SDVOSB Competitive | Open competition among certified Service-Disabled Veteran-Owned Small Businesses |
| `SDVOSBS` | SDVOSB Sole Source | Single-award to a specific SDVOSB without competition |
| `VSB` / `VOSB` | Veteran-Owned Small Business | Broader veteran set-aside (not limited to service-disabled) |

**Other set-aside groups also available:** 8(a), HUBZone, Women-Owned (WOSB/EDWOSB), and general
Small Business.

> To compete for SDVOSB set-asides, your business must be certified through the VA CVE
> (Center for Verification and Eligibility). Register first at https://sam.gov, then apply at
> https://www.va.gov/osdbu/.

### Solicitation Type

Filters by the stage of the procurement process:

| Code | Type | When to use |
|------|------|-------------|
| `o` | Solicitation (RFP/RFQ/IFB) | Active bids — you can respond now |
| `p` | Pre-Solicitation | Upcoming bids — start preparing |
| `k` | Combined Synopsis/Solicitation | Combined notice + solicitation |
| `r` | Sources Sought / RFI | Agency gauging market interest — respond to get on radar |
| `s` | Special Notice | Miscellaneous agency announcements |
| `a` | Award Notice | Already awarded — useful for research (requires toggling off "Open Only") |

### Industry (NAICS Code)

Filters by North American Industry Classification System code. Select a common code from the
dropdown or type a 6-digit NAICS code manually. Common codes pre-loaded include IT services
(541511–541519), construction (236220, 237310), engineering (541330), staffing (561320), and
security services (561612).

### Agency / Department

Free-text search against the contracting agency name. Examples:
- `Department of Defense`
- `Department of Veterans Affairs`
- `Department of Homeland Security`

Partial matches work — entering `Veterans` will match the VA.

### Place of Performance

A state dropdown. Filters to contracts where the primary work location is in the selected state.
Useful if your business operates in a specific region.

### Posted Date Range

Restricts results to contracts posted within a date window. Useful for finding very recent
postings (e.g., last 7 days) or auditing a historical period.

### Response Deadline

Filters by when responses are due. Use this to find contracts with upcoming deadlines — for
example, set "Deadline From" to today's date to exclude already-expired solicitations.

### Quick Filters

The row of pill buttons at the top of the page (below the search bar) provides one-click shortcuts
for the most common veteran-owned business filter combinations: All SDVOSB, SDVOSB Sole Source,
VOSB, 8(a), HUBZone, and Sources Sought.

---

## 9. Getting Future Updates

Pull the latest code from the working branch and restart the backend:

```powershell
git pull origin claude/military-contract-search-tool-9hm2D
```

If new Python dependencies were added:

```powershell
cd backend
pip install -r requirements.txt
```

If new Node dependencies were added:

```powershell
cd frontend
npm install
```

Then restart the backend (`Ctrl+C` in the uvicorn terminal, then `uvicorn main:app --reload --port 8000`).
The Vite frontend hot-reloads automatically — no restart needed.

---

## 10. Troubleshooting

### `.venv` pip.exe is missing after `python -m venv .venv`

This happens when Python was installed from the Microsoft Store. The Store version ships without
pip and cannot build working virtual environments.

Fix:
1. Open **Settings → Apps → Installed Apps**, search for `Python`, and uninstall the Microsoft
   Store version.
2. Download the official installer from https://www.python.org/downloads/.
3. During install, check **"Add python.exe to PATH"**.
4. Restart VS Code, then retry the backend setup steps.

### PowerShell blocks `.venv\Scripts\Activate.ps1` (Execution Policy)

```
.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

Run this command in PowerShell (as Administrator if needed):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry activating the virtual environment.

### `python` is not recognised as a command

Windows may use `py` instead of `python`. Try:

```powershell
py --version
py -m venv .venv
py -m pip install -r requirements.txt
```

Alternatively, find where Python is installed and add it to your PATH manually via
**System Properties → Environment Variables → Path**.

### Port 8000 is already in use

```
ERROR: [Errno 98] Address already in use
```

Find and stop the process occupying port 8000:

```powershell
netstat -ano | findstr :8000
```

Note the PID in the last column, then:

```powershell
taskkill /PID <pid> /F
```

Then restart uvicorn. The same pattern applies to port 5173 for the Vite frontend.

### The yellow "API key not configured" banner appears

Open `backend\.env` in a text editor and confirm:

1. The file exists (not just `.env.example`).
2. The line reads `SAM_GOV_API_KEY=` followed by your actual key — not the placeholder
   `your_api_key_here`.
3. Save the file and restart the backend server.

### Search returns no results even with a valid key

SAM.gov API keys can take up to 24 hours to activate after generation. If your key is brand new,
wait and try again the following day.

---

## 11. Coming Next

Web deployment documentation is in progress. Once deployed, Horizon Search will be accessible
from any browser without local setup. Details will be added to this guide when the hosted
environment is configured.

In the meantime, the application runs fully locally using the steps above.
