from datetime import datetime, timedelta

import pandas as pd
import pytest

from suara.analysis import ReviewAnalysis
from suara.classifier import SentimentClassifier
from suara.scraper import WIB

TEXTS = [
    "aplikasi error terus gak bisa login",
    "otp tidak masuk, error terus",
    "mantap sangat membantu",
    "mantap terima kasih",
    "⭐⭐⭐",
    "nik saya 3171234567890001 tidak terdaftar",
]


@pytest.fixture(scope="module")
def analysis():
    t0 = datetime(2026, 10, 16, 9, tzinfo=WIB)
    df = pd.DataFrame(
        {
            "review_id": [f"r{i}" for i in range(len(TEXTS))],
            "at": [t0 - timedelta(days=i) for i in range(len(TEXTS))],
            "score": [1, 1, 5, 5, 3, 1],
            "content": TEXTS,
            "app_version": "1.0",
            "thumbs_up": 0,
            "replied": [True, False, False, False, False, False],
        }
    )
    return ReviewAnalysis(df, SentimentClassifier().predict_many(TEXTS))


def test_counts_exclude_unreadable(analysis):
    c = analysis.counts()
    assert sum(c.values()) == 5 and analysis.unreadable() == 1
    assert c["positive"] == 2


def test_personal_numbers_are_masked(analysis):
    assert not analysis.df["content"].str.contains("3171234567890001").any()
    assert analysis.df["content"].str.contains(r"\[angka\]").any()


def test_star_agreement_between_0_and_1(analysis):
    assert 0 <= analysis.star_agreement() <= 1


def test_table_filter_and_csv(analysis):
    assert set(analysis.table("negative")["nada"]) == {"Negatif"}
    csv = analysis.to_csv().decode("utf-8-sig")
    assert csv.splitlines()[0] == "tanggal,bintang,nada,keyakinan,disukai,dibalas,ulasan"
    assert "Tidak terbaca" in csv


def test_trend_daily(analysis):
    assert analysis.trend()["jumlah"].sum() == 5


def test_top_words_skip_short_and_digits(analysis):
    words = analysis.top_words("negative")
    assert len(words) > 0
    assert all(len(w) >= 3 and not w.isdigit() for w in words["kata"])
