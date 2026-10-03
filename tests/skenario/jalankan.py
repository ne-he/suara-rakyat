"""Pengujian skenario (black box) Suara Rakyat lewat browser sungguhan.

Setiap skenario punya kode, kebutuhan yang diuji (lihat docs/kebutuhan-pengguna.md), langkah,
data uji, dan hasil yang diharapkan. Hasil yang benar-benar terjadi dicatat apa adanya, lulus
atau gagal, lalu disimpan ke tests/skenario/hasil-<nama>.json dan HASIL-<nama>.md.

Pakai:
  python tests/skenario/jalankan.py                       # web live
  python tests/skenario/jalankan.py http://localhost:3130 lokal

Butuh: pip install playwright, lalu python -m playwright install chromium.
Skenario pembatas laju sengaja dijalankan paling akhir karena membuat alamat IP penguji
ditolak selama satu menit.
"""

from __future__ import annotations

import json
import platform
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

HERE = Path(__file__).resolve().parent
URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://suara-rakyat-xi.vercel.app"
NAMA = sys.argv[2] if len(sys.argv) > 2 else "live"
DESKTOP = {"width": 1366, "height": 800}

KELUHAN = "Sudah 3 hari tidak bisa login, kode OTP tidak pernah masuk. Tolong diperbaiki."
PUJIAN = "Pesan tiket jadi gampang, tidak perlu antre lagi. Mantap, terima kasih!"
GAUL = "aplikasinya gk bs dibuka, ngelag trs, udh update tetep error"

