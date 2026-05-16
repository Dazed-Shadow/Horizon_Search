"""
One-time setup: creates the PROJECT-HORIZON_SEARCH Notion workspace structure.

Before running:
  1. In Notion, open the page you want as the project root
  2. Click ••• → Connections → search "MR_C-HANDS" → Connect
  3. Copy the page URL and paste the page ID below (or pass as argument)
  4. Add NOTION_API_KEY to your .env file
  5. Run: python scripts/notion_setup.py

The script creates four databases as child pages:
  - Decisions     — architecture choices and Opus guidance
  - Backlog       — features, bugs, enhancements (mirrors BACKLOG.md)
  - Session Log   — per-session notes, what was done and what's next
  - Reference     — SAM.gov quirks, deployment notes, external docs
"""
import os
import sys
import json
from pathlib import Path

# Load .env from backend directory
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from notion_client import (
    create_database, create_page, rich_text,
    paragraph_block, heading_block, bullet_block, divider_block, now_iso,
)

# ── Page ID ──────────────────────────────────────────────────────────────────
# Extract from your Notion page URL:
# https://www.notion.so/Page-Title-{PAGE_ID}?...
# Paste the 32-char hex ID here (no dashes needed):
ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID", "")

if not ROOT_PAGE_ID:
    if len(sys.argv) > 1:
        ROOT_PAGE_ID = sys.argv[1].replace("-", "")
    else:
        print("Usage: python notion_setup.py <root-page-id>")
        print("       or set NOTION_ROOT_PAGE_ID in .env")
        sys.exit(1)

ROOT_PAGE_ID = ROOT_PAGE_ID.replace("-", "")


# ── Database schemas ─────────────────────────────────────────────────────────

DECISIONS_PROPS = {
    "Decision": {"title": {}},
    "Status": {"select": {"options": [
        {"name": "Active",    "color": "green"},
        {"name": "Superseded","color": "yellow"},
        {"name": "Pending",   "color": "gray"},
    ]}},
    "Made By": {"select": {"options": [
        {"name": "Opus",   "color": "purple"},
        {"name": "Sonnet", "color": "blue"},
        {"name": "JR",     "color": "orange"},
    ]}},
    "Area": {"multi_select": {"options": [
        {"name": "Architecture","color": "red"},
        {"name": "Frontend",    "color": "blue"},
        {"name": "Backend",     "color": "green"},
        {"name": "Deploy",      "color": "yellow"},
        {"name": "UX",          "color": "pink"},
        {"name": "API",         "color": "purple"},
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
        {"name": "Open",       "color": "red"},
        {"name": "In Progress","color": "yellow"},
        {"name": "Fixed",      "color": "green"},
        {"name": "Pending",    "color": "gray"},
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
        {"name": "Complete",   "color": "green"},
        {"name": "In Progress","color": "yellow"},
        {"name": "Blocked",    "color": "red"},
    ]}},
}

REFERENCE_PROPS = {
    "Title": {"title": {}},
    "Category": {"select": {"options": [
        {"name": "SAM.gov API",    "color": "blue"},
        {"name": "Deployment",     "color": "green"},
        {"name": "Architecture",   "color": "purple"},
        {"name": "External Links", "color": "orange"},
        {"name": "Credentials",    "color": "red"},
    ]}},
    "URL": {"url": {}},
}


def seed_backlog(db_id: str):
    """Populate Backlog DB with the current open items."""
    items = [
        {
            "title": "Contract detail drawer/modal",
            "type": "Feature", "priority": "High", "status": "Open",
            "tags": ["#frontend", "#ux"],
        },
        {
            "title": "NAICS code discovery helper",
            "type": "Feature", "priority": "High", "status": "Open",
            "tags": ["#frontend", "#ux"],
        },
        {
            "title": "Deadline urgency indicators on cards",
            "type": "Enhancement", "priority": "High", "status": "Open",
            "tags": ["#frontend", "#ux"],
        },
        {
            "title": "Sort controls (deadline, posted date, value)",
            "type": "Enhancement", "priority": "High", "status": "Open",
            "tags": ["#frontend", "#ux"],
        },
        {
            "title": "VSB code may not match SAM.gov VOSB parameter",
            "type": "Bug", "priority": "Medium", "status": "Open",
            "tags": ["#api", "#frontend"],
        },
        {
            "title": "Saved searches (localStorage)",
            "type": "Feature", "priority": "Medium", "status": "Open",
            "tags": ["#frontend"],
        },
        {
            "title": "Bookmark / watch list",
            "type": "Feature", "priority": "Medium", "status": "Open",
            "tags": ["#frontend"],
        },
        {
            "title": "Contract value filter (floor/ceiling)",
            "type": "Feature", "priority": "Medium", "status": "Open",
            "tags": ["#frontend", "#api"],
        },
        {
            "title": "Email digest for saved searches",
            "type": "Feature", "priority": "Low", "status": "Open",
            "tags": ["#auth", "#backend"],
        },
        {
            "title": "Teaming board for veteran-owned businesses",
            "type": "Feature", "priority": "Low", "status": "Open",
            "tags": ["#auth", "#backend", "#frontend"],
        },
    ]
    for item in items:
        create_page(db_id, {
            "Title":    {"title": rich_text(item["title"])},
            "Type":     {"select": {"name": item["type"]}},
            "Priority": {"select": {"name": item["priority"]}},
            "Status":   {"select": {"name": item["status"]}},
            "Tags":     {"multi_select": [{"name": t} for t in item["tags"]]},
            "Date":     {"date": {"start": now_iso()}},
        })
    print(f"  Seeded {len(items)} backlog items")


