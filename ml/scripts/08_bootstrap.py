"""Rentang bootstrap 95% macro-F1 test dan selisih antar model (resampling berpasangan).

Bias kelas tiap model diambil dari final_selection.json (hasil tuning di validation), jadi
di sini tidak ada yang di-tune ulang. 1000 kali ambil ulang baris test dengan pengembalian.

Output: ml/reports/bootstrap_ci.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.evaluate import fast_macro_f1  # noqa: E402

REPORTS = ROOT / "ml" / "reports"
SCORES = ROOT / "data" / "scores"
FEATS = ROOT / "data" / "feats"
N_BOOT = 1000
MODELS = ["svc_wordchar_C0.1", "indobertweet", "indobertweet_int8", "lr_wordchar_C2.0", "mnb_word_a0.1", "svc_word_C0.1", "cnb_word_a0.1"]
PAIRS = [
    ("indobertweet", "svc_wordchar_C0.1"),
    ("indobertweet_int8", "svc_wordchar_C0.1"),
    ("indobertweet", "indobertweet_int8"),
    ("svc_wordchar_C0.1", "lr_wordchar_C2.0"),
    ("svc_wordchar_C0.1", "mnb_word_a0.1"),
    ("svc_wordchar_C0.1", "svc_word_C0.1"),
    ("svc_wordchar_C0.1", "cnb_word_a0.1"),
]


def main() -> None:
    y = np.load(FEATS / "y.npz")["test"]
    sel = json.loads((REPORTS / "final_selection.json").read_text(encoding="utf-8"))
    cands = {c["name"]: c for c in sel["candidates"]}
    pred = {}
    for name in MODELS:
        s = np.load(SCORES / f"{name}_test.npy").astype(np.float64)
        pred[name] = (s + np.array(cands[name]["bias"])).argmax(1)
        # skor IndoBERT sudah diurutkan ulang ke urutan data oleh 07_indobert_import.py
        assert abs(fast_macro_f1(y, pred[name]) - cands[name]["test"]["macro_f1"]) < 1e-3, name

    rng = np.random.default_rng(7)
    idx = rng.integers(0, len(y), size=(N_BOOT, len(y)))
    boot = {name: np.array([fast_macro_f1(y[i], pred[name][i]) for i in idx]) for name in MODELS}
    ci = lambda a: [round(float(np.percentile(a, 2.5)), 4), round(float(np.percentile(a, 97.5)), 4)]  # noqa: E731
    out = {
        "bootstrap": N_BOOT,
        "test_macro_f1_ci95": {name: ci(boot[name]) for name in MODELS},
        "diff_ci95": {f"{a} - {b}": ci(boot[a] - boot[b]) for a, b in PAIRS},
    }
    (REPORTS / "bootstrap_ci.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
