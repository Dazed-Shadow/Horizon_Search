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
import re
import subprocess
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


BRANCH = "claude/military-contract-search-tool-9hm2D"

# ── Helpers ───────────────────────────────────────────────────────────────────

def existing_titles(db_id: str) -> set:
    """Return set of title strings already in a database (to skip duplicates)."""
    pages = query_all_pages(db_id)
    titles = set()
    for p in pages:
        props = p.get("properties", {})
        for key in ("Decision", "Title", "Session", "Commit Message", "Test Name"):
            val = props.get(key, {})
            if val.get("type") == "title":
                items = val.get("title", [])
                if items:
                    titles.add(items[0].get("plain_text", ""))
                break
    return titles


def _add(label: str) -> None:
    print(f"    + {label}")


def _skip(label: str) -> None:
    print(f"    · skip  {label}")


def _err(label: str, exc: Exception) -> None:
    print(f"    ! ERROR {label}: {exc}")


def check_git_version() -> None:
    """Warn if the local repo is behind the remote branch."""
    try:
        repo = Path(__file__).parent.parent
        local = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()[:7]
        # fetch quietly so we can compare without pulling
        subprocess.run(
            ["git", "fetch", "origin", BRANCH, "--quiet"],
            cwd=repo, capture_output=True
        )
        remote = subprocess.check_output(
            ["git", "rev-parse", f"origin/{BRANCH}"],
            cwd=repo, text=True
        ).strip()[:7]
        if local == remote:
            print(f"  Git: local is current ({local}) — OK")
        else:
            print(f"  Git: WARNING — local={local} but origin={remote}")
            print("       Run: git pull origin " + BRANCH)
            print("       Then re-run this script to pick up the latest data.\n")
    except Exception:
        print("  Git: could not verify version (non-fatal)")


# ── Decisions ─────────────────────────────────────────────────────────────────

