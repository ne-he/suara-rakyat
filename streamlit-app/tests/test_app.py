"""Uji alur tampilan dengan Streamlit AppTest. Google Play diganti sumber palsu, jadi tes jalan tanpa internet."""

from datetime import datetime, timedelta

import pytest
from streamlit.testing.v1 import AppTest

import suara.scraper as scraper_mod
from suara.scraper import WIB, AppNotFound

TEXTS = ["aplikasi error terus gak bisa login", "mantap sangat membantu", "otp tidak masuk masuk", "terima kasih bagus"]


def fake_pages(n: int, newest: datetime | None = None, step_hours: float = 3):
    newest = newest or datetime.now(WIB)
    items = [
        {
            "reviewId": f"r{i}",
            "userName": "Nama Asli",
            "userImage": "https://foto",
            "content": TEXTS[i % len(TEXTS)],
            "score": [1, 5, 1, 5][i % 4],
            "thumbsUpCount": i % 7,
            "appVersion": "1.0",
            "at": (newest - timedelta(hours=step_hours * i)).astimezone().replace(tzinfo=None),
            "replyContent": None,
        }
        for i in range(n)
    ]

    def fetch(app_id, token):
        start = token or 0
        return items[start : start + 200], (start + 200 if start + 200 < n else None)

    return fetch


@pytest.fixture
def app(monkeypatch):
    seen = {}

    def info(app_id):
        seen["app_id"] = app_id
        if app_id == "com.tidak.ada":
            raise AppNotFound(app_id)
        return {"title": "Aplikasi Uji", "developer": "Instansi Uji", "icon": None, "reviews": 100}

    monkeypatch.setattr(scraper_mod.ReviewScraper, "app_info", staticmethod(info))
    monkeypatch.setattr(scraper_mod, "_fetch_page", fake_pages(400))
    at = AppTest.from_file("app.py", default_timeout=120)
    at.seen = seen
    return at.run()


def test_initial_page(app):
    assert app.title[0].value.endswith("Suara Rakyat")
    assert len(app.selectbox[0].options) == 7  # 6 aplikasi + aplikasi lain
    assert app.date_input[1].value - app.date_input[0].value == timedelta(days=6)
    assert not app.exception


def test_start_after_end_is_rejected(app):
    today = app.date_input[1].value
    app.date_input[0].set_value(today)
    app.date_input[1].set_value(today - timedelta(days=3)).run()
    app.button[0].click().run()
    assert any("Start date" in e.value for e in app.error)
    assert "hasil" not in app.session_state


def test_invalid_custom_app_id(app):
    app.selectbox[0].set_value("Aplikasi lain (isi application ID)").run()
    app.text_input[0].set_value("bukan id").run()
    app.button[0].click().run()
    assert any("application ID" in e.value for e in app.error)


def test_play_store_link_is_accepted(app):
    app.selectbox[0].set_value("Aplikasi lain (isi application ID)").run()
    app.text_input[0].set_value("https://play.google.com/store/apps/details?id=com.contoh.app&hl=id").run()
    app.button[0].click().run()
    assert app.seen["app_id"] == "com.contoh.app"
    assert not app.error


def test_unknown_app(app):
    app.selectbox[0].set_value("Aplikasi lain (isi application ID)").run()
    app.text_input[0].set_value("com.tidak.ada").run()
    app.button[0].click().run()
    assert any("tidak ditemukan" in e.value for e in app.error)


def test_successful_search_shows_dashboard(app):
    app.button[0].click().run()
    assert not app.exception and not app.error
    labels = [m.label for m in app.metric]
    assert labels == ["Ulasan dibaca", "Negatif", "Netral", "Positif"]
    shown = app.dataframe[0].value
    assert set(shown["nada"]) == {"Negatif"}  # default daftar menampilkan ulasan negatif
    assert "userName" not in shown.columns
    hasil = app.session_state["hasil"]
    start = datetime.combine(hasil["start"], datetime.min.time(), WIB)
    assert hasil["res"].reviews["at"].min() >= start
    assert int(app.metric[0].value.replace(".", "")) == len(hasil["res"].reviews)
    assert len(shown) == hasil["analysis"].counts()["negative"]


def test_filter_positive(app):
    app.button[0].click().run()
    app.button_group[0].set_value("Positif").run()
    assert set(app.dataframe[0].value["nada"]) == {"Positif"}


def test_empty_range(app, monkeypatch):
    monkeypatch.setattr(scraper_mod, "_fetch_page", fake_pages(50, newest=datetime.now(WIB) - timedelta(days=60)))
    app.button[0].click().run()
    assert any("Tidak ada ulasan" in i.value for i in app.info)


def test_limit_warning(app, monkeypatch):
    monkeypatch.setattr(scraper_mod, "_fetch_page", fake_pages(3000, step_hours=0.01))
    monkeypatch.setattr(scraper_mod.ReviewScraper, "max_fetch", 1000)
    app.button[0].click().run()
    assert any("dibatasi 1.000 ulasan" in w.value for w in app.warning)
