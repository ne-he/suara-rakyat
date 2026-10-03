"""Evaluasi sentimen dengan cosine similarity, dari empat sudut.

Semua vektor teks memakai fitur TF-IDF kata 1-2 gram yang sudah dinormalisasi L2 (data/feats/word_*),
jadi cosine similarity dua ulasan sama dengan hasil kali titik vektornya.

A. Kemiripan antar kelas. Rata-rata cosine antara semua pasangan ulasan dari dua kelas sama persis
   dengan hasil kali titik vektor rata-rata kedua kelas, jadi bisa dihitung tepat untuk 289 ribu
   ulasan latih tanpa sampel. Dipakai untuk menjelaskan kenapa kelas netral paling sulit.
B. Tetangga terdekat. Untuk sampel ulasan uji, cari ulasan latih yang paling mirip. Hasilnya dipakai
   tiga kali: cek kebocoran (seberapa mirip data uji dengan data latih), pembanding sederhana
   (label tetangga terdekat sebagai tebakan, cara kerja kNN), dan ketepatan model web per tingkat
   kemiripan.
C. Profil sentimen per aplikasi. Vektor porsi negatif, netral, positif dari bintang dibandingkan
   dengan vektor porsi dari tebakan model, per aplikasi dan per aplikasi per kuartal. Ini mengukur
   seberapa bisa dipercaya ringkasan nada pada fitur cek massal.
D. Kesepakatan antar model. Cosine antara vektor peluang tiap pasangan model di seluruh data uji.

Output: ml/reports/cosine.json, ml/reports/cosine_kelas.png, ml/reports/cosine_aplikasi.png
"""

from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[2]
FEATS = ROOT / "data" / "feats"
SCORES = ROOT / "data" / "scores"
REPORTS = ROOT / "ml" / "reports"
LABELS = ["negative", "neutral", "positive"]
LABEL_ID = {"negative": "negatif", "neutral": "netral", "positive": "positif"}
NAMA_APP = {"JMO": "JMO", "satusehat": "SatuSehat", "mobileJKN": "Mobile JKN", "pertamina": "MyPertamina", "KAI": "KAI Access", "BMKG": "Info BMKG"}
SEED = 42
N_SAMPEL = 5000
K = 10
MIN_KUARTAL = 100


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def peluang_model(prep_test: pd.DataFrame) -> dict[str, dict]:
    """Peluang tiap model di data uji, urutan baris sama dengan data/feats (kunci teks terurut)."""
    meta = json.loads((ROOT / "web" / "model" / "meta.json").read_text(encoding="utf-8"))
    pilih = json.loads((REPORTS / "final_selection.json").read_text(encoding="utf-8"))
    cand = {c["name"]: c for c in pilih["candidates"]}
    out = {}
    for m in meta["models"]:
        s = np.load(SCORES / f"{m['run']}_test.npy").astype(np.float64)
        out[m["id"]] = {"nama": m["name"], "p": softmax((s + np.array(m["bias"])) / m["temperature"])}
    run = "indobertweet_int8"
    if (SCORES / f"{run}_test.npy").exists():
        logits = np.load(SCORES / f"{run}_test.npy").astype(np.float64)
        keys = pd.read_parquet(SCORES / f"{run}_test_keys.parquet")["key"]
        pos = pd.Series(range(len(keys)), index=keys.values)
        logits = logits[pos.loc[prep_test["key"].values].values]
        c = cand[run]
        out["indobert"] = {"nama": "IndoBERTweet int8", "p": softmax((logits + np.array(c["bias"])) / c["temperature"])}
    return out


def bagian_a(X_tr: sp.csr_matrix, y_tr: np.ndarray) -> dict:
    rata = np.vstack([np.asarray(X_tr[y_tr == k].mean(axis=0)).ravel() for k in range(3)])
    pasangan = rata @ rata.T  # rata-rata cosine semua pasangan ulasan antar kelas (tepat)
    pusat = rata / np.linalg.norm(rata, axis=1, keepdims=True)
    return {
        "jumlah_latih": {LABELS[k]: int((y_tr == k).sum()) for k in range(3)},
        "rata_cosine_pasangan": {LABELS[i]: {LABELS[j]: round(float(pasangan[i, j]), 4) for j in range(3)} for i in range(3)},
        "cosine_pusat_kelas": {LABELS[i]: {LABELS[j]: round(float(pusat[i] @ pusat[j]), 4) for j in range(3)} for i in range(3)},
    }


