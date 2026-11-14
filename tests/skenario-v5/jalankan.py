"""Pengujian skenario (black box) Suara Rakyat v5 (Streamlit) lewat browser sungguhan.

Berbeda dengan tes AppTest di streamlit-app/tests yang memakai sumber palsu, skenario di sini
memakai Google Play asli, jadi jumlah ulasan berubah tiap hari. Kode kebutuhan merujuk ke
docs/kebutuhan-pengguna-v5.md. Hasil disimpan apa adanya, lulus atau gagal, ke
tests/skenario-v5/hasil-<nama>.json dan HASIL-<nama>.md.

Pakai:
  python tests/skenario-v5/jalankan.py http://localhost:8531 lokal
  python tests/skenario-v5/jalankan.py https://<app>.streamlit.app live
"""

from __future__ import annotations

import csv
import io
import json
import platform
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8531"
NAMA = sys.argv[2] if len(sys.argv) > 2 else "lokal"
DESKTOP = {"width": 1366, "height": 900}
TUNGGU = 180_000  # pengambilan ulasan dari Google Play bisa makan puluhan detik
HARI_INI = datetime.now(timezone(timedelta(hours=7))).date()

SKENARIO: list[dict] = [
    dict(id="SV-01", fitur="Input", kebutuhan="FR5-01, FR5-02", skenario="Membuka halaman", langkah="Buka app", data="-", harapan="Judul tampil, pilihan berisi 6 aplikasi dan Aplikasi lain, rentang bawaan 7 hari sampai hari ini"),
    dict(id="SV-02", fitur="Input", kebutuhan="FR5-02", skenario="Start date setelah end date", langkah="Isi start date hari ini dan end date 3 hari lalu, tekan Ambil", data="start hari ini, end 3 hari lalu", harapan="Pesan galat tentang start date muncul dan tidak ada ulasan yang diambil"),
    dict(id="SV-03", fitur="Input", kebutuhan="FR5-01", skenario="Application ID tidak valid", langkah="Pilih Aplikasi lain, isi teks bebas, tekan Ambil", data="bukan id", harapan="Pesan galat meminta application ID yang valid"),
    dict(id="SV-04", fitur="Input", kebutuhan="FR5-01, NFR5-06", skenario="Application ID yang tidak ada di Google Play", langkah="Pilih Aplikasi lain, isi com.suararakyat.tidakada, tekan Ambil", data="com.suararakyat.tidakada", harapan="Pesan aplikasi tidak ditemukan"),
    dict(id="SV-05", fitur="Input", kebutuhan="FR5-01", skenario="Menempel link Google Play utuh", langkah="Pilih Aplikasi lain, tempel link Access by KAI, tekan Ambil", data="https://play.google.com/store/apps/details?id=com.kai.kaiticketing&hl=id", harapan="Dashboard Access by KAI tampil"),
    dict(id="SV-06", fitur="Dashboard", kebutuhan="FR5-03, FR5-04, FR5-05", skenario="Pantau Mobile JKN 7 hari terakhir", langkah="Pilih Mobile JKN, rentang bawaan, tekan Ambil", data="app.bpjs.mobile, 7 hari", harapan="Empat angka tampil, persen tiga nada berjumlah sekitar 100%, kecocokan dengan bintang ditampilkan"),
    dict(id="SV-07", fitur="Dashboard", kebutuhan="FR5-06, FR5-07", skenario="Grafik tren dan kata penentu", langkah="Setelah SV-06, lihat bagian tren dan kata penentu", data="hasil SV-06", harapan="Satu grafik tren dan dua grafik kata penentu tampil"),
    dict(id="SV-08", fitur="Daftar ulasan", kebutuhan="FR5-08", skenario="Saring daftar per nada", langkah="Setelah SV-06, pilih Negatif lalu Positif", data="hasil SV-06", harapan="Jumlah baris daftar sama dengan jumlah ulasan nada itu di ringkasan"),
    dict(id="SV-09", fitur="Daftar ulasan", kebutuhan="FR5-08", skenario="Urutkan daftar", langkah="Setelah SV-06, ganti urutan ke Paling banyak disukai", data="hasil SV-06", harapan="Daftar tetap tampil tanpa galat dan jumlah baris tidak berubah"),
    dict(id="SV-10", fitur="Unduh", kebutuhan="FR5-09, NFR5-04", skenario="Unduh hasil CSV", langkah="Setelah SV-06, tekan Unduh semua hasil (CSV)", data="hasil SV-06", harapan="CSV terunduh, kolomnya tanggal, bintang, nada, keyakinan, disukai, dibalas, ulasan, tanpa nama pengulas, jumlah baris sama dengan ulasan yang diambil"),
    dict(id="SV-11", fitur="Dashboard", kebutuhan="FR5-06", skenario="Rentang panjang memakai tren mingguan", langkah="Pilih Info BMKG, start date 1 Januari 2026, tekan Ambil", data="com.Info_BMKG, 1 Jan 2026 sampai hari ini", harapan="Dashboard tampil dengan grafik tren (per minggu karena rentang lebih dari 62 hari)"),
    dict(id="SV-12", fitur="Pengambilan", kebutuhan="FR5-03", skenario="Aplikasi ramai melewati batas 10.000 ulasan", langkah="Pilih JMO, rentang 90 hari, tekan Ambil", data="com.bpjstku, 90 hari", harapan="Peringatan batas 10.000 ulasan muncul dan dashboard tetap tampil"),
    dict(id="SV-13", fitur="Tampilan", kebutuhan="NFR5-01", skenario="Dibuka di layar HP", langkah="Buka app di lebar 390 px", data="-", harapan="Tidak ada bagian yang perlu digeser ke samping"),
    dict(id="SV-14", fitur="Kecepatan", kebutuhan="NFR5-02", skenario="Waktu tunggu pantau 7 hari", langkah="Ukur waktu dari tekan Ambil sampai angka ringkasan tampil di SV-06", data="app.bpjs.mobile, 7 hari", harapan="Di bawah 30 detik"),
]


