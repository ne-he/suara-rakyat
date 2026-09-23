"""Gambar diagram untuk laporan: kerangka berpikir, use case, class diagram, dan sequence.

Semua digambar dari kode supaya mudah diperbarui kalau arsitekturnya berubah, dan supaya
warnanya sama dengan web. Hasilnya SVG (untuk web dan slide) plus PNG (untuk dokumen Word).

Jalankan: python docs/diagram/buat_diagram.py
PNG dibuat lewat Chromium Playwright. Kalau Playwright tidak ada, SVG tetap dibuat.
"""

from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MERAH = "#ce1126"
MERAH_TUA = "#8e0c1a"
ASPAL = "#141210"
ABU = "#6f675c"
KERTAS = "#efe7d6"
PUTIH = "#f6f1e7"
GARIS = "#d9ceb8"
FONT = "Plus Jakarta Sans, Segoe UI, Arial, sans-serif"


class Kanvas:
    def __init__(self, w: int, h: int, judul: str) -> None:
        self.w, self.h, self.judul = w, h, judul
        self.isi: list[str] = []

    def teks(self, x: float, y: float, s: str, ukuran: int = 13, warna: str = ASPAL, tebal: int = 400, anchor: str = "middle", miring: bool = False) -> None:
        gaya = f' font-style="italic"' if miring else ""
        self.isi.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-size="{ukuran}" font-weight="{tebal}" fill="{warna}"{gaya}>{html.escape(s)}</text>'
        )

    def baris_teks(self, x: float, y: float, baris: list[str], ukuran: int = 13, warna: str = ASPAL, tebal: int = 400, jarak: float = 15, anchor: str = "middle") -> None:
        for i, s in enumerate(baris):
            self.teks(x, y + i * jarak, s, ukuran, warna, tebal, anchor)

    def kotak(self, x: float, y: float, w: float, h: float, baris: list[str], isi: str = PUTIH, garis: str = ASPAL, tebal_garis: float = 2, r: float = 6, ukuran: int = 13, tebal: int = 500, judul: str | None = None) -> None:
        self.isi.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{isi}" stroke="{garis}" stroke-width="{tebal_garis}"/>')
        atas = y + h / 2 - (len(baris) - 1) * 8 + 4
        if judul:
            self.teks(x + w / 2, y + 20, judul, ukuran + 1, MERAH_TUA, 700)
            atas = y + 42
        self.baris_teks(x + w / 2, atas, baris, ukuran, ASPAL, tebal, 16)

    def elips(self, cx: float, cy: float, rx: float, ry: float, baris: list[str], isi: str = PUTIH, garis: str = ASPAL) -> None:
        self.isi.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{isi}" stroke="{garis}" stroke-width="2"/>')
        self.baris_teks(cx, cy - (len(baris) - 1) * 7 + 4, baris, 12.5, ASPAL, 500, 14)

    def aktor(self, x: float, y: float, nama: list[str]) -> None:
        g = f'stroke="{ASPAL}" stroke-width="2" fill="none"'
        self.isi.append(f'<circle cx="{x}" cy="{y}" r="9" {g}/>')
        self.isi.append(f'<path d="M{x},{y + 9}V{y + 33}M{x - 13},{y + 18}H{x + 13}M{x},{y + 33}L{x - 11},{y + 50}M{x},{y + 33}L{x + 11},{y + 50}" {g}/>')
        self.baris_teks(x, y + 66, nama, 12.5, ASPAL, 600, 14)

    def panah(self, x1: float, y1: float, x2: float, y2: float, label: str | None = None, putus: bool = False, warna: str = ASPAL, kepala: str = "penuh", geser: float = 0) -> None:
        dash = ' stroke-dasharray="6 4"' if putus else ""
        ujung = {"penuh": "url(#panah)", "garis": "url(#panah-garis)", "tidak": "none"}[kepala]
        self.isi.append(f'<path d="M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}" stroke="{warna}" stroke-width="1.8" fill="none"{dash} marker-end="{ujung}"/>')
        if label:
            self.teks((x1 + x2) / 2 + geser, (y1 + y2) / 2 - 6, label, 11.5, ABU, 600)

    def siku(self, titik: list[tuple[float, float]], label: str | None = None, putus: bool = False) -> None:
        d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in titik)
        dash = ' stroke-dasharray="6 4"' if putus else ""
        self.isi.append(f'<path d="{d}" stroke="{ASPAL}" stroke-width="1.8" fill="none"{dash} marker-end="url(#panah)"/>')
        if label:
            x1, y1 = titik[0]
            x2, y2 = titik[1]
            self.teks((x1 + x2) / 2, (y1 + y2) / 2 - 7, label, 11.5, ABU, 600)

    def belah(self, cx: float, cy: float, w: float, h: float, baris: list[str]) -> None:
        self.isi.append(f'<path d="M{cx},{cy - h / 2}L{cx + w / 2},{cy}L{cx},{cy + h / 2}L{cx - w / 2},{cy}Z" fill="{KERTAS}" stroke="{ASPAL}" stroke-width="2"/>')
        self.baris_teks(cx, cy - (len(baris) - 1) * 7 + 4, baris, 12, ASPAL, 600, 14)

    def bingkai(self, x: float, y: float, w: float, h: float, nama: str) -> None:
        self.isi.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="{MERAH}" stroke-width="2" stroke-dasharray="8 5"/>')
        self.teks(x + 14, y + 22, nama, 14, MERAH_TUA, 700, anchor="start")

    def simpan(self, nama: str) -> Path:
        kepala = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{html.escape(self.judul)}">'
            f"<defs>"
            f'<marker id="panah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10Z" fill="{ASPAL}"/></marker>'
            f'<marker id="panah-garis" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0L10,5L0,10" fill="none" stroke="{ASPAL}" stroke-width="1.6"/></marker>'
            f"</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="{PUTIH}"/>'
        )
        f = HERE / nama
        f.write_text(kepala + "".join(self.isi) + "</svg>", encoding="utf-8", newline="\n")
        return f


