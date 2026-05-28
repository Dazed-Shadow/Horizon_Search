#!/usr/bin/env python3
"""
phile_catalog.py — Article catalog builder for C-Phile.

Scans research/data/drafts/_consumed/*.md bundles and produces three output files:

  _catalog/articles.jsonl   -- machine-readable, one JSON object per consumed article
  _catalog/index.html       -- brand-themed sortable table (vanilla JS, no external assets)
  _catalog/summary.md       -- counts by source, counts by category, recent activity timeline

Fully idempotent: re-running rebuilds all three files from current _consumed/ state.

Usage:
    python scripts/phile_catalog.py
    python scripts/phile_catalog.py --out-dir /custom/path

See Central Hub: pipeline/DECISIONS.md (D-017) for rationale.
"""

import argparse
import json
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

HERE         = Path(__file__).resolve().parent.parent   # repo root
CONSUMED_DIR = HERE / "research" / "data" / "drafts" / "_consumed"
FEEDS_TOML   = HERE / "research" / "feeds.toml"
DEFAULT_OUT  = HERE / "research" / "data" / "drafts" / "_catalog"

# Brand colors (mirrors phile_package.py)
COLOR_OCEAN  = "#0B2C4D"
COLOR_SLATE  = "#5A7795"
COLOR_ACCENT = "#2E6DA4"
COLOR_BG     = "#F4F7FA"
COLOR_MUTED  = "#8AA3BC"
COLOR_TEXT   = "#1A2D40"


# ---------------------------------------------------------------------------
# feeds.toml → {source_slug: category} lookup
# ---------------------------------------------------------------------------
def _slug(name_or_url: str) -> str:
    """Normalise a feed name or URL fragment into a lowercase slug for matching."""
    return name_or_url.lower().replace(" ", "_")


