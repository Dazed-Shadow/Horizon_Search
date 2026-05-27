#!/usr/bin/env python3
"""
C-SPOTTER -- SBA small business finder (Playwright edition).

Queries https://search.certifications.sba.gov/ using a headless Chromium
browser to bypass the React SPA wall that blocked the httpx-only prototype.
Searches by NAICS code, waits for the results table to hydrate, paginates,
and writes {name, naics, url} records to JSONL.

Writes: research/data/candidates/spotter_<YYYY-MM-DD>.jsonl  (one JSON per line)

Usage:
    python scripts/spotter_find.py
    python scripts/spotter_find.py --limit-per-naics 5
    python scripts/spotter_find.py --limit-per-naics 3 --headed
    python scripts/spotter_find.py --delay-seconds 2.0
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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="C-SPOTTER: find SBA small businesses by NAICS")
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
    args = parser.parse_args()

    started_at  = datetime.now(timezone.utc)
    all_records: list[dict] = []
    all_errors:  list[str]  = []

    print(
        f"C-SPOTTER: querying SBA cert search for {len(PIPELINE_NAICS)} NAICS codes "
        f"(limit {args.limit_per_naics}/code, {'headed' if args.headed else 'headless'})"
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

        naics_items = list(PIPELINE_NAICS.items())
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

        context.close()
        browser.close()

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
