# Dokumen dan diagram

Gambar untuk laporan dan presentasi. Semuanya dibuat dari satu skrip supaya gampang diperbarui
kalau arsitekturnya berubah, dan supaya warnanya sama dengan web.

```bash
python docs/diagram/buat_diagram.py
```

| Berkas | Isi | Dipakai di bab |
|---|---|---|
| `diagram/kerangka-berpikir.svg` | Alur kerja dari masalah sampai simpulan, termasuk umpan balik kalau skor belum cukup | Metode, kerangka berpikir |
| `diagram/use-case.svg` | Aktor warga, tim peneliti, dan server IndoBERTweet beserta use case-nya | Metode, UML |
| `diagram/class-diagram.svg` | Kelas yang berjalan saat ada pengunjung, dibagi tiga paket: web, indobert-api, ml | Metode, UML |
| `diagram/sequence-prediksi.svg` | Urutan pesan saat satu ulasan dibaca, termasuk jalur server IndoBERTweet | Metode, UML |

Tiap SVG punya PNG dengan nama sama untuk ditempel ke dokumen Word. PNG dibuat lewat Chromium
Playwright pada skala 2 kali, jadi tetap tajam saat dicetak.
