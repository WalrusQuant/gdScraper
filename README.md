# Grateful Dead Setlist Archive

A fan tribute that scrapes Mark Leone’s Grateful Dead setlist archive at CMU and presents it as a browsable static site.

**Coverage:** 1972–1995 · **~1,605 shows** · non-commercial fan project

## Quick start

```bash
# Activate venv (requests + beautifulsoup4)
source venv/bin/activate

# Serve the site — required so fetch() can load the JSON
# (file:// will not work)
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000).

## Commands

```bash
# Offline date recovery + chronological sort (no network)
python scripts/backfill_dates.py

# Full re-scrape from CMU (~10 min, be polite — 0.3s delay)
# Only when parser/venue logic changes, not for routine date fixes
python gd_scraper.py

# Tests
pip install -r requirements-dev.txt
pytest
```

## Architecture

| Piece | Role |
| --- | --- |
| `gd_scraper.py` | One-shot scraper → `grateful_dead_setlists.json` |
| `scripts/backfill_dates.py` | Offline ISO date recovery + empty-last sort |
| `index.html` | Static SPA: filter, run grouping, stats, deep links |
| `attribution.md` | Source credits (also shown in UI footer) |

Data is finished (tours ended 1995). The scraper is ad-hoc, not scheduled. Prefer **offline backfill** over re-scraping CMU.

## Filters & deep links

Hash params (via `applyFilters()` + `writeHash()`):

- `#year=1977`
- `#song=Sugaree`
- `#q=winterland`
- combined: `#song=Sugaree&year=1977`

## Non-goals

Accounts, live scrape-as-a-service, multi-band CMS, streaming, social features, backend API for setlists.

## Deploy

Static host: **GitHub Pages** (or any static host). Ship `index.html` + `grateful_dead_setlists.json` (+ optional assets).

## Attribution

Setlist data from [Mark Leone’s CMU archive](https://www.cs.cmu.edu/~mleone/gdead/setlists.html), originally by Jerry Stratton and others; 1995 data by Tim Buller. This site is a fan tribute and is not affiliated with the Grateful Dead or related entities. See `attribution.md`.

## Design

Product/architecture design: [`tasks/design-gdscraper.md`](tasks/design-gdscraper.md).
