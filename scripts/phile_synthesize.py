#!/usr/bin/env python3
"""
C-Phile -- voice synthesis agent.

Reads voice reference from Weaving I am Content.docx, picks one article
from the most recent research/data/inbox/*.jsonl, calls Claude Sonnet 4.6,
and writes:
  research/data/drafts/phile_<timestamp>_social.txt
  research/data/drafts/phile_<timestamp>_blog.html

API key: read from backend/.env -> ANTHROPIC_API_KEY
If key is missing, writes stub files and exits 0 (timing infra still runs).

Usage:
    python scripts/phile_synthesize.py
    python scripts/phile_synthesize.py --voice "G:/path/to/voice.docx"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx  # noqa: F401 -- kept so import order matches project style

HERE       = Path(__file__).resolve().parent.parent   # repo root
INBOX_DIR  = HERE / "research" / "data" / "inbox"
DRAFTS_DIR = HERE / "research" / "data" / "drafts"
ENV_PATH   = HERE / "backend" / ".env"

DEFAULT_VOICE_DOC = Path("G:/My Drive/AI GEN/Weaving I am Content.docx")
MODEL_ID          = "claude-sonnet-4-6"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402


# ---------------------------------------------------------------------------
# Env loading -- mirrors fetch_awards.py
# ---------------------------------------------------------------------------
def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


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
# Pick most recent inbox file and read one article
# ---------------------------------------------------------------------------
def pick_article() -> tuple[dict | None, list[str]]:
    """Return (article_dict, errors). Article is None if nothing found."""
    errors: list[str] = []
    inbox_files = sorted(INBOX_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not inbox_files:
        errors.append(f"No .jsonl files found in {INBOX_DIR}")
        return None, errors

    latest = inbox_files[0]
    try:
        with open(latest, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    return json.loads(line), errors
    except Exception as exc:
        errors.append(f"Failed to read inbox file {latest}: {exc}")

    errors.append(f"Inbox file {latest} was empty or unreadable")
    return None, errors


# ---------------------------------------------------------------------------
# Stub output when no API key
# ---------------------------------------------------------------------------
def write_stubs(ts: str) -> tuple[Path, Path]:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    social_path = DRAFTS_DIR / f"phile_{ts}_social.txt"
    blog_path   = DRAFTS_DIR / f"phile_{ts}_blog.html"
    stub_msg    = "[stub -- no ANTHROPIC_API_KEY set]"
    social_path.write_text(stub_msg, encoding="utf-8")
    blog_path.write_text(f"<p>{stub_msg}</p>", encoding="utf-8")
    return social_path, blog_path


# ---------------------------------------------------------------------------
# Call Claude Sonnet 4.6
# ---------------------------------------------------------------------------
def synthesize(api_key: str, voice_text: str, article: dict) -> tuple[str, str, list[str]]:
    """
    Returns (social_draft, blog_html, errors).
    social_draft: <=280 char social post
    blog_html: short HTML blog draft with <h1> + <p>
    """
    errors: list[str] = []

    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = f"""You are C-Phile, the voice synthesizer for Shade of Design LLC.
Your job: transform source articles into two content pieces that match the established voice.

VOICE REFERENCE (from Weaving I am Content.docx):
{voice_text}

VOICE GUIDELINES:
- Reflective and grounded, not promotional
- Connects current events to human experience and personal growth
- Pairs business/government themes with meaning and purpose
- Uses "we" to include the reader
- Short, punchy sentences. No fluff.

