"""Generate ml/notebooks/indobert_colab.ipynb (Google Colab, GPU T4).

Dirancang untuk sekali "Run all" lalu ditinggal:
- semua langkah yang butuh klik (izin Drive, upload data) ada di sel paling atas
- hasil langsung disalin ke Google Drive begitu training selesai (cadangan kalau tab tertutup)
- di akhir dua zip otomatis terunduh
Uji lokal tanpa GPU: set env SUARA_SMOKE=1 (model mini, data kecil).
"""

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
# SUARA RAKYAT: fine-tune IndoBERT untuk sentimen ulasan IGAR

Split data **sama persis** dengan model klasik (kolom `split` di `igar_prepared.parquet`).

## Cara pakai (sekali jalan, lalu boleh ditinggal)
1. Menu **Runtime** > **Change runtime type** > pilih **T4 GPU** > **Save**.
2. Klik ikon **folder** di kiri, seret file `igar_prepared.parquet` ke situ. Tunggu upload selesai.
3. Menu **Runtime** > **Run all**.
4. Muncul jendela izin Google Drive: klik **Connect to Google Drive**, pilih akunmu, klik **Continue** / **Allow**.
5. Kalau sel kedua bilang `DATA OK` dan `GPU OK`, notebook boleh ditinggal.

Supaya unduhan otomatis di akhir jalan: **tab ini jangan ditutup dan laptop jangan tidur**.
Kalau tab keburu tertutup, semua hasil tetap aman di Google Drive folder `suara_rakyat_indobert`.

Perkiraan waktu: 40 sampai 80 menit.

Yang terunduh otomatis di akhir:
- `suara_indobert_hasil.zip` (kecil): logit validation dan test, kunci teks, ringkasan metrik. **Ini yang wajib dikirim balik.**
- `suara_indobert_onnx_int8.zip` (sekitar 110 MB): versi model ringan untuk web, kalau IndoBERT menang.
"""
    ),
    code(
        """
# 1) Persiapan: cek GPU, paket, lingkungan
import importlib.util, json, os, shutil, subprocess, sys, time
SMOKE = os.environ.get("SUARA_SMOKE") == "1"
try:
    from google.colab import drive, files  # noqa: F401
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

for pkg in ["transformers", "accelerate", "datasets", "emoji", "onnx", "onnxruntime"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

import numpy as np, pandas as pd, torch, transformers, datasets
print("torch", torch.__version__, "| transformers", transformers.__version__, "| datasets", datasets.__version__)
if torch.cuda.is_available():
    print("GPU OK:", torch.cuda.get_device_name(0))
elif not SMOKE:
    raise SystemExit("GPU belum aktif. Runtime > Change runtime type > T4 GPU, lalu Run all lagi.")
"""
    ),
    code(
        """
# 2) Konfigurasi + izin Drive + data (semua yang butuh klik ada di sini)
MODEL_NAME = "indolem/indobertweet-base-uncased"   # alternatif: "indobenchmark/indobert-base-p1"
MAX_LEN = 128
EPOCHS = 2
LR = 3e-5
BATCH = 64
SEED = 42
TRAIN_SAMPLE = None        # isi angka (misal 150000) kalau waktu Colab mepet
USE_DRIVE = True           # cadangan hasil ke Google Drive
DRIVE_DIR = "/content/drive/MyDrive/suara_rakyat_indobert"
DATA = "igar_prepared.parquet"
LABELS = ["negative", "neutral", "positive"]

if SMOKE:  # uji lokal cepat tanpa GPU
    MODEL_NAME = "hf-internal-testing/tiny-random-BertForSequenceClassification"
    EPOCHS, BATCH, TRAIN_SAMPLE, USE_DRIVE = 1, 32, 2000, False
RUN_NAME = "indobertweet" if "indobertweet" in MODEL_NAME else MODEL_NAME.split("/")[-1].lower()

if IN_COLAB and USE_DRIVE:
    try:
        drive.mount("/content/drive")
        os.makedirs(DRIVE_DIR, exist_ok=True)
        print("Drive OK:", DRIVE_DIR)
    except Exception as e:
        USE_DRIVE = False
        print("Drive dilewati (hasil tetap diunduh di akhir):", repr(e))
else:
    USE_DRIVE = False

if not os.path.exists(DATA) and IN_COLAB and os.path.exists(f"{DRIVE_DIR}/{DATA}"):
    shutil.copy(f"{DRIVE_DIR}/{DATA}", DATA)
if not os.path.exists(DATA) and IN_COLAB:
    print("File igar_prepared.parquet belum ada. Pilih filenya di tombol upload di bawah.")
    files.upload()
df = pd.read_parquet(DATA)
assert {"key", "text", "label", "split"} <= set(df.columns), "file data salah"
print("DATA OK:", df.shape)
print(df.groupby(["split", "label"]).size().unstack())
"""
    ),
    md("Mulai dari sini tidak perlu klik apa pun lagi."),
    code(
        """
# 3) Pra-proses teks sesuai model
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
if SMOKE:
    val_df, test_df = val_df.head(300), test_df.head(300)
print(len(train_df), len(val_df), len(test_df))
print(val_df["input"].head(3).tolist())
"""
    ),
    code(
        """
# 4) Tokenisasi + model
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

tok = AutoTokenizer.from_pretrained(MODEL_NAME)

def to_ds(frame):
    ds = Dataset.from_pandas(frame[["input", "labels"]].reset_index(drop=True))
    return ds.map(lambda b: tok(b["input"], truncation=True, max_length=MAX_LEN), batched=True, remove_columns=["input"])

ds_train, ds_val, ds_test = to_ds(train_df), to_ds(val_df), to_ds(test_df)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=3, id2label=dict(enumerate(LABELS)),
    label2id={l: i for i, l in enumerate(LABELS)}, ignore_mismatched_sizes=True,
)
"""
    ),
    code(
        """
