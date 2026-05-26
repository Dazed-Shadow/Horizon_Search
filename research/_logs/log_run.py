#!/usr/bin/env python3
"""
Shared timing helper for pipeline agents.

Appends one JSONL line per call to research/data/_logs/<agent>_<YYYY-MM-DD>.jsonl.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

HERE     = Path(__file__).resolve().parent
LOG_DIR  = HERE.parent / "data" / "_logs"


def log(
    agent: str,
    started_at: datetime,
    record_count: int,
    errors: list[str] | None = None,
) -> None:
    """Append one JSONL timing record for the given agent run."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    finished_at = datetime.now(timezone.utc)
    # Ensure started_at is tz-aware for consistent subtraction
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    date_str    = finished_at.strftime("%Y-%m-%d")
    log_file    = LOG_DIR / f"{agent}_{date_str}.jsonl"

    record = {
        "agent":        agent,
        "started_at":   started_at.isoformat(),
        "finished_at":  finished_at.isoformat(),
        "duration_ms":  duration_ms,
        "record_count": record_count,
        "errors":       errors if errors is not None else [],
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(
        f"[log_run] {agent} | {record_count} records | {duration_ms} ms"
        + (f" | {len(record['errors'])} error(s)" if record["errors"] else "")
    )
