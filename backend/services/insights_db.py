"""
SQLite persistent cache for NAICS insights data.

Two tables:
  monthly_counts — one row per (naics_code, set_aside, year, month)
  agency_counts  — one row per (naics_code, set_aside, agency)

TTL policy:
  Historical months  → 90 days  (completed months are stable)
  Current month      → 5 minutes (still accumulating)
  Agency totals      → 24 hours

The DB file lives at backend/data/insights.db and is committed to the repo
pre-seeded for all COMMON_NAICS codes so git pull gives instant data.
"""
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional

# Tests override this via INSIGHTS_DB_PATH env var to avoid touching the real DB
DB_PATH = Path(os.environ.get("INSIGHTS_DB_PATH",
               str(Path(__file__).parent.parent / "data" / "insights.db")))

TTL_HISTORICAL = 90 * 86_400   # 90 days
TTL_CURRENT    = 300            # 5 min
TTL_AGENCY     = 86_400         # 24 hours

_conn: Optional[sqlite3.Connection] = None


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_counts (
                naics_code TEXT    NOT NULL,
                set_aside  TEXT    NOT NULL DEFAULT '',
                year       INTEGER NOT NULL,
                month      INTEGER NOT NULL,
                count      INTEGER NOT NULL,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (naics_code, set_aside, year, month)
            )
        """)
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS agency_counts (
                naics_code TEXT    NOT NULL,
                set_aside  TEXT    NOT NULL DEFAULT '',
                agency     TEXT    NOT NULL,
                count      INTEGER NOT NULL,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (naics_code, set_aside, agency)
            )
        """)
        _conn.commit()
    return _conn


def get_monthly(naics: str, sa: str, year: int, month: int, ttl: int) -> Optional[int]:
    try:
        row = _db().execute(
            "SELECT count, fetched_at FROM monthly_counts "
            "WHERE naics_code=? AND set_aside=? AND year=? AND month=?",
            (naics, sa, year, month),
        ).fetchone()
        if row and (time.time() - row[1]) < ttl:
            return row[0]
    except Exception:
        pass
    return None


def set_monthly(naics: str, sa: str, year: int, month: int, count: int) -> None:
    try:
        _db().execute(
            "INSERT OR REPLACE INTO monthly_counts VALUES (?,?,?,?,?,?)",
            (naics, sa, year, month, count, int(time.time())),
        )
        _db().commit()
    except Exception:
        pass


def get_agencies(naics: str, sa: str) -> Optional[list[tuple[str, int]]]:
    """Return all agency rows for this (naics, set_aside) if all are fresh, else None."""
    try:
        rows = _db().execute(
            "SELECT agency, count, fetched_at FROM agency_counts "
            "WHERE naics_code=? AND set_aside=?",
            (naics, sa),
        ).fetchall()
        if rows and all((time.time() - r[2]) < TTL_AGENCY for r in rows):
            return [(r[0], r[1]) for r in rows]
    except Exception:
        pass
    return None


def set_agencies(naics: str, sa: str, agency_data: list[tuple[str, int]]) -> None:
    try:
        now = int(time.time())
        _db().executemany(
            "INSERT OR REPLACE INTO agency_counts VALUES (?,?,?,?,?)",
            [(naics, sa, a, c, now) for a, c in agency_data],
        )
        _db().commit()
    except Exception:
        pass
