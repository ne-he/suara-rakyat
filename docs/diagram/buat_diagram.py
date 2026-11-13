"""Gambar diagram untuk laporan dan presentasi.

Diagram: kerangka berpikir (desain penelitian), alur praproses dengan contoh kalimat, model
pengembangan Waterfall, use case, class diagram, sequence diagram, dan activity diagram.
Semua digambar dari kode supaya mudah diperbarui kalau arsitekturnya berubah, dan angka di
dalamnya dibaca dari berkas hasil (ml/reports, web/model, web/data), bukan diketik tangan.

Jalankan: python docs/diagram/buat_diagram.py
Hasilnya SVG (untuk slide) plus PNG (untuk dokumen Word). PNG dibuat lewat Chromium Playwright.
Alur praproses butuh data lokal (models/featurizer_wordchar.joblib) dan npm install di folder web.
"""

from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "ml"))

MERAH = "#ce1126"
MERAH_TUA = "#8e0c1a"
ASPAL = "#141210"
ABU = "#6f675c"
KERTAS = "#efe7d6"
PUTIH = "#f6f1e7"
GARIS = "#d9ceb8"
HIJAU = "#1c7a4c"
FONT = "Plus Jakarta Sans, Segoe UI, Arial, sans-serif"
MONO = "Consolas, JetBrains Mono, monospace"


def muat(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def ribuan(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def koma(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}".replace(".", ",")


class Kanvas:
    def __init__(self, w: int, h: int, judul: str) -> None:
        self.w, self.h, self.judul = w, h, judul
        self.isi: list[str] = []

    def teks(self, x: float, y: float, s: str, ukuran: float = 13, warna: str = ASPAL, tebal: int = 400, anchor: str = "middle", miring: bool = False, font: str = FONT) -> None:
        gaya = ' font-style="italic"' if miring else ""
        self.isi.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{font}" font-size="{ukuran}" font-weight="{tebal}" fill="{warna}"{gaya} xml:space="preserve">{html.escape(s)}</text>'
        )

    def baris_teks(self, x: float, y: float, baris: list[str], ukuran: float = 13, warna: str = ASPAL, tebal: int = 400, jarak: float = 15, anchor: str = "middle", font: str = FONT) -> None:
        for i, s in enumerate(baris):
            self.teks(x, y + i * jarak, s, ukuran, warna, tebal, anchor, font=font)

    def kotak(self, x: float, y: float, w: float, h: float, baris: list[str], isi: str = PUTIH, garis: str = ASPAL, tebal_garis: float = 2, r: float = 6, ukuran: float = 13, tebal: int = 500, judul: str | None = None) -> None:
        self.isi.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{isi}" stroke="{garis}" stroke-width="{tebal_garis}"/>')
        if judul:
            self.teks(x + w / 2, y + 22, judul, ukuran + 1.5, MERAH_TUA, 700)
            self.baris_teks(x + w / 2, y + 43, baris, ukuran, ASPAL, tebal, ukuran + 4)
        else:
            atas = y + h / 2 - (len(baris) - 1) * (ukuran + 3) / 2 + ukuran * 0.35
            self.baris_teks(x + w / 2, atas, baris, ukuran, ASPAL, tebal, ukuran + 3)

    def elips(self, cx: float, cy: float, rx: float, ry: float, baris: list[str], isi: str = PUTIH, garis: str = ASPAL) -> None:
        self.isi.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{isi}" stroke="{garis}" stroke-width="2"/>')
        self.baris_teks(cx, cy - (len(baris) - 1) * 7 + 4, baris, 12.5, ASPAL, 500, 14)

    def aktor(self, x: float, y: float, nama: list[str]) -> None:
        g = f'stroke="{ASPAL}" stroke-width="2" fill="none"'
        self.isi.append(f'<circle cx="{x}" cy="{y}" r="9" {g}/>')
        self.isi.append(f'<path d="M{x},{y + 9}V{y + 33}M{x - 13},{y + 18}H{x + 13}M{x},{y + 33}L{x - 11},{y + 50}M{x},{y + 33}L{x + 11},{y + 50}" {g}/>')
        self.baris_teks(x, y + 66, nama, 12.5, ASPAL, 600, 14)

    def garis(self, titik: list[tuple[float, float]], putus: bool = False, kepala: str = "penuh", warna: str = ASPAL, tebal: float = 1.8) -> None:
        d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in titik)
        dash = ' stroke-dasharray="6 4"' if putus else ""
        ujung = {"penuh": "url(#panah)", "garis": "url(#panah-garis)", "tidak": "none", "segitiga": "url(#segitiga)"}[kepala]
        self.isi.append(f'<path d="{d}" stroke="{warna}" stroke-width="{tebal}" fill="none"{dash} marker-end="{ujung}"/>')

    def panah(self, x1: float, y1: float, x2: float, y2: float, label: str | None = None, putus: bool = False, kepala: str = "penuh", geser: float = 0, naik: float = 6) -> None:
        self.garis([(x1, y1), (x2, y2)], putus, kepala)
        if label:
            self.teks((x1 + x2) / 2 + geser, (y1 + y2) / 2 - naik, label, 11.5, ABU, 600)

    def belah(self, cx: float, cy: float, w: float, h: float, baris: list[str], ukuran: float = 12) -> None:
        self.isi.append(f'<path d="M{cx},{cy - h / 2}L{cx + w / 2},{cy}L{cx},{cy + h / 2}L{cx - w / 2},{cy}Z" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="2"/>')
        self.baris_teks(cx, cy - (len(baris) - 1) * 7 + 4, baris, ukuran, ASPAL, 600, 14)

    def bingkai(self, x: float, y: float, w: float, h: float, nama: str) -> None:
        self.isi.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="{MERAH}" stroke-width="2" stroke-dasharray="8 5"/>')
        self.teks(x + 14, y + 22, nama, 14, MERAH_TUA, 700, anchor="start")

    def kelompok(self, x: float, y1: float, y2: float, nama: str) -> None:
        """Kurung kurawal sederhana di kiri beberapa kotak, dengan label tegak."""
        self.isi.append(f'<path d="M{x + 10},{y1}H{x}V{y2}H{x + 10}" stroke="{MERAH}" stroke-width="2" fill="none"/>')
        cy = (y1 + y2) / 2
        self.isi.append(
            f'<text x="{x - 12}" y="{cy}" transform="rotate(-90 {x - 12} {cy})" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="700" fill="{MERAH_TUA}">{html.escape(nama)}</text>'
        )

    def simpan(self, nama: str) -> Path:
        kepala = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{html.escape(self.judul)}">'
            f"<defs>"
            f'<marker id="panah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10Z" fill="{ASPAL}"/></marker>'
            f'<marker id="panah-garis" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0L10,5L0,10" fill="none" stroke="{ASPAL}" stroke-width="1.6"/></marker>'
            f'<marker id="segitiga" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path d="M0,0L12,6L0,12Z" fill="{PUTIH}" stroke="{ASPAL}" stroke-width="1.4"/></marker>'
            f"</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="{PUTIH}"/>'
        )
        f = HERE / nama
        f.write_text(kepala + "".join(self.isi) + "</svg>", encoding="utf-8", newline="\n")
        return f


def angka() -> dict:
    audit = muat("ml/reports/data_audit.json")
    site = muat("web/data/site.json")
    meta = muat("web/model/meta.json")
    cepat = muat("web/data/speed.json")
    from suara_ml.textnorm import slang_map

    svm = next(m for m in meta["models"] if m["id"] == meta["default_model"])
    return {
        "mentah": audit["raw_rows"],
        "unik": site["dataset"]["unique_texts"],
        "kembar": site["dataset"]["exact_duplicates"],
        "tahun": (site["dataset"]["date_min"][:4], site["dataset"]["date_max"][:4]),
        "slang": len(slang_map()),
        "kolom": meta["n_word"] + meta["n_char"],
        "konfigurasi": len(site["leaderboard"]),
        "f1": svm["metrics"]["test"]["macro_f1"],
        "ms": cepat["ms_per_review"][svm["id"]],
        "paritas": len(json.loads((ROOT / "web" / "scripts" / "parity_samples.json").read_text(encoding="utf-8"))),
    }


