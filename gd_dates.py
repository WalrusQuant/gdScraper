"""
Shared date recovery and sort helpers for gd_scraper and offline backfill.

Date precedence:
  1. Header date_raw via parse_date → ISO YYYY-MM-DD
  2. source_url basename M-D-YY.txt (2-digit year → 19xx for this corpus)
  3. empty string

Sort: ISO ascending, empty / non-ISO last (never bare key=date).
"""

from __future__ import annotations

import re
from typing import Any

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_DATE_RE = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{2,4})\.txt$")


def parse_date(raw_date: str, year: int) -> str:
    """
    Convert '2/19/95' or '2/19/1995' to 'YYYY-MM-DD'.
    Returns raw string if parsing fails (not always empty).
    """
    try:
        parts = (raw_date or "").strip().split("/")
        if len(parts) == 3:
            m, d, y = parts
            if len(y) == 2:
                y = f"19{y}"
            return f"{y}-{int(m):02d}-{int(d):02d}"
    except Exception:
        pass
    return raw_date or ""


def is_iso_date(value: str) -> bool:
    return bool(value and ISO_DATE_RE.fullmatch(value))


def date_from_source_url(source_url: str) -> str:
    """Recover ISO date from setlist .txt URL basename, or ''."""
    if not source_url:
        return ""
    m = URL_DATE_RE.search(source_url)
    if not m:
        return ""
    month, day, yr = m.group(1), m.group(2), m.group(3)
    if len(yr) == 2:
        yr = f"19{yr}"
    try:
        return f"{int(yr):04d}-{int(month):02d}-{int(day):02d}"
    except ValueError:
        return ""


def recover_date(show: dict[str, Any], year: int | None = None) -> tuple[str, str]:
    """
    Return (iso_date, source) where source is 'header' | 'url' | ''.

    Conflict rule: if header ISO and URL ISO both exist and disagree,
    keep header and return source 'header' (caller may log).
    Does not invent date_raw / day_of_week.
    """
    yr = year if year is not None else int(show.get("year") or 0)
    raw = show.get("date_raw") or ""
    header = parse_date(raw, yr) if raw else (show.get("date") or "")
    header_iso = header if is_iso_date(header) else ""
    # If current date field is already ISO and no date_raw, treat as header
    if not header_iso and is_iso_date(show.get("date") or ""):
        header_iso = show["date"]

    url_iso = date_from_source_url(show.get("source_url") or "")

    if header_iso and url_iso and header_iso != url_iso:
        return header_iso, "header"  # conflict: keep header
    if header_iso:
        return header_iso, "header"
    if url_iso:
        return url_iso, "url"
    return "", ""


def show_date_sort_key(show: dict[str, Any]) -> tuple:
    """ISO ascending; empty / non-ISO last. Do not use bare date string as key."""
    d = show.get("date") or ""
    if is_iso_date(d):
        return (0, d)
    return (1, "")


def apply_date_recovery(shows: list[dict[str, Any]], log_conflicts: bool = True) -> dict[str, int]:
    """
    Mutate shows in place: set date from recover_date, sort with show_date_sort_key.
    Returns stats dict.
    """
    empty_before = sum(1 for s in shows if not is_iso_date(s.get("date") or ""))
    conflicts = 0
    for show in shows:
        date, source = recover_date(show)
        url_iso = date_from_source_url(show.get("source_url") or "")
        raw = show.get("date_raw") or ""
        yr = int(show.get("year") or 0)
        header_try = parse_date(raw, yr) if raw else ""
        if is_iso_date(header_try) and url_iso and header_try != url_iso:
            conflicts += 1
            if log_conflicts:
                print(
                    f"  date conflict header={header_try} url={url_iso} "
                    f"venue={show.get('venue')} — keeping header"
                )
        show["date"] = date

    shows.sort(key=show_date_sort_key)
    empty_after = sum(1 for s in shows if not is_iso_date(s.get("date") or ""))
    return {
        "empty_before": empty_before,
        "empty_after": empty_after,
        "conflicts": conflicts,
        "count": len(shows),
    }