def buka(page: Page) -> None:
    page.goto(URL, wait_until="domcontentloaded")
    page.get_by_role("button", name="Ambil dan baca ulasan").wait_for(timeout=TUNGGU)


def pilih_aplikasi(page: Page, nama: str) -> None:
    page.locator('[data-testid="stSelectbox"]').first.click()
    page.get_by_role("option", name=nama).click()
    page.wait_for_timeout(1500)


def isi_tanggal(page: Page, urutan: int, tgl: date) -> None:
    # kolom tanggal Streamlit memakai input bermasker, jadi harus diketik per huruf.
    # Ketikan bisa hilang kalau halaman sedang memuat ulang, jadi hasilnya dicek dan diulang.
    teks = tgl.strftime("%d/%m/%Y")
    kotak = page.locator('[data-testid="stDateInputField"]').nth(urutan)
    for _ in range(3):
        page.wait_for_timeout(800)
        kotak.click()
        page.keyboard.press("End")
        for _ in range(12):
            page.keyboard.press("Backspace")
        page.keyboard.type(teks, delay=60)
        page.keyboard.press("Enter")
        page.keyboard.press("Escape")
        page.wait_for_timeout(1200)
        if kotak.input_value() == teks:
            return
    raise AssertionError(f"tanggal {teks} gagal diisi, kolom berisi {kotak.input_value()}")


def ambil(page: Page) -> float:
    t0 = time.perf_counter()
    page.get_by_role("button", name="Ambil dan baca ulasan").click()
    page.locator('[data-testid="stMetric"]:visible, [data-testid="stAlertContentError"]:visible, [data-testid="stAlertContentInfo"]:visible').first.wait_for(timeout=TUNGGU)
    page.wait_for_timeout(1500)
    return time.perf_counter() - t0


def galat(page: Page) -> str:
    return " | ".join(page.locator('[data-testid="stAlertContentError"]').all_inner_texts())


def metrik(page: Page) -> dict[str, str]:
    out = {}
    for teks in page.locator('[data-testid="stMetric"]').all_inner_texts():
        bagian = [b for b in teks.split("\n") if b.strip()]
        out[bagian[0]] = bagian[-1]
    return out


def angka(s: str) -> float:
    return float(s.replace(".", "").replace(",", ".").replace("%", ""))


