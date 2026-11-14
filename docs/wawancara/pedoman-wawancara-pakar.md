# Pedoman wawancara pakar

Dipakai untuk evaluasi subjektif di laporan (Bab 4.3). Tujuannya meminta penilaian orang yang
paham analisis sentimen atau layanan publik terhadap metode, hasil, dan kegunaan Suara Rakyat v5
(app Streamlit untuk pengelola layanan: pilih aplikasi dan rentang tanggal, ulasan diambil dari
Google Play, lalu nadanya dibaca).

## Siapa yang diwawancarai

Minimal satu, idealnya dua sampai tiga orang dengan latar berbeda:

| Profil | Kenapa relevan | Fokus pertanyaan |
|---|---|---|
| Dosen data science atau text mining | Paham pelabelan, metrik, dan model teks | Bagian A dan B |
| Praktisi atau peneliti NLP bahasa Indonesia | Paham bahasa gaul, singkatan, dan sindiran di ulasan | Bagian B dan C |
| Orang yang mengelola atau meneliti layanan publik digital (misalnya pegawai humas atau pengelola aplikasi instansi) | Paham apa yang berguna bagi pengelola layanan | Bagian C dan D |

Nama, jabatan, dan rekaman tidak disimpan di repositori publik. Simpan di folder tim yang tertutup.

## Sebelum wawancara

1. Kirim tautan app Streamlit dan satu paragraf ringkasan projek sehari sebelumnya.
2. Minta izin merekam. Kalau tidak boleh, satu anggota tim mencatat.
3. Siapkan laptop berisi app yang sudah dibuka sekali (supaya tidak menunggu app bangun), dan tabel hasil model dari laporan.
4. Durasi 30 sampai 40 menit. Satu orang bertanya, satu orang mencatat.

Kalimat pembuka yang bisa dipakai:

> Terima kasih sudah meluangkan waktu. Kami dari kelompok AOL Software Engineering BINUS
> membangun Suara Rakyat, alat untuk pengelola layanan publik yang mengambil ulasan aplikasi dari
> Google Play lalu membaca nadanya secara otomatis. Kami ingin
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

## Bagian C. Kegunaan app (sekitar 12 menit)

Minta pakar mencoba tiga tugas sambil berpikir keras: (1) pantau Mobile JKN tujuh hari terakhir,
(2) sebutkan hal yang paling sering dikeluhkan dari kata penentu dan daftar ulasan negatif, dan
(3) pantau aplikasi lain dengan menempel link Google Play-nya, lalu unduh CSV.

10. Apakah hasil di layar mudah dipahami oleh pegawai yang tidak paham model?
11. Apakah persen nada, tren, dan kata penentu cukup untuk menentukan apa yang harus diperbaiki?
    Informasi apa yang masih kurang, misalnya kategori keluhan seperti login atau pembayaran?
12. Apakah kolom "dibalas" dan urutan "paling banyak disukai" membantu tim layanan memilih ulasan
    yang perlu dibalas lebih dulu?
13. Ulasan diambil dengan library google-play-scraper, bukan API resmi Google. Menurut Bapak atau
    Ibu, apakah ini layak untuk pemakaian instansi, atau sebaiknya lewat ekspor resmi Play Console
    yang dimiliki instansi pemilik aplikasi?
14. Model dilatih dari ulasan 2012 sampai 2023, sedangkan yang dibaca sekarang ulasan 2026.
    Seberapa sering model seperti ini perlu dilatih ulang?

## Bagian D. Dampak dan etika (sekitar 5 menit)

15. Risiko apa yang perlu kami tulis di bagian batasan? Contoh: ulasan Play Store tidak mewakili
    seluruh warga, atau angka nada dikira penilaian resmi instansi.
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
