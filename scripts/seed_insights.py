#!/usr/bin/env python3
"""
Pre-populate the SQLite insights cache for all common NAICS codes.

Run from the repo root:
    python scripts/seed_insights.py

Requires SAM_GOV_API_KEY in backend/.env.

Each NAICS code costs 24 monthly calls + 15 agency calls = 39 SAM.gov calls.
Free-tier daily limit is ~1,000 calls, so ~25 codes per day maximum.

The resulting backend/data/insights.db is committed to the repo so that
after a git pull the Insights page works instantly for all seeded codes.
"""
import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load .env manually (no python-dotenv dependency)
def _load_env() -> None:
    env_file = REPO_ROOT / "backend" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

_load_env()

from services.insights import get_naics_activity  # noqa: E402

# All codes from frontend/src/utils/constants.js COMMON_NAICS
NAICS_TO_SEED = [
    # Technology & IT
    "511210", "517110", "517410", "518210", "519290",
    "541511", "541512", "541513", "541519", "811212",
    # Professional & Consulting Services
    "541211", "541310", "541330", "541380",
    "541611", "541612", "541613", "541620", "541690",
    "541711", "541715", "541990",
    # Administrative & Support Services
    "561110", "561210", "561320", "561612", "561621",
    # Construction
    "236115", "236220", "237110", "237310", "237990",
    "238110", "238990",
    # Healthcare & Social Assistance
    "621111", "621210", "621330", "621391",
    # Logistics & Supply Chain
    "484110", "484121", "488510", "493110",
]


async def seed_code(code: str, idx: int, total: int) -> bool:
    print(f"  [{idx:02d}/{total}] NAICS {code} ...", end=" ", flush=True)
    try:
        await get_naics_activity(code, None, 24)
        print("✓")
        return True
    except Exception as exc:
        msg = str(exc)
        if "429" in msg or "limit" in msg.lower():
            print(f"RATE LIMITED — stopping here. Run again tomorrow.")
            return False
        print(f"✗  {exc}")
        return True  # continue to next code on non-rate-limit errors


async def main() -> None:
    api_key = os.getenv("SAM_GOV_API_KEY", "")
    if not api_key:
        print("ERROR: SAM_GOV_API_KEY not set. Add it to backend/.env and retry.")
        sys.exit(1)

    total = len(NAICS_TO_SEED)
    print(f"Seeding {total} NAICS codes × 24 months (up to {total * 39} SAM.gov calls)")
    print(f"Free-tier limit is ~1,000 calls/day — script stops automatically on 429.\n")

    for i, code in enumerate(NAICS_TO_SEED, 1):
        ok = await seed_code(code, i, total)
        if not ok:
            break
        if i < total:
            await asyncio.sleep(0.5)  # brief pause between codes

    print("\nDone. DB written to backend/data/insights.db")
    print("Commit the DB so git pull gives instant data: git add backend/data/insights.db")


asyncio.run(main())
