# Horizon Search · Backlog
*Running log of bugs, feature requests, and ideas. Append new items at the top.*

---

## How to use this file

This is **your** file — you own the items, I work through them. Paste in anything you notice while using the app, read or heard about, or just thought of. I read this at the start of every session and prioritize accordingly.

**Pattern for each entry:**

```
## [YYYY-MM-DD] One-line description
**Type:** Bug | Feature | Enhancement | Idea
**Priority:** High | Medium | Low
**Tags:** #area #concept
**Detail:** (free-form — what you observed, what you want, why it matters)
**Resolution:** (filled in when complete — what was done and in which commit)
```

**Tag conventions:**

- `#api` — SAM.gov integration, rate limits, parsing
- `#backend` — FastAPI, models, services
- `#frontend` — React, UI, filters, cards
- `#auth` — API keys, user accounts
- `#perf` — speed, caching, debounce
- `#ux` — usability, layout, mobile
- `#deploy` — hosting, domain, CI/CD
- `#docs` — documentation, guides
- `#bug` `#feature` `#enhancement` `#idea`

---

## Open Items

*New entries go here, newest at the top.*

---

## [2026-05-10] API calls getting blocked after too many searches
**Type:** Bug / Enhancement
**Priority:** High — FIXED
**Tags:** #api #perf #backend #frontend
**Detail:** SAM.gov free-tier API has rate limits (roughly 1,000 calls/day per key). Rapid searching or filter changes hit this quickly in dev and will hit it even faster once deployed to real users.
**Resolution:** Three changes shipped together:
1. **Backend 5-minute TTL cache** (`services/sam_gov.py`) — identical searches within 5 min are served from memory; `_cache_key()` hashes all params except the API key. Cache cleared between test runs via `autouse` fixture.
2. **429 handling in router** (`routers/contracts.py`) — `httpx.HTTPStatusError` with status 429 is now caught before the generic `Exception` handler and re-raised as `HTTPException(429, "SAM.gov daily search limit reached...")` instead of a confusing 502.
3. **Rate-limit UI** (`ContractList.jsx` / `useContracts.js`) — frontend detects `res.status === 429` and shows an amber clock icon with a calm "Search limit reached — wait a few minutes" message instead of the generic red error. Also notes that cached searches won't burn quota.
Tests: `test_search_sam_gov_429`, `test_cache_avoids_duplicate_sam_requests`. Commit: see push.

---

## [2026-05-10] Web deployment / easier access
**Type:** Feature
**Priority:** High
**Tags:** #deploy
**Detail:** Currently requires local setup (Python + Node + git). Goal is a publicly accessible URL so users don't need to install anything. Options to evaluate:
- **Railway** — free tier, one-click Python + static site, custom domain support
- **Render** — similar free tier, good FastAPI support
- **Vercel (frontend) + Railway (backend)** — separate deployment, slightly more setup but scales better
- **Docker Compose** — containerize both services for consistent deploys
Need to decide on hosting before building auth/user features since that shapes the architecture.
**Resolution:** Pending

---

## [2026-05-10] No keyword + SDVOSBC filter returned 500 / empty results
**Type:** Bug
**Priority:** High — FIXED
**Tags:** #api #bug #backend
**Detail:** Clicking the SDVOSBC set-aside button with no keyword caused a 500 error. Root cause: SAM.gov returns `naicsCode` as an integer (e.g. `541512`) but Pydantic v2 typed it as `Optional[str]` and rejected the int silently, dropping every contract in the response.
**Resolution:** Added `_str_or_none()` helper to coerce all string fields; handles `placeOfPerformance` as plain string too. 7 new tests added. Commit `f00295e`.

---

## Completed Items

*Resolved entries stay here as a permanent record.*

---

## [2026-05-09] 500 error on search after ZIP re-download
**Type:** Bug — FIXED
**Tags:** #api #bug #backend
**Detail:** SAM.gov sometimes returns `totalRecords` as a string; also null in fields typed as non-optional `str` caused Pydantic serialization to fail after the try/except block, producing an unhandled 500.
**Resolution:** Added `@field_validator("total")` coercion; default values on all Contract fields; wrapped `_parse_opportunity` in try/except returning Optional. Commit `584ce33`.

---

## [2026-05-09] SAM.gov 400 Bad Request on all searches
**Type:** Bug — FIXED
**Tags:** #api #bug #backend
**Detail:** Sending `status=active` (not supported by v2 API) and missing required `postedFrom`/`postedTo` date range caused 400s.
**Resolution:** Removed `status` param; added default 90-day window; fixed state param name to `placeOfPerformanceState`. Earlier commit.

---

## [2026-05-09] Sidebar scroll independent of results
**Type:** Enhancement — FIXED
**Tags:** #frontend #ux
**Detail:** Filter sidebar scrolled with the page instead of independently.
**Resolution:** Added `sticky top-4 overflow-y-auto max-h-[calc(100vh-5rem)]` to sidebar wrapper.

---
