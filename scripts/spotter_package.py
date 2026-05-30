#!/usr/bin/env python3
"""
spotter_package.py — Review package generator for C-SPOTTER candidates.

Reads a spotter_<YYYY-MM-DD>.jsonl file and produces two standalone review files:

  _packages/spotter_review_<date>.html  -- brand-themed (Deep Ocean Blue / Slate Grey-Blue)
                                           accordion-style grouped by NAICS code;
                                           one business card per record;
                                           null fields shown as dimmed placeholders;
                                           Award History panel per card (D-021).
  _packages/spotter_review_<date>.csv   -- clean tabular CSV, one row per business,
                                           UTF-8 with BOM (Excel-safe), QUOTE_ALL.
                                           Includes award columns + jr_status / jr_notes /
                                           jr_priority annotation columns.

Input file preference (D-021):
  If spotter_<date>_awards.jsonl exists, it is used (awards sidecar from
  spotter_awards.py). Falls back to spotter_<date>.jsonl otherwise. Running the
  packager before awards enrichment still works — it just shows no award data.

Annotation preservation (D-021 / CRITICAL):
  Before writing the CSV, the packager checks for an existing CSV at the output
  path. If one exists it reads jr_status, jr_notes, jr_priority keyed on
  cage_code. When writing the new CSV it carries those values forward for any
  matching row. This makes the packager idempotent: JR can re-run it after
  editing the CSV in Excel without losing annotations.
  Rows with null/blank cage_code cannot be matched and are written with blank
  annotations (safe degradation).

Usage:
    python scripts/spotter_package.py --date 2026-05-28
    python scripts/spotter_package.py --date 2026-05-28 --out-dir /custom/path

See Central Hub: pipeline/DECISIONS.md (D-015, D-021) for rationale.
"""

import argparse
import codecs
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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
# Load JSONL (B1: prefer awards sidecar if present)
# ---------------------------------------------------------------------------
def load_records(date_str: str) -> tuple[list[dict], str]:
    """
    Load records for the given date.  Returns (records, source_label).

    Preference order (D-021):
      1. spotter_<date>_awards.jsonl  — enriched with USAspending data
      2. spotter_<date>.jsonl         — raw scrape (no award fields)
    """
    awards_path = CANDIDATES_DIR / f"spotter_{date_str}_awards.jsonl"
    raw_path    = CANDIDATES_DIR / f"spotter_{date_str}.jsonl"

    if awards_path.exists():
        path = awards_path
        source_label = f"awards sidecar ({awards_path.name})"
    elif raw_path.exists():
        path = raw_path
        source_label = f"raw scrape ({raw_path.name}) — no award data"
    else:
        print(f"[ERROR] No input file found for {date_str}: tried {awards_path.name} and {raw_path.name}", file=sys.stderr)
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

    return records, source_label


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

