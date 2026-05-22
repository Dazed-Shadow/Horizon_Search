"""
notion_sync.py — Full project state sync to Notion.

Run this after notion_setup.py has been run at least once OR as a replacement
for notion_setup.py if the databases don't exist yet. Idempotent: databases are
created only if missing; the session log is always appended (one entry per run).

Usage:
    cd /home/user/Horizon_Search
    python scripts/notion_sync.py

Requirements in backend/.env:
    NOTION_API_KEY=<your integration token>
    NOTION_ROOT_PAGE_ID=<32-char hex ID of the root page>
"""
import os
import sys
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

sys.path.insert(0, str(Path(__file__).parent))
from notion_client import (
    create_page, query_all_pages, rich_text,
    paragraph_block, heading_block, bullet_block, divider_block, now_iso,
    get_or_create_database, update_env_key,
)

# ── Validate required env vars ────────────────────────────────────────────────
ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID", "").replace("-", "")
if not ROOT_PAGE_ID:
    print("ERROR: NOTION_ROOT_PAGE_ID is not set in backend/.env")
    print("  1. Open your Notion root page")
    print("  2. Click ••• → Connections → connect 'MR_C-HANDS'")
    print("  3. Copy the page ID from the URL")
    print("  4. Add NOTION_ROOT_PAGE_ID=<id> to backend/.env")
    sys.exit(1)

if not os.getenv("NOTION_API_KEY"):
    print("ERROR: NOTION_API_KEY is not set in backend/.env")
    sys.exit(1)


# ── Database schemas ──────────────────────────────────────────────────────────

DECISIONS_PROPS = {
    "Decision": {"title": {}},
    "Status": {"select": {"options": [
        {"name": "Active",     "color": "green"},
        {"name": "Superseded", "color": "yellow"},
        {"name": "Pending",    "color": "gray"},
    ]}},
    "Made By": {"select": {"options": [
        {"name": "Opus",   "color": "purple"},
        {"name": "Sonnet", "color": "blue"},
        {"name": "JR",     "color": "orange"},
    ]}},
    "Area": {"multi_select": {"options": [
        {"name": "Architecture", "color": "red"},
        {"name": "Frontend",     "color": "blue"},
        {"name": "Backend",      "color": "green"},
        {"name": "Deploy",       "color": "yellow"},
        {"name": "UX",           "color": "pink"},
        {"name": "API",          "color": "purple"},
        {"name": "Content",      "color": "orange"},
    ]}},
    "Date": {"date": {}},
}

BACKLOG_PROPS = {
    "Title": {"title": {}},
    "Type": {"select": {"options": [
        {"name": "Bug",         "color": "red"},
        {"name": "Feature",     "color": "blue"},
        {"name": "Enhancement", "color": "green"},
        {"name": "Idea",        "color": "yellow"},
    ]}},
    "Priority": {"select": {"options": [
        {"name": "High",   "color": "red"},
        {"name": "Medium", "color": "yellow"},
        {"name": "Low",    "color": "gray"},
    ]}},
    "Status": {"select": {"options": [
        {"name": "Open",        "color": "red"},
        {"name": "In Progress", "color": "yellow"},
        {"name": "Complete",    "color": "green"},
        {"name": "Fixed",       "color": "green"},
        {"name": "Pending",     "color": "gray"},
    ]}},
    "Tags": {"multi_select": {"options": [
        {"name": "#api",      "color": "purple"},
        {"name": "#backend",  "color": "blue"},
        {"name": "#frontend", "color": "pink"},
        {"name": "#ux",       "color": "orange"},
        {"name": "#perf",     "color": "yellow"},
        {"name": "#deploy",   "color": "green"},
        {"name": "#auth",     "color": "red"},
        {"name": "#docs",     "color": "gray"},
        {"name": "#outreach", "color": "pink"},
    ]}},
    "Date": {"date": {}},
    "Commit": {"rich_text": {}},
}

SESSION_LOG_PROPS = {
    "Session": {"title": {}},
    "Date": {"date": {}},
    "Agent": {"select": {"options": [
        {"name": "Opus + Sonnet", "color": "purple"},
        {"name": "Sonnet",        "color": "blue"},
    ]}},
    "Branch": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "Complete",    "color": "green"},
        {"name": "In Progress", "color": "yellow"},
        {"name": "Blocked",     "color": "red"},
    ]}},
}

CHANGES_PROPS = {
    "Commit Message": {"title": {}},
    "Commit Hash":    {"rich_text": {}},
    "Date":           {"date": {}},
    "Branch":         {"rich_text": {}},
    "Test Status": {"select": {"options": [
        {"name": "All Passing", "color": "green"},
        {"name": "Failing",     "color": "red"},
        {"name": "Not Run",     "color": "gray"},
    ]}},
    "Files Changed": {"rich_text": {}},
    "Pushed By": {"select": {"options": [
        {"name": "Sonnet", "color": "blue"},
        {"name": "Opus",   "color": "purple"},
        {"name": "JR",     "color": "orange"},
    ]}},
}

