# Pengujian skenario

Pengujian black box berbasis skenario: tiap skenario menirukan satu hal yang dilakukan pengguna,
lalu hasil yang benar-benar terjadi dibandingkan dengan hasil yang diharapkan. Semua dijalankan
otomatis di browser Chromium lewat Playwright, jadi bisa diulang kapan saja dengan hasil yang
sama dan tidak bergantung pada ingatan penguji.

```bash
pip install playwright
python -m playwright install chromium
python tests/skenario/jalankan.py                               # web live
python tests/skenario/jalankan.py http://localhost:3130 lokal   # server lokal
```

Hasilnya tersimpan di `hasil-<nama>.json` (lengkap, dipakai laporan) dan `HASIL-<nama>.md` (tabel).
Kode kebutuhan (FR dan NFR) merujuk ke `docs/kebutuhan-pengguna.md`.

## Cakupan

| Fitur | Skenario |
|---|---|
| Baca satu ulasan | SK-01 sampai SK-09 |
| Cek massal | SK-10 sampai SK-17 |
| Dashboard aplikasi | SK-18 sampai SK-20 |
| Kuesioner SUS | SK-21 sampai SK-23 |
| API, keamanan, kinerja, tampilan, privasi, navigasi | SK-24 sampai SK-32 |

## Putaran pertama (lokal, sebelum perbaikan)

`hasil-lokal-putaran1.json` mencatat putaran pertama apa adanya: 29 dari 31 lulus. Temuannya:

- **Cacat produk (SK-07).** Teks tanpa satu pun kata yang dikenali, misalnya aksara Jawa, tetap
  diberi stempel Positif karena skor model jatuh ke nilai bias. Skenario itu sempat dinyatakan
  lulus karena harapan awalnya hanya "hasil muncul". Setelah ditinjau, tim menilai stempel nada
  untuk teks yang tidak terbaca menyesatkan orang awam. Harapan diubah, web diperbaiki: formulir
  menampilkan "Tidak terbaca" dan cek massal menandai baris itu sebagai tidak terbaca. Skenario
  SK-17 ditambahkan untuk cek massal.
- **Kesalahan skrip uji (SK-22 dan SK-31).** Teks tombol terbaca huruf kapital karena gaya CSS, dan
  pengecekan alamat halaman dilakukan sebelum navigasi selesai. Perilaku web sudah benar.
- **Data uji yang keliru (SK-24).** Teks JSON rusak dibungkus ulang menjadi JSON sah oleh pustaka
  pengujian, jadi yang teruji justru teks kosong. Data diganti menjadi bytes mentah.

Putaran kedua di lokal setelah perbaikan: 32 dari 32 lulus. Hasil terhadap web live ada di
`hasil-live.json`.

## Catatan

- SK-32 (pembatas laju) sengaja paling akhir karena membuat alamat IP penguji ditolak satu menit.
- Pembatas laju disimpan di memori tiap instance server. Di Vercel, permintaan yang tersebar ke
  beberapa instance bisa lolos lebih banyak dari 60 per menit. Batasan ini dicatat di laporan.
- Pengujian model terhadap bahasa sehari-hari (salah ketik, gaul, negasi, sindiran) ada terpisah di
  `ml/eval/uji_tahan.csv` dan `ml/scripts/12_uji_tahan.py`.
