"""Contoh nyata label yang bertabrakan, untuk dipajang di dashboard.

Label di dataset ini berasal dari bintang, bukan dari pembaca teksnya. Teks yang sama persis
bisa dapat bintang 1 dan bintang 5 dari orang berbeda. Skrip ini mengambil teks yang sering
muncul lalu menghitung sebaran labelnya, supaya batas atas skor model terlihat dari data,
bukan cuma dari kalimat.

Penyaringan: teks pendek, tanpa angka panjang, email, kata kasar, tuduhan politik, penanda
lokasi, atau sapaan diikuti nama. Sisanya tetap dibaca manual sebelum dipajang.

Output: ml/reports/label_kotor.json dan web/data/label.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import mask_personal, tokens  # noqa: E402

sys.path.insert(0, str(ROOT / "ml" / "scripts"))
from importlib import import_module  # noqa: E402

extras = import_module("09_web_extras")

LABELS = ["negative", "neutral", "positive"]
MIN_N = 40  # teks harus muncul minimal sekian kali supaya sebarannya berarti
MIN_MINORITAS = 0.08  # minimal sekian porsi label di luar mayoritas
JUMLAH = 12


def main() -> None:
    raw = pd.read_csv(ROOT / "dataset" / "Rating_labeled.csv", usecols=["content", "score", "labelScoreBase"])
    raw["label"] = raw["labelScoreBase"].astype(str).str.strip().str.lower()
    raw = raw[raw["label"].isin(LABELS)]
    raw["content"] = raw["content"].fillna("").astype(str)
    raw["key"] = [" ".join(tokens(t, use_slang=False)) for t in raw["content"]]
    raw = raw[raw["key"] != ""]

    counts = raw.groupby(["key", "label"]).size().unstack(fill_value=0)
    for lab in LABELS:
        if lab not in counts:
            counts[lab] = 0
    counts = counts[LABELS]
    n = counts.sum(axis=1)
    minoritas = 1 - counts.max(axis=1) / n
    layak = counts[(n >= MIN_N) & (minoritas >= MIN_MINORITAS)].copy()

    teks = raw.drop_duplicates("key").set_index("key")["content"]
    bintang = raw.groupby("key")["score"].mean()
    t = teks.reindex(layak.index).astype(str)
    bersih = extras.clean_mask(t) & ~t.str.contains(r"\d{6,}|@|http", regex=True) & t.str.len().between(4, 70)
    layak = layak[bersih.values]

    layak["n"] = layak.sum(axis=1)
    layak["minoritas"] = 1 - layak[LABELS].max(axis=1) / layak["n"]
    layak = layak.sort_values(["minoritas", "n"], ascending=False).head(JUMLAH)

    contoh = [
        {
            "teks": mask_personal(" ".join(str(teks[k]).split()))[:70],
            "n": int(row["n"]),
            "negative": int(row["negative"]),
            "neutral": int(row["neutral"]),
            "positive": int(row["positive"]),
            "bintang_rata": round(float(bintang[k]), 2),
        }
        for k, row in layak.iterrows()
    ]

    semua_n = n[n >= 2]
    out = {
        "min_kemunculan": MIN_N,
        "teks_unik": int(len(counts)),
        "teks_muncul_ulang": int(len(semua_n)),
        "teks_label_bertabrakan": int((counts.gt(0).sum(axis=1) > 1).sum()),
        "baris_di_teks_bertabrakan": int(counts[counts.gt(0).sum(axis=1) > 1].values.sum()),
        "contoh": contoh,
    }
    (ROOT / "ml" / "reports" / "label_kotor.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "web" / "data" / "label.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
