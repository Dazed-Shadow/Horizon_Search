"""
RFP Digest service — Phase A.

parse_digest: pure function that extracts structured fields from contract.description.
build_digest: async wrapper that fetches via sam_gov.get_contract_by_notice_id, then parses.
"""
import re
import time
from typing import Optional

from models.contract import Contract
from models.digest import ContractDigest, KeyDate

# ---------------------------------------------------------------------------
# In-memory TTL cache — keyed by notice_id, mirrors _response_cache pattern.
# ---------------------------------------------------------------------------
_DIGEST_CACHE: dict[str, tuple[float, ContractDigest]] = {}
_DIGEST_TTL = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Section-to-field keyword mapping
# ---------------------------------------------------------------------------
_SECTION_FIELD_MAP: list[tuple[str, list[str]]] = [
    ("scope_summary", [
        "scope of work", "statement of work", "sow", "description",
        "background", "project description", "objective", "purpose",
    ]),
    ("deliverables", [
        "deliverables", "required services", "tasks", "work required", "requirements",
    ]),
    ("submission_requirements", [
        "submission instructions", "proposal submission", "how to apply",
        "submission requirements", "quote submission", "instructions to offerors",
    ]),
    ("evaluation_criteria", [
        "evaluation criteria", "basis for award", "evaluation factors",
        "award basis", "selection criteria",
    ]),
    ("period_of_performance", [
        "period of performance", "performance period", "pop", "contract period",
    ]),
    ("estimated_value", [
        "estimated value", "anticipated value", "contract ceiling",
        "nte", "not to exceed", "magnitude",
    ]),
]

# Regex patterns for section header detection
_ALLCAPS_RE = re.compile(r"^[A-Z][A-Z\s\d\.\-/&]{3,}$")
_NUMBERED_RE = re.compile(r"^\d+\.\s+\S")
_LETTERED_RE = re.compile(r"^[A-Z]\.\s+\S")

# Regex for bullet markers (used when splitting section body into list items)
_BULLET_RE = re.compile(r"^[\-\*\•]\s+|^\d+\.\s+|^[A-Z]\.\s+")

# Key-date regex: label phrase + optional filler + date expression
_KEY_DATE_RE = re.compile(
    r"(Q\&A|Questions?|Pre-?proposal|Industry Day|Site Visit|Walk-?through|"
    r"Proposal Due|Offer Due|Response Due|Responses Due|Submissions? Due|"
    r"Closing Date|Deadline)"
    r".{0,80}?"
    r"(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})",
    re.IGNORECASE,
)


def _is_header(line: str) -> bool:
    """Return True if the line looks like a section header.

    Note: numbered/lettered prefix alone is NOT sufficient — that pattern
    matches list items like "1. Technical approach" inside an EVALUATION
    CRITERIA section. We require the numbered/lettered line to ALSO have
    either an all-caps body (after the prefix) or a trailing colon. This
    keeps "1. BACKGROUND" and "1. Scope of work:" as headers while letting
    "1. Technical approach" fall through to be parsed as a list item.
    """
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.endswith(":"):
        return True
    if _ALLCAPS_RE.match(stripped):
        return True
    if (_NUMBERED_RE.match(stripped) or _LETTERED_RE.match(stripped)) and len(stripped) < 80:
        # Strip the prefix; require all-caps body to count as a header
        content = re.sub(r"^(\d+|[A-Z])\.\s+", "", stripped)
        if content and content == content.upper() and any(c.isalpha() for c in content):
            return True
    return False


def _normalize_header(header: str) -> str:
    """Lowercase, strip trailing colon and whitespace."""
    return re.sub(r":\s*$", "", header.strip()).lower()


def _header_to_field(header_norm: str) -> Optional[str]:
    """Map a normalized header string to a ContractDigest field name (or None)."""
    for field, keywords in _SECTION_FIELD_MAP:
        for kw in keywords:
            if kw in header_norm:
                return field
    return None


def _split_sections(text: str) -> list[tuple[str, str]]:
    """
    Split description text into (header, body) pairs.
    The header for body that appears before any section header is an empty string.
    """
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_header = ""
    current_body: list[str] = []

    for line in lines:
        if _is_header(line):
            # Save previous section
            sections.append((current_header, "\n".join(current_body).strip()))
            current_header = line.strip()
            current_body = []
        else:
            current_body.append(line)

    # Final section
    sections.append((current_header, "\n".join(current_body).strip()))
    return sections