def bagian_b(X_tr, y_tr, X_te, y_te, pred_svm) -> dict:
    rng = np.random.default_rng(SEED)
    idx = np.sort(rng.choice(X_te.shape[0], size=N_SAMPEL, replace=False))
    Xs = X_te[idx]
    XtrT = X_tr.T.tocsr()
    maks = np.zeros(N_SAMPEL)
    tebak1 = np.zeros(N_SAMPEL, dtype=int)
    tebakk = np.zeros(N_SAMPEL, dtype=int)
    t0 = time.time()
    for a in range(0, N_SAMPEL, 100):
        sim = (Xs[a : a + 100] @ XtrT).toarray()
        top = np.argpartition(-sim, K, axis=1)[:, :K]
        for r in range(sim.shape[0]):
            t = top[r][np.argsort(-sim[r, top[r]])]
            maks[a + r] = sim[r, t[0]]
            tebak1[a + r] = y_tr[t[0]]
            suara = np.bincount(y_tr[t], weights=sim[r, t], minlength=3)
            tebakk[a + r] = int(suara.argmax())
    detik = time.time() - t0
    y = y_te[idx]
    svm = pred_svm[idx]
    batas = [(0.0, 0.5, "di bawah 0,5"), (0.5, 0.8, "0,5 sampai 0,8"), (0.8, 0.95, "0,8 sampai 0,95"), (0.95, 1.01, "0,95 ke atas")]
    per_tingkat = []
    for lo, hi, nama in batas:
        m = (maks >= lo) & (maks < hi)
        if m.sum() == 0:
            continue
        per_tingkat.append(
            {
                "kemiripan": nama,
                "n": int(m.sum()),
                "porsi": round(float(m.mean()), 4),
                "akurasi_svm": round(float((svm[m] == y[m]).mean()), 4),
                "akurasi_tetangga_1": round(float((tebak1[m] == y[m]).mean()), 4),
            }
        )
    skor = lambda p: {"macro_f1": round(float(f1_score(y, p, average="macro")), 4), "akurasi": round(float(accuracy_score(y, p)), 4)}
    return {
        "sampel_uji": N_SAMPEL,
        "seed": SEED,
        "k": K,
        "detik": round(detik, 1),
        "kemiripan_maksimum": {
            "median": round(float(np.median(maks)), 4),
            "p10": round(float(np.percentile(maks, 10)), 4),
            "p90": round(float(np.percentile(maks, 90)), 4),
            "porsi_di_atas_0_95": round(float((maks >= 0.95).mean()), 4),
            "porsi_sama_persis": round(float((maks >= 0.9999).mean()), 4),
        },
        "per_tingkat": per_tingkat,
        "skor": {"tetangga_1": skor(tebak1), f"tetangga_{K}_berbobot": skor(tebakk), "linear_svm_web": skor(svm)},
    }


def bagian_c(prep_test: pd.DataFrame, y_te: np.ndarray, model: dict) -> dict:
    hasil = {}
    benar = np.eye(3)[y_te]
    kuartal = pd.to_datetime(prep_test["at_min"]).dt.to_period("Q").astype(str).values
    for mid, m in model.items():
        pred = m["p"].argmax(1)
        tebak = np.eye(3)[pred]
        per_app = {}
        for app in NAMA_APP:
            mask = prep_test["app"].values == app
            vb, vt = benar[mask].sum(0), tebak[mask].sum(0)
            per_app[app] = {
                "n": int(mask.sum()),
                "porsi_bintang": [round(float(x), 4) for x in vb / vb.sum()],
                "porsi_model": [round(float(x), 4) for x in vt / vt.sum()],
                "cosine": round(cos(vb, vt), 4),
                "selisih_negatif": round(float(abs(vt[0] - vb[0]) / vb.sum()), 4),
            }
        grup = pd.DataFrame({"app": prep_test["app"].values, "q": kuartal, "y": y_te, "p": pred})
        nilai = []
        for _, g in grup.groupby(["app", "q"]):
            if len(g) < MIN_KUARTAL:
                continue
            nilai.append(cos(np.bincount(g["y"], minlength=3).astype(float), np.bincount(g["p"], minlength=3).astype(float)))
        vb, vt = benar.sum(0), tebak.sum(0)
        hasil[mid] = {
            "nama": m["nama"],
            "semua": {"porsi_bintang": [round(float(x), 4) for x in vb / vb.sum()], "porsi_model": [round(float(x), 4) for x in vt / vt.sum()], "cosine": round(cos(vb, vt), 4)},
            "per_app": per_app,
            "per_app_kuartal": {"jumlah_kelompok": len(nilai), "min_ulasan": MIN_KUARTAL, "rata": round(float(np.mean(nilai)), 4), "terendah": round(float(np.min(nilai)), 4)},
        }
    return hasil


