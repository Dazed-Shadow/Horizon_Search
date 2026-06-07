# Phase A — RFP Digest

**Status:** Designed by Opus 2026-06-06 · Awaiting Sonnet implementation
**Branch:** `claude/military-contract-search-tool-9hm2D`
**Builds on:** Plain-language contract translator (shipped 2026-05-22)
**Feeds into:** Phase B (similar opportunities sidebar) · Phase C (USAspending intelligence layer — BACKLOG 2026-05-23)

---

## Goal

Transform the contract detail drawer from "raw description + metadata" into a structured RFP digest — a scannable, plain-language view of what's actually being asked for. **No new external data sources.** This is parsing and UI over data HZ already pulls from SAM.gov.

---

## Context

`ContractDetailDrawer.jsx` already surfaces structured metadata well — At-a-glance stats, set-aside / notice-type / NAICS explainers, POC, IDs. What it does NOT do is parse the **description text** itself, where agencies bury the actual scope, deliverables, evaluation criteria, and submission instructions. That field is currently dumped as `whitespace-pre-line` text in the "Description" section.

Phase A extracts structure out of that text via heuristic parsing and renders it in a new **Digest** tab in the drawer body, keeping the existing description rendering on a **Raw** tab.

---

## Backend changes

### 1. New model — `backend/models/digest.py`

```python
from pydantic import BaseModel
from typing import Optional

class KeyDate(BaseModel):
    label: str
    date: Optional[str] = None
    context: Optional[str] = None  # surrounding sentence for disambiguation

class ContractDigest(BaseModel):
    notice_id: str
    scope_summary: Optional[str] = None         # 1–2 sentence plain-language summary
    deliverables: list[str] = []                # identified deliverables
    submission_requirements: list[str] = []     # what the bid must contain
    evaluation_criteria: list[str] = []         # how the bid will be judged
    period_of_performance: Optional[str] = None # e.g. "12 months", "FY26 base + 4 option years"
    estimated_value: Optional[str] = None       # raw text: "$5M NTE", "TBD", or None
    key_dates: list[KeyDate] = []
    extraction_confidence: str = "low"          # "high" | "medium" | "low"
```

`extraction_confidence` is computed from the count of populated fields and lets the UI signal when the parser got rich structure vs. very little.

### 2. New service — `backend/services/digest.py`

Two top-level functions:

```python
def parse_digest(contract: Contract) -> ContractDigest:
    """Pure function — extract structured fields from contract.description via heuristics."""

async def build_digest(notice_id: str) -> Optional[ContractDigest]:
    """Fetch via sam_gov.get_contract_by_notice_id, then parse_digest. Returns None if 404."""
```

The parser is pure (no I/O) so it's trivial to unit-test against sample description strings.

**Parsing heuristics (initial pass — keep them simple, evolve from real data):**

- **Section detection.** Split description on lines that look like section headers:
  - ALL-CAPS lines (regex `^[A-Z][A-Z\s\d\.\-/&]{3,}$`)
  - Lines ending in `:`
  - Numbered/lettered prefixes (`^\d+\.\s+`, `^[A-Z]\.\s+`)

  Each header starts a new section; everything until the next header is body.

- **Section-name normalization.** Lowercase + keyword match to map header → field:

  | Field | Matching headers (case-insensitive substrings) |
  |---|---|
  | `scope_summary` | scope of work, statement of work, sow, description, background, project description, objective, purpose |
  | `deliverables` | deliverables, required services, tasks, work required, requirements |
  | `submission_requirements` | submission instructions, proposal submission, how to apply, submission requirements, quote submission, instructions to offerors |
  | `evaluation_criteria` | evaluation criteria, basis for award, evaluation factors, award basis, selection criteria |
  | `period_of_performance` | period of performance, performance period, pop, contract period |
  | `estimated_value` | estimated value, anticipated value, contract ceiling, nte, not to exceed, magnitude |

- **Field-level extraction:**
  - `scope_summary`: first 1–2 sentences (≤280 chars) of the matched section body, whitespace normalized.
  - `deliverables`, `submission_requirements`, `evaluation_criteria`: split section body on bullet markers (`-`, `*`, `•`, numbered prefix) or sentence boundaries; trim; cap at 8 items.
  - `period_of_performance`, `estimated_value`: first non-empty line of the section body, trimmed.
  - `key_dates`: regex scan across the full description for `(Q&A|Questions?|Pre-proposal|Industry Day|Site Visit|Walk-?through).{0,80}(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})` and similar variants.