SKENARIO: list[dict] = [
    # fitur 1: baca satu ulasan
    dict(id="SK-01", fitur="Baca satu ulasan", kebutuhan="FR-01, FR-02", skenario="Ulasan berisi keluhan jelas", langkah="Tulis ulasan di formulir halaman depan, tekan Baca nadanya", data=KELUHAN, harapan="Stempel Negatif muncul beserta tingkat keyakinan dan tiga batang peluang"),
    dict(id="SK-02", fitur="Baca satu ulasan", kebutuhan="FR-01, FR-02", skenario="Ulasan berisi pujian jelas", langkah="Tulis ulasan, tekan Baca nadanya", data=PUJIAN, harapan="Stempel Positif muncul"),
    dict(id="SK-03", fitur="Baca satu ulasan", kebutuhan="FR-01", skenario="Formulir dikirim kosong", langkah="Kosongkan formulir, tekan Baca nadanya", data="(kosong)", harapan="Pesan 'Tulis atau tempel ulasanmu dulu.' muncul dan tidak ada permintaan ke server"),
    dict(id="SK-04", fitur="Baca satu ulasan", kebutuhan="FR-01", skenario="Ulasan lebih dari 2.000 karakter", langkah="Ketik 2.050 karakter ke formulir", data="huruf a sebanyak 2.050", harapan="Formulir berhenti menerima ketikan di 2.000 karakter, penghitung menunjukkan 2000/2000"),
    dict(id="SK-05", fitur="Baca satu ulasan", kebutuhan="FR-03", skenario="Ulasan memakai singkatan dan bahasa gaul", langkah="Tulis ulasan, tekan Baca nadanya, lihat daftar kata", data=GAUL, harapan="Hasil muncul dan daftar kata sudah dibakukan: gk jadi tidak, bs jadi bisa, udh jadi sudah"),
    dict(id="SK-06", fitur="Baca satu ulasan", kebutuhan="FR-04", skenario="Memakai contoh ulasan", langkah="Klik tombol Contoh KAI Access", data="contoh bawaan", harapan="Formulir terisi otomatis dan hasil Positif langsung muncul"),
    dict(id="SK-07", fitur="Baca satu ulasan", kebutuhan="FR-02", skenario="Teks tanpa huruf Latin sama sekali", langkah="Tulis teks aksara Jawa, tekan Baca nadanya", data="ꦱꦸꦫꦏꦂꦠ", harapan="Tidak diberi nada: muncul keterangan Tidak terbaca beserta saran menulis lebih lengkap"),
    dict(id="SK-08", fitur="Baca satu ulasan", kebutuhan="FR-05", skenario="Mengunduh kartu hasil", langkah="Setelah hasil muncul, klik Unduh kartu hasil", data=KELUHAN, harapan="Berkas PNG bernama suara-rakyat-negative.png terunduh"),
    dict(id="SK-09", fitur="Baca satu ulasan", kebutuhan="FR-01", skenario="Kirim dengan pintasan papan ketik", langkah="Tulis ulasan, tekan Ctrl + Enter", data=PUJIAN, harapan="Hasil muncul tanpa menekan tombol"),
    # fitur 2: cek massal
    dict(id="SK-10", fitur="Cek massal", kebutuhan="FR-06, FR-08", skenario="Menempel tiga ulasan", langkah="Buka /massal, tempel tiga ulasan satu per baris, tekan Baca semua", data="tiga ulasan", harapan="Ringkasan menunjukkan 3 ulasan dibaca dan tabel berisi 3 baris"),
    dict(id="SK-11", fitur="Cek massal", kebutuhan="FR-06, FR-08", skenario="Memakai 200 ulasan contoh", langkah="Klik Pakai 200 ulasan contoh, tekan Baca semua", data="web/public/contoh/ulasan-contoh.csv", harapan="200 ulasan dibaca dan kecocokan dengan bintang ditampilkan"),
    dict(id="SK-12", fitur="Cek massal", kebutuhan="FR-07", skenario="Mengunggah CSV dengan nama kolom tidak baku", langkah="Unggah CSV berkolom komentar dan rating", data="5 baris, kolom komentar dan rating", harapan="Kolom ulasan otomatis terpilih komentar dan kolom bintang terpilih rating"),
    dict(id="SK-13", fitur="Cek massal", kebutuhan="FR-09", skenario="Mengunduh hasil CSV", langkah="Setelah 200 ulasan contoh dibaca, klik Unduh hasil CSV", data="200 ulasan contoh", harapan="CSV berisi 201 baris (judul + 200) dengan kolom nada dan keyakinan"),
    dict(id="SK-14", fitur="Cek massal", kebutuhan="FR-08", skenario="Menyaring hasil per nada", langkah="Setelah hasil muncul, klik saringan Negatif", data="200 ulasan contoh", harapan="Semua baris tabel yang tampil bernada Negatif"),
    dict(id="SK-15", fitur="Cek massal", kebutuhan="FR-06", skenario="Lebih dari 1.000 ulasan", langkah="Tempel 1.005 baris, tekan Baca semua", data="1.005 ulasan pendek", harapan="Peringatan batas 1.000 muncul dan tepat 1.000 ulasan dibaca"),
    dict(id="SK-16", fitur="Cek massal", kebutuhan="FR-06", skenario="Dikirim kosong", langkah="Tekan Baca semua tanpa mengisi apa pun", data="(kosong)", harapan="Pesan 'Tempel minimal satu ulasan' muncul"),
    # fitur 3: dashboard aplikasi
    dict(id="SK-17", fitur="Cek massal", kebutuhan="FR-08", skenario="Ada ulasan yang tidak terbaca", langkah="Tempel dua ulasan biasa dan satu baris aksara Jawa, tekan Baca semua", data="2 ulasan + 1 baris ꦱꦸꦫꦏꦂꦠ", harapan="2 ulasan diberi nada, 1 ditandai tidak terbaca"),
    dict(id="SK-18", fitur="Dashboard aplikasi", kebutuhan="FR-10", skenario="Membuka dashboard", langkah="Buka /dashboard", data="-", harapan="Enam aplikasi tampil di ringkasan, diurutkan dari porsi negatif terbesar"),
    dict(id="SK-19", fitur="Dashboard aplikasi", kebutuhan="FR-10", skenario="Memilih aplikasi lewat tombol", langkah="Klik tombol KAI Access", data="-", harapan="Judul, angka, daftar keluhan, dan grafik tren berganti ke KAI Access"),
    dict(id="SK-20", fitur="Dashboard aplikasi", kebutuhan="FR-10", skenario="Memilih aplikasi lewat baris ringkasan", langkah="Klik baris JMO di ringkasan", data="-", harapan="Bagian detail berganti ke JMO"),
    # fitur 4: kuesioner SUS
    dict(id="SK-21", fitur="Kuesioner SUS", kebutuhan="FR-11", skenario="Mengisi semua butir dengan jawaban terbaik", langkah="Pilih 5 untuk butir ganjil dan 1 untuk butir genap, tekan Hitung skor", data="5,1,5,1,5,1,5,1,5,1", harapan="Skor SUS 100"),
    dict(id="SK-22", fitur="Kuesioner SUS", kebutuhan="FR-11", skenario="Belum semua butir diisi", langkah="Isi 9 butir saja", data="9 jawaban", harapan="Tombol tidak aktif dan bertuliskan Terisi 9 dari 10"),
    dict(id="SK-23", fitur="Kuesioner SUS", kebutuhan="FR-11", skenario="Merekap jawaban dua responden", langkah="Buka tab Rekap tim, tempel dua baris jawaban", data="5,1,5,1,5,1,5,1,5,1 dan 3 sepuluh kali", harapan="Rata-rata SUS 75,0 (dari skor 100 dan 50)"),
    # kebutuhan nonfungsional
    dict(id="SK-24", fitur="API dan keamanan", kebutuhan="NFR-05", skenario="Permintaan JSON rusak", langkah="POST /api/predict dengan isi bukan JSON", data="{rusak", harapan="Status 400 dengan pesan format"),
    dict(id="SK-25", fitur="API dan keamanan", kebutuhan="NFR-05", skenario="Teks melebihi batas lewat API", langkah="POST /api/predict dengan teks 2.001 karakter", data="2.001 karakter", harapan="Status 400"),
    dict(id="SK-26", fitur="API dan keamanan", kebutuhan="NFR-05", skenario="Cek massal melebihi batas lewat API", langkah="POST /api/predict-batch dengan 1.001 teks", data="1.001 teks", harapan="Status 400"),
    dict(id="SK-27", fitur="API dan keamanan", kebutuhan="NFR-05", skenario="Header keamanan", langkah="Buka halaman depan, periksa header respons", data="-", harapan="Ada Content-Security-Policy, X-Frame-Options DENY, X-Content-Type-Options nosniff, Strict-Transport-Security"),
    dict(id="SK-28", fitur="Kinerja", kebutuhan="NFR-02", skenario="Waktu respons baca satu ulasan", langkah="Kirim 20 permintaan /api/predict berurutan", data="ulasan keluhan SK-01", harapan="Median waktu respons di bawah 1 detik"),
    dict(id="SK-29", fitur="Tampilan", kebutuhan="NFR-06", skenario="Dibuka di layar HP", langkah="Buka keempat halaman di lebar 390 px", data="-", harapan="Tidak ada halaman yang perlu digeser ke samping"),
    dict(id="SK-30", fitur="Privasi", kebutuhan="NFR-04", skenario="Contoh ulasan di dashboard bersih dari data pribadi", langkah="Buka /dashboard, periksa semua contoh ulasan keenam aplikasi", data="-", harapan="Tidak ada deret angka 6 digit atau lebih dan tidak ada alamat surel"),
    dict(id="SK-31", fitur="Navigasi", kebutuhan="NFR-01", skenario="Semua menu berfungsi", langkah="Klik tiap menu di kepala halaman dalam", data="-", harapan="Tiap menu membuka halaman yang benar"),
    dict(id="SK-32", fitur="API dan keamanan", kebutuhan="NFR-05", skenario="Pembatas laju", langkah="Kirim 70 permintaan /api/predict secepatnya", data="70 permintaan", harapan="Sebagian permintaan ditolak dengan status 429"),
]


