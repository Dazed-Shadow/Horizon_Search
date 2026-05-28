#!/usr/bin/env python3
"""
spotter_package.py — Review package generator for C-SPOTTER candidates.

Reads a spotter_<YYYY-MM-DD>.jsonl file and produces two standalone review files:

  _packages/spotter_review_<date>.html  -- brand-themed (Deep Ocean Blue / Slate Grey-Blue)
                                           accordion-style grouped by NAICS code;
                                           one business card per record;
                                           null fields shown as dimmed placeholders.
  _packages/spotter_review_<date>.csv   -- clean tabular CSV, one row per business,
                                           UTF-8 with BOM (Excel-safe), QUOTE_ALL.
                                           Includes jr_status / jr_notes / jr_priority
                                           annotation columns (always blank).

Usage:
    python scripts/spotter_package.py --date 2026-05-28
    python scripts/spotter_package.py --date 2026-05-28 --out-dir /custom/path

See Central Hub: pipeline/DECISIONS.md (D-015) for rationale.
"""

import argparse
import codecs
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE           = Path(__file__).resolve().parent.parent   # repo root
CANDIDATES_DIR = HERE / "research" / "data" / "candidates"
PACKAGES_DIR   = CANDIDATES_DIR / "_packages"

# ---------------------------------------------------------------------------
# Brand palette (mirrors phile_package.py)
# ---------------------------------------------------------------------------
COLOR_OCEAN   = "#0B2C4D"
COLOR_SLATE   = "#5A7795"
COLOR_ACCENT  = "#2E6DA4"
COLOR_BG      = "#F4F7FA"
COLOR_CARD_BG = "#FFFFFF"
COLOR_MUTED   = "#8AA3BC"
COLOR_TEXT    = "#1A2D40"
COLOR_NULL    = "#B0BEC8"   # dimmed placeholder colour


# ---------------------------------------------------------------------------
# Load JSONL
# ---------------------------------------------------------------------------
def load_records(date_str: str) -> list[dict]:
    path = CANDIDATES_DIR / f"spotter_{date_str}.jsonl"
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[WARN] Line {lineno} is not valid JSON — skipping: {exc}", file=sys.stderr)
    return records


# ---------------------------------------------------------------------------
# Group by NAICS
# ---------------------------------------------------------------------------
def group_by_naics(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for rec in records:
        naics = rec.get("naics", "unknown")
        groups.setdefault(naics, []).append(rec)
    return groups


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------
CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: {COLOR_BG};
    color: {COLOR_TEXT};
    line-height: 1.6;
}}
a {{ color: {COLOR_ACCENT}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ── Header ── */
#page-header {{
    background: {COLOR_OCEAN};
    color: #fff;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}}
#page-header h1 {{
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}}
#page-header .meta {{
    font-size: 0.8rem;
    color: {COLOR_MUTED};
    margin-top: 0.2rem;
}}

/* ── Main layout ── */
.container {{
    max-width: 920px;
    margin: 2rem auto;
    padding: 0 1rem 4rem;
}}

/* ── NAICS group (accordion) ── */
.naics-group {{
    margin-bottom: 2rem;
}}
.naics-group summary {{
    background: {COLOR_OCEAN};
    color: #fff;
    padding: 0.75rem 1.2rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 1rem;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    user-select: none;
}}
.naics-group summary::-webkit-details-marker {{ display: none; }}
.naics-group summary::before {{
    content: "▶";
    font-size: 0.75rem;
    transition: transform 0.15s;
    flex-shrink: 0;
}}
.naics-group[open] summary::before {{
    transform: rotate(90deg);
}}
.naics-badge {{
    background: rgba(255,255,255,0.15);
    border-radius: 999px;
    padding: 0.15rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 400;
    letter-spacing: 0.04em;
}}
.naics-count {{
    margin-left: auto;
    font-size: 0.78rem;
    font-weight: 400;
    color: {COLOR_MUTED};
}}
.naics-cards {{
    margin-top: 0.75rem;
    display: grid;
    gap: 1rem;
}}

/* ── Business card ── */
.biz-card {{
    background: {COLOR_CARD_BG};
    border-radius: 8px;
    border: 1px solid #D8E6F3;
    box-shadow: 0 1px 6px rgba(11,44,77,0.07);
    overflow: hidden;
}}
.biz-card-header {{
    background: #EEF4FA;
    border-bottom: 1px solid #D8E6F3;
    padding: 0.65rem 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}}
.biz-name {{
    font-weight: 700;
    font-size: 1rem;
    color: {COLOR_OCEAN};
    flex: 1;
}}
.biz-fields {{
    padding: 0.75rem 1.1rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.5rem 1.5rem;
}}
.field {{
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}}
.field-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: {COLOR_SLATE};
}}
.field-value {{
    font-size: 0.9rem;
    color: {COLOR_TEXT};
    word-break: break-word;
}}
.field-null {{
    font-size: 0.85rem;
    color: {COLOR_NULL};
    font-style: italic;
}}