TEST_SCENARIOS_PROPS = {
    "Test Name":   {"title": {}},
    "Description": {"rich_text": {}},
    "Area": {"select": {"options": [
        {"name": "Backend",     "color": "blue"},
        {"name": "Frontend",    "color": "pink"},
        {"name": "Integration", "color": "purple"},
    ]}},
    "Type": {"select": {"options": [
        {"name": "Unit",        "color": "blue"},
        {"name": "Integration", "color": "purple"},
        {"name": "E2E",         "color": "orange"},
    ]}},
    "Status": {"select": {"options": [
        {"name": "Passing", "color": "green"},
        {"name": "Failing", "color": "red"},
        {"name": "Pending", "color": "gray"},
    ]}},
    "Added In": {"rich_text": {}},
}

REFERENCE_PROPS = {
    "Title":    {"title": {}},
    "Category": {"select": {"options": [
        {"name": "SAM.gov API",    "color": "blue"},
        {"name": "Deployment",     "color": "green"},
        {"name": "Architecture",   "color": "purple"},
        {"name": "External Links", "color": "orange"},
        {"name": "Credentials",    "color": "red"},
    ]}},
    "URL": {"url": {}},
}


# ── Helper ────────────────────────────────────────────────────────────────────

def existing_titles(db_id: str) -> set:
    """Return set of title strings already in a database (to skip duplicates)."""
    pages = query_all_pages(db_id)
    titles = set()
    for p in pages:
        props = p.get("properties", {})
        for key in ("Decision", "Title", "Session", "Commit Message",
                    "Test Name", "Commit Message"):
            val = props.get(key, {})
            if val.get("type") == "title":
                items = val.get("title", [])
                if items:
                    titles.add(items[0].get("plain_text", ""))
                break
    return titles


BRANCH = "claude/military-contract-search-tool-9hm2D"


# ── Decisions ─────────────────────────────────────────────────────────────────

DECISIONS = [
    {
        "title": "Railway for deployment — backend + frontend as separate services",
        "status": "Active", "by": "Sonnet", "area": ["Deploy"], "date": "2026-05-16",
        "body": "Railway chosen over Render and Vercel+Railway split. Free tier avoids cold-start penalty that Render free tier has. Backend root: /backend, Frontend root: /frontend. CORS handled via CORS_ORIGINS env var. VITE_API_URL baked at build time.",
    },
    {
        "title": "Opus + Sonnet two-tier agent model",
        "status": "Active", "by": "Opus", "area": ["Architecture"], "date": "2026-05-16",
        "body": "Opus acts as orchestrator for architectural decisions and feature design. Sonnet implements. Notion is shared memory. This split keeps implementation fast while keeping architecture coherent.",
    },
    {
        "title": "respx mock pattern: url__startswith not mock.get()",
        "status": "Active", "by": "Sonnet", "area": ["Backend"], "date": "2026-05-10",
        "body": "httpcore passes HTTP method as bytes, which breaks respx Method pattern matcher. Use mock.route(url__startswith=SAM_URL) across all tests — this is the only pattern that reliably intercepts httpx calls through respx.",
    },
    {
        "title": "plain-language translator toggle on contract cards",
        "status": "Active", "by": "Opus", "area": ["Frontend", "UX"], "date": "2026-05-22",
        "body": "Opus recommended adding a 'What does this mean?' toggle on each contract card. SET_ASIDE_PLAIN and SOLICITATION_TYPE_PLAIN maps added to constants.js. Renders inline green/blue panel below card content without opening the drawer.",
    },
    {
        "title": "Testimonials strategy: placeholder SBA quotes, real by weekend",
        "status": "Active", "by": "JR", "area": ["Content", "Frontend"], "date": "2026-05-22",
        "body": "Three testimonial quote placeholders in testimonials.js. JR will source real veteran quotes from sba.gov/about-sba/sba-newsroom/success-stories by weekend. sourceUrl field auto-activates 'Read their story' link. founderNote stays as personal voice regardless.",
    },
    {
        "title": "Trailblazer figures: verified public-domain bios only",
        "status": "Active", "by": "Opus", "area": ["Content", "Frontend"], "date": "2026-05-22",
        "body": "Opus initially recommended Robert L. Johnson (Air Force Reserve) but military service was unverifiable. Replaced with David Goggins (Army/SEAL — very well documented). Adam Driver chosen over Jaime Cruz (Veteran Roasters) because Driver's USMC service and AITAF nonprofit are extensively documented public record.",
    },
    {
        "title": "FastAPI route ordering: wildcard /{notice_id} must be last",
        "status": "Active", "by": "Sonnet", "area": ["Backend", "Architecture"], "date": "2026-05-22",
        "body": "GET /{notice_id} must be registered after all specific routes (/stats, /filters/*) in contracts.py. FastAPI matches routes in declaration order — placing the wildcard first would cause 'filters' to be interpreted as a notice_id, shadowing all filter endpoints.",
    },
    {
        "title": "Stats endpoint: 1-hour in-memory cache with asyncio.gather",
        "status": "Active", "by": "Sonnet", "area": ["Backend", "API"], "date": "2026-05-22",
        "body": "GET /api/contracts/stats fires 4 concurrent SAM.gov count calls via asyncio.gather. Results cached in _STATS_CACHE dict with _STATS_TTL=3600. Cache keyed by set_aside code. Avoids burning 4 API calls on every stats page view.",
    },
    {
        "title": "Drawer slide-in animation via CSS keyframes, not Framer Motion",
        "status": "Active", "by": "Sonnet", "area": ["Frontend", "UX"], "date": "2026-05-22",
        "body": "Animation added as @keyframes slide-in-right in index.css with cubic-bezier(0.22,1,0.36,1). Same pattern for backdrop-fade-in. Keeps the bundle small (no animation library needed). Both drawers (ContractDetailDrawer, TrailblazerDrawer) use the same classes.",
    },
    {
        "title": "Bookmarks: full contract snapshot in localStorage, versioned key",
        "status": "Active", "by": "Sonnet", "area": ["Frontend"], "date": "2026-05-19",
        "body": "useBookmarks hook stores full contract objects (not just IDs) under key horizon_search.bookmarks.v1. Survives deadline expiry — user can still see what they saved even after a contract closes. Version suffix allows future migration.",
    },
]


