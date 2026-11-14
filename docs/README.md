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
| `diagram/waterfall.svg` | Enam tahap Waterfall beserta kegiatan tim, dan lima putaran versi (v1 sampai v5) dari riwayat commit | 1.6 dan 3.3 Metode pengembangan |
| `diagram/use-case.svg` | v5: aktor Pengelola layanan (pemerintah) dan Google Play sebagai sistem luar, include dan extend | 3.4 Perancangan UML |
| `diagram/class-diagram.svg` | v5: `ReviewScraper`, `SentimentClassifier`, `ReviewAnalysis`, `ScrapeResult`, `Prediction`, beserta library dan berkas model | 3.4 Perancangan UML |
| `diagram/sequence-v5.svg` | v5: urutan pesan saat ulasan diambil dan dibaca, termasuk jalur galat dan perulangan per 200 ulasan | 3.4 Perancangan UML |
| `diagram/activity-v5.svg` | v5: aktivitas pantau satu aplikasi dalam tiga jalur: pengelola layanan, app Streamlit, Google Play | 3.4 Perancangan UML |
| `diagram/use-case-v4.svg`, `class-diagram-v4.svg`, `sequence-prediksi.svg`, `activity-massal.svg` | diagram web v4 (Next.js), disimpan untuk riwayat versi | lampiran atau 3.3 riwayat versi |

Tiap SVG punya PNG dengan nama sama untuk ditempel ke dokumen Word atau slide. PNG dibuat lewat
Chromium Playwright pada skala 2 kali, jadi tetap tajam saat dicetak.
