#!/usr/bin/env python3
"""
spotter_classify.py — Website fetch + design-quality classification for C-SPOTTER.

Reads spotter_<date>_enriched.jsonl if present, otherwise spotter_<date>_awards.jsonl.
For each record with a business_website URL, fetches the site and populates four new
fields per record:

  what_they_do      -- 1-2 sentence plain-language summary from <title>, <meta description>,
                       first <h1>, first prominent <p>
  design_quality    -- "clean" | "dated" | "broken" | "no-site"
  geographic_scope  -- "local" | "regional" | "national" | "unknown"
  tech_signals      -- {generator, has_ssl, has_viewport, framework_hint}

Output is written to spotter_<date>_enriched.jsonl (creates or extends without overwriting
fields written by a prior pass, e.g. ownership from spotter_ownership.py).

Classification rubric (design_quality):
  no-site  -- business_website is null OR HTTP fails to connect
  broken   -- HTTP 4xx/5xx, OR 200 but body < 200 chars
  clean    -- has <meta name="viewport"> AND https AND at least one external CSS link
              AND no legacy-generator signal ("FrontPage", "Microsoft FrontPage", etc.)
  dated    -- everything else that loaded (default fallback)

Geographic scope heuristic:
  - "nationwide" / "across the country" / "serving the US" / "serving the united states" → national
  - "tri-state" / "northeast" / "pacific northwest" / "southeast" / "midwest" / "serving the region"
    / "serving [2+ named regions]" → regional
  - Count distinct US state name mentions; if one state dominates → local
  - No location signals → unknown

Usage:
    python scripts/spotter_classify.py --date 2026-05-29
    python scripts/spotter_classify.py --date 2026-05-29 --limit 5
    python scripts/spotter_classify.py --date 2026-05-29 --delay-seconds 2.0
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# Force UTF-8 stdout on Windows (default cp1252 crashes on emoji/arrow chars)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE           = Path(__file__).resolve().parent.parent   # repo root
CANDIDATES_DIR = HERE / "research" / "data" / "candidates"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Real Chrome 124 UA — matches spotter_find.py
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_DELAY   = 1.5
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT    = 10.0

# Legacy generator signals → "dated"
LEGACY_GENERATORS = re.compile(
    r"(FrontPage|Microsoft FrontPage|Adobe GoLive|Dreamweaver|NetObjects|"
    r"Microsoft Publisher|WebPlus|CoffeeCup|SiteBuilder)", re.IGNORECASE
)

# Framework hints from asset URL patterns
FRAMEWORK_PATTERNS = [
    (re.compile(r"wp-content|wp-includes|wordpress", re.IGNORECASE), "WordPress"),
    (re.compile(r"wix\.com|wixstatic|wixsite", re.IGNORECASE), "Wix"),
    (re.compile(r"squarespace", re.IGNORECASE), "Squarespace"),
    (re.compile(r"shopify", re.IGNORECASE), "Shopify"),
    (re.compile(r"webflow\.io|webflow\.com", re.IGNORECASE), "Webflow"),
    (re.compile(r"godaddy|godaddysites", re.IGNORECASE), "GoDaddy"),
]

# US state names (full names, lowercase) for geographic scope
US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
}

# State abbreviations (2-letter uppercase) — only use when isolated as words
US_STATE_ABBREVS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

# National scope signals (case-insensitive)
NATIONAL_PATTERNS = re.compile(
    r"\b(nationwide|nation.?wide|across the country|serving the us\b|"
    r"serving the united states|national(ly)?\b|all 50 states|"
    r"coast.to.coast)\b",
    re.IGNORECASE,
)

# Regional scope signals
REGIONAL_PATTERNS = re.compile(
    r"\b(tri.state|northeast|pacific northwest|pacific north west|"
    r"southeast|south east|midwest|mid.west|southwest|south west|northwest|"
    r"new england|mid.atlantic|serving the region|serving our region|"
    r"gulf coast|great plains|mountain west|rocky mountain)\b",
    re.IGNORECASE,
)

# Minimum body length to count as "loaded" (not broken)
MIN_BODY_CHARS = 200

# Minimum paragraph length to be considered "prominent"
MIN_PARA_CHARS = 50


# ---------------------------------------------------------------------------
# JSONL helpers — sidecar read/write with field-merge semantics
# ---------------------------------------------------------------------------

def _load_enriched(date_str: str) -> tuple[list[dict], str]:
    """
    Load the best available input file for the given date.

    Cascade: _enriched.jsonl → _awards.jsonl → .jsonl
    Returns (records, source_path_name).
    """
    candidates = [
        CANDIDATES_DIR / f"spotter_{date_str}_enriched.jsonl",
        CANDIDATES_DIR / f"spotter_{date_str}_awards.jsonl",
        CANDIDATES_DIR / f"spotter_{date_str}.jsonl",
    ]
    for path in candidates:
        if path.exists():
            records = []
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        print(f"[WARN] Line {lineno} not valid JSON — skipping: {exc}", file=sys.stderr)
            return records, path.name
    print(
        f"[ERROR] No input file found for {date_str}. "
        "Tried: " + ", ".join(p.name for p in candidates),
        file=sys.stderr,
    )
    sys.exit(1)


def _write_enriched(date_str: str, records: list[dict]) -> Path:
    """Write (or overwrite) the _enriched.jsonl sidecar."""
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"spotter_{date_str}_enriched.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out_path


# ---------------------------------------------------------------------------
# Classify helpers
# ---------------------------------------------------------------------------

def _extract_what_they_do(soup: BeautifulSoup) -> str:
    """
    Extract a 1-2 sentence plain-language summary of what the business does.
    Priority: <meta description> → <h1> → first prominent <p> → <title>.
    Falls back gracefully if all are empty.
    """
    # 1. Meta description
    meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.IGNORECASE)})
    if meta_desc:
        content = (meta_desc.get("content") or "").strip()
        if len(content) > 20:
            # Truncate to ~200 chars at sentence boundary
            return _truncate_to_sentences(content, 200)

    # 2. First <h1>
    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(" ", strip=True)
        if len(h1_text) > 5:
            # Combine with first prominent <p>
            p_text = _first_prominent_p(soup, min_chars=MIN_PARA_CHARS)
            if p_text:
                combined = f"{h1_text}. {p_text}"
                return _truncate_to_sentences(combined, 200)
            return _truncate_to_sentences(h1_text, 200)

    # 3. First prominent <p>
    p_text = _first_prominent_p(soup, min_chars=MIN_PARA_CHARS)
    if p_text:
        return _truncate_to_sentences(p_text, 200)

    # 4. Title fallback
    title = soup.find("title")
    if title:
        title_text = title.get_text(" ", strip=True)
        if len(title_text) > 5:
            return title_text[:200]

    return ""


def _first_prominent_p(soup: BeautifulSoup, min_chars: int) -> str:
    """Return the first <p> tag with text length >= min_chars."""
    # Skip paragraphs inside nav, header footer, aside
    noise_parents = {"nav", "header", "footer", "aside", "script", "style"}
    for p in soup.find_all("p"):
        # Check if any ancestor is a noise element
        skip = False
        for parent in p.parents:
            if getattr(parent, "name", None) in noise_parents:
                skip = True
                break
        if skip:
            continue
        text = p.get_text(" ", strip=True)
        if len(text) >= min_chars:
            return text
    return ""


def _truncate_to_sentences(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, preferring sentence boundaries."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Find last sentence boundary
    last_period = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
    if last_period > max_chars // 2:
        return truncated[: last_period + 1].strip()
    return truncated.rstrip(".,:;") + "…"


def _detect_framework(html_str: str, soup: BeautifulSoup) -> Optional[str]:
    """Detect CMS/framework from asset URL patterns in page source."""
    # Check full HTML source for URL patterns
    for pattern, name in FRAMEWORK_PATTERNS:
        if pattern.search(html_str):
            return name
    return None


def _classify_design_quality(
    url: str,
    html_body: str,
    soup: BeautifulSoup,
    http_status: int,
) -> str:
    """
    Classify design quality into clean / dated / broken / no-site.

    Rubric:
      broken — HTTP 4xx/5xx OR body < MIN_BODY_CHARS
      clean  — has viewport meta AND https AND external CSS AND no legacy generator
      dated  — default fallback (loaded but not clearly clean)
    """
    if http_status >= 400:
        return "broken"
    if len(html_body) < MIN_BODY_CHARS:
        return "broken"

    # Check for legacy generator
    generator_meta = soup.find("meta", attrs={"name": re.compile(r"^generator$", re.IGNORECASE)})
    generator_str = ""
    if generator_meta:
        generator_str = (generator_meta.get("content") or "").strip()
    if LEGACY_GENERATORS.search(generator_str):
        return "dated"

    # Clean requires: viewport + https + external CSS
    has_viewport = bool(soup.find("meta", attrs={"name": re.compile(r"viewport", re.IGNORECASE)}))
    has_https = url.startswith("https://") or url.startswith("https:")
    # External CSS: <link rel="stylesheet" href="..."> with an http/https href or absolute path
    external_css_links = [
        tag for tag in soup.find_all("link", rel=lambda r: r and "stylesheet" in r)
        if (tag.get("href") or "").startswith(("http", "//", "/"))
    ]
    has_external_css = len(external_css_links) > 0

    if has_viewport and has_https and has_external_css:
        return "clean"

    return "dated"


def _classify_geographic_scope(text: str) -> str:
    """
    Classify geographic scope from page body text.

    Returns: "local" | "regional" | "national" | "unknown"
    """
    text_lower = text.lower()

    # National first (strongest signal)
    if NATIONAL_PATTERNS.search(text_lower):
        return "national"

    # Regional
    if REGIONAL_PATTERNS.search(text_lower):
        return "regional"

    # Count distinct state mentions
    # Full state names
    state_mentions: set[str] = set()
    for state in US_STATES:
        # Use word boundary pattern
        pattern = r"\b" + re.escape(state) + r"\b"
        if re.search(pattern, text_lower):
            state_mentions.add(state)

    # Also check abbreviations (uppercase, isolated as words)
    abbrev_pattern = re.compile(r"\b([A-Z]{2})\b")
    for match in abbrev_pattern.finditer(text):
        abbrev = match.group(1)
        if abbrev in US_STATE_ABBREVS:
            # Map back to state name (we just need count)
            state_mentions.add(abbrev.lower())

    if len(state_mentions) == 0:
        return "unknown"
    if len(state_mentions) == 1:
        return "local"
    if len(state_mentions) >= 5:
        # 5+ distinct states mentioned → regional or national; lean regional unless
        # national signals already fired above
        return "regional"
    # 2-4 states — still local/regional; treat as local unless pattern says otherwise
    return "local"


def _build_tech_signals(
    url: str,
    soup: BeautifulSoup,
    html_str: str,
) -> dict:
    """Build the tech_signals dict."""
    # Generator
    generator_meta = soup.find("meta", attrs={"name": re.compile(r"^generator$", re.IGNORECASE)})
    generator = None
    if generator_meta:
        generator = (generator_meta.get("content") or "").strip() or None

    # SSL
    has_ssl = url.startswith("https://") or url.startswith("https:")

    # Viewport
    has_viewport = bool(soup.find("meta", attrs={"name": re.compile(r"viewport", re.IGNORECASE)}))

    # Framework hint
    framework_hint = _detect_framework(html_str, soup)

    return {
        "generator":       generator,
        "has_ssl":         has_ssl,
        "has_viewport":    has_viewport,
        "framework_hint":  framework_hint,
    }


# ---------------------------------------------------------------------------
# Per-business classification
# ---------------------------------------------------------------------------

def _classify_business(rec: dict, client: httpx.Client, errors: list[str]) -> dict:
    """
    Fetch business_website and classify it. Returns updated record dict.
    All new fields are set even on failure (fail-soft).
    """
    out = dict(rec)
    name = rec.get("name", "?")
    url = rec.get("business_website")

    # Default all new fields — will be overwritten on success
    out.setdefault("what_they_do", "")
    out.setdefault("design_quality", "no-site")
    out.setdefault("geographic_scope", "unknown")
    out.setdefault("tech_signals", {"generator": None, "has_ssl": False, "has_viewport": False, "framework_hint": None})

    if not url:
        out["design_quality"] = "no-site"
        out["what_they_do"] = ""
        out["geographic_scope"] = "unknown"
        out["tech_signals"] = {"generator": None, "has_ssl": False, "has_viewport": False, "framework_hint": None}
        return out

    # Normalize URL — ensure it has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        response = client.get(
            url,
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=5.0, pool=5.0),
            follow_redirects=True,
        )
        html_body = response.text
        http_status = response.status_code

        # Update URL to final (post-redirect) URL for SSL check
        final_url = str(response.url)

        soup = BeautifulSoup(html_body, "html.parser")

        out["what_they_do"]      = _extract_what_they_do(soup)
        out["design_quality"]    = _classify_design_quality(final_url, html_body, soup, http_status)
        out["geographic_scope"]  = _classify_geographic_scope(soup.get_text(" ", strip=True))
        out["tech_signals"]      = _build_tech_signals(final_url, soup, html_body)

        print(
            f"    quality={out['design_quality']:<8}  scope={out['geographic_scope']:<10}  "
            f"ssl={out['tech_signals']['has_ssl']}  viewport={out['tech_signals']['has_viewport']}  "
            f"fw={out['tech_signals']['framework_hint'] or '—'}"
        )

    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TooManyRedirects) as exc:
        msg = f"[classify] {name}: connection failed — {type(exc).__name__}: {exc}"
        errors.append(msg)
        print(f"    [WARN] {msg}")
        out["design_quality"] = "broken"

    except Exception as exc:
        msg = f"[classify] {name}: unexpected error — {type(exc).__name__}: {exc}"
        errors.append(msg)
        print(f"    [WARN] {msg}")
        out["design_quality"] = "broken"

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="C-SPOTTER-CLASSIFY: fetch + classify business websites for design quality"
    )
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        metavar="YYYY-MM-DD",
        help="Date of the spotter JSONL to process (default: today)",
    )
    parser.add_argument(
        "--delay-seconds", type=float, default=DEFAULT_DELAY,
        metavar="F",
        help=f"Polite delay between website fetches in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        metavar="N",
        help="Process only the first N records (default: all; useful for testing)",
    )
    args = parser.parse_args()

    date_str = args.date
    delay    = args.delay_seconds
    limit    = args.limit

    records, source_name = _load_enriched(date_str)

    if limit is not None:
        records = records[:limit]

    print(
        f"C-SPOTTER-CLASSIFY: classifying {len(records)} record(s) from {source_name} "
        f"(delay {delay}s between fetches)"
    )

    started_at  = datetime.now(timezone.utc)
    errors:     list[str] = []
    classified: list[dict] = []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    with httpx.Client(headers=headers) as client:
        for i, rec in enumerate(records, 1):
            name    = rec.get("name", f"record #{i}")
            url     = rec.get("business_website") or "(no website)"
            print(f"  [{i}/{len(records)}] {name[:55]}  →  {url[:60]}")

            out = _classify_business(rec, client, errors)
            classified.append(out)

            if i < len(records) and rec.get("business_website"):
                time.sleep(delay)

    # Write sidecar
    out_path = _write_enriched(date_str, classified)

    # Summary stats
    by_quality: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for r in classified:
        dq = r.get("design_quality", "?")
        gs = r.get("geographic_scope", "?")
        by_quality[dq] = by_quality.get(dq, 0) + 1
        by_scope[gs]   = by_scope.get(gs, 0) + 1

    quality_str = "  ".join(f"{k}={v}" for k, v in sorted(by_quality.items()))
    scope_str   = "  ".join(f"{k}={v}" for k, v in sorted(by_scope.items()))
    print(f"\nC-SPOTTER-CLASSIFY: done.")
    print(f"  Design quality: {quality_str}")
    print(f"  Geo scope:      {scope_str}")
    print(f"  Enriched → {out_path}  ({out_path.stat().st_size:,} bytes)")

    log_run(
        "c-spotter-classify",
        started_at,
        record_count=len(classified),
        errors=errors if errors else None,
    )


if __name__ == "__main__":
    main()