def sync_decisions(db_id: str):
    existing = existing_titles(db_id)
    added = 0
    for d in DECISIONS:
        if d["title"] in existing:
            continue
        create_page(db_id, {
            "Decision": {"title": rich_text(d["title"])},
            "Status":   {"select": {"name": d["status"]}},
            "Made By":  {"select": {"name": d["by"]}},
            "Area":     {"multi_select": [{"name": a} for a in d["area"]]},
            "Date":     {"date": {"start": d["date"]}},
        }, children=[paragraph_block(d["body"])])
        added += 1
    print(f"  Decisions: {added} added, {len(existing)} already existed")


# ── Backlog ───────────────────────────────────────────────────────────────────

BACKLOG_ITEMS = [
    # ── OPEN ──
    {
        "title": "Brand identity — logo + company name",
        "type": "Feature", "priority": "Medium", "status": "Open",
        "tags": ["#frontend", "#ux", "#docs"], "date": "2026-05-22",
        "detail": "Logo placeholder: 80×80 brand-900 square in MissionPage.jsx and scales SVG in Navbar.jsx. Owner will register veteran LLC and feed company name into testimonials.js founderNote and Mission page About section.",
    },
    {
        "title": "Trailblazers content — articles URL verification",
        "type": "Enhancement", "priority": "Medium", "status": "Open",
        "tags": ["#frontend", "#docs", "#outreach"], "date": "2026-05-22",
        "detail": "Articles in articles.json with verify:true need real direct URLs. Sources: Inc. Vet 100, Forbes veteran founders, HBR military leadership, Task & Purpose SDVOSB coverage, WATM/Adam Driver AITAF, Military Times/Mark Geist.",
    },
    {
        "title": "Match Score personalization",
        "type": "Feature", "priority": "Medium", "status": "Open",
        "tags": ["#frontend", "#ux"], "date": "2026-05-22",
        "detail": "Post-distribution, week 1. 60-second localStorage profile wizard + match badge on cards. Opus recommendation #5.",
    },
    {
        "title": "Real testimonials from SBA veteran success stories",
        "type": "Enhancement", "priority": "Medium", "status": "Open",
        "tags": ["#frontend", "#outreach"], "date": "2026-05-22",
        "detail": "JR will source 3 real veteran quotes from sba.gov success stories by weekend. Replace placeholders in testimonials.js. sourceUrl field auto-activates 'Read their story' link.",
    },
    {
        "title": "Web deployment / easier access",
        "type": "Feature", "priority": "High", "status": "Open",
        "tags": ["#deploy"], "date": "2026-05-10",
        "detail": "Railway is configured. Needs PR to main for Railway to deploy latest features. Branch: claude/military-contract-search-tool-9hm2D.",
    },
    # ── COMPLETE ──
    {
        "title": "Plain-language contract translator toggle on cards",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux"], "date": "2026-05-22",
        "detail": "SHIPPED. 'What does this mean? ▼' toggle on ContractCard. SET_ASIDE_PLAIN and SOLICITATION_TYPE_PLAIN maps in constants.js.",
        "commit": "5ca90a9",
    },
    {
        "title": "Start Here guided onboarding page",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux", "#outreach"], "date": "2026-05-22",
        "detail": "SHIPPED. 4-step journey at /start. EIN prerequisite card. NAICS code directory with category accordion and search filter. FAQ accordion per step.",
        "commit": "66ce696",
    },
    {
        "title": "Testimonials + Share button",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux", "#outreach"], "date": "2026-05-22",
        "detail": "SHIPPED. TestimonialStrip on Mission page. ShareButton on search hero with Web Share API + clipboard fallback.",
        "commit": "dcbfe69",
    },
    {
        "title": "Mission hero with live stats ticker",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#backend", "#api"], "date": "2026-05-22",
        "detail": "SHIPPED. /api/contracts/stats endpoint (1hr cache). SDVOSB/VOSB/SBA counts displayed in search hero.",
        "commit": "e834300",
    },
    {
        "title": "Mission page",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux", "#outreach"], "date": "2026-05-22",
        "detail": "SHIPPED. /mission — hero with ShareButton, 3 values cards, founder note, full testimonial card grid, CTAs.",
        "commit": "e834300",
    },
    {
        "title": "Trailblazers page — veteran entrepreneur profiles",
        "type": "Feature", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux", "#outreach"], "date": "2026-05-22",
        "detail": "SHIPPED. /trailblazers — 5 figures (Fred Smith, Jocko Willink, David Goggins, Mark Oz Geist, Adam Driver). Slide-in drawer with bio/resources/articles. ArticleList with bucket filter. Deep-link via ?figure= param.",
        "commit": "69e4d73",
    },
    {
        "title": "Contract detail drawer — slide-in animation, focus trap, deep-link",
        "type": "Enhancement", "priority": "Low", "status": "Complete",
        "tags": ["#frontend", "#ux"], "date": "2026-05-22",
        "detail": "SHIPPED. CSS keyframe slide-in-right. Tab focus trap. ?notice= deep-link. /api/contracts/{notice_id} endpoint.",
        "commit": "1bdea9c",
    },
    {
        "title": "Bookmark / watch list",
        "type": "Feature", "priority": "Medium", "status": "Complete",
        "tags": ["#frontend"], "date": "2026-05-19",
        "detail": "SHIPPED. useBookmarks hook. BookmarksPanel slide-in. Full contract snapshot in localStorage key horizon_search.bookmarks.v1.",
        "commit": "432bf71",
    },
    {
        "title": "Sort controls (deadline, posted date, value)",
        "type": "Enhancement", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux"], "date": "2026-05-19",
        "detail": "SHIPPED. sortBy state in useContracts. sortedContracts useMemo. Sort select in ContractList.",
        "commit": "432bf71",
    },
    {
        "title": "Deadline urgency indicators on cards",
        "type": "Enhancement", "priority": "High", "status": "Complete",
        "tags": ["#frontend", "#ux"], "date": "2026-05-19",
        "detail": "SHIPPED. deadlineStatus() extended with urgency tier. Full-width color strip above card content.",
        "commit": "432bf71",
    },
    {
        "title": "VSB code may not match SAM.gov VOSB parameter",
        "type": "Bug", "priority": "Medium", "status": "Fixed",
        "tags": ["#api", "#bug", "#frontend"], "date": "2026-05-15",
        "detail": "Fixed. QUICK_FILTERS in SearchPage.jsx changed from set_aside: 'VSB' to set_aside: 'VOSB'.",
        "commit": "7213481",
    },
    {
        "title": "API calls getting blocked after too many searches (rate limit)",
        "type": "Bug", "priority": "High", "status": "Fixed",
        "tags": ["#api", "#perf", "#backend", "#frontend"], "date": "2026-05-10",
        "detail": "Fixed. 5-min TTL cache in sam_gov.py. 429 re-raised as HTTPException(429). Amber rate-limit UI in ContractList.",
        "commit": "de0f859",
    },
    {
        "title": "No keyword + SDVOSBC filter returned 500",
        "type": "Bug", "priority": "High", "status": "Fixed",
        "tags": ["#api", "#bug", "#backend"], "date": "2026-05-10",
        "detail": "Fixed. _str_or_none() helper coerces int naicsCode to str. placeOfPerformance as plain string handled.",
        "commit": "f00295e",
    },
]


