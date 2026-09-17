"""Seberapa berisik label dari bintang?

Untuk teks yang muncul berkali-kali (kunci sama), model berbasis teks hanya bisa
menebak satu label. Akurasi terbaik yang mungkin di baris-baris itu = porsi label
mayoritas. Ini memberi gambaran batas atas akibat label yang tidak konsisten.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import tokens  # noqa: E402

LABELS = ["negative", "neutral", "positive"]


def main() -> None:
    df = pd.read_csv(ROOT / "dataset" / "Rating_labeled.csv", usecols=["content", "labelScoreBase"])
    df["label"] = df["labelScoreBase"].str.lower()
    df["key"] = [" ".join(tokens(t, use_slang=False)) if isinstance(t, str) else "" for t in df["content"]]
    df = df[df["key"] != ""]
    counts = df.groupby(["key", "label"]).size().unstack(fill_value=0)[LABELS]
    n = counts.sum(axis=1)
    multi = counts[n >= 2]
    rows_multi = int(multi.values.sum())
    oracle_acc = float(multi.max(axis=1).sum() / rows_multi)

    # macro-F1 "oracle" di baris duplikat: tiap baris diprediksi label mayoritas kuncinya
    maj = multi.values.argmax(axis=1)
    y_true = np.repeat(np.tile(np.arange(3), (len(multi), 1)).ravel(), multi.values.ravel())
    y_pred = np.repeat(np.repeat(maj, 3), multi.values.ravel())
    out = {
        "keys_seen_2plus": int(len(multi)),
        "rows_in_those_keys": rows_multi,
        "oracle_accuracy_on_duplicated_rows": round(oracle_acc, 4),
        "oracle_macro_f1_on_duplicated_rows": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "neutral_rows_whose_text_majority_is_not_neutral": round(
            float(multi["neutral"][maj != 1].sum() / max(1, multi["neutral"].sum())), 4
        ),
        "example_mixed": {
            k: counts.loc[k].to_dict() for k in ["mantap", "bagus", "ok", "lumayan", "aplikasi sangat membantu"] if k in counts.index
        },
    }
    (ROOT / "ml" / "reports" / "label_noise.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
