"""Latih banyak model klasik, nilai HANYA di validation.

Skor test ikut disimpan ke disk tapi tidak dihitung metriknya di sini.
Pemilihan model dan penyesuaian bias terjadi di 04_final.py memakai validation.
Bisa dilanjutkan: run yang sudah ada di runs.jsonl dilewati.

Pakai: python 03_models.py [filter_substring]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.dummy import DummyClassifier
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import LogisticRegression, Ridge, SGDClassifier
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.evaluate import OrdinalAsClasses, metrics  # noqa: E402

FEATS = ROOT / "data" / "feats"
SCORES = ROOT / "data" / "scores"
RUNS_DIR = ROOT / "models" / "runs"
RUNS = ROOT / "ml" / "reports" / "runs.jsonl"


def lgbm(**kw):
    import lightgbm as lgb

    return lgb.LGBMClassifier(
        objective="multiclass",
        n_estimators=2000,
        learning_rate=0.1,
        num_leaves=127,
        min_child_samples=20,
        colsample_bytree=0.5,
        subsample=0.8,
        subsample_freq=1,
        reg_lambda=1.0,
        n_jobs=8,
        verbose=-1,
        **kw,
    )


EXPERIMENTS = [
    ("dummy_majority", "word", lambda: DummyClassifier(strategy="most_frequent")),
    *[(f"cnb_word_a{a}", "word", (lambda a=a: ComplementNB(alpha=a))) for a in [0.1, 0.3, 1.0]],
    ("mnb_word_a0.1", "word", lambda: MultinomialNB(alpha=0.1)),
    *[(f"svc_word_C{c}", "word", (lambda c=c: LinearSVC(C=c))) for c in [0.05, 0.1, 0.2, 0.5]],
    *[(f"svc_wordnoslang_C{c}", "word_noslang", (lambda c=c: LinearSVC(C=c))) for c in [0.1, 0.2]],
    *[(f"svc_wordchar_C{c}", "wordchar", (lambda c=c: LinearSVC(C=c))) for c in [0.05, 0.1, 0.2, 0.4]],
    ("svc_wordchar_C0.1_bal", "wordchar", lambda: LinearSVC(C=0.1, class_weight="balanced")),
    *[(f"lr_word_C{c}", "word", (lambda c=c: LogisticRegression(C=c, max_iter=2000))) for c in [2.0, 8.0]],
    # C=20 dibatalkan: C=8 sudah 16 menit dan tidak lebih baik dari C=2
    *[(f"lr_wordchar_C{c}", "wordchar", (lambda c=c: LogisticRegression(C=c, max_iter=2000))) for c in [2.0, 8.0]],
    ("sgdhuber_wordchar", "wordchar", lambda: SGDClassifier(loss="modified_huber", alpha=2e-6, max_iter=30, tol=None, average=True, random_state=42)),
    ("lgbm_word_chi2k30000", "word", "lgbm"),
    *[(f"ridge_wordchar_a{a}", "wordchar", (lambda a=a: ("ridge", Ridge(alpha=a, solver="sparse_cg", max_iter=300)))) for a in [1.0, 3.0]],
    ("ridge_word_a1.0", "word", lambda: ("ridge", Ridge(alpha=1.0, solver="sparse_cg", max_iter=300))),
]


def done_runs() -> set[str]:
    if not RUNS.exists():
        return set()
    return {json.loads(line)["run"] for line in RUNS.read_text(encoding="utf-8").splitlines() if line.strip()}


def scores_of(model, X) -> np.ndarray:
    """Skor per kelas: decision function untuk SVM, log-probabilitas untuk sisanya."""
    if isinstance(model, (LinearSVC, OrdinalAsClasses)):
        return model.decision_function(X).astype(np.float32)
    with np.errstate(divide="ignore"):
        s = np.log(model.predict_proba(X))
    return np.nan_to_num(s, neginf=-50.0).astype(np.float32)


def main(flt: str | None) -> None:
    SCORES.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    y = np.load(FEATS / "y.npz")
    cache: dict[str, dict] = {}
    done = done_runs()

    for run, fset, factory in EXPERIMENTS:
        if run in done or (flt and flt not in run):
            continue
        if fset not in cache:
            cache.clear()
            cache[fset] = {s: sp.load_npz(FEATS / f"{fset}_{s}.npz") for s in ["train", "val", "test"]}
        X = cache[fset]
        t0 = time.time()
        extra = {}
        if factory == "lgbm":
            sel = SelectKBest(chi2, k=30000).fit(X["train"], y["train"])
            Xtr, Xva, Xte = (sel.transform(X[s]).astype(np.float32) for s in ["train", "val", "test"])
            import lightgbm as lgb

            model = lgbm()
            model.fit(
                Xtr, y["train"], eval_set=[(Xva, y["val"])],
                callbacks=[lgb.early_stopping(50, verbose=False)],
            )
            extra["best_iteration"] = int(model.best_iteration_)
            fit_s = time.time() - t0
            s_val, s_te = scores_of(model, Xva), scores_of(model, Xte)
            joblib.dump({"selector": sel, "model": model}, RUNS_DIR / f"{run}.joblib")
        else:
            model = factory()
            if isinstance(model, tuple) and model[0] == "ridge":
                score_mean = np.load(FEATS / "score_mean.npz")
                reg = model[1].fit(X["train"], score_mean["train"])
                model = OrdinalAsClasses(reg)
            else:
                model.fit(X["train"], y["train"])
            fit_s = time.time() - t0
            s_val, s_te = scores_of(model, X["val"]), scores_of(model, X["test"])
            joblib.dump(model, RUNS_DIR / f"{run}.joblib")

        np.save(SCORES / f"{run}_val.npy", s_val)
        np.save(SCORES / f"{run}_test.npy", s_te)
        m = metrics(y["val"], s_val.argmax(1))
        rec = {"run": run, "features": fset, "fit_seconds": round(fit_s, 1), **extra, "val": m}
        with open(RUNS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        pc = m["per_class"]
        print(
            f"{run:28s} valF1={m['macro_f1']:.4f} acc={m['accuracy']:.4f} "
            f"neg={pc['negative']['f1']:.3f} neu={pc['neutral']['f1']:.3f} pos={pc['positive']['f1']:.3f} "
            f"fit={fit_s:.0f}s",
            flush=True,
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
