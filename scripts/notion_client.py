"""
Notion API client for PROJECT-HORIZON_SEARCH.
Handles all reads/writes to the project's Notion workspace.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
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


def append_blocks(page_id: str, children: list) -> dict:
    return _request("PATCH", f"/blocks/{page_id}/children", {"children": children})


# ── Convenience helpers ──────────────────────────────────────────────────────

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
