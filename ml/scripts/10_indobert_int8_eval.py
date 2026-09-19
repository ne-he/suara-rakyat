"""Evaluasi penuh IndoBERTweet versi ONNX int8 (versi yang dipasang di server) di val dan test.

Versi int8 sedikit berbeda dari versi penuh, jadi geser bias kelasnya di-tune ulang sendiri di
validation lewat 04_final.py (run baru bernama indobertweet_int8).
Inferensi dikelompokkan per panjang token supaya cepat di CPU, lalu dikembalikan ke urutan data.

Butuh: ml/requirements-indobert.txt
Output: data/scores/indobertweet_int8_{val,test}.npy + _keys.parquet, ml/reports/indobert_int8_speed.json
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import emoji
import numpy as np
import onnxruntime as ort
import pandas as pd
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
ONNX = ROOT / "data" / "indobert" / "suara_indobert_onnx_int8"
SCORES = ROOT / "data" / "scores"
RUN = "indobertweet_int8"
MAX_LEN = 128
BATCH = 32
URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
MENTION_RE = re.compile(r"@\w+")


def prep(t: str) -> str:
    t = str(t).lower()
    t = URL_RE.sub("HTTPURL", t)
    t = MENTION_RE.sub("@USER", t)
    t = emoji.demojize(t, delimiters=(" ", " "))
    return " ".join(t.split())


def main() -> None:
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = os.cpu_count() or 4
    sess = ort.InferenceSession(str(ONNX / "model-int8.onnx"), opts, providers=["CPUExecutionProvider"])
    tok = AutoTokenizer.from_pretrained(ONNX / "tokenizer")
    df = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "text", "split"])
    speed = {}
    for split in ["val", "test"]:
        frame = df[df["split"] == split].reset_index(drop=True)
        enc = tok([prep(t) for t in frame["text"]], truncation=True, max_length=MAX_LEN)
        ids = enc["input_ids"]
        order = np.argsort([len(x) for x in ids], kind="stable")
        out = np.zeros((len(ids), 3), dtype=np.float32)
        t0 = time.perf_counter()
        for s in range(0, len(order), BATCH):
            idx = order[s : s + BATCH]
            width = max(len(ids[i]) for i in idx)
            x = np.zeros((len(idx), width), dtype=np.int64)
            m = np.zeros((len(idx), width), dtype=np.int64)
            for r, i in enumerate(idx):
                x[r, : len(ids[i])] = ids[i]
                m[r, : len(ids[i])] = 1
            out[idx] = sess.run(["logits"], {"input_ids": x, "attention_mask": m})[0]
            if s % (BATCH * 200) == 0:
                print(split, s, "/", len(order), round(time.perf_counter() - t0), "dtk", flush=True)
        secs = time.perf_counter() - t0
        speed[split] = {"rows": len(ids), "seconds": round(secs, 1), "ms_per_review_batched": round(secs / len(ids) * 1000, 2)}
        np.save(SCORES / f"{RUN}_{split}.npy", out)
        frame[["key"]].to_parquet(SCORES / f"{RUN}_{split}_keys.parquet", index=False)
        print(split, speed[split], flush=True)
    speed["threads"] = opts.intra_op_num_threads
    speed["batch"] = BATCH
    (ROOT / "ml" / "reports" / "indobert_int8_speed.json").write_text(json.dumps(speed, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
