#!/usr/bin/env python3
"""
C-Transit -- RSS intake agent.

Fetches SBA-related RSS, normalizes entries, writes to
research/data/inbox/<source>_<YYYY-MM-DD>.jsonl.

One record per entry: {title, url, body, source, fetched_at}

Primary feed: SBA Blog (https://www.sba.gov/blog/feed)
Fallback:     Federal Register SBA documents RSS (used if primary returns non-200)
              -- SBA removed their blog RSS; FR covers SBA regulatory notices.

Usage:
    python scripts/transit_fetch_feeds.py
    python scripts/transit_fetch_feeds.py --limit 5
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx

HERE       = Path(__file__).resolve().parent.parent   # repo root
INBOX_DIR  = HERE / "research" / "data" / "inbox"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402

SBA_PRIMARY_URL = "https://www.sba.gov/blog/feed"
SBA_FALLBACK_URL = (
    "https://www.federalregister.gov/api/v1/documents.rss"
    "?conditions[agencies][]=small-business-administration&per_page=20"
)
SOURCE_NAME = "sba"


def _fetch_raw_text(url: str) -> tuple[str, int]:
    """Return (raw_text, status_code) for a URL using httpx."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        resp = client.get(url)
        return resp.text, resp.status_code


def fetch_entries(limit: int) -> tuple[list[dict], list[str]]:
    """Fetch SBA RSS entries. Returns (records, errors)."""
    errors: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    # Try primary URL
    raw, status = _fetch_raw_text(SBA_PRIMARY_URL)
    feed = feedparser.parse(raw)

    if status != 200 or not feed.entries:
        errors.append(
            f"Primary SBA RSS returned status={status} with {len(feed.entries)} entries. "
            f"Falling back to Federal Register SBA feed."
        )
        print(f"  [WARN] {errors[-1]}")
        raw, status = _fetch_raw_text(SBA_FALLBACK_URL)
        feed = feedparser.parse(raw)
        if not feed.entries:
            errors.append(f"Fallback feed also returned 0 entries (status={status}).")
            return [], errors

    entries = feed.entries[:limit]
    records = []

    for entry in entries:
        body = ""
        if hasattr(entry, "summary"):
            body = entry.summary or ""
        if hasattr(entry, "content") and entry.content:
            body = entry.content[0].get("value", body)

        records.append({
            "title":      entry.get("title", "").strip(),
            "url":        entry.get("link", "").strip(),
            "body":       body.strip(),
            "source":     SOURCE_NAME,
            "fetched_at": now,
        })

    return records, errors


def write_inbox(records: list[dict], source: str) -> Path:
    """Write records to dated JSONL in inbox dir. Returns output path."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = INBOX_DIR / f"{source}_{date_str}.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="C-Transit: fetch SBA RSS feed")
    parser.add_argument(
        "--limit", type=int, default=20,
        help="Max entries to fetch (default: 20)",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    print(f"C-Transit: fetching SBA feed (limit={args.limit})")

    entries, errors = fetch_entries(args.limit)
    out_path = write_inbox(entries, SOURCE_NAME)
    print(f"  Wrote {len(entries)} records -> {out_path}")

    log_run("c-transit", started_at, record_count=len(entries), errors=errors or None)


if __name__ == "__main__":
    main()
