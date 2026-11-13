"""Uji ReviewScraper tanpa internet: halaman ulasan palsu, urut dari yang terbaru."""

from datetime import date, datetime, timedelta

from suara.scraper import WIB, ReviewScraper

NEWEST = datetime(2026, 10, 16, 12, 0, tzinfo=WIB)


def fake_source(n: int, step_hours: float = 6, page: int = 200):
    """n ulasan palsu, satu tiap step_hours mundur dari NEWEST, dipecah per halaman seperti Google Play."""
    items = [
        {
            "reviewId": f"r{i}",
            "userName": "Nama Asli",
            "userImage": "https://foto",
            "content": f"ulasan {i}",
            "score": 1 + i % 5,
            "thumbsUpCount": 0,
            "appVersion": "1.0",
            # library mengembalikan waktu lokal mesin tanpa zona
            "at": (NEWEST - timedelta(hours=step_hours * i)).astimezone().replace(tzinfo=None),
            "replyContent": "terima kasih" if i % 3 == 0 else None,
        }
        for i in range(n)
    ]
    calls = []

    def fetch(app_id, token):
        start = token or 0
        calls.append(start)
        nxt = start + page if start + page < n else None
        return items[start : start + page], nxt

    return fetch, calls


def test_only_reviews_inside_range_are_kept():
    fetch, _ = fake_source(1000)
    res = ReviewScraper(fetch).fetch("x", date(2026, 10, 10), date(2026, 10, 12))
    at = res.reviews["at"]
    assert len(res.reviews) == 12  # 3 hari x 4 ulasan per hari
    assert at.min() >= datetime(2026, 10, 10, tzinfo=WIB)
    assert at.max() < datetime(2026, 10, 13, tzinfo=WIB)


def test_stops_after_passing_start_date():
    fetch, calls = fake_source(5000, step_hours=1)
    ReviewScraper(fetch).fetch("x", date(2026, 10, 15), date(2026, 10, 16))
    assert len(calls) == 1  # 200 ulasan satu per jam sudah mundur lebih dari 8 hari


def test_hit_limit_is_reported():
    fetch, _ = fake_source(5000, step_hours=0.1)
    res = ReviewScraper(fetch, max_fetch=400).fetch("x", date(2026, 1, 1), date(2026, 10, 16))
    assert res.hit_limit and res.fetched == 400


def test_all_reviews_exhausted_is_not_a_limit():
    fetch, _ = fake_source(300)
    res = ReviewScraper(fetch).fetch("x", date(2020, 1, 1), date(2026, 10, 16))
    assert not res.hit_limit and len(res.reviews) == 300


def test_reviewer_identity_is_not_kept():
    fetch, _ = fake_source(50)
    res = ReviewScraper(fetch).fetch("x", date(2026, 10, 1), date(2026, 10, 16))
    assert "userName" not in res.reviews.columns and "userImage" not in res.reviews.columns
    assert res.reviews["replied"].sum() == 17