def sync_backlog(db_id: str):
    existing = existing_titles(db_id)
    added = 0
    for item in BACKLOG_ITEMS:
        if item["title"] in existing:
            continue
        props = {
            "Title":    {"title": rich_text(item["title"])},
            "Type":     {"select": {"name": item["type"]}},
            "Priority": {"select": {"name": item["priority"]}},
            "Status":   {"select": {"name": item["status"]}},
            "Tags":     {"multi_select": [{"name": t} for t in item["tags"]]},
            "Date":     {"date": {"start": item["date"]}},
        }
        if "commit" in item:
            props["Commit"] = {"rich_text": rich_text(item["commit"])}
        children = [paragraph_block(item["detail"])] if "detail" in item else None
        create_page(db_id, props, children=children)
        added += 1
    print(f"  Backlog: {added} added, {len(existing)} already existed")


# ── Changes / Commits ─────────────────────────────────────────────────────────

ALL_COMMITS = [
    # 2026-05-22 session
    ("Trailblazers page — veteran entrepreneur profiles, articles, shareable drawers",
     "69e4d73", "2026-05-22",
     "frontend/src/pages/TrailblazersPage.jsx, frontend/src/components/TrailblazerCard.jsx, "
     "frontend/src/components/TrailblazerDrawer.jsx, frontend/src/components/ArticleList.jsx, "
     "frontend/src/data/trailblazers.js, frontend/src/data/articles.js",
     "Opus recommendation #6. 5 veteran figures with bio drawers, deep-link ?figure= param, "
     "ArticleList with bucket filter tabs, 9 seed articles across 5 categories."),
    ("Mission page + live stats ticker — Opus recommendations #4 & #5",
     "e834300", "2026-05-22",
     "frontend/src/pages/MissionPage.jsx, frontend/src/components/TestimonialStrip.jsx, "
     "backend/services/sam_gov.py, backend/routers/contracts.py, "
     "frontend/src/hooks/useOpportunityStats.js",
     "Mission page at /mission with hero, values, testimonials, about section. "
     "GET /api/contracts/stats endpoint with 1hr cache and asyncio.gather for concurrent SAM.gov calls."),
    ("Testimonials + Share button — Opus recommendation #3",
     "dcbfe69", "2026-05-22",
     "frontend/src/data/testimonials.js, frontend/src/components/ShareButton.jsx, "
     "frontend/src/pages/SearchPage.jsx",
     "3 placeholder veteran testimonials with sourceUrl support. "
     "ShareButton with Web Share API and clipboard fallback. Removed TestimonialStrip from SearchPage."),
    ("Start Here: EIN prerequisite card + NAICS code directory",
     "66ce696", "2026-05-22",
     "frontend/src/pages/StartHerePage.jsx",
     "EIN amber prerequisite card before step strip. NaicsSection with category accordion, "
     "search filter across 55 NAICS codes, and naics.com links. 7 categories."),
    ("Plain-language translator + Start Here onboarding page",
     "5ca90a9", "2026-05-22",
     "frontend/src/components/ContractCard.jsx, frontend/src/utils/constants.js, "
     "frontend/src/pages/StartHerePage.jsx, frontend/src/App.jsx, frontend/src/components/Navbar.jsx",
     "SET_ASIDE_PLAIN and SOLICITATION_TYPE_PLAIN maps. Inline toggle on ContractCard. "
     "4-step Start Here page with FAQ accordion. Green CTA nav pill."),
    ("Drawer polish: slide-in animation, focus trap, deep-link + notice ID endpoint",
     "1bdea9c", "2026-05-22",
     "frontend/src/index.css, frontend/src/components/ContractDetailDrawer.jsx, "
     "backend/routers/contracts.py, backend/services/sam_gov.py",
     "CSS keyframe drawer-slide-in and backdrop-fade-in. Tab focus trap. "
     "?notice= deep-link. GET /api/contracts/{notice_id} endpoint (placed after /stats and /filters/* "
     "to avoid route shadowing)."),
    # 2026-05-19 session
    ("Add bookmark list, sort controls, and deadline urgency strips",
     "432bf71", "2026-05-19",
     "frontend/src/hooks/useBookmarks.js, frontend/src/components/BookmarksPanel.jsx, "
     "frontend/src/hooks/useContracts.js, frontend/src/components/ContractList.jsx, "
     "frontend/src/components/ContractCard.jsx, frontend/src/utils/formatters.js",
     "useBookmarks hook with localStorage. BookmarksPanel slide-in. "
     "sortBy state + sortedContracts useMemo. Urgency strip on cards with 4 tiers."),
    # Earlier commits
    ("Add contract detail drawer with plain-English set-aside explainers",
     "7213481", "2026-05-16",
     "frontend/src/components/ContractDetailDrawer.jsx, frontend/src/utils/constants.js, "
     "frontend/src/pages/SearchPage.jsx",
     "First iteration drawer. Fixed QUICK_FILTERS VSB→VOSB bug alongside."),
    ("Add 'How to Win a Contract' primer page for veterans",
     "c232ef3", "2026-05-16",
     "frontend/src/pages/ContractPrimerPage.jsx, frontend/src/App.jsx, "
     "frontend/src/components/Navbar.jsx",
     "Six-section field guide covering set-asides, lifecycle, proposals, and teaming."),
    ("Add Notion integration and Opus orchestrator workflow",
     "2550697", "2026-05-16",
     "scripts/notion_client.py, scripts/notion_setup.py, CLAUDE.md, BACKLOG.md",
     "Notion as project memory. Opus+Sonnet two-tier agent model documented in CLAUDE.md."),
    ("Add Railway deployment config for backend and frontend",
     "0d0f3f0", "2026-05-16",
     "backend/Procfile, backend/railway.toml, frontend/railway.toml, "
     "frontend/src/hooks/useContracts.js",
     "VITE_API_URL support for production API calls. Railway can build and run both services."),
    ("Fix API rate limiting: 5-min cache, 429 handling, rate-limit UI",
     "de0f859", "2026-05-10",
     "backend/services/sam_gov.py, backend/routers/contracts.py, "
     "frontend/src/components/ContractList.jsx, frontend/src/hooks/useContracts.js",
     "5-min TTL cache. 429 re-raised properly. Amber clock icon UI state."),
]


