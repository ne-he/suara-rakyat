"""Uji paritas: hasil classifier Python v5 harus sama dengan Linear SVM asli (sklearn) di 3.018 teks."""

import json
import math

import numpy as np
import pytest

from suara.classifier import LABELS, ROOT, SentimentClassifier
from suara_ml.textnorm import char_ngrams, tokens, word_ngrams

SAMPLES = json.loads((ROOT / "web" / "scripts" / "parity_samples.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def clf():
    return SentimentClassifier()


def test_parity_with_sklearn(clf):
    preds = clf.predict_many([s["text"] for s in SAMPLES])
    mismatch, max_diff = 0, 0.0
    for s, got in zip(SAMPLES, preds):
        exp = s["probs"]["svm"]
        if got.label is None:
            continue
        max_diff = max(max_diff, max(abs(a - b) for a, b in zip(got.probs, exp)))
        mismatch += got.label != LABELS[exp.index(max(exp))]
    print(f"samples={len(SAMPLES)} label_mismatch={mismatch} max_prob_diff={max_diff:.2e}")
    assert mismatch == 0
    assert max_diff < 1e-5


def reference_contributions(clf, text):
    """Atribusi versi lambat, ditulis langsung mengikuti web/lib/model.ts, sebagai pembanding."""
    cfg = clf.config
    toks = tokens(text, cfg["use_slang"])
    grams = word_ngrams(toks, cfg["word_ngram_max"])
    owners = [(i,) for i in range(len(toks))] + [(i, i + 1) for i in range(len(toks) - 1)]
    feats = [(clf.word_index.get(g), o) for g, o in zip(grams, owners)]
    char = [(clf.char_index.get(x), (i,)) for i, t in enumerate(toks) for x in char_ngrams([t], cfg["char_min"], cfg["char_max"])]
    entries = []
    for block, offset in ((feats, 0), (char, clf.n_word)):
        counts = {}
        for col, own in block:
            if col is None:
                continue
            e = counts.setdefault(offset + col, [0, set()])
            e[0] += 1
            e[1].update(own)
        vals = {col: (1 + math.log(cnt)) * clf.idf[col] for col, (cnt, _) in counts.items()}
        norm = math.sqrt(sum(v * v for v in vals.values()))
        entries += [(col, vals[col] / norm, sorted(own)) for col, (_, own) in counts.items()]
    scores = clf.offset + sum(clf.coef[:, col] * v for col, v, _ in entries)
    best = int(np.argmax(scores))
    contrib = [0.0] * len(toks)
    for col, v, own in entries:
        w = clf.coef[:, col]
        push = (w[best] - (w.sum() - w[best]) / 2) * v
        for o in own:
            contrib[o] += push / len(own)
    return contrib


def test_contributions_match_reference(clf):
    texts = [s["text"] for s in SAMPLES[:200]]
    for text, p in zip(texts, clf.predict_many(texts)):
        if p.label is None:
            continue
        got = [w for _, w in p.tokens]
        assert np.allclose(got, reference_contributions(clf, text), atol=1e-9), text


def test_batch_equals_single(clf):
    texts = ["gk bisa login", "", "mantap", "otp tidak masuk masuk masuk"]
    for single, text in zip(clf.predict_many(texts), texts):
        assert single == clf.predict(text)


def test_unreadable_text_has_no_label(clf):
    for text in ["", "   ", "!!! ???", "⭐⭐⭐"]:
        p = clf.predict(text)
        assert p.label is None and p.confidence is None


def test_obvious_examples(clf):
    assert clf.predict("aplikasi error terus, gak bisa login, otp tidak masuk").label == "negative"
    assert clf.predict("mantap sangat membantu, terima kasih").label == "positive"


def test_token_contributions_follow_tokens(clf):
    p = clf.predict("gk bisa login")
    assert [t for t, _ in p.tokens] == ["tidak", "bisa", "login"]