/* ── Footer ── */
footer {{
    text-align: center;
    color: {COLOR_MUTED};
    font-size: 0.78rem;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #D8E6F3;
}}
"""


def _field_html(label: str, value, link: bool = False, mailto: bool = False) -> str:
    """Render one field row. value=None → dimmed placeholder."""
    if value is None or value == "":
        val_html = '<span class="field-null">not on profile</span>'
    elif mailto and value:
        val_html = f'<span class="field-value"><a href="mailto:{value}" target="_blank">{value}</a></span>'
    elif link and value:
        href = value if value.startswith("http") else f"https://{value}"
        val_html = f'<span class="field-value"><a href="{href}" target="_blank" rel="noopener">{value}</a></span>'
    else:
        val_html = f'<span class="field-value">{value}</span>'

    return (
        f'<div class="field">'
        f'<span class="field-label">{label}</span>'
        f'{val_html}'
        f'</div>'
    )


def _build_card(rec: dict) -> str:
    name = rec.get("name", "—")
    sba_url = rec.get("url", "")
    sba_link = (
        f'<a href="{sba_url}" target="_blank" rel="noopener" class="naics-badge" '
        f'style="background:{COLOR_ACCENT};color:#fff;text-decoration:none;">SBA Profile ↗</a>'
        if sba_url else ""
    )
    sam_url = rec.get("sam_profile_url")
    sam_link = (
        f'<a href="{sam_url}" target="_blank" rel="noopener" class="naics-badge" '
        f'style="background:{COLOR_SLATE};color:#fff;text-decoration:none;">SAM.gov ↗</a>'
        if sam_url else ""
    )
    fields = "\n".join([
        _field_html("CAGE Code",       rec.get("cage_code")),
        _field_html("Business Website", rec.get("business_website"), link=True),
        _field_html("Email",            rec.get("email"), mailto=True),
        _field_html("Contact",          rec.get("contact_name")),
        _field_html("SAM Profile",      rec.get("sam_profile_url"), link=True),
    ])
    return f"""
<div class="biz-card">
  <div class="biz-card-header">
    <span class="biz-name">{name}</span>
    {sba_link}
    {sam_link}
  </div>
  <div class="biz-fields">
    {fields}
  </div>
</div>"""


def build_html_package(date_str: str, records: list[dict]) -> str:
    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(records)
    groups = group_by_naics(records)

    group_html_parts = []
    for naics, group_records in sorted(groups.items()):
        cards_html = "\n".join(_build_card(r) for r in group_records)
        group_html_parts.append(f"""
<details class="naics-group" open>
  <summary>
    NAICS <span class="naics-badge">{naics}</span>
    <span class="naics-count">{len(group_records)} business(es)</span>
  </summary>
  <div class="naics-cards">
    {cards_html}
  </div>
</details>""")

    groups_html = "\n".join(group_html_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>C-SPOTTER Review · {date_str}</title>
<style>{CSS}</style>
</head>
<body>

<div id="page-header">
  <h1>C-SPOTTER Candidate Review &mdash; {date_str}</h1>
  <div class="meta">Generated {gen_ts} &nbsp;&middot;&nbsp; {total} business(es) &nbsp;&middot;&nbsp; {len(groups)} NAICS group(s)</div>
</div>

<div class="container">
{groups_html}

  <footer>
    Generated {gen_ts} &nbsp;&middot;&nbsp; {total} candidate(s) &nbsp;&middot;&nbsp; C-SPOTTER {date_str}
  </footer>
</div>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# CSV builder
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "name",
    "naics_matched",
    "cage_code",
    "business_website",
    "email",
    "contact_name",
    "sba_profile_url",
    "sam_profile_url",
    "jr_status",
    "jr_notes",
    "jr_priority",
]


def build_csv_package(date_str: str, records: list[dict], out_path: Path) -> None:
    """Write UTF-8-BOM CSV (QUOTE_ALL) so Excel reads it cleanly."""
    with codecs.open(str(out_path), "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        writer.writerow(CSV_COLUMNS)
        for rec in records:
            writer.writerow([
                rec.get("name", ""),
                rec.get("naics", ""),
                rec.get("cage_code") or "",
                rec.get("business_website") or "",
                rec.get("email") or "",
                rec.get("contact_name") or "",
                rec.get("url", ""),          # sba_profile_url ← url field
                rec.get("sam_profile_url") or "",
                "",   # jr_status  — JR annotation
                "",   # jr_notes   — JR annotation
                "",   # jr_priority — JR annotation
            ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="spotter_package.py — generate HTML + CSV review package from SPOTTER JSONL"
    )
    parser.add_argument(
        "--date", required=True,
        help="Date string matching the JSONL filename, e.g. 2026-05-28"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help=f"Output directory (default: {PACKAGES_DIR})"
    )
    args = parser.parse_args()

    date_str = args.date
    out_dir  = args.out_dir if args.out_dir else PACKAGES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"spotter_package: building review package for {date_str}")
    records = load_records(date_str)
    print(f"  Loaded {len(records)} record(s) from spotter_{date_str}.jsonl")

    if not records:
        print("[ERROR] No records to package. Exiting.")
        sys.exit(1)

    # Write HTML
    html_path = out_dir / f"spotter_review_{date_str}.html"
    html_path.write_text(build_html_package(date_str, records), encoding="utf-8")
    print(f"  HTML -> {html_path}  ({html_path.stat().st_size:,} bytes)")

    # Write CSV
    csv_path = out_dir / f"spotter_review_{date_str}.csv"
    build_csv_package(date_str, records, csv_path)
    print(f"  CSV  -> {csv_path}  ({csv_path.stat().st_size:,} bytes)")

    print(f"\nspotter_package: done. Review at:\n  {out_dir}")


if __name__ == "__main__":
    main()