- **Confidence:**
  - `high` if ≥4 of `{scope_summary, deliverables, submission_requirements, evaluation_criteria, period_of_performance}` are populated.
  - `medium` if 2–3 are populated.
  - `low` otherwise.

- **Graceful degrade:** if nothing matches, return a digest with `extraction_confidence="low"` and empty/None fields. The UI handles that gracefully.

### 3. New endpoint — extend `backend/routers/contracts.py`

Add **before** the wildcard `/{notice_id}` route (the existing file already has a comment warning that the wildcard must remain last):

```python
@router.get("/{notice_id}/digest", response_model=ContractDigest)
async def get_digest(notice_id: str):
    try:
        digest = await build_digest(notice_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"SAM.gov returned {exc.response.status_code}")
    except Exception as exc:
        log.exception("Digest build failed")
        raise HTTPException(status_code=502, detail=str(exc))
    if digest is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return digest
```

Note FastAPI route precedence: `/{notice_id}/digest` is more specific than `/{notice_id}` and must be declared first (or use explicit ordering). The current file declares `/{notice_id}` last with a code comment about ordering — keep the same pattern, just add the digest route above it.

### 4. Optional caching (recommended)

Description text is stable for a given notice ID; digests are deterministic. Add a tiny in-memory TTL cache mirroring `_response_cache` in `sam_gov.py`:

```python
_DIGEST_CACHE: dict[str, tuple[float, ContractDigest]] = {}
_DIGEST_TTL = 3600  # 1 hour
```

Keyed by `notice_id`. Saves a SAM.gov call every time the drawer is reopened.

---

## Frontend changes

### 1. Drawer tabs — extend `frontend/src/components/ContractDetailDrawer.jsx`

Add a tab strip just below the sticky header (above the scrollable body). Two tabs:

- **Digest** (default)
- **Raw**

State additions inside the component:

```jsx
const [tab, setTab] = useState("digest");
const [digest, setDigest] = useState(null);
const [digestLoading, setDigestLoading] = useState(false);
const digestCache = useRef(new Map()); // notice_id -> digest
```

Fetch logic in a new `useEffect` keyed on `contract?.notice_id`:

```jsx
useEffect(() => {
  if (!contract?.notice_id) return;
  if (digestCache.current.has(contract.notice_id)) {
    setDigest(digestCache.current.get(contract.notice_id));
    return;
  }
  setDigestLoading(true);
  fetch(`/api/contracts/${contract.notice_id}/digest`)
    .then(r => r.ok ? r.json() : null)
    .then(d => {
      if (d) digestCache.current.set(contract.notice_id, d);
      setDigest(d);
    })
    .finally(() => setDigestLoading(false));
}, [contract?.notice_id]);
```

Body renders conditionally:

```jsx
{tab === "digest"
  ? <DigestTab digest={digest} loading={digestLoading} onSeeRaw={() => setTab("raw")} />
  : <RawTabContent contract={contract} {...existingProps} />}
```

`RawTabContent` is the existing scrollable-body content (At-a-glance, explainers, description, POC) extracted into a sibling component, or kept inline — implementer's choice. Cleaner as a sibling component.

### 2. New component — `frontend/src/components/DigestTab.jsx`

Renders the structured fields. Each section is hidden if its field is empty. Match the existing drawer's visual language (`SectionLabel`, gray-50 stat cards, brand colors).

Layout:

- **Header row:** "RFP Digest" title + confidence pill
  - `high` → green pill, "High confidence"
  - `medium` → amber pill, "Medium confidence"
  - `low` → gray pill, "Limited structure found — see Raw tab"
- **Scope summary:** prominent, brand-tinted card if present
- **Period of performance** + **Estimated value:** two stat cards side-by-side, matching At-a-glance styling
- **Deliverables:** SectionLabel + bulleted list
- **Submission requirements:** SectionLabel + bulleted list
- **Evaluation criteria:** SectionLabel + bulleted list
- **Key dates:** small inline list
- **Footer:** "Need the full text? Switch to Raw." (button that calls `onSeeRaw`)

Loading state: simple skeleton with three gray placeholder bars.

---

## Tests

### New file — `backend/tests/test_digest.py`

Unit tests for `parse_digest` (pure function, no fixtures needed):