def load_feed_categories() -> dict[str, str]:
    """Return {source_slug: category} built from research/feeds.toml.

    The bundle stores the source as a slug like 'mit_technology_review'. We
    match against the feed name (title-cased then slugged) as well as keywords
    found in the URL, so partial matches work for most cases.
    """
    cats: dict[str, str] = {}
    if not FEEDS_TOML.exists():
        return cats
    try:
        with open(FEEDS_TOML, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return cats

    for feed in data.get("feeds", []):
        name     = feed.get("name", "")
        url      = feed.get("url", "")
        category = feed.get("category", "uncategorized")
        # Store by slugged name
        cats[_slug(name)] = category
        # Also store by domain fragment extracted from URL for fallback matching
        m = re.search(r"https?://(?:www\.|feeds\.)?([^/]+)", url)
        if m:
            domain_key = m.group(1).replace(".", "_").lower()
            cats.setdefault(domain_key, category)
    return cats


def derive_category(source_slug: str, feed_cats: dict[str, str]) -> str:
    """Look up category for a source slug using the feed catalog.

    Strategy:
    1. Exact match on slug.
    2. Check if any catalog key is a substring of the source slug or vice versa.
    3. Fallback to 'uncategorized'.
    """
    if not source_slug:
        return "uncategorized"
    slug_lower = source_slug.lower()
    # Exact
    if slug_lower in feed_cats:
        return feed_cats[slug_lower]
    # Substring match
    for key, cat in feed_cats.items():
        if key in slug_lower or slug_lower in key:
            return cat
    return "uncategorized"


# ---------------------------------------------------------------------------
# Bundle parsing
# ---------------------------------------------------------------------------
_GENERATED_RE = re.compile(r"<!--\s*generated:\s*(\S+)\s*-->")
_BUNDLE_RE    = re.compile(r"<!--\s*bundle:\s*(\S+)\s*-->")
_URL_RE       = re.compile(r"\*\*URL:\*\*\s*(.+)")
_TITLE_RE     = re.compile(r"\*\*Title:\*\*\s*(.+)")
_SOURCE_RE    = re.compile(r"\*\*Source:\*\*\s*(.+)")


def parse_bundle(path: Path, feed_cats: dict[str, str]) -> dict | None:
    """Parse a consumed bundle file and return a catalog record dict, or None on failure."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    # HTML comment metadata
    m = _GENERATED_RE.search(text)
    batch_ts = m.group(1).strip() if m else ""

    m = _BUNDLE_RE.search(text)
    bundle_slug = m.group(1).strip() if m else path.stem

    # Narrow to ## Source article section
    sec_match = re.search(
        r"## Source article(.*?)(?=^##|\Z)", text, re.DOTALL | re.MULTILINE
    )
    search_text = sec_match.group(1) if sec_match else text

    m = _TITLE_RE.search(search_text)
    title = m.group(1).strip() if m else ""
    if title.startswith("["):
        title = ""  # unfilled placeholder

    m = _SOURCE_RE.search(search_text)
    source = m.group(1).strip() if m else ""

    m = _URL_RE.search(search_text)
    url = m.group(1).strip() if m else ""
    if url.startswith("["):
        url = ""  # unfilled placeholder

    if not url:
        return None  # can't use this as a catalog entry without a URL key

    # consumed_at from file mtime (UTC ISO8601)
    try:
        mtime = path.stat().st_mtime
        consumed_at = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        consumed_at = ""

    # source_name: humanize the slug
    source_name = source.replace("_", " ").title()

    # category: derive from source slug via feeds.toml
    category = derive_category(source, feed_cats)

    return {
        "url":         url,
        "title":       title or "(no title)",
        "source":      source,
        "source_name": source_name,
        "category":    category,
        "batch_ts":    batch_ts,
        "bundle_slug": bundle_slug,
        "consumed_at": consumed_at,
    }


# ---------------------------------------------------------------------------
# Load all bundles
# ---------------------------------------------------------------------------
def load_all_records(feed_cats: dict[str, str]) -> list[dict]:
    """Return all catalog records from _consumed/, sorted by consumed_at descending."""
    records: list[dict] = []
    seen_urls: set[str] = set()

    if not CONSUMED_DIR.exists():
        return records

    for path in sorted(CONSUMED_DIR.glob("*.md")):
        rec = parse_bundle(path, feed_cats)
        if rec is None:
            continue
        url = rec["url"]
        if url in seen_urls:
            continue  # same article bundled multiple times — keep first occurrence in sort
        seen_urls.add(url)
        records.append(rec)

    # Sort newest consumed_at first
    records.sort(key=lambda r: r["consumed_at"], reverse=True)
    return records


# ---------------------------------------------------------------------------
# Output: articles.jsonl
# ---------------------------------------------------------------------------
def write_jsonl(records: list[dict], out_path: Path) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Output: index.html
# ---------------------------------------------------------------------------
_CATALOG_CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: {COLOR_BG};
    color: {COLOR_TEXT};
    line-height: 1.6;
}}
a {{ color: {COLOR_ACCENT}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

header {{
    background: {COLOR_OCEAN};
    color: #fff;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}}
header h1 {{ font-size: 1.2rem; font-weight: 700; }}
header .subtitle {{ font-size: 0.82rem; color: {COLOR_MUTED}; }}

.container {{
    max-width: 1100px;
    margin: 1.5rem auto;
    padding: 0 1rem 4rem;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(11,44,77,0.07);
    font-size: 0.88rem;
}}
thead th {{
    background: {COLOR_OCEAN};
    color: #fff;
    padding: 0.65rem 1rem;
    text-align: left;
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
}}
thead th:hover {{ background: {COLOR_SLATE}; }}
thead th .sort-arrow {{ margin-left: 0.3rem; opacity: 0.5; font-size: 0.7rem; }}
thead th.sorted-asc .sort-arrow::after {{ content: "▲"; opacity: 1; }}
thead th.sorted-desc .sort-arrow::after {{ content: "▼"; opacity: 1; }}
thead th:not(.sorted-asc):not(.sorted-desc) .sort-arrow::after {{ content: "⇅"; }}

tbody tr:nth-child(even) {{ background: {COLOR_BG}; }}
tbody tr:hover {{ background: #E8F2FC; }}
td {{ padding: 0.55rem 1rem; vertical-align: top; border-bottom: 1px solid #E0EAF4; }}
td.td-consumed {{ white-space: nowrap; font-size: 0.78rem; color: {COLOR_MUTED}; }}
td.td-source   {{ font-size: 0.82rem; white-space: nowrap; }}
td.td-category {{ }}
td.td-title    {{ }}
td.td-batch    {{ white-space: nowrap; font-size: 0.78rem; color: {COLOR_MUTED}; font-family: monospace; }}

.cat-badge {{
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    white-space: nowrap;
}}

footer {{
    text-align: center;
    color: {COLOR_MUTED};
    font-size: 0.78rem;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #D8E6F3;
}}
"""

# Category badge colors (same palette as phile_package.py)
_CAT_COLORS: dict[str, tuple[str, str]] = {
    "ai":            ("#6C3ABF", "#EDE7FF"),
    "tech":          ("#1A6B8A", "#E0F4FF"),
    "health":        ("#1A7A4A", "#E0F5EA"),
    "smallbiz":      ("#8A5A1A", "#FFF4E0"),
    "policy":        ("#5A1A8A", "#F4E0FF"),
    "world":         ("#1A3A8A", "#E0E8FF"),
    "general":       ("#4A5A6A", "#EEF2F6"),
    "uncategorized": ("#4A5A6A", "#EEF2F6"),
}


def _cat_badge(cat: str) -> str:
    fg, bg = _CAT_COLORS.get(cat.lower(), _CAT_COLORS["uncategorized"])
    return f'<span class="cat-badge" style="background:{bg};color:{fg};">{cat.upper()}</span>'


_SORT_JS = """
(function () {
  const table = document.getElementById('catalog-table');
  const headers = table.querySelectorAll('thead th');
  let sortCol = 0, sortAsc = false;

  function cellText(row, col) {
    return row.cells[col] ? row.cells[col].dataset.sort || row.cells[col].innerText.trim() : '';
  }

  function sortTable(col) {
    if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
    headers.forEach((th, i) => {
      th.classList.toggle('sorted-asc',  i === sortCol &&  sortAsc);
      th.classList.toggle('sorted-desc', i === sortCol && !sortAsc);
    });
    const tbody = table.tBodies[0];
    const rows  = Array.from(tbody.rows);
    rows.sort((a, b) => {
      const va = cellText(a, sortCol);
      const vb = cellText(b, sortCol);
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
    rows.forEach(r => tbody.appendChild(r));
  }

  headers.forEach((th, i) => { th.addEventListener('click', () => sortTable(i)); });
  // Default sort: Consumed descending (col 0)
  sortTable(0); sortAsc = false; sortTable(0);
})();
"""


def build_html(records: list[dict], gen_ts: str) -> str:
    total = len(records)
    rows_html: list[str] = []
    for r in records:
        url   = r["url"]
        title = r["title"]
        title_cell = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title
        rows_html.append(
            f'<tr>'
            f'<td class="td-consumed" data-sort="{r["consumed_at"]}">{r["consumed_at"][:10]}</td>'
            f'<td class="td-source">{r["source_name"] or r["source"]}</td>'
            f'<td class="td-category">{_cat_badge(r["category"])}</td>'
            f'<td class="td-title">{title_cell}</td>'
            f'<td class="td-batch">{r["batch_ts"]}</td>'
            f'</tr>'
        )
    rows = "\n".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>C-Phile Article Catalog</title>
<style>{_CATALOG_CSS}</style>
</head>
<body>

<header>
  <div>
    <h1>C-Phile Article Catalog</h1>
    <div class="subtitle">Generated {gen_ts} &nbsp;·&nbsp; {total} article(s) &nbsp;·&nbsp; Click column headers to sort</div>
  </div>
</header>

<div class="container">
<table id="catalog-table">
  <thead>
    <tr>
      <th>Consumed <span class="sort-arrow"></span></th>
      <th>Source <span class="sort-arrow"></span></th>
      <th>Category <span class="sort-arrow"></span></th>
      <th>Title <span class="sort-arrow"></span></th>
      <th>Batch <span class="sort-arrow"></span></th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
</div>

<footer>C-Phile Article Catalog &nbsp;·&nbsp; Generated {gen_ts} &nbsp;·&nbsp; {total} article(s)</footer>

<script>{_SORT_JS}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Output: summary.md
# ---------------------------------------------------------------------------
def build_summary(records: list[dict], gen_ts: str) -> str:
    from collections import Counter, defaultdict

    total = len(records)
    by_source:   Counter = Counter(r["source_name"] or r["source"] for r in records)
    by_category: Counter = Counter(r["category"] for r in records)

    # Recent activity: last 14 days
    today = datetime.now(timezone.utc).date()
    cutoff_ts = (today.isoformat() + "T00:00:00Z")
    # compute 14-day cutoff string for comparison
    from datetime import timedelta
    cutoff_date = today - timedelta(days=14)
    cutoff_ts_str = cutoff_date.isoformat() + "T00:00:00Z"

    by_date: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        if r["consumed_at"] >= cutoff_ts_str:
            date_str = r["consumed_at"][:10]
            by_date[date_str].append(r)

    lines: list[str] = [
        f"# C-Phile Article Catalog — Summary",
        "",
        f"_Generated {gen_ts} · {total} article(s) total_",
        "",
        "---",
        "",
        "## 1. Articles by Source",
        "",
        "| Source | Count |",
        "|--------|-------|",
    ]
    for source, count in sorted(by_source.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {source} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## 2. Articles by Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for cat, count in sorted(by_category.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {cat} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## 3. Recent Activity (Last 14 Days)",
        "",
    ]
    if not by_date:
        lines.append("_No activity in the last 14 days._")
    else:
        for date_str in sorted(by_date.keys(), reverse=True):
            lines.append(f"**{date_str}**")
            for r in sorted(by_date[date_str], key=lambda x: x["consumed_at"], reverse=True):
                src = r["source_name"] or r["source"]
                lines.append(f"- {src} · {r['title']}")
            lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="phile_catalog.py — build article catalog from _consumed/ bundles"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("phile_catalog: loading feed categories from feeds.toml ...")
    feed_cats = load_feed_categories()
    print(f"  {len(feed_cats)} feed category mapping(s) loaded.")

    print(f"phile_catalog: scanning {CONSUMED_DIR} ...")
    records = load_all_records(feed_cats)
    print(f"  {len(records)} unique article(s) found.")

    if not records:
        print("  [WARN] No consumed bundles found — catalog files will be empty.")

    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # articles.jsonl
    jsonl_path = out_dir / "articles.jsonl"
    write_jsonl(records, jsonl_path)
    print(f"  articles.jsonl  -> {jsonl_path}  ({jsonl_path.stat().st_size:,} bytes)")

    # index.html
    html_path = out_dir / "index.html"
    html_path.write_text(build_html(records, gen_ts), encoding="utf-8")
    print(f"  index.html      -> {html_path}  ({html_path.stat().st_size:,} bytes)")

    # summary.md
    md_path = out_dir / "summary.md"
    md_path.write_text(build_summary(records, gen_ts), encoding="utf-8")
    print(f"  summary.md      -> {md_path}  ({md_path.stat().st_size:,} bytes)")

    print(f"\nphile_catalog: done. Catalog at:\n  {out_dir}")


if __name__ == "__main__":
    main()