def jumlah_daftar(page: Page) -> int:
    teks = [t for t in page.locator('[data-testid="stCaptionContainer"]').all_inner_texts() if re.fullmatch(r"[\d.]+ ulasan", t.strip())]
    return int(teks[-1].split()[0].replace(".", ""))


def nada(page: Page, label: str) -> None:
    page.locator('[data-testid="stRadio"] label', has_text=label).click()
    page.wait_for_timeout(1500)


def jalankan() -> list[dict]:
    hasil = {s["id"]: dict(s, hasil="", status="") for s in SKENARIO}

    def catat(kode: str, lulus: bool, teks: str) -> None:
        hasil[kode].update(status="LULUS" if lulus else "GAGAL", hasil=teks)
        print(f"{kode} {'LULUS' if lulus else 'GAGAL'}: {teks}")

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport=DESKTOP, accept_downloads=True)
        page = ctx.new_page()

        buka(page)
        page.locator('[data-testid="stSelectbox"]').first.click()
        opsi = page.get_by_role("option").all_inner_texts()
        page.keyboard.press("Escape")
        tgl = [page.locator('[data-testid="stDateInputField"]').nth(i).input_value() for i in range(2)]
        judul = page.get_by_role("heading", name="Suara Rakyat").count() > 0
        harap_tgl = [(HARI_INI - timedelta(days=6)).strftime("%d/%m/%Y"), HARI_INI.strftime("%d/%m/%Y")]
        catat("SV-01", judul and len(opsi) == 7 and tgl == harap_tgl, f"judul tampil: {judul}, {len(opsi)} pilihan, rentang {tgl[0]} sampai {tgl[1]}")

        buka(page)
        isi_tanggal(page, 0, HARI_INI)
        isi_tanggal(page, 1, HARI_INI - timedelta(days=3))
        page.get_by_role("button", name="Ambil dan baca ulasan").click()
        try:
            page.locator('[data-testid="stAlertContentError"]').first.wait_for(timeout=15000)
        except Exception:
            pass
        g = galat(page)
        catat("SV-02", "Start date" in g and page.locator('[data-testid="stMetric"]').count() == 0, f"pesan: {g or '(tidak ada)'}")

        for kode, isian, kunci in (("SV-03", "bukan id", "application ID yang valid"), ("SV-04", "com.suararakyat.tidakada", "tidak ditemukan")):
            buka(page)
            pilih_aplikasi(page, "Aplikasi lain (isi application ID)")
            page.get_by_role("textbox", name="Application ID").fill(isian)
            page.get_by_role("textbox", name="Application ID").press("Enter")
            page.wait_for_timeout(800)
            ambil(page)
            g = galat(page)
            catat(kode, kunci in g, f"pesan: {g or '(tidak ada)'}")

        buka(page)
        pilih_aplikasi(page, "Aplikasi lain (isi application ID)")
        link = "https://play.google.com/store/apps/details?id=com.kai.kaiticketing&hl=id"
        page.get_by_role("textbox", name="Application ID").fill(link)
        page.get_by_role("textbox", name="Application ID").press("Enter")
        page.wait_for_timeout(800)
        ambil(page)
        sub = page.locator('[data-testid="stHeading"]').all_inner_texts()
        catat("SV-05", any("Access by KAI" in s for s in sub) and not galat(page), f"judul dashboard: {[s for s in sub if 'KAI' in s] or sub[-1:]}")

        buka(page)
        pilih_aplikasi(page, "Mobile JKN (BPJS Kesehatan)")
        detik = ambil(page)
        m = metrik(page)
        total_persen = sum(angka(m.get(k, "0")) for k in ("Negatif", "Netral", "Positif"))
        cocok = [t for t in page.locator('[data-testid="stCaptionContainer"]').all_inner_texts() if "sama dengan nada dari bintang" in t]
        catat("SV-06", len(m) == 4 and abs(total_persen - 100) < 0.5 and bool(cocok), f"{m}, jumlah persen {total_persen:.1f}, {cocok[0][:70] if cocok else 'kecocokan tidak tampil'}")
        catat("SV-14", detik < 30, f"{detik:.1f} detik untuk {m.get('Ulasan dibaca', '?')} ulasan")

        grafik = page.locator('[data-testid="stVegaLiteChart"]').count()
        catat("SV-07", grafik == 3, f"{grafik} grafik tampil (1 tren + 2 kata penentu)")

        caps = [t for t in page.locator('[data-testid="stCaptionContainer"]').all_inner_texts() if re.fullmatch(r"[\d.]+ ulasan", t.strip())]
        per_nada = dict(zip(["Negatif", "Netral", "Positif"], [int(c.split()[0].replace(".", "")) for c in caps[:3]]))
        cek = []
        for lab in ("Positif", "Negatif"):
            nada(page, lab)
            cek.append((lab, jumlah_daftar(page), per_nada[lab]))
        catat("SV-08", all(a == b for _, a, b in cek), "; ".join(f"{lab}: daftar {a}, ringkasan {b}" for lab, a, b in cek))

        sebelum = jumlah_daftar(page)
        page.locator('[data-testid="stSelectbox"]').nth(1).click()
        page.get_by_role("option", name="Paling banyak disukai").click()
        page.wait_for_timeout(1500)
        catat("SV-09", jumlah_daftar(page) == sebelum and page.locator('[data-testid="stException"]').count() == 0, f"baris sebelum {sebelum}, sesudah {jumlah_daftar(page)}")

        with page.expect_download() as unduh:
            page.get_by_role("button", name="Unduh semua hasil (CSV)").click()
        isi = Path(unduh.value.path()).read_text(encoding="utf-8-sig")
        baris = list(csv.reader(io.StringIO(isi)))
        kepala = baris[0]
        dibaca = int(m["Ulasan dibaca"].replace(".", ""))
        tak = sum(1 for r in baris[1:] if r[2] == "Tidak terbaca")
        ok = kepala == ["tanggal", "bintang", "nada", "keyakinan", "disukai", "dibalas", "ulasan"] and len(baris) - 1 == dibaca + tak
        catat("SV-10", ok, f"{unduh.value.suggested_filename}, kolom {kepala}, {len(baris) - 1} baris data")

        buka(page)
        pilih_aplikasi(page, "Info BMKG (BMKG)")
        isi_tanggal(page, 0, date(2026, 1, 1))
        ambil(page)
        m = metrik(page)
        grafik = page.locator('[data-testid="stVegaLiteChart"]').count()
        catat("SV-11", "Ulasan dibaca" in m and grafik >= 1, f"{m.get('Ulasan dibaca', '?')} ulasan dibaca, {grafik} grafik")

        buka(page)
        pilih_aplikasi(page, "JMO (BPJS Ketenagakerjaan)")
        isi_tanggal(page, 0, HARI_INI - timedelta(days=89))
        ambil(page)
        w = " | ".join(page.locator('[data-testid="stAlertContentWarning"]').all_inner_texts())
        m = metrik(page)
        catat("SV-12", "dibatasi" in w and "Ulasan dibaca" in m, f"peringatan: {w[:110] or '(tidak ada)'}, {m.get('Ulasan dibaca', '?')} ulasan dibaca")

        hp = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        ph = hp.new_page()
        buka(ph)
        lebar = ph.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
        catat("SV-13", lebar[0] <= lebar[1], f"lebar isi {lebar[0]} px, lebar layar {lebar[1]} px")
        b.close()
    return list(hasil.values())


def simpan(hasil: list[dict]) -> None:
    lulus = sum(h["status"] == "LULUS" for h in hasil)
    meta = {"url": URL, "waktu": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(), "lulus": lulus, "total": len(hasil)}
    (HERE / f"hasil-{NAMA}.json").write_text(json.dumps({"meta": meta, "skenario": hasil}, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Hasil pengujian skenario v5 ({NAMA})", "", f"URL: {URL}. Waktu: {meta['waktu']} UTC. Lulus {lulus} dari {len(hasil)}.", "",
          "| Kode | Kebutuhan | Skenario | Data uji | Hasil yang diharapkan | Hasil sebenarnya | Status |", "|---|---|---|---|---|---|---|"]
    for h in hasil:
        sel = [h["id"], h["kebutuhan"], h["skenario"], h["data"], h["harapan"], h["hasil"], h["status"]]
        md.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in sel) + " |")
    (HERE / f"HASIL-{NAMA}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n{lulus} dari {len(hasil)} lulus, disimpan ke {HERE}")


if __name__ == "__main__":
    simpan(jalankan())
