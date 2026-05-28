#!/usr/bin/env python3
"""
phile_package.py — Batch review package generator for C-Phile.

Assembles all per-article outputs from a given batch timestamp into two
standalone review documents:

  _packages/phile_batch_<ts>.html   -- brand-themed, sticky TOC, card layout
  _packages/phile_batch_<ts>.md     -- portable, renders in Notion/Obsidian/GH

Usage:
    python scripts/phile_package.py --batch 20260527_234450
    python scripts/phile_package.py --batch 20260527_234450 --out-dir /custom/path

See Central Hub: pipeline/DECISIONS.md (D-013) for rationale.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE        = Path(__file__).resolve().parent.parent   # repo root
DONE_DIR    = HERE / "research" / "data" / "drafts" / "_done"
CONSUMED_DIR = HERE / "research" / "data" / "drafts" / "_consumed"
PACKAGES_DIR = HERE / "research" / "data" / "drafts" / "_packages"

# Brand color palette (Deep Ocean Blue + Slate Grey-Blue)
COLOR_OCEAN   = "#0B2C4D"
COLOR_SLATE   = "#5A7795"
COLOR_ACCENT  = "#2E6DA4"
COLOR_BG      = "#F4F7FA"
COLOR_CARD_BG = "#FFFFFF"
COLOR_MUTED   = "#8AA3BC"
COLOR_TEXT    = "#1A2D40"


# ---------------------------------------------------------------------------
# Metadata extraction from consumed bundle
# ---------------------------------------------------------------------------
def extract_bundle_meta(ts: str, nn: str) -> dict:
    """Read the consumed bundle and extract title, source, source_name, url, category."""
    path = CONSUMED_DIR / f"phile_{ts}_{nn}.md"
    meta = {
        "title": f"Article {nn}",
        "source": "",
        "source_name": "",
        "url": "",
        "category": "uncategorized",
    }
    if not path.exists():
        return meta

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return meta

    # Narrow to the "Source article" section only to avoid false matches
    # in the voice reference / GEM template embedded in the bundle.
    source_section_match = re.search(
        r"## Source article(.*?)(?=^##|\Z)", text, re.DOTALL | re.MULTILINE
    )
    search_text = source_section_match.group(1) if source_section_match else text

    # Title: "- **Title:** ..."
    m = re.search(r"\*\*Title:\*\*\s*(.+)", search_text)
    if m:
        val = m.group(1).strip()
        if val and not val.startswith("["):   # skip unfilled placeholders
            meta["title"] = val

    # Source (slug): "- **Source:**"
    m = re.search(r"\*\*Source:\*\*\s*(.+)", search_text)
    if m:
        meta["source"] = m.group(1).strip()
        # Humanize the slug: underscores → spaces, title-case
        meta["source_name"] = m.group(1).strip().replace("_", " ").title()

    # URL
    m = re.search(r"\*\*URL:\*\*\s*(.+)", search_text)
    if m:
        meta["url"] = m.group(1).strip()

    # Category: infer from round-robin position in bundle comment or source slug
    # The bundle doesn't store category directly; derive from source slug heuristics
    src = meta["source"].lower()
    if "federal_register" in src or "sba" in src or "smallbiz" in src:
        meta["category"] = "smallbiz"
    elif "policy" in src or "regulation" in src:
        meta["category"] = "policy"
    elif "ars_technica" in src or "tech" in src:
        meta["category"] = "tech"
    elif "technology_review" in src or "mit" in src or "ai" in src:
        meta["category"] = "ai"
    elif "kff" in src or "health" in src:
        meta["category"] = "health"
    elif "bbc" in src or "world" in src:
        meta["category"] = "world"
    else:
        meta["category"] = "general"

    return meta


# ---------------------------------------------------------------------------
# Load per-article artifacts
# ---------------------------------------------------------------------------
def load_article(ts: str, nn: str) -> dict:
    """Load social, blog, visual for one article index. Graceful on missing files."""
    def read_file(path: Path) -> str | None:
        if path.exists():
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception:
                return None
        return None

    slug = f"{ts}_{nn}"
    social  = read_file(DONE_DIR / f"phile_{slug}_social.txt")
    blog    = read_file(DONE_DIR / f"phile_{slug}_blog.html")
    visual  = read_file(DONE_DIR / f"phile_{slug}_visual.md")
    meta    = extract_bundle_meta(ts, nn)

    return {
        "nn": nn,
        "slug": slug,
        "meta": meta,
        "social": social or "_[social post not yet produced]_",
        "blog": blog or "<p><em>[blog draft not yet produced]</em></p>",
        "visual": visual,   # None = not yet produced; handled per renderer
    }


# ---------------------------------------------------------------------------
# Find all article indices for a batch
# ---------------------------------------------------------------------------
def find_article_indices(ts: str) -> list[str]:
    """Return sorted list of NN strings that have at least one artifact for ts."""
    pattern = re.compile(rf"^phile_{re.escape(ts)}_(\d{{2}})_(social\.txt|blog\.html|visual\.md)$")
    indices: set[str] = set()
    for f in DONE_DIR.iterdir():
        m = pattern.match(f.name)
        if m:
            indices.add(m.group(1))
    return sorted(indices)


# ---------------------------------------------------------------------------
# Category badge colors (per CSS class)
# ---------------------------------------------------------------------------
CATEGORY_COLORS: dict[str, tuple[str, str]] = {
    "ai":          ("#6C3ABF", "#EDE7FF"),
    "tech":        ("#1A6B8A", "#E0F4FF"),
    "health":      ("#1A7A4A", "#E0F5EA"),
    "smallbiz":    ("#8A5A1A", "#FFF4E0"),
    "policy":      ("#5A1A8A", "#F4E0FF"),
    "world":       ("#1A3A8A", "#E0E8FF"),
    "general":     ("#4A5A6A", "#EEF2F6"),
    "uncategorized": ("#4A5A6A", "#EEF2F6"),
}


def category_colors(cat: str) -> tuple[str, str]:
    return CATEGORY_COLORS.get(cat.lower(), CATEGORY_COLORS["general"])


# ---------------------------------------------------------------------------
# Social char count helper
# ---------------------------------------------------------------------------
def char_count_badge(text: str) -> str:
    """Return a char count string like '260 / 280 chars'."""
    # Strip markdown italic markers that appear in fallback string
    clean = re.sub(r"_\[.*?\]_", "", text).strip()
    n = len(clean)
    return f"{n} / 280 chars"


# ---------------------------------------------------------------------------
# Visual direction: parse markdown sections for HTML rendering
# ---------------------------------------------------------------------------
def parse_visual_md(visual_md: str) -> dict:
    """Return dict with writing, visual_dir, brand, image_prompt sections."""
    result = {
        "writing": "",
        "visual_dir": "",
        "brand": "",
        "image_prompt": "",
    }
    if not visual_md:
        return result

    # Extract code block for image prompt (between triple backtick fences)
    prompt_match = re.search(r"### 🖼️ Suggested Image Prompt\n```\n(.*?)\n```", visual_md, re.DOTALL)
    if prompt_match:
        result["image_prompt"] = prompt_match.group(1).strip()

    # Writing section
    m = re.search(r"### 🖋️ Writing(.*?)(?=###|\Z)", visual_md, re.DOTALL)
    if m:
        result["writing"] = m.group(1).strip()

    # Visual Direction section
    m = re.search(r"### 🎨 Visual Direction(.*?)(?=###|\Z)", visual_md, re.DOTALL)
    if m:
        result["visual_dir"] = m.group(1).strip()

    # Brand Integration section
    m = re.search(r"### 📐 Brand Integration(.*?)(?=###|\Z)", visual_md, re.DOTALL)
    if m:
        result["brand"] = m.group(1).strip()

    return result


def md_fields_to_html(md_text: str) -> str:
    """Convert markdown bullet field list to simple HTML dl."""
    lines = md_text.strip().splitlines()
    html_lines: list[str] = []
    for line in lines:
        # Match "- **Field:** value"
        m = re.match(r"-\s+\*\*(.+?):\*\*\s*(.*)", line)
        if m:
            label = m.group(1).strip()
            value = m.group(2).strip()
            # Strip wrapping quotes from Key Excerpt
            if value.startswith('"') and value.endswith('"'):
                value = f"<em>{value[1:-1]}</em>"
            html_lines.append(
                f'<div class="vd-field">'
                f'<span class="vd-label">{label}</span>'
                f'<span class="vd-value">{value}</span>'
                f'</div>'
            )
        elif line.strip():
            html_lines.append(f'<p class="vd-misc">{line.strip()}</p>')
    return "\n".join(html_lines)


# ---------------------------------------------------------------------------
# HTML package builder
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

/* ── Top nav / TOC ── */
#toc {{
    background: {COLOR_OCEAN};
    color: #fff;
    padding: 0.75rem 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}}
#toc .toc-title {{
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {COLOR_MUTED};
    white-space: nowrap;
    margin-right: 0.5rem;
}}
#toc a {{
    color: #D4E6F7;
    font-size: 0.82rem;
    white-space: nowrap;
    border-bottom: 1px dotted rgba(255,255,255,0.3);
    padding-bottom: 1px;
}}
#toc a:hover {{ color: #fff; text-decoration: none; border-bottom-color: #fff; }}

/* ── Main content ── */
.container {{
    max-width: 860px;
    margin: 2rem auto;
    padding: 0 1rem 4rem;
}}

/* ── Article card ── */
.article-card {{
    background: {COLOR_CARD_BG};
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(11,44,77,0.08);
    margin-bottom: 2.5rem;
    overflow: hidden;
    border: 1px solid #D8E6F3;
}}
.card-header {{
    background: {COLOR_OCEAN};
    padding: 1rem 1.5rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}}
.card-header h2 {{
    color: #fff;
    font-size: 1.15rem;
    font-weight: 600;
    flex: 1;
}}
.cat-badge {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    white-space: nowrap;
    margin-top: 0.15rem;
}}
.source-line {{
    padding: 0.4rem 1.5rem;
    font-size: 0.8rem;
    color: {COLOR_MUTED};
    background: #EEF4FA;
    border-bottom: 1px solid #D8E6F3;
}}
.source-line a {{ color: {COLOR_SLATE}; }}

/* ── Sections inside card ── */
.section {{
    padding: 1.2rem 1.5rem;
    border-top: 1px solid #EEF2F6;
}}
.section:first-of-type {{ border-top: none; }}
.section-label {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {COLOR_SLATE};
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.section-label .char-badge {{
    background: {COLOR_BG};
    border: 1px solid #C8D8E8;
    border-radius: 999px;
    padding: 0.1rem 0.5rem;
    font-size: 0.7rem;
    color: {COLOR_MUTED};
    font-weight: 400;
    letter-spacing: 0;
}}

/* ── Social block ── */
.social-block {{
    background: #F0F7FF;
    border: 1px solid #C8DDF0;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-family: "Courier New", Courier, monospace;
    font-size: 0.9rem;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.5;
}}

/* ── Blog block ── */
.blog-block h1 {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 0.6rem; color: {COLOR_OCEAN}; }}
.blog-block p  {{ margin-bottom: 0.6rem; font-size: 0.93rem; }}
.blog-block p:last-child {{ margin-bottom: 0; }}

/* ── Visual direction block ── */
.vd-section-head {{
    font-size: 0.8rem;
    font-weight: 700;
    color: {COLOR_OCEAN};
    margin: 0.75rem 0 0.4rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid #D8E6F3;
}}
.vd-field {{
    display: flex;
    gap: 0.5rem;
    font-size: 0.88rem;
    margin-bottom: 0.3rem;
    align-items: flex-start;
}}
.vd-label {{
    font-weight: 600;
    color: {COLOR_SLATE};
    white-space: nowrap;
    min-width: 140px;
    flex-shrink: 0;
}}
.vd-label::after {{ content: ":"; }}
.vd-value {{ color: {COLOR_TEXT}; }}
.vd-misc {{ font-size: 0.85rem; color: {COLOR_MUTED}; font-style: italic; }}
.vd-missing {{
    background: #FFF8E8;
    border: 1px dashed #C8A84A;
    border-radius: 6px;
    padding: 0.6rem 0.9rem;
    font-size: 0.85rem;
    color: #8A6A1A;
    font-style: italic;
}}

/* ── Image prompt block ── */
.prompt-block {{
    background: #1A2D40;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin-top: 0.4rem;
}}
.prompt-block pre {{
    color: #B8D8F0;
    font-family: "Courier New", Courier, monospace;
    font-size: 0.88rem;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
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


def build_html_article(article: dict, idx_of_total: str) -> str:
    nn   = article["nn"]
    meta = article["meta"]
    cat  = meta["category"]
    badge_fg, badge_bg = category_colors(cat)

    toc_anchor = f"article-{nn}"
    total_n, total_count = idx_of_total.split("/")
    source_label = meta["source_name"] or meta["source"]
    url_link = f'<a href="{meta["url"]}" target="_blank" rel="noopener">{meta["url"]}</a>' if meta["url"] else "—"

    social_text = article["social"]
    char_badge = char_count_badge(social_text)

    # Blog block
    blog_html = article["blog"]

    # Visual direction
    visual_md = article["visual"]
    if visual_md:
        vd = parse_visual_md(visual_md)
        writing_html  = md_fields_to_html(vd["writing"])
        vis_html      = md_fields_to_html(vd["visual_dir"])
        brand_html    = md_fields_to_html(vd["brand"])
        image_prompt  = vd["image_prompt"]

        visual_section = f"""
