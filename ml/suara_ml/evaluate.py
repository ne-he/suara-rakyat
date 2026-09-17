"""Metrik, penyesuaian bias kelas, dan kalibrasi suhu."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import log_softmax
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

LABELS = ["negative", "neutral", "positive"]


def metrics(y_true, y_pred) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1, 2], zero_division=0)
    return {
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted")), 4),
        "per_class": {
            LABELS[i]: {
                "precision": round(float(p[i]), 4),
                "recall": round(float(r[i]), 4),
                "f1": round(float(f[i]), 4),
                "support": int(s[i]),
            }
            for i in range(3)
        },
        "confusion": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
    }


def fast_macro_f1(y, pred, k: int = 3) -> float:
    """Macro-F1 via confusion matrix numpy (hasil sama dengan sklearn, jauh lebih cepat)."""
    cm = np.bincount(y * k + pred, minlength=k * k).reshape(k, k)
    tp = np.diag(cm).astype(np.float64)
    denom = cm.sum(axis=0) + cm.sum(axis=1)
    f1 = np.divide(2 * tp, denom, out=np.zeros(k), where=denom > 0)
    return float(f1.mean())


def macro_f1(y, scores, d) -> float:
    return fast_macro_f1(y, np.argmax(scores + d, axis=1))


def tune_bias(y_val, scores, lo=-3.0, hi=3.0) -> np.ndarray:
    """Cari geser skor (negatif, netral) yang memaksimalkan macro-F1 validation.

    Skor positif dijadikan acuan (geser 0). Grid kasar lalu grid halus.
    """
    best = (macro_f1(y_val, scores, np.zeros(3)), np.zeros(3))
    for step, span in [(0.25, None), (0.05, 0.3), (0.01, 0.06)]:
        if span is None:
            grid_a = grid_b = np.arange(lo, hi + 1e-9, step)
        else:
            c = best[1]
            grid_a = np.arange(c[0] - span, c[0] + span + 1e-9, step)
            grid_b = np.arange(c[1] - span, c[1] + span + 1e-9, step)
        for a in grid_a:
            for b in grid_b:
                d = np.array([a, b, 0.0])
                m = macro_f1(y_val, scores, d)
                if m > best[0] + 1e-9:
                    best = (m, d)
    return np.round(best[1], 4)


def fit_temperature(y_val, scores) -> float:
    """Suhu T supaya softmax(skor / T) punya log-loss terkecil di validation."""
    idx = np.arange(len(y_val))

    def nll(log_t):
        lp = log_softmax(scores / np.exp(log_t), axis=1)
        return -lp[idx, y_val].mean()

    res = minimize_scalar(nll, bounds=(-4, 4), method="bounded")
    return float(np.exp(res.x))


def log_loss_T(y, scores, T) -> float:
    lp = log_softmax(scores / T, axis=1)
    return float(-lp[np.arange(len(y)), y].mean())


class OrdinalAsClasses:
    """Regresi bintang (1-5) yang dibungkus jadi skor 3 kelas linear.

    r = w.x + b - 3, skor = [-r, 0, r]. Dengan geser bias (dn, du) dari tune_bias,
    argmax menghasilkan ambang: negatif kalau r di bawah ambang bawah, positif kalau
    di atas ambang atas, sisanya netral. Tetap satu matriks linear, bisa diekspor ke web.
    """

    def __init__(self, regressor):
        self.regressor = regressor

    @property
    def coef_(self):
        w = np.asarray(self.regressor.coef_, dtype=np.float64).ravel()
        return np.vstack([-w, np.zeros_like(w), w])

    @property
    def intercept_(self):
        b = float(np.ravel(self.regressor.intercept_)[0]) - 3.0
        return np.array([-b, 0.0, b])

    def decision_function(self, X):
        return np.asarray(X @ self.coef_.T + self.intercept_)
