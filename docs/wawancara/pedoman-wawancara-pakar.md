# Pedoman wawancara pakar

Dipakai untuk evaluasi subjektif di laporan (Bab 4.3). Tujuannya meminta penilaian orang yang
paham analisis sentimen atau layanan publik terhadap metode, hasil, dan kegunaan Suara Rakyat.

## Siapa yang diwawancarai

Minimal satu, idealnya dua sampai tiga orang dengan latar berbeda:

| Profil | Kenapa relevan | Fokus pertanyaan |
|---|---|---|
| Dosen data science atau text mining | Paham pelabelan, metrik, dan model teks | Bagian A dan B |
| Praktisi atau peneliti NLP bahasa Indonesia | Paham bahasa gaul, singkatan, dan sindiran di ulasan | Bagian B dan C |
| Orang yang mengelola atau meneliti layanan publik digital | Paham apa yang berguna bagi pengelola layanan | Bagian C dan D |

Nama, jabatan, dan rekaman tidak disimpan di repositori publik. Simpan di folder tim yang tertutup.

## Sebelum wawancara

1. Kirim tautan web dan satu paragraf ringkasan projek sehari sebelumnya.
2. Minta izin merekam. Kalau tidak boleh, satu anggota tim mencatat.
3. Siapkan laptop berisi web live, dashboard, dan tabel hasil model dari laporan.
4. Durasi 30 sampai 40 menit. Satu orang bertanya, satu orang mencatat.

Kalimat pembuka yang bisa dipakai:

> Terima kasih sudah meluangkan waktu. Kami dari kelompok AOL Software Engineering BINUS
> membangun web Suara Rakyat yang membaca nada ulasan enam aplikasi layanan publik. Kami ingin
> minta pendapat Bapak atau Ibu tentang metode, hasil, dan kegunaannya. Wawancara sekitar 30
> menit. Boleh kami rekam untuk keperluan laporan? Nama tidak akan kami tampilkan tanpa izin.

## Bagian A. Data dan pelabelan (sekitar 8 menit)

1. Label kami berasal dari bintang: 1 dan 2 negatif, 3 netral, 4 dan 5 positif. Menurut Bapak atau
   Ibu, seberapa layak cara ini untuk analisis sentimen?
2. Kami menemukan teks yang sama persis bisa mendapat bintang berbeda, misalnya kata "lambat"
   yang 20 kali diberi bintang tinggi. Apa saran untuk menangani label seperti ini?
3. Kami menggabungkan ulasan kembar dan membagi data dengan hash teks supaya teks yang sama tidak
   muncul di data latih dan data uji sekaligus. Apakah langkah ini sudah cukup, atau ada yang
   terlewat?
4. Kelas netral hanya sekitar 7 persen data. Lebih baik kelas ini dipertahankan, digabung, atau
   dipecah, misalnya menjadi pertanyaan dan saran?

## Bagian B. Model dan evaluasi (sekitar 10 menit)

5. Kami membandingkan Linear SVM, Logistic Regression, dan Naive Bayes, lalu memakai Linear SVM di
   web. Selain skor, alasan apa yang menurut Bapak atau Ibu paling penting dalam memilih model
   untuk produk seperti ini?
6. IndoBERTweet unggul sekitar 0,02 macro-F1 tetapi sekitar 95 kali lebih lambat dan butuh server
   tersendiri. Apakah keputusan kami tidak memakainya di web masuk akal?
7. Kami memakai macro-F1 sebagai metrik utama, bukan akurasi. Setuju? Ada metrik lain yang
   sebaiknya ditambahkan?
8. Kami juga memakai cosine similarity untuk tiga hal: kemiripan antar kelas, tetangga terdekat,
   dan kemiripan porsi nada per aplikasi. Apakah cara ini tepat untuk mengevaluasi sentimen?
9. Model kami paling sering keliru pada sindiran dan ulasan campuran. Pendekatan apa yang paling
   realistis untuk memperbaikinya dalam waktu satu semester?

## Bagian C. Kegunaan web (sekitar 10 menit)

Minta pakar mencoba tiga tugas sambil berpikir keras: baca satu ulasan, buka dashboard lalu
temukan keluhan terbanyak di satu aplikasi, dan cek 200 ulasan contoh di halaman Massal.

10. Apakah hasil di layar mudah dipahami oleh orang yang tidak paham model?
11. Apakah keterangan "mesin yakin" dan kata yang diwarnai membantu, atau justru membingungkan?
12. Dari dashboard, informasi apa yang paling berguna, dan apa yang masih kurang?
13. Apakah ada bagian yang bisa disalahartikan, misalnya dikira penilaian resmi instansi?

## Bagian D. Dampak dan etika (sekitar 5 menit)

14. Siapa yang menurut Bapak atau Ibu paling diuntungkan oleh alat seperti ini?
15. Risiko apa yang perlu kami tulis di bagian batasan? Contoh: ulasan Play Store tidak mewakili
    seluruh warga.
16. Kalau projek ini dilanjutkan, satu hal apa yang paling perlu dikerjakan lebih dulu?

## Penutup

Tanyakan apakah boleh dikutip namanya di laporan, atau cukup ditulis dengan inisial dan latar
belakangnya. Ucapkan terima kasih.

## Lembar catatan (satu lembar per narasumber)

| Butir | Isi |
|---|---|
| Kode narasumber | P1, P2, ... |
| Latar belakang | [jabatan atau bidang, tanpa nama kalau tidak diizinkan] |
| Tanggal, tempat, durasi | |
| Rekaman | ya / tidak |
| Jawaban nomor 1 sampai 16 | ringkas per nomor, kutipan penting ditulis apa adanya |
| Saran yang bisa langsung dikerjakan | |
| Saran untuk pengembangan lanjutan | |

## Cara mengolah hasil

1. Tulis ulang jawaban tiap narasumber per nomor pertanyaan.
2. Beri kode tema pada tiap jawaban, misalnya label, metrik, kegunaan, risiko.
3. Hitung berapa narasumber yang menyebut tiap tema.
4. Di laporan, tampilkan tabel tema, jumlah narasumber, dan satu kutipan pendukung, lalu tulis apa
   yang sudah atau akan diperbaiki dari tiap tema.
