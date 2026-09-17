"""Export 3 model linear ke format web (web/model/) + sampel uji paritas.

Ketiga model memakai featurizer kata + karakter yang sama. Blok kata di featurizer itu
identik dengan featurizer "word" (kosakata, idf, dan normalisasi L2 per blok sama),
jadi Naive Bayes yang dilatih di fitur kata cukup memakai kolom blok kata saja.

File per model: coef_<id>.f32 berukuran kelas x n_cols (n_cols = n_word untuk model kata).
Bias kelas dan suhu diambil dari ml/reports/final_selection.json (hasil tuning di validation).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.evaluate import metrics  # noqa: E402
from suara_ml.textnorm import mask_personal  # noqa: E402

MODELS = ROOT / "models"
SCORES = ROOT / "data" / "scores"
WEB_MODEL = ROOT / "web" / "model"
SEL = ROOT / "ml" / "reports" / "final_selection.json"
LABELS = ["negative", "neutral", "positive"]

WEB_MODELS = [
    {
        "id": "svm",
        "run": "svc_wordchar_C0.1",
        "name": "Linear SVM",
        "features": "kata + karakter",
        "tagline": "Juara di validation. Paling seimbang.",
    },
    {
        "id": "logreg",
        "run": "lr_wordchar_C2.0",
        "name": "Logistic Regression",
        "features": "kata + karakter",
        "tagline": "Belajar peluang langsung. Sedikit lebih hati-hati.",
    },
    {
        "id": "nb",
        "run": "mnb_word_a0.1",
        "name": "Naive Bayes",
        "features": "kata",
        "tagline": "Paling sederhana dan tercepat dilatih. Pembanding klasik.",
    },
]
DEFAULT_ID = "svm"

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


def linear_parts(model, n_word: int, n_feat: int) -> tuple[np.ndarray, np.ndarray]:
    """Bobot (kelas x kolom) dan intercept, untuk SVM/LR (coef_) dan MultinomialNB."""
    if hasattr(model, "feature_log_prob_"):
        coef = model.feature_log_prob_.astype(np.float64)
        intercept = model.class_log_prior_.astype(np.float64)
    else:
        coef = model.coef_.astype(np.float64)
        intercept = model.intercept_.astype(np.float64)
    assert coef.shape[1] in (n_word, n_feat), coef.shape
    return coef, intercept


def main() -> None:
    sel_all = json.loads(SEL.read_text(encoding="utf-8"))
    cands = {c["name"]: c for c in sel_all["candidates"]}
    fz = joblib.load(MODELS / "featurizer_wordchar.joblib")
    n_word = len(fz.word_vec.vocabulary_)
    n_char = len(fz.char_vec.vocabulary_)
    n_feat = n_word + n_char

    WEB_MODEL.mkdir(parents=True, exist_ok=True)
    for old in WEB_MODEL.glob("coef*.f32"):
        old.unlink()
    words = [None] * n_word
    for t, i in fz.word_vec.vocabulary_.items():
        words[i] = t
    chars = [None] * n_char
    for t, i in fz.char_vec.vocabulary_.items():
        chars[i] = t
    assert not any("\n" in w for w in words + chars)
    (WEB_MODEL / "vocab_word.txt").write_text("\n".join(words) + "\n", encoding="utf-8", newline="\n")
    (WEB_MODEL / "vocab_char.txt").write_text("\n".join(chars) + "\n", encoding="utf-8", newline="\n")
    np.concatenate([fz.word_vec.idf_, fz.char_vec.idf_]).astype("<f4").tofile(WEB_MODEL / "idf.f32")

    # data test untuk metrik tambahan per model
    y = np.load(ROOT / "data" / "feats" / "y.npz")
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet")
    te = prep[prep["split"] == "test"].reset_index(drop=True)
    polar = y["test"] != 1

    df_val = prep[prep["split"] == "val"].sample(n=3000, random_state=7)
    texts = TRICKY + [mask_personal(t) for t in df_val["text"].tolist()]
    X = fz.transform(texts)

    meta_models = []
    parity: dict[str, list] = {}
    for wm in WEB_MODELS:
        cand = cands[wm["run"]]
        model = joblib.load(MODELS / "runs" / f"{wm['run']}.joblib")
        coef, intercept = linear_parts(model, n_word, n_feat)
        coef.astype("<f4").tofile(WEB_MODEL / f"coef_{wm['id']}.f32")
        bias = np.array(cand["bias"], dtype=np.float64)
        T = float(cand["temperature"])

        # cek: skor linear hasil export = skor asli model (beda konstanta per baris boleh)
        Xm = X[:, : coef.shape[1]]
        scores = np.asarray(Xm @ coef.T) + intercept
        if hasattr(model, "feature_log_prob_"):
            ref = model.predict_joint_log_proba(Xm)
        else:
            ref = model.decision_function(X)
        assert np.allclose(ref, scores, atol=1e-4), f"export {wm['id']} tidak sama dengan model asli"
        probs = softmax((scores + bias) / T, axis=1)
        parity[wm["id"]] = [[round(float(v), 6) for v in p] for p in probs]

        s_te = np.load(SCORES / f"{wm['run']}_test.npy").astype(np.float64) + bias
        pred = s_te.argmax(1)
        flips = ((y["test"] == 0) & (pred == 2)) | ((y["test"] == 2) & (pred == 0))
        bin_pred = np.where(s_te[:, 0] >= s_te[:, 2], 0, 2)
        meta_models.append(
            {
                **wm,
                "n_cols": int(coef.shape[1]),
                "intercept": intercept.tolist(),
                "bias": bias.tolist(),
                "temperature": T,
                "fit_seconds": cand["fit_seconds"],
                "metrics": {
                    "val_macro_f1": cand["val"]["macro_f1"],
                    "test": cand["test"],
                    "test_macro_f1_raw": cand["test_raw"]["macro_f1"],
                    "polarity_flip_rate": round(float(flips[polar].mean()), 4),
                    "binary_neg_pos_accuracy": round(float((bin_pred[polar] == y["test"][polar]).mean()), 4),
                    "binary_neg_pos_macro_f1": round(float(f1_score(y["test"][polar], bin_pred[polar], average="macro")), 4),
                    "test_by_app": {
                        app: metrics(y["test"][idx], pred[idx])["macro_f1"] for app, idx in te.groupby("app").indices.items()
                    },
                },
            }
        )

    meta = {
        "version": "v1.1",
        "labels": LABELS,
        "config": {
            "use_slang": fz.cfg.use_slang,
            "word_ngram_max": fz.cfg.word_ngram_max,
            "use_char": fz.cfg.use_char,
            "char_min": fz.cfg.char_min,
            "char_max": fz.cfg.char_max,
        },
        "n_word": n_word,
        "n_char": n_char,
        "default_model": DEFAULT_ID,
        "models": meta_models,
    }
    (WEB_MODEL / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (WEB_MODEL / "report.json").unlink(missing_ok=True)
    slang_src = ROOT / "ml" / "suara_ml" / "slang_id.json"
    (ROOT / "web" / "lib" / "slang_id.json").write_text(slang_src.read_text(encoding="utf-8"), encoding="utf-8")

    samples = [
        {"text": t, "probs": {m["id"]: parity[m["id"]][i] for m in WEB_MODELS}} for i, t in enumerate(texts)
    ]
    (ROOT / "web" / "scripts" / "parity_samples.json").write_text(json.dumps(samples, ensure_ascii=False), encoding="utf-8")
    write_site_data(sel_all)
    sizes = {p.name: round(p.stat().st_size / 1e6, 2) for p in sorted(WEB_MODEL.iterdir())}
    print(json.dumps({"n_word": n_word, "n_char": n_char, "files_mb": sizes}, indent=2))


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


def write_site_data(sel_all: dict) -> None:
    """Data halaman: ringkasan dataset, papan peringkat, plafon label."""
    audit = json.loads((ROOT / "ml" / "reports" / "data_audit.json").read_text(encoding="utf-8"))
    noise = json.loads((ROOT / "ml" / "reports" / "label_noise.json").read_text(encoding="utf-8"))
    web_runs = {m["run"]: m["id"] for m in WEB_MODELS}
    board = [
        {
            "name": c["name"],
            "family": family(c["name"]),
            "features": c["features"],
            "web_id": web_runs.get(c["name"]),
            "val_macro_f1": c["val"]["macro_f1"],
            "test_macro_f1": c["test"]["macro_f1"],
            "test_macro_f1_raw": c["test_raw"]["macro_f1"],
            "test_accuracy": c["test"]["accuracy"],
            "test_f1": {k: v["f1"] for k, v in c["test"]["per_class"].items()},
        }
        for c in sel_all["candidates"]
    ]
    site = {
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
        "label_noise": {
            "rows_in_duplicated_texts": noise["rows_in_those_keys"],
            "oracle_macro_f1": noise["oracle_macro_f1_on_duplicated_rows"],
            "neutral_not_majority": noise["neutral_rows_whose_text_majority_is_not_neutral"],
            "mantap": noise["example_mixed"].get("mantap", {}),
        },
        "leaderboard": board,
    }
    (ROOT / "web" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "web" / "data" / "site.json").write_text(json.dumps(site, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
