"""
Adds the Changes and Test Scenarios databases to an existing
PROJECT-HORIZON_SEARCH Notion workspace.

Run this if you already ran notion_setup.py and just need the two new DBs.
It reads NOTION_ROOT_PAGE_ID from backend/.env (same as setup) and will NOT
touch any databases that already exist.

Usage:
  python scripts/notion_add_databases.py

Prerequisites:
  - NOTION_API_KEY in backend/.env
  - NOTION_ROOT_PAGE_ID in backend/.env
  - MR_C-HANDS integration connected to your root Notion page
"""
import os
import sys
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
    create_database, create_page, rich_text, paragraph_block,
)

ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID", "")
if not ROOT_PAGE_ID:
    print("ERROR: NOTION_ROOT_PAGE_ID not set in backend/.env")
    sys.exit(1)

ROOT_PAGE_ID = ROOT_PAGE_ID.replace("-", "")

# ── Database schemas ──────────────────────────────────────────────────────────

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

# ── Seed data ─────────────────────────────────────────────────────────────────

def seed_test_scenarios(db_id: str):
    tests = [
        ("test_search_returns_results",             "Keyword search returns contracts; first result has expected notice_id and set_aside_code",             "Backend", "Integration"),
        ("test_open_only_filters_awards",           "open_only=true drops award-type contracts from results",                                               "Backend", "Unit"),
        ("test_open_only_false_shows_awards",       "open_only=false includes award notices in results",                                                    "Backend", "Unit"),
        ("test_search_with_veteran_set_aside",      "set_aside=SDVOSBC filter returns contracts with matching set_aside_code",                              "Backend", "Integration"),
        ("test_search_empty_results",               "Empty opportunitiesData returns total=0 and empty contracts list",                                      "Backend", "Unit"),
        ("test_search_sam_gov_400",                 "SAM.gov 400 → our API returns 502",                                                                    "Backend", "Integration"),
        ("test_search_sam_gov_500",                 "SAM.gov 500 → our API returns 502",                                                                    "Backend", "Integration"),
        ("test_search_malformed_sam_response",      "Unexpected SAM.gov response shape → 200 with empty contracts, no 500",                                 "Backend", "Unit"),
        ("test_search_string_total",                "totalRecords as string '42' coerces to integer 42",                                                    "Backend", "Unit"),
        ("test_pagination_params",                  "limit and offset forwarded correctly to SAM.gov",                                                      "Backend", "Integration"),
        ("test_search_sam_gov_429",                 "SAM.gov 429 → our API returns 429 with 'limit' in detail message",                                     "Backend", "Integration"),
        ("test_cache_avoids_duplicate_sam_requests","Second identical search served from cache; SAM.gov called only once",                                   "Backend", "Unit"),
        ("test_limit_max_capped",                   "limit > 100 rejected with 422 by FastAPI validation",                                                  "Backend", "Unit"),
        ("test_sdvosbc_no_keyword",                 "SDVOSB filter with no keyword, integer naicsCode — mirrors original bug",                              "Backend", "Integration"),
        ("test_integer_naics_does_not_drop_contract","Contracts with integer naicsCode are not silently dropped",                                           "Backend", "Unit"),
        ("test_parse_integer_naics_code",           "naicsCode: 541512 (int) parsed to naics_code: '541512' (str)",                                        "Backend", "Unit"),
        ("test_parse_integer_classification_code",  "classificationCode as int coerces to str",                                                             "Backend", "Unit"),
        ("test_parse_place_of_performance_string",  "placeOfPerformance as plain string returned as-is",                                                   "Backend", "Unit"),
        ("test_parse_place_of_performance_partial", "city-only placeOfPerformance has no trailing comma",                                                   "Backend", "Unit"),
        ("test_sdvosbc_real_world_record",          "Full real-world SDVOSB record with int NAICS and dict contact parses correctly",                       "Backend", "Integration"),
    ]
    for name, desc, area, kind in tests:
        create_page(db_id, {
            "Test Name":   {"title": rich_text(name)},
            "Description": {"rich_text": rich_text(desc)},
            "Area":        {"select": {"name": area}},
            "Type":        {"select": {"name": kind}},
            "Status":      {"select": {"name": "Passing"}},
            "Added In":    {"rich_text": rich_text("initial suite")},
        })
    print(f"  Seeded {len(tests)} test scenarios")


