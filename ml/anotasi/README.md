# Anotasi manusia

Label di dataset IGAR berasal dari bintang, dan pembuat datasetnya sendiri menulis bahwa tidak
ada anotator kedua untuk satu ulasan. Bagian ini membaca ulang 300 ulasan dari split test tanpa
melihat bintangnya, supaya kita punya dua angka: seberapa sering pembaca manusia sepakat satu
sama lain, dan seberapa jauh label bintang dari pembacaan manusia.

## Cara kerja

1. `python ml/scripts/14_anotasi_siapkan.py` membuat 5 berkas di `lembar/` dan kunci di `kunci/`.
2. Tiap anggota tim mengambil satu berkas, mengisinya sendiri tanpa berdiskusi, dan tidak membuka
   folder `kunci/` sampai selesai.
3. Berkas yang sudah terisi disalin ke `hasil/` (boleh .xlsx atau .csv, nama bebas asal berbeda).
4. `python ml/scripts/15_anotasi_hitung.py` menghitung kappa Fleiss, kappa tiap pasangan, label
   mayoritas, dan skor tiap model terhadap pembaca manusia.

Hasilnya otomatis muncul di halaman dashboard begitu `web/data/anotasi.json` ada.

## Isi folder

| Folder | Isi |
|---|---|
| `lembar/` | Lembar kosong untuk tiap anotator, ada menu pilihan label dan panduan |
| `kunci/` | Label bintang dan tebakan tiap model, jangan dibuka sebelum mengisi |
| `hasil/` | Lembar yang sudah terisi, dibaca oleh skrip 15 |
