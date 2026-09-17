# SUARA v1: model sentimen ulasan aplikasi layanan publik

Web kecil untuk membaca nada ulasan aplikasi pemerintah (Mobile JKN, JMO, SatuSehat, MyPertamina, KAI Access, Info BMKG). Tempel satu ulasan, lalu web menampilkan label negatif, netral, atau positif, probabilitasnya, dan kata yang paling mendorong hasil itu.

Ini versi pertama dari projek SUARA untuk mata kuliah Software Engineering. Fokus v1 cuma dua: cari model terbaik secara jujur, lalu jalankan di web.

Web: `[?]` (diisi setelah deploy Vercel)

## Hasil singkat

Model yang dipakai web: **Linear SVM** (C = 0,1) dengan fitur TF-IDF kata 1-2 gram dan karakter 2-5 gram.

| Metrik (test, 36.227 ulasan unik) | Nilai |
|---|---|
| Macro-F1 | **0,668** (bootstrap 95%: 0,662 sampai 0,674) |
| Akurasi | 82,7% |
| F1 negatif / netral / positif | 0,889 / 0,271 / 0,843 |
| Negatif terbaca positif atau sebaliknya | 6,6% |
| Akurasi kalau netral dikesampingkan | 91,1% |
| Waktu prediksi di web | sekitar 0,5 ms per ulasan (setelah model dimuat) |

Ada 27 konfigurasi yang diadu. Potongan papan peringkatnya:

| Model | Fitur | Val macro-F1 | Test macro-F1 |
|---|---|---|---|
| Linear SVM C=0,1 (dipakai web) | kata + karakter | 0,665 | 0,668 |
| Linear SVM C=0,1 | kata | 0,664 | 0,666 |
| Logistic Regression C=2 | kata + karakter | 0,659 | 0,663 |
| LightGBM (30 ribu fitur chi2) | kata | 0,659 | 0,658 |
| Multinomial Naive Bayes | kata | 0,647 | 0,651 |
| Regresi bintang (Ridge) | kata + karakter | 0,643 | 0,646 |
| Complement Naive Bayes | kata | 0,632 | 0,636 |
| Tebak kelas mayoritas | kata | 0,246 | 0,247 |

Tabel lengkap ada di `ml/reports/results.md`. Semua angka di atas sudah memakai geser bias kelas yang di-tune di validation.

Beda SVM kata + karakter dengan SVM kata saja tidak signifikan (selisih bootstrap 95%: -0,001 sampai 0,005). Beda dengan Complement Naive Bayes signifikan (0,027 sampai 0,037).

## Data dan cara membersihkannya

Sumber: IGAR v3 dari Mendeley Data, file `Rating_labeled.csv`, 617.722 ulasan Google Play tahun 2012 sampai 2023.

Temuan audit (`ml/reports/data_audit.json`):

- Label murni dari bintang. Bintang 1-2 jadi negatif, 3 netral, 4-5 positif.
- 234.107 baris adalah duplikat persis. Kebanyakan ulasan pendek seperti "mantap" dan "bagus".
- Setelah teks dinormalisasi tersisa 362.292 teks unik. Sebanyak 1.005 teks labelnya seri (misal satu kali positif, satu kali negatif) dan dibuang, jadi total 361.287.

Kalau duplikat dibiarkan, "mantap" bisa muncul di train dan test sekaligus. Skor jadi terlihat tinggi padahal model cuma hafal. Karena itu tiap teks unik dibagi ke train, validation, atau test berdasarkan hash md5 dari teks ternormalisasi (80/10/10). Teks yang sama pasti masuk kelompok yang sama.

Normalisasi (`ml/suara_ml/textnorm.py`): NFKC, huruf kecil, URL dibuang, huruf yang berulang 3 kali atau lebih dipangkas jadi 2, token huruf/angka dan emoji, lalu 84 singkatan umum dibakukan (gak jadi tidak, bgt jadi banget, dan seterusnya). Kamus singkatan menaikkan macro-F1 validation sedikit (0,664 dibanding 0,661 tanpa kamus).

## Kenapa angkanya tidak 0,9

