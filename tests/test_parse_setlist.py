"""Golden tests for parse_setlist_text and year-link mapping."""

from pathlib import Path

import pytest

from gd_scraper import parse_setlist_text, parse_venue_line

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_year_link_mapping_72_to_1972():
    """Document get_year_links year mapping: yy >= 72 → 1900+yy."""
    yy = 72
    year = 1900 + yy if yy >= 72 else 2000 + yy
    assert year == 1972
    yy95 = 95
    assert (1900 + yy95 if yy95 >= 72 else 2000 + yy95) == 1995


def test_winterland_1972_set_break():
    show = parse_setlist_text(
        _load("72_winterland.txt"),
        1972,
        "https://www.cs.cmu.edu/~mleone/gdead/dead-sets/72/1-2-72.txt",
    )
    assert show["venue"] == "Winterland Arena"
    assert show["city"] == "San Francisco"
    assert show["state"] == "CA"
    assert show["year"] == 1972
    assert show["date"] == "1972-01-02"
    assert "Truckin'" in show["sets"]["set1"]
    assert "Dark Star" in show["sets"]["set2"]
    assert show["sets"]["encore"] == []


def test_cornell_1977_encore():
    show = parse_setlist_text(
        _load("77_cornell.txt"),
        1977,
        "https://example.com/dead-sets/77/5-8-77.txt",
    )
    assert show["venue"] == "Barton Hall"
    assert show["date"] == "1977-05-08"
    assert "Scarlet Begonias" in show["sets"]["set2"]
    assert show["sets"]["encore"] == ["One More Saturday Night"]


def test_encore_multiple_songs():
    show = parse_setlist_text(
        _load("encore_multi.txt"),
        1985,
        "https://example.com/dead-sets/85/3-15-85.txt",
    )
    assert show["sets"]["encore"] == ["U.S. Blues", "Brokedown Palace"]
    assert "Playing in the Band" in show["sets"]["set2"]


def test_notes_stars_and_parens():
    show = parse_setlist_text(
        _load("notes_stars.txt"),
        1984,
        "https://example.com/dead-sets/84/7-13-84.txt",
    )
    assert any(n.startswith("*") for n in show["notes"])
    assert any(n.startswith("(") for n in show["notes"])
    # Arrow suffixes preserved as raw set tokens
    assert any("->" in s for s in show["sets"]["set2"])


def test_messy_header_venue_line():
    info = parse_venue_line("Some Hall, Boston, MA (Monday, 9/21/72)")
    assert info["venue"] == "Some Hall"
    assert info["city"] == "Boston"
    assert info["state"] == "MA"
    assert info["day_of_week"] == "Monday"
    assert info["date_raw"] == "9/21/72"


def test_no_paren_date_falls_back_to_url():
    show = parse_setlist_text(
        _load("no_paren_date.txt"),
        1973,
        "https://www.cs.cmu.edu/~mleone/gdead/dead-sets/73/6-10-73.txt",
    )
    assert show["date"] == "1973-06-10"
    assert show["date_raw"] == ""
    assert show["day_of_week"] == ""


def test_1995_late_era():
    show = parse_setlist_text(
        _load("95_late.txt"),
        1995,
        "https://example.com/dead-sets/95/2-19-95.txt",
    )
    assert show["year"] == 1995
    assert show["date"] == "1995-02-19"
    assert show["venue"] == "Delta Center"
    assert show["city"] == "Salt Lake City"
    assert show["sets"]["encore"] == ["Liberty"]
