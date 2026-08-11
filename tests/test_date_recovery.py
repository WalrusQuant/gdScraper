"""Tests for gd_dates recovery and empty-last sort."""

from gd_dates import (
    apply_date_recovery,
    date_from_source_url,
    is_iso_date,
    parse_date,
    recover_date,
    show_date_sort_key,
)


def test_parse_date_two_digit_year():
    assert parse_date("2/19/95", 1995) == "1995-02-19"
    assert parse_date("1/2/72", 1972) == "1972-01-02"


def test_date_from_source_url():
    url = "https://www.cs.cmu.edu/~mleone/gdead/dead-sets/72/1-2-72.txt"
    assert date_from_source_url(url) == "1972-01-02"


def test_recover_prefers_header_over_url():
    show = {
        "date_raw": "5/8/77",
        "date": "",
        "year": 1977,
        "source_url": "https://example.com/dead-sets/77/5-9-77.txt",  # mismatch
    }
    iso, source = recover_date(show)
    assert iso == "1977-05-08"
    assert source == "header"


def test_recover_url_when_no_header():
    show = {
        "date_raw": "",
        "date": "",
        "year": 1972,
        "source_url": "https://example.com/dead-sets/72/1-2-72.txt",
    }
    iso, source = recover_date(show)
    assert iso == "1972-01-02"
    assert source == "url"


def test_show_date_sort_key_empty_last():
    shows = [
        {"date": ""},
        {"date": "1972-01-02"},
        {"date": "not-a-date"},
        {"date": "1995-02-19"},
    ]
    ordered = sorted(shows, key=show_date_sort_key)
    assert ordered[0]["date"] == "1972-01-02"
    assert ordered[1]["date"] == "1995-02-19"
    assert ordered[-1]["date"] in ("", "not-a-date")
    assert not is_iso_date(ordered[-1]["date"])
    # Residual undated must not lead
    assert is_iso_date(ordered[0]["date"])


def test_apply_date_recovery_mutates_and_sorts():
    shows = [
        {
            "date": "",
            "date_raw": "",
            "year": 1973,
            "venue": "B",
            "source_url": "https://x/dead-sets/73/6-10-73.txt",
        },
        {
            "date": "",
            "date_raw": "1/2/72",
            "year": 1972,
            "venue": "A",
            "source_url": "https://x/dead-sets/72/1-2-72.txt",
        },
        {
            "date": "",
            "date_raw": "",
            "year": 1993,
            "venue": "YEAR IN REVIEW",
            "source_url": "https://x/dead-sets/93/review.txt",
        },
    ]
    stats = apply_date_recovery(shows, log_conflicts=False)
    assert stats["empty_after"] == 1
    assert shows[0]["date"] == "1972-01-02"
    assert shows[1]["date"] == "1973-06-10"
    assert shows[-1]["venue"] == "YEAR IN REVIEW"
    assert not is_iso_date(shows[-1]["date"])
