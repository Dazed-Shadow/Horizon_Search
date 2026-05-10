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
    pages/SearchPage.jsx  # Main search UI
    pages/LicensingPage.jsx # Veteran licensing guide
    components/FilterPanel.jsx
    components/ContractCard.jsx
    hooks/useContracts.js # API calls, filter state, pagination
    utils/constants.js    # SET_ASIDES, SOLICITATION_TYPES, NAICS codes
docs/
  setup_guide.md / .html  # End-user setup documentation
  veteran_llc_requirements.md / .pdf
BACKLOG.md                # Feature/bug tracker — read before each session
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

## Owner preferences

- Commit messages: concise, explain WHY not what.
- No half-finished features — complete each item before moving to the next.
- Test new parsing logic before pushing — run `python -m pytest -v` from `backend/`.
- User downloads via `git pull origin claude/military-contract-search-tool-9hm2D` after each push.
