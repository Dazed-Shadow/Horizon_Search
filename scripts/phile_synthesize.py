#!/usr/bin/env python3
"""
C-Phile -- voice synthesis PREP agent.

Builds self-contained synthesis bundles (one markdown file per article) that
a Claude Code session can consume. Synthesis itself runs on JR's Claude Code
subscription, not on a metered Anthropic API key.

Inputs:
  research/data/inbox/*.jsonl   -- C-Transit output (picks most recent file)
  G:/My Drive/AI GEN/Weaving I am Content.docx   -- voice reference (override with --voice)

Output:
  research/data/drafts/_pending/phile_<timestamp>_<NN>.md  (one per article)
    -- complete prompt: voice excerpt + article + task + output spec
    -- ready to be consumed by either:
       (Option A) a scheduled Claude Code agent that watches _pending/
       (Option B) JR opening the file in an interactive Claude Code session

Consumer writes finished drafts to research/data/drafts/_done/ and moves the
bundle to research/data/drafts/_consumed/.

Usage:
    python scripts/phile_synthesize.py
    python scripts/phile_synthesize.py --count 5
    python scripts/phile_synthesize.py --voice "G:/path/to/voice.docx"

See Central Hub: pipeline/DECISIONS.md (D-006, D-009) and pipeline/AGENTS.md (C-Phile)
for the rationale behind the prep/consume split and batch mode.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE         = Path(__file__).resolve().parent.parent   # repo root
INBOX_DIR    = HERE / "research" / "data" / "inbox"
DRAFTS_DIR   = HERE / "research" / "data" / "drafts"
PENDING_DIR  = DRAFTS_DIR / "_pending"
CONSUMED_DIR = DRAFTS_DIR / "_consumed"

DEFAULT_VOICE_DOC = Path("G:/My Drive/AI GEN/Weaving I am Content.docx")

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402


# ---------------------------------------------------------------------------
# Read voice doc (python-docx)
# ---------------------------------------------------------------------------
def read_voice_doc(path: Path) -> tuple[str, list[str]]:
    """Return (text, errors). On failure returns empty string + error."""
    errors: list[str] = []
    try:
        from docx import Document  # type: ignore
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text, errors
    except FileNotFoundError:
        errors.append(f"Voice doc not found: {path}")
        return "", errors
    except Exception as exc:
        errors.append(f"Failed to read voice doc: {exc}")
        return "", errors


# ---------------------------------------------------------------------------
# Cross-batch dedupe — scan _consumed/ for previously-synthesized URLs
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"\*\*URL:\*\*\s*(.+)")


def load_consumed_urls() -> set[str]:
    """Scan _consumed/*.md bundles and return a set of all previously-synthesized URLs.

    Uses the same narrow-to-Source-article approach as phile_package.py to avoid
    false matches in voice reference text or GEM template embedded in the bundle.
    """
    consumed: set[str] = []
    if not CONSUMED_DIR.exists():
        return set()
    for path in CONSUMED_DIR.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Narrow search to ## Source article section only
        sec_match = re.search(
            r"## Source article(.*?)(?=^##|\Z)", text, re.DOTALL | re.MULTILINE
        )
        search_text = sec_match.group(1) if sec_match else text
        m = _URL_RE.search(search_text)
        if m:
            url = m.group(1).strip()
            if url and not url.startswith("["):
                consumed.append(url)
    return set(consumed)


# ---------------------------------------------------------------------------
# Pick articles from today's inbox files, round-robin by category
# ---------------------------------------------------------------------------
def pick_articles(count: int, allow_duplicates: bool = False) -> tuple[list[dict], list[str]]:
    """
    Return (article_list, errors). List may be shorter than count if inbox is thin.

    Reads all today's inbox JSONLs (glob inbox/*_<YYYY-MM-DD>.jsonl), dedupes
    by URL across files, then round-robins across categories until count is
    reached or all categories are exhausted.

    Falls back to all .jsonl files modified in the last 24 hours if the
    date-glob yields nothing (e.g. when running just after midnight UTC).

    Cross-batch dedupe: unless allow_duplicates=True, articles whose URL already
    appears in any _consumed/*.md bundle are excluded from the candidate pool.
    """
    import time as _time

    errors: list[str] = []

    # --- cross-batch dedupe ---
    if allow_duplicates:
        consumed_urls: set[str] = set()
    else:
        consumed_urls = load_consumed_urls()

    # --- locate today's files ---
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_files = sorted(INBOX_DIR.glob(f"*_{today_str}.jsonl"))

    if not date_files:
        # Fallback: any .jsonl modified within the last 24 h
        cutoff = _time.time() - 86400
        date_files = [
            p for p in INBOX_DIR.glob("*.jsonl")
            if p.stat().st_mtime >= cutoff
        ]
        if date_files:
            print(f"  [INFO] No date-stamped files for {today_str}; "
                  f"using {len(date_files)} file(s) modified in last 24h.")

    if not date_files:
        all_files = sorted(INBOX_DIR.glob("*.jsonl"))
        if not all_files:
            errors.append(f"No .jsonl files found in {INBOX_DIR}")
            return [], errors
        # Last resort: single most-recent file (original behavior)
        date_files = [all_files[-1]]
        print(f"  [INFO] Falling back to most-recent inbox file: {date_files[0].name}")

    # --- load all records, deduping by URL (within-batch) ---
    seen_urls: set[str] = set()
    excluded_count: int = 0
    by_category: dict[str, list[dict]] = {}

    for path in date_files:
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        article = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"Skipped malformed JSON line in {path.name}: {exc}")
                        continue
                    url = article.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    # cross-batch dedupe
                    if url in consumed_urls:
                        excluded_count += 1
                        continue
                    cat = article.get("category", "uncategorized")
                    by_category.setdefault(cat, []).append(article)
        except Exception as exc:
            errors.append(f"Failed to read inbox file {path}: {exc}")

    if excluded_count:
        print(f"  [INFO] Excluded {excluded_count} already-consumed URL(s) from picker pool.")

    if not by_category:
        errors.append("All inbox files were empty or had no valid records")
        return [], errors

    total_available = sum(len(v) for v in by_category.values())
    categories = sorted(by_category.keys())   # stable alphabetical order
    # index pointers per category (how many we've already consumed)
    pointers: dict[str, int] = {c: 0 for c in categories}

    # --- round-robin pick ---
    articles: list[dict] = []
    while len(articles) < count:
        added_this_round = 0
        for cat in categories:
            if len(articles) >= count:
                break
            idx = pointers[cat]
            pool = by_category[cat]
            if idx >= len(pool):
                continue   # this category is exhausted
            articles.append(pool[idx])
            pointers[cat] += 1
            added_this_round += 1
        if added_this_round == 0:
            # all categories exhausted
            break

    if not articles:
        errors.append("All inbox articles were consumed before any could be selected")
    elif len(articles) < count:
        errors.append(
            f"Inbox only had {total_available} article(s) across "
            f"{len(categories)} category(ies) (requested {count}). "
            "Run C-Transit to refresh the inbox."
        )
        print(f"  [WARN] Inbox thin — writing {len(articles)} bundle(s) instead of {count}.")

    return articles, errors


# ---------------------------------------------------------------------------
# Build the synthesis bundle
# ---------------------------------------------------------------------------
def build_bundle(ts: str, seq: str, voice_text: str, article: dict) -> str:
    """Return the full markdown bundle as a string.

    ts  -- shared timestamp for the batch (YYYYMMDD_HHMMSS)
    seq -- zero-padded 2-digit sequence within the batch, e.g. "01"
    """
    slug   = f"{ts}_{seq}"
    title  = article.get("title", "").strip() or "[no title]"
    source = article.get("source", "").strip() or "[no source]"
    url    = article.get("url", "").strip() or "[no url]"
    body   = (article.get("body", "") or "").strip()[:2000]

    if not voice_text:
        voice_section = "_(voice doc unavailable -- consumer should default to grounded, reflective tone)_"
    else:
        voice_section = voice_text

    return f"""# C-Phile Synthesis Request

<!-- generated: {ts} -->
<!-- bundle: {slug} -->
<!-- consumer: Claude Code session (Option A scheduled, or Option B ad-hoc) -->

## Voice reference

_(excerpted from `Weaving I am Content.docx`)_

{voice_section}

## Voice guidelines

- Reflective and grounded, not promotional
- Connect current events to human experience and personal growth
- Pair business/government themes with meaning and purpose
- Use "we" to include the reader
- Short, punchy sentences. No fluff.

## Source article

- **Title:** {title}
- **Source:** {source}
- **URL:** {url}

### Body

{body}

## Task

Synthesize the article above into three pieces, in the voice described:

1. **One social post** — max 280 characters
2. **One short HTML blog draft** — `<h1>` + 2-3 `<p>` paragraphs
3. **One visual direction file** — markdown using the GEM template below

### Visual direction template (lock this structure — field names are used downstream)

```markdown
### 🖋️ Writing
- **Title:** <blog title>
- **Core Theme/Hook:** <1-2 sentences summarizing the main emotional or philosophical takeaway>
- **Key Excerpt:** "<a specific quote or paragraph from the blog draft with the strongest visual imagery>"

### 🎨 Visual Direction
- **Concept Idea:** <e.g. diagonal split image, metaphorical landscape, person in a state of mind>
- **Mood/Vibe:** <e.g. somber, reflective, empowering, gritty, minimalist>
- **Color Temperature:** <e.g. dominated by Deep Ocean Blue + Slate Grey-Blue with warm lighting accents>

### 📐 Brand Integration
- **Logo Placement:** Top-right corner (default — change per article if you have reason)
- **Logo Style:** <e.g. full color crest, or clean Slate Grey-Blue silhouette>
- **Text Overlays:** <e.g. the blog title in clean sans-serif typography, OR no text>

### 🖼️ Suggested Image Prompt
```
<a single ready-to-paste prompt, optimized for Gemini Image / Midjourney / DALL-E. 1-3 sentences. Include subject, style, mood, color, composition. No quote marks around it.>
```
```

## Output protocol

When done, write the results to:

- `research/data/drafts/_done/phile_{slug}_social.txt`  _(plain text, ≤280 chars)_
- `research/data/drafts/_done/phile_{slug}_blog.html`  _(HTML only, no `<html>`/`<body>` wrapper)_
- `research/data/drafts/_done/phile_{slug}_visual.md`  _(markdown, GEM template filled in — including the Suggested Image Prompt block)_

Then move this bundle from `_pending/` to `_consumed/`:

```
mv research/data/drafts/_pending/phile_{slug}.md research/data/drafts/_consumed/phile_{slug}.md
```
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="C-Phile: build synthesis bundles for Claude Code to consume")
    parser.add_argument(
        "--voice", type=Path, default=DEFAULT_VOICE_DOC,
        help="Path to voice reference .docx (default: G:/My Drive/AI GEN/Weaving I am Content.docx)",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of bundles to produce in this batch (default: 1). "
             "Each bundle consumes one article from the most recent inbox JSONL.",
    )
    parser.add_argument(
        "--allow-duplicates", action="store_true",
        help="Skip cross-batch dedupe. Useful for re-synthesizing an article "
             "whose first bundle was thin (e.g. before the body extractor was fixed). "
             "Default: dedupe is ON.",
    )
    args = parser.parse_args()

    if args.count < 1:
        print("ERROR: --count must be at least 1")
        sys.exit(1)

    started_at = datetime.now(timezone.utc)
    ts         = started_at.strftime("%Y%m%d_%H%M%S")
    all_errors: list[str] = []

    print(f"C-Phile: reading voice doc from {args.voice}")
    voice_text, errs = read_voice_doc(args.voice)
    all_errors.extend(errs)

    print(f"C-Phile: selecting {args.count} article(s) from {INBOX_DIR}")
    articles, errs = pick_articles(args.count, allow_duplicates=args.allow_duplicates)
    all_errors.extend(errs)

    if not articles:
        print("[WARN] No articles available -- nothing to bundle. Run C-Transit first.")
        log_run("c-phile", started_at, record_count=0, errors=all_errors)
        return

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for i, article in enumerate(articles, 1):
        seq      = f"{i:02d}"
        slug     = f"{ts}_{seq}"
        print(f"  [{i}/{len(articles)}] {article.get('title', '')[:70]}")
        bundle   = build_bundle(ts, seq, voice_text, article)
        out_path = PENDING_DIR / f"phile_{slug}.md"
        out_path.write_text(bundle, encoding="utf-8")
        print(f"    Bundle  -> {out_path}")
        written += 1

    print(f"\nC-Phile: {written} bundle(s) written to {PENDING_DIR}")
    print("  Consume via scheduled Claude Code agent (Option A) or /synth-batch (Option B).")

    log_run("c-phile", started_at, record_count=written, errors=all_errors if all_errors else None)


if __name__ == "__main__":
    main()