def buka(p: Page, jalan: str) -> None:
    p.goto(URL + jalan, wait_until="networkidle", timeout=90000)


def baca(p: Page, teks: str) -> str:
    buka(p, "/#coba")
    p.fill("#review", teks)
    p.locator("#coba button[type=submit]").click()
    hasil = p.locator("[data-hasil]")
    expect(hasil).to_be_visible(timeout=15000)
    return hasil.get_attribute("data-hasil") or ""


def sk01(p, **_):
    label = baca(p, KELUHAN)
    teks = p.locator("section[aria-label='Hasil baca']").inner_text()
    yakin = re.search(r"Mesin [a-z -]+ \((\d+)%\)", teks)
    assert label == "negative", f"hasil {label}"
    assert yakin, "keterangan keyakinan tidak ada"
    return f"Negatif, {yakin.group(0)}"


def sk02(p, **_):
    label = baca(p, PUJIAN)
    assert label == "positive", f"hasil {label}"
    return "Positif"


def sk03(p, **_):
    buka(p, "/#coba")
    kirim = []
    p.on("request", lambda r: kirim.append(r.url) if "/api/predict" in r.url else None)
    p.locator("#coba button[type=submit]").click()
    pesan = p.locator("#coba [role=alert]").inner_text()
    p.wait_for_timeout(800)
    assert pesan == "Tulis atau tempel ulasanmu dulu.", pesan
    assert not kirim, "ada permintaan ke server"
    return f"pesan '{pesan}', 0 permintaan ke server"


