"""Klasifikasi nada ulasan dengan Linear SVM hasil penelitian.

Bobot dibaca dari web/model, file yang sama dengan web v4, dan praproses memakai
ml/suara_ml/textnorm.py, kode yang sama dengan saat model dilatih. Rumusnya:
  tf = 1 + ln(count), x = tf * idf, dinormalisasi L2 per blok (kata, karakter)
  skor = W x + intercept + bias, peluang = softmax(skor / T)

Semua ulasan dalam satu pencarian dihitung sekaligus sebagai satu matriks, jadi
10.000 ulasan tetap selesai dalam hitungan detik.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from suara_ml.textnorm import char_ngrams, tokens, word_ngrams  # noqa: E402

LABELS = ("negative", "neutral", "positive")
MODEL_DIR = ROOT / "web" / "model"


@dataclass(frozen=True)
class Prediction:
    label: str | None  # None kalau tidak ada satu pun kata yang dikenali model
    confidence: float | None
    probs: tuple[float, ...] | None
    tokens: tuple[tuple[str, float], ...]  # dorongan tiap token ke label terpilih


class SentimentClassifier:
    """Linear SVM (TF-IDF kata 1-2 + karakter 2-5) dengan geser bias dan temperature scaling."""

    def __init__(self, model_dir: Path = MODEL_DIR, model_id: str | None = None) -> None:
        meta = json.loads((model_dir / "meta.json").read_text(encoding="utf-8"))
        info = next(m for m in meta["models"] if m["id"] == (model_id or meta["default_model"]))
        self.name: str = info["name"]
        self.config: dict = meta["config"]
        self.n_word: int = meta["n_word"]
        self.n_feat: int = meta["n_word"] + meta["n_char"]
        self.word_index = self._vocab(model_dir / "vocab_word.txt", meta["n_word"])
        self.char_index = self._vocab(model_dir / "vocab_char.txt", meta["n_char"])
        self.idf = np.fromfile(model_dir / "idf.f32", dtype="<f4").astype(np.float64)
        coef = np.fromfile(model_dir / f"coef_{info['id']}.f32", dtype="<f4")
        self.coef = coef.reshape(len(LABELS), info["n_cols"]).astype(np.float64)
        self.offset = np.asarray(info["intercept"], dtype=np.float64) + np.asarray(info["bias"], dtype=np.float64)
        self.temperature: float = info["temperature"]
        self._char_cache: dict[str, np.ndarray] = {}

    @staticmethod
    def _vocab(path: Path, expected: int) -> dict[str, int]:
        # spasi di awal/akhir token adalah bagian dari n-gram karakter, jadi hanya \r yang dibuang
        lines = path.read_text(encoding="utf-8").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        if len(lines) != expected:
            raise ValueError(f"{path.name}: {len(lines)} baris, harusnya {expected}")
        return {t.rstrip("\r"): i for i, t in enumerate(lines)}

    def _char_features(self, tok: str) -> np.ndarray:
        """Kolom n-gram karakter yang dikenal untuk satu token. Token sering berulang, jadi hasilnya disimpan."""
        hit = self._char_cache.get(tok)
        if hit is None:
            cfg = self.config
            grams = char_ngrams([tok], cfg["char_min"], cfg["char_max"])
            hit = np.asarray([self.n_word + i for g in grams if (i := self.char_index.get(g)) is not None], dtype=np.int64)
            if len(self._char_cache) > 200_000:
                self._char_cache.clear()
            self._char_cache[tok] = hit
        return hit

    def _word_features(self, toks: list[str], first_tok: int, occ: list, cols: list, owners: list) -> None:
        """Kolom n-gram kata yang dikenal. occ: satu baris per kemunculan (kolom, token pertama).
        cols/owners: satu baris per (kolom, token pemilik), bigram punya dua pemilik."""
        cfg = self.config
        grams = word_ngrams(toks, cfg["word_ngram_max"])
        g = 0
        # word_ngrams mengurutkan unigram dulu lalu n-gram, jadi posisi token tiap n-gram bisa direkonstruksi
        for n in range(1, cfg["word_ngram_max"] + 1):
            for i in range(len(toks) - n + 1):
                col = self.word_index.get(grams[g])
                g += 1
                if col is not None:
                    occ.append((col, first_tok + i))
                    cols.extend([col] * n)
                    owners.extend(range(first_tok + i, first_tok + i + n))

    def predict_many(self, texts: list[str]) -> list[Prediction]:
        if not texts:
            return []
        n, nf = len(texts), self.n_feat
        toks_all = [tokens(t, self.config["use_slang"]) for t in texts]
        tok_start = np.concatenate([[0], np.cumsum([len(t) for t in toks_all])]).astype(np.int64)
        n_tok = int(tok_start[-1])
        tok_row = np.repeat(np.arange(n), np.diff(tok_start))  # ulasan asal tiap token

        # 1. kumpulkan pasangan (kolom fitur, token pemilik) dari semua ulasan
        w_occ: list[tuple[int, int]] = []
        w_cols: list[int] = []
        w_owner: list[int] = []
        for r, toks in enumerate(toks_all):
            self._word_features(toks, int(tok_start[r]), w_occ, w_cols, w_owner)
        w_occ_a = np.asarray(w_occ, dtype=np.int64).reshape(-1, 2)
        w_cols_a = np.asarray(w_cols, dtype=np.int64)
        w_owner_a = np.asarray(w_owner, dtype=np.int64)
        if self.config["use_char"] and n_tok:
            per_tok = [self._char_features(t) for toks in toks_all for t in toks]
            c_cols = np.concatenate(per_tok)
            c_owner = np.repeat(np.arange(n_tok), [len(x) for x in per_tok])
        else:
            c_cols = c_owner = np.zeros(0, dtype=np.int64)

        # 2. TF-IDF: count per (ulasan, fitur), tf = 1 + ln(count), kali idf
        occ_cell = np.concatenate([tok_row[w_occ_a[:, 1]] * nf + w_occ_a[:, 0], tok_row[c_owner] * nf + c_cols])
        cell, count = _unique_counts(occ_cell)
        r, c = cell // nf, cell % nf
        val = (1 + np.log(count)) * self.idf[c]

        # 3. normalisasi L2 terpisah untuk blok kata dan blok karakter di tiap ulasan
        group = r * 2 + (c >= self.n_word)
        norm = np.sqrt(np.bincount(group, weights=val * val, minlength=2 * n))
        val = val / norm[group]

        # 4. skor kelas = W x + intercept + bias, lalu softmax(skor / T)
        w = self.coef[:, c]
        scores = self.offset[:, None] + np.stack([np.bincount(r, weights=w[k] * val, minlength=n) for k in range(len(LABELS))])
        z = scores / self.temperature
        prob = np.exp(z - z.max(axis=0))
        prob /= prob.sum(axis=0)
        best = prob.argmax(axis=0)
        has_feat = np.bincount(r, minlength=n) > 0

        # 5. atribusi: dorongan tiap fitur ke kelas terpilih dibanding rata-rata kelas lain,
        #    dibagi rata ke token pemiliknya
        k = len(LABELS)
        w_best = w[best[r], np.arange(len(c))]
        push = (w_best - (w.sum(axis=0) - w_best) / (k - 1)) * val
        owner = np.concatenate([w_owner_a, c_owner])
        span = max(n_tok, 1)
        # kunci diurutkan menurut sel (ulasan, fitur) dulu, supaya pencarian posisi sel berjalan berurutan
        pair, _ = _unique_counts((tok_row[owner] * nf + np.concatenate([w_cols_a, c_cols])) * span + owner)
        p_owner = pair % span
        pos = np.searchsorted(cell, pair // span)
        n_owner = np.bincount(pos, minlength=len(cell))
        contrib = np.bincount(p_owner, weights=push[pos] / n_owner[pos], minlength=n_tok)

        out = []
        for i, toks in enumerate(toks_all):
            weights = contrib[tok_start[i] : tok_start[i + 1]].tolist()
            if not has_feat[i]:
                out.append(Prediction(None, None, None, tuple((t, 0.0) for t in toks)))
                continue
            p = tuple(float(x) for x in prob[:, i])
            out.append(Prediction(LABELS[best[i]], p[best[i]], p, tuple(zip(toks, weights))))
        return out

    def predict(self, text: str) -> Prediction:
        return self.predict_many([text])[0]


def _unique_counts(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Nilai unik terurut beserta jumlahnya (versi sort, jauh lebih cepat dari np.unique untuk jutaan angka)."""
    a = np.sort(a)
    if len(a) == 0:
        return a, a
    start = np.flatnonzero(np.concatenate([[True], a[1:] != a[:-1]]))
    return a[start], np.diff(np.append(start, len(a)))
