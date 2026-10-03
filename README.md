# Suara Rakyat

Web untuk membaca nada ulasan aplikasi layanan publik (Mobile JKN, JMO, SatuSehat, MyPertamina, KAI Access, Info BMKG). Tulis satu ulasan lalu tekan Baca nadanya. Web menampilkan nada negatif, netral, atau positif, seberapa yakin mesinnya dalam kata-kata, dan kata yang paling menentukan hasil. Dibuat untuk orang awam, jadi tidak ada pilihan model atau istilah teknis di layar.

Projek AOL mata kuliah Software Engineering. Tim: Nehemiah, Marcel, Wilson, Hans, Daniel.

Web: https://suara-rakyat-xi.vercel.app

Isi web:

| Halaman | Isi |
|---|---|
| `/` | cerita scroll, pita ulasan asli, panduan tiga langkah, formulir baca satu ulasan, porsi keluhan tiap aplikasi, cara kerja dan batasan dalam bahasa awam |
| `/massal` | tempel atau unggah CSV sampai 1.000 ulasan, ringkasan nada, kata pendorong, saringan per nada, unduh hasil CSV |
| `/dashboard` | ringkasan per aplikasi: porsi nada, rata-rata bintang, hal yang paling sering dikeluhkan dan dipuji, contoh ulasan, tren keluhan per kuartal |
| `/kuesioner` | kuesioner SUS untuk evaluasi subjektif plus alat rekap jawaban tim |

Versi sebelumnya disimpan di branch: `versi-lama` (v1.1), `versi-2`, dan `versi-3` (masih dengan pilihan tiga model dan dashboard perbandingan model).

## Satu model di web, tiga dibandingkan di laporan

Web hanya memakai Linear SVM. Logistic Regression dan Naive Bayes tetap dilatih dan dibandingkan untuk laporan, bobotnya disimpan di `web/model/` untuk uji paritas, tapi tidak ikut dibundel ke server. Alasan memilih Linear SVM selain skor: paling cepat dilatih ulang di antara model yang skornya setara (29 detik lawan 340 detik untuk Logistic Regression), bobot liniernya bisa langsung menunjukkan kata penentu ke pengguna, cukup jalan di server web gratis tanpa GPU, dan hasilnya sama persis dengan versi Python.

Semua dites di 36.227 ulasan unik yang tidak pernah dilihat saat training.

| Model | Fitur | Val macro-F1 | Test macro-F1 | Akurasi | Polaritas terbalik |
|---|---|---|---|---|---|
| Linear SVM (dipakai di web) | kata + karakter | 0,665 | **0,668** | 82,7% | 6,6% |
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

Ketiga model memakai satu mesin fitur yang sama. Kecepatan baca per ulasan di laptop (11th Gen Intel(R) Core(TM) i5-11320H @ 3.20GHz, `npm run bench`): Linear SVM 0,21 ms, Logistic Regression 0,19 ms, Naive Bayes 0,18 ms, ketiganya sekaligus 0,23 ms.

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

## Evaluasi tambahan

Bukti di luar skor macro-F1 biasa. Angkanya dipakai di laporan (`ml/reports/`), tidak lagi ditampilkan di web karena web dibuat untuk orang awam.

**Label yang bertabrakan** (`ml/scripts/11_label_kotor.py`). Ada 3.260 teks unik yang mendapat lebih dari satu label bintang, mencakup 224.664 ulasan. Contoh: kata "lambat" muncul 122 kali, 76 diberi bintang negatif dan 20 diberi bintang positif. Ini batas yang tidak bisa dilewati model mana pun.

**Uji tahan bahasa** (`ml/eval/uji_tahan.csv`, `ml/scripts/12_uji_tahan.py`). 60 kalimat disusun tim untuk menguji salah ketik, bahasa gaul, negasi, sindiran, pujian yang bercampur keluhan, pertanyaan netral, ulasan pendek, dan emoji. Kalimat dan labelnya buatan tim, jadi ini uji tambahan, bukan tolok ukur resmi.

| Model | Akurasi 60 kalimat | Paling lemah di |
|---|---|---|
| IndoBERTweet int8 | 78,3% | pertanyaan dan saran |
| Naive Bayes | 76,7% | pujian campur keluhan |
| Logistic Regression | 71,7% | pujian campur keluhan |
| Linear SVM | 68,3% | pujian campur keluhan dan sindiran |

