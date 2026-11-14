# Hasil pengujian skenario v5 (lokal)

URL: http://localhost:8531. Waktu: 2026-11-14T03:59:42+00:00 UTC. Lulus 14 dari 14.

| Kode | Kebutuhan | Skenario | Data uji | Hasil yang diharapkan | Hasil sebenarnya | Status |
|---|---|---|---|---|---|---|
| SV-01 | FR5-01, FR5-02 | Membuka halaman | - | Judul tampil, pilihan berisi 6 aplikasi dan Aplikasi lain, rentang bawaan 7 hari sampai hari ini | judul tampil: True, 7 pilihan, rentang 08/11/2026 sampai 14/11/2026 | LULUS |
| SV-02 | FR5-02 | Start date setelah end date | start hari ini, end 3 hari lalu | Pesan galat tentang start date muncul dan tidak ada ulasan yang diambil | pesan: Start date harus sama dengan atau sebelum end date. | LULUS |
| SV-03 | FR5-01 | Application ID tidak valid | bukan id | Pesan galat meminta application ID yang valid | pesan: Isi application ID yang valid, misalnya com.bpjstku. | LULUS |
| SV-04 | FR5-01, NFR5-06 | Application ID yang tidak ada di Google Play | com.suararakyat.tidakada | Pesan aplikasi tidak ditemukan | pesan: Application ID com.suararakyat.tidakada tidak ditemukan di Google Play Indonesia. Cek lagi ejaannya. | LULUS |
| SV-05 | FR5-01 | Menempel link Google Play utuh | https://play.google.com/store/apps/details?id=com.kai.kaiticketing&hl=id | Dashboard Access by KAI tampil | judul dashboard: ['Access by KAI'] | LULUS |
| SV-06 | FR5-03, FR5-04, FR5-05 | Pantau Mobile JKN 7 hari terakhir | app.bpjs.mobile, 7 hari | Empat angka tampil, persen tiga nada berjumlah sekitar 100%, kecocokan dengan bintang ditampilkan | {'Ulasan dibaca': '610', 'Negatif': '43,9%', 'Netral': '3,9%', 'Positif': '52,1%'}, jumlah persen 99.9, Nada hasil model sama dengan nada dari bintang pada 89,7% ulasan. Bint | LULUS |
| SV-07 | FR5-06, FR5-07 | Grafik tren dan kata penentu | hasil SV-06 | Satu grafik tren dan dua grafik kata penentu tampil | 3 grafik tampil (1 tren + 2 kata penentu) | LULUS |
| SV-08 | FR5-08 | Saring daftar per nada | hasil SV-06 | Jumlah baris daftar sama dengan jumlah ulasan nada itu di ringkasan | Positif: daftar 318, ringkasan 318; Negatif: daftar 268, ringkasan 268 | LULUS |
| SV-09 | FR5-08 | Urutkan daftar | hasil SV-06 | Daftar tetap tampil tanpa galat dan jumlah baris tidak berubah | baris sebelum 268, sesudah 268 | LULUS |
| SV-10 | FR5-09, NFR5-04 | Unduh hasil CSV | hasil SV-06 | CSV terunduh, kolomnya tanggal, bintang, nada, keyakinan, disukai, dibalas, ulasan, tanpa nama pengulas, jumlah baris sama dengan ulasan yang diambil | suara-rakyat_app.bpjs.mobile_20261108-20261114.csv, kolom ['tanggal', 'bintang', 'nada', 'keyakinan', 'disukai', 'dibalas', 'ulasan'], 610 baris data | LULUS |
| SV-11 | FR5-06 | Rentang panjang memakai tren mingguan | com.Info_BMKG, 1 Jan 2026 sampai hari ini | Dashboard tampil dengan grafik tren (per minggu karena rentang lebih dari 62 hari) | 550 ulasan dibaca, 3 grafik | LULUS |
| SV-12 | FR5-03 | Aplikasi ramai melewati batas 10.000 ulasan | com.bpjstku, 90 hari | Peringatan batas 10.000 ulasan muncul dan dashboard tetap tampil | peringatan: Pencarian dibatasi 10.000 ulasan terbaru. Ulasan tertua yang terambil bertanggal 05/10/2026, jadi ulasan sebel, 9.999 ulasan dibaca | LULUS |
| SV-13 | NFR5-01 | Dibuka di layar HP | - | Tidak ada bagian yang perlu digeser ke samping | lebar isi 390 px, lebar layar 390 px | LULUS |
| SV-14 | NFR5-02 | Waktu tunggu pantau 7 hari | app.bpjs.mobile, 7 hari | Di bawah 30 detik | 4.9 detik untuk 610 ulasan | LULUS |
