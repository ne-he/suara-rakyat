# Kebutuhan pengguna Suara Rakyat v5

Versi 5 menggantikan web v4 setelah feedback dosen 14 Oktober 2026: pengguna utama adalah
pengelola layanan di instansi pemerintah, bukan warga, dan mereka tidak perlu memasukkan ulasan
satu per satu. Pengguna cukup memilih aplikasi dan rentang tanggal, lalu sistem mengambil ulasan
dari Google Play dan membaca nadanya. Kode skenario uji (SV) merujuk ke `tests/skenario-v5/jalankan.py`,
tes otomatis merujuk ke `streamlit-app/tests/`. Kebutuhan v4 tetap ada di `kebutuhan-pengguna.md`
sebagai riwayat.

## 1. Pemangku kepentingan

| Pengguna | Yang ingin dilakukan | Yang membuat mereka berhenti memakai |
|---|---|---|
| Pengelola layanan di instansi (pengguna utama), misalnya tim humas, layanan pelanggan, atau pengelola aplikasi | Melihat porsi keluhan aplikasinya di rentang waktu tertentu, kapan memuncak, soal apa, dan membaca keluhannya langsung | Harus memasukkan data sendiri, istilah teknis, hasil tidak bisa diunduh |
| Pimpinan instansi | Angka ringkas dan tren untuk laporan berkala | Angka tanpa penjelasan sumber dan batasannya |
| Tim pengembang Suara Rakyat | Merawat model, daftar aplikasi, dan pengujian | Kode yang tidak bisa dijalankan ulang atau tidak punya tes |

## 2. Kebutuhan fungsional

| Kode | Kebutuhan | Diuji di |
|---|---|---|
| FR5-01 | Pengguna memilih satu dari enam aplikasi layanan publik, atau mengisi application ID sendiri. Link Google Play utuh juga diterima | SV-01, SV-03, SV-04, SV-05, `test_app.py` |
| FR5-02 | Pengguna mengisi start date dan end date. Sistem menolak start date yang jatuh setelah end date | SV-01, SV-02 |
| FR5-03 | Sistem mengambil ulasan Google Play Indonesia di rentang tanggal itu dengan google-play-scraper, menampilkan progres, dan berhenti di 10.000 ulasan dengan peringatan | SV-06, SV-12, `test_scraper.py` |
| FR5-04 | Sistem membaca nada tiap ulasan (negatif, netral, positif) dengan Linear SVM hasil penelitian. Ulasan tanpa kata yang dikenali ditandai tidak terbaca | SV-06, `test_classifier.py` |
| FR5-05 | Sistem menampilkan jumlah ulasan, persen tiap nada, dan kecocokan nada dengan bintang | SV-06 |
| FR5-06 | Sistem menampilkan tren nada per hari, atau per minggu untuk rentang lebih dari 62 hari | SV-07, SV-11, `test_analysis.py` |
| FR5-07 | Sistem menampilkan kata yang paling mendorong ulasan ke negatif dan ke positif | SV-07, `test_analysis.py` |
| FR5-08 | Pengguna membaca daftar ulasan per nada, bisa diurutkan menurut terbaru, paling banyak disukai, atau keyakinan, lengkap dengan bintang dan status sudah dibalas | SV-08, SV-09 |
| FR5-09 | Pengguna mengunduh seluruh hasil sebagai CSV yang langsung terbaca di Excel | SV-10 |

## 3. Kebutuhan nonfungsional

| Kode | Kebutuhan | Ukuran keberhasilan | Bukti |
|---|---|---|---|
| NFR5-01 | Mudah dipakai pengguna non-IT | Aplikasi dipilih dari nama, bukan kode. Tampil baik di lebar 390 px. Skor SUS rata-rata minimal 68 | SV-01, SV-13, kuesioner SUS |
| NFR5-02 | Cepat | Pantau 7 hari Mobile JKN di bawah 30 detik, klasifikasi di bawah 1 ms per ulasan | SV-14, ukuran di README app |
| NFR5-03 | Hasil sama dengan penelitian | Uji paritas classifier v5 dengan Linear SVM asli tanpa beda label | `test_classifier.py` (3.018 teks, 0 beda) |
| NFR5-04 | Menjaga data pribadi (UU PDP Nomor 27 Tahun 2022) | Nama dan foto pengulas tidak diambil, angka panjang dan email disamarkan, hasil tidak disimpan di server | SV-10, `test_scraper.py`, `test_analysis.py` |
| NFR5-05 | Biaya nol | Berjalan di Streamlit Community Cloud gratis tanpa database | konfigurasi deploy |
| NFR5-06 | Galat dijelaskan dengan bahasa biasa | Input salah, aplikasi tidak ditemukan, rentang tanpa ulasan, dan Google Play tidak bisa dihubungi masing-masing punya pesan | SV-02 sampai SV-04, `test_app.py` |

## 4. Cara kebutuhan ini dikumpulkan dan divalidasi

1. Feedback dosen setelah presentasi 14 Oktober 2026: pengguna utama pemerintah, input berupa
   application ID dan rentang tanggal, ambil data lewat google-play-scraper, tampilkan statistik
   dan daftar komentar per nada, cukup dengan Streamlit.
2. Pertanyaan teman sekelas saat presentasi: pemerintah tidak akan memasukkan ulasan satu per satu.
3. Divalidasi lewat wawancara pakar dan uji pakai dengan pedoman di `docs/wawancara/`, lalu kuesioner SUS.
