"""Fitur TF-IDF kata dan karakter yang bisa ditiru persis di web.

Rumus yang dipakai (sama dengan sklearn TfidfVectorizer default + sublinear_tf):
  tf  = 1 + ln(jumlah kemunculan)
  idf = ln((1 + N) / (1 + df)) + 1
  x   = tf * idf, lalu dinormalisasi L2 per blok (kata dan karakter terpisah)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

from .textnorm import char_ngrams, tokens, word_ngrams


def _identity(doc):
    return doc


@dataclass
class FeatureConfig:
    use_slang: bool = True
    word_ngram_max: int = 2
    word_min_df: int = 2
    word_max_features: int | None = None
    use_char: bool = True
    char_min: int = 2
    char_max: int = 5
    char_min_df: int = 3
    char_max_features: int | None = None


class TextFeaturizer:
    def __init__(self, cfg: FeatureConfig):
        self.cfg = cfg
        self.word_vec = TfidfVectorizer(
            analyzer=_identity,
            sublinear_tf=True,
            min_df=cfg.word_min_df,
            max_features=cfg.word_max_features,
            dtype=np.float32,
        )
        self.char_vec = (
            TfidfVectorizer(
                analyzer=_identity,
                sublinear_tf=True,
                min_df=cfg.char_min_df,
                max_features=cfg.char_max_features,
                dtype=np.float32,
            )
            if cfg.use_char
            else None
        )

    def _toks(self, texts):
        return [tokens(t, use_slang=self.cfg.use_slang) for t in texts]

    # generator, supaya n-gram karakter tidak ditampung semua di memori sekaligus
    def _word_docs(self, toks):
        return (word_ngrams(t, self.cfg.word_ngram_max) for t in toks)

    def _char_docs(self, toks):
        return (char_ngrams(t, self.cfg.char_min, self.cfg.char_max) for t in toks)

    def fit_transform(self, texts) -> sp.csr_matrix:
        toks = self._toks(texts)
        blocks = [self.word_vec.fit_transform(self._word_docs(toks))]
        if self.char_vec is not None:
            blocks.append(self.char_vec.fit_transform(self._char_docs(toks)))
        return sp.hstack(blocks, format="csr", dtype=np.float32)

    def transform(self, texts) -> sp.csr_matrix:
        toks = self._toks(texts)
        blocks = [self.word_vec.transform(self._word_docs(toks))]
        if self.char_vec is not None:
            blocks.append(self.char_vec.transform(self._char_docs(toks)))
        return sp.hstack(blocks, format="csr", dtype=np.float32)

    @property
    def n_word(self) -> int:
        return len(self.word_vec.vocabulary_)

    @property
    def n_features(self) -> int:
        n = self.n_word
        if self.char_vec is not None:
            n += len(self.char_vec.vocabulary_)
        return n

    def feature_names(self) -> list[str]:
        names = [""] * self.n_features
        for term, idx in self.word_vec.vocabulary_.items():
            names[idx] = "w:" + term
        if self.char_vec is not None:
            off = self.n_word
            for term, idx in self.char_vec.vocabulary_.items():
                names[off + idx] = "c:" + term
        return names
