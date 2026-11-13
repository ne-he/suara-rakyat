"""Ambil ulasan Google Play per rentang tanggal lewat google-play-scraper.

Library ini tidak punya filter tanggal. Ulasan diambil dari yang terbaru, 200 per halaman,
lalu berhenti begitu sudah melewati start date. Nama dan foto pengulas tidak pernah disimpan.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from google_play_scraper import Sort, app, reviews
from google_play_scraper.exceptions import NotFoundError

WIB = ZoneInfo("Asia/Jakarta")
PAGE_SIZE = 200
MAX_FETCH = 10_000
COLUMNS = ["review_id", "at", "score", "content", "app_version", "thumbs_up", "replied"]

Page = tuple[list[dict], object | None]


def _fetch_page(app_id: str, token: object | None) -> Page:
    page, nxt = reviews(app_id, lang="id", country="id", sort=Sort.NEWEST, count=PAGE_SIZE, continuation_token=token)
    return page, (nxt if nxt.token is not None else None)


@dataclass
class ScrapeResult:
    reviews: pd.DataFrame
    fetched: int  # semua ulasan yang diambil, termasuk yang di luar rentang
    hit_limit: bool  # berhenti karena MAX_FETCH sebelum sampai start date
    oldest_seen: datetime | None


class AppNotFound(Exception):
    pass


class ReviewScraper:
    max_fetch: int = MAX_FETCH

    def __init__(self, fetch_page: Callable[[str, object | None], Page] | None = None, max_fetch: int | None = None) -> None:
        self.fetch_page = fetch_page or _fetch_page
        if max_fetch is not None:
            self.max_fetch = max_fetch

    @staticmethod
    def app_info(app_id: str) -> dict:
        try:
            d = app(app_id, lang="id", country="id")
        except NotFoundError as e:
            raise AppNotFound(app_id) from e
        return {"title": d["title"], "developer": d["developer"], "icon": d.get("icon"), "reviews": d.get("reviews")}

    def fetch(
        self,
        app_id: str,
        start: date,
        end: date,
        on_progress: Callable[[int, datetime | None], None] | None = None,
    ) -> ScrapeResult:
        start_dt = datetime.combine(start, time.min, WIB)
        end_dt = datetime.combine(end + timedelta(days=1), time.min, WIB)  # end date ikut dihitung penuh
        rows: list[dict] = []
        fetched, token, oldest, reached_start = 0, None, None, False
        while fetched < self.max_fetch:
            page, token = self.fetch_page(app_id, token)
            if not page:
                reached_start = True  # tidak ada ulasan lagi
                break
            fetched += len(page)
            for r in page:
                # library memberi waktu lokal mesin tanpa zona, astimezone menafsirkannya sebagai waktu lokal itu
                at = r["at"].astimezone(WIB)
                oldest = at if oldest is None or at < oldest else oldest
                if start_dt <= at < end_dt:
                    rows.append(
                        {
                            "review_id": r["reviewId"],
                            "at": at,
                            "score": r["score"],
                            "content": r["content"] or "",
                            "app_version": r.get("appVersion"),
                            "thumbs_up": r.get("thumbsUpCount", 0),
                            "replied": bool(r.get("replyContent")),
                        }
                    )
            if on_progress:
                on_progress(fetched, oldest)
            if (oldest is not None and oldest < start_dt) or token is None:
                reached_start = True
                break
        df = pd.DataFrame(rows, columns=COLUMNS).drop_duplicates("review_id").reset_index(drop=True)
        return ScrapeResult(df, fetched, not reached_start, oldest)
