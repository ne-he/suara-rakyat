"""Normalisasi dan tokenisasi teks ulasan.

Semua aturan di sini sengaja dibuat sederhana dan deterministik supaya bisa
ditiru persis di TypeScript (web/lib/textnorm.ts). Kalau aturan diubah di sini,
ubah juga di sana lalu jalankan uji paritas.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

SLANG_PATH = Path(__file__).with_name("slang_id.json")

URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
REPEAT_RE = re.compile(r"(.)\1{2,}")
TOKEN_RE = re.compile(r"[a-z0-9]+|[☀-➿\U0001f300-\U0001faff]")


@lru_cache(maxsize=1)
def slang_map() -> dict[str, str]:
    with open(SLANG_PATH, encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    """Teks mentah ke teks bersih (huruf kecil, tanpa URL, huruf berulang dipangkas)."""
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKC", text).lower()
    t = URL_RE.sub(" ", t)
    t = REPEAT_RE.sub(r"\1\1", t)
    return t


def tokens(text: str, use_slang: bool = True) -> list[str]:
    """Token kata setelah normalisasi. Slang dipetakan ke bentuk baku."""
    toks = TOKEN_RE.findall(normalize(text))
    if use_slang:
        sm = slang_map()
        out: list[str] = []
        for tok in toks:
            out.extend(sm.get(tok, tok).split())
        return out
    return toks


def word_ngrams(toks: list[str], n_max: int = 2) -> list[str]:
    feats = list(toks)
    for n in range(2, n_max + 1):
        feats.extend(" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1))
    return feats


def char_ngrams(toks: list[str], n_min: int = 2, n_max: int = 5) -> list[str]:
    """N-gram karakter per token, token dibungkus spasi (mirip char_wb sklearn)."""
    feats: list[str] = []
    for tok in toks:
        w = " " + tok + " "
        L = len(w)
        for n in range(n_min, n_max + 1):
            if n > L:
                break
            feats.extend(w[i : i + n] for i in range(L - n + 1))
    return feats


_DIGITS_RE = re.compile(r"\d{6,}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def mask_personal(text: str) -> str:
    """Samarkan deret angka panjang dan email sebelum teks ulasan dipublikasikan."""
    return _DIGITS_RE.sub("[angka]", _EMAIL_RE.sub("[email]", text))