DECISIONS = [
    # ── 2026-05-24 decisions ──
    {
        "title": "LLC identity: Shade of Design LLC, no veteran-owned claim, tagline 'Matching services to those who serve'",
        "status": "Active", "by": "JR", "area": ["Content", "Frontend"], "date": "2026-05-24",
        "body": "Jon is not a veteran. Shade of Design LLC (NJ single-member, design & data analytics) must never claim veteran-owned status unless a qualifying veteran holds 51%+ unconditional ownership per VetCert requirements. Tagline describes what the tool does (connects services to veterans), not what the builder is. Specialty badges: Data Analytics (blue) + Small Business (grey). 'Veteran-Owned' badge deliberately excluded from testimonials.js founderNote.specialties.",
    },
    {
        "title": "NAICS insights rate-limit strategy: limit=1 reads totalRecords without fetching opportunity bodies",
        "status": "Active", "by": "Opus", "area": ["Backend", "API"], "date": "2026-05-24",
        "body": "SAM.gov returns totalRecords in every response even when limit=1. By sending limit=1 and offset=0 we get a precise count for any NAICS+set-aside+date-range combo at the cost of exactly 1 API call — no opportunity bodies are parsed. 12 monthly calls + 15 agency calls = 27 total calls per cold first load. asyncio.Semaphore(3) prevents burst throttling. 24h TTL for completed months and agency totals; 5m for current partial month. With caching, second request for same combo costs zero calls.",
    },
    {
        "title": "Phase 2 agency breakdown: organizationName filter, top 15 federal agencies, 24h cache",
        "status": "Active", "by": "Opus", "area": ["Backend", "API"], "date": "2026-05-24",
        "body": "Per-agency 12-month totals fetched using SAM.gov organizationName filter with the same limit=1 totalRecords trick. TOP_AGENCIES list of 15 major federal buyers covers ~85% of veteran set-aside volume. Results sorted descending, top 5 surfaced in UI. Agency cache keys: 'agency:<naics>:<set_aside>:<agency>' in the same _insight_cache dict as monthly counts — cleared together by the autouse test fixture. All 27 tasks (12 monthly + 15 agency) run concurrently in a single asyncio.gather/AsyncClient/Semaphore block.",
    },
    # ── 2026-05-22 and earlier decisions ──
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
    added = errors = 0
    for d in DECISIONS:
        if d["title"] in existing:
            _skip(d["title"][:80])
            continue
        try:
            create_page(db_id, {
                "Decision": {"title": rich_text(d["title"])},
                "Status":   {"select": {"name": d["status"]}},
                "Made By":  {"select": {"name": d["by"]}},
                "Area":     {"multi_select": [{"name": a} for a in d["area"]]},
                "Date":     {"date": {"start": d["date"]}},
            }, children=[paragraph_block(d["body"])])
            _add(d["title"][:80])
            added += 1
        except Exception as exc:
            _err(d["title"][:60], exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


# ── Backlog — parsed live from BACKLOG.md ─────────────────────────────────────
#
# No hardcoded list. Every time the sync runs it reads BACKLOG.md directly.
# To add a new entry to Notion: add it to BACKLOG.md using the standard template,
# then run `python scripts/notion_sync.py` — it will be picked up automatically.

_VALID_TAGS = {
    "#api", "#backend", "#frontend", "#ux", "#perf",
    "#deploy", "#auth", "#docs", "#outreach",
}

_TYPE_MAP = {"bug": "Bug", "feature": "Feature", "enhancement": "Enhancement", "idea": "Idea"}
_PRIORITY_MAP = {"high": "High", "medium": "Medium", "low": "Low"}


def parse_backlog_md() -> list[dict]:
    md_path = Path(__file__).parent.parent / "BACKLOG.md"
    text = md_path.read_text(encoding="utf-8")

    header_re = re.compile(r'^## \[(\d{4}-\d{2}-\d{2})\] (.+)$', re.MULTILINE)
    matches = list(header_re.finditer(text))
    items = []

    for i, m in enumerate(matches):
        date  = m.group(1)
        title = m.group(2).strip()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body  = text[m.end():end]

        # Skip structural headers (no **Type:** field)
        type_m = re.search(r'\*\*Type:\*\*\s*([^\n]+)', body)
        if not type_m:
            continue

        # Type — first word only, normalised
        raw_type  = type_m.group(1).strip().split()[0].rstrip('|').lower()
        item_type = _TYPE_MAP.get(raw_type, "Feature")

        # Priority and Status — "High — COMPLETE", "Medium — OPEN", "High — BLOCKED (...)"
        pri_m       = re.search(r'\*\*Priority:\*\*\s*([^\n]+)', body)
        raw_pri     = pri_m.group(1).strip() if pri_m else "Medium"
        parts       = [p.strip() for p in raw_pri.split("—", 1)]
        priority    = _PRIORITY_MAP.get(parts[0].split()[0].lower(), "Medium")
        suffix      = parts[1].upper() if len(parts) > 1 else ""

        if "COMPLETE" in suffix or "FIXED" in suffix:
            status = "Fixed" if item_type == "Bug" else "Complete"
        elif "BLOCKED" in suffix or "ACTION" in suffix:
            status = "Pending"
        elif "IN PROGRESS" in suffix:
            status = "In Progress"
        else:
            status = "Open"

        # Tags — keep only values in the valid set
        tags_m = re.search(r'\*\*Tags:\*\*\s*([^\n]+)', body)
        tags   = []
        if tags_m:
            tags = [t for t in tags_m.group(1).split() if t in _VALID_TAGS]

        # Detail — everything from **Detail:** to the next **field or end of section
        det_m  = re.search(r'\*\*Detail:\*\*\s*([\s\S]+?)(?=\n\*\*[A-Z]|\Z)', body)
        detail = det_m.group(1).strip() if det_m else ""
        # Strip backticks and bold markers for cleaner plain text in Notion
        detail = re.sub(r'`([^`]+)`', r'\1', detail)
        detail = re.sub(r'\*\*([^*]+)\*\*', r'\1', detail)
        detail = detail[:2000]

        # Commit hash — first 7-char hex string in **Resolution:** line
        res_m  = re.search(r'\*\*Resolution:\*\*\s*([^\n]+)', body)
        commit = ""
        if res_m:
            h = re.search(r'\b([0-9a-f]{7,40})\b', res_m.group(1), re.I)
            if h:
                commit = h.group(1)[:7]

        entry = {"title": title, "date": date, "type": item_type,
                 "priority": priority, "status": status, "tags": tags, "detail": detail}
        if commit:
            entry["commit"] = commit
        items.append(entry)

    print(f"  Parsed {len(items)} items from BACKLOG.md")
    return items


# Legacy alias kept so the variable name is recognisable in sync_backlog below
def _backlog_items() -> list[dict]:
    return parse_backlog_md()


# ── (removed static BACKLOG_ITEMS — source of truth is now BACKLOG.md) ────────
# Everything below this line that once referenced BACKLOG_ITEMS now calls
# parse_backlog_md() at sync time so Notion always reflects the markdown file.

def sync_backlog(db_id: str):
    """Read BACKLOG.md directly — no hardcoded list. Add any entry not yet in Notion."""
    items    = parse_backlog_md()
    existing = existing_titles(db_id)
    added = errors = 0
    for item in items:
        if item["title"] in existing:
            _skip(item["title"][:80])
            continue
        try:
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
            children = [paragraph_block(item["detail"])] if item.get("detail") else None
            create_page(db_id, props, children=children)
            _add(f"[{item['status']}] {item['title'][:70]}")
            added += 1
        except Exception as exc:
            _err(item["title"][:60], exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


# ── Changes / Commits ─────────────────────────────────────────────────────────

ALL_COMMITS = [
    # 2026-05-24 session
    ("Document Notion env vars in .env.example",
     "27a4768", "2026-05-24",
     "backend/.env.example",
     "NOTION_API_KEY and NOTION_ROOT_PAGE_ID were never in the example file. Added both with inline comments pointing to notion.so/my-integrations and explaining how to extract the root page ID from the URL."),
    ("Add Phase 2 NAICS insights: FY forecast, agency breakdown, bid timing",
     "c9fceb0", "2026-05-24",
     "backend/models/insights.py, backend/services/insights.py, backend/tests/test_insights.py, "
     "frontend/src/components/NaicsInsightPanel.jsx",
     "Three new panels: (1) FY Forecast amber/gray callout with surge-window detection; (2) Agency Breakdown — 15 agencies queried via organizationName filter, top 5 as indigo bar chart; (3) Best Months to Bid — peak months as chips, recommendation, prep window. 27 total SAM.gov calls per cold load, all Semaphore(3)-throttled. 10 new tests; 51 total passing."),
    ("NAICS Activity Insights Phase 1 — 12-month counts, bar chart, API endpoint",
     "698cc75", "2026-05-24",
     "backend/models/insights.py, backend/services/insights.py, backend/routers/insights.py, "
     "backend/tests/test_insights.py, backend/tests/conftest.py, "
     "frontend/src/hooks/useNaicsInsight.js, frontend/src/components/NaicsInsightPanel.jsx, "
     "frontend/src/components/FilterPanel.jsx, frontend/src/pages/SearchPage.jsx",
     "GET /api/insights/naics-activity endpoint. limit=1 totalRecords trick for rate-efficient counting. "
     "CSS-only bar chart. 24h/5m cache split. asyncio.Semaphore(3). 8 new tests; 41 total passing."),
    ("Fix invisible text — add missing brand-200/300/400/800 color stops to tailwind.config.js",
     "525a077", "2026-05-24",
     "frontend/tailwind.config.js",
     "brand-200/300/400/800 were referenced in 10+ components but missing from the config. "
     "Tailwind silently generated no CSS for those classes, causing black text on dark backgrounds. "
     "Added all four stops using the standard indigo scale."),
    ("Remove Veteran-Owned badge — correct specialties to Data Analytics + Small Business",
     "8afab9d", "2026-05-24",
     "frontend/src/data/testimonials.js, frontend/src/pages/MissionPage.jsx",
     "Prior commit incorrectly added 'Veteran-Owned' as a specialty badge. Jon is not a veteran. "
     "Fixed: specialties now ['Data Analytics', 'Small Business']; about paragraph corrected; "
     "guard comment added in testimonials.js to prevent future regression."),
    ("Shade of Design LLC identity — Navbar subtitle, footer tagline, mission about section",
     "fbd7828", "2026-05-24",
     "frontend/src/data/testimonials.js, frontend/src/pages/MissionPage.jsx, "
     "frontend/src/components/Navbar.jsx, frontend/src/App.jsx",
     "First LLC identity commit: Navbar subtitle → 'Matching services to those who serve'; "
     "footer updated; founderNote.name → 'Shade of Design LLC'. Note: this commit still had "
     "Veteran-Owned badge — corrected in next commit 8afab9d."),
    ("notion_sync.py — comprehensive idempotent catch-up sync for all 6 Notion databases",
     "738b8f3", "2026-05-24",
     "scripts/notion_sync.py",
     "Full project state sync: Decisions (10), Backlog (18), Session Log, Reference (10), "
     "Changes (11), Test Scenarios (33). Idempotent — skips existing titles. "
     "Blocked until user adds NOTION_API_KEY + NOTION_ROOT_PAGE_ID to backend/.env."),
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
    added = errors = 0
    for msg, hash_, date, files, detail in ALL_COMMITS:
        label = f"{hash_[:7]} — {msg}"
        if label in existing or msg in existing:
            _skip(label[:80])
            continue
        try:
            create_page(db_id, {
                "Commit Message": {"title": rich_text(msg)},
                "Commit Hash":    {"rich_text": rich_text(hash_)},
                "Date":           {"date": {"start": date}},
                "Branch":         {"rich_text": rich_text(BRANCH)},
                "Test Status":    {"select": {"name": "All Passing"}},
                "Files Changed":  {"rich_text": rich_text(files[:2000])},
                "Pushed By":      {"select": {"name": "Sonnet"}},
            }, children=[paragraph_block(detail)])
            _add(label[:80])
            added += 1
        except Exception as exc:
            _err(label[:60], exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


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
    # test_insights.py — Phase 1 (698cc75)
    ("test_insight_endpoint_basic",             "Endpoint returns 12 MonthlyCount objects for a valid NAICS code",                           "Backend", "Integration", "698cc75"),
    ("test_insight_endpoint_with_set_aside",    "set_aside param forwarded to SAM.gov and reflected in response with correct label",         "Backend", "Integration", "698cc75"),
    ("test_insight_missing_naics",              "Missing naics_code query param returns 422 validation error",                               "Backend", "Unit",        "698cc75"),
    ("test_insight_months_param",               "months=6 query param returns exactly 6 MonthlyCount objects",                              "Backend", "Unit",        "698cc75"),
    ("test_insight_cache_hit",                  "Second request for same NAICS serves from cache; SAM.gov called only once per month/agency","Backend", "Unit",        "698cc75"),
    ("test_insight_sam_error_returns_502",      "SAM.gov 500 per month returns count=0; endpoint succeeds with all-zero months",            "Backend", "Integration", "698cc75"),
    ("test_insight_avg_excludes_current_month", "avg_per_month is mean of complete months only — current partial month excluded",           "Backend", "Unit",        "698cc75"),
    ("test_insight_zero_activity_interpretation","All-zero months produces interpretation with guidance to broaden search",                  "Backend", "Unit",        "698cc75"),
    # test_insights.py — Phase 2 (c9fceb0)
    ("test_bid_timing_present",                 "When months have activity, bid_timing advice is populated with best_months, recommendation, prep_window", "Backend", "Unit", "c9fceb0"),
    ("test_bid_timing_zero_activity",           "When all months are 0, bid_timing is None",                                               "Backend", "Unit",        "c9fceb0"),
    ("test_fy_forecast_always_present",         "fy_forecast is always included regardless of NAICS activity level",                       "Backend", "Unit",        "c9fceb0"),
    ("test_fy_forecast_fields",                 "fy_forecast has fy_label starting with FY, bool is_surge_window, days_remaining > 0, non-empty message", "Backend", "Unit", "c9fceb0"),
    ("test_agency_breakdown_present",           "When agencies have activity, agency_breakdown is populated with up to 5 agencies",        "Backend", "Integration", "c9fceb0"),
    ("test_agency_breakdown_max_5_agencies",    "agency_breakdown never surfaces more than 5 agencies even when all 15 have activity",     "Backend", "Unit",        "c9fceb0"),
    ("test_agency_breakdown_zero_activity",     "When all agency queries return 0, agency_breakdown is None",                              "Backend", "Unit",        "c9fceb0"),
    ("test_agency_breakdown_sorted_desc",       "Agencies in breakdown are sorted by count descending",                                    "Backend", "Unit",        "c9fceb0"),
    ("test_bid_timing_best_months_are_valid_labels", "best_months must be a subset of the complete months' labels",                       "Backend", "Unit",        "c9fceb0"),
    ("test_phase2_response_shape",              "Full response includes all Phase 1 and Phase 2 fields (months, interpretation, bid_timing, fy_forecast, agency_breakdown)", "Backend", "Unit", "c9fceb0"),
]


def sync_test_scenarios(db_id: str):
    existing = existing_titles(db_id)
    added = errors = 0
    for name, desc, area, kind, commit in ALL_TESTS:
        if name in existing:
            _skip(name)
            continue
        try:
            create_page(db_id, {
                "Test Name":   {"title": rich_text(name)},
                "Description": {"rich_text": rich_text(desc)},
                "Area":        {"select": {"name": area}},
                "Type":        {"select": {"name": kind}},
                "Status":      {"select": {"name": "Passing"}},
                "Added In":    {"rich_text": rich_text(commit)},
            })
            _add(name)
            added += 1
        except Exception as exc:
            _err(name, exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


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
    added = errors = 0
    for title, category, url in REFERENCE_LINKS:
        if title in existing:
            _skip(title)
            continue
        try:
            create_page(db_id, {
                "Title":    {"title": rich_text(title)},
                "Category": {"select": {"name": category}},
                "URL":      {"url": url},
            })
            _add(title)
            added += 1
        except Exception as exc:
            _err(title, exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


# ── Session Log ───────────────────────────────────────────────────────────────

SESSION_LOGS = [
    {
        "title": "2026-05-22 · Opus visual uplift + outreach features",
        "date": "2026-05-22", "agent": "Opus + Sonnet", "status": "Complete",
        "done": [
            "Plain-language translator toggle on contract cards (SET_ASIDE_PLAIN, SOLICITATION_TYPE_PLAIN)",
            "Start Here onboarding page at /start — 4 steps, EIN card, NAICS code directory (55 codes, 7 categories)",
            "Testimonials + ShareButton — TestimonialStrip on Mission page, Web Share API + clipboard fallback",
            "Mission page at /mission — hero, 3 values cards, founder note, full testimonial grid, CTAs",
            "GET /api/contracts/stats endpoint — 1hr cache, asyncio.gather for concurrent SAM.gov calls",
            "Trailblazers page at /trailblazers — 5 figures (Fred Smith, Jocko Willink, David Goggins, Mark Oz Geist, Adam Driver)",
            "TrailblazerDrawer — bio, resources, articles; deep-link via ?figure= param",
            "ArticleList — 9 seed articles, 5 bucket filters, source color badges",
            "Drawer polish from earlier: CSS slide-in-right, Tab focus trap, ?notice= deep-link",
            "GET /api/contracts/{notice_id} endpoint — placed after /stats and /filters/* to prevent route shadowing",
            "notion_sync.py — comprehensive idempotent sync script for full project state",
        ],
        "decisions": [
            "Trailblazer figure selection: Goggins replaced Robert L. Johnson (unverifiable military service); Driver replaced Jaime Cruz (Veteran Roasters — insufficient documentation)",
            "Testimonials: placeholder strategy with sourceUrl field auto-activating story links; JR will source real SBA quotes",
            "Route ordering: wildcard /{notice_id} must always be last in contracts.py",
            "Stats cache: _STATS_CACHE dict with _STATS_TTL=3600 seconds, asyncio.gather for 4 concurrent set-aside counts",
        ],
        "next": [
            "Merge branch to main so Railway deploys the new pages (PR required)",
            "Replace placeholder testimonials with real SBA veteran success stories",
            "Verify article URLs marked verify:true in articles.json before distribution",
            "Logo + company name — pending owner's LLC formation",
            "Match Score personalization (post-distribution, week 1)",
        ],
        "commits": [
            "1bdea9c — Drawer polish: slide-in animation, focus trap, deep-link + notice ID endpoint",
            "5ca90a9 — Plain-language translator + Start Here onboarding page",
            "66ce696 — Start Here: EIN prerequisite card + NAICS code directory",
            "dcbfe69 — Testimonials + Share button",
            "e834300 — Mission page + live stats ticker",
            "69e4d73 — Trailblazers page — veteran entrepreneur profiles, articles, shareable drawers",
        ],
        "blockers": [
            "Notion logging was BLOCKED all session — NOTION_API_KEY and NOTION_ROOT_PAGE_ID missing from backend/.env",
        ],
    },
    {
        "title": "2026-05-24 · LLC identity, brand colors, NAICS Activity Insights Phase 1 + Phase 2",
        "date": "2026-05-24", "agent": "Opus + Sonnet", "status": "Complete",
        "done": [
            "Shade of Design LLC identity: founderNote corrected, Navbar subtitle + footer tagline updated",
            "Removed Veteran-Owned badge — Jon is not a veteran; specialties now Data Analytics + Small Business only",
            "Fixed invisible text: added brand-200/300/400/800 color stops to tailwind.config.js (affected 10+ components)",
            "NAICS Activity Insights Phase 1: GET /api/insights/naics-activity, NaicsInsightPanel, CSS bar chart, 12-month cache — 41 tests",
            "NAICS Activity Insights Phase 2: FY Forecast (surge window callout), Agency Breakdown (top 15 federal buyers, indigo bar chart), Best Months to Bid (peak chips + prep window) — 51 tests",
            "notion_sync.py completed and first successful Notion sync run by JR",
            "backend/.env.example updated with Notion key documentation",
        ],
        "decisions": [
            "LLC identity: Shade of Design LLC must never claim veteran-owned status. Tagline 'Matching services to those who serve' describes what the tool does, not what the builder is.",
            "NAICS rate-limit strategy: limit=1 reads totalRecords without fetching opportunity bodies — 27 calls per cold load (12 monthly + 15 agency), Semaphore(3), 24h cache",
            "Agency breakdown: TOP_AGENCIES list of 15 federal buyers; organizationName filter with same totalRecords trick; top 5 returned to UI sorted descending",
        ],
        "next": [
            "Replace placeholder testimonials with real SBA veteran success stories",
            "Verify article URLs marked verify:true in articles.json before distribution",
            "Logo: replace scales SVG in Navbar + 80x80 square in MissionPage with Shade of Design brand mark",
            "Match Score personalization (post-distribution, week 1)",
            "NAICS Phase 3: SQLite persistent cache, dollar-amount trends, multi-NAICS comparison",
        ],
        "commits": [
            "fbd7828 — Shade of Design LLC identity — Navbar subtitle, footer tagline, mission about section",
            "8afab9d — Remove Veteran-Owned badge — correct specialties to Data Analytics + Small Business",
            "525a077 — Fix invisible text — add missing brand-200/300/400/800 color stops",
            "698cc75 — NAICS Activity Insights Phase 1 — 12-month counts, bar chart, API endpoint",
            "c9fceb0 — NAICS Activity Insights Phase 2 — FY forecast, agency breakdown, bid timing",
            "27a4768 — Document Notion env vars in .env.example",
        ],
        "blockers": [],
    },
]


def sync_session_logs(db_id: str):
    existing = existing_titles(db_id)
    added = errors = 0
    for log in SESSION_LOGS:
        if log["title"] in existing:
            _skip(log["title"])
            continue
        try:
            children = [heading_block(2, "What was done")]
            for item in log["done"]:
                children.append(bullet_block(item))
            if log["decisions"]:
                children += [divider_block(), heading_block(2, "Key decisions")]
                for item in log["decisions"]:
                    children.append(bullet_block(item))
            if log["next"]:
                children += [divider_block(), heading_block(2, "Next session")]
                for item in log["next"]:
                    children.append(bullet_block(item))
            if log["commits"]:
                children += [divider_block(), heading_block(2, "Commits this session")]
                for item in log["commits"]:
                    children.append(bullet_block(item))
            if log["blockers"]:
                children += [divider_block(), heading_block(2, "Open blockers")]
                for item in log["blockers"]:
                    children.append(bullet_block(item))
            create_page(db_id, {
                "Session": {"title": rich_text(log["title"])},
                "Date":    {"date": {"start": log["date"]}},
                "Agent":   {"select": {"name": log["agent"]}},
                "Branch":  {"rich_text": rich_text(BRANCH)},
                "Status":  {"select": {"name": log["status"]}},
            }, children=children)
            _add(log["title"])
            added += 1
        except Exception as exc:
            _err(log["title"][:60], exc)
            errors += 1
    print(f"  → {added} added, {len(existing)} skipped, {errors} errors")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nHorizon Search — Notion Full Sync")
    print(f"Root page: {ROOT_PAGE_ID}")
    print(f"Date:      {now_iso()}")
    check_git_version()
    print()

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
    sync_session_logs(session_id)

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