def sk04(p, **_):
    buka(p, "/#coba")
    p.locator("#review").press_sequentially("a" * 2050, delay=0)
    n = len(p.locator("#review").input_value())
    hitung = p.locator("#coba form").inner_text()
    assert n == 2000, f"panjang {n}"
    assert "2000/2000" in hitung
    return f"berhenti di {n} karakter, penghitung 2000/2000"


def sk05(p, **_):
    baca(p, GAUL)
    kata = p.locator("[data-kata]").inner_text().split()
    for k in ["tidak", "bisa", "sudah"]:
        assert k in kata, f"{k} tidak ada di {kata}"
    assert "gk" not in kata and "udh" not in kata
    return "kata terbaca: " + " ".join(kata)


def sk06(p, **_):
    buka(p, "/#coba")
    p.get_by_role("button", name="Contoh KAI Access").click()
    expect(p.locator("[data-hasil]")).to_have_attribute("data-hasil", "positive", timeout=15000)
    isi = p.locator("#review").input_value()
    assert isi.startswith("Pesan tiket mudik")
    return f"formulir terisi '{isi[:40]}...', hasil Positif"


def sk07(p, **_):
    label = baca(p, "ꦱꦸꦫꦏꦂꦠ")
    assert label == "kosong", f"masih diberi nada {label}"
    expect(p.get_by_text("Tidak ada kata yang dikenali")).to_be_visible()
    return "keterangan Tidak terbaca muncul, tidak ada stempel nada"


def sk08(p, **_):
    baca(p, KELUHAN)
    with p.expect_download() as dl:
        p.get_by_role("button", name="Unduh kartu hasil").click()
    f = dl.value
    data = Path(f.path()).read_bytes()
    assert f.suggested_filename == "suara-rakyat-negative.png", f.suggested_filename
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bukan PNG"
    return f"{f.suggested_filename}, {len(data) // 1024} KB, berkas PNG sah"


def sk09(p, **_):
    buka(p, "/#coba")
    p.fill("#review", PUJIAN)
    p.locator("#review").press("Control+Enter")
    expect(p.locator("[data-hasil]")).to_have_attribute("data-hasil", "positive", timeout=15000)
    return "hasil Positif muncul lewat Ctrl + Enter"


def pakai_contoh(p: Page) -> None:
    p.get_by_role("button", name="Pakai 200 ulasan contoh").click()
    expect(p.get_by_text("ulasan-contoh.csv: 200 baris")).to_be_visible(timeout=20000)


def baca_massal(p: Page) -> str:
    p.get_by_role("button", name="Baca semua").click()
    kartu = p.locator("p", has_text="Ulasan dibaca").locator("xpath=..")
    expect(kartu).to_be_visible(timeout=30000)
    return kartu.inner_text()


def sk10(p, **_):
    buka(p, "/massal")
    p.fill("#massal", "otp tidak masuk dari kemarin\ntampilan baru lebih rapi, mantap\nlumayan tapi sering logout sendiri")
    ringkas = baca_massal(p)
    baris = p.locator("table tbody tr").count()
    assert re.search(r"\b3\b", ringkas) and baris == 3, f"{ringkas} | {baris} baris"
    return f"3 ulasan dibaca, tabel {baris} baris"


