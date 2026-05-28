#!/usr/bin/env python3
"""
C-SPOTTER -- SBA small business finder (Playwright edition).

Queries https://search.certifications.sba.gov/ using a headless Chromium
browser to bypass the React SPA wall that blocked the httpx-only prototype.
Searches by NAICS code, waits for the results table to hydrate, paginates,
and writes enriched records to JSONL.

Writes: research/data/candidates/spotter_<YYYY-MM-DD>.jsonl  (one JSON per line)

Record shape (v2 -- enriched):
  {name, naics, url, cage_code, business_website, email, contact_name, sam_profile_url}
  New fields are additive -- old consumers reading only {name, naics, url} are unaffected.
  Any field the profile doesn't expose is null; a per-record warning is printed.

Two modes:
  pipeline mode (default) — writes to candidates/ and logs timing via log_run.
  ad-hoc mode (--ad-hoc)  — prints results to stdout only; no file writes, no log entry.

Usage:
    # Pipeline (all 5 NAICS codes):
    python scripts/spotter_find.py
    python scripts/spotter_find.py --limit-per-naics 5

    # Pipeline (specific NAICS codes):
    python scripts/spotter_find.py 561110 561990

    # Ad-hoc exploration (stdout only, no log, no candidate file):
    python scripts/spotter_find.py --ad-hoc 561110
    python scripts/spotter_find.py --ad-hoc --limit-per-naics 2 561110 541611

    # Other options:
    python scripts/spotter_find.py --limit-per-naics 3 --headed
    python scripts/spotter_find.py --delay-seconds 2.0
    python scripts/spotter_find.py --profile-delay-seconds 2.0
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

HERE           = Path(__file__).resolve().parent.parent   # repo root
CANDIDATES_DIR = HERE / "research" / "data" / "candidates"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402

# ---------------------------------------------------------------------------
# Pipeline NAICS -- mirrors fetch_expiring.py / AGENTS.md
# ---------------------------------------------------------------------------
PIPELINE_NAICS = {
    "561110": "Office Administrative Services",
    "561990": "All Other Support Services",
    "561320": "Temporary Staffing Services",
    "541611": "Administrative Management Consulting",
    "493110": "General Warehousing & Storage",
}

CERT_BASE_URL = "https://search.certifications.sba.gov/"

# Default per-profile page delay (seconds) -- profile dive adds N extra page loads
DEFAULT_PROFILE_DELAY_SECONDS = 1.5

# Profile page: how long to wait for the page to load before scraping fields
PROFILE_WAIT_TIMEOUT_MS = 15_000

# Real Chrome 124 UA on Windows -- minimises bot-detection surface
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Selector that indicates results have hydrated
RESULTS_ROW_SELECTOR = "table tbody tr"
# Selector for the search / NAICS input field
# We'll try multiple candidate selectors and use the first one that matches
NAICS_INPUT_CANDIDATES = [
    "input[placeholder*='NAICS']",
    "input[aria-label*='NAICS']",
    "input[name*='naics']",
    "input[id*='naics']",
    "input[type='search']",
    "input[type='text']",
]

# How long to wait for the results table after submitting a search (ms)
RESULT_WAIT_TIMEOUT_MS = 15_000


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

def _find_input(page, candidates: list[str]):
    """Return the first input selector that resolves on the page, or None."""
    for sel in candidates:
        try:
            if page.locator(sel).count() > 0:
                return sel
        except Exception:
            continue
    return None


def _extract_rows(page, naics: str, limit: int, base_url: str) -> list[dict]:
    """
    Pull business records from the currently-visible results table.
    Returns up to `limit` records as {name, naics, url}.
    """
    records: list[dict] = []
    rows = page.locator(RESULTS_ROW_SELECTOR).all()

    for row in rows:
        if len(records) >= limit:
            break
        try:
            # Try to grab a link inside the row (business profile link)
            link = row.locator("a").first
            if link.count() > 0:
                name = link.inner_text().strip()
                href = link.get_attribute("href") or ""
                if href.startswith("http"):
                    url = href
                elif href.startswith("/"):
                    url = base_url.rstrip("/") + href
                else:
                    url = base_url
            else:
                # Fallback: grab first cell text as name, use base search URL
                cells = row.locator("td").all()
                if not cells:
                    continue
                name = cells[0].inner_text().strip()
                url = base_url

            if not name or name.lower() in ("", "name", "business name"):
                continue

            records.append({"name": name, "naics": naics, "url": url})
        except Exception:
            continue

    return records


def _enrich_profile(page, record: dict, errors: list[str]) -> dict:
    """
    Navigate to record["url"] (the SBA cert profile page) and extract enrichment
    fields.  Returns the record dict with new keys added:
        cage_code, business_website, email, contact_name, sam_profile_url
    All new fields default to None; per-field failures are logged and do not
    abort the record or the run.

    DOM pattern discovered 2026-05-28:
      Each field lives in a div containing an h5 label followed by a p value.
      We locate the h5 by text, then read the sibling p (or its child a).
      CSS class names are CSS-module hashed -- do not rely on them.
    """
    enriched = dict(record)
    enriched.setdefault("cage_code", None)
    enriched.setdefault("business_website", None)
    enriched.setdefault("email", None)
    enriched.setdefault("contact_name", None)
    enriched.setdefault("sam_profile_url", None)

    name = record.get("name", record.get("url", "?"))
    profile_url = record.get("url", "")
    if not profile_url:
        errors.append(f"  [enrich] {name}: no profile URL -- skipping enrichment")
        return enriched

    try:
        # The SBA cert profile is a React SPA; domcontentloaded fires before
        # React renders the profile data.  Wait for a profile-specific element
        # (an h5 inside the profile section) to confirm hydration.
        page.goto(profile_url, wait_until="domcontentloaded", timeout=PROFILE_WAIT_TIMEOUT_MS)
        page.wait_for_selector("h5", timeout=PROFILE_WAIT_TIMEOUT_MS)
    except Exception as exc:
        errors.append(f"  [enrich] {name}: failed to load profile page -- {exc}")
        return enriched

    def _read_label_value(label_text: str) -> str | None:
        """Find the h5 whose text contains label_text; return the sibling p's text."""
        try:
            h5 = page.locator(f"h5:has-text('{label_text}')").first
            if h5.count() == 0:
                return None
            # Sibling p is inside the same parent div
            p = h5.locator("xpath=../p").first
            if p.count() == 0:
                return None
            return p.inner_text().strip() or None
        except Exception:
            return None

    def _read_label_link(label_text: str, attr: str = "href") -> str | None:
        """Find the h5 by label_text; return the href on the child anchor in its sibling p."""
        try:
            h5 = page.locator(f"h5:has-text('{label_text}')").first
            if h5.count() == 0:
                return None
            a = h5.locator("xpath=../p//a").first
            if a.count() == 0:
                return None
            return a.get_attribute(attr) or None
        except Exception:
            return None

    # ---- CAGE code ----
    try:
        val = _read_label_value("CAGE code")
        enriched["cage_code"] = val
        if val is None:
            errors.append(f"  [enrich] {name}: cage_code not found on profile")
    except Exception as exc:
        errors.append(f"  [enrich] {name}: cage_code extraction error -- {exc}")

    # ---- Business website (h5 "Website" but NOT "Additional website") ----
    try:
        # Playwright text selector does a substring match; filter to exact label
        h5s = page.locator("h5").all()
        website_val = None
        for h5 in h5s:
            try:
                txt = h5.inner_text().strip()
                if txt == "Website":
                    a = h5.locator("xpath=../p//a").first
                    if a.count() > 0:
                        website_val = a.get_attribute("href") or None
                    break
            except Exception:
                continue
        enriched["business_website"] = website_val
        if website_val is None:
            errors.append(f"  [enrich] {name}: business_website not found on profile")
    except Exception as exc:
        errors.append(f"  [enrich] {name}: business_website extraction error -- {exc}")

    # ---- Email (h5 "Email address"; link is mailto:) ----
    try:
        href = _read_label_link("Email address")
        if href and href.startswith("mailto:"):
            enriched["email"] = href[len("mailto:"):]
        elif href:
            enriched["email"] = href
        else:
            enriched["email"] = None
            errors.append(f"  [enrich] {name}: email not found on profile")
    except Exception as exc:
        errors.append(f"  [enrich] {name}: email extraction error -- {exc}")

    # ---- Contact name (h5 "Contact person") ----
    try:
        val = _read_label_value("Contact person")
        enriched["contact_name"] = val
        if val is None:
            errors.append(f"  [enrich] {name}: contact_name not found on profile")
    except Exception as exc:
        errors.append(f"  [enrich] {name}: contact_name extraction error -- {exc}")

    # ---- SAM.gov profile URL (outbound link to sam.gov/entity) ----
    try:
        sam_links = page.locator("a[href*='sam.gov']").all()
        sam_url = None
        for link in sam_links:
            try:
                href = link.get_attribute("href") or ""
                # Target entity profile pages, not generic sam.gov references
                if "sam.gov" in href and (
                    "/entity/" in href or "/opp/" in href or "UEI" in href
                ):
                    sam_url = href
                    break
            except Exception:
                continue
        enriched["sam_profile_url"] = sam_url
        # sam_profile_url being None is normal -- not all profiles link out
    except Exception as exc:
        errors.append(f"  [enrich] {name}: sam_profile_url extraction error -- {exc}")

    return enriched


