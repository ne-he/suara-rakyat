# Kebutuhan pengguna Suara Rakyat

Dokumen ini merangkum siapa yang memakai web, apa yang mereka butuhkan, dan bagaimana tiap
kebutuhan diuji. Kode skenario uji (SK) merujuk ke `tests/skenario/jalankan.py`.

## 1. Pemangku kepentingan

| Pengguna | Yang ingin dilakukan | Yang membuat mereka berhenti memakai |
|---|---|---|
| Warga (pengguna umum) | Tahu apakah ulasan atau keluhannya terbaca sebagai keluhan, lalu membagikannya | Istilah teknis, pilihan yang membingungkan, harus daftar akun |
| Pengelola layanan publik | Melihat keluhan apa yang paling sering muncul di aplikasinya dan kapan memuncak, membaca ratusan masukan sekaligus | Hasil yang tidak bisa diunduh, tidak jelas sumber angkanya |
| Peneliti atau jurnalis | Ringkasan nada per aplikasi dan data mentah hasil baca untuk diolah lagi | Metode yang tertutup, data pribadi ikut terbuka |
| Tim pengembang | Melatih ulang model, memperbarui data dashboard, merekap kuesioner | Pipeline yang tidak bisa dijalankan ulang |

## 2. Kebutuhan fungsional

| Kode | Kebutuhan | Diuji di |
|---|---|---|
| FR-01 | Pengguna dapat menulis atau menempel satu ulasan (maksimal 2.000 karakter) lalu meminta nadanya | SK-01, SK-02, SK-03, SK-04, SK-09 |
| FR-02 | Sistem menampilkan nada (negatif, netral, positif), tingkat keyakinan dalam kata dan persen, dan peluang tiap nada. Teks tanpa kata yang dikenali ditandai tidak terbaca, bukan diberi nada | SK-01, SK-02, SK-07 |
| FR-03 | Sistem menandai kata yang paling menentukan hasil, setelah singkatan dibakukan | SK-05 |
| FR-04 | Pengguna dapat mencoba contoh ulasan dengan sekali klik | SK-06 |
| FR-05 | Pengguna dapat mengunduh kartu hasil PNG, dengan atau tanpa teks ulasan | SK-08 |
| FR-06 | Pengguna dapat membaca sampai 1.000 ulasan sekaligus dengan menempel teks atau mengunggah CSV | SK-10, SK-11, SK-15, SK-16 |
| FR-07 | Sistem mengenali kolom ulasan dan kolom bintang di CSV secara otomatis, dan pengguna bisa menggantinya | SK-12 |
| FR-08 | Sistem menampilkan porsi nada, kata pendorong tiap nada, kecocokan dengan bintang (kalau ada), dan tabel yang bisa disaring | SK-10, SK-11, SK-14, SK-17 |
| FR-09 | Pengguna dapat mengunduh hasil cek massal sebagai CSV | SK-13 |
| FR-10 | Sistem menampilkan dashboard per aplikasi: porsi nada, rata-rata bintang, keluhan dan pujian yang khas, contoh ulasan, tren per kuartal | SK-18, SK-19, SK-20 |
| FR-11 | Pengguna dapat mengisi kuesioner SUS dan melihat skornya, dan tim dapat merekap jawaban | SK-21, SK-22, SK-23 |

## 3. Kebutuhan nonfungsional

| Kode | Kebutuhan | Ukuran keberhasilan | Bukti |
|---|---|---|---|
| NFR-01 | Mudah dipakai orang awam | Tanpa istilah model di layar, panduan tiga langkah, skor SUS rata-rata minimal 68 | SK-31, kuesioner SUS |
| NFR-02 | Cepat | Median respons baca satu ulasan di bawah 1 detik, hitungan model di bawah 1 ms per ulasan | SK-28, `npm run bench` |
| NFR-03 | Cukup tepat | Macro-F1 data uji di atas baseline paper IGAR yang direplikasi pada pembagian data yang sama | `ml/reports/final_selection.json`, `pembanding_luar.json` |
| NFR-04 | Menjaga data pribadi (UU PDP Nomor 27 Tahun 2022) | Teks pengunjung tidak disimpan, contoh ulasan disamarkan | SK-30, kode route API |
| NFR-05 | Aman dari penyalahgunaan sederhana | Batas ukuran, validasi input, pembatas laju, header keamanan | SK-24 sampai SK-27, SK-32 |
| NFR-06 | Tampil baik di HP | Tidak ada halaman yang perlu digeser ke samping di lebar 390 px | SK-29 |
| NFR-07 | Biaya nol | Berjalan di paket gratis Vercel tanpa basis data | konfigurasi deploy |
| NFR-08 | Hasil web sama dengan hasil penelitian | Uji paritas Python lawan TypeScript tanpa beda label | `npm run parity` |

## 4. Cara kebutuhan ini dikumpulkan dan divalidasi

1. Dirumuskan tim dari masalah yang ditemukan saat audit data, dari paper dataset IGAR, dan dari
   perbandingan dengan aplikasi sejenis.
2. Disaring ulang setelah konsultasi dengan dosen pada 2 Oktober 2026: web harus bisa dipakai
   orang yang tidak paham model, jadi pilihan model dan angka teknis dikeluarkan dari tampilan.
3. Divalidasi lewat wawancara pakar dan pengguna dengan pedoman di `docs/wawancara/`, lalu
   kuesioner SUS di halaman `/kuesioner`.