```python
def test_parse_digest_extracts_scope_summary():
    contract = Contract(notice_id="x", description=(
        "SCOPE OF WORK\n"
        "The contractor shall provide IT support services for the Army. "
        "Services include help desk operations and network maintenance."
    ))
    digest = parse_digest(contract)
    assert "IT support" in (digest.scope_summary or "")

def test_parse_digest_extracts_bulleted_deliverables():
    contract = Contract(notice_id="x", description=(
        "Deliverables:\n"
        "- Monthly status reports\n"
        "- Quarterly system audits\n"
        "- Annual security review"
    ))
    digest = parse_digest(contract)
    assert len(digest.deliverables) == 3
    assert "Monthly status reports" in digest.deliverables

def test_parse_digest_extracts_evaluation_criteria():
    contract = Contract(notice_id="x", description=(
        "EVALUATION CRITERIA:\n"
        "1. Technical approach\n"
        "2. Past performance\n"
        "3. Price"
    ))
    digest = parse_digest(contract)
    assert len(digest.evaluation_criteria) == 3

def test_parse_digest_high_confidence():
    contract = Contract(notice_id="x", description=(
        "SCOPE OF WORK\nProvide services.\n\n"
        "DELIVERABLES:\n- Reports\n\n"
        "EVALUATION CRITERIA:\n- Technical\n\n"
        "PERIOD OF PERFORMANCE:\n12 months\n\n"
        "SUBMISSION INSTRUCTIONS:\nEmail proposal by deadline."
    ))
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "high"

def test_parse_digest_no_structure_returns_low_confidence():
    contract = Contract(notice_id="x", description="Just a single sentence with no headers.")
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "low"

def test_parse_digest_empty_description():
    contract = Contract(notice_id="x", description=None)
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "low"
    assert digest.deliverables == []
```

Endpoint tests — pattern matches existing `test_contracts.py`:

```python
@pytest.mark.asyncio
async def test_digest_endpoint_returns_structured_fields(client):
    payload = {**SAMPLE_OPPORTUNITY, "description": (
        "SCOPE OF WORK\nProvide IT services.\n\n"
        "DELIVERABLES:\n- Monthly reports\n- Quarterly audits"
    )}
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 1, "opportunitiesData": [payload]})
        )
        r = await client.get(f"/api/contracts/{payload['noticeId']}/digest")
    assert r.status_code == 200
    data = r.json()
    assert data["scope_summary"] is not None
    assert len(data["deliverables"]) == 2

@pytest.mark.asyncio
async def test_digest_endpoint_404_when_notice_missing(client):
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 0, "opportunitiesData": []})
        )
        r = await client.get("/api/contracts/missing-id/digest")
    assert r.status_code == 404
```

**Target:** 6–8 new tests. All 31 existing tests must continue to pass — run `python -m pytest -v` from `backend/` to confirm before push.

---

## Implementation sequence — atomic commits

1. **`feat: add ContractDigest model and digest service stub`** — `models/digest.py` complete; `services/digest.py` with `parse_digest` returning an empty digest (signature only). No tests yet. Verifies imports.
2. **`feat: implement digest text parser with heuristics`** — fill in `parse_digest`; add the 6 unit tests in `test_digest.py`. Green pytest.
3. **`feat: add /contracts/{notice_id}/digest endpoint`** — `build_digest` + the router route (placed before the wildcard) + 2 endpoint tests + optional TTL cache. Green pytest.
4. **`feat: digest tab in contract drawer`** — `DigestTab.jsx` + tab strip wiring in `ContractDetailDrawer.jsx` + fetch hook. Manual visual check on real contracts via dev server (a known-detailed RFP, a sparse one, an award notice).
5. **`docs: mark Phase A complete in BACKLOG`** — close the backlog item with commit refs.

---

## Non-goals (explicit out-of-scope)

- **No LLM-based summarization.** Heuristics only for v1. (LLM fallback for `low` confidence is a candidate for Phase A.5 once we have data on real-world parser hit rate.)
- **No new external data sources.** Phase A is parsing and UI only.
- **No similar-opportunities sidebar.** That's Phase B.
- **No historical award comparison.** That's Phase C (USAspending — BACKLOG 2026-05-23).

---

## Open questions for the next Opus session

- Real-world hit rate. Once shipped, sample 20 random contracts across NAICS codes and count how often each section is found. If `scope_summary` hits < 60%, the heuristics need a second pass before Phase B builds on top.
- Default tab. Current design defaults to Digest. If hit rate is low for any reason, Raw may need to be the default until the parser improves. Easy flip later.
- LLM fallback. Once we see where heuristics fall down, decide whether to add a small `description → digest` LLM call for `low`-confidence cases, gated behind a feature flag. Phase A.5 candidate.
- Notion logging. This spec and the resulting commits should be carried to the Notion Decisions and Backlog DBs via `scripts/notion_sync.py` on the next Claude Code session — idempotent, no manual push.

---

*Phase A spec · Designed by Opus · 2026-06-06*