**Pembanding dari penelitian lain** (`ml/scripts/13_pembanding_luar.py`). Paper resmi dataset IGAR melaporkan kesepakatan label bintang dengan VADER sebesar kappa 0,33 dan kecocokan 58,65%. Hitungan ulang kami dari berkas yang sama: kappa 0,3338 dan kecocokan 58,65%. Baseline paper (TF-IDF 5.000 fitur, LinearSVC bawaan) juga kami jalankan ulang:

| Cara membagi data | F1 tertimbang | Macro-F1 |
|---|---|---|
| Acak, ulasan kembar dibiarkan (mirip setelan paper) | 0,845 | 0,602 |
| Kunci teks, ulasan kembar digabung (setelan kami) | 0,798 | 0,574 |
| Model web kami di setelan kami | 0,830 | 0,668 |

Jadi jarak antara angka paper (0,81 sampai 0,92 per aplikasi) dan angka kami muncul dari dua hal: metrik tertimbang lawan macro, dan ulasan kembar yang bocor antar bagian data. VADER sendiri, kalau dipakai sebagai model di data test kami, hanya mencapai macro-F1 0,437 dengan akurasi 50,4%.

**Dibaca ulang manusia** (`ml/anotasi/`). Pembuat dataset menulis bahwa tiap ulasan hanya dinilai satu orang lewat bintang. `14_anotasi_siapkan.py` menyiapkan 300 ulasan test untuk dibaca ulang lima anggota tim tanpa melihat bintangnya, `15_anotasi_hitung.py` menghitung kappa Fleiss antar pembaca dan skor tiap model terhadap label pembaca.

**Cosine similarity** (`ml/scripts/17_cosine.py`, `ml/reports/cosine.json`). Dipakai dari empat sudut, semua di atas vektor TF-IDF kata yang sudah dinormalisasi L2:

| Sudut | Hasil |
|---|---|
| Kemiripan pusat kelas di data latih | negatif dengan netral 0,92, netral dengan positif 0,61, negatif dengan positif 0,53. Ulasan netral nyaris tidak bisa dibedakan dari ulasan negatif, ini penjelasan kenapa F1 netral paling rendah |
| Tetangga terdekat (5.000 ulasan uji lawan 288.775 ulasan latih) | median kemiripan maksimum 0,47, hanya 2,6% ulasan uji punya kembaran vektor di data latih. Tebakan dari 10 tetangga terdekat mencapai macro-F1 0,591, Linear SVM 0,666 di sampel yang sama |
| Porsi nada per aplikasi, bintang lawan tebakan Linear SVM | cosine 0,993 sampai 0,9996 per aplikasi, rata-rata 0,993 per aplikasi per kuartal. Ringkasan nada di cek massal bisa dipercaya walau tebakan per ulasan kadang keliru |
| Kesepakatan antar model | Linear SVM dan Logistic Regression rata-rata cosine peluang 0,992 dengan label sama 95,4%. Dengan Naive Bayes 0,967 (89,3%), dengan IndoBERTweet int8 0,966 (89,1%) |

**Pengujian skenario** (`tests/skenario/`). 32 skenario black box dijalankan otomatis di Chromium lewat Playwright terhadap web live. Hasil terakhir 31 dari 32 lulus. Yang gagal adalah pembatas laju, yang tidak selalu terpicu di Vercel karena disimpan di memori tiap instance. Dua putaran sebelumnya menemukan dua cacat yang sudah diperbaiki: teks tanpa kata yang dikenali sempat diberi nada Positif, dan tombol Baca semua bisa ditekan sebelum ulasan contoh selesai dimuat. Detail di `tests/skenario/README.md`.

**Kebutuhan dan wawancara** (`docs/`). Kebutuhan fungsional dan nonfungsional beserta ketertelusurannya ke skenario uji ada di `docs/kebutuhan-pengguna.md`. Pedoman wawancara pakar dan uji pakai pengguna ada di `docs/wawancara/`.

## Cara model dipilih

1. Semua model dilatih di train (288.775 teks).
2. Untuk tiap model, geser bias kelas dicari di validation supaya macro-F1 maksimal, lalu suhu softmax dikalibrasi di validation.
3. Urutan model ditentukan macro-F1 validation. Test baru dihitung setelah itu dan tidak dipakai untuk memilih.