Label bintang itu berisik. Teks "mantap" diberi bintang negatif 295 kali dan netral 324 kali. Untuk 268.270 ulasan yang teksnya muncul berulang, tebakan paling sempurna yang bisa dibuat dari teks cuma mencapai macro-F1 0,670. Sebanyak 92% ulasan bintang 3 di kelompok itu punya teks yang mayoritasnya bukan netral. Detail di `ml/reports/label_noise.json`.

Jadi kelas netral memang sulit bagi model apa pun yang hanya membaca teks. Geser bias kelas (dipilih di validation) menaikkan F1 netral di test dari 0,09 ke 0,27, dengan biaya akurasi turun dari 85,0% ke 82,7%.

## Cara model dipilih

1. Semua model dilatih di train (288.775 teks).
2. Untuk tiap model, geser bias kelas dicari di validation supaya macro-F1 maksimal, lalu suhu softmax dikalibrasi di validation.
3. Model dengan macro-F1 validation tertinggi dan bisa dijalankan di web dipilih.
4. Test baru dihitung setelah itu. Angka test tidak dipakai untuk memilih.

## Dari Python ke web

Bobot SVM, idf, dan kosakata diekspor ke `web/model/` (sekitar 9 MB). Rumus fitur ditulis ulang di TypeScript (`web/lib/textnorm.ts`, `web/lib/model.ts`), jadi web tidak butuh Python, GPU, atau layanan luar.

Uji paritas membandingkan prediksi TypeScript dengan Python di 3.018 teks (3.000 teks validation plus 18 teks jebakan seperti emoji, huruf unicode aneh, URL, dan teks kosong). Hasil terakhir: 0 label berbeda, selisih probabilitas maksimal 0,0000005.

## Struktur folder

```
ml/
  suara_ml/          normalisasi teks, fitur TF-IDF, metrik
  scripts/           01_prepare sampai 06_label_noise, generator notebook Colab
  notebooks/         indobert_colab.ipynb (fine-tune IndoBERT di GPU Colab)
  reports/           audit data, hasil semua run, seleksi final, confusion matrix
web/
  app/               halaman dan route /api/predict
  components/        form analisis ulasan
  lib/               port TypeScript normalisasi dan inferensi
  model/             bobot model hasil export
  scripts/           uji paritas
```

## Menjalankan ulang

Data mentah tidak ikut di repo. Unduh IGAR v3 dari https://doi.org/10.17632/7zryc6k76z.3 lalu taruh `Rating_labeled.csv` di folder `dataset/`.

```bash
pip install -r ml/requirements.txt
cd ml/scripts
python 01_prepare.py
python 02_features.py
python 03_models.py
python 06_label_noise.py
python 04_final.py
python 05_export_web.py
```

Web:

```bash
cd web
npm install
npm run parity
npm run dev
```

`03_models.py` makan waktu sekitar 1 jam di CPU 8 core. Paling lama LightGBM (18 menit) dan Logistic Regression kata + karakter C=8 (16 menit).

## IndoBERT

Notebook `ml/notebooks/indobert_colab.ipynb` melatih IndoBERTweet di split yang sama persis, lalu menyimpan logit validation dan test. Hasilnya bisa dimasukkan ke `data/scores/` dan otomatis ikut dibandingkan oleh `04_final.py`. Status v1: belum dijalankan.

## Batasan

- Label berasal dari bintang, bukan anotasi manusia.
- Model membaca pola kata. Sarkasme dan konteks panjang bisa salah baca.
- Data berhenti di 2023. Istilah atau fitur aplikasi yang lebih baru bisa belum dikenali.
- Hasil model bukan penilaian resmi instansi mana pun.

## Sumber data

Isnan, M. dan Pardamean, B. (2025). IGAR: Indonesian Government App Review Dataset. Mendeley Data, V3. https://doi.org/10.17632/7zryc6k76z.3. Lisensi CC BY 4.0.

Perubahan dari data asli: teks dinormalisasi, duplikat digabung dengan label mayoritas, teks berlabel seri dibuang. Contoh teks ulasan yang ikut di repo sudah disamarkan (deret angka 6 digit atau lebih dan alamat email).