def sk11(p, **_):
    buka(p, "/massal")
    pakai_contoh(p)
    ringkas = baca_massal(p)
    cocok = p.get_by_text(re.compile(r"Cocok dengan label dari bintang")).inner_text()
    assert "200" in ringkas, ringkas
    return " ".join(cocok.split())


def sk12(p, **_):
    buka(p, "/massal")
    csv = "no,komentar,rating\n1,otp tidak masuk,1\n2,mantap cepat,5\n3,lumayan,3\n4,susah login,2\n5,sangat membantu,5\n"
    p.get_by_role("tab", name="Unggah CSV").click()
    p.set_input_files("#berkas", files=[{"name": "uji.csv", "mimeType": "text/csv", "buffer": csv.encode()}])
    pilih = p.locator("select")
    teks_kolom = pilih.nth(0).locator("option:checked").inner_text()
    bintang = pilih.nth(1).locator("option:checked").inner_text()
    assert teks_kolom == "komentar" and bintang == "rating", f"{teks_kolom} / {bintang}"
    ringkas = baca_massal(p)
    return f"kolom ulasan {teks_kolom}, kolom bintang {bintang}, " + " ".join(ringkas.split()[:3])


def sk13(p, **_):
    buka(p, "/massal")
    pakai_contoh(p)
    baca_massal(p)
    with p.expect_download() as dl:
        p.get_by_role("button", name="Unduh hasil CSV").click()
    baris = Path(dl.value.path()).read_text(encoding="utf-8-sig").splitlines()
    kepala = baris[0].split(",")
    assert len(baris) == 201 and kepala[-2:] == ["nada", "keyakinan"], f"{len(baris)} baris, {kepala}"
    return f"{dl.value.suggested_filename}, {len(baris)} baris, kolom {', '.join(kepala)}"


def sk14(p, **_):
    buka(p, "/massal")
    pakai_contoh(p)
    baca_massal(p)
    p.get_by_role("button", name=re.compile(r"^Negatif \(")).click()
    nada = p.locator("table tbody tr td:nth-child(3)").all_inner_texts()
    assert nada and all(n.strip() == "Negatif" for n in nada), set(nada)
    return f"{len(nada)} baris tampil, semuanya Negatif"


def sk15(p, **_):
    buka(p, "/massal")
    p.fill("#massal", "\n".join(f"ulasan nomor {i} aplikasinya lambat" for i in range(1005)))
    ringkas = baca_massal(p)
    peringatan = p.get_by_text(re.compile(r"Maksimal 1\.000 per kiriman")).inner_text()
    assert "1.000" in ringkas, ringkas
    return f"peringatan muncul ('{peringatan[:60]}...'), 1.000 ulasan dibaca"


def sk16(p, **_):
    buka(p, "/massal")
    p.get_by_role("button", name="Baca semua").click()
    pesan = p.get_by_text("Tempel minimal satu ulasan")
    expect(pesan).to_be_visible()
    return pesan.inner_text()


def sk17(p, **_):
    buka(p, "/massal")
    p.fill("#massal", "otp tidak masuk dari kemarin\nꦱꦸꦫꦏꦂꦠ\ntampilan baru lebih rapi, mantap")
    ringkas = baca_massal(p)
    tidak = p.locator("table tbody tr", has_text="tidak terbaca").count()
    assert re.search(r"\b2\b", ringkas) and "1 tidak terbaca" in ringkas and tidak == 1, ringkas
    return "2 ulasan diberi nada, 1 baris ditandai tidak terbaca"


def sk18(p, **_):
    buka(p, "/dashboard")
    baris = p.locator("section[aria-labelledby=ringkas] li button")
    nama = [b.locator("span span").first.inner_text() for b in baris.all()]
    assert len(nama) == 6, nama
    return "urutan: " + ", ".join(nama)


def sk19(p, **_):
    buka(p, "/dashboard")
    p.get_by_role("radio", name="KAI Access", exact=True).first.click()
    expect(p.locator("#detail")).to_have_text("KAI Access")
    keluhan = p.locator("ol").first.locator("li").count()
    grafik = p.locator("svg[aria-label*='KAI Access']").count()
    assert keluhan >= 3 and grafik == 1, f"{keluhan} keluhan, {grafik} grafik"
    return f"judul KAI Access, {keluhan} keluhan teratas, grafik tren KAI Access tampil"


