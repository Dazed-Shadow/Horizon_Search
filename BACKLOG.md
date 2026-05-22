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

## [2026-05-22] Brand identity — logo + company name
**Type:** Feature
**Priority:** Medium — OPEN
**Tags:** #frontend #ux #docs
**Detail:** Two related items tracked together:
- **Logo**: A proper mark for Horizon Search to replace the current SVG placeholder in the Mission page About section and the Navbar icon. Consider a horizon line / star / compass motif that resonates with a veteran audience. Placeholder is in `MissionPage.jsx` (the 80×80 brand-900 square) and `Navbar.jsx` (the scales SVG).
- **Business/company name**: The site owner intends to walk through the same SAM.gov registration process featured on the Start Here page — registering their own veteran LLC. The company name will feed into the founderNote in `frontend/src/data/testimonials.js` (`name` and `role` fields) and the About section of the Mission page. Until then, "Horizon Search" is the working name.
- **Next steps**: Once business name is decided, update `testimonials.js` founderNote, Mission page About section, and footer in `App.jsx`.

---

## [2026-05-22] Opus recommendations — pre-distribution outreach & visual uplift
**Type:** Feature
**Priority:** High — IN PROGRESS
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
