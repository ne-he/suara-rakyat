# Hasil pengujian skenario (lokal)

Diuji di http://localhost:3130 pada 2026-10-03 02:46 UTC dengan Chromium 148.0.7778.96 (Playwright). Lulus 29 dari 31 skenario.

| Kode | Fitur | Kebutuhan | Skenario | Hasil yang diharapkan | Hasil sebenarnya | Status |
|---|---|---|---|---|---|---|
| SK-01 | Baca satu ulasan | FR-01, FR-02 | Ulasan berisi keluhan jelas | Stempel Negatif muncul beserta tingkat keyakinan dan tiga batang peluang | Negatif, Mesin yakin (89%) | LULUS |
| SK-02 | Baca satu ulasan | FR-01, FR-02 | Ulasan berisi pujian jelas | Stempel Positif muncul | Positif | LULUS |
| SK-03 | Baca satu ulasan | FR-01 | Formulir dikirim kosong | Pesan 'Tulis atau tempel ulasanmu dulu.' muncul dan tidak ada permintaan ke server | pesan 'Tulis atau tempel ulasanmu dulu.', 0 permintaan ke server | LULUS |
| SK-04 | Baca satu ulasan | FR-01 | Ulasan lebih dari 2.000 karakter | Formulir berhenti menerima ketikan di 2.000 karakter, penghitung menunjukkan 2000/2000 | berhenti di 2000 karakter, penghitung 2000/2000 | LULUS |
| SK-05 | Baca satu ulasan | FR-03 | Ulasan memakai singkatan dan bahasa gaul | Hasil muncul dan daftar kata sudah dibakukan: gk jadi tidak, bs jadi bisa, udh jadi sudah | kata terbaca: aplikasinya tidak bisa dibuka ngelag terus sudah update tetep error | LULUS |
| SK-06 | Baca satu ulasan | FR-04 | Memakai contoh ulasan | Formulir terisi otomatis dan hasil Positif langsung muncul | formulir terisi 'Pesan tiket mudik jadi gampang banget, t...', hasil Positif | LULUS |
| SK-07 | Baca satu ulasan | FR-02 | Teks tanpa huruf Latin sama sekali | Hasil tetap muncul dengan keterangan bahwa tidak ada kata yang dikenali | hasil positive dengan keterangan tidak ada kata yang dikenali | LULUS |
| SK-08 | Baca satu ulasan | FR-05 | Mengunduh kartu hasil | Berkas PNG bernama suara-rakyat-negative.png terunduh | suara-rakyat-negative.png, 190 KB, berkas PNG sah | LULUS |
| SK-09 | Baca satu ulasan | FR-01 | Kirim dengan pintasan papan ketik | Hasil muncul tanpa menekan tombol | hasil Positif muncul lewat Ctrl + Enter | LULUS |
| SK-10 | Cek massal | FR-06, FR-08 | Menempel tiga ulasan | Ringkasan menunjukkan 3 ulasan dibaca dan tabel berisi 3 baris | 3 ulasan dibaca, tabel 3 baris | LULUS |
| SK-11 | Cek massal | FR-06, FR-08 | Memakai 200 ulasan contoh | 200 ulasan dibaca dan kecocokan dengan bintang ditampilkan | Cocok dengan label dari bintang di 84,5% dari 200 ulasan yang punya bintang. | LULUS |
| SK-12 | Cek massal | FR-07 | Mengunggah CSV dengan nama kolom tidak baku | Kolom ulasan otomatis terpilih komentar dan kolom bintang terpilih rating | kolom ulasan komentar, kolom bintang rating, ULASAN DIBACA 5 | LULUS |
| SK-13 | Cek massal | FR-09 | Mengunduh hasil CSV | CSV berisi 201 baris (judul + 200) dengan kolom nada dan keyakinan | hasil-suara-rakyat.csv, 201 baris, kolom app, ulasan, bintang, nada, keyakinan | LULUS |
| SK-14 | Cek massal | FR-08 | Menyaring hasil per nada | Semua baris tabel yang tampil bernada Negatif | 128 baris tampil, semuanya Negatif | LULUS |
| SK-15 | Cek massal | FR-06 | Lebih dari 1.000 ulasan | Peringatan batas 1.000 muncul dan tepat 1.000 ulasan dibaca | peringatan muncul ('Ada 1.005 ulasan. Maksimal 1.000 per kiriman, jadi hanya 1.0...'), 1.000 ulasan dibaca | LULUS |
| SK-16 | Cek massal | FR-06 | Dikirim kosong | Pesan 'Tempel minimal satu ulasan' muncul | Tempel minimal satu ulasan, satu ulasan per baris. | LULUS |
| SK-18 | Dashboard aplikasi | FR-10 | Membuka dashboard | Enam aplikasi tampil di ringkasan, diurutkan dari porsi negatif terbesar | urutan: MyPertamina, KAI Access, SatuSehat, Mobile JKN, JMO, Info BMKG | LULUS |
| SK-19 | Dashboard aplikasi | FR-10 | Memilih aplikasi lewat tombol | Judul, angka, daftar keluhan, dan grafik tren berganti ke KAI Access | judul KAI Access, 8 keluhan teratas, grafik tren KAI Access tampil | LULUS |
| SK-20 | Dashboard aplikasi | FR-10 | Memilih aplikasi lewat baris ringkasan | Bagian detail berganti ke JMO | detail berganti ke JMO | LULUS |
| SK-21 | Kuesioner SUS | FR-11 | Mengisi semua butir dengan jawaban terbaik | Skor SUS 100 | skor 100 | LULUS |
| SK-22 | Kuesioner SUS | FR-11 | Belum semua butir diisi | Tombol tidak aktif dan bertuliskan Terisi 9 dari 10 | AssertionError: TERISI 9 DARI 10 | GAGAL |
| SK-23 | Kuesioner SUS | FR-11 | Merekap jawaban dua responden | Rata-rata SUS 75,0 (dari skor 100 dan 50) | rata-rata 75,0 dari 2 responden | LULUS |
| SK-24 | API dan keamanan | NFR-05 | Permintaan JSON rusak | Status 400 dengan pesan format | status 400: Tulis ulasannya dulu. | LULUS |
| SK-25 | API dan keamanan | NFR-05 | Teks melebihi batas lewat API | Status 400 | status 400: Ulasan maksimal 2000 karakter. | LULUS |
| SK-26 | API dan keamanan | NFR-05 | Cek massal melebihi batas lewat API | Status 400 | status 400: Maksimal 1000 ulasan per kiriman. | LULUS |
| SK-27 | API dan keamanan | NFR-05 | Header keamanan | Ada Content-Security-Policy, X-Frame-Options DENY, X-Content-Type-Options nosniff, Strict-Transport-Security | keempat header ada | LULUS |
| SK-28 | Kinerja | NFR-02 | Waktu respons baca satu ulasan | Median waktu respons di bawah 1 detik | median 26 ms, maksimum 62 ms dari sisi penguji; hitungan model di server median 0.54 ms | LULUS |
| SK-29 | Tampilan | NFR-06 | Dibuka di layar HP | Tidak ada halaman yang perlu digeser ke samping | keempat halaman pas di lebar 390 px | LULUS |
| SK-30 | Privasi | NFR-04 | Contoh ulasan di dashboard bersih dari data pribadi | Tidak ada deret angka 6 digit atau lebih dan tidak ada alamat surel | 28 contoh ulasan diperiksa, tidak ada angka panjang atau surel | LULUS |
| SK-31 | Navigasi | NFR-01 | Semua menu berfungsi | Tiap menu membuka halaman yang benar | AssertionError: Dashboard ke /massal | GAGAL |
| SK-32 | API dan keamanan | NFR-05 | Pembatas laju | Sebagian permintaan ditolak dengan status 429 | 38 diterima, 32 ditolak dengan 429 | LULUS |