<div class="section">
  <div class="section-label">🎨 Visual Direction</div>
  <div class="vd-section-head">🖋️ Writing</div>
  {writing_html}
  <div class="vd-section-head">🎨 Visual</div>
  {vis_html}
  <div class="vd-section-head">📐 Brand Integration</div>
  {brand_html}
</div>
<div class="section">
  <div class="section-label">🖼️ Suggested Image Prompt</div>
  <div class="prompt-block"><pre>{image_prompt}</pre></div>
</div>"""
    else:
        visual_section = f"""
<div class="section">
  <div class="section-label">🎨 Visual Direction</div>
  <div class="vd-missing">Visual direction not yet produced for this article. Run /synth-batch with the updated bundle to generate it.</div>
</div>"""

    return f"""
<div class="article-card" id="{toc_anchor}">
  <div class="card-header">
    <h2>{meta["title"]}</h2>
    <span class="cat-badge" style="background:{badge_bg};color:{badge_fg};">{cat.upper()}</span>
  </div>
  <div class="source-line">
    {source_label} &nbsp;·&nbsp; {url_link} &nbsp;·&nbsp; Article {total_n} of {total_count}
  </div>

  <div class="section">
    <div class="section-label">
      📣 Social Post
      <span class="char-badge">{char_badge}</span>
    </div>
    <div class="social-block">{social_text}</div>
  </div>

  <div class="section">
    <div class="section-label">📝 Blog Draft</div>
    <div class="blog-block">{blog_html}</div>
  </div>
  {visual_section}
