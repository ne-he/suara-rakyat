"""Uji tahan bahasa: 60 kalimat buatan tim, bukan dari dataset.

Kalimat disusun tim untuk menguji hal yang jarang terlihat di skor rata-rata: salah ketik,
bahasa gaul, kalimat bernegasi, sindiran, kalimat campur pujian dan keluhan, kalimat netral,
ulasan sangat pendek, dan emoji. Label acuan ditetapkan tim, jadi ini uji buatan sendiri,
bukan tolok ukur resmi. Kategori campuran dan netral paling bisa diperdebatkan dan memang
sengaja dipakai untuk melihat perilaku model, bukan untuk menghakiminya.

Model yang diuji sama persis dengan yang dipakai produk: 3 model web lewat kode TypeScript,
dan IndoBERTweet int8 lewat fungsi di indobert-api/app.py kalau modelnya ada di laptop.

Input: ml/eval/uji_tahan.csv
Output: ml/reports/uji_tahan.json dan web/data/uji.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml import prediksi  # noqa: E402

NAMA = {"svm": "Linear SVM", "logreg": "Logistic Regression", "nb": "Naive Bayes", "indobert": "IndoBERTweet int8"}
URUT = ["typo", "slang", "negasi", "sarkasme", "campuran", "netral", "pendek", "emoji"]


def main() -> None:
    df = pd.read_csv(ROOT / "ml" / "eval" / "uji_tahan.csv")
    teks = df["teks"].astype(str).tolist()

    jawab = prediksi.web_models(teks)
    if prediksi.indobert_available():
        jawab["indobert"] = prediksi.indobert(teks)
    else:
        print("model IndoBERT tidak ada di laptop ini, bagian itu dilewati")

    model_ids = [m for m in ["svm", "logreg", "nb", "indobert"] if m in jawab]
    for m in model_ids:
        df[m] = jawab[m]

    per_kategori = []
    for kat in [k for k in URUT if k in set(df["kategori"])]:
        g = df[df["kategori"] == kat]
        per_kategori.append({"kategori": kat, "n": int(len(g)), **{m: round(float((g[m] == g["label"]).mean()), 4) for m in model_ids}})

    out = {
        "catatan": "kalimat dan label disusun tim, bukan dari dataset. Kategori campuran dan netral paling bisa diperdebatkan.",
        "n": int(len(df)),
        "model": [{"id": m, "nama": NAMA[m]} for m in model_ids],
        "akurasi": {m: round(float((df[m] == df["label"]).mean()), 4) for m in model_ids},
        "per_kategori": per_kategori,
        "butir": [
            {
                "kategori": r["kategori"],
                "teks": r["teks"],
                "label": r["label"],
                "alasan": r["alasan"],
                "jawab": {m: r[m] for m in model_ids},
            }
            for _, r in df.iterrows()
        ],
    }
    (ROOT / "ml" / "reports" / "uji_tahan.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "web" / "data" / "uji.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"akurasi": out["akurasi"], "per_kategori": per_kategori}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