# 5) Training (bagian paling lama)
import inspect
from sklearn.metrics import accuracy_score, classification_report, f1_score
from transformers import Trainer, TrainingArguments

def compute_metrics(p):
    pred = p.predictions.argmax(-1)
    return {"macro_f1": f1_score(p.label_ids, pred, average="macro"), "accuracy": accuracy_score(p.label_ids, pred)}

kw = dict(
    output_dir="ckpt", save_strategy="epoch", load_best_model_at_end=True,
    metric_for_best_model="macro_f1", save_total_limit=1, learning_rate=LR,
    per_device_train_batch_size=BATCH, per_device_eval_batch_size=256, num_train_epochs=EPOCHS,
    weight_decay=0.01, fp16=torch.cuda.is_available(), logging_steps=200, report_to="none", seed=SEED,
)
# nama argumen beda antar versi transformers (v4 vs v5), disesuaikan otomatis
params = inspect.signature(TrainingArguments.__init__).parameters
kw["eval_strategy" if "eval_strategy" in params else "evaluation_strategy"] = "epoch"
if "warmup_ratio" in params:
    kw["warmup_ratio"] = 0.06
else:
    kw["warmup_steps"] = 0.06          # v5: angka < 1 dibaca sebagai rasio
if "group_by_length" in params:
    kw["group_by_length"] = True
elif "train_sampling_strategy" in params:
    kw["train_sampling_strategy"] = "group_by_length"
dropped = [k for k in kw if k not in params]
if dropped:
    print("Argumen tidak dikenal versi ini, dilewati:", dropped)
args = TrainingArguments(**{k: v for k, v in kw.items() if k in params})
print("warmup:", getattr(args, "warmup_ratio", None) or args.warmup_steps,
      "| sampler:", getattr(args, "train_sampling_strategy", None) or getattr(args, "group_by_length", None))
trainer = Trainer(
    model=model, args=args, train_dataset=ds_train, eval_dataset=ds_val,
    data_collator=DataCollatorWithPadding(tok), compute_metrics=compute_metrics,
)
t_train = time.time()
trainer.train()
print("training selesai dalam", round((time.time() - t_train) / 60, 1), "menit")
"""
    ),
    code(
        """
# 6) Prediksi val + test, simpan hasil, langsung cadangkan ke Drive
# Prediksi sengaja tidak lewat trainer.predict: di transformers 5.x sampler group_by_length ikut
# dipakai saat evaluasi, jadi urutan logits teracak dan tidak cocok lagi dengan urutan data.
from torch.utils.data import DataLoader

OUT = "suara_indobert_hasil"
os.makedirs(OUT, exist_ok=True)
summary = {"model": MODEL_NAME, "epochs": EPOCHS, "lr": LR, "batch": BATCH, "max_len": MAX_LEN,
           "train_rows": len(train_df), "train_minutes": round((time.time() - t_train) / 60, 1)}

def predict_in_order(ds):
    dl = DataLoader(ds.remove_columns(["labels"]), batch_size=256, shuffle=False, collate_fn=DataCollatorWithPadding(tok))
    net = trainer.model.eval()
    out = []
    with torch.no_grad():
        for b in dl:
            b = {k: v.to(net.device) for k, v in b.items()}
            with torch.autocast("cuda", dtype=torch.float16, enabled=torch.cuda.is_available()):
                out.append(net(**b).logits.float().cpu().numpy())
    return np.concatenate(out)

for name, ds, frame in [("val", ds_val, val_df), ("test", ds_test, test_df)]:
    t0 = time.time()
    logits = predict_in_order(ds).astype("float32")
    summary[f"{name}_predict_seconds"] = round(time.time() - t0, 1)
    np.save(f"{OUT}/{RUN_NAME}_{name}.npy", logits)
    frame[["key"]].to_parquet(f"{OUT}/{RUN_NAME}_{name}_keys.parquet", index=False)
    y = frame["labels"].to_numpy()
    summary[f"{name}_macro_f1_raw"] = float(f1_score(y, logits.argmax(-1), average="macro"))
    print(name, classification_report(y, logits.argmax(-1), target_names=LABELS, digits=4, zero_division=0))