OUTPUT FORMAT — respond with EXACTLY this structure, nothing else:
SOCIAL: <your social post text, 280 chars max>
BLOG_TITLE: <a short blog title>
BLOG_HTML:
<h1>title here</h1>
<p>paragraph one</p>
<p>paragraph two</p>"""

    article_text = (
        f"Title: {article.get('title', '')}\n"
        f"Source: {article.get('source', '')} | {article.get('url', '')}\n\n"
        f"{article.get('body', '')[:2000]}"
    )

    user_prompt = (
        f"Synthesize this article into (a) one <=280 char social post and "
        f"(b) one short HTML blog draft with <h1> + <p> paragraphs.\n\n"
        f"ARTICLE:\n{article_text}"
    )

    try:
        message = client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )
        raw = message.content[0].text if message.content else ""
    except Exception as exc:
        errors.append(f"Claude API call failed: {exc}")
        return "", "", errors

    # Parse structured output
    social = ""
    blog_html = ""
    blog_title = ""

    lines = raw.splitlines()
    blog_lines: list[str] = []
    in_blog = False

    for line in lines:
        if line.startswith("SOCIAL:"):
            social = line[len("SOCIAL:"):].strip()
        elif line.startswith("BLOG_TITLE:"):
            blog_title = line[len("BLOG_TITLE:"):].strip()
        elif line.startswith("BLOG_HTML:"):
            in_blog = True
        elif in_blog:
            blog_lines.append(line)

    blog_html = "\n".join(blog_lines).strip()

    # Fallback: if parsing failed, use raw response wrapped in HTML
    if not social:
        social = raw[:280]
    if not blog_html:
        safe = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        blog_html = f"<h1>{blog_title or 'Draft'}</h1>\n<pre>{safe}</pre>"

    # Enforce 280 char cap on social
    if len(social) > 280:
        social = social[:277] + "..."

    return social, blog_html, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="C-Phile: synthesize articles with Claude")
    parser.add_argument(
        "--voice", type=Path, default=DEFAULT_VOICE_DOC,
        help="Path to voice reference .docx (default: G:/My Drive/AI GEN/Weaving I am Content.docx)",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    ts         = started_at.strftime("%Y%m%d_%H%M%S")
    all_errors: list[str] = []

    # Load API key
    env     = load_env(ENV_PATH)
    api_key = env.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        msg = "ANTHROPIC_API_KEY not set in backend/.env -- writing stub files"
        print(f"[WARN] {msg}")
        all_errors.append(msg)
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        social_path, blog_path = write_stubs(ts)
        print(f"  Stub social  -> {social_path}")
        print(f"  Stub blog    -> {blog_path}")
        log_run("c-phile", started_at, record_count=1, errors=all_errors)
        return

    # Read voice doc
    print(f"C-Phile: reading voice doc from {args.voice}")
    voice_text, errs = read_voice_doc(args.voice)
    all_errors.extend(errs)
    if not voice_text:
        voice_text = "[voice doc unavailable -- using default tone]"

    # Pick article
    print(f"C-Phile: selecting article from {INBOX_DIR}")
    article, errs = pick_article()
    all_errors.extend(errs)

    if article is None:
        msg = "No article available -- writing stub files"
        print(f"[WARN] {msg}")
        all_errors.append(msg)
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        social_path, blog_path = write_stubs(ts)
        print(f"  Stub social  -> {social_path}")
        print(f"  Stub blog    -> {blog_path}")
        log_run("c-phile", started_at, record_count=1, errors=all_errors)
        return

    print(f"  Article: {article.get('title', '')[:70]}")
    print(f"  Calling {MODEL_ID} ...")

    # Synthesize
    social, blog_html, errs = synthesize(api_key, voice_text, article)
    all_errors.extend(errs)

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    social_path = DRAFTS_DIR / f"phile_{ts}_social.txt"
    blog_path   = DRAFTS_DIR / f"phile_{ts}_blog.html"

    if not social and not blog_html:
        social_path, blog_path = write_stubs(ts)
        print(f"  Synthesis failed -- wrote stubs")
    else:
        social_path.write_text(social, encoding="utf-8")
        blog_path.write_text(blog_html, encoding="utf-8")
        print(f"  Social ({len(social)} chars) -> {social_path}")
        print(f"  Blog HTML    -> {blog_path}")
        print(f"\n  Social preview: {social[:120]}")

    log_run("c-phile", started_at, record_count=1, errors=all_errors if all_errors else None)


if __name__ == "__main__":
    main()
