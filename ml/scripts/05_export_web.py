"""Export model linear terpilih ke format web (web/model/) + sampel uji paritas.

Baca ml/reports/final_selection.json bagian "deploy":
  {"features": "wordchar", "members": [{"run": "...", "weight": 1.0}], "bias": [...], "temperature": T}
Beberapa model linear di set fitur yang sama digabung jadi satu matriks bobot
(jumlah skor berbobot tetap linear), jadi web cukup menghitung satu perkalian.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

MODELS = ROOT / "models"
WEB_MODEL = ROOT / "web" / "model"
SEL = ROOT / "ml" / "reports" / "final_selection.json"
LABELS = ["negative", "neutral", "positive"]

TRICKY = [
    "",
    "   ",
    "👍👍👍",
    "Mantap...sangat membantu 👍",
    "GAK BISA LOGIN!!! otp ga masukkkkk",
    "ｂａｇｕｓ ｂａｎｇｅｔ",
    "cek https://example.com/a?b=c aplikasinya error terus",
    "Aplikasi ini sangat bagus tapi sering error saat verifikasi wajah",
    "😡😡😡 lemot bgt",
    "biasa aja sih",
    "tolong diperbaiki, saya sudah 3x coba daftar tidak bisa",
    "ok",
    "Terimakasih KAI, pesan tiket jadi mudah",
    "MyPertamina ribet, harus scan QR segala",
    "Ⓑⓐⓖⓤⓢ",
    "tidak buruk",
    "aplikasi\tbagus\nsekali",
    "İstanbul ǅ ß ẞ",
]


def main() -> None:
    sel = json.loads(SEL.read_text(encoding="utf-8"))["deploy"]
    fz = joblib.load(MODELS / f"featurizer_{sel['features']}.joblib")
    coef = None
    intercept = None
    for m in sel["members"]:
        model = joblib.load(MODELS / "runs" / f"{m['run']}.joblib")
        c = model.coef_.astype(np.float64) * m["weight"]
        b = model.intercept_.astype(np.float64) * m["weight"]
        coef = c if coef is None else coef + c
        intercept = b if intercept is None else intercept + b
    bias = np.array(sel["bias"], dtype=np.float64)
    T = float(sel["temperature"])

    WEB_MODEL.mkdir(parents=True, exist_ok=True)
    wv = fz.word_vec.vocabulary_
    words = [None] * len(wv)
    for t, i in wv.items():
        words[i] = t
    (WEB_MODEL / "vocab_word.txt").write_text("\n".join(words) + "\n", encoding="utf-8", newline="\n")
    idf = [fz.word_vec.idf_]
    n_char = 0
    if fz.char_vec is not None:
        cv = fz.char_vec.vocabulary_
        chars = [None] * len(cv)
        for t, i in cv.items():
            chars[i] = t
        assert not any("\n" in c for c in chars)
        (WEB_MODEL / "vocab_char.txt").write_text("\n".join(chars) + "\n", encoding="utf-8", newline="\n")
        idf.append(fz.char_vec.idf_)
        n_char = len(cv)
    assert not any("\n" in w for w in words)
    np.concatenate(idf).astype("<f4").tofile(WEB_MODEL / "idf.f32")
    coef.astype("<f4").tofile(WEB_MODEL / "coef.f32")

    meta = {
        "version": sel.get("version", "v1"),
        "labels": LABELS,
        "config": {
            "use_slang": fz.cfg.use_slang,
            "word_ngram_max": fz.cfg.word_ngram_max,
            "use_char": fz.cfg.use_char,
            "char_min": fz.cfg.char_min,
            "char_max": fz.cfg.char_max,
        },
        "n_word": len(wv),
        "n_char": n_char,
        "intercept": intercept.tolist(),
        "bias": bias.tolist(),
        "temperature": T,
        "source_run": "+".join(f"{m['weight']}*{m['run']}" for m in sel["members"]),
        "metrics": sel.get("metrics", {}),
    }
    (WEB_MODEL / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    slang_src = ROOT / "ml" / "suara_ml" / "slang_id.json"
    (ROOT / "web" / "lib" / "slang_id.json").write_text(slang_src.read_text(encoding="utf-8"), encoding="utf-8")

    # sampel paritas: teks jebakan + 3000 teks validation
    df = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet")
    val = df[df["split"] == "val"].sample(n=3000, random_state=7)
    from suara_ml.textnorm import mask_personal

    texts = TRICKY + [mask_personal(t) for t in val["text"].tolist()]
    X = fz.transform(texts)
    scores = X @ coef.T + intercept + bias
    probs = softmax(scores / T, axis=1)

    # cek export konsisten dengan model aslinya
    ref = None
    for m in sel["members"]:
        model = joblib.load(MODELS / "runs" / f"{m['run']}.joblib")
        d = model.decision_function(X) * m["weight"]
        ref = d if ref is None else ref + d
    assert np.allclose(ref + bias, scores, atol=1e-4), "export tidak sama dengan decision_function"

    samples = [
        {"text": t, "label": LABELS[int(p.argmax())], "probs": [round(float(x), 6) for x in p]}
        for t, p in zip(texts, probs)
    ]
    (ROOT / "web" / "scripts").mkdir(parents=True, exist_ok=True)
    (ROOT / "web" / "scripts" / "parity_samples.json").write_text(
        json.dumps(samples, ensure_ascii=False), encoding="utf-8"
    )
    write_report(json.loads(SEL.read_text(encoding="utf-8")))
    sizes = {p.name: round(p.stat().st_size / 1e6, 2) for p in WEB_MODEL.iterdir()}
    print(json.dumps({"n_word": len(wv), "n_char": n_char, "files_mb": sizes}, indent=2))


def family(name: str) -> str:
    for prefix, fam in [
        ("ens[", "Gabungan skor"),
        ("svc_", "Linear SVM"),
        ("ridge_", "Regresi bintang (Ridge)"),
        ("lr_", "Logistic Regression"),
        ("sgdhuber_", "SGD (modified Huber)"),
        ("cnb_", "Complement Naive Bayes"),
        ("mnb_", "Multinomial Naive Bayes"),
        ("lgbm_", "LightGBM"),
        ("dummy_", "Baseline mayoritas"),
        ("indo", "IndoBERT (transformer)"),
    ]:
        if name.startswith(prefix):
            return fam
    return name


def write_report(sel_all: dict) -> None:
    """Ringkasan untuk halaman web: data, model deploy, papan peringkat."""
    audit = json.loads((ROOT / "ml" / "reports" / "data_audit.json").read_text(encoding="utf-8"))
    dep = sel_all["deploy"]
    board = []
    for c in sel_all["candidates"]:
        board.append(
            {
                "name": c["name"],
                "family": family(c["name"]),
                "features": c["features"],
                "deployable": bool(c["linear"]),
                "val_macro_f1": c["val"]["macro_f1"],
                "test_macro_f1": c["test"]["macro_f1"],
                "test_macro_f1_raw": c["test_raw"]["macro_f1"],
                "test_accuracy": c["test"]["accuracy"],
                "test_f1": {k: v["f1"] for k, v in c["test"]["per_class"].items()},
            }
        )
    report = {
        "dataset": {
            "raw_rows": audit["raw_rows"],
            "exact_duplicates": audit["exact_duplicate_content"],
            "unique_texts": audit["prepared_rows"],
            "label_counts_unique": audit["prepared_label_counts"],
            "split_counts": audit["split_counts"],
            "date_min": audit["date_min"],
            "date_max": audit["date_max"],
            "apps": audit["app_counts_raw"],
        },
        "deploy": {"name": dep["name"], "features": dep["features"], "metrics": dep["metrics"]},
        "best_overall": sel_all["best_overall"]["name"],
        "leaderboard": board,
    }
    (WEB_MODEL / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
