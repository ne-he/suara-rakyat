"""Server kecil untuk IndoBERTweet (ONNX int8): satu ulasan masuk, label + probabilitas + kata penentu keluar.

Dipanggil oleh web (route /api/predict-indobert di Vercel), bukan langsung oleh browser.
Jalan di mana saja yang bisa menjalankan Python atau Docker: laptop, Hugging Face Spaces, Render.

Env:
  MODEL_DIR   folder berisi model-int8.onnx dan tokenizer.json (default ./model)
  MODEL_REPO  opsional, repo model Hugging Face (misal ne-he/suara-indobertweet-int8). Kalau MODEL_DIR
              kosong, file diunduh dari sana saat server menyala.
  SUARA_KEY   opsional, kalau diisi setiap request wajib membawa header x-suara-key yang sama
  ORT_THREADS jumlah thread CPU untuk onnxruntime (default 2)
"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
import urllib.request
from pathlib import Path

import emoji
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
MODEL_DIR = Path(os.environ.get("MODEL_DIR", HERE / "model"))
MODEL_REPO = os.environ.get("MODEL_REPO", "")
SUARA_KEY = os.environ.get("SUARA_KEY", "")
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
LABELS: list[str] = CONFIG["labels"]
BIAS = np.array(CONFIG["bias"], dtype=np.float64)
TEMPERATURE = float(CONFIG["temperature"])
MAX_LEN = int(CONFIG["max_len"])
MAX_CHARS = 2000
MAX_WORDS_EXPLAINED = 60  # ulasan lebih panjang tetap diprediksi, tapi kata penentunya tidak dihitung

# sama persis dengan pra-proses saat training (notebook Colab sel 3)
URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
MENTION_RE = re.compile(r"@\w+")


def prep(t: str) -> str:
    t = str(t).lower()
    t = URL_RE.sub("HTTPURL", t)
    t = MENTION_RE.sub("@USER", t)
    t = emoji.demojize(t, delimiters=(" ", " "))
    return " ".join(t.split())


def ensure_model() -> None:
    files = ["model-int8.onnx", "tokenizer.json"]
    if all((MODEL_DIR / f).exists() for f in files):
        return
    if not MODEL_REPO:
        raise RuntimeError(f"model belum ada di {MODEL_DIR} dan MODEL_REPO tidak diisi")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for f in files:
        url = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{f}"
        print("mengunduh", url, flush=True)
        urllib.request.urlretrieve(url, MODEL_DIR / f)


ensure_model()
opts = ort.SessionOptions()
opts.intra_op_num_threads = int(os.environ.get("ORT_THREADS", "2"))
SESSION = ort.InferenceSession(str(MODEL_DIR / "model-int8.onnx"), opts, providers=["CPUExecutionProvider"])
TOKENIZER = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
TOKENIZER.enable_truncation(max_length=MAX_LEN)
TOKENIZER.no_padding()


def probs_of(texts: list[str]) -> np.ndarray:
    enc = TOKENIZER.encode_batch(texts)
    width = max(len(e.ids) for e in enc)
    ids = np.zeros((len(enc), width), dtype=np.int64)
    mask = np.zeros((len(enc), width), dtype=np.int64)
    for r, e in enumerate(enc):
        ids[r, : len(e.ids)] = e.ids
        mask[r, : len(e.ids)] = 1
    logits = SESSION.run(["logits"], {"input_ids": ids, "attention_mask": mask})[0].astype(np.float64)
    z = (logits + BIAS) / TEMPERATURE
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class Body(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_CHARS)


app = FastAPI(title="Suara Rakyat IndoBERTweet", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/")
def health() -> dict:
    return {"ok": True, "model": "indobertweet-int8", "labels": LABELS}


@app.post("/predict")
def predict(body: Body, x_suara_key: str = Header(default="")) -> dict:
    if SUARA_KEY and not secrets.compare_digest(x_suara_key, SUARA_KEY):
        raise HTTPException(status_code=401, detail="kunci salah")
    text = prep(body.text)
    if not text:
        raise HTTPException(status_code=400, detail="teks kosong")
    t0 = time.perf_counter()
    words = text.split(" ")
    explain = 1 < len(words) <= MAX_WORDS_EXPLAINED
    # kata penentu: hapus satu kata, lihat seberapa turun peluang label terpilih (occlusion)
    variants = [text] + ([" ".join(words[:i] + words[i + 1 :]) for i in range(len(words))] if explain else [])
    p = probs_of(variants)
    best = int(p[0].argmax())
    tokens = [
        # tanda baca di ujung kata ikut dibuang supaya tampilannya rapi, bobotnya tetap dari kata aslinya
        {"token": w.strip(".,!?:;\"'()") or w, "weight": round(float(p[0, best] - p[i + 1, best]), 5) if explain else 0.0}
        for i, w in enumerate(words)
    ]
    return {
        "model": "indobert",
        "label": LABELS[best],
        "probs": {l: round(float(p[0, k]), 6) for k, l in enumerate(LABELS)},
        "tokens": tokens,
        "empty": False,
        "explained": explain,
        "ms": round((time.perf_counter() - t0) * 1000, 1),
    }
