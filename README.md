# Suara Rakyat

Web untuk membaca nada ulasan aplikasi layanan publik (Mobile JKN, JMO, SatuSehat, MyPertamina, KAI Access, Info BMKG). Tulis satu ulasan, pilih salah satu dari tiga model, lalu web menampilkan label negatif, netral, atau positif, probabilitasnya, kata yang paling mendorong hasil itu, dan pendapat dua model lainnya.

Projek AOL mata kuliah Software Engineering. Tim: Nehemiah, Marcel, Wilson, Hans, Daniel.

Web: `[?]` (diisi setelah deploy Vercel)

## Tiga model di web

Semua dites di 36.227 ulasan unik yang tidak pernah dilihat saat training.

| Model | Fitur | Val macro-F1 | Test macro-F1 | Akurasi | Polaritas terbalik |
|---|---|---|---|---|---|
| Linear SVM (default) | kata + karakter | 0,665 | **0,668** | 82,7% | 6,6% |
| Logistic Regression | kata + karakter | 0,659 | 0,663 | 82,1% | 7,0% |
| Naive Bayes (Multinomial) | kata | 0,647 | 0,651 | 79,6% | 7,4% |

"Polaritas terbalik" artinya ulasan negatif terbaca positif atau sebaliknya. Rentang bootstrap 95% untuk macro-F1 Linear SVM: 0,662 sampai 0,674.

Ketiganya dipilih dari 27 konfigurasi yang diadu (tabel lengkap di `ml/reports/results.md`). Beda Linear SVM dengan SVM fitur kata saja tidak signifikan (selisih bootstrap 95%: -0,001 sampai 0,005). Beda dengan Complement Naive Bayes signifikan (0,027 sampai 0,037).

Ketiga model memakai satu mesin fitur yang sama, jadi satu request menghitung fitur sekali lalu menjalankan ketiganya. Rata-rata di laptop: sekitar 0,7 ms untuk tiga model sekaligus.

## Data dan cara membersihkannya

Sumber: IGAR v3 dari Mendeley Data, file `Rating_labeled.csv`, 617.722 ulasan Google Play tahun 2012 sampai 2023.

Temuan audit (`ml/reports/data_audit.json`):

- Label murni dari bintang. Bintang 1-2 jadi negatif, 3 netral, 4-5 positif.
- 234.107 baris adalah duplikat persis. Kebanyakan ulasan pendek seperti "mantap" dan "bagus".
- Setelah teks dinormalisasi tersisa 362.292 teks unik. Sebanyak 1.005 teks labelnya seri dan dibuang, jadi total 361.287.

Kalau duplikat dibiarkan, "mantap" bisa muncul di train dan test sekaligus. Skor jadi terlihat tinggi padahal model cuma hafal. Karena itu tiap teks unik dibagi ke train, validation, atau test berdasarkan hash md5 dari teks ternormalisasi (80/10/10). Teks yang sama pasti masuk kelompok yang sama.

Normalisasi (`ml/suara_ml/textnorm.py`): NFKC, huruf kecil, URL dibuang, huruf yang berulang 3 kali atau lebih dipangkas jadi 2, token huruf/angka dan emoji, lalu 84 singkatan umum dibakukan (gak jadi tidak, bgt jadi banget, dan seterusnya). Kamus singkatan menaikkan macro-F1 validation sedikit (0,664 dibanding 0,661 tanpa kamus).

## Kenapa angkanya tidak 0,9

Label bintang itu berisik. Teks "mantap" diberi bintang negatif 295 kali dan netral 324 kali. Untuk 268.270 ulasan yang teksnya muncul berulang, tebakan paling sempurna yang bisa dibuat dari teks cuma mencapai macro-F1 0,670. Sebanyak 92% ulasan bintang 3 di kelompok itu punya teks yang mayoritasnya bukan netral. Detail di `ml/reports/label_noise.json`.

Geser bias kelas (dipilih di validation) menaikkan F1 netral Linear SVM di test dari 0,09 ke 0,27, dengan biaya akurasi turun dari 85,0% ke 82,7%.

## Cara model dipilih

1. Semua model dilatih di train (288.775 teks).
2. Untuk tiap model, geser bias kelas dicari di validation supaya macro-F1 maksimal, lalu suhu softmax dikalibrasi di validation.
3. Urutan model ditentukan macro-F1 validation. Test baru dihitung setelah itu dan tidak dipakai untuk memilih.

## Dari Python ke web

