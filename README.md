# Suara Rakyat

Web untuk membaca nada ulasan aplikasi layanan publik (Mobile JKN, JMO, SatuSehat, MyPertamina, KAI Access, Info BMKG). Tulis satu ulasan, pilih salah satu dari tiga model, lalu web menampilkan label negatif, netral, atau positif, probabilitasnya, kata yang paling mendorong hasil itu, dan pendapat dua model lainnya.

Projek AOL mata kuliah Software Engineering. Tim: Nehemiah, Marcel, Wilson, Hans, Daniel.

Web: https://suara-rakyat-xi.vercel.app

Isi web:

| Halaman | Isi |
|---|---|
| `/` | cerita scroll, pita ulasan asli, formulir satu ulasan dengan pilihan model, tren keluhan per kuartal, panel bukti per model, papan perbandingan |
| `/massal` | tempel atau unggah CSV sampai 1.000 ulasan, ringkasan nada, kata pendorong, unduh hasil CSV |
| `/dashboard` | perbandingan semua model: kecepatan, akurasi, presisi, grafik skor vs waktu latih, unduh tabel CSV dan grafik PNG atau SVG |
| `/kuesioner` | kuesioner SUS untuk evaluasi subjektif plus alat rekap jawaban tim |

## Tiga model di web

Semua dites di 36.227 ulasan unik yang tidak pernah dilihat saat training.

| Model | Fitur | Val macro-F1 | Test macro-F1 | Akurasi | Polaritas terbalik |
|---|---|---|---|---|---|
| Linear SVM (default) | kata + karakter | 0,665 | **0,668** | 82,7% | 6,6% |
| Logistic Regression | kata + karakter | 0,659 | 0,663 | 82,1% | 7,0% |
| Naive Bayes (Multinomial) | kata | 0,647 | 0,651 | 79,6% | 7,4% |

"Polaritas terbalik" artinya ulasan negatif terbaca positif atau sebaliknya. Rentang bootstrap 95% untuk macro-F1 Linear SVM: 0,662 sampai 0,674.

Tabel lengkap 29 konfigurasi ada di `ml/reports/results.md`. Selisih macro-F1 test (bootstrap berpasangan 1.000 kali, rentang 95%, `ml/reports/bootstrap_ci.json`):

| Perbandingan | Selisih | Signifikan |
|---|---|---|
| IndoBERTweet dikurangi Linear SVM | 0,019 sampai 0,030 | ya |
| Linear SVM dikurangi Logistic Regression | 0,001 sampai 0,009 | ya, tapi tipis |
| Linear SVM dikurangi Naive Bayes | 0,012 sampai 0,022 | ya |
| Linear SVM kata + karakter dikurangi SVM kata saja | -0,001 sampai 0,005 | tidak |

Ketiga model memakai satu mesin fitur yang sama, jadi satu request menghitung fitur sekali lalu menjalankan ketiganya. Kecepatan baca per ulasan di laptop (11th Gen Intel(R) Core(TM) i5-11320H @ 3.20GHz, `npm run bench`): Linear SVM 0,21 ms, Logistic Regression 0,19 ms, Naive Bayes 0,18 ms, ketiganya sekaligus 0,23 ms.

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
- **Mode video** (aktif sekarang): frame dari 3 klip ilustrasi (jalan menuju Monas, HP dan balon suara, pita negatif/netral/positif) diputar sesuai posisi scroll. Kalau folder `web/public/frames/` dihapus, web kembali ke mode kode.

Cara memasang atau mengganti video:

```bash
# taruh scene1.mp4, scene2.mp4, scene3.mp4 di folder vid/ (root repo)
# atur potongan detik dan porsi scroll di tools/frames/scenes.json
cd tools/frames
npm install
npm run frames
```

