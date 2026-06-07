#!/usr/bin/env python3
"""
spotter_ownership.py — SBA PDF ownership flag extraction for C-SPOTTER.

Reads spotter_<date>_enriched.jsonl if present, otherwise spotter_<date>_awards.jsonl.
For each record with a profile_pdf path, extracts text from the PDF and regex-scans
for SBA certification ownership flags. Writes results to spotter_<date>_enriched.jsonl
(creates or merges — does not overwrite fields written by prior passes like
spotter_classify.py).

Output field added per record:
  ownership -- {
    woman_owned:                     bool,
    veteran_owned:                   bool,
    service_disabled_veteran_owned:  bool,
    minority_owned:                  bool,
    hubzone:                         bool,
    "8a":                            bool,
    raw_phrases:                     [str]   # matched phrase(s) for audit
  }
  or null if PDF missing/corrupt/unreadable.

Phrase patterns (case-insensitive):
  woman_owned                  -- Woman.Owned | Women.Owned
  veteran_owned                -- Veteran.Owned (excluding Service-Disabled Veteran)
  service_disabled_veteran_owned -- Service.Disabled Veteran
  minority_owned               -- Minority.Owned
  hubzone                      -- HUBZone
  "8a"                         -- 8.a\\b | Section 8.a.

Usage:
    python scripts/spotter_ownership.py --date 2026-05-29
    python scripts/spotter_ownership.py --date 2026-05-29 --limit 5
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

DEFAULT_DELAY = 0.1   # PDF extraction is local; short delay is just for log pacing


# ---------------------------------------------------------------------------
# Ownership phrase patterns
# ---------------------------------------------------------------------------

# Each entry: (flag_key, compiled_pattern)
# Order matters for veteran_owned — we check service_disabled first so the
# "Veteran.Owned" pattern doesn't fire for "Service-Disabled Veteran Owned" records.
OWNERSHIP_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Service-Disabled Veteran must come BEFORE veteran_owned
    (
        "service_disabled_veteran_owned",
        re.compile(r"service[\s\-]+disabled\s+veteran", re.IGNORECASE),
    ),
    (
        "veteran_owned",
        # Match "Veteran-Owned" / "Veteran Owned" but NOT "Service-Disabled Veteran..."
        # We post-filter below by excluding matches that sit inside a service-disabled phrase.
        re.compile(r"veteran[\s\-]+owned", re.IGNORECASE),
    ),
    (
        "woman_owned",
        re.compile(r"wo?men[\s\-]+owned", re.IGNORECASE),
    ),
    (
        "minority_owned",
        re.compile(r"minority[\s\-]+owned", re.IGNORECASE),
    ),
    (
        "hubzone",
        re.compile(r"hubzone", re.IGNORECASE),
    ),
    (
        "8a",
        re.compile(r"\b8[\s\-]?a\b|section\s+8[\s\-]?a", re.IGNORECASE),
    ),
]

# Used to suppress veteran_owned when it fires inside a service-disabled phrase
SERVICE_DISABLED_RE = re.compile(r"service[\s\-]+disabled\s+veteran", re.IGNORECASE)


# ---------------------------------------------------------------------------
# JSONL helpers — sidecar read/write with field-merge semantics
# ---------------------------------------------------------------------------

def _load_enriched(date_str: str) -> tuple[list[dict], str]:
    """
    Load the best available input file for the given date.
    Cascade: _enriched.jsonl → _awards.jsonl → .jsonl
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
# PDF text extraction
# ---------------------------------------------------------------------------

def _extract_pdf_text(pdf_path: Path, errors: list[str], record_name: str) -> str | None:
    """
    Extract all text from a PDF file using pypdf.
    Returns concatenated page text, or None on any failure (fail-soft).
    """
    if not PYPDF_AVAILABLE:
        errors.append(f"[ownership] {record_name}: pypdf not installed — cannot extract PDF text")
        return None

    if not pdf_path.exists():
        errors.append(f"[ownership] {record_name}: PDF file not found — {pdf_path}")
        return None

    try:
        reader = PdfReader(str(pdf_path))
        pages_text: list[str] = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
                pages_text.append(text)
            except Exception as page_exc:
                # Page extraction failure — skip page, continue
                errors.append(
                    f"[ownership] {record_name}: page extraction error ({pdf_path.name}) — {page_exc}"
                )
        return "\n".join(pages_text) if pages_text else ""

    except Exception as exc:
        errors.append(f"[ownership] {record_name}: PDF parse error ({pdf_path.name}) — {exc}")
        return None