def sk20(p, **_):
    buka(p, "/dashboard")
    p.locator("section[aria-labelledby=ringkas] li button", has_text="JMO").click()
    expect(p.locator("#detail")).to_have_text("JMO")
    return "detail berganti ke JMO"


def isi_sus(p: Page, jawaban: list[int]) -> None:
    buka(p, "/kuesioner")
    for i, v in enumerate(jawaban):
        p.locator(f"input[name=q{i}][value='{v}']").locator("xpath=..").click()


def sk21(p, **_):
    isi_sus(p, [5, 1] * 5)
    p.get_by_role("button", name="Hitung skor").click()
    skor = p.locator("p", has_text="Skor SUS kamu").locator("xpath=..").locator("p.display").inner_text()
    assert skor.strip() == "100", skor
    return f"skor {skor.strip()}"


def sk22(p, **_):
    isi_sus(p, [5, 1] * 4 + [5])
    tombol = p.locator("form button[type=submit]")
    tulisan = (tombol.text_content() or "").strip()
    assert tombol.is_disabled() and tulisan == "Terisi 9 dari 10", tulisan
    return f"tombol nonaktif bertuliskan '{tulisan}'"


def sk23(p, **_):
    buka(p, "/kuesioner")
    p.get_by_role("tab", name="Rekap tim").click()
    p.fill("#rekap", "5\t1\t5\t1\t5\t1\t5\t1\t5\t1\n3\t3\t3\t3\t3\t3\t3\t3\t3\t3")
    kartu = p.locator("p", has_text="Rata-rata SUS").locator("xpath=..").inner_text()
    assert "75,0" in kartu, kartu
    return "rata-rata 75,0 dari 2 responden"


def sk24(api, **_):
    # bytes dikirim apa adanya (string yang bukan JSON akan dibungkus jadi JSON oleh Playwright)
    r = api.post("/api/predict", data=b"{rusak", headers={"Content-Type": "application/json"})
    assert r.status == 400, r.status
    return f"status {r.status}: {r.json()['error']}"


def sk25(api, **_):
    r = api.post("/api/predict", data=json.dumps({"text": "a" * 2001}), headers={"Content-Type": "application/json"})
    assert r.status == 400, r.status
    return f"status {r.status}: {r.json()['error']}"


def sk26(api, **_):
    r = api.post("/api/predict-batch", data=json.dumps({"texts": ["ulasan"] * 1001}), headers={"Content-Type": "application/json"})
    assert r.status == 400, r.status
    return f"status {r.status}: {r.json()['error']}"


def sk27(api, **_):
    r = api.get("/")
    h = {k.lower(): v for k, v in r.headers.items()}
    wajib = {"content-security-policy": None, "x-frame-options": "DENY", "x-content-type-options": "nosniff", "strict-transport-security": None}
    kurang = [k for k, v in wajib.items() if k not in h or (v and h[k] != v)]
    assert not kurang, f"kurang: {kurang}"
    return "keempat header ada"


def sk28(api, **_):
    waktu, server = [], []
    for _ in range(20):
        t0 = time.perf_counter()
        r = api.post("/api/predict", data=json.dumps({"text": KELUHAN}), headers={"Content-Type": "application/json"})
        waktu.append((time.perf_counter() - t0) * 1000)
        assert r.status == 200, r.status
        server.append(r.json()["ms"])
    med = statistics.median(waktu)
    assert med < 1000, med
    return f"median {med:.0f} ms, maksimum {max(waktu):.0f} ms dari sisi penguji, hitungan model di server median {statistics.median(server):.2f} ms"


def sk29(_p, browser, **__):
    hasil = []
    for jalan in ["/", "/massal", "/dashboard", "/kuesioner"]:
        hp = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        hp.goto(URL + jalan, wait_until="networkidle", timeout=90000)
        hp.wait_for_timeout(500)
        meluber = hp.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
        hasil.append((jalan, meluber))
        hp.close()
    salah = [j for j, m in hasil if m]
    assert not salah, f"meluber: {salah}"
    return "keempat halaman pas di lebar 390 px"