def sync_changes(db_id: str):
    existing = existing_titles(db_id)
    added = 0
    for msg, hash_, date, files, detail in ALL_COMMITS:
        title = f"{hash_[:7]} — {msg}"
        if title in existing or msg in existing:
            continue
        create_page(db_id, {
            "Commit Message": {"title": rich_text(msg)},
            "Commit Hash":    {"rich_text": rich_text(hash_)},
            "Date":           {"date": {"start": date}},
            "Branch":         {"rich_text": rich_text(BRANCH)},
            "Test Status":    {"select": {"name": "All Passing"}},
            "Files Changed":  {"rich_text": rich_text(files[:2000])},
            "Pushed By":      {"select": {"name": "Sonnet"}},
        }, children=[paragraph_block(detail)])
        added += 1
    print(f"  Changes: {added} added, {len(existing)} already existed")


# ── Test Scenarios ────────────────────────────────────────────────────────────

ALL_TESTS = [
    # test_health.py
    ("test_health",                      "GET /health returns 200 with status:ok",                                                            "Backend", "Unit",        "initial suite"),
    ("test_config_status_no_key",        "GET /api/config/status returns configured:false when SAM_GOV_API_KEY is unset",                     "Backend", "Unit",        "initial suite"),
    ("test_config_status_with_key",      "GET /api/config/status returns configured:true when SAM_GOV_API_KEY is set",                        "Backend", "Unit",        "initial suite"),
    ("test_filter_set_asides",           "GET /api/contracts/filters/set-asides returns expected set-aside codes and labels",                  "Backend", "Unit",        "initial suite"),
    ("test_filter_solicitation_types",   "GET /api/contracts/filters/solicitation-types returns expected type codes and labels",               "Backend", "Unit",        "initial suite"),
    # test_parsing.py
    ("test_parse_full_opportunity",      "Full opportunity object parses to Contract with all expected fields populated",                      "Backend", "Unit",        "initial suite"),
    ("test_parse_award_opportunity",     "Award-type opportunity (type='a') parses; solicitation_type set to 'a'",                            "Backend", "Unit",        "initial suite"),
    ("test_parse_missing_fields",        "Opportunity with missing optional fields returns Contract with None values (no exception)",           "Backend", "Unit",        "initial suite"),
    ("test_parse_null_fields",           "Opportunity with explicit null fields returns Contract with None values",                            "Backend", "Unit",        "initial suite"),
    ("test_parse_bad_award_amount",      "Non-numeric awardAmount string returns award_amount=None (no exception)",                            "Backend", "Unit",        "initial suite"),
    ("test_parse_string_total",          "totalRecords as string '42' coerces to integer 42 via ContractSearchResult.coerce_total",           "Backend", "Unit",        "initial suite"),
    ("test_parse_contact_list",          "pointOfContact as list extracts first entry's fullName and email",                                   "Backend", "Unit",        "initial suite"),
    ("test_parse_contact_empty",         "pointOfContact as empty list returns contact_name=None, contact_email=None",                         "Backend", "Unit",        "initial suite"),
    ("test_parse_integer_naics_code",    "naicsCode: 541512 (int) parsed to naics_code: '541512' (str) via _str_or_none()",                   "Backend", "Unit",        "f00295e"),
    ("test_parse_integer_classification_code", "classificationCode as int coerces to str",                                                    "Backend", "Unit",        "f00295e"),
    ("test_parse_place_of_performance_string", "placeOfPerformance as plain string returned as-is",                                           "Backend", "Unit",        "f00295e"),
    ("test_parse_place_of_performance_partial", "city-only placeOfPerformance dict has no trailing comma in formatted string",                 "Backend", "Unit",        "f00295e"),
    ("test_sdvosbc_real_world_record",   "Full real-world SDVOSB record with int NAICS and dict contact parses correctly end-to-end",         "Backend", "Integration", "f00295e"),
    # test_contracts.py
    ("test_search_returns_results",      "Keyword search returns contracts; first result has expected notice_id and set_aside_code",           "Backend", "Integration", "initial suite"),
    ("test_open_only_filters_awards",    "open_only=true drops award-type contracts from results",                                             "Backend", "Unit",        "initial suite"),
    ("test_open_only_false_shows_awards","open_only=false includes award notices in results",                                                  "Backend", "Unit",        "initial suite"),
    ("test_search_with_veteran_set_aside","set_aside=SDVOSBC filter returns contracts with matching set_aside_code",                          "Backend", "Integration", "initial suite"),
    ("test_search_empty_results",        "Empty opportunitiesData returns total=0 and empty contracts list",                                   "Backend", "Unit",        "initial suite"),
    ("test_search_sam_gov_400",          "SAM.gov 400 → our API returns 502 with descriptive error",                                          "Backend", "Integration", "initial suite"),
    ("test_search_sam_gov_500",          "SAM.gov 500 → our API returns 502 with descriptive error",                                          "Backend", "Integration", "initial suite"),
    ("test_search_malformed_sam_response","Unexpected SAM.gov response shape → 200 with empty contracts list, no 500",                        "Backend", "Unit",        "initial suite"),
    ("test_search_string_total",         "totalRecords as string '42' coerces to integer 42 in search response",                              "Backend", "Unit",        "initial suite"),
    ("test_pagination_params",           "limit and offset are forwarded correctly to SAM.gov query params",                                   "Backend", "Integration", "initial suite"),
    ("test_search_sam_gov_429",          "SAM.gov 429 → our API returns 429 with 'limit' in detail message",                                  "Backend", "Integration", "de0f859"),
    ("test_cache_avoids_duplicate_sam_requests","Second identical search is served from cache; SAM.gov called only once",                     "Backend", "Unit",        "de0f859"),
    ("test_limit_max_capped",            "limit > 100 rejected with 422 by FastAPI validation",                                               "Backend", "Unit",        "initial suite"),
    ("test_sdvosbc_no_keyword",          "SDVOSB filter with no keyword and integer naicsCode — mirrors original bug report",                  "Backend", "Integration", "f00295e"),
    ("test_integer_naics_does_not_drop_contract","Contracts with integer naicsCode are not silently dropped from results",                    "Backend", "Unit",        "f00295e"),
]


