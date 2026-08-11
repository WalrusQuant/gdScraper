# gdScraper implementation — Phases A–C (PRs 1–9)

Status: **implemented** (2026-08-10)

## Checklist

- [x] PR1 — README, CLAUDE, hero 1972–1995, run microcopy
- [x] PR2 — Date recovery (`gd_dates.py`, backfill script, scraper, night sort)
- [x] PR3 — Backfilled + sorted JSON (empty dates 1426 → 1)
- [x] PR4 — Footer attribution
- [x] PR5 — `songKey` + Playin'/Playing aliases
- [x] PR6 — Righteous H1, mockup2 accents, `display=optional`
- [x] PR7 — pytest fixtures + requirements pins (14 passed)
- [x] PR8 — Unknown location display + docs
- [x] PR9 — Song detail focus trap

Deferred (design stretch): PR10 multi-file split, PR11 this-day/random, PR12 SW, PR13 transition graph.

## Review notes

- Playin' in the Band merged count: **512** (was ~451 + ~125 split)
- Corpus: 1605 shows; residual undated: 1 (`1993 YEAR IN REVIEW`) at end of file
- No git repo yet — commit when ready
- No full CMU re-scrape performed

## Serve locally

```bash
source venv/bin/activate
python -m http.server 8000
```
