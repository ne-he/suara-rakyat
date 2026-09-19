"""Pilih model pakai validation, lalu evaluasi sekali di test.

1. Semua run di runs.jsonl (+ skor IndoBERT dari Colab kalau ada di data/scores/).
2. Tiap kandidat: geser bias kelas di-tune di validation untuk macro-F1, suhu dikalibrasi.
3. Gabungan skor dua model linear di set fitur sama (tetap linear, bisa dideploy).
4. Pemenang = macro-F1 validation tertinggi. Pemenang yang bisa dideploy ke web = linear terbaik.
5. Test dihitung untuk semua kandidat (tabel laporan), keputusan tidak berubah karena test.

Output: ml/reports/final_selection.json, ml/reports/results.md, ml/reports/confusion_*.png
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.evaluate import LABELS, fit_temperature, log_loss_T, metrics, tune_bias  # noqa: E402
from suara_ml.textnorm import mask_personal  # noqa: E402

FEATS = ROOT / "data" / "feats"
SCORES = ROOT / "data" / "scores"
REPORTS = ROOT / "ml" / "reports"
LINEAR_PREFIX = ("svc_", "lr_", "sgdhuber_", "ridge_")


def load_runs() -> dict[str, dict]:
    runs = {}
    for line in (REPORTS / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            runs[r["run"]] = r
    return runs


def evaluate_candidate(name, s_val, s_te, y, info) -> dict:
    raw_val = metrics(y["val"], s_val.argmax(1))
    d = tune_bias(y["val"], s_val)
    T = fit_temperature(y["val"], s_val + d)
    val = metrics(y["val"], (s_val + d).argmax(1))
    test_raw = metrics(y["test"], s_te.argmax(1))
    test = metrics(y["test"], (s_te + d).argmax(1))
    return {
        "name": name,
        **info,
        "bias": d.tolist(),
        "temperature": round(T, 4),
        "val_raw": raw_val,
        "val": val,
        "val_logloss": round(log_loss_T(y["val"], s_val + d, T), 4),
        "test_raw": test_raw,
        "test": test,
        "test_logloss": round(log_loss_T(y["test"], s_te + d, T), 4),
    }


def main() -> None:
    y = dict(np.load(FEATS / "y.npz"))
    runs = load_runs()
    cands: list[dict] = []
    scores: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for name, r in runs.items():
        s_val = np.load(SCORES / f"{name}_val.npy").astype(np.float64)
        s_te = np.load(SCORES / f"{name}_test.npy").astype(np.float64)
        scores[name] = (s_val, s_te)
        info = {"features": r["features"], "linear": name.startswith(LINEAR_PREFIX), "fit_seconds": r["fit_seconds"], "members": [{"run": name, "weight": 1.0}]}
        cands.append(evaluate_candidate(name, s_val, s_te, y, info))

    # IndoBERT dari Colab: urutan baris disamakan lewat kunci teks
    prepared = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet", columns=["key", "split"])
    for f in sorted(SCORES.glob("indo*_val.npy")):
        run = f.name[: -len("_val.npy")]
        per = {}
        for s in ["val", "test"]:
            logits = np.load(SCORES / f"{run}_{s}.npy").astype(np.float64)
            keys = pd.read_parquet(SCORES / f"{run}_{s}_keys.parquet")["key"]
            order = prepared[prepared["split"] == s]["key"].reset_index(drop=True)
            pos = pd.Series(range(len(keys)), index=keys.values)
            per[s] = logits[pos.loc[order.values].values]
        scores[run] = (per["val"], per["test"])
        colab = REPORTS / f"{run.removesuffix('_int8')}_colab_run.json"
        fit = round(json.loads(colab.read_text(encoding="utf-8"))["train_minutes"] * 60) if colab.exists() else None  # GPU T4
        cands.append(evaluate_candidate(run, per["val"], per["test"], y, {"features": "transformer", "linear": False, "fit_seconds": fit, "members": [{"run": run, "weight": 1.0}]}))

    # gabungan skor dua model linear terbaik per set fitur
    by_val = sorted(cands, key=lambda c: c["val"]["macro_f1"], reverse=True)
    linear_top = [c for c in by_val if c["linear"]][:4]
    for a, b in combinations(linear_top, 2):
        if a["features"] != b["features"]:
            continue
        sa, sb = scores[a["name"]], scores[b["name"]]
        # samakan skala: bagi dengan simpangan baku skor validation
        ka, kb = 1 / sa[0].std(), 1 / sb[0].std()
        best = None
        for w in [0.25, 0.4, 0.5, 0.6, 0.75]:
            v = w * ka * sa[0] + (1 - w) * kb * sb[0]
            f1 = metrics(y["val"], (v + tune_bias(y["val"], v)).argmax(1))["macro_f1"]
            if best is None or f1 > best[0]:
                best = (f1, w)
        w = best[1]
        members = [{"run": a["name"], "weight": round(w * ka, 6)}, {"run": b["name"], "weight": round((1 - w) * kb, 6)}]
        s_val = members[0]["weight"] * sa[0] + members[1]["weight"] * sb[0]
        s_te = members[0]["weight"] * sa[1] + members[1]["weight"] * sb[1]
        name = f"ens[{a['name']}+{b['name']}]"
        cands.append(evaluate_candidate(name, s_val, s_te, y, {"features": a["features"], "linear": True, "fit_seconds": None, "members": members}))

    # transformer + linear terbaik (hanya untuk laporan, butuh GPU/ONNX jadi tidak dipasang di web)
    for tr in [c for c in by_val if c["features"] == "transformer" and not c["name"].endswith("_int8")]:
        lin = linear_top[0]
        st, sl = scores[tr["name"]], scores[lin["name"]]
        kt, kl = 1 / st[0].std(), 1 / sl[0].std()
        best = None
        for w in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            v = w * kt * st[0] + (1 - w) * kl * sl[0]
            f1 = metrics(y["val"], (v + tune_bias(y["val"], v)).argmax(1))["macro_f1"]
            if best is None or f1 > best[0]:
                best = (f1, w)
        best_w = best[1]
        members = [{"run": tr["name"], "weight": round(best_w * kt, 6)}, {"run": lin["name"], "weight": round((1 - best_w) * kl, 6)}]
        s_val = members[0]["weight"] * st[0] + members[1]["weight"] * sl[0]
        s_te = members[0]["weight"] * st[1] + members[1]["weight"] * sl[1]
        cands.append(evaluate_candidate(f"ens[{tr['name']}+{lin['name']}]", s_val, s_te, y, {"features": "transformer+wordchar", "linear": False, "fit_seconds": None, "members": members}))

    cands.sort(key=lambda c: c["val"]["macro_f1"], reverse=True)
    best = cands[0]
    deploy = next(c for c in cands if c["linear"])

    # analisis tambahan untuk model deploy
    prep = pd.read_parquet(ROOT / "data" / "igar_prepared.parquet")
    te = prep[prep["split"] == "test"].reset_index(drop=True)
    comb_te = sum(m["weight"] * scores[m["run"]][1] for m in deploy["members"])
    pred = (comb_te + np.array(deploy["bias"])).argmax(1)
    extra = {
        "test_weighted_by_frequency": {
            "macro_f1": round(float(f1_score(y["test"], pred, average="macro", sample_weight=te["n"])), 4),
            "accuracy": round(float(np.average(pred == y["test"], weights=te["n"])), 4),
        },
        "test_by_app": {
            app: metrics(y["test"][idx], pred[idx])["macro_f1"]
            for app, idx in te.groupby("app").indices.items()
        },
        "test_agree_1": metrics(y["test"][te["agree"].values == 1], pred[te["agree"].values == 1])["macro_f1"],
    }
    # seberapa sering polaritas terbalik (negatif jadi positif atau sebaliknya)
    polar = y["test"] != 1
    flips = ((y["test"] == 0) & (pred == 2)) | ((y["test"] == 2) & (pred == 0))
    extra["polarity_flip_rate"] = round(float(flips[polar].mean()), 4)
    # tugas dua kelas (tanpa netral): pilih yang lebih besar antara skor negatif dan positif
    bin_pred = np.where(comb_te[:, 0] + deploy["bias"][0] >= comb_te[:, 2] + deploy["bias"][2], 0, 2)
    extra["binary_neg_pos"] = {
        "accuracy": round(float((bin_pred[polar] == y["test"][polar]).mean()), 4),
        "macro_f1": round(float(f1_score(y["test"][polar], bin_pred[polar], average="macro")), 4),
    }
    extra["label_noise_ceiling"] = json.loads((REPORTS / "label_noise.json").read_text(encoding="utf-8"))
    wrong = te.assign(pred=[LABELS[i] for i in pred])[pred != y["test"]]
    sample = wrong.sample(n=min(40, len(wrong)), random_state=1)[["text", "label", "pred", "app"]]
    sample["text"] = sample["text"].map(mask_personal)
    extra["error_examples"] = sample.to_dict(orient="records")

    selection = {
        "selected_by": "macro-F1 validation setelah geser bias (test tidak dipakai untuk memilih)",
        "best_overall": {k: best[k] for k in ["name", "features", "linear", "members", "bias", "temperature"]},
        "deploy": {
            "version": "v1",
            "features": deploy["features"],
            "members": deploy["members"],
            "bias": deploy["bias"],
            "temperature": deploy["temperature"],
            "name": deploy["name"],
            "metrics": {"test": deploy["test"], "val": deploy["val"], **{k: v for k, v in extra.items() if k != "error_examples"}},
        },
        "candidates": cands,
        "deploy_extra": extra,
    }
    (REPORTS / "final_selection.json").write_text(json.dumps(selection, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for c in cands:
        t, v = c["test"], c["val"]
        pc = t["per_class"]
        rows.append(
            f"| {c['name']} | {c['features']} | {v['macro_f1']:.4f} | {t['macro_f1']:.4f} | {c['test_raw']['macro_f1']:.4f} | {t['accuracy']:.4f} | "
            f"{pc['negative']['f1']:.3f} | {pc['neutral']['f1']:.3f} | {pc['positive']['f1']:.3f} | {c['fit_seconds'] if c['fit_seconds'] is not None else '-'} |"
        )
    md = [
        "# Hasil perbandingan model",
        "",
        f"Dipilih berdasarkan macro-F1 validation. Terbaik: `{best['name']}`. Dideploy ke web: `{deploy['name']}`.",
        "",
        "| Model | Fitur | Val macro-F1 | Test macro-F1 | Test macro-F1 tanpa geser bias | Test accuracy | F1 negatif | F1 netral | F1 positif | Detik latih |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "## Model deploy: analisis tambahan (test)",
        "```json",
        json.dumps({k: v for k, v in extra.items() if k != "error_examples"}, indent=2),
        "```",
    ]
    (REPORTS / "results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:8 + len(rows)]))
    plot_confusion(deploy, "deploy")
    if best["name"] != deploy["name"]:
        plot_confusion(best, "best")


def plot_confusion(c: dict, tag: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = np.array(c["test"]["confusion"])
    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(4.6, 4))
    ax.imshow(norm, cmap="Greys", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n{norm[i, j]:.1%}", ha="center", va="center", color="white" if norm[i, j] > 0.5 else "black", fontsize=9)
    ax.set_xticks(range(3), ["negatif", "netral", "positif"])
    ax.set_yticks(range(3), ["negatif", "netral", "positif"])
    ax.set_xlabel("prediksi")
    ax.set_ylabel("label asli")
    ax.set_title(f"{c['name'][:40]}\nmacro-F1 test {c['test']['macro_f1']:.4f}", fontsize=9)
    fig.tight_layout()
    fig.savefig(REPORTS / f"confusion_{tag}.png", dpi=160)


if __name__ == "__main__":
    main()