def kerangka() -> Kanvas:
    a = angka()
    langkah: list[tuple[str, list[str]]] = [
        ("Identifikasi masalah", ["Ulasan aplikasi layanan publik di Play Store menumpuk dan tidak terbaca satu per satu", "Pengelola layanan (pemerintah) sulit tahu keluhan yang paling sering muncul dan kapan memuncak"]),
        ("Studi literatur", ["Analisis sentimen, TF-IDF, SVM, Logistic Regression, Naive Bayes, IndoBERTweet", "Paper dataset IGAR, metrik macro-F1, cosine similarity, SDLC Waterfall"]),
        ("Pengumpulan data", [f"Dataset IGAR v3: {ribuan(a['mentah'])} ulasan Google Play, 6 aplikasi, {a['tahun'][0]} sampai {a['tahun'][1]}", "Label dari bintang: 1-2 negatif, 3 netral, 4-5 positif"]),
        ("Text preprocessing", ["Normalisasi Unicode NFKC, lowercase, buang URL", "Pangkas huruf berulang (aaa jadi aa), tokenization huruf, angka, emoji", f"Kamus slang {a['slang']} entri: gk jadi tidak, udh jadi sudah"]),
        ("Data cleaning dan data splitting", [f"Ulasan yang sama persis digabung: {ribuan(a['unik'])} teks unik", "Label mayoritas per teks, teks dengan label seri dibuang", "Hash MD5 teks: 80% train, 10% validation, 10% test (tanpa data leakage)"]),
        ("Feature extraction", ["TF-IDF word 1-2 gram dan character 2-5 gram", f"sublinear tf, normalisasi L2 per blok, {ribuan(a['kolom'])} fitur"]),
        ("Model training", ["Linear SVM, Logistic Regression, Multinomial Naive Bayes", f"Model pembanding: Ridge, SGD, LightGBM, IndoBERTweet ({a['konfigurasi']} konfigurasi)"]),
        ("Hyperparameter tuning di validation set", ["Pilih setelan dengan macro-F1 validation tertinggi", "Class bias adjustment dan temperature scaling"]),
        ("Evaluasi di test set", ["Macro-F1, accuracy, precision, recall, confusion matrix, kecepatan", "Bootstrap 1.000 kali, cosine similarity, uji 60 kalimat, replikasi paper"]),
    ]
    lanjut: list[tuple[str, list[str]]] = [
        ("Model selection", [f"Linear SVM: macro-F1 {koma(a['f1'])}, {koma(a['ms'])} ms per ulasan", "bobotnya bisa menunjukkan kata penentu ke pengguna"]),
        ("Implementasi aplikasi", ["Streamlit: pengelola pilih aplikasi, start date, end date", f"Ulasan diambil google-play-scraper, dibaca Linear SVM yang sama (parity test {ribuan(a['paritas'])} teks)"]),
        ("Pengujian dan evaluasi pengguna", ["Unit test, UI test, dan black-box scenario testing", "Kuesioner SUS dan wawancara pakar"]),
        ("Simpulan dan saran", []),
    ]
    W = 1080
    x, w = 220, 680
    tinggi = lambda n: 44 + 17 * n if n else 46
    jarak = 34
    k = Kanvas(W, 10, "Kerangka berpikir Suara Rakyat")
    k.teks(W / 2, 40, "Kerangka berpikir", 22, ASPAL, 800)
    k.teks(W / 2, 64, "tahapan penelitian dari masalah sampai simpulan", 13, ABU, 500)

    y = 96
    pos: list[tuple[float, float]] = []
    for i, (judul, baris) in enumerate(langkah):
        h = tinggi(len(baris))
        k.kotak(x, y, w, h, baris, isi=KERTAS if i in (0, 1) else PUTIH, judul=judul, ukuran=12.5, tebal=400)
        pos.append((y, h))
        if i < len(langkah) - 1:
            k.panah(x + w / 2, y + h, x + w / 2, y + h + jarak - 2)
        y += h + jarak

    cy = y + 50
    k.panah(x + w / 2, y - jarak + 0, x + w / 2, cy - 54)
    k.belah(x + w / 2, cy, 300, 108, ["akurat, cepat, dan", "bisa jalan gratis?"], 12.5)
    yf, hf = pos[5]
    k.garis([(x + w / 2 + 150, cy), (x + w + 60, cy), (x + w + 60, yf + hf / 2), (x + w + 2, yf + hf / 2)])
    k.teks(x + w / 2 + 210, cy - 8, "belum", 12, ABU, 700)
    k.baris_teks(x + w + 68, (yf + hf / 2 + cy) / 2 - 8, ["ubah fitur", "atau setelan"], 11.5, ABU, 600, 15, anchor="start")

    y = cy + 54 + jarak
    k.panah(x + w / 2, cy + 54, x + w / 2, y - 2, "sudah", geser=34, naik=-2)
    for i, (judul, baris) in enumerate(lanjut):
        h = tinggi(len(baris))
        akhir = i == len(lanjut) - 1
        k.kotak(x, y, w, h, baris if not akhir else [], isi=KERTAS if akhir else PUTIH, judul=judul, ukuran=12.5, tebal=400)
        pos.append((y, h))
        if not akhir:
            k.panah(x + w / 2, y + h, x + w / 2, y + h + jarak - 2)
        y += h + jarak

    k.kelompok(196, pos[0][0], pos[1][0] + pos[1][1], "Persiapan")
    k.kelompok(196, pos[2][0], pos[4][0] + pos[4][1], "Data dan preprocessing")
    k.kelompok(196, pos[5][0], pos[9][0] + pos[9][1], "Modeling dan evaluasi")
    k.kelompok(196, pos[10][0], pos[11][0] + pos[11][1], "Implementasi")
    k.h = int(y + 10)
    return k


def jejak_praproses() -> list[tuple[str, str]]:
    """Satu kalimat contoh dilewatkan ke fungsi praproses yang sama persis dengan pipeline."""
    import joblib

    from suara_ml.textnorm import REPEAT_RE, TOKEN_RE, URL_RE, char_ngrams, tokens, word_ngrams

    teks = "Aplikasinyaaa GK BISA login!!! udh 3x coba, OTP gak masuk2 https://bit.ly/abc 😡"
    s1 = unicodedata.normalize("NFKC", teks).lower()
    s2 = URL_RE.sub(" ", s1)
    s3 = REPEAT_RE.sub(r"\1\1", s2)
    t4 = TOKEN_RE.findall(s3)
    t5 = tokens(teks)
    kata = word_ngrams(t5, 2)
    huruf = char_ngrams(t5, 2, 5)
    fz = joblib.load(ROOT / "models" / "featurizer_wordchar.joblib")
    x = fz.transform([teks])
    nama = fz.feature_names()
    n_kata = int((x.indices < fz.n_word).sum())
    n_huruf = int(x.nnz - n_kata)
    urut = sorted(zip(x.indices, x.data), key=lambda p: -p[1])
    teratas = [f"{nama[i][2:]} {koma(v, 2)}" for i, v in urut if nama[i].startswith("w:")][:5]
    tak_dikenal = [g for g in kata if g not in fz.word_vec.vocabulary_]

    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "a.json", Path(d) / "b.json"
        src.write_text(json.dumps([teks], ensure_ascii=False), encoding="utf-8")
        npx = "npx.cmd" if os.name == "nt" else "npx"
        subprocess.run([npx, "tsx", "scripts/label-file.ts", str(src), str(dst)], cwd=ROOT / "web", check=True, capture_output=True)
        svm = json.loads(dst.read_text(encoding="utf-8"))[0]["svm"]
    p = svm["probs"]
    nada = {"negative": "negatif", "neutral": "netral", "positive": "positif"}
    return [
        ("Teks asli", teks),
        ("1. NFKC dan huruf kecil", s1),
        ("2. Buang tautan", " ".join(s2.split())),
        ("3. Pangkas huruf berulang", " ".join(s3.split())),
        ("4. Tokenisasi", " | ".join(t4)),
        ("5. Kamus slang", " | ".join(t5)),
        ("6. N-gram kata 1-2", f"{len(kata)} fitur: {', '.join(kata[11:16])}, ... ({len(tak_dikenal)} di antaranya tidak ada di kosakata latih, jadi diabaikan)"),
        ("7. N-gram karakter 2-5", f"{len(huruf)} potongan, contoh dari token login (_ = batas kata): {', '.join(g.replace(' ', '_') for g in char_ngrams(['login'], 2, 5)[:9])}, ..."),
        ("8. TF-IDF dan L2", f"{n_kata} kolom kata dan {n_huruf} kolom karakter terisi. Bobot kata tertinggi: {'; '.join(teratas)}"),
        ("9. Linear SVM", f"skor kelas + geser bias, softmax: negatif {koma(p['negative'], 2)}, netral {koma(p['neutral'], 2)}, positif {koma(p['positive'], 2)}. Hasil: {nada[svm['label']]}"),
    ]