def seed_changes(db_id: str):
    commits = [
        (
            "Add contract detail drawer with plain-English set-aside explainers",
            "7213481", "2026-05-17",
            "ContractDetailDrawer.jsx, LiveCountdown.jsx, explainers.js, ContractCard.jsx, ContractList.jsx, SearchPage.jsx, notion_setup.py, BACKLOG.md",
            "Right-side drawer with educational explainers for every set-aside and notice type. Fixes VOSB quick-link bug. Adds Changes + Test Scenarios to Notion setup.",
        ),
        (
            "Add Notion integration and Opus orchestrator workflow",
            "2550697", "2026-05-16",
            "scripts/notion_client.py, scripts/notion_setup.py, CLAUDE.md, BACKLOG.md",
            "Establishes Notion as project memory and Opus+Sonnet two-tier agent model.",
        ),
        (
            "Add Railway deployment config for backend and frontend",
            "0d0f3f0", "2026-05-16",
            "backend/Procfile, backend/railway.toml, frontend/railway.toml, frontend/src/hooks/useContracts.js",
            "Enables Railway to build and run both services. VITE_API_URL support for production API calls.",
        ),
        (
            "Add 'How to Win a Contract' primer page for veterans",
            "c232ef3", "2026-05-16",
            "frontend/src/pages/ContractPrimerPage.jsx, frontend/src/App.jsx, frontend/src/components/Navbar.jsx",
            "Six-section field guide for newcomers: set-asides, contracting lifecycle, proposal writing, teaming strategy.",
        ),
        (
            "Rate limiting: 5-min cache, 429 handling, amber UI state",
            "de0f859", "2026-05-10",
            "backend/services/sam_gov.py, backend/routers/contracts.py, frontend/src/components/ContractList.jsx, frontend/src/hooks/useContracts.js",
            "Prevents quota exhaustion. Friendly 'Search limit reached' message instead of confusing error.",
        ),
    ]
    for msg, hash_, date, files, detail in commits:
        create_page(db_id, {
            "Commit Message": {"title": rich_text(msg)},
            "Commit Hash":    {"rich_text": rich_text(hash_)},
            "Date":           {"date": {"start": date}},
            "Branch":         {"rich_text": rich_text("claude/military-contract-search-tool-9hm2D")},
            "Test Status":    {"select": {"name": "All Passing"}},
            "Files Changed":  {"rich_text": rich_text(files)},
            "Pushed By":      {"select": {"name": "Sonnet"}},
        }, children=[paragraph_block(detail)])
    print(f"  Seeded {len(commits)} commit entries")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nAdding new databases to existing Notion workspace...")
    print(f"Root page ID: {ROOT_PAGE_ID}\n")
    print("Existing databases (Decisions, Backlog, Session Log, Reference) are untouched.\n")

    print("Creating Changes database...")
    changes_db = create_database(ROOT_PAGE_ID, "Changes", CHANGES_PROPS)
    changes_id = changes_db["id"]
    seed_changes(changes_id)
    print(f"  ✓ Changes DB: {changes_id}\n")

    print("Creating Test Scenarios database...")
    tests_db = create_database(ROOT_PAGE_ID, "Test Scenarios", TEST_SCENARIOS_PROPS)
    tests_id = tests_db["id"]
    seed_test_scenarios(tests_id)
    print(f"  ✓ Test Scenarios DB: {tests_id}\n")

    # Append only the new IDs to .env
    ids_block = (
        f"\n# New Notion Database IDs (written by notion_add_databases.py)\n"
        f"NOTION_CHANGES_DB={changes_id}\n"
        f"NOTION_TESTS_DB={tests_id}\n"
    )
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    with open(env_file, "a") as f:
        f.write(ids_block)
    print(f"New database IDs appended to backend/.env")
    print("\nDone. Open Notion to verify the two new databases.")


if __name__ == "__main__":
    main()
