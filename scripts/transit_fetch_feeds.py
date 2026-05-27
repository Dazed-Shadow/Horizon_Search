#!/usr/bin/env python3
"""
C-Transit -- RSS intake agent.

Fetches SBA-related RSS, normalizes entries, writes to
research/data/inbox/<source>_<YYYY-MM-DD>.jsonl.

One record per entry: {title, url, body, source, fetched_at}

Primary feed: SBA Blog (https://www.sba.gov/blog/feed)
Fallback:     Federal Register SBA documents RSS (used if primary returns non-200)
              -- SBA removed their blog RSS; FR covers SBA regulatory notices.

Body extraction strategy:
  - Federal Register URLs (federalregister.gov): call the FR JSON API to get
    the raw_text_url, fetch that, strip HTML boilerplate with BeautifulSoup.
  - All other URLs: generic HTML extraction via BeautifulSoup, targeting
    <article> / <main> / <div.entry-content> with a text fallback.
  - Body is capped at MAX_BODY_CHARS (default 8000) to keep JSONL sizes sane.
  - Per-article fetch errors are logged per-record and set body=""; the run
    continues normally (fail-soft).

Usage:
    python scripts/transit_fetch_feeds.py
    python scripts/transit_fetch_feeds.py --limit 5
    python scripts/transit_fetch_feeds.py --limit 5 --body-delay 1.5
    python scripts/transit_fetch_feeds.py --no-body
    python scripts/transit_fetch_feeds.py --max-body-chars 4000
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx
from bs4 import BeautifulSoup

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

# Body extraction settings (overridable via CLI)
DEFAULT_MAX_BODY_CHARS = 8_000
DEFAULT_BODY_DELAY_S   = 1.0

# Regex to pull the document number from a Federal Register document URL.
# e.g. /documents/2026/05/22/2026-10339/some-title  ->  "2026-10339"
_FR_DOC_NUMBER_RE = re.compile(
    r"federalregister\.gov/documents/\d{4}/\d{2}/\d{2}/([^/?\s]+)"
)

_FR_API_TEMPLATE = "https://www.federalregister.gov/api/v1/documents/{doc_number}.json"

# HTML tags to strip from FR raw_text pages (they arrive as <html><pre>...)
_BOILERPLATE_STRIP_RE = re.compile(
    r"(\[Federal Register[^\]]*\]|\[FR Doc[^\]]*\]|BILLING CODE[^\n]*|={10,}|-{10,})"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _http_get(client: httpx.Client, url: str) -> tuple[str, int]:
    """GET url, return (text, status_code). Never raises — returns ("", 0) on error."""
    try:
        resp = client.get(url)
        return resp.text, resp.status_code
    except Exception as exc:  # noqa: BLE001
        return "", 0


def _fetch_raw_text(url: str) -> tuple[str, int]:
    """Return (raw_text, status_code) for a URL using a fresh httpx client."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        return _http_get(client, url)


def _extract_body_fr(
    url: str, client: httpx.Client, max_chars: int
) -> tuple[str, str | None]:
    """
    Fetch the body for a Federal Register document URL.

    Returns (body_text, error_str | None).
    Uses the FR JSON API to locate raw_text_url, then fetches and strips it.
    """
    m = _FR_DOC_NUMBER_RE.search(url)
    if not m:
        return "", f"Could not extract FR doc number from URL: {url}"

    doc_number = m.group(1)
    api_url = _FR_API_TEMPLATE.format(doc_number=doc_number)

    api_text, status = _http_get(client, api_url)
    if status != 200 or not api_text:
        return "", f"FR API returned status={status} for doc {doc_number}"

    try:
        meta = json.loads(api_text)
    except json.JSONDecodeError as exc:
        return "", f"FR API JSON parse error for {doc_number}: {exc}"

    raw_text_url = meta.get("raw_text_url")
    if not raw_text_url:
        # Fallback: use abstract if present
        abstract = (meta.get("abstract") or "").strip()
        if abstract:
            return abstract[:max_chars], None
        return "", f"FR API has no raw_text_url or abstract for {doc_number}"

    body_html, status2 = _http_get(client, raw_text_url)
    if status2 != 200 or not body_html:
        return "", f"FR raw_text fetch returned status={status2} for {doc_number}"

    soup = BeautifulSoup(body_html, "html.parser")
    pre = soup.find("pre")
    raw = pre.get_text() if pre else soup.get_text(separator="\n")

    # Strip FR boilerplate lines and compress whitespace
    lines = raw.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _BOILERPLATE_STRIP_RE.match(stripped):
            continue
        cleaned.append(stripped)

    body = "\n".join(cleaned)
    return body[:max_chars], None