def alur_praproses() -> Kanvas:
    baris = jejak_praproses()
    W = 1240
    kiri, lebar_kiri = 30, 270
    kanan = kiri + lebar_kiri + 24
    lebar_kanan = W - kanan - 30
    k = Kanvas(W, 10, "Alur praproses satu ulasan")
    k.teks(W / 2, 38, "Alur praproses dan pembacaan satu ulasan", 21, ASPAL, 800)
    k.teks(W / 2, 61, "setiap baris adalah keluaran asli fungsi yang dipakai pipeline dan web", 13, ABU, 500)
    y = 86
    for i, (langkah, hasil) in enumerate(baris):
        pecah = textwrap.wrap(hasil, 112) or [""]
        h = max(44, 20 + len(pecah) * 17)
        isi = KERTAS if i in (0, len(baris) - 1) else PUTIH
        k.kotak(kiri, y, lebar_kiri, h, [langkah], isi=isi, ukuran=13, tebal=700 if i in (0, len(baris) - 1) else 600)
        k.isi.append(f'<rect x="{kanan}" y="{y}" width="{lebar_kanan}" height="{h}" rx="6" fill="#ffffff" stroke="{GARIS}" stroke-width="1.6"/>')
        k.baris_teks(kanan + 14, y + 26 - (0 if len(pecah) > 1 else 3) + (h - 20 - len(pecah) * 17) / 2, pecah, 12.5, ASPAL, 400, 17, anchor="start", font=MONO)
        k.panah(kiri + lebar_kiri, y + h / 2, kanan - 2, y + h / 2)
        if i < len(baris) - 1:
            k.panah(kiri + lebar_kiri / 2, y + h, kiri + lebar_kiri / 2, y + h + 16)
        y += h + 18
    k.h = int(y + 6)
    return k


def waterfall() -> Kanvas:
    fase = [
        ("1. Analisis kebutuhan", ["Masalah, pengguna, dan data IGAR", "Functional dan non-functional requirement", "v5: pengguna utama pengelola layanan"]),
        ("2. Perancangan", ["Arsitektur tanpa database", "v4: model di serverless Vercel", "v5: Streamlit + google-play-scraper"]),
        ("3. Implementasi", ["Pipeline ML Python, skrip 01 sampai 17", "v4: Next.js dan TypeScript", "v5: Streamlit, 3 class Python"]),
        ("4. Pengujian", ["Parity test model lawan sklearn", "Unit test, UI test, black-box testing", "Evaluasi model di test set"]),
        ("5. Penerapan", ["v4 di Vercel, v5 di Streamlit", "Community Cloud, kode di GitHub", "Video demo dan presentasi"]),
        ("6. Pemeliharaan", ["Perbaikan dari masukan dosen dan", "pengguna, lalu putaran berikutnya", "dimulai lagi dari analisis kebutuhan"]),
    ]
    k = Kanvas(1220, 900, "Model pengembangan Waterfall Suara Rakyat")
    k.teks(610, 38, "Model pengembangan Waterfall", 22, ASPAL, 800)
    k.teks(610, 62, "setiap versi Suara Rakyat melewati keenam tahap secara berurutan", 13, ABU, 500)
    w, h, dx, dy, x0, y0 = 330, 104, 158, 122, 70, 92
    for i, (judul, baris) in enumerate(fase):
        x, y = x0 + i * dx, y0 + i * dy
        k.kotak(x, y, w, h, baris, isi=KERTAS if i in (0, 5) else PUTIH, judul=judul, ukuran=12, tebal=400)
        if i < len(fase) - 1:
            k.garis([(x + w, y + h / 2), (x + w + 34, y + h / 2), (x + w + 34, y + dy - 2)])
    xl, yl = x0 + 5 * dx, y0 + 5 * dy
    bawah = yl + h + 44
    k.garis([(xl + w / 2, yl + h), (xl + w / 2, bawah), (34, bawah), (34, y0 + h / 2), (x0 - 2, y0 + h / 2)], putus=True)
    k.teks(380, bawah - 10, "umpan balik: kebutuhan baru masuk ke putaran berikutnya", 12, ABU, 700)
    versi = [("v1", "17 Sep 2026", ["model dan web", "prediksi pertama"]), ("v2", "19 Sep 2026", ["cek massal, SUS,", "tren keluhan"]), ("v3", "23 Sep 2026", ["evaluasi tambahan,", "diagram laporan"]), ("v4", "3 Okt 2026", ["satu model,", "dashboard aplikasi"]), ("v5", "13 Nov 2026", ["Streamlit + scraper", "untuk pengelola layanan"])]
    k.teks(70, bawah + 44, "Putaran yang sudah dilalui (tanggal dari riwayat commit Git):", 13, ASPAL, 700, anchor="start")
    for i, (v, tgl, isi) in enumerate(versi):
        cx = 70 + i * 220
        k.kotak(cx, bawah + 58, 206, 66, [f"{v}, {tgl}", *isi], isi=KERTAS if v == "v5" else "#ffffff", garis=GARIS, ukuran=11.5, tebal=500)
    k.h = int(bawah + 146)
    return k


def use_case() -> Kanvas:
    k = Kanvas(1400, 840, "Use case diagram Suara Rakyat")
    k.teks(700, 36, "Use case diagram", 21, ASPAL, 800)
    k.bingkai(270, 66, 900, 720, "Suara Rakyat (web)")
    k.aktor(130, 330, ["Warga", "(pengguna umum)"])
    k.aktor(130, 610, ["Pengelola layanan", "atau peneliti"])
    k.garis([(130, 600), (130, 424)], kepala="segitiga")
    k.teks(140, 520, "generalisasi", 11, ABU, 600, anchor="start")
    k.aktor(1280, 330, ["Tim", "pengembang"])

    A, B, C = 450, 730, 1010
    utama = {
        "baca": (A, 150, ["Baca nada", "satu ulasan"]),
        "massal": (A, 360, ["Cek banyak", "ulasan"]),
        "dash": (A, 560, ["Lihat dashboard", "aplikasi"]),
        "sus": (A, 710, ["Isi kuesioner", "SUS"]),
    }
    tambahan = {
        "kata": (B, 110, ["Lihat kata", "penentu"]),
        "kartu": (B, 200, ["Unduh kartu", "hasil"]),
        "csv": (B, 310, ["Unggah file", "CSV"]),
        "unduh": (B, 410, ["Unduh hasil", "CSV"]),
        "tren": (B, 560, ["Lihat tren", "keluhan"]),
    }
    tim = [(C, 170, ["Latih dan", "pilih model"]), (C, 300, ["Ekspor model", "ke web"]), (C, 430, ["Perbarui data", "dashboard"]), (C, 560, ["Rekap jawaban", "kuesioner"])]
    for cx, cy, baris in utama.values():
        k.elips(cx, cy, 98, 38, baris)
    for cx, cy, baris in tambahan.values():
        k.elips(cx, cy, 88, 34, baris, isi="#ffffff")
    for cx, cy, baris in tim:
        k.elips(cx, cy, 98, 38, baris, isi=KERTAS)

    warga = (166, 352)
    for kunci in ["baca", "massal", "dash", "sus"]:
        cx, cy, _ = utama[kunci]
        k.garis([warga, (cx - 98, cy)], kepala="tidak")
    for cx, cy, _ in tim:
        k.garis([(1244, 352), (cx + 98, cy)], kepala="tidak")

    def relasi(dari, ke, label, gx, gy):
        k.garis([dari, ke], putus=True, kepala="garis")
        k.teks(gx, gy, label, 11, ABU, 600)

    bx, by, _ = utama["baca"]
    relasi((bx + 92, by - 14), (B - 88, 112), "«include»", 590, 112)
    relasi((B - 86, 206), (bx + 94, by + 12), "«extend»", 590, 200)
    mx, my, _ = utama["massal"]
    relasi((B - 86, 316), (mx + 94, my - 12), "«extend»", 590, 318)
    relasi((B - 86, 404), (mx + 94, my + 12), "«extend»", 590, 404)
    dx_, dy_, _ = utama["dash"]
    relasi((dx_ + 98, dy_), (B - 90, 560), "«include»", 590, 552)
    k.teks(700, 816, "Notasi UML: «include» selalu ikut dijalankan, «extend» hanya kalau pengguna memilihnya. Pengelola layanan atau peneliti mewarisi semua use case Warga.", 11.5, ABU, 500)
    return k