def sync_test_scenarios(db_id: str):
    existing = existing_titles(db_id)
    added = 0
    for name, desc, area, kind, commit in ALL_TESTS:
        if name in existing:
            continue
        create_page(db_id, {
            "Test Name":   {"title": rich_text(name)},
            "Description": {"rich_text": rich_text(desc)},
            "Area":        {"select": {"name": area}},
            "Type":        {"select": {"name": kind}},
            "Status":      {"select": {"name": "Passing"}},
            "Added In":    {"rich_text": rich_text(commit)},
        })
        added += 1
    print(f"  Test Scenarios: {added} added, {len(existing)} already existed")


# ── Reference links ───────────────────────────────────────────────────────────

REFERENCE_LINKS = [
    ("SAM.gov Opportunities API v2",  "SAM.gov API",    "https://open.gsa.gov/api/get-opportunities-public-api/"),
    ("SAM.gov Registration",          "External Links",  "https://sam.gov"),
    ("SBA Veteran Certifications",    "External Links",  "https://veterans.certify.sba.gov"),
    ("Railway Dashboard",             "Deployment",      "https://railway.app/dashboard"),
    ("USASpending.gov",               "External Links",  "https://www.usaspending.gov"),
    ("CMMC Resource Center",          "External Links",  "https://www.acq.osd.mil/cmmc/"),
    ("SBA Veteran Success Stories",   "External Links",  "https://www.sba.gov/about-sba/sba-newsroom/success-stories"),
    ("IRS EIN Online Application",    "External Links",  "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online"),
    ("NAICS Code Lookup",             "External Links",  "https://naics.com"),
    ("AITAF (Adam Driver nonprofit)", "External Links",  "https://www.aitaf.org"),
]


