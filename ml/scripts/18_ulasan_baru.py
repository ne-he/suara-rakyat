"""Evaluasi di ulasan baru (out-of-time): model dilatih dari ulasan 2012 sampai 2023, diuji di ulasan 30 hari terakhir.

Ulasan diambil dari Google Play dengan ReviewScraper milik app v5 (maksimal 10.000 per aplikasi),
dibaca SentimentClassifier v5, lalu dibandingkan dengan label dari bintang memakai aturan IGAR
(1-2 negatif, 3 netral, 4-5 positif). Yang disimpan hanya angka ringkasan, bukan teks ulasan.

Output: ml/reports/ulasan_baru.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "streamlit-app"))
from suara.analysis import star_label  # noqa: E402
from suara.apps import APPS  # noqa: E402
from suara.classifier import LABELS, SentimentClassifier  # noqa: E402
from suara.scraper import WIB, ReviewScraper  # noqa: E402

HARI = 30


def test_igar() -> dict:
    meta = json.loads((ROOT / "web" / "model" / "meta.json").read_text(encoding="utf-8"))
    t = next(m for m in meta["models"] if m["id"] == meta["default_model"])["metrics"]["test"]
    return {"accuracy": round(t["accuracy"], 4), "macro_f1": round(t["macro_f1"], 4)}


def main() -> None:
    clf = SentimentClassifier()
    akhir = datetime.now(WIB).date()
    awal = akhir - timedelta(days=HARI - 1)
    hasil, semua_y, semua_p = {}, [], []
    for nama, app_id in APPS.items():
        r = ReviewScraper().fetch(app_id, awal, akhir)
        preds = clf.predict_many(r.reviews["content"].tolist())
        y, p = [], []
        for skor, pr in zip(r.reviews["score"], preds):
            if pr.label is None:
                continue
            y.append(star_label(int(skor)))
            p.append(pr.label)
        semua_y += y
        semua_p += p
        hasil[app_id] = {
            "aplikasi": nama,
            "ulasan": len(r.reviews),
            "terbaca": len(y),
            "kena_batas": r.hit_limit,
            "ulasan_tertua": r.oldest_seen.isoformat() if r.oldest_seen else None,
            "accuracy": round(accuracy_score(y, p), 4) if y else None,
            "macro_f1": round(f1_score(y, p, labels=list(LABELS), average="macro", zero_division=0), 4) if y else None,
            "porsi_bintang": {lab: round(float(np.mean([v == lab for v in y])), 4) for lab in LABELS} if y else None,
            "porsi_model": {lab: round(float(np.mean([v == lab for v in p])), 4) for lab in LABELS} if y else None,
        }
        print(nama, hasil[app_id]["ulasan"], "ulasan, acc", hasil[app_id]["accuracy"], "macro-F1", hasil[app_id]["macro_f1"])
    total = {
        "terbaca": len(semua_y),
        "accuracy": round(accuracy_score(semua_y, semua_p), 4),
        "macro_f1": round(f1_score(semua_y, semua_p, labels=list(LABELS), average="macro", zero_division=0), 4),
        "f1_per_kelas": dict(zip(LABELS, [round(x, 4) for x in f1_score(semua_y, semua_p, labels=list(LABELS), average=None, zero_division=0)])),
    }
    out = {
        "diambil": datetime.now(WIB).isoformat(timespec="seconds"),
        "rentang": [awal.isoformat(), akhir.isoformat()],
        "catatan": "label pembanding dari bintang (aturan IGAR), batas 10.000 ulasan terbaru per aplikasi",
        "pembanding_test_set_igar": test_igar(),
        "gabungan": total,
        "per_aplikasi": hasil,
    }
    tujuan = ROOT / "ml" / "reports" / "ulasan_baru.json"
    tujuan.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("gabungan", total, "->", tujuan)


if __name__ == "__main__":
    main()
