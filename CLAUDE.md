# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A fan tribute that scrapes Mark Leone's Grateful Dead setlist archive at CMU and presents it as a browsable single-page site. Two halves:

1. **`gd_scraper.py`** — one-shot Python scraper that crawls `https://www.cs.cmu.edu/~mleone/gdead/setlists.html`, parses each year's `.txt` show files, and writes `grateful_dead_setlists.json`.
2. **`index.html`** — static single-file SPA (inlined HTML/CSS/JS) that fetches that JSON at load time and handles all filtering/search/rendering client-side.

The data is static and finished (tours ended 1995). The scraper runs ad-hoc, not on a schedule. Prefer **`scripts/backfill_dates.py`** (offline) over a full CMU re-scrape for date fixes.

## Commands

```bash
# Activate the existing venv (requests + beautifulsoup4 already installed)
source venv/bin/activate

# Offline date recovery + sort (no network)
python scripts/backfill_dates.py

# Re-scrape the archive (writes grateful_dead_setlists.json, ~10 min with 0.3s delay)
# Only when parser/venue logic changes
python gd_scraper.py

# Serve the site locally — index.html fetches grateful_dead_setlists.json,
# so you need an HTTP server, not file://
python -m http.server 8000

# Tests
pip install -r requirements-dev.txt && pytest
```

No build step, no bundler.

## Architecture notes that matter

**Data shape.** Each show in the JSON is a flat dict: `date`, `date_raw`, `day_of_week`, `year`, `venue`, `city`, `state`, `source_url`, `sets: {set1, set2, encore}`, `notes`. Set arrays contain raw song strings — some entries aren't songs (parenthetical notes, jam markers). `index.html` uses an `isSong()` filter before counting/displaying.

**Date recovery.** Precedence: header ISO via `parse_date`/`date_raw` → `source_url` basename `M-D-YY.txt` (2-digit year → `19xx`) → empty. Do not invent `date_raw`/`day_of_week` from URL-only recovery. Sort with `show_date_sort_key` / `sortShowsByDate` (**ISO ascending, empty/non-ISO last**). Never bare `sort(key=date)` (puts `""` first).

**Run grouping is load-bearing (Map semantics).** Key is `normalize(venue)|city|state|year` via `runKey()` / `groupIntoRuns()` — **all** shows sharing that key form one card, including non-contiguous return engagements in a year (~**874** runs, ~**378** multi-night; consecutive-only would be ~927). UI copy: **“N shows · …” / “N shows at this venue in {year}”** — do not imply a single unbroken “stand.” Night order: `sortShowsByDate(run.shows)` after grouping. Cards can hold N nights.

**State + routing.** Three filters — `searchQuery`, `yearFilter`, `songFilter` — are serialized to `location.hash` via `readHash()`/`writeHash()` so deep links work (`#song=Sugaree&year=1977`). **All filter changes must go through `applyFilters()`** or state and URL desync.

**Song identity (`songKey`).** Join key = `alias(normalize(stripTrailingArrow(raw)))`. Counts, rare highlighting, transitions, and song filter match on `songKey`. Hash `#song=` stores canonical **display** string. Pills keep raw archive text. Small alias map merges Playin'/Playing in the Band (+ Reprise).

**Stats are derived once on load.** `songPlayCounts`, `topSongs`, and `songTransitions` are built in a single pass after `fetch()`. Rare-song highlighting uses count `< 10` by `songKey`. If you add a new stat, compute it in that same init pass rather than on every render.

**Pagination.** Rendering uses a simple `PAGE_SIZE` + "Load More" button (`renderNextPage()`) over **runs** (not shows) to avoid laying out ~1,600 cards at once. When filters change, `renderedCount` resets to 0.

**Empty city/state.** Often inherently unknown (~74 shows). UI shows **“Unknown”**; do not treat remaining empties as open parser bugs. Opaque headers include codes like `HJK` and `[location unknown]`.

**The two `mockup*.html` files are design explorations, not code.** They're static shells with hardcoded example data — kept for visual reference. Don't wire them to the real JSON; if a design idea from them lands, port it into `index.html`.

## Scraper parsing quirks

`parse_setlist_text()` in `gd_scraper.py` makes assumptions about the CMU archive's text format that aren't obvious:

- **Set breaks are detected by blank lines**, not explicit "Set II" headers. First blank line after Set I songs flips state to Set II.
- **Encores are marked by `E:` or `Encore:` prefix** and can contain multiple songs on one line separated by `/` or `,`.
- **Lines starting with `*` or `(` are treated as notes**, not songs.
- **Year is inferred from the year-index page** (`72.html` → 1972 via `yy >= 72 → 1900+yy`), not from the show file, because two-digit years in the raw files are ambiguous.

If parsing ever breaks, the first thing to check is whether the source files' formatting conventions hold for the year in question — earlier years are messier.

## Attribution

`attribution.md` credits Mark Leone (CMU), Jerry Stratton, and Tim Buller for the underlying data. This is a fan tribute, non-commercial. The UI footer must surface attribution; any public-facing deploy should keep it visible.

## Design doc

See `tasks/design-gdscraper.md` for product decisions and PR plan.
