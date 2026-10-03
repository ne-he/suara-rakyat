"""Data dashboard per aplikasi untuk halaman /dashboard.

Isinya ringkasan yang bisa dibaca orang awam, bukan perbandingan model:
- jumlah ulasan, rentang waktu, rata-rata bintang, porsi negatif/netral/positif per aplikasi
  (dari bintang penulisnya, semua 617.722 baris mentah, karena tiap ulasan tetap satu suara);
- kata dan frasa yang paling khas di ulasan negatif dibanding ulasan positif aplikasi yang sama
  (log-odds dengan prior Dirichlet, Monroe dkk. 2008), begitu juga sebaliknya untuk pujian;
- beberapa contoh ulasan pendek dari data uji, disaring dan disamarkan seperti pita ulasan.

Kata sifat umum (jelek, bagus, mantap, ...) sengaja dikeluarkan dari daftar keluhan dan pujian
supaya yang tampil adalah hal yang dikeluhkan (OTP, login, saldo), bukan sekadar rasa kesal.
Daftar hasil tetap dibaca manual sebelum dipajang.

Output: web/data/aplikasi.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
sys.path.insert(0, str(ROOT / "ml" / "scripts"))
from suara_ml.prediksi import web_models  # noqa: E402
from suara_ml.textnorm import mask_personal, tokens  # noqa: E402

web_extras = __import__("09_web_extras")
clean_mask, KASAR, SENSITIF = web_extras.clean_mask, web_extras.KASAR, web_extras.SENSITIF

SEED = 7
TOP = 8
ORDER = ["mobileJKN", "JMO", "satusehat", "pertamina", "KAI", "BMKG"]
NAMA = {"JMO": "JMO", "satusehat": "SatuSehat", "mobileJKN": "Mobile JKN", "pertamina": "MyPertamina", "KAI": "KAI Access", "BMKG": "Info BMKG"}
PENGELOLA = {
    "mobileJKN": "BPJS Kesehatan",
    "JMO": "BPJS Ketenagakerjaan",
    "satusehat": "Kementerian Kesehatan",
    "pertamina": "Pertamina",
    "KAI": "KAI",
    "BMKG": "BMKG",
}

# kata tugas: tidak dipakai sebagai kata tunggal, boleh muncul di dalam frasa dua kata
TUGAS = set(
    """yang dan di ke dari ini itu ada untuk dengan atau juga pada saja aja sudah udah lagi sih nya ya
    kok kan pun jadi bisa tidak tak bukan belum akan mau masih sangat banget sekali lebih kurang agak
    saya aku kami kita gue gw anda kamu dia mereka min admin kak pak bu tolong mohon karena krn jika
    kalau kalo tapi namun terus trus lalu apa kenapa mengapa bagaimana gimana kapan dimana mana siapa
    the and to is for of in it this app apk aplikasi aplikasinya apps nya kali buat bikin sama dah deh
    dong lah tuh nih gitu begitu begini semua setiap tiap harus hanya cuma cuman baru masa udh sdh blm
    tdk gak ga nggak enggak engga g gk ngga kenapa emang memang dulu nanti sampai sampe hari sekarang
    padahal malah minta buka pakai masuk cukup lumayan alhamdulillah dapat tau tahu biar kasih coba
    bener benar kayak seperti mending langsung kayaknya sepertinya biasa banyak sedikit selalu sering
    pernah kali kalinya cara mohon dapet ingin pengen pingin sangat amat paling tolonglah dibuka buat
    setelah sebelum mulu melulu pas dalam bagi jelas orang maju selama tetap kembali ulang lain lainnya
    adanya pokoknya like""".split()
)
# kata rasa umum: penting untuk model, tapi tidak memberi tahu apa yang dikeluhkan atau dipuji
RASA = set(
    """jelek buruk parah payah kecewa mengecewakan sampah ampas lambat lemot lelet ribet susah sulit ruwet
    error eror rusak gagal kacau aneh capek kesal kesel benci menyebalkan nyebelin percuma ngecewain
    bagus baik mantap mantab keren hebat top puas memuaskan suka senang membantu bermanfaat berguna mudah
    gampang cepat lancar terbaik oke ok good nice best great thanks terimakasih terima kasih semoga sukses
    makasih mantul jos sip luar biasa recommended rekomendasi bintang lima satu job membatu membantuu
    sangat banget bgt nice puas kurang lebih tingkatkan pertahankan diperbaiki perbaiki simple simpel
    mntap mantep efektif efisien""".split()
)


def rasa(t: str) -> bool:
    """Kata rasa umum, termasuk ejaan berulang seperti mantapp atau siip."""
    return t in RASA or re.sub(r"(.)\1+", r"\1", t) in RASA
BOLEH_FRASA_AWAL = {"tidak", "belum", "gagal", "susah", "sulit", "sering", "selalu", "harus", "lama", "masih"}


def istilah(toks: list[str]) -> set[str]:
    out = set()
    for t in toks:
        if len(t) >= 3 and t.isalpha() and t not in TUGAS and not rasa(t):
            out.add(t)
    for a, b in zip(toks, toks[1:]):
        if not (a.isalpha() and b.isalpha()) or a == b:
            continue
        if b in TUGAS or rasa(b):
            continue
        if (a in TUGAS or rasa(a)) and a not in BOLEH_FRASA_AWAL:
            continue
        out.add(f"{a} {b}")
    return out


def log_odds(a: Counter, na: int, b: Counter, nb: int, alpha: float = 0.5) -> dict[str, float]:
    """Skor z log-odds jumlah dokumen yang memuat istilah di kelompok a dibanding b."""
    hasil = {}
    for t in set(a) | set(b):
        x, y = a.get(t, 0), b.get(t, 0)
        la = np.log((x + alpha) / (na - x + alpha))
        lb = np.log((y + alpha) / (nb - y + alpha))
        var = 1 / (x + alpha) + 1 / (na - x + alpha) + 1 / (y + alpha) + 1 / (nb - y + alpha)
        hasil[t] = float((la - lb) / np.sqrt(var))
    return hasil


def pilih(skor: dict[str, float], cacah: Counter, n: int, minimum: int, k: int = TOP) -> list[dict]:
    calon = [(t, s) for t, s in skor.items() if s > 0 and cacah.get(t, 0) >= minimum]
    calon.sort(key=lambda x: -x[1])
    out: list[str] = []
    for t, _ in calon[:400]:
        if KASAR.search(t) or SENSITIF.search(t):
            continue
        kata = t.split()
        if len(kata) == 1:
            # kata yang sudah terwakili frasa di daftar dilewati
            if any(t in o.split() for o in out):
                continue
            out.append(t)
        else:
            # frasa lebih spesifik dari kata tunggalnya: ganti kata itu kalau frasanya cukup sering
            induk = [o for o in out if o in kata]
            if induk:
                o = induk[0]
                if cacah[t] >= 0.35 * cacah[o] and not any(o2 != o and set(kata) & set(o2.split()) for o2 in out):
                    out[out.index(o)] = t
                continue
            if any(set(kata) & set(o.split()) for o in out):
                continue
            out.append(t)
        if len(out) == k:
            break
    return [{"teks": t, "ulasan": int(cacah[t]), "porsi": round(cacah[t] / n, 4)} for t in out]


def contoh(prep: pd.DataFrame, app: str) -> list[dict]:
    te = prep[(prep["split"] == "test") & (prep["agree"] == 1) & (prep["app"] == app)].copy()
    t = te["text"].astype(str)
    ok = t.str.len().between(30, 140) & ~t.str.contains(r"\d|@|http|www\.|\n", regex=True) & clean_mask(t) & (t.str.count(r"[A-Za-z]") > 22)
    te = te[ok]
    out = []
    for label, k in [("negative", 2), ("neutral", 1), ("positive", 2)]:
        pool = te[te["label"] == label]
        if len(pool) == 0:
            continue
        # contoh yang dipajang hanya yang bintangnya sejalan dengan bacaan model web, supaya tidak
        # membingungkan pengunjung (ulasan bintang 5 berisi keluhan dibahas di bagian batasan)
        calon = pool.sample(n=min(40, len(pool)), random_state=SEED)
        teks = [mask_personal(" ".join(str(x).split())) for x in calon["text"]]
        baca = web_models(teks)["svm"]
        ambil = [(t, r) for t, b, (_, r) in zip(teks, baca, calon.iterrows()) if b == label][:k]
        out.extend({"teks": t, "label": label, "bintang": int(round(r["score_mean"]))} for t, r in ambil)
    return out


def main() -> None:
    raw = pd.read_csv(ROOT / "dataset" / "Rating_labeled.csv", usecols=["app", "content", "score", "at"])
    raw["content"] = raw["content"].fillna("").astype(str)
    raw["label"] = np.select([raw["score"] <= 2, raw["score"] == 3], ["negative", "neutral"], "positive")
    raw["at"] = pd.to_datetime(raw["at"], errors="coerce")
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet")

    # tokenisasi sekali per teks unik, lalu dihitung per baris lewat bobot jumlah kemunculan
    grup = raw.groupby(["app", "label", "content"]).size().reset_index(name="baris")
    unik = pd.Series(grup["content"].unique())
    peta = {c: istilah(tokens(c)) for c in unik}

    apps = []
    for app in ORDER:
        g = raw[raw["app"] == app]
        porsi = g["label"].value_counts(normalize=True)
        cacah: dict[str, Counter] = {"negative": Counter(), "positive": Counter()}
        n_label = {"negative": 0, "positive": 0}
        for lab in cacah:
            sub = grup[(grup["app"] == app) & (grup["label"] == lab)]
            n_label[lab] = int(sub["baris"].sum())
            for c, w in zip(sub["content"], sub["baris"]):
                for t in peta[c]:
                    cacah[lab][t] += int(w)
        skor = log_odds(cacah["negative"], n_label["negative"], cacah["positive"], n_label["positive"])
        minimum = max(5, int(0.004 * min(n_label.values())))
        apps.append(
            {
                "id": app,
                "nama": NAMA[app],
                "pengelola": PENGELOLA[app],
                "ulasan": int(len(g)),
                "mulai": str(g["at"].min())[:10],
                "akhir": str(g["at"].max())[:10],
                "rata_bintang": round(float(g["score"].mean()), 2),
                "porsi": {k: round(float(porsi.get(k, 0)), 4) for k in ["negative", "neutral", "positive"]},
                "keluhan": pilih(skor, cacah["negative"], n_label["negative"], minimum),
                "pujian": pilih({t: -s for t, s in skor.items()}, cacah["positive"], n_label["positive"], minimum),
                "contoh": contoh(prep, app),
            }
        )
        print(NAMA[app], "| keluhan:", [k["teks"] for k in apps[-1]["keluhan"]], "| pujian:", [k["teks"] for k in apps[-1]["pujian"]])

    total = raw["label"].value_counts(normalize=True)
    out = {
        "sumber": "IGAR v3 (Isnan dan Pardamean, 2025), ulasan Google Play, label dari bintang",
        "ulasan": int(len(raw)),
        "mulai": str(raw["at"].min())[:10],
        "akhir": str(raw["at"].max())[:10],
        "porsi": {k: round(float(total.get(k, 0)), 4) for k in ["negative", "neutral", "positive"]},
        "apps": apps,
    }
    dest = ROOT / "web" / "data" / "aplikasi.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("tersimpan", dest)


if __name__ == "__main__":
    main()
