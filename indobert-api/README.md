---
title: Suara Rakyat IndoBERTweet
emoji: 📣
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Server IndoBERTweet Suara Rakyat

Server kecil (FastAPI + onnxruntime) untuk model IndoBERTweet versi ONNX int8. Web Suara Rakyat memanggilnya lewat route `/api/predict-indobert`, jadi browser tidak pernah bicara langsung ke server ini.

Blok YAML di atas hanya dipakai kalau folder ini diunggah sebagai Space Docker di Hugging Face.

## Isi folder

| File | Fungsi |
|---|---|
| `app.py` | endpoint `GET /` (cek hidup) dan `POST /predict` |
| `config.json` | urutan label, geser bias, dan suhu hasil tuning validation (dibuat `ml/scripts/05_export_web.py`) |
| `model/` | `model-int8.onnx` (111 MB) dan `tokenizer.json`, tidak ikut GitHub |
| `Dockerfile` | resep container untuk Hugging Face Spaces atau Render |

## Jalan di laptop

```bash
# dari root repo, salin model hasil Colab
mkdir -p indobert-api/model
cp data/indobert/suara_indobert_onnx_int8/model-int8.onnx indobert-api/model/
cp data/indobert/suara_indobert_onnx_int8/tokenizer/tokenizer.json indobert-api/model/

cd indobert-api
pip install -r requirements.txt
uvicorn app:app --port 7860
```

Lalu di `web/.env.local` isi `INDOBERT_URL=http://127.0.0.1:7860` dan jalankan ulang web.

Contoh panggilan:

```bash
curl -X POST http://127.0.0.1:7860/predict -H "Content-Type: application/json" -d "{\"text\": \"otp tidak masuk\"}"
```

## Keluaran

```json
{
  "model": "indobert",
  "label": "negative",
  "probs": {"negative": 0.93, "neutral": 0.05, "positive": 0.02},
  "tokens": [{"token": "otp", "weight": 0.01}],
  "explained": true,
  "ms": 120.5
}
```

`weight` tiap kata = seberapa turun peluang label terpilih kalau kata itu dihapus. Positif berarti kata itu mendorong ke label tersebut.