def bagian_d(model: dict) -> dict:
    out = []
    for a, b in combinations(model, 2):
        pa, pb = model[a]["p"], model[b]["p"]
        c = (pa * pb).sum(1) / (np.linalg.norm(pa, axis=1) * np.linalg.norm(pb, axis=1))
        out.append(
            {
                "pasangan": f"{model[a]['nama']} dan {model[b]['nama']}",
                "rata_cosine_peluang": round(float(c.mean()), 4),
                "label_sama": round(float((pa.argmax(1) == pb.argmax(1)).mean()), 4),
            }
        )
    return {"pasangan": out}


def gambar(a: dict, c: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"
    nama = [LABEL_ID[l] for l in LABELS]
    m = np.array([[a["cosine_pusat_kelas"][i][j] for j in LABELS] for i in LABELS])
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    ax.imshow(m, cmap="Greys", vmin=0.3, vmax=1.05)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{m[i, j]:.2f}".replace(".", ","), ha="center", va="center", fontsize=12, color="white" if m[i, j] > 0.8 else "black")
    ax.set_xticks(range(3), nama)
    ax.set_yticks(range(3), nama)
    ax.set_title("Cosine similarity antar pusat kelas\n(rata-rata vektor TF-IDF ulasan latih)", fontsize=10)
    fig.tight_layout()
    fig.savefig(REPORTS / "cosine_kelas.png", dpi=180)
    plt.close(fig)

    svm = c["svm"]["per_app"]
    apps = sorted(NAMA_APP, key=lambda x: -svm[x]["porsi_bintang"][0])
    warna = ["#b0151f", "#c98a05", "#1c7a4c"]
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    y = 0
    ticks, lab = [], []
    for app in apps:
        for jenis, kunci in [("bintang", "porsi_bintang"), ("model", "porsi_model")]:
            kiri = 0.0
            for k, v in enumerate(svm[app][kunci]):
                ax.barh(y, v, left=kiri, color=warna[k], height=0.8, edgecolor="white")
                if v > 0.08:
                    ax.text(kiri + v / 2, y, f"{v * 100:.0f}%", ha="center", va="center", color="white" if k != 1 else "black", fontsize=8)
                kiri += v
            ticks.append(y)
            lab.append(f"{NAMA_APP[app]} ({jenis})")
            y += 1
        ax.text(1.01, y - 1.5, f"cos {svm[app]['cosine']:.4f}".replace(".", ","), va="center", fontsize=8.5)
        y += 0.6
    ax.set_yticks(ticks, lab, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_title("Porsi nada dari bintang dan dari Linear SVM di data uji", fontsize=10)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(REPORTS / "cosine_aplikasi.png", dpi=180)
    plt.close(fig)


def main() -> None:
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "split", "app", "at_min"])
    prep_test = prep[prep["split"] == "test"].reset_index(drop=True)
    y = np.load(FEATS / "y.npz")
    y_tr, y_te = y["train"].astype(int), y["test"].astype(int)
    X_tr = sp.load_npz(FEATS / "word_train.npz").tocsr()
    X_te = sp.load_npz(FEATS / "word_test.npz").tocsr()
    assert X_te.shape[0] == len(prep_test) == len(y_te)

    model = peluang_model(prep_test)
    pred_svm = model["svm"]["p"].argmax(1)
    f1 = f1_score(y_te, pred_svm, average="macro")
    assert abs(f1 - 0.6678) < 5e-4, f"urutan baris tidak cocok, macro-F1 SVM {f1:.4f}"

    a = bagian_a(X_tr, y_tr)
    print("A selesai", json.dumps(a["rata_cosine_pasangan"]), flush=True)
    b = bagian_b(X_tr, y_tr, X_te, y_te, pred_svm)
    print("B selesai", json.dumps(b["skor"]), b["detik"], "detik", flush=True)
    c = bagian_c(prep_test, y_te, model)
    print("C selesai", {k: v["semua"]["cosine"] for k, v in c.items()}, flush=True)
    d = bagian_d(model)
    out = {"fitur": "TF-IDF kata 1-2 gram, L2", "A_antar_kelas": a, "B_tetangga_terdekat": b, "C_profil_aplikasi": c, "D_antar_model": d}
    (REPORTS / "cosine.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    gambar(a, c)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
