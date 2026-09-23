"""Pembanding dari luar: angka resmi paper IGAR, replikasinya, dan pelabelan VADER.

Tiga hal yang dihitung di sini:

1. Kesepakatan label bintang dengan label VADER di seluruh 617.722 ulasan. Dipakai untuk
   mengecek apakah angka yang dilaporkan paper IGAR (kappa 0,33 dan kecocokan 58,65 persen)
   bisa kami hasilkan ulang dari file yang sama.
2. VADER sebagai model pembanding di split test kami, supaya sebaris dengan model lain.
3. Replikasi baseline paper (TF-IDF 5000 fitur + LinearSVC bawaan) dalam dua setelan:
   - "acak": baris mentah, duplikat dibiarkan, acak 80/20 per aplikasi. Ini tebakan kami atas
     setelan paper, karena paper tidak menyebut cara memisah data.
   - "kunci teks": split milik kami, teks kembar digabung dan tidak pernah pindah split.
   Selisih dua setelan itu yang menjelaskan kenapa angka paper jauh lebih tinggi.

Angka paper ditulis ulang dari Tabel 9 (kolom LinearSVC, teks Indonesia) di
Isnan dan Pardamean (2026), Data in Brief 66, 112708, doi:10.1016/j.dib.2026.112708.

Output: ml/reports/pembanding_luar.json dan web/data/pembanding.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, precision_score, recall_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import tokens  # noqa: E402

LABELS = ["negative", "neutral", "positive"]
SEED = 42
# Tabel 9 paper IGAR, baris teks Indonesia, kolom LinearSVC (accuracy, precision, recall, F1)
PAPER = {
    "satusehat": [0.87, 0.87, 0.87, 0.87],
    "BMKG": [0.88, 0.88, 0.88, 0.87],
    "KAI": [0.81, 0.81, 0.81, 0.81],
    "pertamina": [0.88, 0.88, 0.88, 0.88],  # paper menyebutnya MyPertamina
    "mobileJKN": [0.89, 0.89, 0.89, 0.89],
    "JMO": [0.92, 0.92, 0.92, 0.92],
}


def skor(y_true, y_pred) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_weighted": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "recall_weighted": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
    }


def latih_uji(train_text, train_y, test_text, test_y) -> dict:
    """Setelan baseline paper: TF-IDF maksimal 5000 fitur, LinearSVC bawaan."""
    vec = TfidfVectorizer(max_features=5000)
    xtr = vec.fit_transform(train_text)
    t0 = time.perf_counter()
    clf = LinearSVC().fit(xtr, train_y)
    detik = time.perf_counter() - t0
    out = skor(test_y, clf.predict(vec.transform(test_text)))
    out.update({"n_train": int(len(train_y)), "n_test": int(len(test_y)), "fit_seconds": round(detik, 1)})
    return out


def main() -> None:
    kolom = ["app", "content", "score", "labelScoreBase"]
    raw = pd.read_csv(ROOT / "dataset" / "Rating_labeled.csv", usecols=kolom)
    vader = pd.read_csv(ROOT / "dataset" / "VADER_labeled.csv", usecols=["app", "score", "vader_label"])
    assert len(raw) == len(vader) and (raw["app"] == vader["app"]).all() and (raw["score"] == vader["score"]).all(), "urutan dua file tidak sama"

    raw["label"] = raw["labelScoreBase"].astype(str).str.strip().str.lower()
    raw["vader"] = vader["vader_label"].astype(str).str.strip().str.lower()
    raw["content"] = raw["content"].fillna("").astype(str)
    pakai = raw["label"].isin(LABELS) & raw["vader"].isin(LABELS)

    v = raw[pakai]
    kesepakatan = {
        "n": int(len(v)),
        "kappa": round(float(cohen_kappa_score(v["label"], v["vader"])), 4),
        "kecocokan": round(float((v["label"] == v["vader"]).mean()), 4),
        "paper_kappa": 0.33,
        "paper_kecocokan": 0.5865,
        "silang": pd.crosstab(v["label"], v["vader"]).reindex(index=LABELS, columns=LABELS, fill_value=0).values.tolist(),
    }

    # VADER di split test kami: satu label per teks unik, diambil dari label terbanyak barisnya
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "label", "app", "split"])
    te = prep[prep["split"] == "test"]
    v = v.copy()
    v["key"] = [" ".join(tokens(t, use_slang=False)) for t in v["content"]]
    per_kunci = v.groupby(["key", "vader"]).size().unstack(fill_value=0).reindex(columns=LABELS, fill_value=0)
    per_kunci = per_kunci.loc[per_kunci.index.intersection(te["key"])]
    vader_label = pd.Series([LABELS[i] for i in per_kunci.values.argmax(1)], index=per_kunci.index)
    t = te.set_index("key").loc[vader_label.index]
    vader_test = skor(t["label"], vader_label.values)
    vader_test["n_test"] = int(len(t))

    # replikasi baseline paper per aplikasi
    prep_full = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "text", "label", "app", "split"])
    rng = np.random.default_rng(SEED)
    per_app = []
    for app in PAPER:
        g = raw[(raw["app"] == app) & raw["label"].isin(LABELS)]
        acak = rng.permutation(len(g))
        batas = int(len(g) * 0.8)
        tr, ts = g.iloc[acak[:batas]], g.iloc[acak[batas:]]
        hasil_acak = latih_uji(tr["content"], tr["label"], ts["content"], ts["label"])

        h = prep_full[prep_full["app"] == app]
        htr, hts = h[h["split"] == "train"], h[h["split"] == "test"]
        hasil_kunci = latih_uji(htr["text"], htr["label"], hts["text"], hts["label"])

        per_app.append({"app": app, "paper_linearsvc": dict(zip(["accuracy", "precision", "recall", "f1"], PAPER[app])), "acak": hasil_acak, "kunci_teks": hasil_kunci})
        print(app, "acak f1w", hasil_acak["f1_weighted"], "| kunci f1w", hasil_kunci["f1_weighted"], "| macro", hasil_kunci["f1_macro"], flush=True)

    # semua aplikasi sekaligus, setelan yang sama
    g = raw[raw["label"].isin(LABELS)]
    acak = rng.permutation(len(g))
    batas = int(len(g) * 0.8)
    semua_acak = latih_uji(g["content"].iloc[acak[:batas]], g["label"].iloc[acak[:batas]], g["content"].iloc[acak[batas:]], g["label"].iloc[acak[batas:]])
    tr, ts = prep_full[prep_full["split"] == "train"], prep_full[prep_full["split"] == "test"]
    semua_kunci = latih_uji(tr["text"], tr["label"], ts["text"], ts["label"])

    out = {
        "sumber_paper": {
            "sitasi": "Isnan, M. dan Pardamean, B. (2026). IGAR: Indonesian government applications review for sentiment analysis dataset. Data in Brief, 66, 112708.",
            "doi": "10.1016/j.dib.2026.112708",
            "setelan": "TF-IDF maksimal 5000 fitur, Random Forest dan LinearSVC bawaan, tanpa penyetelan. Cara memisah data dan cara merata-rata skor tidak disebut di paper.",
        },
        "kesepakatan_bintang_vader": kesepakatan,
        "vader_di_test_kami": vader_test,
        "per_app": per_app,
        "semua_app": {"acak": semua_acak, "kunci_teks": semua_kunci},
    }
    (ROOT / "ml" / "reports" / "pembanding_luar.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "web" / "data" / "pembanding.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"kesepakatan": {k: kesepakatan[k] for k in ["kappa", "kecocokan", "paper_kappa", "paper_kecocokan"]}, "vader_test": vader_test, "semua": out["semua_app"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