def kerangka() -> Kanvas:
    k = Kanvas(880, 1430, "Kerangka berpikir Suara Rakyat")
    k.teks(440, 38, "Kerangka berpikir", 21, ASPAL, 800)
    k.teks(440, 62, "dari keluhan warga sampai simpulan laporan", 13, ABU, 500)

    x, w, h, jarak = 130, 470, 66, 96
    langkah = [
        ["Masalah: keluhan warga tersebar di kolom ulasan,", "tidak mungkin dibaca satu per satu"],
        ["Data IGAR: 617.722 ulasan, 6 aplikasi layanan publik,", "label diturunkan dari bintang"],
        ["Audit dan pembersihan: teks kembar digabung,", "tersisa 361.287 teks unik"],
        ["Pembagian data dengan hash teks:", "80 persen latih, 10 validasi, 10 uji"],
        ["Fitur TF-IDF kata 1-2 gram dan karakter 2-5 gram,", "plus kamus slang Indonesia"],
        ["Latih 30 konfigurasi: SVM, Logistic Regression, Naive", "Bayes, Ridge, SGD, LightGBM, IndoBERTweet"],
        ["Pilih model di data validasi,", "lalu geser ambang tiap kelas"],
        ["Uji di data test: macro-F1, presisi, recall,", "dan selang kepercayaan bootstrap 1.000 kali"],
    ]
    lanjut = [
        ["Ekspor bobot ke TypeScript,", "diuji sama persis di 3.018 teks"],
        ["Produk web: baca satu ulasan, cek massal,", "dashboard bukti, tren keluhan"],
        ["Evaluasi subjektif (kuesioner SUS) dan objektif", "(paper IGAR, VADER, uji bahasa, anotasi manusia)"],
        ["Simpulan dan saran"],
    ]
    y0 = 96
    for i, baris in enumerate(langkah):
        y = y0 + i * jarak
        k.kotak(x, y, w, h, baris, isi=KERTAS if i < 2 else PUTIH)
        if i < len(langkah) - 1:
            k.panah(x + w / 2, y + h, x + w / 2, y + jarak - 2)

    y_belah = y0 + len(langkah) * jarak + 44
    k.belah(x + w / 2, y_belah, 250, 96, ["cukup akurat dan cukup cepat?"])
    k.panah(x + w / 2, y0 + (len(langkah) - 1) * jarak + h, x + w / 2, y_belah - 48)
    k.siku(
        [(x + w / 2 + 125, y_belah), (800, y_belah), (800, y0 + 5 * jarak + h / 2), (x + w + 2, y0 + 5 * jarak + h / 2)],
        None,
    )
    k.teks(690, y_belah - 10, "belum", 12, ABU, 700)
    k.teks(798, y0 + 5 * jarak - 26, "ulangi dengan setelan lain", 11.5, ABU, 600, anchor="end")

    y1 = y_belah + 66
    for i, baris in enumerate(lanjut):
        y = y1 + i * jarak
        k.kotak(x, y, w, h, baris, isi=KERTAS if i >= len(lanjut) - 2 else PUTIH)
        if i < len(lanjut) - 1:
            k.panah(x + w / 2, y + h, x + w / 2, y + jarak - 2)
    k.panah(x + w / 2, y_belah + 48, x + w / 2, y1 - 2, "sudah", geser=36)
    return k


