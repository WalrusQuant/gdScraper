"""
Grateful Dead Setlist Scraper
Scrapes https://www.cs.cmu.edu/~mleone/gdead/setlists.html
Outputs: grateful_dead_setlists.json
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import logging

from gd_dates import apply_date_recovery, parse_date, recover_date

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "https://www.cs.cmu.edu/~mleone/gdead/"
OUTPUT_FILE = "grateful_dead_setlists.json"
FAILED_LOG = "failed_shows.log"
DELAY = 0.3  # seconds between requests — be polite to the old server

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

failed_shows = []


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch(url: str) -> str | None:
    """Fetch a URL and return text, or None on failure."""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log.warning(f"FAILED {url} — {e}")
        return None


def parse_venue_line(line: str):
    """
    Parse the first line of a .txt file.
    Example: 'Delta Center, Salt Lake City, UT (Sunday, 2/19/95)'
    Returns dict with venue, city, state, day_of_week, date_raw
    """
    result = {
        "venue": "",
        "city": "",
        "state": "",
        "day_of_week": "",
        "date_raw": "",
    }

    # Extract the parenthetical (Sunday, 2/19/95)
    paren_match = re.search(r"\(([^)]+)\)", line)
    if paren_match:
        paren = paren_match.group(1)
        # day and date split by comma
        paren_parts = [p.strip() for p in paren.split(",")]
        if len(paren_parts) >= 2:
            result["day_of_week"] = paren_parts[0]
            result["date_raw"] = paren_parts[1]

    # Everything before the parenthetical is venue info
    venue_part = re.sub(r"\s*\([^)]*\)", "", line).strip()
    # Split by comma: last part is state, second-to-last is city, rest is venue
    parts = [p.strip() for p in venue_part.split(",")]
    if len(parts) >= 3:
        result["venue"] = ", ".join(parts[:-2])
        result["city"] = parts[-2]
        result["state"] = parts[-1]
    elif len(parts) == 2:
        result["venue"] = parts[0]
        result["city"] = parts[1]
    elif len(parts) == 1:
        result["venue"] = parts[0]

    return result


def parse_setlist_text(text: str, year: int, source_url: str) -> dict:
    """
    Parse raw .txt content into a structured dict.
    Handles set breaks by looking for blank lines between song groups,
    and 'E:' prefix for encores.
    """
    lines = text.strip().splitlines()

    if not lines:
        return {}

    # First line = header
    header_line = lines[0].strip()
    venue_info = parse_venue_line(header_line)

    set1 = []
    set2 = []
    encore = []
    notes = []

    # Track which set we're in
    # Sets are separated by a blank line; encore lines start with 'E:'
    current_set = "set1"
    blank_count = 0
    set_break_seen = False

    for line in lines[1:]:
        stripped = line.strip()

        # blank line = potential set break
        if stripped == "":
            blank_count += 1
            if blank_count == 1 and current_set == "set1" and set1:
                # first blank after set1 songs → move to set2
                current_set = "set2"
                set_break_seen = True
            continue
        else:
            blank_count = 0

        # Encore: line starts with 'E:' or 'Encore:'
        if re.match(r"^E\s*:", stripped, re.IGNORECASE) or re.match(r"^Encore\s*:", stripped, re.IGNORECASE):
            current_set = "encore"
            song_part = re.sub(r"^(Encore|E)\s*:\s*", "", stripped, flags=re.IGNORECASE).strip()
            if song_part:
                # Sometimes multiple songs on one line separated by comma or /
                for s in re.split(r"\s*/\s*|\s*,\s*", song_part):
                    s = s.strip()
                    if s:
                        encore.append(s)
            continue

        # Notes: lines starting with * or ( are notes/comments
        if stripped.startswith("*") or stripped.startswith("("):
            notes.append(stripped)
            continue

        # If we're in a "notes" zone (after songs, multiple stars)
        # treat remaining starred/parenthetical lines as notes
        if current_set == "encore" and not re.match(r"^[A-Za-z0-9'\"]", stripped):
            notes.append(stripped)
            continue

        # Regular song line
        if current_set == "set1":
            set1.append(stripped)
        elif current_set == "set2":
            set2.append(stripped)
        elif current_set == "encore":
            encore.append(stripped)

    show = {
        "date": parse_date(venue_info["date_raw"], year) if venue_info["date_raw"] else "",
        "date_raw": venue_info["date_raw"],
        "day_of_week": venue_info["day_of_week"],
        "year": year,
        "venue": venue_info["venue"],
        "city": venue_info["city"],
        "state": venue_info["state"],
        "source_url": source_url,
        "sets": {
            "set1": set1,
            "set2": set2,
            "encore": encore,
        },
        "notes": notes,
    }
    # Prefer header ISO, else URL basename — do not invent date_raw / day_of_week
    iso, _src = recover_date(show, year)
    show["date"] = iso
    return show


# ── Main Scraping Logic ────────────────────────────────────────────────────────
def get_year_links() -> list[tuple[int, str]]:
    """Scrape main index → list of (year, url)."""
    html = fetch(BASE_URL + "setlists.html")
    if not html:
        raise RuntimeError("Could not fetch main index page.")
    soup = BeautifulSoup(html, "html.parser")
    years = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Year links look like '95.html', '72.html', etc.
        m = re.match(r"^(\d{2})\.html$", href)
        if m:
            yy = int(m.group(1))
            year = 1900 + yy if yy >= 72 else 2000 + yy
            years.append((year, BASE_URL + href))
    return sorted(years)


def get_show_links(year: int, year_url: str) -> list[tuple[str, str]]:
    """Scrape a year page → list of (show_label, txt_url)."""
    time.sleep(DELAY)
    html = fetch(year_url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    shows = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("dead-sets/") and href.endswith(".txt"):
            label = a.get_text(strip=True)
            txt_url = BASE_URL + href
            shows.append((label, txt_url))
    return shows


def scrape_show(year: int, label: str, txt_url: str) -> dict | None:
    """Fetch and parse a single show .txt file."""
    time.sleep(DELAY)
    text = fetch(txt_url)
    if not text:
        failed_shows.append({"url": txt_url, "label": label, "reason": "fetch failed"})
        return None
    try:
        show = parse_setlist_text(text, year, txt_url)
        return show
    except Exception as e:
        failed_shows.append({"url": txt_url, "label": label, "reason": str(e)})
        log.warning(f"Parse error for {txt_url}: {e}")
        return None


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    log.info("Starting Grateful Dead setlist scraper...")
    all_shows = []

    year_links = get_year_links()
    log.info(f"Found {len(year_links)} years: {[y for y, _ in year_links]}")

    for year, year_url in year_links:
        log.info(f"── {year} ──")
        show_links = get_show_links(year, year_url)
        log.info(f"  {len(show_links)} shows found")

        for label, txt_url in show_links:
            log.info(f"  Scraping: {label}")
            show = scrape_show(year, label, txt_url)
            if show:
                all_shows.append(show)

    # ISO ascending, empty/non-ISO last (shared with offline backfill)
    stats = apply_date_recovery(all_shows, log_conflicts=False)
    log.info(
        f"Date recovery: empty after={stats['empty_after']} conflicts={stats['conflicts']}"
    )

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_shows, f, indent=2, ensure_ascii=False)
        f.write("\n")

    log.info(f"\n✅ Done! {len(all_shows)} shows saved to {OUTPUT_FILE}")

    if failed_shows:
        with open(FAILED_LOG, "w", encoding="utf-8") as f:
            for item in failed_shows:
                f.write(f"{item['url']} | {item['label']} | {item['reason']}\n")
        log.warning(f"⚠️  {len(failed_shows)} shows failed — see {FAILED_LOG}")
    else:
        log.info("No failures.")


if __name__ == "__main__":
    main()