# ---------------------------------------------------------------------------
# Ownership extraction
# ---------------------------------------------------------------------------

def _extract_ownership(text: str) -> dict:
    """
    Regex-scan PDF text for ownership/certification flags.

    Returns the ownership dict with bool flags and raw_phrases for audit.
    """
    flags: dict[str, bool] = {
        "woman_owned":                    False,
        "veteran_owned":                  False,
        "service_disabled_veteran_owned": False,
        "minority_owned":                 False,
        "hubzone":                        False,
        "8a":                             False,
    }
    raw_phrases: list[str] = []

    for flag_key, pattern in OWNERSHIP_PATTERNS:
        for match in pattern.finditer(text):
            matched_text = match.group(0)

            # Special case: suppress veteran_owned when it overlaps with
            # a service-disabled veteran phrase in surrounding context.
            if flag_key == "veteran_owned":
                # Get 60-char window before the match
                start = max(0, match.start() - 60)
                context = text[start: match.end()]
                if SERVICE_DISABLED_RE.search(context):
                    # This "veteran-owned" match is part of a service-disabled phrase
                    continue

            flags[flag_key] = True
            if matched_text not in raw_phrases:
                raw_phrases.append(matched_text)

    return {**flags, "raw_phrases": raw_phrases}


# ---------------------------------------------------------------------------
# Per-record processing
# ---------------------------------------------------------------------------

def _process_record(rec: dict, errors: list[str]) -> dict:
    """
    Extract ownership flags from the record's profile_pdf.
    Sets rec["ownership"] to the ownership dict or null on failure.
    Returns the updated record.
    """
    out = dict(rec)
    name      = rec.get("name", "?")
    pdf_rel   = rec.get("profile_pdf")

    if not pdf_rel:
        out["ownership"] = None
        return out

    pdf_path = HERE / pdf_rel

    text = _extract_pdf_text(pdf_path, errors, name)
    if text is None:
        out["ownership"] = None
        return out

    if not text.strip():
        # PDF parsed OK but yielded no text (e.g. scanned image PDF)
        errors.append(f"[ownership] {name}: PDF yielded no extractable text ({pdf_path.name})")
        out["ownership"] = None
        return out

    ownership = _extract_ownership(text)
    out["ownership"] = ownership

    # Summary line for stdout
    active_flags = [k for k, v in ownership.items() if k != "raw_phrases" and v is True]
    if active_flags:
        print(f"    flags: {', '.join(active_flags)}")
        print(f"    raw:   {ownership['raw_phrases']}")
    else:
        print(f"    flags: (none found)")

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not PYPDF_AVAILABLE:
        print(
            "[ERROR] pypdf is not installed. Run: pip install 'pypdf>=5.0.0'",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="C-SPOTTER-OWNERSHIP: extract ownership flags from SBA profile PDFs"
    )
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        metavar="YYYY-MM-DD",
        help="Date of the spotter JSONL to process (default: today)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        metavar="N",
        help="Process only the first N records (default: all; useful for testing)",
    )
    args = parser.parse_args()

    date_str = args.date
    limit    = args.limit

    records, source_name = _load_enriched(date_str)

    if limit is not None:
        records = records[:limit]

    print(
        f"C-SPOTTER-OWNERSHIP: processing {len(records)} record(s) from {source_name}"
    )

    started_at  = datetime.now(timezone.utc)
    errors:     list[str] = []
    processed:  list[dict] = []

    for i, rec in enumerate(records, 1):
        name    = rec.get("name", f"record #{i}")
        pdf_rel = rec.get("profile_pdf") or "(no PDF)"
        print(f"  [{i}/{len(records)}] {name[:55]}  →  {pdf_rel}")

        out = _process_record(rec, errors)
        processed.append(out)

    # Write sidecar
    out_path = _write_enriched(date_str, processed)

    # Summary stats
    null_count  = sum(1 for r in processed if r.get("ownership") is None)
    found_count = sum(1 for r in processed if r.get("ownership") and any(
        v for k, v in r["ownership"].items() if k != "raw_phrases" and v is True
    ))
    clean_count = len(processed) - null_count - found_count

    print(f"\nC-SPOTTER-OWNERSHIP: done.")
    print(f"  Records with flags:      {found_count}")
    print(f"  Records no flags found:  {clean_count}")
    print(f"  Records null (no PDF):   {null_count}")
    print(f"  Enriched → {out_path}  ({out_path.stat().st_size:,} bytes)")

    log_run(
        "c-spotter-ownership",
        started_at,
        record_count=len(processed),
        errors=errors if errors else None,
    )


if __name__ == "__main__":
    main()