Script memotong video jadi frame WebP 12 fps dalam dua ukuran: 1280 px untuk desktop dan 640 px untuk HP. Scene 2 dipotong di detik 6,0 karena setelahnya kamera turun lagi. Scene 3 mendapat porsi scroll dua babak. Total frame sekarang 288 (desktop 9,6 MB, HP 4,7 MB), dimuat bertahap: frame jarang dulu, lalu makin rapat.

Uji kemulusan di Chromium dengan GPU Intel Iris Xe, scroll roda mouse naik turun sepanjang cerita:

| Mode | Layar | Median waktu frame | Frame di atas 33 ms |
|---|---|---|---|
| Video | desktop 1440×900 | 16,7 ms | 2 dari 338 |
| Video | HP 390×844 | 16,7 ms | 1 dari 316 |
| Kode | desktop 1440×900 | 16,7 ms | 0 dari 368 |
| Kode | HP 390×844 | 16,7 ms | 0 dari 355 |

## Struktur folder

```
ml/
  suara_ml/          normalisasi teks, fitur TF-IDF, metrik
  scripts/           01_prepare sampai 10_indobert_int8_eval, generator notebook Colab
  notebooks/         indobert_colab.ipynb (fine-tune IndoBERT di GPU Colab)
  reports/           audit data, hasil semua run, seleksi final, confusion matrix
web/
  app/               halaman dan route /api/predict
  components/        cerita scroll, formulir + pilihan model, panel bukti
  lib/               port TypeScript normalisasi dan inferensi 3 model
  model/             bobot model hasil export
  data/              ringkasan dataset dan papan peringkat untuk halaman
  scripts/           uji paritas (npm run parity) dan uji kecepatan (npm run bench)
  app/massal, app/dashboard, app/kuesioner    halaman cek massal, dashboard model, kuesioner SUS
tools/frames/        pemotong video jadi frame + scenes.json (potongan dan porsi scroll)
indobert-api/        server IndoBERTweet int8 (FastAPI + onnxruntime + Dockerfile)
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
python 08_bootstrap.py
python 05_export_web.py
python 09_web_extras.py
```

`09_web_extras.py` menyiapkan pita ulasan, data tren per kuartal, dan file contoh untuk cek massal.

Web:

```bash
cd web
npm install
npm run parity
npm run bench
npm run dev
```

`03_models.py` makan waktu sekitar 1 jam di CPU 8 core. Paling lama LightGBM (18 menit) dan Logistic Regression kata + karakter C=8 (16 menit).

## IndoBERT (pembanding)

Notebook `ml/notebooks/indobert_colab.ipynb` melatih IndoBERTweet (`indolem/indobertweet-base-uncased`) di split yang sama persis: 2 epoch, learning rate 3e-5, batch 64, panjang maksimal 128 token. Training di GPU T4 Colab makan 15 menit.

| | IndoBERTweet | Linear SVM (web) |
|---|---|---|
| Val macro-F1 | 0,684 | 0,665 |
| Test macro-F1 | **0,692** | 0,668 |
| Test macro-F1 tanpa geser bias | 0,636 | 0,612 |
| Akurasi test | 83,0% | 82,7% |
| F1 netral | 0,323 | 0,271 |
| Waktu latih | 15 menit (GPU T4) | 29 detik (CPU laptop) |
| Kecepatan baca per ulasan (CPU laptop) | 19,6 ms (ONNX int8) | 0,21 ms |
| Ukuran model | 111,3 MB (int8) | sekitar 9 MB bobot + kosakata |

IndoBERTweet unggul sekitar 0,02 macro-F1 dan selisihnya signifikan. Model ini belum dipasang di web karena jauh lebih berat. Versi int8 setuju dengan versi penuh di 96,6% dari 3.000 ulasan test, tapi macro-F1 turun dari 0,637 ke 0,615 di sampel itu (tanpa geser bias).

