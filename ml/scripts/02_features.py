"""Bangun matriks fitur untuk tiap set fitur, fit HANYA di train.

Set fitur:
  word          kata 1-2 gram, kamus slang aktif
  word_noslang  sama, tanpa kamus slang (ablation)
  wordchar      kata 1-2 gram + karakter 2-5 gram, kamus slang aktif

Output: data/feats/<set>_{train,val,test}.npz, data/feats/<set>_y.npz,
        models/featurizer_<set>.joblib
Pakai: python 02_features.py word wordchar
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.features import FeatureConfig, TextFeaturizer  # noqa: E402

DATA = ROOT / "data" / "igar_prepared.parquet"
FEATS = ROOT / "data" / "feats"
MODELS = ROOT / "models"
LABELS = ["negative", "neutral", "positive"]

SETS = {
    "word": FeatureConfig(use_char=False),
    "word_noslang": FeatureConfig(use_char=False, use_slang=False),
    "wordchar": FeatureConfig(use_char=True),
}


def main(names: list[str]) -> None:
    df = pd.read_parquet(DATA)
    FEATS.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    parts = {s: df[df["split"] == s] for s in ["train", "val", "test"]}
    y = {s: p["label"].map(LABELS.index).to_numpy(np.int8) for s, p in parts.items()}
    np.savez(FEATS / "y.npz", **y)

    for name in names:
        t0 = time.time()
        fz = TextFeaturizer(SETS[name])
        X_train = fz.fit_transform(parts["train"]["text"].tolist())
        sp.save_npz(FEATS / f"{name}_train.npz", X_train, compressed=False)
        for s in ["val", "test"]:
            sp.save_npz(FEATS / f"{name}_{s}.npz", fz.transform(parts[s]["text"].tolist()), compressed=False)
        joblib.dump(fz, MODELS / f"featurizer_{name}.joblib")
        info = {
            "set": name,
            "n_features": fz.n_features,
            "n_word": fz.n_word,
            "train_nnz": int(X_train.nnz),
            "seconds": round(time.time() - t0, 1),
        }
        print(json.dumps(info))
        with open(ROOT / "ml" / "reports" / "features.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(info) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or list(SETS))