## Dari Python ke web

Bobot tiga model, idf, dan kosakata diekspor ke `web/model/`. Fungsi serverless hanya membawa bobot Linear SVM, idf, dan kosakata. Rumus fitur ditulis ulang di TypeScript (`web/lib/textnorm.ts`, `web/lib/model.ts`), jadi web tidak butuh Python, GPU, atau layanan luar.

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
  suara_ml/          normalisasi teks, fitur TF-IDF, metrik, pemanggil model web dan IndoBERT
  scripts/           01_prepare sampai 17_cosine, generator notebook Colab
  eval/              kalimat uji tahan bahasa buatan tim
  anotasi/           lembar anotasi manusia, kunci, dan folder hasil
  notebooks/         indobert_colab.ipynb (fine-tune IndoBERT di GPU Colab)
  reports/           audit data, hasil semua run, seleksi final, confusion matrix
web/
  app/               halaman dan route /api/predict, /api/predict-batch
  components/        cerita scroll, formulir baca ulasan, cek massal, dashboard aplikasi, kuesioner
  lib/               port TypeScript normalisasi dan inferensi model
  model/             bobot model hasil export (web memakai Linear SVM)
  data/              ringkasan dataset, data dashboard per aplikasi, tren, pita ulasan
  scripts/           uji paritas (npm run parity) dan uji kecepatan (npm run bench)
  app/massal, app/dashboard, app/kuesioner    halaman cek massal, dashboard aplikasi, kuesioner SUS
tests/skenario/      pengujian skenario black box (Playwright) dan hasilnya
tools/frames/        pemotong video jadi frame + scenes.json (potongan dan porsi scroll)
indobert-api/        server IndoBERTweet int8 (FastAPI + onnxruntime + Dockerfile)
docs/diagram/        kerangka berpikir, alur praproses, Waterfall, use case, class, sequence, activity (SVG + PNG)
docs/                kebutuhan pengguna, pedoman wawancara pakar dan pengguna
```

Draf laporan dan bahan presentasi ada di folder `laporan/` yang sengaja tidak ikut ke repo publik.

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
python 11_label_kotor.py
python 12_uji_tahan.py
python 13_pembanding_luar.py
python 14_anotasi_siapkan.py
python 16_dashboard_aplikasi.py
python 17_cosine.py
```

`09_web_extras.py` menyiapkan pita ulasan, data tren per kuartal, dan file contoh untuk cek massal. `16_dashboard_aplikasi.py` menyiapkan data halaman dashboard. Skrip 11 sampai 13 dan 17 menghasilkan bukti tambahan untuk laporan. Skrip 14 membuat lembar anotasi, dan `15_anotasi_hitung.py` dijalankan setelah lembarnya terisi. Skrip 12, 14, dan 16 memanggil model web lewat `web/scripts/label-file.ts`, jadi `npm install` di folder `web` harus sudah dijalankan.

Diagram untuk laporan dibuat terpisah:

```bash
python docs/diagram/buat_diagram.py
```

Web:

```bash
cd web
npm install
npm run parity
npm run bench
npm run dev
```

Pengujian skenario:

