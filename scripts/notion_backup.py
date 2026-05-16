"""
Exports all PROJECT-HORIZON_SEARCH Notion databases to a timestamped
JSON file in scripts/backups/.

Safe to run at any time — read-only, never writes to Notion.
Run before any destructive operation or on a regular schedule.

Usage:
  python scripts/notion_backup.py

Output:
  scripts/backups/backup_YYYY-MM-DD_HH-MM-SS.json

The backup file contains every page from every known database.
Restore guidance: if a database is accidentally deleted, re-run
notion_add_databases.py (it will recreate the empty shell) then
use the backup JSON to manually re-enter critical records, or
contact the project maintainer to build a restore script.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

ENV_FILE = Path(__file__).parent.parent / "backend" / ".env"
BACKUP_DIR = Path(__file__).parent / "backups"

# Load .env
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from notion_client import query_all_pages, database_exists

DATABASES = {
    "Decisions":     os.getenv("NOTION_DECISIONS_DB", ""),
    "Backlog":       os.getenv("NOTION_BACKLOG_DB", ""),
    "Session Log":   os.getenv("NOTION_SESSION_DB", ""),
    "Reference":     os.getenv("NOTION_REFERENCE_DB", ""),
    "Changes":       os.getenv("NOTION_CHANGES_DB", ""),
    "Test Scenarios":os.getenv("NOTION_TESTS_DB", ""),
}


def extract_title(page: dict) -> str:
    """Pull the plain-text title from any page regardless of property name."""
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return "".join(p.get("plain_text", "") for p in parts)
    return "(untitled)"


def main():
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}.json"

    backup = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "databases": {},
    }

    missing = [name for name, db_id in DATABASES.items() if not db_id]
    if missing:
        print(f"Warning: no ID found for: {', '.join(missing)}")
        print("These will be skipped. Run notion_setup.py or notion_add_databases.py first.\n")

    total_pages = 0
    for name, db_id in DATABASES.items():
        if not db_id:
            continue

        db_id_clean = db_id.replace("-", "")
        print(f"Backing up '{name}' ({db_id_clean[:8]}...)...", end=" ", flush=True)

        if not database_exists(db_id_clean):
            print("NOT FOUND in Notion — skipping")
            backup["databases"][name] = {"id": db_id_clean, "error": "database not found", "pages": []}
            continue

        try:
            pages = query_all_pages(db_id_clean)
            backup["databases"][name] = {
                "id": db_id_clean,
                "page_count": len(pages),
                "pages": pages,
            }
            total_pages += len(pages)
            print(f"{len(pages)} records")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            backup["databases"][name] = {"id": db_id_clean, "error": str(e), "pages": []}

    backup_path.write_text(json.dumps(backup, indent=2, default=str))

    print(f"\n✓ Backup complete")
    print(f"  File:    {backup_path}")
    print(f"  Records: {total_pages} pages across {len(DATABASES)} databases")

    # Keep only the 10 most recent backups to avoid unbounded growth
    all_backups = sorted(BACKUP_DIR.glob("backup_*.json"))
    if len(all_backups) > 10:
        for old in all_backups[:-10]:
            old.unlink()
            print(f"  Pruned old backup: {old.name}")


if __name__ == "__main__":
    main()
