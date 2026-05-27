---
description: Synthesize N inbox articles into social + blog drafts (Phile batch consume)
argument-hint: [N]
---

Batch-synthesize inbox articles using C-Phile. Default N is 5 if `$ARGUMENTS` is empty.

## Step 1 — Resolve N

If `$ARGUMENTS` is empty or whitespace, use N=5. Otherwise parse `$ARGUMENTS` as an integer and use that as N.

## Step 2 — Run phile_synthesize.py

From the HZ repo root, run:

```
backend/.venv/Scripts/python.exe scripts/phile_synthesize.py --count N
```

Replace N with the resolved value. Capture stdout. Report the prep duration (it will appear in the `[log_run]` line at the end of the output).

## Step 3 — List pending bundles

List all `.md` files in `research/data/drafts/_pending/` sorted chronologically (oldest first). There should be N files (or fewer if the inbox was thin — that's fine, continue with what's there). Note the filenames.

## Step 4 — Synthesize each bundle

For each bundle file in chronological order:

a. Read the bundle file from `research/data/drafts/_pending/`.

b. The bundle is self-documenting. It contains: the voice reference, voice guidelines, source article, task instructions, and exact output file paths. Follow them.

c. Synthesize:
   - **Social post**: max 280 characters, plain text. Match the voice guidelines in the bundle.
   - **Blog draft**: `<h1>` + 2–3 `<p>` paragraphs, HTML only (no `<html>`/`<body>` wrapper). Match the voice guidelines.

d. Write outputs to the paths specified in the bundle's Output Protocol section:
   - `research/data/drafts/_done/phile_<slug>_social.txt`
   - `research/data/drafts/_done/phile_<slug>_blog.html`

   Where `<slug>` is `<timestamp>_<NN>` as shown in the bundle's output protocol.

e. Move the bundle from `_pending/` to `_consumed/`:
   ```
   mv research/data/drafts/_pending/phile_<slug>.md research/data/drafts/_consumed/phile_<slug>.md
   ```
   Create `_consumed/` if it doesn't exist.

Repeat for every bundle.

## Step 5 — Summary packet

After all bundles are processed, print a summary in this format:

```
Batch complete — N article(s) synthesized

1. [Article title]
   [Full social post text]

2. [Article title]
   [Full social post text]

...

Review at: research/data/drafts/_done/
```

- Number each item.
- Show the article title and the full social post text (no HTML).
- End with the "Review at:" line exactly as shown.