def seed_reference(db_id: str):
    links = [
        ("SAM.gov Opportunities API v2", "SAM.gov API", "https://open.gsa.gov/api/get-opportunities-public-api/"),
        ("SAM.gov Registration", "External Links", "https://sam.gov"),
        ("SBA Veteran Certifications", "External Links", "https://veterans.certify.sba.gov"),
        ("Railway Dashboard", "Deployment", "https://railway.app/dashboard"),
        ("USASpending.gov", "External Links", "https://www.usaspending.gov"),
        ("CMMC Resource Center", "External Links", "https://www.acq.osd.mil/cmmc/"),
    ]
    for title, category, url in links:
        create_page(db_id, {
            "Title":    {"title": rich_text(title)},
            "Category": {"select": {"name": category}},
            "URL":      {"url": url},
        })
    print(f"  Seeded {len(links)} reference links")


def seed_first_decision(db_id: str):
    create_page(db_id, {
        "Decision": {"title": rich_text("Railway for deployment — backend + frontend as separate services")},
        "Status":   {"select": {"name": "Active"}},
        "Made By":  {"select": {"name": "Sonnet"}},
        "Area":     {"multi_select": [{"name": "Deploy"}]},
        "Date":     {"date": {"start": "2026-05-16"}},
    }, children=[
        paragraph_block("Railway chosen over Render and Vercel+Railway split. Free tier avoids cold-start penalty that Render free tier has. Backend root: /backend, Frontend root: /frontend. CORS handled via CORS_ORIGINS env var. VITE_API_URL baked at build time."),
    ])
    print("  Seeded initial deployment decision")


def seed_first_session(db_id: str):
    create_page(db_id, {
        "Session": {"title": rich_text("2026-05-16 · Notion + Opus workflow setup")},
        "Date":    {"date": {"start": "2026-05-16"}},
        "Agent":   {"select": {"name": "Sonnet"}},
        "Branch":  {"rich_text": rich_text("claude/military-contract-search-tool-9hm2D")},
        "Status":  {"select": {"name": "Complete"}},
    }, children=[
        heading_block(2, "What was done"),
        bullet_block("Set up Notion workspace structure (this session log)"),
        bullet_block("Updated BACKLOG.md with entries from user's local copy"),
        bullet_block("Established Opus orchestrator + Notion workflow documented in CLAUDE.md"),
        divider_block(),
        heading_block(2, "Next session"),
        bullet_block("Contract detail drawer/modal (Session A item 1)"),
        bullet_block("NAICS code discovery helper (Session A item 2)"),
        bullet_block("Fix VSB → VOSB code in constants.js"),
    ])
    print("  Seeded first session log entry")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\nConnecting to Notion workspace...")
    print(f"Root page ID: {ROOT_PAGE_ID}\n")

    print("Creating Decisions database...")
    decisions_db = create_database(ROOT_PAGE_ID, "Decisions", DECISIONS_PROPS)
    decisions_id = decisions_db["id"]
    seed_first_decision(decisions_id)
    print(f"  ✓ Decisions DB: {decisions_id}\n")

    print("Creating Backlog database...")
    backlog_db = create_database(ROOT_PAGE_ID, "Backlog", BACKLOG_PROPS)
    backlog_id = backlog_db["id"]
    seed_backlog(backlog_id)
    print(f"  ✓ Backlog DB: {backlog_id}\n")

    print("Creating Session Log database...")
    session_db = create_database(ROOT_PAGE_ID, "Session Log", SESSION_LOG_PROPS)
    session_id = session_db["id"]
    seed_first_session(session_id)
    print(f"  ✓ Session Log DB: {session_id}\n")

    print("Creating Reference database...")
    reference_db = create_database(ROOT_PAGE_ID, "Reference", REFERENCE_PROPS)
    reference_id = reference_db["id"]
    seed_reference(reference_id)
    print(f"  ✓ Reference DB: {reference_id}\n")

    # Write DB IDs to .env for future use
    ids_block = (
        f"\n# Notion Database IDs (written by notion_setup.py)\n"
        f"NOTION_DECISIONS_DB={decisions_id}\n"
        f"NOTION_BACKLOG_DB={backlog_id}\n"
        f"NOTION_SESSION_DB={session_id}\n"
        f"NOTION_REFERENCE_DB={reference_id}\n"
    )
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    with open(env_file, "a") as f:
        f.write(ids_block)
    print(f"Database IDs appended to backend/.env\n")
    print("Setup complete. Open Notion to verify the structure.")


if __name__ == "__main__":
    main()
