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

## [2026-05-25] NAICS Insights — SQLite persistent cache + 24-month data
**Type:** Enhancement
**Priority:** High — COMPLETE (Hybrid resolution per Opus)
**Tags:** #backend #frontend #perf #api
**Detail:** The Insights page was fetching 27–39 live SAM.gov calls per load, causing "backend not responding" errors for users who only ran the Vite frontend. Resolved via a hybrid architecture (Opus recommendation):
1. **SQLite persistent cache** (`backend/data/insights.db`) — pre-seeded for all 42 COMMON_NAICS codes × 24 months + 15 agencies = 1,716 data points. Survives restarts.
2. **Static JSON bundle** (`frontend/public/naics-insights.json`, 113KB) — exported from SQLite and served by Vite directly. The Insights page loads instantly from this file for all 42 codes with no backend required.
3. **Set-aside filter removed from InsightsPage** — the only code path that required the backend. Set-aside filtered research lives in the Search Contracts page.
4. **Snapshot date label** — "Data as of [generated_at]" shown in the hero so users understand the data is a periodic snapshot.
5. **Longer-term** — re-enable set-aside filtering and custom codes once the app is deployed to a hosted URL with a persistent backend (see deployment BACKLOG item). Refresh scripts: `scripts/seed_insights.py` → `scripts/export_insights_json.py` → commit JSON.
**Resolution:** Committed 2026-05-25. Static path works with only `npm run dev` running.

---

## [2026-05-24] LLC identity — Shade of Design LLC, tagline, accurate specialties
**Type:** Feature
**Priority:** High — COMPLETE
**Tags:** #frontend #ux #outreach
**Detail:** Jon registered Shade of Design LLC (New Jersey, single-member, design & data analytics). Jon is not a veteran. Site updated to reflect accurate identity — no veteran-ownership claims anywhere:
1. **Company name** — `founderNote.name` → "Shade of Design LLC"; `founderNote.role` → "Design & Data Analytics · Building tools for veteran entrepreneurs"
2. **Tagline** "Matching services to those who serve" — Navbar subtitle (every page), footer (every page), Mission About section. Describes what the tool does (connects services to veterans), not what the builder is.
3. **Specialty badges** — "Data Analytics" (blue) + "Small Business" (grey). "Veteran-Owned" deliberately excluded — do not add it unless a qualifying veteran holds 51%+ unconditional ownership per VetCert.
4. **About paragraph** — "built by Shade of Design LLC — a small design and data analytics business dedicated to building tools that help veteran entrepreneurs access federal contracting opportunities."
**Resolution:** Committed 2026-05-24. Files: `testimonials.js`, `MissionPage.jsx`, `Navbar.jsx`, `App.jsx`.