def _extract_body_generic(
    url: str, client: httpx.Client, max_chars: int
) -> tuple[str, str | None]:
    """
    Generic HTML body extraction for non-FR URLs.

    Tries <article>, <main>, <div class="entry-content"> in order.
    Falls back to <body> text. Returns (body_text, error | None).
    """
    html, status = _http_get(client, url)
    if status not in (200, 301, 302) or not html:
        return "", f"HTTP {status} fetching {url}"

    soup = BeautifulSoup(html, "html.parser")

    # Remove nav/header/footer noise
    for tag in soup(["nav", "header", "footer", "script", "style", "noscript"]):
        tag.decompose()

    # Try semantic containers in order of preference
    container = (
        soup.find("article")
        or soup.find("main")
        or soup.find(class_="entry-content")
        or soup.find(class_="post-content")
        or soup.find(class_="article-body")
        or soup.find("body")
    )

    if not container:
        return "", f"No content container found in {url}"

    text = container.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body = "\n".join(lines)
    return body[:max_chars], None


def fetch_article_body(
    url: str,
    client: httpx.Client,
    max_chars: int,
) -> tuple[str, str | None]:
    """
    Dispatch to the right extractor based on URL domain.
    Returns (body_text, error_message | None).
    """
    if "federalregister.gov" in url:
        return _extract_body_fr(url, client, max_chars)
    return _extract_body_generic(url, client, max_chars)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def fetch_entries(
    limit: int,
    fetch_body: bool,
    body_delay: float,
    max_body_chars: int,
) -> tuple[list[dict], list[str]]:
    """Fetch SBA RSS entries + (optionally) article bodies. Returns (records, errors)."""
    errors: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    # --- Step 1: fetch and parse the RSS feed ---
    raw, status = _fetch_raw_text(SBA_PRIMARY_URL)
    feed = feedparser.parse(raw)

    if status != 200 or not feed.entries:
        msg = (
            f"Primary SBA RSS returned status={status} with {len(feed.entries)} entries. "
            f"Falling back to Federal Register SBA feed."
        )
        errors.append(msg)
        print(f"  [WARN] {msg}")
        raw, status = _fetch_raw_text(SBA_FALLBACK_URL)
        feed = feedparser.parse(raw)
        if not feed.entries:
            errors.append(f"Fallback feed also returned 0 entries (status={status}).")
            return [], errors

    entries = feed.entries[:limit]

    # --- Step 2: for each entry, pull body if requested ---
    records = []

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for i, entry in enumerate(entries):
            # Seed body from RSS metadata (summary / content fields)
            rss_body = ""
            if hasattr(entry, "summary"):
                rss_body = entry.summary or ""
            if hasattr(entry, "content") and entry.content:
                rss_body = entry.content[0].get("value", rss_body)
            rss_body = rss_body.strip()

            url   = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            body  = rss_body
            body_error: str | None = None

            if fetch_body and url:
                t0 = time.monotonic()
                fetched, body_error = fetch_article_body(url, client, max_body_chars)
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if body_error:
                    print(f"  [WARN] body fetch failed ({elapsed_ms}ms): {body_error}")
                    errors.append(f"[{title[:60]}] {body_error}")
                    # Keep rss_body as fallback; add error annotation
                    body = rss_body
                elif fetched:
                    body = fetched
                    print(f"  [OK]   body fetched ({elapsed_ms}ms, {len(body)} chars): {title[:60]}")
                else:
                    body = rss_body
                    print(f"  [WARN] body empty after fetch ({elapsed_ms}ms): {title[:60]}")

                # Polite delay between article fetches (skip after last entry)
                if i < len(entries) - 1 and body_delay > 0:
                    time.sleep(body_delay)

            rec: dict = {
                "title":      title,
                "url":        url,
                "body":       body,
                "source":     SOURCE_NAME,
                "fetched_at": now,
            }
            if body_error:
                rec["body_error"] = body_error

            records.append(rec)

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
    parser.add_argument(
        "--no-body", action="store_true",
        help="Skip article body fetching (metadata-only, fast)",
    )
    parser.add_argument(
        "--body-delay", type=float, default=DEFAULT_BODY_DELAY_S,
        metavar="SECONDS",
        help=f"Polite delay between body fetches in seconds (default: {DEFAULT_BODY_DELAY_S})",
    )
    parser.add_argument(
        "--max-body-chars", type=int, default=DEFAULT_MAX_BODY_CHARS,
        metavar="N",
        help=f"Truncate article bodies to N characters (default: {DEFAULT_MAX_BODY_CHARS})",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    fetch_body = not args.no_body
    print(
        f"C-Transit: fetching SBA feed "
        f"(limit={args.limit}, body={'yes' if fetch_body else 'no'}, "
        f"delay={args.body_delay}s, max_chars={args.max_body_chars})"
    )

    entries, errors = fetch_entries(
        limit=args.limit,
        fetch_body=fetch_body,
        body_delay=args.body_delay,
        max_body_chars=args.max_body_chars,
    )
    out_path = write_inbox(entries, SOURCE_NAME)
    print(f"  Wrote {len(entries)} records -> {out_path}")

    log_run("c-transit", started_at, record_count=len(entries), errors=errors or None)


if __name__ == "__main__":
    main()
