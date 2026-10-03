# Dokumen dan diagram

Gambar untuk laporan dan presentasi. Semuanya dibuat dari satu skrip supaya gampang diperbarui
kalau arsitekturnya berubah, warnanya sama dengan web, dan angkanya dibaca dari berkas hasil
(`ml/reports`, `web/model`, `web/data`), bukan diketik tangan.

```bash
python docs/diagram/buat_diagram.py                 # semua diagram
python docs/diagram/buat_diagram.py use-case        # satu diagram saja
```

Alur praproses butuh data lokal (`models/featurizer_wordchar.joblib` dari skrip 02) dan
`npm install` di folder `web`, karena contoh kalimatnya benar-benar dilewatkan ke fungsi pipeline
dan model web.

| Berkas | Isi | Dipakai di bab |
|---|---|---|
| `diagram/kerangka-berpikir.svg` | Tahapan penelitian dari masalah sampai simpulan, rinci per tahap (praproses, pembagian data, fitur, model, evaluasi, aplikasi), dengan putaran balik kalau model belum memadai | 3.1 Kerangka berpikir |
| `diagram/alur-praproses.svg` | Satu kalimat contoh dilewatkan ke tiap langkah praproses sampai hasil Linear SVM, semua keluaran asli | 3.3 Metode penelitian |
| `diagram/waterfall.svg` | Enam tahap Waterfall beserta kegiatan tim, dan empat putaran versi (v1 sampai v4) dari riwayat commit | 1.6 dan 3.3 Metode pengembangan |
| `diagram/use-case.svg` | Aktor warga, pengelola layanan atau peneliti (generalisasi), dan tim pengembang | 3.4 Perancangan UML |
| `diagram/class-diagram.svg` | Kelas web (komponen, route API, ModelStore, TextNorm) dan pipeline Python | 3.4 Perancangan UML |
| `diagram/sequence-prediksi.svg` | Urutan pesan saat satu ulasan dibaca, termasuk jalur galat | 3.4 Perancangan UML |
| `diagram/activity-massal.svg` | Aktivitas cek banyak ulasan dalam tiga jalur: pengguna, browser, server | 3.4 Perancangan UML |

Tiap SVG punya PNG dengan nama sama untuk ditempel ke dokumen Word atau slide. PNG dibuat lewat
Chromium Playwright pada skala 2 kali, jadi tetap tajam saat dicetak.