def use_case() -> Kanvas:
    k = Kanvas(1240, 820, "Use case diagram Suara Rakyat")
    k.teks(620, 36, "Use case diagram", 21, ASPAL, 800)
    k.bingkai(260, 70, 640, 660, "Suara Rakyat")

    k.aktor(140, 330, ["Warga", "pengunjung"])
    k.aktor(1080, 220, ["Tim", "peneliti"])
    k.aktor(1080, 600, ["Server", "IndoBERTweet"])

    kiri = [
        (420, 145, ["Baca nada", "satu ulasan"]),
        (420, 250, ["Bandingkan", "jawaban model"]),
        (420, 355, ["Cek massal", "dari berkas CSV"]),
        (420, 460, ["Lihat dashboard", "bukti model"]),
        (420, 565, ["Lihat tren", "keluhan"]),
        (420, 670, ["Isi kuesioner", "SUS"]),
    ]
    kanan = [
        (760, 145, ["Latih dan pilih", "model"]),
        (760, 250, ["Ekspor model", "ke web"]),
        (760, 355, ["Anotasi ulang", "300 ulasan"]),
        (760, 460, ["Rekap jawaban", "kuesioner"]),
    ]
    for cx, cy, baris in kiri:
        k.elips(cx, cy, 92, 36, baris)
        k.panah(176, 348, cx - 92, cy, kepala="tidak")
    for cx, cy, baris in kanan:
        k.elips(cx, cy, 92, 36, baris, isi=KERTAS)
        k.panah(1044, 240, cx + 92, cy, kepala="tidak")

    k.elips(760, 570, 92, 36, ["Unduh hasil"], isi=KERTAS)
    k.elips(760, 675, 92, 36, ["Baca dengan", "model besar"], isi=KERTAS)
    k.panah(1044, 618, 852, 675, kepala="tidak")
    k.panah(512, 355, 666, 552, None, putus=True, kepala="garis")
    k.teks(566, 404, "«extend»", 11.5, ABU, 600, anchor="start")
    k.panah(504, 176, 668, 655, None, putus=True, kepala="garis")
    k.teks(556, 292, "«include»", 11.5, ABU, 600, anchor="start")
    k.teks(620, 786, "Notasi UML: «include» selalu ikut dijalankan, «extend» hanya kalau pengunjung memilihnya", 11.5, ABU, 500)
    return k


