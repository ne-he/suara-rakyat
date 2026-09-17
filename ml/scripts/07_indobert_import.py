"""Impor hasil IndoBERTweet dari Colab dan perbaiki urutan barisnya.

Masalah di run Colab 17 Sep 2026 (transformers 5.16): train_sampling_strategy="group_by_length"
ikut dipakai Trainer.predict, jadi logits val/test tersimpan dalam urutan acak LengthGroupedSampler,
bukan urutan data. Skor yang tercetak di notebook (macro-F1 0,333) salah karena itu.
Sampler tersebut memakai generator dengan seed tetap (args.seed = 42), jadi urutannya bisa dibangun
ulang persis: tokenisasi ulang, hitung panjang token, panggil fungsi pengelompokan yang sama.
Bukti benar: macro-F1 dan akurasi val hasil pemulihan harus sama dengan eval_* di log training.

Butuh: torch, transformers, tokenizers, emoji, onnxruntime (lihat ml/requirements-indobert.txt).
Pakai:  python ml/scripts/07_indobert_import.py [folder_hasil_unzip] [folder_onnx_unzip]
Output: data/scores/indobertweet_{val,test}.npy + _keys.parquet, ml/reports/indobert_import.json
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

import emoji
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoTokenizer
from transformers.trainer_pt_utils import get_length_grouped_indices

ROOT = Path(__file__).resolve().parents[2]
HASIL = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "indobert" / "suara_indobert_hasil"
ONNX = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "indobert" / "suara_indobert_onnx_int8"
SCORES = ROOT / "data" / "scores"
REPORTS = ROOT / "ml" / "reports"
LABELS = ["negative", "neutral", "positive"]
RUN = "indobertweet"

# sama persis dengan sel 3 notebook
URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
MENTION_RE = re.compile(r"@\w+")


def prep(t: str) -> str:
    t = str(t).lower()
    t = URL_RE.sub("HTTPURL", t)
    t = MENTION_RE.sub("@USER", t)
    t = emoji.demojize(t, delimiters=(" ", " "))
    return " ".join(t.split())


def main() -> None:
    run = json.loads((HASIL / f"{RUN}_run.json").read_text(encoding="utf-8"))
    evals = [e for e in run["log_history"] if "eval_macro_f1" in e]
    best = max(evals, key=lambda e: e["eval_macro_f1"])  # load_best_model_at_end memakai metrik ini
    eval_batch = 256
    seed = 42
    max_len = run["max_len"]

    tok = AutoTokenizer.from_pretrained(ONNX / "tokenizer")
    df = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "text", "label", "split"])
    report: dict = {"source_run": {k: v for k, v in run.items() if k != "log_history"}, "best_epoch_log": best}
    SCORES.mkdir(parents=True, exist_ok=True)
    aligned_all = {}

    for split in ["val", "test"]:
        frame = df[df["split"] == split].reset_index(drop=True)
        keys = pd.read_parquet(HASIL / f"{RUN}_{split}_keys.parquet")["key"]
        assert (keys.values == frame["key"].values).all(), f"urutan kunci {split} tidak sama dengan data lokal"
        enc = tok([prep(t) for t in frame["text"]], truncation=True, max_length=max_len)
        lengths = [len(ids) for ids in enc["input_ids"]]
        order = get_length_grouped_indices(lengths, eval_batch, generator=torch.Generator().manual_seed(seed))
        logits = np.load(HASIL / f"{RUN}_{split}.npy")
        assert len(order) == len(logits) == len(frame)
        aligned = np.empty_like(logits)
        aligned[np.asarray(order)] = logits  # baris ke-i hasil predict = data ke-order[i]
        y = frame["label"].map(LABELS.index).to_numpy()
        pred = aligned.argmax(1)
        report[split] = {
            "macro_f1_as_saved": round(float(f1_score(y, logits.argmax(1), average="macro")), 4),
            "macro_f1_recovered": round(float(f1_score(y, pred, average="macro")), 6),
            "accuracy_recovered": round(float(accuracy_score(y, pred)), 6),
        }
        aligned_all[split] = (aligned, frame, y)
        print(split, report[split])

    ok = abs(report["val"]["macro_f1_recovered"] - best["eval_macro_f1"]) < 1e-4 and abs(
        report["val"]["accuracy_recovered"] - best["eval_accuracy"]
    ) < 1e-4
    report["recovery_verified"] = ok
    print("cocok dengan log training:", ok, "| log:", round(best["eval_macro_f1"], 6), round(best["eval_accuracy"], 6))
    if not ok:
        (REPORTS / "indobert_import.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit("pemulihan urutan tidak terbukti, skor tidak disimpan")

    for split, (aligned, frame, _) in aligned_all.items():
        np.save(SCORES / f"{RUN}_{split}.npy", aligned.astype(np.float32))
        frame[["key"]].to_parquet(SCORES / f"{RUN}_{split}_keys.parquet", index=False)

    # versi ONNX int8 (yang realistis untuk dipasang di server CPU): cek kesamaan dan kecepatan di laptop
    if (ONNX / "model-int8.onnx").exists():
        import onnxruntime as ort

        sess = ort.InferenceSession(str(ONNX / "model-int8.onnx"), providers=["CPUExecutionProvider"])
        aligned, frame, y = aligned_all["test"]
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(len(frame), size=3000, replace=False))
        texts = [prep(t) for t in frame["text"].values[idx]]
        for t in texts[:20]:  # pemanasan
            e = tok([t], truncation=True, max_length=max_len, return_tensors="np")
            sess.run(["logits"], {"input_ids": e["input_ids"].astype("int64"), "attention_mask": e["attention_mask"].astype("int64")})
        preds, t0 = [], time.perf_counter()
        for t in texts:
            e = tok([t], truncation=True, max_length=max_len, return_tensors="np")
            preds.append(sess.run(["logits"], {"input_ids": e["input_ids"].astype("int64"), "attention_mask": e["attention_mask"].astype("int64")})[0][0])
        ms = (time.perf_counter() - t0) / len(texts) * 1000
        preds = np.array(preds)
        report["onnx_int8_sample"] = {
            "n": len(idx),
            "size_mb": round((ONNX / "model-int8.onnx").stat().st_size / 1e6, 1),
            "laptop_cpu_ms_per_review": round(ms, 1),
            "agreement_with_fp32": round(float((preds.argmax(1) == aligned[idx].argmax(1)).mean()), 4),
            "macro_f1_int8": round(float(f1_score(y[idx], preds.argmax(1), average="macro")), 4),
            "macro_f1_fp32_same_rows": round(float(f1_score(y[idx], aligned[idx].argmax(1), average="macro")), 4),
        }
        print("onnx int8:", report["onnx_int8_sample"])

    (REPORTS / "indobert_import.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    shutil.copy(HASIL / f"{RUN}_run.json", REPORTS / f"{RUN}_colab_run.json")
    print("tersimpan:", SCORES / f"{RUN}_val.npy", "dan", REPORTS / "indobert_import.json")


if __name__ == "__main__":
    main()