def _search_naics(
    page,
    naics: str,
    label: str,
    limit: int,
    errors: list[str],
) -> list[dict]:
    """
    Navigate to the SBA cert search, enter a NAICS code, wait for results,
    and extract up to `limit` businesses.  Paginates via Next button if needed.
    Returns list of {name, naics, url} dicts.
    """
    records: list[dict] = []

    try:
        page.goto(CERT_BASE_URL, wait_until="domcontentloaded", timeout=30_000)
    except Exception as exc:
        errors.append(f"NAICS {naics}: failed to load {CERT_BASE_URL} -- {exc}")
        return records

    # Check for anti-bot / captcha pages
    body_text = page.locator("body").inner_text()
    if any(kw in body_text.lower() for kw in ("captcha", "verify you are human", "access denied", "cloudflare")):
        errors.append(
            f"NAICS {naics}: anti-bot interstitial detected on page load. "
            "Saving whatever records exist and stopping gracefully."
        )
        return records

    # ---- Locate the NAICS input ----
    input_sel = _find_input(page, NAICS_INPUT_CANDIDATES)
    if not input_sel:
        # Try to find ANY visible text input as last resort
        errors.append(
            f"NAICS {naics}: could not locate NAICS search input on page. "
            "Page structure may have changed. Skipping this code."
        )
        return records

    # ---- Enter the NAICS code and search ----
    try:
        page.locator(input_sel).first.click()
        page.keyboard.press("Control+a")
        page.keyboard.type(naics)
        page.keyboard.press("Enter")
    except Exception as exc:
        errors.append(f"NAICS {naics}: error entering search term -- {exc}")
        return records

    # ---- Wait for results table to hydrate ----
    try:
        page.wait_for_selector(RESULTS_ROW_SELECTOR, timeout=RESULT_WAIT_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        # Check if it's a captcha / rate-limit page
        body_text = page.locator("body").inner_text()
        if any(kw in body_text.lower() for kw in ("captcha", "verify you are human", "access denied", "rate limit")):
            errors.append(
                f"NAICS {naics}: anti-bot / rate-limit wall after search. "
                "Saving whatever records collected so far."
            )
        else:
            errors.append(
                f"NAICS {naics}: results table selector '{RESULTS_ROW_SELECTOR}' "
                f"not found within {RESULT_WAIT_TIMEOUT_MS}ms. "
                "Page may have no results or selector changed."
            )
        return records
    except Exception as exc:
        errors.append(f"NAICS {naics}: unexpected error waiting for results -- {exc}")
        return records

    # ---- Paginate until we have `limit` records ----
    page_num = 1
    while len(records) < limit:
        batch = _extract_rows(page, naics, limit - len(records), CERT_BASE_URL)
        records.extend(batch)

        if len(records) >= limit:
            break

        # Look for a "Next" pagination button
        next_btn = page.locator("button:has-text('Next'), a:has-text('Next'), [aria-label='Next']").first
        try:
            if next_btn.count() > 0 and next_btn.is_enabled():
                next_btn.click()
                try:
                    page.wait_for_selector(RESULTS_ROW_SELECTOR, timeout=RESULT_WAIT_TIMEOUT_MS)
                    page_num += 1
                except PlaywrightTimeoutError:
                    break
            else:
                break
        except Exception:
            break

    return records[:limit]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_candidates(records: list[dict]) -> Path:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = CANDIDATES_DIR / f"spotter_{date_str}.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return out_path


# ---------------------------------------------------------------------------
# Ad-hoc output formatter
# ---------------------------------------------------------------------------

def _print_adhoc_results(records: list[dict], errors: list[str]) -> None:
    """Print results to stdout in a readable table. Used by --ad-hoc mode."""
    if not records:
        print("\n  (no results)")
    else:
        # Column widths
        col_name  = max((len(r["name"])  for r in records), default=20)
        col_naics = max((len(r["naics"]) for r in records), default=10)
        col_name  = max(col_name, 20)
        col_naics = max(col_naics, 6)

        header = f"  {'Business Name':<{col_name}}  {'NAICS':<{col_naics}}  URL"
        sep    = "  " + "-" * (col_name) + "  " + "-" * col_naics + "  " + "-" * 40
        print(header)
        print(sep)
        for r in records:
            print(f"  {r['name']:<{col_name}}  {r['naics']:<{col_naics}}  {r['url']}")

    if errors:
        print("\n  [WARNINGS]")
        for e in errors:
            print(f"    {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="C-SPOTTER: find SBA small businesses by NAICS")
    parser.add_argument(
        "naics_codes", nargs="*", metavar="NAICS",
        help=(
            "NAICS codes to search (positional). "
            "If omitted, uses the 5 pipeline codes. "
            "Example: 561110 541611"
        ),
    )
    parser.add_argument(
        "--ad-hoc", action="store_true",
        help=(
            "Ad-hoc mode: print results to stdout only. "
            "Skips writing to candidates/ and skips log_run. "
            "Use for one-off exploration without polluting pipeline artifacts."
        ),
    )
    parser.add_argument(
        "--limit-per-naics", type=int, default=10,
        help="Max businesses per NAICS code (default: 10)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run with visible browser window (for debugging)",
    )
    parser.add_argument(
        "--delay-seconds", type=float, default=1.5,
        help="Seconds to wait between NAICS code searches (default: 1.5)",
    )
    parser.add_argument(
        "--profile-delay-seconds", type=float, default=DEFAULT_PROFILE_DELAY_SECONDS,
        help=(
            f"Seconds to wait between individual profile page dives during enrichment "
            f"(default: {DEFAULT_PROFILE_DELAY_SECONDS}). "
            "Use 0 to disable."
        ),
    )
    args = parser.parse_args()

    # ---- Resolve NAICS target set ----
    if args.naics_codes:
        # Positional args: build label map, unknown codes get their code as label
        naics_items = [(code, PIPELINE_NAICS.get(code, code)) for code in args.naics_codes]
    else:
        naics_items = list(PIPELINE_NAICS.items())

    started_at  = datetime.now(timezone.utc)
    all_records: list[dict] = []
    all_errors:  list[str]  = []

    mode_label = "ad-hoc" if args.ad_hoc else "pipeline"
    print(
        f"C-SPOTTER [{mode_label}]: querying SBA cert search for {len(naics_items)} NAICS code(s) "
        f"(limit {args.limit_per_naics}/code, {'headed' if args.headed else 'headless'}, "
        f"profile-delay {args.profile_delay_seconds}s)"
    )

    # ---- Launch Playwright ----
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Stealth: remove webdriver property (basic anti-detection)
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        for i, (naics, label) in enumerate(naics_items, 1):
            print(f"  [{i}/{len(naics_items)}] {naics} -- {label}")
            records = _search_naics(page, naics, label, args.limit_per_naics, all_errors)
            all_records.extend(records)
            status_str = f"{len(records)} businesses" if records else "0 (see errors)"
            print(f"    {status_str}")

            # Print any new errors for this NAICS
            if all_errors:
                new_errs = [e for e in all_errors if naics in e]
                for e in new_errs:
                    print(f"    [WARN] {e}")

            # Bail early if we hit a persistent anti-bot wall
            anti_bot_wall = any(
                "anti-bot" in e or "captcha" in e or "rate-limit" in e
                for e in all_errors
            )
            if anti_bot_wall:
                print("  [STOP] Anti-bot / captcha wall detected -- stopping early and saving partial results.")
                all_errors.append("Stopped early due to anti-bot wall.")
                break

            # Delay between NAICS codes
            if i < len(naics_items):
                time.sleep(args.delay_seconds)

        # ---- Profile enrichment pass ----
        # Navigate to each business's SBA cert profile to pull additional fields.
        # Fail-soft per field: missing data logs a warning; never aborts the run.
        if all_records:
            print(f"\nC-SPOTTER [enrich]: diving {len(all_records)} profile(s) "
                  f"(delay {args.profile_delay_seconds}s between each)")
            enrich_errors: list[str] = []
            enriched_records: list[dict] = []
            for j, rec in enumerate(all_records, 1):
                print(f"  [{j}/{len(all_records)}] {rec['name'][:60]}")
                enriched = _enrich_profile(page, rec, enrich_errors)
                enriched_records.append(enriched)

                # Print per-record enrichment gap warnings inline
                for gap_warn in enrich_errors[-(len(enrich_errors)):]:
                    if rec["name"][:20] in gap_warn or "[enrich]" in gap_warn:
                        pass  # already visible in enrich_errors accumulation

                if j < len(all_records) and args.profile_delay_seconds > 0:
                    time.sleep(args.profile_delay_seconds)

            all_records = enriched_records
            all_errors.extend(enrich_errors)
            if enrich_errors:
                print(f"  [enrich] {len(enrich_errors)} gap warning(s) (null fields) -- see log")

        context.close()
        browser.close()

    # ---- Output -- diverges by mode ----
    if args.ad_hoc:
        print(f"\nAd-hoc results ({len(all_records)} total):")
        _print_adhoc_results(all_records, all_errors)
        # No file write. No log_run entry.
    else:
        out_path = write_candidates(all_records)
        print(f"\nTotal: {len(all_records)} candidates -> {out_path}")
        if not all_records:
            print("[INFO] Zero records -- check errors above.")
        log_run(
            "c-spotter",
            started_at,
            record_count=len(all_records),
            errors=all_errors if all_errors else None,
        )


if __name__ == "__main__":
    main()
