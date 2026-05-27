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
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE        = Path(__file__).resolve().parent.parent   # repo root
INBOX_DIR   = HERE / "research" / "data" / "inbox"
DRAFTS_DIR  = HERE / "research" / "data" / "drafts"
PENDING_DIR = DRAFTS_DIR / "_pending"

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
# Pick most recent inbox file and read N distinct articles
# ---------------------------------------------------------------------------
def pick_articles(count: int) -> tuple[list[dict], list[str]]:
    """Return (article_list, errors). List may be shorter than count if inbox is thin."""
    errors: list[str] = []
    inbox_files = sorted(INBOX_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not inbox_files:
        errors.append(f"No .jsonl files found in {INBOX_DIR}")
        return [], errors

    latest = inbox_files[0]
    articles: list[dict] = []
    seen_urls: set[str] = set()

    try:
        with open(latest, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    article = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"Skipped malformed JSON line in {latest}: {exc}")
                    continue
                url = article.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append(article)
                if len(articles) >= count:
                    break
    except Exception as exc:
        errors.append(f"Failed to read inbox file {latest}: {exc}")
        return articles, errors

    if not articles:
        errors.append(f"Inbox file {latest} was empty or had no valid records")
    elif len(articles) < count:
        errors.append(
            f"Inbox only had {len(articles)} article(s) (requested {count}). "
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

Synthesize the article above into two pieces, in the voice described:

1. **One social post** — max 280 characters
2. **One short HTML blog draft** — `<h1>` + 2-3 `<p>` paragraphs

## Output protocol

When done, write the results to:

- `research/data/drafts/_done/phile_{slug}_social.txt`  _(plain text, ≤280 chars)_
- `research/data/drafts/_done/phile_{slug}_blog.html`  _(HTML only, no `<html>`/`<body>` wrapper)_

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
    articles, errs = pick_articles(args.count)
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