</div>
"""


def build_html_package(ts: str, articles: list[dict]) -> str:
    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(articles)

    # TOC entries
    toc_items = []
    for a in articles:
        nn   = a["nn"]
        meta = a["meta"]
        cat  = meta["category"].upper()
        title = meta["title"]
        toc_items.append(f'<a href="#article-{nn}">[{nn}] · {cat} · {title[:55]}</a>')
    toc_html = "\n    ".join(toc_items)

    # Article cards
    cards = []
    for i, a in enumerate(articles, 1):
        cards.append(build_html_article(a, f"{i}/{total}"))
    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>C-Phile Batch · {ts}</title>
<style>{CSS}</style>
</head>
<body>

<nav id="toc">
  <span class="toc-title">Batch {ts}</span>
  {toc_html}
</nav>

<div class="container">
{cards_html}

  <footer>
    Generated {gen_ts} &nbsp;·&nbsp; {total} article(s) &nbsp;·&nbsp; C-Phile batch {ts}
  </footer>
</div>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Markdown package builder
# ---------------------------------------------------------------------------
def html_to_text_blog(html: str) -> str:
    """Very light HTML → readable text for the MD package. Strips tags."""
    text = re.sub(r"<h1>(.*?)</h1>", r"**\1**\n", html, flags=re.DOTALL)
    text = re.sub(r"<p>(.*?)</p>", r"\1\n\n", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def build_md_package(ts: str, articles: list[dict]) -> str:
    total = len(articles)
    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        f"# C-Phile Batch — {ts}",
        "",
        f"_Generated {gen_ts} · {total} article(s)_",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]

    for a in articles:
        nn   = a["nn"]
        meta = a["meta"]
        cat  = meta["category"].upper()
        title = meta["title"]
        # GitHub/Notion anchor: lowercase, spaces → hyphens, drop special chars
        anchor = re.sub(r"[^\w\s-]", "", f"{nn} {cat} {title}".lower())
        anchor = re.sub(r"[\s]+", "-", anchor.strip())
        lines.append(f"- [{nn}] · {cat} · [{title}](#{anchor})")

    lines.append("")
    lines.append("---")
    lines.append("")

    for i, a in enumerate(articles, 1):
        nn   = a["nn"]
        meta = a["meta"]
        cat  = meta["category"].upper()
        title = meta["title"]
        source_label = meta["source_name"] or meta["source"]
        url = meta["url"]

        lines.append(f"## [{nn}] · {cat} · {title}")
        lines.append("")
        if source_label:
            url_part = f" · [{url}]({url})" if url else ""
            lines.append(f"_{source_label}{url_part} · Article {i} of {total}_")
            lines.append("")

        # Social
        social_text = a["social"]
        char_n = len(re.sub(r"_\[.*?\]_", "", social_text).strip())
        lines.append("### Social Post")
        lines.append("")
        lines.append(f"_{char_n} / 280 chars_")
        lines.append("")
        lines.append("```")
        lines.append(social_text)
        lines.append("```")
        lines.append("")

        # Blog
        lines.append("### Blog Draft")
        lines.append("")
        blog_readable = html_to_text_blog(a["blog"])
        lines.append(blog_readable)
        lines.append("")

        # Visual Direction
        lines.append("### Visual Direction")
        lines.append("")
        if a["visual"]:
            vd = parse_visual_md(a["visual"])
            if vd["writing"]:
                lines.append("**🖋️ Writing**")
                lines.append("")
                lines.append(vd["writing"])
                lines.append("")
            if vd["visual_dir"]:
                lines.append("**🎨 Visual**")
                lines.append("")
                lines.append(vd["visual_dir"])
                lines.append("")
            if vd["brand"]:
                lines.append("**📐 Brand Integration**")
                lines.append("")
                lines.append(vd["brand"])
                lines.append("")
            if vd["image_prompt"]:
                lines.append("**🖼️ Suggested Image Prompt**")
                lines.append("")
                lines.append("```")
                lines.append(vd["image_prompt"])
                lines.append("```")
                lines.append("")
        else:
            lines.append("_Visual direction not yet produced for this article._")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="phile_package.py — assemble batch review packages from C-Phile outputs"
    )
    parser.add_argument(
        "--batch", required=True,
        help="Batch timestamp, e.g. 20260527_234450"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help=f"Output directory (default: {PACKAGES_DIR})"
    )
    args = parser.parse_args()

    ts      = args.batch
    out_dir = args.out_dir if args.out_dir else PACKAGES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"phile_package: assembling batch {ts}")

    indices = find_article_indices(ts)
    if not indices:
        print(f"  [ERROR] No _done/ artifacts found for batch {ts}.")
        print(f"          Expected files like: phile_{ts}_01_social.txt")
        sys.exit(1)

    print(f"  Found {len(indices)} article(s): {', '.join(indices)}")

    articles: list[dict] = []
    for nn in indices:
        a = load_article(ts, nn)
        articles.append(a)
        has_visual = "yes" if a["visual"] else "no (fallback)"
        print(f"  [{nn}] {a['meta']['title'][:60]} | visual={has_visual}")

    # Write HTML package
    html_path = out_dir / f"phile_batch_{ts}.html"
    html_path.write_text(build_html_package(ts, articles), encoding="utf-8")
    print(f"\n  HTML package -> {html_path}  ({html_path.stat().st_size:,} bytes)")

    # Write MD package
    md_path = out_dir / f"phile_batch_{ts}.md"
    md_path.write_text(build_md_package(ts, articles), encoding="utf-8")
    print(f"  MD package   -> {md_path}  ({md_path.stat().st_size:,} bytes)")

    print(f"\nphile_package: done. Review at:\n  {out_dir}")


if __name__ == "__main__":
    main()