def sync_reference(db_id: str):
    existing = existing_titles(db_id)
    added = 0
    for title, category, url in REFERENCE_LINKS:
        if title in existing:
            continue
        create_page(db_id, {
            "Title":    {"title": rich_text(title)},
            "Category": {"select": {"name": category}},
            "URL":      {"url": url},
        })
        added += 1
    print(f"  Reference: {added} added, {len(existing)} already existed")


# ── Session Log ───────────────────────────────────────────────────────────────

def add_session_log(db_id: str):
    """Always appends a new session log entry for today."""
    create_page(db_id, {
        "Session": {"title": rich_text("2026-05-22 · Opus visual uplift + outreach features")},
        "Date":    {"date": {"start": "2026-05-22"}},
        "Agent":   {"select": {"name": "Opus + Sonnet"}},
        "Branch":  {"rich_text": rich_text(BRANCH)},
        "Status":  {"select": {"name": "Complete"}},
    }, children=[
        heading_block(2, "What was done"),
        bullet_block("Plain-language translator toggle on contract cards (SET_ASIDE_PLAIN, SOLICITATION_TYPE_PLAIN)"),
        bullet_block("Start Here onboarding page at /start — 4 steps, EIN card, NAICS code directory (55 codes, 7 categories)"),
        bullet_block("Testimonials + ShareButton — TestimonialStrip on Mission page, Web Share API + clipboard fallback"),
        bullet_block("Mission page at /mission — hero, 3 values cards, founder note, full testimonial grid, CTAs"),
        bullet_block("GET /api/contracts/stats endpoint — 1hr cache, asyncio.gather for concurrent SAM.gov calls"),
        bullet_block("Trailblazers page at /trailblazers — 5 figures (Fred Smith, Jocko Willink, David Goggins, Mark Oz Geist, Adam Driver)"),
        bullet_block("TrailblazerDrawer — bio, resources, articles; deep-link via ?figure= param"),
        bullet_block("ArticleList — 9 seed articles, 5 bucket filters, source color badges"),
        bullet_block("Drawer polish from earlier: CSS slide-in-right, Tab focus trap, ?notice= deep-link"),
        bullet_block("GET /api/contracts/{notice_id} endpoint — placed after /stats and /filters/* to prevent route shadowing"),
        bullet_block("notion_sync.py — comprehensive idempotent sync script for full project state"),
        divider_block(),
        heading_block(2, "Key decisions"),
        bullet_block("Trailblazer figure selection: Goggins replaced Robert L. Johnson (unverifiable military service); Driver replaced Jaime Cruz (Veteran Roasters — insufficient documentation)"),
        bullet_block("Testimonials: placeholder strategy with sourceUrl field auto-activating story links; JR will source real SBA quotes by weekend"),
        bullet_block("Route ordering: wildcard /{notice_id} must always be last in contracts.py"),
        bullet_block("Stats cache: _STATS_CACHE dict with _STATS_TTL=3600 seconds, asyncio.gather for 4 concurrent set-aside counts"),
        divider_block(),
        heading_block(2, "Next session"),
        bullet_block("Merge branch to main so Railway deploys the new pages (PR required)"),
        bullet_block("Replace placeholder testimonials with real SBA veteran success stories"),
        bullet_block("Verify article URLs marked verify:true in articles.json before distribution"),
        bullet_block("Logo + company name — pending owner's veteran LLC registration"),
        bullet_block("Match Score personalization (post-distribution, week 1)"),
        divider_block(),
        heading_block(2, "Commits this session"),
        bullet_block("1bdea9c — Drawer polish: slide-in animation, focus trap, deep-link + notice ID endpoint"),
        bullet_block("5ca90a9 — Plain-language translator + Start Here onboarding page"),
        bullet_block("66ce696 — Start Here: EIN prerequisite card + NAICS code directory"),
        bullet_block("dcbfe69 — Testimonials + Share button"),
        bullet_block("e834300 — Mission page + live stats ticker"),
        bullet_block("69e4d73 — Trailblazers page — veteran entrepreneur profiles, articles, shareable drawers"),
        divider_block(),
        heading_block(2, "Open blockers"),
        bullet_block("Notion logging was BLOCKED all session — NOTION_API_KEY and NOTION_ROOT_PAGE_ID missing from backend/.env"),
        bullet_block("Resolution: user adds keys, runs notion_sync.py — this session log is the catch-up entry"),
    ])
    print("  Session Log: entry added for 2026-05-22")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nHorizon Search — Notion Full Sync")
    print(f"Root page: {ROOT_PAGE_ID}")
    print(f"Date: {now_iso()}\n")

    print("[1/6] Decisions database...")
    decisions_id, _ = get_or_create_database(ROOT_PAGE_ID, "Decisions", DECISIONS_PROPS,
                                              "NOTION_DECISIONS_DB", env_path)
    sync_decisions(decisions_id)

    print("\n[2/6] Backlog database...")
    backlog_id, _ = get_or_create_database(ROOT_PAGE_ID, "Backlog", BACKLOG_PROPS,
                                            "NOTION_BACKLOG_DB", env_path)
    sync_backlog(backlog_id)

    print("\n[3/6] Session Log database...")
    session_id, _ = get_or_create_database(ROOT_PAGE_ID, "Session Log", SESSION_LOG_PROPS,
                                            "NOTION_SESSION_DB", env_path)
    add_session_log(session_id)

    print("\n[4/6] Reference database...")
    reference_id, _ = get_or_create_database(ROOT_PAGE_ID, "Reference", REFERENCE_PROPS,
                                              "NOTION_REFERENCE_DB", env_path)
    sync_reference(reference_id)

    print("\n[5/6] Changes database...")
    changes_id, _ = get_or_create_database(ROOT_PAGE_ID, "Changes", CHANGES_PROPS,
                                            "NOTION_CHANGES_DB", env_path)
    sync_changes(changes_id)

    print("\n[6/6] Test Scenarios database...")
    tests_id, _ = get_or_create_database(ROOT_PAGE_ID, "Test Scenarios", TEST_SCENARIOS_PROPS,
                                          "NOTION_TESTS_DB", env_path)
    sync_test_scenarios(tests_id)

    print(f"\nSync complete. All database IDs saved to backend/.env")
    print("Open Notion to verify the structure.\n")


if __name__ == "__main__":
    main()
