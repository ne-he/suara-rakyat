# Suara Rakyat v5 (Streamlit)

Dashboard pemantauan ulasan aplikasi layanan publik untuk pengelola layanan. Pengguna memilih aplikasi
(atau mengisi application ID), start date, dan end date. Sistem mengambil ulasan dari Google Play lewat
`google-play-scraper`, membaca nadanya dengan Linear SVM hasil penelitian, lalu menampilkan komposisi nada,
tren per hari atau per minggu, kata yang paling menentukan, dan daftar ulasan per nada yang bisa diunduh sebagai CSV.

Model tidak dilatih ulang. Bobotnya dibaca dari `web/model/` (file yang sama dengan web v4) dan praprosesnya
memakai `ml/suara_ml/textnorm.py` (kode yang sama dengan saat training).

## Menjalankan

```bash
pip install -r streamlit-app/requirements.txt
streamlit run streamlit-app/app.py
```

## Struktur

| File | Isi |
|---|---|
| `app.py` | Tampilan Streamlit saja: input, dashboard, daftar ulasan, unduhan |
| `suara/apps.py` | Enam aplikasi yang bisa dipilih langsung beserta application ID-nya |
| `suara/scraper.py` | `ReviewScraper`: ambil ulasan per rentang tanggal, buang nama dan foto pengulas |
| `suara/classifier.py` | `SentimentClassifier`: TF-IDF kata dan karakter, Linear SVM, bias, temperature scaling, atribusi kata |
| `suara/analysis.py` | `ReviewAnalysis`: komposisi nada, kecocokan dengan bintang, tren, kata penentu, tabel, CSV |
| `tests/` | Unit test dan UI test (Streamlit AppTest), tanpa internet |

## Pengujian

```bash
cd streamlit-app
python -m pytest
```

- `test_classifier.py`: uji paritas dengan Linear SVM asli (sklearn) di 3.018 teks, hasilnya 0 label berbeda dan
  selisih peluang maksimal 5,15e-7. Atribusi kata dibandingkan dengan versi lambat yang ditulis langsung dari rumusnya.
- `test_scraper.py`: filter rentang tanggal, berhenti setelah melewati start date, batas 10.000 ulasan, identitas pengulas tidak disimpan.
- `test_analysis.py`: hitungan nada, penyamaran angka panjang, tabel dan CSV, tren, kata penentu.
- `test_app.py`: alur tampilan (halaman awal, start date setelah end date, application ID tidak valid, tautan
  Google Play, aplikasi tidak ditemukan, pencarian berhasil, filter nada, rentang kosong, peringatan batas).

## Batasan

- `google-play-scraper` bukan API resmi Google. Kalau Google mengubah halamannya, pengambilan ulasan bisa berhenti bekerja.
- Library tidak punya filter tanggal, jadi ulasan diambil dari yang terbaru sampai melewati start date, paling banyak 10.000 ulasan per pencarian.
- Model dilatih dari ulasan 2012 sampai 2023. Istilah dan fitur aplikasi yang muncul sesudahnya bisa belum dikenali.
- Hasil tidak disimpan di server. Setiap pencarian mengambil ulang dari Google Play.