def _extract_list_items(body: str, cap: int = 8) -> list[str]:
    """
    Extract list items from a section body.
    Splits on bullet markers first; falls back to sentence boundaries.
    """
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    items: list[str] = []

    # Try bullet-marker split first
    for line in lines:
        cleaned = _BULLET_RE.sub("", line).strip()
        if cleaned:
            items.append(cleaned)

    # If no bullets found, try splitting on sentence boundaries
    if not items or all(i == items[0] for i in items):
        # Re-parse as sentences if bullet parsing gave us back the whole body as one item
        if len(items) == 1 and len(items[0]) > 100:
            sentences = re.split(r"(?<=[.!?])\s+", items[0])
            items = [s.strip() for s in sentences if s.strip()]

    return items[:cap]


def _first_sentences(text: str, max_chars: int = 280) -> str:
    """Return the first 1-2 sentences of text, whitespace-normalized, up to max_chars."""
    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    # Try to cut at sentence boundary
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    result = ""
    for s in sentences:
        candidate = (result + " " + s).strip() if result else s
        if len(candidate) > max_chars:
            break
        result = candidate
    return result or normalized[:max_chars]


def _extract_key_dates(text: str) -> list[KeyDate]:
    """Scan full description text for event + date patterns."""
    dates: list[KeyDate] = []
    seen_dates: set[str] = set()
    for match in _KEY_DATE_RE.finditer(text):
        label = match.group(1).strip()
        date_str = match.group(2).strip()
        key = f"{label.lower()}:{date_str}"
        if key in seen_dates:
            continue
        seen_dates.add(key)
        # Grab surrounding context: the sentence containing the match
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        context = text[start:end].strip()
        dates.append(KeyDate(label=label, date=date_str, context=context))
    return dates


def _compute_confidence(digest: ContractDigest) -> str:
    """
    high  = ≥4 of the 5 core fields populated
    medium = 2–3
    low    = 0–1
    """
    core = [
        digest.scope_summary,
        digest.deliverables if digest.deliverables else None,
        digest.submission_requirements if digest.submission_requirements else None,
        digest.evaluation_criteria if digest.evaluation_criteria else None,
        digest.period_of_performance,
    ]
    populated = sum(1 for f in core if f)
    if populated >= 4:
        return "high"
    if populated >= 2:
        return "medium"
    return "low"


def parse_digest(contract: Contract) -> ContractDigest:
    """Pure function — extract structured fields from contract.description via heuristics."""
    digest = ContractDigest(notice_id=contract.notice_id)

    description = contract.description
    if not description or not description.strip():
        return digest  # extraction_confidence stays "low"

    # Key dates: regex scan over full text first (before section splitting)
    digest.key_dates = _extract_key_dates(description)

    sections = _split_sections(description)

    for header, body in sections:
        if not body and not header:
            continue

        header_norm = _normalize_header(header)
        field = _header_to_field(header_norm)

        if field is None:
            continue

        if not body.strip():
            continue

        if field == "scope_summary":
            if digest.scope_summary is None:
                digest.scope_summary = _first_sentences(body)

        elif field == "deliverables":
            if not digest.deliverables:
                digest.deliverables = _extract_list_items(body)

        elif field == "submission_requirements":
            if not digest.submission_requirements:
                digest.submission_requirements = _extract_list_items(body)

        elif field == "evaluation_criteria":
            if not digest.evaluation_criteria:
                digest.evaluation_criteria = _extract_list_items(body)

        elif field == "period_of_performance":
            if digest.period_of_performance is None:
                first_line = next(
                    (l.strip() for l in body.splitlines() if l.strip()), None
                )
                digest.period_of_performance = first_line

        elif field == "estimated_value":
            if digest.estimated_value is None:
                first_line = next(
                    (l.strip() for l in body.splitlines() if l.strip()), None
                )
                digest.estimated_value = first_line

    digest.extraction_confidence = _compute_confidence(digest)
    return digest


async def build_digest(notice_id: str) -> Optional[ContractDigest]:
    """Fetch via sam_gov.get_contract_by_notice_id, then parse_digest. Returns None if 404."""
    # Check cache first
    cached = _DIGEST_CACHE.get(notice_id)
    if cached is not None:
        ts, digest = cached
        if (time.monotonic() - ts) < _DIGEST_TTL:
            return digest

    from services.sam_gov import get_contract_by_notice_id
    contract = await get_contract_by_notice_id(notice_id)
    if contract is None:
        return None

    digest = parse_digest(contract)
    _DIGEST_CACHE[notice_id] = (time.monotonic(), digest)
    return digest
