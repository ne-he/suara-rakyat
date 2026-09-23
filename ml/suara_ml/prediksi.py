"""Prediksi dari model yang benar-benar dipakai produk, untuk skrip evaluasi tambahan.

- Model web (SVM, Logistic Regression, Naive Bayes): lewat web/scripts/label-file.ts, jadi kodenya
  sama persis dengan API di Vercel (normalisasi, fitur, geser bias).
- IndoBERTweet int8: lewat fungsi inferensi di indobert-api/app.py (prep, tokenizer, bias, suhu sama).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
API = ROOT / "indobert-api"
LABELS = ["negative", "neutral", "positive"]
WEB_IDS = ["svm", "logreg", "nb"]


def web_models(texts: list[str]) -> dict[str, list[str]]:
    """Label dari 3 model web untuk tiap teks."""
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "masuk.json", Path(d) / "keluar.json"
        src.write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        npx = "npx.cmd" if os.name == "nt" else "npx"
        subprocess.run([npx, "tsx", "scripts/label-file.ts", str(src), str(dst)], cwd=WEB, check=True, capture_output=True)
        rows = json.loads(dst.read_text(encoding="utf-8"))
    return {m: [r[m]["label"] for r in rows] for m in WEB_IDS}


@lru_cache(maxsize=1)
def _api():
    spec = importlib.util.spec_from_file_location("indobert_app", API / "app.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(API))
    spec.loader.exec_module(mod)
    return mod


def indobert_available() -> bool:
    return (API / "model" / "model-int8.onnx").exists() and (API / "model" / "tokenizer.json").exists()


def indobert(texts: list[str], batch: int = 32) -> list[str]:
    """Label IndoBERTweet int8. Teks diurutkan menurut panjang supaya padding per batch kecil."""
    api = _api()
    prepped = [api.prep(t) for t in texts]
    order = np.argsort([len(t) for t in prepped], kind="stable")
    out = [""] * len(texts)
    for i in range(0, len(order), batch):
        idx = order[i : i + batch]
        probs = api.probs_of([prepped[j] for j in idx])
        for j, p in zip(idx, probs):
            out[j] = LABELS[int(p.argmax())]
    return out
