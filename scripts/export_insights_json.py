#!/usr/bin/env python3
"""
Export pre-seeded SQLite insights data to a static JSON file.

Run from the repo root:
    python scripts/export_insights_json.py

Reads backend/data/insights.db (no SAM.gov calls needed — uses cached data).
Writes frontend/public/naics-insights.json for Vite to serve as a static asset.

The frontend loads this file directly, so the Insights page works for all
42 common NAICS codes even when the backend is not running.
"""
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))


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

NAICS_CODES = [
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
    # Healthcare
    "621111", "621210", "621330", "621391",
    # Logistics & Supply Chain
    "484110", "484121", "488510", "493110",
]


async def export() -> None:
    today = date.today().isoformat()
    output = {
        "generated_at": today,
        "coverage_months": 24,
        "codes": {},
    }

    total = len(NAICS_CODES)
    for i, code in enumerate(NAICS_CODES, 1):
        print(f"  [{i:02d}/{total}] {code} ...", end=" ", flush=True)
        try:
            resp = await get_naics_activity(code, None, 24)
            output["codes"][code] = resp.model_dump(mode="json")
            print("✓")
        except Exception as exc:
            print(f"✗  {exc}")

    out_path = REPO_ROOT / "frontend" / "public" / "naics-insights.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"\nWrote {len(output['codes'])} codes → {out_path} ({size_kb}KB)")


asyncio.run(export())