/* ── Award History panel (D-021) ── */
.award-panel {{
    border-top: 1px solid #D8E6F3;
    padding: 0.65rem 1.1rem;
    background: #F9FBFD;
}}
.award-panel-header {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
}}
.award-panel-title {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: {COLOR_SLATE};
}}
.award-count-badge {{
    background: {COLOR_ACCENT};
    color: #fff;
    border-radius: 999px;
    padding: 0.05rem 0.45rem;
    font-size: 0.68rem;
    font-weight: 600;
}}
.award-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem 1.5rem;
}}
.award-col-label {{
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {COLOR_MUTED};
    margin-bottom: 0.1rem;
}}
.award-line {{
    font-size: 0.82rem;
    color: {COLOR_TEXT};
}}
.award-amount {{
    font-weight: 600;
    color: {COLOR_OCEAN};
}}
.award-none {{
    font-size: 0.85rem;
    color: #4A7C59;
    font-style: italic;
}}
.award-fail {{
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


def _fmt_amount(amount) -> str:
    """Format a dollar amount as $1,234,567. Returns '—' if None/zero."""
    if amount is None:
        return "—"
    try:
        return f"${float(amount):,.0f}"
    except (TypeError, ValueError):
        return str(amount)


def _build_award_panel(rec: dict) -> str:
    """
    Render the Award History panel for a business card (D-021).

    award_status determines layout:
      "has_awards"              → first + latest award grid with count badge
      "no_federal_awards_found" → ground-floor message
      "lookup_failed"           → unavailable placeholder
      missing/None              → awards sidecar not used (raw scrape fallback)
    """
    status = rec.get("award_status")

    if status is None:
        # Raw scrape — no award enrichment was run
        return ""

    badge_html = ""
    total = rec.get("total_awards_count", 0)
    if status == "has_awards" and total:
        badge_html = f'<span class="award-count-badge">{total} contract(s)</span>'

    header = f"""
  <div class="award-panel">
    <div class="award-panel-header">
      <span class="award-panel-title">Award History</span>
      {badge_html}
    </div>"""

    if status == "no_federal_awards_found":
        return header + """
    <div class="award-none">No federal awards found yet &mdash; ground-floor candidate.</div>
  </div>"""

    if status == "lookup_failed":
        return header + """
    <div class="award-fail">Lookup unavailable.</div>
  </div>"""

    # has_awards
    fa = rec.get("first_award") or {}
    la = rec.get("latest_award") or {}

    def _award_col(label: str, award: dict) -> str:
        date  = award.get("date") or "—"
        amt   = _fmt_amount(award.get("amount"))
        agency = award.get("agency") or "—"
        ctype  = award.get("contract_type") or "—"
        return (
            f'<div>'
            f'<div class="award-col-label">{label}</div>'
            f'<div class="award-line"><span class="award-amount">{amt}</span> &middot; {date}</div>'
            f'<div class="award-line">{agency}</div>'
            f'<div class="award-line" style="color:{COLOR_MUTED};font-size:0.78rem">{ctype}</div>'
            f'</div>'
        )

    return header + f"""
    <div class="award-grid">
      {_award_col("First Award", fa)}
      {_award_col("Latest Award", la)}
    </div>
  </div>"""


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

    # PDF badge — file:// link so it opens in the user's default PDF viewer.
    # CANDIDATES_DIR is the parent of _pdfs/; resolve the absolute path for file://.
    pdf_rel = rec.get("profile_pdf")
    if pdf_rel:
        # pdf_rel is relative to repo root (e.g. research/data/candidates/_pdfs/9AZM9.pdf)
        # Convert to absolute path for the file:// URI.
        abs_pdf = (HERE / pdf_rel).resolve()
        # Use forward slashes; Windows file:// needs triple slash + drive letter.
        pdf_uri = abs_pdf.as_uri()
        pdf_link = (
            f'<a href="{pdf_uri}" class="naics-badge" '
            f'style="background:#4A7C59;color:#fff;text-decoration:none;">📎 Profile PDF</a>'
        )
    else:
        pdf_link = (
            f'<span class="naics-badge" '
            f'style="background:transparent;color:{COLOR_NULL};border:1px solid {COLOR_NULL};">'
            f'no PDF</span>'
        )

    fields = "\n".join([
        _field_html("CAGE Code",       rec.get("cage_code")),
        _field_html("Business Website", rec.get("business_website"), link=True),
        _field_html("Email",            rec.get("email"), mailto=True),
        _field_html("Contact",          rec.get("contact_name")),
        _field_html("SAM Profile",      rec.get("sam_profile_url"), link=True),
    ])
    award_panel = _build_award_panel(rec)
    return f"""
<div class="biz-card">
  <div class="biz-card-header">
    <span class="biz-name">{name}</span>
    {sba_link}
    {sam_link}
    {pdf_link}
  </div>
  <div class="biz-fields">
    {fields}
  </div>
  {award_panel}
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
# CSV builder (B3: new award columns; B4: annotation preservation)
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "name",
    "naics_matched",
    "cage_code",
    "business_website",
    "email",
    "contact_name",
    "pdf_path",              # relative path to _pdfs/<cage_code>.pdf, or blank
    # Award columns (D-021) — blank when no awards sidecar was used
    "award_status",
    "first_award_date",
    "first_award_amount",
    "first_award_agency",
    "latest_award_date",
    "latest_award_amount",
    "latest_award_agency",
    "total_awards_count",
    # Profile links
    "sba_profile_url",
    "sam_profile_url",
    # JR annotation columns — always last; preserved across re-runs via CAGE key
    "jr_status",
    "jr_notes",
    "jr_priority",
]


def _load_existing_annotations(csv_path: Path) -> dict[str, dict]:
    """
    Read existing CSV and build a {cage_code: {jr_status, jr_notes, jr_priority}} map.

    Called before writing a new CSV to carry forward any JR annotations.
    Rows with blank or missing cage_code are skipped (unmatchable).
    Returns an empty dict if the file does not exist.
    """
    annotations: dict[str, dict] = {}
    if not csv_path.exists():
        return annotations

    try:
        with open(str(csv_path), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cage = (row.get("cage_code") or "").strip()
                if not cage:
                    continue
                jr_status   = (row.get("jr_status")   or "").strip()
                jr_notes    = (row.get("jr_notes")    or "").strip()
                jr_priority = (row.get("jr_priority") or "").strip()
                if jr_status or jr_notes or jr_priority:
                    annotations[cage] = {
                        "jr_status":   jr_status,
                        "jr_notes":    jr_notes,
                        "jr_priority": jr_priority,
                    }
    except Exception as exc:
        print(f"[WARN] Could not read existing CSV for annotation carry-forward: {exc}", file=sys.stderr)

    return annotations


def build_csv_package(date_str: str, records: list[dict], out_path: Path) -> None:
    """
    Write UTF-8-BOM CSV (QUOTE_ALL) so Excel reads it cleanly.

    B3: Award columns appended after pdf_path (see CSV_COLUMNS).
    B4: Annotation preservation — reads existing CSV before writing; carries
        forward jr_status/jr_notes/jr_priority keyed on cage_code so JR's
        annotations survive a packager re-run. See D-021.
    """
    # B4: load any existing annotations before overwriting
    annotations = _load_existing_annotations(out_path)
    if annotations:
        print(f"  [annotations] Carrying forward {len(annotations)} annotated row(s) from existing CSV")

    with codecs.open(str(out_path), "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        writer.writerow(CSV_COLUMNS)
        for rec in records:
            cage = (rec.get("cage_code") or "").strip()
            ann  = annotations.get(cage, {})

            # Award fields — blank when no sidecar was used (award_status absent)
            fa     = rec.get("first_award")  or {}
            la     = rec.get("latest_award") or {}

            writer.writerow([
                rec.get("name", ""),
                rec.get("naics", ""),
                cage,
                rec.get("business_website") or "",
                rec.get("email") or "",
                rec.get("contact_name") or "",
                rec.get("profile_pdf") or "",        # pdf_path
                # Award columns
                rec.get("award_status") or "",
                fa.get("date") or "",
                fa.get("amount") if fa.get("amount") is not None else "",
                fa.get("agency") or "",
                la.get("date") or "",
                la.get("amount") if la.get("amount") is not None else "",
                la.get("agency") or "",
                rec.get("total_awards_count") if rec.get("total_awards_count") is not None else "",
                # Profile links
                rec.get("url", ""),                  # sba_profile_url
                rec.get("sam_profile_url") or "",
                # JR annotations (preserved or blank)
                ann.get("jr_status", ""),
                ann.get("jr_notes", ""),
                ann.get("jr_priority", ""),
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
    records, source_label = load_records(date_str)
    print(f"  Loaded {len(records)} record(s) from {source_label}")

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