def kelas(k: Kanvas, x: float, y: float, w: float, nama: str, atribut: list[str], metode: list[str], isi: str = PUTIH) -> float:
    tinggi = 34 + max(len(atribut), 1) * 16 + 8 + max(len(metode), 1) * 16 + 10
    k.isi.append(f'<rect x="{x}" y="{y}" width="{w}" height="{tinggi}" rx="6" fill="{isi}" stroke="{ASPAL}" stroke-width="2"/>')
    k.teks(x + w / 2, y + 22, nama, 13, MERAH_TUA, 700)
    k.isi.append(f'<path d="M{x},{y + 32}H{x + w}" stroke="{ASPAL}" stroke-width="1.4"/>')
    for i, a in enumerate(atribut):
        k.teks(x + 11, y + 50 + i * 16, a, 11, ASPAL, 400, anchor="start")
    ymetode = y + 42 + max(len(atribut), 1) * 16
    k.isi.append(f'<path d="M{x},{ymetode}H{x + w}" stroke="{ASPAL}" stroke-width="1.4"/>')
    for i, m in enumerate(metode):
        k.teks(x + 11, ymetode + 18 + i * 16, m, 11, ASPAL, 400, anchor="start")
    return tinggi


def class_diagram() -> Kanvas:
    k = Kanvas(1500, 900, "Class diagram Suara Rakyat")
    k.teks(750, 36, "Class diagram", 21, ASPAL, 800)
    k.teks(750, 58, "kelas yang bekerja saat web dipakai, ditambah pipeline Python yang menyiapkan berkasnya", 13, ABU, 500)
    k.bingkai(30, 80, 1105, 790, "web (Next.js, TypeScript)")
    k.bingkai(1185, 80, 290, 790, "ml (Python, sebelum rilis)")
    c1, c2, c3, c4, lebar = 55, 330, 615, 880, 230

    def kotak(x, y, w, nama, atribut, metode, isi=PUTIH):
        return x, y, w, kelas(k, x, y, w, nama, atribut, metode, isi)

    an = kotak(c1, 118, lebar, "Analyzer  «komponen»", ["- teks: string", "- hasil: Prediction"], ["+ analyze(teks)", "+ unduhKartu()"])
    ba = kotak(c3, 118, lebar, "BatchAnalyzer  «komponen»", ["- tabel: string[][]", "- hasil: BatchResult"], ["+ run()", "+ unduhCsv()"])
    da = kotak(c4, 118, lebar, "DashboardAplikasi «komponen»", ["- pilih: string"], ["+ buka(idAplikasi)"])
    pr = kotak(c1, 300, lebar, "PredictRoute", ["- MAX_CHARS = 2000"], ["+ POST(req): Response"])
    rl = kotak(c2, 300, 240, "RateLimiter", ["- ember: Map<string, number[]>"], ["+ limited(kunci, ip, batas)"])
    br = kotak(c3, 300, lebar, "BatchRoute", ["- MAX_TEXTS = 1000"], ["+ POST(req): Response"])
    dj = kotak(c4, 300, lebar, "DataAplikasi  «json»", ["+ apps: Aplikasi[]", "+ porsi, keluhan, pujian"], [])
    ms = kotak(c2, 490, 240, "ModelStore  «singleton»", ["- meta: ModelMeta", "- coef: Map<string, Float32Array>"], ["+ loadModels(): Loaded", "+ predict(teks): Prediction"], KERTAS)
    tn = kotak(c4, 490, lebar, "TextNorm", ["- slang: Record<string, string>"], ["+ tokens(teks)", "+ wordNgrams(), charNgrams()"])
    mm = kotak(c1, 710, lebar, "ModelMeta", ["+ labels: Label[]", "+ default_model: string", "+ n_word, n_char"], [])
    mi = kotak(c2, 710, 240, "ModelInfo", ["+ id, name, features", "+ bias: number[]", "+ temperature: number"], [])
    pd_ = kotak(c4, 710, lebar, "Prediction", ["+ label: Label", "+ probs: Record<Label, number>", "+ tokens: TokenContribution[]"], [])

    bawah = lambda b: b[1] + b[3]
    tengah_x = lambda b: b[0] + b[2] / 2
    tengah_y = lambda b: b[1] + b[3] / 2
    kanan = lambda b: b[0] + b[2]

    def label(x, y, teks, anchor="start"):
        k.teks(x, y, teks, 11.5, ABU, 600, anchor=anchor)

    k.garis([(tengah_x(an), bawah(an)), (tengah_x(an), pr[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(an) + 8, (bawah(an) + pr[1]) / 2 + 4, "POST /api/predict")
    k.garis([(tengah_x(ba), bawah(ba)), (tengah_x(ba), br[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(ba) + 8, (bawah(ba) + br[1]) / 2 + 4, "POST /api/predict-batch")
    k.garis([(tengah_x(da), bawah(da)), (tengah_x(da), dj[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(da) + 8, (bawah(da) + dj[1]) / 2 + 4, "membaca")
    k.garis([(kanan(pr), tengah_y(pr)), (rl[0] - 2, tengah_y(rl))], putus=True, kepala="garis")
    k.garis([(br[0], tengah_y(br)), (kanan(rl) + 2, tengah_y(rl))], putus=True, kepala="garis")
    label(c2 + 120, 290, "keduanya memeriksa RateLimiter", "middle")
    xp = c1 + 60
    k.garis([(xp, bawah(pr)), (xp, ms[1] + 50), (ms[0] - 2, ms[1] + 50)], putus=True, kepala="garis")
    label(xp + 8, bawah(pr) + 40, "memakai")
    xb = c3 + 60
    yb = (bawah(br) + ms[1]) / 2
    k.garis([(xb, bawah(br)), (xb, yb), (c2 + 170, yb), (c2 + 170, ms[1] - 2)], putus=True, kepala="garis")
    label(xb + 8, bawah(br) + 22, "memakai")
    k.garis([(kanan(ms), ms[1] + 50), (tn[0] - 2, ms[1] + 50)], putus=True, kepala="garis")
    label((kanan(ms) + tn[0]) / 2, ms[1] + 42, "memakai", "middle")
    # komposisi: ModelStore memiliki satu ModelMeta
    xs, ys = ms[0] + 40, bawah(ms)
    k.isi.append(f'<path d="M{xs},{ys}l-7,10l7,10l7,-10z" fill="{ASPAL}"/>')
    k.garis([(xs, ys + 20), (xs, ys + 50), (tengah_x(mm), ys + 50), (tengah_x(mm), mm[1])], kepala="tidak")
    label(tengah_x(mm) + 8, ys + 44, "berisi 1")
    k.garis([(kanan(mm), tengah_y(mm)), (mi[0], tengah_y(mi))], kepala="tidak")
    label(mi[0] - 4, tengah_y(mi) - 6, "1..*", "end")
    xg = ms[0] + 190
    k.garis([(xg, bawah(ms)), (xg, ys + 70), (tengah_x(pd_), ys + 70), (tengah_x(pd_), pd_[1] - 2)], putus=True, kepala="garis")
    label((xg + tengah_x(pd_)) / 2, ys + 62, "menghasilkan", "middle")

    pl = kotak(1200, 118, 260, "PipelineML", ["+ skrip 01 sampai 17"], ["+ siapkan(), fitur(), latih()", "+ pilih(), ekspor()", "+ evaluasi(), dashboard()"], KERTAS)
    tf = kotak(1200, 330, 260, "TextFeaturizer", ["- word_vec, char_vec", "- FeatureConfig"], ["+ fit_transform(teks)", "+ transform(teks)"])
    tp = kotak(1200, 540, 260, "suara_ml.textnorm", ["- slang_id.json"], ["+ normalize(teks)", "+ tokens(teks)"])
    k.garis([(tengah_x(pl), bawah(pl)), (tengah_x(pl), tf[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(pl) + 8, (bawah(pl) + tf[1]) / 2 + 4, "memakai")
    k.garis([(tengah_x(tf), bawah(tf)), (tengah_x(tf), tp[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(tf) + 8, (bawah(tf) + tp[1]) / 2 + 4, "memakai")
    k.garis([(1185, 852), (1137, 852)], putus=True, kepala="garis")
    k.baris_teks(1200, 790,["berkas model dan aplikasi.json", "disalin ke web saat rilis.", "Aturan textnorm sama persis", "dengan TextNorm web (uji paritas)."], 11.5, ABU, 600, 15, anchor="start")
    return k


def sequence() -> Kanvas:
    k = Kanvas(1300, 856, "Sequence diagram baca satu ulasan")
    k.teks(650, 34, "Sequence diagram: satu ulasan dibaca", 20, ASPAL, 800)
    peserta = [(110, ["Pengguna"]), (350, ["Halaman web", "(Analyzer)"]), (620, ["PredictRoute", "/api/predict"]), (870, ["RateLimiter"]), (1120, ["ModelStore"])]
    for x, nama in peserta:
        k.kotak(x - 90, 58, 180, 52, nama, isi=KERTAS)
        k.isi.append(f'<path d="M{x},110V800" stroke="{ABU}" stroke-width="1.4" stroke-dasharray="5 5"/>')

    def pesan(y, x1, x2, teks, balas=False):
        k.panah(x1, y, x2, y, None, putus=balas, kepala="garis" if balas else "penuh")
        k.teks((x1 + x2) / 2, y - 8, teks, 11.5, ASPAL, 600)

    def aktif(x, y1, y2):
        k.isi.append(f'<rect x="{x - 6}" y="{y1}" width="12" height="{y2 - y1}" fill="{PUTIH}" stroke="{ASPAL}" stroke-width="1.5"/>')

    def catatan(x, y, w, baris):
        k.kotak(x, y, w, 18 + len(baris) * 15, baris, isi=KERTAS, r=4, ukuran=11, tebal=500)

    def bingkai_alt(y1, y2, judul, syarat):
        k.isi.append(f'<rect x="60" y="{y1}" width="1180" height="{y2 - y1}" rx="6" fill="none" stroke="{MERAH}" stroke-width="1.6"/>')
        k.isi.append(f'<path d="M60,{y1}H124V{y1 + 24}H60Z" fill="{MERAH}"/>')
        k.teks(92, y1 + 17, judul, 12, PUTIH, 700)
        k.teks(136, y1 + 17, syarat, 11.5, ABU, 600, anchor="start")

    pesan(150, 110, 350, "tulis ulasan, tekan Baca nadanya")
    aktif(350, 150, 770)
    bingkai_alt(172, 240, "alt", "[teks kosong]")
    pesan(222, 350, 110, "pesan: tulis atau tempel ulasanmu dulu", balas=True)
    pesan(282, 350, 620, "POST /api/predict {text}")
    aktif(620, 282, 715)
    pesan(318, 620, 870, "limited(ip, 60 per menit)")
    pesan(346, 870, 620, "boleh", balas=True)
    catatan(650, 360, 210, ["cek JSON dan panjang teks", "(maksimal 2.000 karakter)"])
    bingkai_alt(412, 470, "alt", "[melebihi batas atau format salah]")
    pesan(456, 620, 350, "429 / 400 / 413 + pesan galat", balas=True)
    pesan(520, 620, 1120, "predict(teks)")
    aktif(1120, 520, 640)
    catatan(905, 536, 200, ["normalisasi, TF-IDF,", "skor Linear SVM + bias,", "softmax, kata penentu"])
    pesan(640, 1120, 620, "Prediction", balas=True)
    pesan(690, 620, 350, "{label, probs, tokens}", balas=True)
    pesan(745, 350, 110, "nada, tingkat yakin, kata penentu", balas=True)
    k.teks(650, 836, "Teks yang dikirim tidak disimpan di mana pun. Bobot model dimuat sekali per instance server, jadi panggilan berikutnya langsung dihitung.", 11.5, ABU, 500)
    return k


def activity() -> Kanvas:
    k = Kanvas(1200, 1250, "Activity diagram cek banyak ulasan")
    k.teks(600, 36, "Activity diagram: cek banyak ulasan", 20, ASPAL, 800)
    jalur = [(40, "Pengguna"), (420, "Halaman web (browser)"), (800, "Server (/api/predict-batch)")]
    for x, nama in jalur:
        k.isi.append(f'<rect x="{x}" y="60" width="380" height="1160" fill="none" stroke="{ASPAL}" stroke-width="1.6"/>')
        k.isi.append(f'<rect x="{x}" y="60" width="380" height="36" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="1.6"/>')
        k.teks(x + 190, 84, nama, 13.5, MERAH_TUA, 700)
    P, Wb, S = 230, 610, 990

    def aksi(cx, cy, baris, w=250):
        h = 22 + len(baris) * 16
        k.kotak(cx - w / 2, cy - h / 2, w, h, baris, isi="#ffffff", r=16, ukuran=12, tebal=500)
        return h / 2

    def mulai(cx, cy):
        k.isi.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{ASPAL}"/>')

    def selesai(cx, cy):
        k.isi.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="none" stroke="{ASPAL}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="8" fill="{ASPAL}"/>')

    def pilihan(cx, cy, baris=None, w=44, h=44):
        k.isi.append(f'<path d="M{cx},{cy - h / 2}L{cx + w / 2},{cy}L{cx},{cy + h / 2}L{cx - w / 2},{cy}Z" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="2"/>')
        if baris:
            k.baris_teks(cx + w / 2 + 8, cy - 18, baris, 11.5, ABU, 600, 14, anchor="start")

    def jaga(x, y, s, anchor="start"):
        k.teks(x, y, s, 11.5, ABU, 700, anchor=anchor)

    mulai(P, 130)
    h = aksi(P, 190, ["Buka halaman Massal"])
    k.panah(P, 141, P, 190 - h - 2)
    k.panah(P, 190 + h, P, 248)
    pilihan(P, 270)
    k.baris_teks(P - 30, 262, ["unggah CSV atau", "pakai contoh?"], 11.5, ABU, 600, 14, anchor="end")
    h = aksi(P, 370, ["Tempel ulasan,", "satu per baris"])
    k.panah(P, 292, P, 370 - h - 2)
    jaga(P - 34, 322, "[tidak]", "end")
    h2 = aksi(Wb, 270, ["Baca file CSV di browser,", "tebak kolom ulasan dan bintang"], 270)
    k.panah(P + 22, 270, Wb - 135 - 2, 270)
    jaga(P + 60, 262, "[ya]")
    h3 = aksi(Wb, 370, ["Tampilkan pilihan kolom", "dan jumlah baris"], 270)
    k.panah(Wb, 270 + h2, Wb, 370 - h3 - 2)
    pilihan(P, 460)
    k.panah(P, 370 + h, P, 438)
    k.garis([(Wb, 370 + h3), (Wb, 460), (P + 24, 460)])
    h = aksi(P, 540, ["Tekan Baca semua"])
    k.panah(P, 482, P, 540 - h - 2)
    pilihan(Wb, 540)
    k.baris_teks(Wb + 30, 506, ["lebih dari", "1.000 ulasan?"], 11.5, ABU, 600, 14, anchor="start")
    k.panah(P + 125, 540, Wb - 24, 540)
    h = aksi(Wb, 630, ["Ambil 1.000 pertama,", "tampilkan peringatan"])
    k.panah(Wb, 562, Wb, 630 - h - 2)
    jaga(Wb - 10, 590, "[ya]", "end")
    pilihan(Wb, 710)
    k.panah(Wb, 630 + h, Wb, 688)
    k.garis([(Wb + 22, 540), (Wb + 150, 540), (Wb + 150, 710), (Wb + 24, 710)])
    jaga(Wb + 144, 594, "[tidak]", "end")
    h = aksi(Wb, 790, ["Kirim POST /api/predict-batch"])
    k.panah(Wb, 732, Wb, 790 - h - 2)
    h4 = aksi(S, 790, ["Validasi JSON, jumlah,", "dan jenis teks"])
    k.panah(Wb + 125, 790, S - 125 - 2, 790)
    h5 = aksi(S, 880, ["Baca nada tiap ulasan", "dengan Linear SVM"])
    k.panah(S, 790 + h4, S, 880 - h5 - 2)
    h6 = aksi(S, 970, ["Hitung porsi nada dan", "kata pendorong tiap nada"])
    k.panah(S, 880 + h5, S, 970 - h6 - 2)
    h7 = aksi(Wb, 970, ["Tampilkan ringkasan, grafik,", "tabel, dan saringan nada"], 270)
    k.panah(S - 125, 970, Wb + 135 + 2, 970)
    pilihan(P, 1060, ["unduh hasil?"])
    k.garis([(Wb, 970 + h7), (Wb, 1060), (P + 24, 1060)])
    h = aksi(P, 1140, ["Tekan Unduh hasil CSV"])
    k.panah(P, 1082, P, 1140 - h - 2)
    jaga(P - 10, 1104, "[ya]", "end")
    h8 = aksi(Wb, 1140, ["Susun file CSV di browser", "(kolom nada dan keyakinan)"], 270)
    k.panah(P + 125, 1140, Wb - 135 - 2, 1140)
    selesai(Wb, 1200)
    k.panah(Wb, 1140 + h8, Wb, 1185)
    k.garis([(P - 22, 1060), (80, 1060), (80, 1200), (Wb - 15, 1200)])
    jaga(88, 1050, "[tidak]")
    return k


# ---------------- v5: app Streamlit untuk pengelola layanan ----------------


def use_case_v5() -> Kanvas:
    k = Kanvas(1400, 820, "Use case diagram Suara Rakyat v5")
    k.teks(700, 36, "Use case diagram (v5)", 21, ASPAL, 800)
    k.bingkai(270, 66, 880, 700, "Suara Rakyat v5 (Streamlit)")
    k.aktor(130, 330, ["Pengelola layanan", "(pemerintah)"])
    k.aktor(1290, 120, ["Google Play", "«sistem»"])

    A, B = 470, 880
    utama = {
        "ambil": (A, 210, ["Ambil dan baca", "ulasan"]),
        "ringkas": (A, 380, ["Lihat ringkasan", "nada"]),
        "tren": (A, 500, ["Lihat tren", "nada"]),
        "daftar": (A, 610, ["Lihat daftar", "ulasan per nada"]),
        "csv": (A, 715, ["Unduh hasil", "CSV"]),
    }
    tambahan = {
        "gp": (B, 120, ["Ambil ulasan dari", "Google Play"]),
        "baca": (B, 215, ["Baca nada dengan", "Linear SVM"]),
        "id": (B, 310, ["Isi application ID", "atau link"]),
        "kata": (B, 410, ["Lihat kata", "penentu"]),
        "urut": (B, 610, ["Urutkan", "ulasan"]),
    }
    for cx, cy, baris in utama.values():
        k.elips(cx, cy, 104, 38, baris)
    for cx, cy, baris in tambahan.values():
        k.elips(cx, cy, 98, 34, baris, isi="#ffffff")

    for cx, cy, _ in utama.values():
        k.garis([(166, 352), (cx - 104, cy)], kepala="tidak")
    gx, gy, _ = tambahan["gp"]
    k.garis([(gx + 98, gy), (1252, 142)], kepala="tidak")

    def relasi(dari, ke, label, lx, ly):
        k.garis([dari, ke], putus=True, kepala="garis")
        k.teks(lx, ly, label, 11, ABU, 600)

    ax, ay, _ = utama["ambil"]
    relasi((ax + 96, ay - 16), (B - 96, 128), "«include»", 680, 150)
    relasi((ax + 104, ay), (B - 98, 213), "«include»", 680, 202)
    relasi((B - 94, 300), (ax + 98, ay + 14), "«extend»", 735, 306)
    rx, ry, _ = utama["ringkas"]
    relasi((rx + 102, ry + 4), (B - 98, 408), "«include»", 680, 384)
    dx_, dy_, _ = utama["daftar"]
    relasi((B - 98, 610), (dx_ + 104, dy_), "«extend»", 680, 600)
    k.teks(710, 796, "«include» selalu ikut dijalankan, «extend» hanya kalau pengguna memilihnya. Ringkasan, tren, daftar, dan CSV tersedia setelah ulasan diambil.", 11.5, ABU, 500)
    return k


def class_diagram_v5() -> Kanvas:
    k = Kanvas(1500, 840, "Class diagram Suara Rakyat v5")
    k.teks(750, 36, "Class diagram (v5)", 21, ASPAL, 800)
    k.teks(750, 58, "kelas di streamlit-app/suara beserta library dan berkas yang dipakainya", 13, ABU, 500)

    def kotak(x, y, w, nama, atribut, metode, isi=PUTIH):
        return x, y, w, kelas(k, x, y, w, nama, atribut, metode, isi)

    bawah = lambda b: b[1] + b[3]
    tengah_x = lambda b: b[0] + b[2] / 2
    kanan = lambda b: b[0] + b[2]

    def label(x, y, teks, anchor="start"):
        k.teks(x, y, teks, 11.5, ABU, 600, anchor=anchor)

    app = kotak(560, 92, 380, "app.py  «Streamlit»", ["- session_state['hasil']: dict", "- APPS: dict[str, str]"], ["+ run_search(app_id, start, end)", "+ show_dashboard(hasil)", "+ parse_app_id(teks): str"], KERTAS)
    anf = kotak(60, 110, 250, "AppNotFound  «exception»", [], [])
    rs = kotak(40, 330, 380, "ReviewScraper", ["+ max_fetch: int = 10000", "- fetch_page: Callable"], ["+ app_info(app_id): dict", "+ fetch(app_id, start, end,", "      on_progress): ScrapeResult"])
    ra = kotak(560, 330, 380, "ReviewAnalysis", ["- df: DataFrame", "- _preds: list[Prediction]"], ["+ counts(), unreadable()", "+ star_agreement(): float", "+ trend(), is_weekly()", "+ top_words(label, n)", "+ table(label), to_csv(): bytes"])
    sc = kotak(1080, 330, 380, "SentimentClassifier", ["- word_index, char_index: dict", "- idf, coef: ndarray", "- offset: ndarray (intercept + bias)", "- temperature: float"], ["+ predict(teks): Prediction", "+ predict_many(teks): list[Prediction]"], KERTAS)
    sr = kotak(40, 640, 250, "ScrapeResult  «dataclass»", ["+ reviews: DataFrame", "+ fetched: int", "+ hit_limit: bool", "+ oldest_seen: datetime"], [])
    gp = kotak(310, 640, 210, "google_play_scraper", ["«library»"], ["+ app(), reviews()"])
    pr = kotak(610, 640, 280, "Prediction  «dataclass»", ["+ label: str | None", "+ confidence: float | None", "+ probs: tuple[float, ...]", "+ tokens: tuple[(str, float)]"], [])
    tn = kotak(990, 640, 240, "suara_ml.textnorm", ["«modul»"], ["+ tokens(), word_ngrams()", "+ char_ngrams(), mask_personal()"])
    wm = kotak(1250, 640, 220, "web/model  «berkas»", ["meta.json, vocab_word.txt,", "vocab_char.txt, idf.f32,", "coef_svm.f32"], [])

    # app memakai tiga kelas utama
    k.garis([(tengah_x(app) - 140, bawah(app)), (tengah_x(app) - 140, 300), (tengah_x(rs), 300), (tengah_x(rs), rs[1] - 2)], putus=True, kepala="garis")
    k.garis([(tengah_x(app), bawah(app)), (tengah_x(ra), ra[1] - 2)], putus=True, kepala="garis")
    k.garis([(tengah_x(app) + 140, bawah(app)), (tengah_x(app) + 140, 300), (tengah_x(sc), 300), (tengah_x(sc), sc[1] - 2)], putus=True, kepala="garis")
    label(758, 292, "memakai")
    # ReviewScraper melempar AppNotFound
    k.garis([(tengah_x(rs) - 60, rs[1]), (tengah_x(anf), bawah(anf) + 2)], putus=True, kepala="garis")
    label(tengah_x(anf) + 8, (bawah(anf) + rs[1]) / 2 + 20, "melempar")
    # ReviewScraper membuat ScrapeResult dan memakai library
    k.garis([(tengah_x(sr), bawah(rs)), (tengah_x(sr), sr[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(sr) + 8, (bawah(rs) + sr[1]) / 2 + 4, "membuat")
    k.garis([(tengah_x(gp), bawah(rs)), (tengah_x(gp), gp[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(gp) + 8, (bawah(rs) + gp[1]) / 2 + 4, "memakai")
    # ReviewAnalysis menyimpan banyak Prediction (aggregation)
    xs, ys = tengah_x(ra), bawah(ra)
    k.isi.append(f'<path d="M{xs},{ys}l-8,11l8,11l8,-11z" fill="{PUTIH}" stroke="{ASPAL}" stroke-width="1.6"/>')
    k.garis([(xs, ys + 22), (xs, pr[1])], kepala="tidak")
    label(xs + 8, pr[1] - 8, "0..*")
    # SentimentClassifier membuat Prediction, memakai textnorm, membaca berkas model
    xa = sc[0] + 30
    k.garis([(xa, bawah(sc)), (xa, 600), (kanan(pr) - 40, 600), (kanan(pr) - 40, pr[1] - 2)], putus=True, kepala="garis")
    label((xa + kanan(pr) - 40) / 2, 592, "membuat", "middle")
    k.garis([(1170, bawah(sc)), (1170, tn[1] - 2)], putus=True, kepala="garis")
    label(1178, 620, "memakai")
    k.garis([(tengah_x(wm), bawah(sc)), (tengah_x(wm), wm[1] - 2)], putus=True, kepala="garis")
    label(tengah_x(wm) + 8, 620, "membaca")
    k.teks(750, 818, "Garis putus = dependency (memakai, membuat, melempar). Belah ketupat kosong = aggregation: satu ReviewAnalysis menyimpan banyak Prediction.", 11.5, ABU, 500)
    return k


def sequence_v5() -> Kanvas:
    k = Kanvas(1400, 1080, "Sequence diagram ambil dan baca ulasan v5")
    k.teks(700, 34, "Sequence diagram (v5): ambil dan baca ulasan", 20, ASPAL, 800)
    xs = [100, 330, 560, 790, 1020, 1260]
    nama = [["Pengelola", "layanan"], ["app.py", "(Streamlit)"], ["ReviewScraper"], ["Google Play"], ["Sentiment", "Classifier"], ["ReviewAnalysis"]]
    for x, n in zip(xs, nama):
        k.kotak(x - 85, 58, 170, 52, n, isi=KERTAS)
        k.isi.append(f'<path d="M{x},110V1030" stroke="{ABU}" stroke-width="1.4" stroke-dasharray="5 5"/>')
    P, A, R, G, S, N = xs

    def latar(x, y, teks, anchor="middle"):
        # latar polos di belakang label supaya garis lifeline tidak menembus tulisan
        w = len(teks) * 6.6 + 10
        x0 = x - w / 2 if anchor == "middle" else x - 5
        k.isi.append(f'<rect x="{x0:.1f}" y="{y - 13}" width="{w:.1f}" height="17" fill="{PUTIH}"/>')

    def pesan(y, x1, x2, teks, balas=False):
        k.panah(x1, y, x2, y, None, putus=balas, kepala="garis" if balas else "penuh")
        latar((x1 + x2) / 2, y - 8, teks)
        k.teks((x1 + x2) / 2, y - 8, teks, 11.5, ASPAL, 600)

    def aktif(x, y1, y2):
        k.isi.append(f'<rect x="{x - 6}" y="{y1}" width="12" height="{y2 - y1}" fill="{PUTIH}" stroke="{ASPAL}" stroke-width="1.5"/>')

    def bingkai(y1, y2, judul, syarat, x1=60, x2=1340):
        k.isi.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="6" fill="none" stroke="{MERAH}" stroke-width="1.6"/>')
        k.isi.append(f'<path d="M{x1},{y1}H{x1 + 64}V{y1 + 24}H{x1}Z" fill="{MERAH}"/>')
        k.teks(x1 + 32, y1 + 17, judul, 12, PUTIH, 700)
        latar(x1 + 76, y1 + 17, syarat, "start")
        k.teks(x1 + 76, y1 + 17, syarat, 11.5, ABU, 600, anchor="start")

    def catatan(x, y, w, baris):
        k.kotak(x, y, w, 18 + len(baris) * 15, baris, isi=KERTAS, r=4, ukuran=11, tebal=500)

    pesan(150, P, A, "pilih aplikasi dan tanggal")
    aktif(A, 150, 1000)
    bingkai(170, 232, "alt", "[start date > end date atau application ID tidak valid]")
    pesan(216, A, P, "pesan galat", balas=True)
    pesan(272, A, R, "app_info(app_id)")
    aktif(R, 272, 340)
    pesan(300, R, G, "app(app_id)")
    pesan(330, G, R, "judul, pengembang", balas=True)
    bingkai(350, 412, "alt", "[aplikasi tidak ditemukan]")
    pesan(396, R, A, "AppNotFound", balas=True)
    pesan(396, A, P, "pesan: tidak ditemukan", balas=True)
    pesan(452, A, R, "fetch(app_id, start, end, on_progress)")
    aktif(R, 452, 640)
    bingkai(472, 610, "loop", "[belum lewat start date, ulasan belum habis, kurang dari 10.000]", 260, 860)
    pesan(516, R, G, "reviews(NEWEST, 200, token)")
    pesan(548, G, R, "200 ulasan + token berikutnya", balas=True)
    pesan(590, R, A, "on_progress(jumlah, tanggal tertua)")
    pesan(636, R, A, "ScrapeResult (tanpa identitas)", balas=True)
    pesan(690, A, S, "predict_many(teks ulasan)")
    aktif(S, 690, 790)
    catatan(1040, 706, 200, ["TF-IDF, skor Linear SVM", "+ bias, softmax(skor/T),", "kata penentu"])
    pesan(790, S, A, "list[Prediction]", balas=True)
    pesan(840, A, N, "ReviewAnalysis(reviews, predictions)")
    aktif(N, 840, 930)
    pesan(880, A, N, "counts(), trend(), top_words(), table()")
    pesan(926, N, A, "ringkasan, tren, kata, tabel", balas=True)
    pesan(980, A, P, "dashboard dan daftar ulasan", balas=True)
    k.teks(700, 1062, "Hasil disimpan di session_state selama halaman terbuka, tidak di database. Ganti filter nada tidak mengambil ulang ulasan.", 11.5, ABU, 500)
    return k


def activity_v5() -> Kanvas:
    k = Kanvas(1200, 1480, "Activity diagram pantau ulasan v5")
    k.teks(600, 36, "Activity diagram (v5): pantau ulasan satu aplikasi", 20, ASPAL, 800)
    jalur = [(40, "Pengelola layanan"), (420, "App Streamlit"), (800, "Google Play")]
    for x, n in jalur:
        k.isi.append(f'<rect x="{x}" y="60" width="380" height="1400" fill="none" stroke="{ASPAL}" stroke-width="1.6"/>')
        k.isi.append(f'<rect x="{x}" y="60" width="380" height="36" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="1.6"/>')
        k.teks(x + 190, 84, n, 13.5, MERAH_TUA, 700)
    P, A, G = 230, 610, 990

    def aksi(cx, cy, baris, w=250):
        h = 22 + len(baris) * 16
        k.kotak(cx - w / 2, cy - h / 2, w, h, baris, isi="#ffffff", r=16, ukuran=12, tebal=500)
        return h / 2

    def pilihan(cx, cy, w=44, h=44):
        k.isi.append(f'<path d="M{cx},{cy - h / 2}L{cx + w / 2},{cy}L{cx},{cy + h / 2}L{cx - w / 2},{cy}Z" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="2"/>')

    def jaga(x, y, s, anchor="start"):
        k.teks(x, y, s, 11.5, ABU, 700, anchor=anchor)

    def tanya(x, y, baris, anchor="start"):
        k.baris_teks(x, y, baris, 11.5, ABU, 600, 14, anchor=anchor)

    k.isi.append(f'<circle cx="{P}" cy="125" r="11" fill="{ASPAL}"/>')
    h = aksi(P, 180, ["Buka Suara Rakyat v5"])
    k.panah(P, 136, P, 180 - h - 2)
    pilihan(P, 255)
    k.panah(P, 180 + h, P, 233)
    tanya(P + 28, 214, ["aplikasi ada", "di daftar?"])
    h1 = aksi(140, 345, ["Pilih dari", "daftar 6 aplikasi"], 170)
    h2 = aksi(320, 345, ["Isi application ID", "atau tempel link"], 170)
    k.garis([(P - 22, 255), (140, 255), (140, 345 - h1 - 2)])
    jaga(150, 247, "[ya]", "end")
    k.garis([(P + 22, 255), (320, 255), (320, 345 - h2 - 2)])
    jaga(310, 247, "[tidak]")
    pilihan(P, 420)
    k.garis([(140, 345 + h1), (140, 420), (P - 24, 420)])
    k.garis([(320, 345 + h2), (320, 420), (P + 24, 420)])
    h = aksi(P, 490, ["Isi start date dan end date"])
    k.panah(P, 442, P, 490 - h - 2)
    h = aksi(P, 570, ["Tekan Ambil dan baca ulasan"])
    k.panah(P, 490 + 19, P, 570 - h - 2)
    pilihan(A, 570)
    k.panah(P + 125, 570, A - 24, 570)
    tanya(A + 30, 555, ["input valid?"])
    he = aksi(A, 480, ["Tampilkan pesan galat"])
    k.panah(A, 548, A, 480 + he + 2)
    jaga(A + 8, 528, "[tidak]")
    k.panah(A - 125, 480, P + 125 + 2, 490)
    h = aksi(A, 660, ["Cek aplikasi (app_info)"])
    k.panah(A, 592, A, 660 - h - 2)
    jaga(A + 8, 614, "[ya]")
    hg = aksi(G, 660, ["Kirim judul dan pengembang"])
    k.panah(A + 125, 660, G - 125 - 2, 660)
    pilihan(A, 750)
    k.garis([(G, 660 + hg), (G, 706), (A, 706), (A, 726)])
    tanya(A - 30, 755, ["ditemukan?"], "end")
    k.garis([(A + 22, 750), (765, 750), (765, 480), (A + 125 + 2, 480)])
    jaga(A + 32, 742, "[tidak]")
    h = aksi(A, 840, ["Minta 200 ulasan terbaru", "(lanjut dari token)"])
    k.panah(A, 772, A, 840 - h - 2)
    jaga(A + 8, 796, "[ya]")
    hg = aksi(G, 840, ["Kirim 200 ulasan", "dan token berikutnya"])
    k.panah(A + 125, 840, G - 125 - 2, 840)
    h3 = aksi(A, 935, ["Simpan ulasan di rentang tanggal,", "buang nama dan foto, perbarui progres"], 300)
    k.garis([(G, 840 + hg), (G, 935), (A + 150 + 2, 935)])
    pilihan(A, 1020)
    k.panah(A, 935 + h3, A, 998)
    tanya(A + 30, 1010, ["lewat start date, ulasan", "habis, atau 10.000?"])
    k.garis([(A - 22, 1020), (440, 1020), (440, 840), (A - 125 - 2, 840)])
    jaga(448, 1012, "[belum]")
    h = aksi(A, 1105, ["Baca nada tiap ulasan", "dengan Linear SVM"])
    k.panah(A, 1042, A, 1105 - h - 2)
    jaga(A + 8, 1064, "[sudah]")
    h4 = aksi(A, 1190, ["Susun ringkasan: persen nada,", "tren, kata penentu, tabel"], 270)
    k.panah(A, 1105 + h, A, 1190 - h4 - 2)
    h5 = aksi(P, 1190, ["Baca dashboard dan daftar", "ulasan per nada"])
    k.panah(A - 135, 1190, P + 125 + 2, 1190)
    pilihan(P, 1275)
    k.panah(P, 1190 + h5, P, 1253)
    tanya(P + 30, 1270, ["unduh CSV?"])
    h = aksi(P, 1355, ["Tekan Unduh semua hasil"])
    k.panah(P, 1297, P, 1355 - h - 2)
    jaga(P - 10, 1320, "[ya]", "end")
    h6 = aksi(A, 1355, ["Susun CSV (UTF-8 untuk Excel)"], 270)
    k.panah(P + 125, 1355, A - 135 - 2, 1355)
    k.isi.append(f'<circle cx="{A}" cy="1425" r="13" fill="none" stroke="{ASPAL}" stroke-width="2"/><circle cx="{A}" cy="1425" r="8" fill="{ASPAL}"/>')
    k.panah(A, 1355 + h6, A, 1410)
    k.garis([(P - 22, 1275), (70, 1275), (70, 1425), (A - 15, 1425)])
    jaga(78, 1266, "[tidak]")
    return k


def ke_png(berkas: list[Path]) -> None:
    kode = """
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chromium")
    p = b.new_page(device_scale_factor=2)
    for f in sys.argv[1:]:
        p.goto("file:///" + f.replace("\\\\", "/"))
        el = p.locator("svg")
        kotak = el.bounding_box()
        p.set_viewport_size({"width": int(kotak["width"]), "height": int(kotak["height"])})
        el.screenshot(path=f.replace(".svg", ".png"))
        print("png", f)
    b.close()
"""
    subprocess.run([sys.executable, "-c", kode, *[str(f) for f in berkas]], check=True)


def main() -> None:
    pilih = set(sys.argv[1:])
    semua = {
        "kerangka-berpikir": kerangka,
        "alur-praproses": alur_praproses,
        "waterfall": waterfall,
        "use-case": use_case_v5,
        "class-diagram": class_diagram_v5,
        "sequence-v5": sequence_v5,
        "activity-v5": activity_v5,
        # diagram v4 (web Next.js) tetap dibuat untuk bab riwayat versi
        "use-case-v4": use_case,
        "class-diagram-v4": class_diagram,
        "sequence-prediksi": sequence,
        "activity-massal": activity,
    }
    berkas = []
    for nama, fungsi in semua.items():
        if pilih and nama not in pilih:
            continue
        berkas.append(fungsi().simpan(f"{nama}.svg"))
        print("svg", nama)
    try:
        ke_png(berkas)
    except Exception as e:  # PNG hanya untuk dokumen Word, bukan syarat
        print("PNG dilewati:", e)


if __name__ == "__main__":
    main()