def sk30(p, **_):
    buka(p, "/dashboard")
    teks = []
    for nama in ["Mobile JKN", "JMO", "SatuSehat", "MyPertamina", "KAI Access", "Info BMKG"]:
        p.get_by_role("radio", name=nama, exact=True).first.click()
        teks += p.locator("p.marker").all_inner_texts()
    buruk = [t for t in teks if re.search(r"\d{6,}|[\w.+-]+@[\w-]+\.\w+", t)]
    assert teks and not buruk, buruk
    return f"{len(teks)} contoh ulasan diperiksa, tidak ada angka panjang atau surel"


def sk31(p, **_):
    buka(p, "/massal")
    tujuan = {"Dashboard": "/dashboard", "Kuesioner": "/kuesioner", "Massal": "/massal", "Coba": "/"}
    hasil = []
    for nama, jalan in tujuan.items():
        p.locator("header nav").get_by_role("link", name=nama, exact=True).click()
        expect(p).to_have_url(re.compile(re.escape(URL + jalan) + r"(#coba)?$"), timeout=20000)
        sampai = p.url.split("#")[0].replace(URL, "") or "/"
        assert sampai == jalan, f"{nama} ke {sampai}"
        hasil.append(f"{nama} ke {sampai}")
        if nama == "Coba":
            break
        buka(p, "/massal")
    return ", ".join(hasil)


def sk32(api, **_):
    status = []
    for _ in range(70):
        r = api.post("/api/predict", data=json.dumps({"text": "cek"}), headers={"Content-Type": "application/json"})
        status.append(r.status)
    tolak = status.count(429)
    assert tolak > 0, f"tidak ada 429 dari {len(status)} permintaan"
    return f"{status.count(200)} diterima, {tolak} ditolak dengan 429"


FUNGSI = {f"SK-{i:02d}": globals()[f"sk{i:02d}"] for i in range(1, 33)}
PAKAI_API = {"SK-24", "SK-25", "SK-26", "SK-27", "SK-28", "SK-32"}


def main() -> None:
    hasil = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chromium")
        api = pw.request.new_context(base_url=URL)
        versi = browser.version
        for s in SKENARIO:
            t0 = time.perf_counter()
            p = browser.new_page(viewport=DESKTOP, accept_downloads=True)
            try:
                nyata = FUNGSI[s["id"]](api if s["id"] in PAKAI_API else p, browser=browser)
                status = "LULUS"
            except Exception as e:  # dicatat apa adanya, tidak disembunyikan
                nyata, status = f"{type(e).__name__}: {str(e)[:300]}", "GAGAL"
            finally:
                p.close()
            detik = round(time.perf_counter() - t0, 1)
            hasil.append({**s, "hasil": nyata, "status": status, "detik": detik})
            print(f"{s['id']} {status:6s} {detik:5.1f}s  {nyata}", flush=True)
        api.dispose()
        browser.close()

    lulus = sum(h["status"] == "LULUS" for h in hasil)
    keluar = {
        "url": URL,
        "waktu_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "peramban": f"Chromium {versi} (Playwright)",
        "sistem": f"{platform.system()} {platform.release()}, Python {platform.python_version()}",
        "jumlah": len(hasil),
        "lulus": lulus,
        "skenario": hasil,
    }
    (HERE / f"hasil-{NAMA}.json").write_text(json.dumps(keluar, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    md = [
        f"# Hasil pengujian skenario ({NAMA})",
        "",
        f"Diuji di {URL} pada {keluar['waktu_utc']} UTC dengan {keluar['peramban']}. Lulus {lulus} dari {len(hasil)} skenario.",
        "",
        "| Kode | Fitur | Kebutuhan | Skenario | Hasil yang diharapkan | Hasil sebenarnya | Status |",
        "|---|---|---|---|---|---|---|",
        *[f"| {h['id']} | {h['fitur']} | {h['kebutuhan']} | {h['skenario']} | {h['harapan']} | {h['hasil']} | {h['status']} |" for h in hasil],
        "",
    ]
    (HERE / f"HASIL-{NAMA}.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(f"\nlulus {lulus}/{len(hasil)}")


if __name__ == "__main__":
    main()
