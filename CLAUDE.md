# Horizon Search — Project Context

Government contract search tool for veteran-owned LLCs. Searches SAM.gov's public API and surfaces opportunities filtered by veteran set-aside programs (SDVOSB, VOSB, 8(a), HUBZone, WOSB).

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI 0.115, Pydantic v2, httpx async |
| Frontend | React 18, Vite, Tailwind CSS, react-router-dom v6 |
| External API | SAM.gov Opportunities v2 (`https://api.sam.gov/opportunities/v2/search`) |
| Tests | pytest + pytest-asyncio + respx (31 tests, all must pass before push) |

## Repo layout

```
backend/
  main.py                 # FastAPI app, CORS, router registration
  routers/contracts.py    # /api/contracts/search, /filters/*
  routers/config.py       # /api/config/status (API key health check)
  services/sam_gov.py     # SAM.gov API integration + parsing
  models/contract.py      # Pydantic models (Contract, ContractSearchResult)
  tests/                  # pytest suite
  .env                    # NOT committed — copy from .env.example
frontend/
  src/
    pages/SearchPage.jsx        # Main search UI
    pages/LicensingPage.jsx     # Veteran licensing guide
    pages/ContractPrimerPage.jsx # How to Win a Contract primer
    components/FilterPanel.jsx
    components/ContractCard.jsx
    hooks/useContracts.js       # API calls, filter state, pagination
    utils/constants.js          # SET_ASIDES, SOLICITATION_TYPES, NAICS codes
scripts/
  notion_client.py  # Reusable Notion API client
  notion_setup.py   # One-time workspace setup (run locally)
docs/
  setup_guide.md / .html  # End-user setup documentation
  veteran_llc_requirements.md / .pdf
BACKLOG.md                # Lightweight commit-level tracker — keep in repo
```

## Development branch

`claude/military-contract-search-tool-9hm2D` — all work goes here. Never push to `main` directly.

## Critical SAM.gov API constraints

- **Requires date range** — always send `postedFrom` / `postedTo` (default: last 90 days). Missing dates → 400.
- **No `status` param** — v2 does not accept `status=active`. Removed.
- **Integer field types** — SAM.gov returns `naicsCode` and `classificationCode` as integers. Use `_str_or_none()` when assigning to `Optional[str]` model fields.
- **`totalRecords` as string** — sometimes returned as `"1234"` instead of `1234`. The `ContractSearchResult.coerce_total` validator handles this.
- **Rate limits** — free tier; avoid hammering in dev. See BACKLOG for planned caching.
- **State filter param** — `placeOfPerformanceState`, not `state`.

## Key conventions

- All `_parse_opportunity` field assignments go through `_str_or_none()` to coerce non-string values safely.
- `open_only=True` (default) post-filters contracts where `solicitation_type in {"a", "u"}` after the API call (SAM.gov has no server-side filter for this).
- respx tests: use `mock.route(url__startswith=SAM_URL)` not `mock.get(SAM_URL)` — httpcore passes method as bytes, breaking the Method pattern matcher.
- Windows startup: `start.ps1` (PowerShell). Linux/Mac: `start.sh`.

## Agent workflow — Opus + Sonnet + Notion

This project runs a two-tier agent model:

| Agent | Role |
|---|---|
| **Opus** | Orchestrator — architectural decisions, feature design, direction |
| **Sonnet** | Implementer — writes and tests all code based on Opus guidance |
| **Notion** | Shared memory — all decisions, specs, and session logs land here |

**When to invoke Opus:**
- New feature design (anything touching more than one file or introducing a new concept)
- Architecture questions (auth strategy, data model changes, new integrations)
- Prioritization disagreements or tradeoffs

**How to invoke Opus in Claude Code:**
Use the Agent tool with `subagent_type: "claude"` and `model: "opus"`. Pass the question with full context. Opus writes its recommendation back; Sonnet implements and logs the decision to Notion.

**Notion workspace:** PROJECT-HORIZON_SEARCH
- **Decisions DB** — every architectural choice with rationale and who made it
- **Backlog DB** — canonical feature/bug list (source of truth over BACKLOG.md)
- **Session Log DB** — per-session record of what was done and what's next
- **Reference DB** — SAM.gov quirks, deployment notes, external links

**Session start checklist:**
1. Read BACKLOG.md for open items
2. Check Notion Session Log for the most recent session's "Next session" notes
3. Check Notion Backlog for any items added between sessions
4. Confirm all tests pass before starting new work

## Notion setup (one-time)

Run from the repo root after adding `NOTION_API_KEY` and `NOTION_ROOT_PAGE_ID` to `backend/.env`:
```
python scripts/notion_setup.py
```
Requires the MR_C-HANDS integration to be connected to the root page in Notion UI first (page ••• → Connections → MR_C-HANDS).

## Owner preferences

- Outreach and inclusivity for newcomers is the north star — every feature should reduce friction for someone learning federal contracting for the first time.
- Commit messages: concise, explain WHY not what.
- No half-finished features — complete each item before moving to the next.
- Test new parsing logic before pushing — run `python -m pytest -v` from `backend/`.
- BACKLOG.md lives in the repo — edit it there, not in a separate local copy.
- User pulls latest via `git pull origin claude/military-contract-search-tool-9hm2D` after each push.
