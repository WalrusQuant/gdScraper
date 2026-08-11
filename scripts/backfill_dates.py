#!/usr/bin/env python3
"""
Offline date recovery for grateful_dead_setlists.json.

No network. Recovers ISO dates from date_raw / source_url, sorts with
empty/non-ISO last, rewrites the JSON in place.

Usage (from repo root):
  python scripts/backfill_dates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gd_dates import apply_date_recovery, is_iso_date  # noqa: E402

OUTPUT = ROOT / "grateful_dead_setlists.json"


def main() -> int:
    if not OUTPUT.exists():
        print(f"Missing {OUTPUT}", file=sys.stderr)
        return 1

    with open(OUTPUT, encoding="utf-8") as f:
        shows = json.load(f)

    if not isinstance(shows, list):
        print("Expected a JSON array of shows", file=sys.stderr)
        return 1

    stats = apply_date_recovery(shows, log_conflicts=True)

    # Spot-checks
    winterland = next(
        (
            s
            for s in shows
            if s.get("source_url", "").endswith("/72/1-2-72.txt")
        ),
        None,
    )
    if winterland:
        print(f"  spot-check Winterland 1-2-72 → date={winterland.get('date')!r}")
        if winterland.get("date") != "1972-01-02":
            print("  WARNING: expected 1972-01-02", file=sys.stderr)

    if shows and not is_iso_date(shows[0].get("date") or ""):
        print(
            "  WARNING: first show is not ISO-dated (empty-last sort may have failed)",
            file=sys.stderr,
        )
    if shows and not is_iso_date(shows[-1].get("date") or ""):
        print(f"  residual undated at end: venue={shows[-1].get('venue')!r}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"Done: {stats['count']} shows | empty dates "
        f"{stats['empty_before']} → {stats['empty_after']} | "
        f"conflicts={stats['conflicts']}"
    )
    if stats["empty_after"] > 1:
        print(f"WARNING: empty dates after backfill = {stats['empty_after']} (target ≤ 1)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
