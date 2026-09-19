"""Data tambahan untuk web: pita ulasan, tren keluhan per kuartal, dan contoh CSV untuk cek massal.

- Pita ulasan: ulasan pendek dari split test, disaring (tanpa angka, tautan, email, kata kasar,
  tuduhan politik, penanda lokasi, sapaan diikuti nama, karakter rusak), lalu disamarkan lagi
  dengan mask_personal. Hasil akhirnya tetap dibaca manual sebelum dipajang.
- Tren per kuartal: dihitung dari file mentah (semua ulasan, termasuk yang teksnya kembar, karena
  tiap ulasan tetap satu suara). Label dari bintang, bukan tebakan model.
- Contoh CSV: 200 ulasan test acak dengan kolom app, ulasan, bintang.

Output: web/data/extras.json, web/public/contoh/ulasan-contoh.csv
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import mask_personal  # noqa: E402

SEED = 11
MIN_ROWS = 100  # kuartal dengan ulasan lebih sedikit dari ini tidak ditampilkan sebagai persentase
KASAR = re.compile(
    r"\b(?:anjing|anjir|anjay|bangsat|goblok|goblog|tolol|babi|kontol|memek|bego|bodoh|dungu|geblek|brengsek"
    r"|kampret|tai|taik|asu|jancok|jancuk|kafir|pki)\b",
    re.I,
)
# pita ulasan dipajang di halaman depan: hindari tuduhan politik dan penanda lokasi atau identitas
SENSITIF = re.compile(
    r"\b(?:jokowi|prabowo|presiden|menteri|dpr|rezim|korup\w*|memperkaya|modus|pemilu|partai"
    r"|desa|kelurahan|kecamatan|kabupaten|kab|rt|rw|nik|ktp)\b",
    re.I,
)
SAPAAN_NAMA = re.compile(r"\b(?:pak|bu|bapak|ibu|mas|mbak|kak|bang|om|min)\s+[A-Z][a-z]+")
RUSAK = re.compile("[\u25a0\ufffd]")


def clean_mask(t: pd.Series) -> pd.Series:
    rapat = t.str.replace(r"(.)\1+", r"\1", regex=True)  # huruf berulang dirapatkan, "tololl" tetap tersaring
    return (
        ~t.str.contains(KASAR)
        & ~rapat.str.contains(KASAR)
        & ~t.str.contains(SENSITIF)
        & ~t.str.contains(SAPAAN_NAMA)
        & ~t.str.contains(RUSAK)
    )


def ticker(prep: pd.DataFrame) -> list[dict]:
    te = prep[(prep["split"] == "test") & (prep["agree"] == 1)].copy()
    t = te["text"].astype(str)
    ok = (
        t.str.len().between(28, 105)
        & ~t.str.contains(r"\d|@|http|www\.|\n", regex=True)
        & clean_mask(t)
        & (t.str.count(r"[A-Za-z]") > 20)
    )
    te = te[ok]
    rng = np.random.default_rng(SEED)
    picked = []
    for label, k in [("negative", 14), ("neutral", 6), ("positive", 10)]:
        pool = te[te["label"] == label]
        # sebar ke semua aplikasi: ambil bergiliran per aplikasi
        per_app = {app: g.sample(frac=1, random_state=int(rng.integers(1e9))) for app, g in pool.groupby("app")}
        taken = 0
        i = 0
        while taken < k and any(len(g) > i for g in per_app.values()):
            for app, g in per_app.items():
                if len(g) > i and taken < k:
                    picked.append({"text": mask_personal(" ".join(g.iloc[i]["text"].split())), "label": label, "app": app, "stars": int(round(g.iloc[i]["score_mean"]))})
                    taken += 1
            i += 1
    order = rng.permutation(len(picked))
    return [picked[i] for i in order]


def trend() -> dict:
    raw = pd.read_csv(ROOT / "dataset" / "Rating_labeled.csv", usecols=["app", "score", "at"])
    raw["period"] = pd.to_datetime(raw["at"], errors="coerce").dt.to_period("Q")
    raw = raw.dropna(subset=["period"])
    raw["label"] = np.select([raw["score"] <= 2, raw["score"] == 3], ["negative", "neutral"], "positive")
    out = {}
    for app, g in raw.groupby("app"):
        rows = []
        for period, gp in g.groupby("period"):
            counts = gp["label"].value_counts()
            rows.append(
                {
                    "period": f"{period.year}-K{period.quarter}",
                    "n": int(len(gp)),
                    "negative": int(counts.get("negative", 0)),
                    "neutral": int(counts.get("neutral", 0)),
                    "positive": int(counts.get("positive", 0)),
                }
            )
        out[app] = rows
    return {"min_rows_per_period": MIN_ROWS, "apps": out, "total_rows": int(len(raw))}


def sample_csv(prep: pd.DataFrame) -> None:
    te = prep[prep["split"] == "test"]
    t = te["text"].astype(str)
    te = te[t.str.len().between(15, 400) & clean_mask(t)]
    s = te.sample(n=200, random_state=SEED)
    out = pd.DataFrame(
        {
            "app": s["app"].values,
            "ulasan": [mask_personal(" ".join(x.split())) for x in s["text"]],
            "bintang": s["score_mean"].round().astype(int).values,
        }
    )
    dest = ROOT / "web" / "public" / "contoh"
    dest.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest / "ulasan-contoh.csv", index=False, encoding="utf-8", lineterminator="\n")


def main() -> None:
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet")
    extras = {"ticker": ticker(prep), "trend": trend()}
    (ROOT / "web" / "data" / "extras.json").write_text(json.dumps(extras, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sample_csv(prep)
    print("ticker", len(extras["ticker"]), "| kuartal per app", {a: len(r) for a, r in extras["trend"]["apps"].items()})


if __name__ == "__main__":
    main()
