"""Generate ml/notebooks/indobert_colab.ipynb (dijalankan di Google Colab GPU T4)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ml" / "notebooks" / "indobert_colab.ipynb"


def md(s: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(keepends=True)}


def code(s: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": s.strip("\n").splitlines(keepends=True),
    }


cells = [
    md(
        """
# SUARA: fine-tune IndoBERT untuk sentimen ulasan IGAR

Notebook ini melatih model transformer di split yang **sama persis** dengan model klasik
(file `igar_prepared.parquet`, kolom `split`). Hasilnya dibandingkan di laptop pakai skor validation.

**Cara pakai**
1. Menu `Runtime` > `Change runtime type` > pilih **T4 GPU** > Save.
2. Klik ikon folder di kiri, upload `igar_prepared.parquet` (atau isi `DATA_URL` di sel konfigurasi).
3. Menu `Runtime` > `Run all`. Perkiraan 45 sampai 90 menit.
4. Di akhir, file `indobert_outputs.zip` otomatis terunduh. Kirim file itu balik.
"""
    ),
    code(
        """
!nvidia-smi -L
import importlib, subprocess, sys
for pkg in ["transformers", "accelerate", "datasets", "emoji"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
import torch, transformers, datasets
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("transformers", transformers.__version__, "datasets", datasets.__version__)
assert torch.cuda.is_available(), "GPU belum aktif: Runtime > Change runtime type > T4 GPU"
"""
    ),
    code(
        """
# ===== Konfigurasi =====
MODEL_NAME = "indolem/indobertweet-base-uncased"   # alternatif: "indobenchmark/indobert-base-p1"
MAX_LEN = 128
EPOCHS = 2
LR = 3e-5
BATCH = 64
SEED = 42
TRAIN_SAMPLE = None      # isi angka (misal 150000) kalau waktu Colab mepet
DATA_URL = ""            # opsional: link langsung ke igar_prepared.parquet
RUN_NAME = MODEL_NAME.split("/")[-1]
LABELS = ["negative", "neutral", "positive"]
"""
    ),
    code(
        """
import os, urllib.request
import pandas as pd
PATH = "igar_prepared.parquet"
if not os.path.exists(PATH) and DATA_URL:
    urllib.request.urlretrieve(DATA_URL, PATH)
if not os.path.exists(PATH):
    from google.colab import files
    print("Upload igar_prepared.parquet")
    files.upload()
df = pd.read_parquet(PATH)
print(df.shape)
print(df.groupby(["split", "label"]).size().unstack())
"""
    ),
    code(
        """
import re, emoji
URL_RE = re.compile(r"(https?://\\S+|www\\.\\S+)")
MENTION_RE = re.compile(r"@\\w+")

def prep(t: str) -> str:
    t = str(t).lower()
    t = URL_RE.sub("HTTPURL", t)
    t = MENTION_RE.sub("@USER", t)
    if "indobertweet" in MODEL_NAME:
        t = emoji.demojize(t, delimiters=(" ", " "))
    return " ".join(t.split())

df["input"] = df["text"].map(prep)
df["labels"] = df["label"].map(LABELS.index)
train_df = df[df.split == "train"]
if TRAIN_SAMPLE:
    train_df = train_df.sample(n=TRAIN_SAMPLE, random_state=SEED)
val_df, test_df = df[df.split == "val"], df[df.split == "test"]
print(len(train_df), len(val_df), len(test_df))
print(val_df["input"].head(5).tolist())
"""
    ),
    code(
        """
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DataCollatorWithPadding

tok = AutoTokenizer.from_pretrained(MODEL_NAME)

def to_ds(frame):
    ds = Dataset.from_pandas(frame[["input", "labels"]].reset_index(drop=True))
    return ds.map(lambda b: tok(b["input"], truncation=True, max_length=MAX_LEN), batched=True, remove_columns=["input"])

ds_train, ds_val, ds_test = to_ds(train_df), to_ds(val_df), to_ds(test_df)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=3, id2label=dict(enumerate(LABELS)), label2id={l: i for i, l in enumerate(LABELS)}
)
"""
    ),
    code(
        """
import numpy as np
from sklearn.metrics import f1_score, accuracy_score
from transformers import Trainer, TrainingArguments

def compute_metrics(p):
    pred = p.predictions.argmax(-1)
    return {"macro_f1": f1_score(p.label_ids, pred, average="macro"), "accuracy": accuracy_score(p.label_ids, pred)}

args = TrainingArguments(
    output_dir="ckpt",
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    save_total_limit=1,
    learning_rate=LR,
    per_device_train_batch_size=BATCH,
    per_device_eval_batch_size=256,
    num_train_epochs=EPOCHS,
    warmup_ratio=0.06,
    weight_decay=0.01,
    fp16=True,
    group_by_length=True,
    logging_steps=200,
    dataloader_num_workers=2,
    report_to="none",
    seed=SEED,
)
trainer = Trainer(
    model=model, args=args, train_dataset=ds_train, eval_dataset=ds_val,
    data_collator=DataCollatorWithPadding(tok), compute_metrics=compute_metrics,
)
trainer.train()
"""
    ),
    code(
        """