```bash
pip install playwright
python -m playwright install chromium
python tests/skenario/jalankan.py                               # web live
python tests/skenario/jalankan.py http://localhost:3000 lokal   # server lokal
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

IndoBERTweet unggul sekitar 0,02 macro-F1 dan selisihnya signifikan. Model ini tidak dipasang di web karena jauh lebih berat dan butuh server sendiri, jadi dipakai sebagai pembanding di laporan. Versi int8 setuju dengan versi penuh di 96,6% dari 3.000 ulasan test, tapi macro-F1 turun dari 0,637 ke 0,615 di sampel itu (tanpa geser bias).

Catatan soal run Colab: di transformers 5.16 sampler `group_by_length` ikut dipakai `trainer.predict`, jadi logit yang tersimpan teracak urutannya dan skor yang tercetak di notebook (0,333) salah. Sampler itu memakai seed tetap, jadi `ml/scripts/07_indobert_import.py` membangun ulang urutannya. Hasilnya terbukti benar karena macro-F1 dan akurasi validation sama persis dengan log evaluasi saat training (0,63663 dan 85,85%). Notebook sudah diperbaiki: prediksi sekarang memakai DataLoader berurutan dan ada cek otomatis terhadap log training.

Cara mengimpor hasil Colab: unzip kedua file ke `data/indobert/`, lalu

```bash
pip install -r ml/requirements-indobert.txt
python ml/scripts/07_indobert_import.py
python ml/scripts/04_final.py
python ml/scripts/08_bootstrap.py
python ml/scripts/05_export_web.py
```

## Server IndoBERT (untuk evaluasi)

Versi int8 IndoBERTweet bisa dijalankan sebagai server sendiri di folder `indobert-api` (FastAPI + onnxruntime). Sejak v4 web tidak memanggilnya lagi. Fungsi inferensinya dipakai langsung oleh skrip evaluasi (`ml/suara_ml/prediksi.py`) untuk uji tahan bahasa dan lembar anotasi.

Skor versi int8 di test: macro-F1 0,684 (rentang bootstrap 95% 0,677 sampai 0,690), akurasi 82,3%, F1 netral 0,310. Bedanya dengan Linear SVM 0,010 sampai 0,021, jadi tetap unggul. Turun dari versi penuh sekitar 0,008 macro-F1 karena pembulatan int8.

Jalan di laptop:

```bash
mkdir -p indobert-api/model
cp data/indobert/suara_indobert_onnx_int8/model-int8.onnx indobert-api/model/
cp data/indobert/suara_indobert_onnx_int8/tokenizer/tokenizer.json indobert-api/model/
cd indobert-api && pip install -r requirements.txt && uvicorn app:app --port 7860
```

Detail endpoint ada di `indobert-api/README.md`.

Catatan hosting (dicek 18 Sep 2026 di dokumentasi resmi Hugging Face): membuat Space baru bertipe Docker atau Gradio sekarang butuh akun berbayar, hanya Static Space yang gratis. Alternatif gratis yang tersisa: server kecil di Render (mati sendiri setelah 15 menit menganggur, bangun lagi sekitar satu menit) atau menjalankan server ini di laptop saat presentasi.

## Batasan

- Label berasal dari bintang, bukan anotasi manusia.
- Model membaca pola kata. Sarkasme dan konteks panjang bisa salah baca.
- Data berhenti di 2023. Istilah atau fitur aplikasi yang lebih baru bisa belum dikenali.
- Info BMKG dan KAI Access datanya sedikit, jadi skor per aplikasi keduanya paling goyah.
- Bukan suara seluruh warga. Yang terbaca hanya pengguna Android yang menyempatkan menulis ulasan, dan orang yang sedang kesal atau sangat puas lebih sering menulis. Ulasan dari iOS dan media sosial tidak ikut.
- Hasil model bukan penilaian resmi instansi mana pun.
- Pembatas laju 60 permintaan per menit disimpan di memori tiap instance server, jadi di Vercel tidak selalu terpicu. Perlu penyimpan bersama kalau web dipakai lebih luas.
- Cek massal mengirim teks ke server untuk dihitung lalu dibuang. Tidak ada yang disimpan, tapi jangan unggah data pribadi.
- Kuesioner SUS tidak menyimpan jawaban. Rekap dilakukan manual lewat tempel data di halaman yang sama.
- Pita ulasan di halaman depan memakai ulasan asli yang sudah disaring (tanpa angka panjang, tautan, kata kasar, penanda lokasi) lalu dibaca manual satu per satu.

## Sumber data

Isnan, M. dan Pardamean, B. (2025). IGAR: Indonesian Government App Review Dataset. Mendeley Data, V3. https://doi.org/10.17632/7zryc6k76z.3. Lisensi CC BY 4.0.

Artikel datanya: Isnan, M. dan Pardamean, B. (2026). IGAR: Indonesian government applications review for sentiment analysis dataset. Data in Brief, 66, 112708. https://doi.org/10.1016/j.dib.2026.112708

Perubahan dari data asli: teks dinormalisasi, duplikat digabung dengan label mayoritas, teks berlabel seri dibuang. Contoh teks ulasan yang ikut di repo sudah disamarkan (deret angka 6 digit atau lebih dan alamat email).