summary["log_history"] = trainer.state.log_history
# cek urutan: skor val di sini harus sama dengan skor eval terbaik saat training
best_eval = max((e["eval_macro_f1"] for e in trainer.state.log_history if "eval_macro_f1" in e), default=None)
if best_eval is not None:
    summary["order_check_ok"] = abs(best_eval - summary["val_macro_f1_raw"]) < 0.005
    print("cek urutan:", "OK" if summary["order_check_ok"] else "BEDA, laporkan ke tim", round(best_eval, 4), round(summary["val_macro_f1_raw"], 4))
json.dump(summary, open(f"{OUT}/{RUN_NAME}_run.json", "w"), indent=2)
shutil.make_archive(OUT, "zip", ".", OUT)
print({k: v for k, v in summary.items() if k != "log_history"})

trainer.save_model(f"model_{RUN_NAME}")
tok.save_pretrained(f"model_{RUN_NAME}")
if USE_DRIVE:
    try:
        shutil.copy(f"{OUT}.zip", DRIVE_DIR)
        shutil.copytree(f"model_{RUN_NAME}", f"{DRIVE_DIR}/model_{RUN_NAME}", dirs_exist_ok=True)
        print("Cadangan hasil + model penuh tersimpan di Drive:", DRIVE_DIR)
    except Exception as e:
        print("Gagal cadangan ke Drive:", repr(e))
"""
    ),
    code(
        """
# 7) Versi ONNX int8 (ringan untuk web). Kalau gagal, hasil utama tetap aman.
ONNX_ZIP = None
try:
    import onnxruntime as ort
    from onnxruntime.quantization import QuantType, quantize_dynamic

    m = trainer.model.float().cpu().eval()
    dummy = tok(["contoh ulasan aplikasi"], return_tensors="pt")
    ekw = dict(
        input_names=["input_ids", "attention_mask"], output_names=["logits"],
        dynamic_axes={"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"}, "logits": {0: "b"}},
        opset_version=17,
    )
    try:
        torch.onnx.export(m, (dummy["input_ids"], dummy["attention_mask"]), "suara.onnx", dynamo=False, **ekw)
    except TypeError:
        torch.onnx.export(m, (dummy["input_ids"], dummy["attention_mask"]), "suara.onnx", **ekw)
    quantize_dynamic("suara.onnx", "suara-int8.onnx", weight_type=QuantType.QInt8)
    sess = ort.InferenceSession("suara-int8.onnx", providers=["CPUExecutionProvider"])

    sub = test_df.sample(n=min(2000, len(test_df)), random_state=SEED)
    fp = np.load(f"{OUT}/{RUN_NAME}_test.npy")[test_df.index.get_indexer(sub.index)]
    preds, t0 = [], time.time()
    for text in sub["input"]:
        enc = tok([text], truncation=True, max_length=MAX_LEN, return_tensors="np")
        feed = {"input_ids": enc["input_ids"].astype("int64"), "attention_mask": enc["attention_mask"].astype("int64")}
        preds.append(sess.run(["logits"], feed)[0][0])
    preds = np.array(preds)
    info = {
        "int8_mb": round(os.path.getsize("suara-int8.onnx") / 1e6, 1),
        "cpu_ms_per_review": round((time.time() - t0) / len(sub) * 1000, 1),
        "agreement_with_fp": float((preds.argmax(1) == fp.argmax(1)).mean()),
        "int8_macro_f1_sample": float(f1_score(sub["labels"], preds.argmax(1), average="macro")),
        "fp_macro_f1_sample": float(f1_score(sub["labels"], fp.argmax(1), average="macro")),
    }
    print(info)
    os.makedirs("suara_indobert_onnx_int8", exist_ok=True)
    shutil.copy("suara-int8.onnx", "suara_indobert_onnx_int8/model-int8.onnx")
    tok.save_pretrained("suara_indobert_onnx_int8/tokenizer")
    json.dump(info, open("suara_indobert_onnx_int8/onnx_info.json", "w"), indent=2)
    json.dump(info, open(f"{OUT}/{RUN_NAME}_onnx_info.json", "w"), indent=2)
    shutil.make_archive(OUT, "zip", ".", OUT)
    ONNX_ZIP = shutil.make_archive("suara_indobert_onnx_int8", "zip", ".", "suara_indobert_onnx_int8")
    if USE_DRIVE:
        shutil.copy(ONNX_ZIP, DRIVE_DIR)
        shutil.copy(f"{OUT}.zip", DRIVE_DIR)
except Exception as e:
    print("ONNX dilewati:", repr(e))
"""
    ),
    code(
        """
# 8) Unduh otomatis
to_download = [f"{OUT}.zip"] + ([ONNX_ZIP] if ONNX_ZIP else [])
for f in to_download:
    print(f, round(os.path.getsize(f) / 1e6, 1), "MB")
if IN_COLAB:
    for f in to_download:
        try:
            files.download(f)
        except Exception as e:
            print("Unduh otomatis gagal untuk", f, repr(e), "| ambil manual di panel file atau di Drive")
print("SELESAI. Kirim suara_indobert_hasil.zip ke tim.")
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