Bobot tiga model, idf, dan kosakata diekspor ke `web/model/` (sekitar 16 MB). Rumus fitur ditulis ulang di TypeScript (`web/lib/textnorm.ts`, `web/lib/model.ts`), jadi web tidak butuh Python, GPU, atau layanan luar.

Uji paritas (`npm run parity`) membandingkan prediksi TypeScript dengan Python untuk tiap model di 3.018 teks, termasuk 18 teks jebakan seperti emoji, huruf unicode aneh, URL, dan teks kosong. Hasil terakhir: 0 label berbeda di ketiga model, selisih probabilitas maksimal 0,00000065.

## Cerita scroll

Bagian atas halaman adalah cerita 4 babak yang bergerak mengikuti scroll (`web/components/ScrollStory.tsx`). Ada dua mode:

- **Mode kode** (default): adegan kerumunan warga, bendera merah putih, dan balon suara yang tersusun jadi proporsi negatif 59%, netral 7%, positif 34% digambar langsung di canvas.
- **Mode video**: kalau folder `web/public/frames/` berisi frame, adegan diganti frame video yang diputar sesuai posisi scroll.

Cara memasang video (misalnya hasil Google Whisk Animate, MP4 8 detik 16:9):

```bash
# taruh video di tools/frames/media/ dengan nama scene-1.mp4, scene-2.mp4, scene-3.mp4
cd tools/frames
npm install
npm run frames
```

Script memotong tiap video jadi 96 frame WebP (12 fps) dalam dua ukuran: 1280 px untuk desktop dan 640 px untuk HP. Web otomatis memakai frame itu setelah build ulang.

Uji kemulusan di Chromium dengan GPU Intel Iris Xe, scroll roda mouse naik turun sepanjang cerita:

| Mode | Layar | Median waktu frame | Frame di atas 33 ms |
|---|---|---|---|
| Kode | desktop 1440×900 | 16,7 ms | 0 dari 368 |
| Kode | HP 390×844 | 16,7 ms | 0 dari 355 |
| Video (frame uji) | HP 390×844, render software | 16,7 ms | 1 dari 306 |

## Struktur folder

```
ml/
  suara_ml/          normalisasi teks, fitur TF-IDF, metrik
  scripts/           01_prepare sampai 06_label_noise, generator notebook Colab
  notebooks/         indobert_colab.ipynb (fine-tune IndoBERT di GPU Colab)
  reports/           audit data, hasil semua run, seleksi final, confusion matrix
web/
  app/               halaman dan route /api/predict
  components/        cerita scroll, formulir + pilihan model, panel bukti
  lib/               port TypeScript normalisasi dan inferensi 3 model
  model/             bobot model hasil export
  data/              ringkasan dataset dan papan peringkat untuk halaman
  scripts/           uji paritas
tools/frames/        pemotong video jadi frame untuk cerita scroll
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

Notebook `ml/notebooks/indobert_colab.ipynb` melatih IndoBERTweet di split yang sama persis. Dirancang untuk sekali Run all lalu ditinggal: izin Google Drive dan upload data ada di sel paling atas, hasil langsung dicadangkan ke Drive, lalu dua zip terunduh otomatis. Logit validation dan test dari zip hasil dimasukkan ke `data/scores/`, lalu `04_final.py` otomatis membandingkannya.

Notebook sudah diuji jalan dari awal sampai akhir di laptop dengan model mini (transformers 5.17, torch 2.14). Status training IndoBERT penuh: belum dijalankan.

## Batasan

- Label berasal dari bintang, bukan anotasi manusia.
- Model membaca pola kata. Sarkasme dan konteks panjang bisa salah baca.
- Data berhenti di 2023. Istilah atau fitur aplikasi yang lebih baru bisa belum dikenali.
- Info BMKG dan KAI Access datanya sedikit, jadi skor per aplikasi keduanya paling goyah.
- Hasil model bukan penilaian resmi instansi mana pun.

## Sumber data

Isnan, M. dan Pardamean, B. (2025). IGAR: Indonesian Government App Review Dataset. Mendeley Data, V3. https://doi.org/10.17632/7zryc6k76z.3. Lisensi CC BY 4.0.

Perubahan dari data asli: teks dinormalisasi, duplikat digabung dengan label mayoritas, teks berlabel seri dibuang. Contoh teks ulasan yang ikut di repo sudah disamarkan (deret angka 6 digit atau lebih dan alamat email).
