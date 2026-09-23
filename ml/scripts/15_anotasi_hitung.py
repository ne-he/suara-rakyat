"""Hitung hasil anotasi manusia: kesepakatan antar pembaca, dan siapa yang lebih dekat ke pembaca.

Dibaca dari ml/anotasi/hasil/*.xlsx (atau .csv) yang berisi kolom no dan label. Skrip ini
menghitung kappa Fleiss antar anggota tim, kappa Cohen tiap pasangan, label mayoritas manusia,
lalu membandingkan label bintang dan tiap model terhadap label mayoritas itu.

Kalau folder hasil masih kosong, skrip berhenti dengan pesan, tidak menulis apa pun.

Output: ml/reports/anotasi.json dan web/data/anotasi.json
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

ROOT = Path(__file__).resolve().parents[2]
HASIL = ROOT / "ml" / "anotasi" / "hasil"
KUNCI = ROOT / "ml" / "anotasi" / "kunci" / "kunci.csv"
LABELS = ["negative", "neutral", "positive"]
KE_INGGRIS = {"negatif": "negative", "netral": "neutral", "positif": "positive", "tidak jelas": "unclear"}
KELAS = LABELS + ["unclear"]
MODEL = {"svm": "Linear SVM", "logreg": "Logistic Regression", "nb": "Naive Bayes", "indobert": "IndoBERTweet int8"}


def baca(f: Path) -> pd.Series:
    df = pd.read_excel(f) if f.suffix == ".xlsx" else pd.read_csv(f)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "no" not in df or "label" not in df:
        raise SystemExit(f"{f.name}: butuh kolom no dan label")
    s = df.set_index("no")["label"].astype(str).str.strip().str.lower().map(KE_INGGRIS)
    return s.dropna()


def fleiss(tabel: np.ndarray) -> float:
    """Kappa Fleiss dari tabel jumlah suara per butir per kelas (baris = butir)."""
    n = tabel.sum(axis=1)
    if len(set(n.tolist())) != 1:
        raise ValueError("tiap butir harus dinilai jumlah anotator yang sama")
    n = int(n[0])
    p_butir = (np.square(tabel).sum(axis=1) - n) / (n * (n - 1))
    p_kelas = tabel.sum(axis=0) / (len(tabel) * n)
    p_bar, p_e = p_butir.mean(), float(np.square(p_kelas).sum())
    return float((p_bar - p_e) / (1 - p_e)) if p_e < 1 else 1.0


def skor(y_true, y_pred) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", labels=LABELS, zero_division=0)), 4),
    }


def main() -> None:
    berkas = sorted([f for f in HASIL.glob("*") if f.suffix in {".xlsx", ".csv"} and not f.name.startswith("~$")]) if HASIL.exists() else []
    if len(berkas) < 2:
        raise SystemExit(f"belum ada cukup hasil di {HASIL} (butuh minimal 2 berkas). Isi lembar di ml/anotasi/lembar dulu.")

    kunci = pd.read_csv(KUNCI).set_index("no")
    jawab = {f.stem: baca(f) for f in berkas}
    per_anotator = {nama: {"terisi": int(s.size), "sebaran": s.value_counts().to_dict()} for nama, s in jawab.items()}

    tabel = pd.DataFrame(jawab)
    penuh = tabel.dropna()
    if penuh.empty:
        raise SystemExit("tidak ada butir yang diisi semua anotator")

    hitung = np.zeros((len(penuh), len(KELAS)), dtype=int)
    for j, kelas in enumerate(KELAS):
        hitung[:, j] = (penuh == kelas).sum(axis=1).values

    pasangan = [
        {"pasangan": f"{a} vs {b}", "kappa": round(float(cohen_kappa_score(penuh[a], penuh[b])), 4)}
        for a, b in combinations(penuh.columns, 2)
    ]

    suara = pd.DataFrame(hitung, index=penuh.index, columns=KELAS)
    tertinggi = suara.max(axis=1)
    seri = (suara.eq(tertinggi, axis=0).sum(axis=1) > 1)
    mayoritas = pd.Series([KELAS[i] for i in suara.values.argmax(1)], index=penuh.index).where(~seri, "seri")
    jelas = mayoritas.isin(LABELS)
    idx = mayoritas[jelas].index
    manusia = mayoritas[jelas]
    bintang = kunci.loc[idx, "label_bintang"]

    banding = {
        "bintang": {
            **skor(manusia, bintang),
            "kappa": round(float(cohen_kappa_score(manusia, bintang)), 4),
            "silang": pd.crosstab(manusia, bintang).reindex(index=LABELS, columns=LABELS, fill_value=0).values.tolist(),
        }
    }
    for m in [m for m in MODEL if m in kunci.columns]:
        banding[m] = {"nama": MODEL[m], "lawan_manusia": skor(manusia, kunci.loc[idx, m]), "lawan_bintang": skor(bintang, kunci.loc[idx, m])}

    out = {
        "catatan": "label mayoritas dari pembaca manusia, bintang tidak diperlihatkan saat menilai. Contoh diambil seimbang 100 per kelas bintang, jadi skor di sini tidak sebanding dengan skor di seluruh data test.",
        "anotator": len(berkas),
        "butir_disiapkan": int(len(kunci)),
        "butir_dinilai_semua": int(len(penuh)),
        "butir_dipakai": int(len(idx)),
        "butir_seri": int((mayoritas == "seri").sum()),
        "butir_tidak_jelas": int((mayoritas == "unclear").sum()),
        "per_anotator": per_anotator,
        "kappa_fleiss": round(fleiss(hitung), 4),
        "kappa_pasangan": pasangan,
        "kesepakatan_penuh": round(float((suara.max(axis=1) == len(penuh.columns)).mean()), 4),
        "sebaran_manusia": manusia.value_counts().to_dict(),
        "sebaran_bintang": bintang.value_counts().to_dict(),
        "banding": banding,
    }
    (ROOT / "ml" / "reports" / "anotasi.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "web" / "data" / "anotasi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