import json, time
from sklearn.metrics import classification_report
os.makedirs("indobert_outputs", exist_ok=True)
out = {"model": MODEL_NAME, "epochs": EPOCHS, "lr": LR, "batch": BATCH, "max_len": MAX_LEN, "train_rows": len(train_df)}
for name, ds, frame in [("val", ds_val, val_df), ("test", ds_test, test_df)]:
    t0 = time.time()
    logits = trainer.predict(ds).predictions.astype("float32")
    out[f"{name}_seconds"] = round(time.time() - t0, 1)
    np.save(f"indobert_outputs/{RUN_NAME}_{name}.npy", logits)
    frame[["key"]].to_parquet(f"indobert_outputs/{RUN_NAME}_{name}_keys.parquet", index=False)
    y = frame["labels"].to_numpy()
    out[f"{name}_macro_f1"] = float(f1_score(y, logits.argmax(-1), average="macro"))
    print(name, classification_report(y, logits.argmax(-1), target_names=LABELS, digits=4))
out["log_history"] = trainer.state.log_history
json.dump(out, open(f"indobert_outputs/{RUN_NAME}_run.json", "w"), indent=2)
print({k: v for k, v in out.items() if k != "log_history"})
"""
    ),
    code(
        """
# Simpan model (dipakai kalau IndoBERT yang menang dan mau dideploy)
trainer.save_model(f"indobert_outputs/model_{RUN_NAME}")
tok.save_pretrained(f"indobert_outputs/model_{RUN_NAME}")
!zip -qr indobert_outputs.zip indobert_outputs -x "indobert_outputs/model_*"
!zip -qr indobert_model.zip indobert_outputs/model_{RUN_NAME}
!ls -la *.zip
from google.colab import files
files.download("indobert_outputs.zip")
"""
    ),
    md(
        """
`indobert_model.zip` (sekitar 450 MB) sengaja tidak otomatis diunduh. Unduh manual dari panel file
hanya kalau diminta, karena cuma dibutuhkan kalau IndoBERT yang dipilih buat deploy.

Sel di bawah opsional: bikin versi ONNX int8 (lebih kecil dan cepat di CPU) plus cek apakah
prediksinya masih sama dengan model aslinya. Kalau sel ini error, hasil utama di atas tetap aman.
"""
    ),
    code(
        """
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "onnx", "onnxruntime"], check=True)
    import onnxruntime as ort
    from onnxruntime.quantization import QuantType, quantize_dynamic

    m = trainer.model.float().cpu().eval()
    dummy = tok(["contoh ulasan aplikasi"], return_tensors="pt")
    export_kw = dict(
        input_names=["input_ids", "attention_mask"], output_names=["logits"],
        dynamic_axes={"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"}, "logits": {0: "b"}},
        opset_version=17,
    )
    try:
        torch.onnx.export(m, (dummy["input_ids"], dummy["attention_mask"]), "suara.onnx", dynamo=False, **export_kw)
    except TypeError:
        torch.onnx.export(m, (dummy["input_ids"], dummy["attention_mask"]), "suara.onnx", **export_kw)
    quantize_dynamic("suara.onnx", "suara-int8.onnx", weight_type=QuantType.QInt8)
    sess = ort.InferenceSession("suara-int8.onnx", providers=["CPUExecutionProvider"])

    sub = test_df.sample(n=3000, random_state=SEED)
    fp_logits = np.load(f"indobert_outputs/{RUN_NAME}_test.npy")[test_df.index.get_indexer(sub.index)]
    preds, t0 = [], time.time()
    for text in sub["input"]:
        enc = tok([text], truncation=True, max_length=MAX_LEN, return_tensors="np")
        out = sess.run(["logits"], {"input_ids": enc["input_ids"].astype("int64"), "attention_mask": enc["attention_mask"].astype("int64")})[0]
        preds.append(out[0])
    ms = (time.time() - t0) / len(sub) * 1000
    preds = np.array(preds)
    onnx_info = {
        "int8_mb": round(os.path.getsize("suara-int8.onnx") / 1e6, 1),
        "cpu_ms_per_review": round(ms, 1),
        "agreement_with_fp": float((preds.argmax(1) == fp_logits.argmax(1)).mean()),
        "int8_macro_f1_sample": float(f1_score(sub["labels"], preds.argmax(1), average="macro")),
        "fp_macro_f1_sample": float(f1_score(sub["labels"], fp_logits.argmax(1), average="macro")),
    }
    print(onnx_info)
    json.dump(onnx_info, open("onnx_info.json", "w"), indent=2)
    tok.save_pretrained("onnx_tokenizer")
    subprocess.run(["zip", "-qr", "indobert_onnx_int8.zip", "suara-int8.onnx", "onnx_tokenizer", "onnx_info.json"], check=True)
    files.download("onnx_info.json")
    print("indobert_onnx_int8.zip siap di panel file (unduh kalau diminta)")
except Exception as e:
    print("ONNX dilewati:", repr(e))
"""
    ),
]

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT)
