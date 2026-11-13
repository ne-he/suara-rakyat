"""Ringkasan hasil baca ulasan untuk dashboard: komposisi nada, tren, kata penentu, unduhan CSV."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from suara.classifier import LABELS, Prediction
from suara_ml.textnorm import mask_personal

LABEL_ID = {"negative": "Negatif", "neutral": "Netral", "positive": "Positif"}
# kata umum yang ikut mendorong nada tapi tidak menunjukkan topik keluhan atau pujian
GENERIC = {"tidak", "aplikasi", "aplikasinya", "sangat", "yang", "dan", "ini", "itu", "saya", "nya", "aja", "juga", "untuk", "dengan", "sudah", "lagi", "jadi", "kok", "sih"}


def star_label(score: int) -> str:
    """Aturan label yang sama dengan dataset IGAR: 1-2 negatif, 3 netral, 4-5 positif."""
    return "negative" if score <= 2 else "neutral" if score == 3 else "positive"


class ReviewAnalysis:
    def __init__(self, reviews: pd.DataFrame, preds: list[Prediction]) -> None:
        df = reviews.copy()
        df["label"] = [p.label for p in preds]
        df["confidence"] = [p.confidence for p in preds]
        # teks ditampilkan setelah deret angka panjang dan email disamarkan
        df["content"] = df["content"].map(mask_personal)
        self.df = df
        self._preds = preds

    @property
    def readable(self) -> pd.DataFrame:
        return self.df[self.df["label"].notna()]

    def counts(self) -> dict[str, int]:
        vc = self.readable["label"].value_counts()
        return {lab: int(vc.get(lab, 0)) for lab in LABELS}

    def unreadable(self) -> int:
        return int(self.df["label"].isna().sum())

    def star_agreement(self) -> float | None:
        r = self.readable
        if r.empty:
            return None
        return float((r["score"].map(star_label) == r["label"]).mean())

    def is_weekly(self) -> bool:
        """Tren dihitung per minggu kalau rentang ulasannya lebih dari 62 hari, supaya batangnya tetap terbaca."""
        r = self.readable
        return not r.empty and (r["at"].max() - r["at"].min()).days > 62

    def trend(self) -> pd.DataFrame:
        """Jumlah ulasan per nada per hari atau per minggu (lihat is_weekly)."""
        r = self.readable
        if r.empty:
            return pd.DataFrame(columns=["periode", "nada", "jumlah"])
        freq = "W-SUN" if self.is_weekly() else "D"
        periode = r["at"].dt.tz_localize(None).dt.to_period(freq).dt.start_time
        t = r.assign(periode=periode).groupby(["periode", "label"]).size().rename("jumlah").reset_index()
        t["nada"] = t["label"].map(LABEL_ID)
        return t[["periode", "nada", "jumlah"]]

    def top_words(self, label: str, n: int = 10) -> pd.DataFrame:
        """Kata yang paling mendorong ulasan ke nada ini, beserta berapa ulasan yang memuatnya."""
        score: dict[str, float] = defaultdict(float)
        docs: dict[str, int] = defaultdict(int)
        n_label = 0
        for p in self._preds:
            if p.label != label:
                continue
            n_label += 1
            seen = set()
            for tok, w in p.tokens:
                if w <= 0 or len(tok) < 3 or tok.isdigit() or tok in GENERIC:
                    continue
                score[tok] += w
                if tok not in seen:
                    docs[tok] += 1
                    seen.add(tok)
        rows = [(t, s, docs[t]) for t, s in score.items() if docs[t] >= 2 or n_label < 20]
        rows.sort(key=lambda x: -x[1])
        return pd.DataFrame(rows[:n], columns=["kata", "skor", "ulasan"])

    def table(self, label: str | None = None) -> pd.DataFrame:
        df = self.df if label is None else self.df[self.df["label"] == label]
        return pd.DataFrame(
            {
                "tanggal": df["at"].dt.strftime("%Y-%m-%d %H:%M"),
                "bintang": df["score"],
                "nada": df["label"].map(LABEL_ID).fillna("Tidak terbaca"),
                "keyakinan": df["confidence"].round(3),
                "disukai": df["thumbs_up"],
                "dibalas": df["replied"].map({True: "sudah", False: "belum"}),
                "ulasan": df["content"],
            }
        )

    def to_csv(self) -> bytes:
        # utf-8-sig supaya langsung terbaca benar saat dibuka di Excel
        return self.table().to_csv(index=False).encode("utf-8-sig")