def class_diagram() -> Kanvas:
    k = Kanvas(1240, 820, "Class diagram Suara Rakyat")
    k.teks(620, 36, "Class diagram", 21, ASPAL, 800)
    k.teks(620, 58, "bagian yang berjalan saat ada pengunjung", 13, ABU, 500)

    k.bingkai(30, 80, 790, 700, "web (Next.js, TypeScript)")
    k.bingkai(850, 80, 360, 300, "indobert-api (Python)")
    k.bingkai(850, 420, 360, 360, "ml (Python, di luar waktu jalan)")

    def kelas(x, y, w, nama, atribut, metode, isi=PUTIH):
        tinggi = 34 + max(len(atribut), 1) * 16 + 8 + len(metode) * 16 + 10
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

    kelas(55, 115, 225, "PredictRoute", ["+ maxDuration"], ["+ POST(req): Response"])
    kelas(300, 115, 225, "BatchRoute", ["+ MAX_TEKS = 1000"], ["+ POST(req): Response"])
    kelas(545, 115, 250, "IndobertProxyRoute", ["- url, key: string"], ["+ POST(req): Response"])
    kelas(55, 250, 290, "RateLimiter", ["- ember: Map<string, number[]>"], ["+ lewat(kunci, batas, jendela)"])
    kelas(400, 250, 340, "ModelStore  «singleton»", ["- meta: ModelMeta", "- coef: Map<string, Float32Array>"], ["+ loadModels(): Loaded", "+ predictOne(teks, id): Prediction", "+ predictAll(teks): Prediction[]"], isi=KERTAS)
    kelas(55, 430, 290, "ModelInfo", ["+ id, name, features", "+ bias: number[]", "+ temperature: number", "+ metrics: Metrics"], [])
    kelas(400, 430, 340, "TextNorm", ["- slang: Record<string, string>"], ["+ normalize(teks), tokens(teks)", "+ wordNgrams(tok), charNgrams(tok)"])
    kelas(55, 620, 290, "ModelMeta", ["+ labels: Label[]", "+ models: ModelInfo[]", "+ n_word, n_char"], [])
    kelas(400, 620, 340, "Prediction", ["+ label: Label", "+ probs: Record<Label, number>", "+ tokens: TokenContribution[]"], [])

    kelas(870, 120, 320, "IndoBertServer", ["- session: InferenceSession", "- tokenizer: Tokenizer", "- bias, temperature"], ["+ prep(teks): str", "+ probs_of(teks[]): ndarray"], isi=KERTAS)
    kelas(870, 450, 320, "PipelineML", ["+ langkah 01 sampai 15"], ["+ siapkan(), fitur(), latih()", "+ pilih(), ekspor()"])
    kelas(870, 640, 320, "SuaraML.TextNorm", ["- slang_id.json"], ["+ normalize(), tokens()"])

    k.panah(167, 196, 167, 248, "memeriksa", geser=54)
    k.panah(280, 176, 400, 280, "memakai", geser=-6)
    k.panah(500, 196, 500, 248, "memakai", geser=-44)
    k.panah(570, 386, 570, 428, "memakai", geser=44)
    k.panah(400, 330, 348, 432, "berisi", geser=-26)
    k.panah(200, 618, 200, 556, "punya banyak", geser=62, kepala="garis")
    k.siku([(740, 340), (800, 340), (800, 662), (744, 662)], None, putus=True)
    k.teks(796, 512, "menghasilkan", 11.5, ABU, 600, anchor="end")
    k.panah(797, 160, 866, 160, "HTTP JSON", putus=True)
    k.panah(866, 496, 744, 332, "berkas model", putus=True, geser=56)
    k.panah(1030, 446, 1030, 386, "melatih", putus=True, geser=42)
    k.panah(866, 676, 744, 524, "paritas diuji", putus=True, geser=28)
    return k


