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

## Step 5 — Assemble review packages

After all bundles are consumed, run the package generator using the batch timestamp from Step 2. The timestamp appears in the filenames of the bundles (e.g. `phile_20260527_234450_01.md` → timestamp is `20260527_234450`).

```
backend/.venv/Scripts/python.exe scripts/phile_package.py --batch <ts>
```

Replace `<ts>` with the actual timestamp. The script will print both output paths on completion. Note the two package paths for the summary.

## Step 6 — Summary packet

After packages are generated, print a summary in this format:

```
Batch complete — N article(s) synthesized

1. [Article title]
   [Full social post text]

2. [Article title]
   [Full social post text]

...

Review at: research/data/drafts/_done/

Packages:
  research/data/drafts/_packages/phile_batch_<ts>.html
  research/data/drafts/_packages/phile_batch_<ts>.md
```

- Number each item.
- Show the article title and the full social post text (no HTML).
- End with the "Review at:" and "Packages:" lines exactly as shown, substituting the real timestamp.
- If the package generator fails (e.g. no `_done/` artifacts yet), note the error in the summary but do not block the output — the per-article files are still available in `_done/`.