Catatan soal run Colab: di transformers 5.16 sampler `group_by_length` ikut dipakai `trainer.predict`, jadi logit yang tersimpan teracak urutannya dan skor yang tercetak di notebook (0,333) salah. Sampler itu memakai seed tetap, jadi `ml/scripts/07_indobert_import.py` membangun ulang urutannya. Hasilnya terbukti benar karena macro-F1 dan akurasi validation sama persis dengan log evaluasi saat training (0,63663 dan 85,85%). Notebook sudah diperbaiki: prediksi sekarang memakai DataLoader berurutan dan ada cek otomatis terhadap log training.

Cara mengimpor hasil Colab: unzip kedua file ke `data/indobert/`, lalu

```bash
pip install -r ml/requirements-indobert.txt
python ml/scripts/07_indobert_import.py
python ml/scripts/04_final.py
python ml/scripts/08_bootstrap.py
python ml/scripts/05_export_web.py
```

## Server IndoBERT (opsional)

Model linear cukup ringan untuk ikut di server web. IndoBERTweet tidak, jadi versi int8-nya dijalankan sebagai server sendiri di folder `indobert-api` (FastAPI + onnxruntime), lalu web memanggilnya lewat route `/api/predict-indobert`. Kalau alamat servernya tidak diisi, web tetap jalan dengan tiga model linear saja.

Skor versi int8 di test: macro-F1 0,684 (rentang bootstrap 95% 0,677 sampai 0,690), akurasi 82,3%, F1 netral 0,310. Bedanya dengan Linear SVM 0,010 sampai 0,021, jadi tetap unggul. Turun dari versi penuh sekitar 0,008 macro-F1 karena pembulatan int8.

Jalan di laptop:

```bash
mkdir -p indobert-api/model
cp data/indobert/suara_indobert_onnx_int8/model-int8.onnx indobert-api/model/
cp data/indobert/suara_indobert_onnx_int8/tokenizer/tokenizer.json indobert-api/model/
cd indobert-api && pip install -r requirements.txt && uvicorn app:app --port 7860
```

Lalu isi `web/.env.local` dengan `INDOBERT_URL=http://127.0.0.1:7860` dan jalankan ulang web. Detail endpoint ada di `indobert-api/README.md`.

Catatan hosting (dicek 18 Sep 2026 di dokumentasi resmi Hugging Face): membuat Space baru bertipe Docker atau Gradio sekarang butuh akun berbayar, hanya Static Space yang gratis. Alternatif gratis yang tersisa: server kecil di Render (mati sendiri setelah 15 menit menganggur, bangun lagi sekitar satu menit) atau menjalankan server ini di laptop saat presentasi.

## Batasan

- Label berasal dari bintang, bukan anotasi manusia.
- Model membaca pola kata. Sarkasme dan konteks panjang bisa salah baca.
- Data berhenti di 2023. Istilah atau fitur aplikasi yang lebih baru bisa belum dikenali.
- Info BMKG dan KAI Access datanya sedikit, jadi skor per aplikasi keduanya paling goyah.
- Hasil model bukan penilaian resmi instansi mana pun.
- Cek massal mengirim teks ke server untuk dihitung lalu dibuang. Tidak ada yang disimpan, tapi jangan unggah data pribadi.
- Kuesioner SUS tidak menyimpan jawaban. Rekap dilakukan manual lewat tempel data di halaman yang sama.
- Pita ulasan di halaman depan memakai ulasan asli yang sudah disaring (tanpa angka panjang, tautan, kata kasar, penanda lokasi) lalu dibaca manual satu per satu.

## Sumber data

Isnan, M. dan Pardamean, B. (2025). IGAR: Indonesian Government App Review Dataset. Mendeley Data, V3. https://doi.org/10.17632/7zryc6k76z.3. Lisensi CC BY 4.0.

Perubahan dari data asli: teks dinormalisasi, duplikat digabung dengan label mayoritas, teks berlabel seri dibuang. Contoh teks ulasan yang ikut di repo sudah disamarkan (deret angka 6 digit atau lebih dan alamat email).