## [2026-05-22] Brand identity — logo (still open)
**Type:** Feature
**Priority:** Medium — OPEN
**Tags:** #frontend #ux #docs
**Detail:** Company name RESOLVED — "Shade of Design LLC" is now live in `founderNote.name` and the Mission page About section. One item remains:
- **Logo**: Replace the scales SVG placeholder in `Navbar.jsx` and the 80×80 brand-900 square in `MissionPage.jsx` About section. Shade of Design has a brand kit (shield/flame mark, Deep Ocean Blue #1A3E62, Slate Grey-Blue #5D809D). When the Horizon Search logo is ready, drop an SVG into `frontend/src/assets/` and update both components.
- **Optional**: If SAM.gov registration completes, add `"SAM.gov Registered"` to `founderNote.specialties` array in `testimonials.js`.

---

## [2026-05-24] NAICS Activity Insights — Phase 1 (backtesting + forecasting foundation)
**Type:** Feature
**Priority:** High — COMPLETE
**Tags:** #backend #frontend #api #ux
**Detail:** 12-month historical contract count aggregation for any NAICS + set-aside combo. Shows veterans how active a given code has been before they commit to pursuing certifications.
- `GET /api/insights/naics-activity?naics_code=&set_aside=&months=` — 12 SAM.gov calls (one per month), asyncio.gather with Semaphore(3), 24h cache historical / 5m current
- `NaicsInsightPanel` — full-width panel above results with CSS-only bar chart (no chart library), 3-stat summary, and server-generated plain-language interpretation
- "View 12-month activity" button in FilterPanel NAICS section (visible when a NAICS code is selected)
- FY end detection: interpretation mentions July–September surge when peak falls in those months
- 8 new tests, all passing. Total test suite: 41 tests.
**Resolution:** Committed 2026-05-24.

## [2026-05-24] NAICS Activity Insights — Phase 2 (best months, FY forecast, agency breakdown)
**Type:** Feature
**Priority:** Medium — COMPLETE
**Tags:** #backend #frontend #api
**Detail:** Three new insight features added to the NAICS Activity panel:
1. **Best Months to Bid** — top 3 high-activity months, slowest months, 2-sentence recommendation, prep window (begin by [month before peak])
2. **FY Forecast / Surge Countdown** — amber callout during June–Sep surge window; gray callout mid-year and Q1; always shows days remaining until Sep 30
3. **Per-Agency Breakdown** — 15 major federal agencies queried via `organizationName` filter; indigo bar chart of top 5 active agencies; plain-language interpretation
- 27 SAM.gov calls per first load (12 monthly + 15 agency); all cached 24h; same Semaphore(3) concurrency
- 10 new tests (agency, bid timing, FY forecast, shape); 51 total tests, all passing
**Resolution:** Committed 2026-05-24. Files: `backend/models/insights.py`, `backend/services/insights.py`, `backend/tests/test_insights.py`, `frontend/src/components/NaicsInsightPanel.jsx`.

## [2026-05-24] NAICS Activity Insights — Phase 3 (deferred)
**Type:** Feature
**Priority:** Low — OPEN
**Tags:** #backend #frontend #api
**Detail:** Items deferred from Phase 2 for a future session:
- Persistent cache (SQLite) to survive restarts and reduce SAM.gov calls across sessions
- Award dollar-amount trend line (parse awardAmount from historical data)
- Compare multiple NAICS codes side-by-side

## [2026-05-24] Brand color palette — missing stops causing invisible text — FIXED
**Type:** Bug
**Priority:** High — COMPLETE
**Tags:** #frontend #bug #ux
**Detail:** `brand-200`, `brand-300`, `brand-400`, `brand-800` were used across 10+ components but not defined in `tailwind.config.js`. Tailwind generated no CSS for those classes, so text fell back to inherited color — black on dark backgrounds (Mission testimonials section, Navbar subtitle, SearchPage quick-filter label, TrailblazersPage bottom CTA, etc.). The "Mission" nav text appearing black was a symptom of this broader gap.
**Resolution:** Added the four missing stops to `tailwind.config.js` using the standard Tailwind indigo scale (200→#c7d2fe, 300→#a5b4fc, 400→#818cf8, 800→#312e81). Full brand-50 through brand-900 palette now defined.

---

## [2026-05-24] Notion keys — ACTION REQUIRED
**Type:** Enhancement
**Priority:** High — BLOCKED (waiting on JR)
**Tags:** #docs
**Detail:** `scripts/notion_sync.py` is ready and covers the full project state. Blocked on two keys missing from `backend/.env`:
1. `NOTION_API_KEY=<integration token from notion.so/my-integrations>`
2. `NOTION_ROOT_PAGE_ID=<32-char hex ID from root page URL>`
Then run: `python scripts/notion_sync.py` from the repo root.
Once run, all 6 databases (Decisions, Backlog, Session Log, Reference, Changes, Test Scenarios) will be seeded and DB IDs written back to `.env` automatically.

---

## [2026-05-22] Notion logging — catch-up sync script
**Type:** Enhancement
**Priority:** High — COMPLETE
**Tags:** #docs
**Detail:** Notion was never seeded because `NOTION_API_KEY` and `NOTION_ROOT_PAGE_ID` were missing from `backend/.env`. `notion_sync.py` written as a comprehensive, idempotent catch-up script covering all 6 databases: Decisions (10), Backlog (18), Session Log, Reference (10 links), Changes (11 commits), Test Scenarios (33 tests).
**Resolution:** `scripts/notion_sync.py` committed. JR must add `NOTION_API_KEY` and `NOTION_ROOT_PAGE_ID` to `backend/.env`, then run `python scripts/notion_sync.py` from the repo root. Script is idempotent — safe to re-run; skips existing titles.

---

## [2026-05-22] Opus recommendations — pre-distribution outreach & visual uplift
**Type:** Feature
**Priority:** High — COMPLETE
**Tags:** #frontend #ux #outreach
**Detail:** Opus reviewed the current state and recommended the following (ordered as revised with user input):
1. **Plain-language contract translator** — SHIPPED 2026-05-22. "What does this mean?" toggle on cards.
2. **"Start Here" guided onboarding** — SHIPPED 2026-05-22. Bumped up by user. 4-step journey page at /start with expandable FAQs, action checklists, green nav CTA.
3. **Testimonials + Share button** — SHIPPED 2026-05-22. Mission page has full testimonial cards; ShareButton on search hero.
4. **Mission hero with live stats ticker** — SHIPPED 2026-05-22. `/api/contracts/stats` endpoint (1hr cache); SDVOSB/VOSB/SBA counts in search hero.
5. **Mission page** — SHIPPED 2026-05-22 (added by user). `/mission` — hero, values, about section, full testimonial cards, CTAs.
5. **Match Score personalization** — OPEN. Post-distribution week 1.
6. **Trailblazers page** — SHIPPED 2026-05-22. `/trailblazers` — 5 anchor figures, slide-in drawer, articles list.

## [2026-05-22] Trailblazers content — articles URL verification
**Type:** Enhancement
**Priority:** Medium — OPEN
**Tags:** #frontend #docs #outreach
**Detail:** Articles in `frontend/src/data/articles.json` marked `verify:true` need real direct URLs
before wide distribution. Check each source and replace the placeholder homepage URL with the
specific article URL. Also: as the owner finds real SBA veteran success stories that fit the
"Founder Profiles" and "Funding & Contracts" buckets, add them to the articles array.
Sources to check: Inc. Vet 100, Forbes veteran founders, HBR military leadership, Task & Purpose
SDVOSB coverage, We Are The Mighty / Adam Driver AITAF, Military Times / Mark Geist.

---

## [2026-05-16] Reviewing Suggested Enhancements
**Type:** Enhancement
**Priority:** High — COMPLETE
**Tags:** #enhancement #api #backend #frontend #deploy #docs
**Detail:** Next two sessions scoped as follows:
- **Session A:** Contract detail drawer/modal + NAICS code discovery helper — DONE
- **Session B:** Deadline urgency indicators + Sort controls + Bookmark/watch list — DONE (2026-05-19)
- **Longer term goal:** Saved searches, contract value filter, email digest, teaming board. Outreach and inclusivity for newcomers is the north star for all decisions on this project.
**Resolution:** All Session A and B items shipped. Bookmark watch list added ahead of schedule. Commit `432bf71`.

---

## [2026-05-15] VSB code may not match SAM.gov VOSB parameter
**Type:** Bug
**Priority:** Medium — FIXED
**Tags:** #api #bug #frontend
**Detail:** The "Veteran-Owned Small Business" quick link sent `set_aside=VSB` but SAM.gov uses `VOSB`. Filter returned 0 results.
**Resolution:** Changed QUICK_FILTERS in SearchPage.jsx from `set_aside: "VSB"` to `set_aside: "VOSB"`. Fixed alongside contract detail drawer in same commit.

---

## [2026-05-17] Contract detail drawer — deferred items
**Type:** Enhancement
**Priority:** Low — COMPLETE
**Tags:** #frontend #ux
**Detail:** Items intentionally deferred from the Session A drawer implementation:
- Full keyboard focus trap (tab cycling within open drawer) — SHIPPED 2026-05-22
- Deep-link via `?notice=` query param for shareable contract URLs — SHIPPED 2026-05-22
- Slide-in animation (drawer snaps in, no transition) — SHIPPED 2026-05-22
- Save for later / bookmark functionality — SHIPPED 2026-05-19 (commit `432bf71`)

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
