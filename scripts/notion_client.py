"""
Notion API client for PROJECT-HORIZON_SEARCH.
Handles all reads/writes to the project's Notion workspace.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _api_key() -> str:
    key = os.getenv("NOTION_API_KEY")
    if not key:
        raise RuntimeError("NOTION_API_KEY not set. Add it to your .env file.")
    return key


def _request(method: str, path: str, body: Optional[dict] = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        raise RuntimeError(f"Notion API {e.code}: {body_text}") from e


def get_page(page_id: str) -> dict:
    return _request("GET", f"/pages/{page_id.replace('-', '')}")


def create_database(parent_page_id: str, title: str, properties: dict) -> dict:
    return _request("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    })


def create_page(database_id: str, properties: dict, children: Optional[list] = None) -> dict:
    body = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    if children:
        body["children"] = children
    return _request("POST", "/pages", body)


def update_page(page_id: str, properties: dict) -> dict:
    return _request("PATCH", f"/pages/{page_id}", {"properties": properties})


def query_database(database_id: str, filter_body: Optional[dict] = None) -> list:
    body = {}
    if filter_body:
        body["filter"] = filter_body
    result = _request("POST", f"/databases/{database_id}/query", body)
    return result.get("results", [])


def query_all_pages(database_id: str) -> list:
    """Paginate through all records in a database."""
    pages = []
    cursor = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        result = _request("POST", f"/databases/{database_id}/query", body)
        pages.extend(result.get("results", []))
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
    return pages


def append_blocks(page_id: str, children: list) -> dict:
    return _request("PATCH", f"/blocks/{page_id}/children", {"children": children})


# ── Safety primitives ─────────────────────────────────────────────────────────

def database_exists(db_id: str) -> bool:
    """Return True if the database exists in Notion and is not archived."""
    if not db_id:
        return False
    try:
        result = _request("GET", f"/databases/{db_id.replace('-', '')}")
        return not result.get("archived", False)
    except RuntimeError:
        return False


def update_env_key(env_file: Path, key: str, value: str) -> None:
    """Write or update a single key in a .env file without creating duplicates."""
    lines = env_file.read_text().splitlines() if env_file.exists() else []
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped == key:
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    env_file.write_text("\n".join(new_lines) + "\n")


def get_or_create_database(
    parent_page_id: str,
    title: str,
    properties: dict,
    env_key: str,
    env_file: Path,
) -> tuple[str, bool]:
    """
    Return (database_id, was_created).

    If env_key is already set and the database is alive in Notion,
    returns the existing ID and was_created=False — no API write occurs.
    If the ID is missing or the database was deleted, creates a fresh one,
    saves the ID to env_file, and returns was_created=True.
    """
    existing_id = os.getenv(env_key, "").replace("-", "")
    if existing_id and database_exists(existing_id):
        print(f"  ↳ '{title}' already exists — skipping creation")
        return existing_id, False

    if existing_id:
        print(f"  ↳ '{title}' ID found in .env but not in Notion — recreating")

    db = create_database(parent_page_id, title, properties)
    db_id = db["id"]
    update_env_key(env_file, env_key, db_id)
    os.environ[env_key] = db_id
    return db_id, True


# ── Convenience helpers ───────────────────────────────────────────────────────

def rich_text(content: str) -> list:
    return [{"type": "text", "text": {"content": content}}]


def heading_block(level: int, content: str) -> dict:
    tag = f"heading_{level}"
    return {tag: {"rich_text": rich_text(content)}, "type": tag}


def paragraph_block(content: str) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": rich_text(content)}}


def bullet_block(content: str) -> dict:
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich_text(content)}}


def divider_block() -> dict:
    return {"type": "divider", "divider": {}}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
