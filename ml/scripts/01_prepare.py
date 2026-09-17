"""Audit dataset IGAR (Rating_labeled.csv) lalu bikin data siap latih.

Langkah:
1. Audit mentah: kolom, nilai kosong, hubungan score dengan label, jumlah per app.
2. Kunci teks = token hasil normalisasi (tanpa kamus slang). Ulasan yang tokennya
   sama dianggap teks yang sama, jadi "Mantap!!" dan "mantap" satu kunci.
3. Satu baris per kunci, label = mayoritas. Kunci dengan label seri dibuang.
4. Split deterministik dari hash md5 kunci: 80% train, 10% validation, 10% test.
   Teks yang sama tidak mungkin muncul di dua split berbeda (anti bocor).

Output: data/igar_prepared.parquet dan ml/reports/data_audit.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import tokens  # noqa: E402

RAW = ROOT / "dataset" / "Rating_labeled.csv"
OUT = ROOT / "data" / "igar_prepared.parquet"
REPORT = ROOT / "ml" / "reports" / "data_audit.json"
LABELS = ["negative", "neutral", "positive"]


def split_of(key: str) -> str:
    b = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % 100
    return "train" if b < 80 else ("val" if b < 90 else "test")


def most_common(df: pd.DataFrame, col: str) -> pd.Series:
    """Nilai paling sering per kunci (seri dipecah urutan alfabet, deterministik)."""
    c = df.groupby(["key", col]).size().reset_index(name="cnt")
    c = c.sort_values(["key", "cnt", col], ascending=[True, False, True])
    return c.drop_duplicates("key").set_index("key")[col]


def main() -> None:
    df = pd.read_csv(RAW, encoding="utf-8")
    audit: dict = {"raw_rows": int(len(df)), "columns": list(df.columns)}
    audit["null_counts"] = {c: int(v) for c, v in df.isna().sum().items()}
    df["label"] = df["labelScoreBase"].astype(str).str.strip().str.lower()
    audit["label_counts_raw"] = df["label"].value_counts().to_dict()
    audit["score_by_label"] = (
        pd.crosstab(df["score"], df["label"]).to_dict(orient="index")
    )
    audit["app_counts_raw"] = df["app"].value_counts().to_dict()
    at = pd.to_datetime(df["at"], errors="coerce")
    audit["date_min"] = str(at.min())
    audit["date_max"] = str(at.max())
    audit["exact_duplicate_content"] = int(df["content"].duplicated().sum())

    df = df[df["label"].isin(LABELS)].copy()
    df["content"] = df["content"].fillna("").astype(str)
    df["key"] = [" ".join(tokens(t, use_slang=False)) for t in df["content"]]
    empty = df["key"].eq("")
    audit["empty_after_normalize"] = int(empty.sum())
    df = df[~empty]
    df["at"] = pd.to_datetime(df["at"], errors="coerce")

    counts = df.groupby(["key", "label"]).size().unstack(fill_value=0)
    for lab in LABELS:
        if lab not in counts:
            counts[lab] = 0
    counts = counts[LABELS]
    n = counts.sum(axis=1)
    srt = np.sort(counts.values, axis=1)
    tie = pd.Series(srt[:, -1] == srt[:, -2], index=counts.index)
    audit["unique_keys"] = int(len(counts))
    audit["keys_with_conflicting_labels"] = int((counts.gt(0).sum(axis=1) > 1).sum())
    audit["keys_dropped_tie"] = int(tie.sum())
    audit["rows_in_tied_keys"] = int(n[tie].sum())

    counts = counts[~tie]
    majority = counts.idxmax(axis=1)
    agree = counts.max(axis=1) / counts.sum(axis=1)

    rep_text = most_common(df, "content")
    app_mode = most_common(df, "app")
    at_min = df.groupby("key")["at"].min()
    score_mean = df.groupby("key")["score"].mean()

    out = pd.DataFrame(
        {
            "key": counts.index,
            "text": rep_text.reindex(counts.index).values,
            "label": majority.values,
            "n": counts.sum(axis=1).values.astype("int32"),
            "agree": agree.values.astype("float32"),
            "app": app_mode.reindex(counts.index).values,
            "at_min": at_min.reindex(counts.index).values,
            "score_mean": score_mean.reindex(counts.index).values.astype("float32"),
        }
    )
    out["split"] = [split_of(k) for k in out["key"]]
    out = out.sort_values("key").reset_index(drop=True)

    audit["prepared_rows"] = int(len(out))
    audit["prepared_label_counts"] = out["label"].value_counts().to_dict()
    audit["split_counts"] = (
        out.groupby(["split", "label"]).size().unstack(fill_value=0).to_dict(orient="index")
    )
    audit["rows_represented"] = int(out["n"].sum())
    audit["token_len_percentiles"] = (
        out["key"].str.split().str.len().quantile([0.5, 0.9, 0.99]).round(1).to_dict()
    )
    audit["share_single_token_keys"] = float(
        (out["key"].str.split().str.len() == 1).mean().round(4)
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    REPORT.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str))


if __name__ == "__main__":
    main()