def sequence() -> Kanvas:
    k = Kanvas(1240, 780, "Sequence diagram prediksi satu ulasan")
    k.teks(620, 34, "Sequence diagram: satu ulasan dibaca", 20, ASPAL, 800)

    peserta = [(110, ["Pengunjung"]), (330, ["Halaman web", "(Analyzer)"]), (570, ["/api/predict"]), (790, ["ModelStore"]), (1010, ["Server", "IndoBERTweet"])]
    for x, nama in peserta:
        k.kotak(x - 85, 58, 170, 50, nama, isi=KERTAS)
        k.isi.append(f'<path d="M{x},108V712" stroke="{ABU}" stroke-width="1.4" stroke-dasharray="5 5"/>')

    def pesan(y, x1, x2, teks, balas=False):
        k.panah(x1, y, x2, y, None, putus=balas, kepala="garis" if balas else "penuh")
        k.teks((x1 + x2) / 2, y - 8, teks, 11.5, ASPAL, 600)

    def aktif(x, y1, y2):
        k.isi.append(f'<rect x="{x - 6}" y="{y1}" width="12" height="{y2 - y1}" fill="{PUTIH}" stroke="{ASPAL}" stroke-width="1.5"/>')

    def catatan(x, y, w, baris):
        k.kotak(x, y, w, 18 + len(baris) * 15, baris, isi=KERTAS, r=4, ukuran=11, tebal=500)

    pesan(148, 110, 330, "tulis ulasan, pilih model")
    aktif(330, 148, 330)
    pesan(184, 330, 570, "POST /api/predict")
    aktif(570, 184, 306)
    catatan(600, 200, 156, ["cek pembatas laju"])
    pesan(256, 570, 790, "predictAll(teks)")
    aktif(790, 256, 282)
    catatan(828, 196, 182, ["normalisasi, TF-IDF,", "skor kelas, geser bias"])
    pesan(282, 790, 570, "Prediction", balas=True)
    pesan(306, 570, 330, "{label, probs, kata penentu}", balas=True)
    pesan(332, 330, 110, "stempel hasil dan kata penentu", balas=True)

    k.isi.append(f'<rect x="60" y="380" width="1120" height="290" rx="8" fill="none" stroke="{MERAH}" stroke-width="1.6"/>')
    k.isi.append(f'<path d="M60,380H176V408H60Z" fill="{MERAH}"/>')
    k.teks(118, 399, "opsional", 12, PUTIH, 700)
    k.teks(196, 399, "kalau pengunjung memilih IndoBERTweet dan alamat servernya sudah diisi", 11.5, ABU, 600, anchor="start")

    pesan(452, 330, 570, "POST /api/predict-indobert")
    aktif(330, 452, 622)
    aktif(570, 452, 592)
    pesan(502, 570, 1010, "POST /predict, header x-suara-key")
    aktif(1010, 502, 572)
    catatan(1042, 510, 152, ["onnxruntime int8", "dan occlusion"])
    pesan(572, 1010, 570, "{label, probs, tokens, ms}", balas=True)
    pesan(592, 570, 330, "kartu model keempat", balas=True)
    pesan(622, 330, 110, "tampilkan hasil server", balas=True)
    k.teks(620, 742, "Teks yang dikirim tidak disimpan. Kalau server mati, tiga model linear tetap menjawab.", 11.5, ABU, 500)
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
    berkas = [
        kerangka().simpan("kerangka-berpikir.svg"),
        use_case().simpan("use-case.svg"),
        class_diagram().simpan("class-diagram.svg"),
        sequence().simpan("sequence-prediksi.svg"),
    ]
    for f in berkas:
        print("svg", f.name)
    try:
        ke_png(berkas)
    except Exception as e:  # PNG hanya untuk dokumen Word, bukan syarat
        print("PNG dilewati:", e)


if __name__ == "__main__":
    main()
