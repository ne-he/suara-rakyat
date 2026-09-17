// Port persis dari ml/suara_ml/textnorm.py. Kalau salah satu diubah, ubah keduanya
// lalu jalankan uji paritas (npm run parity).

import slang from "./slang_id.json";

const SLANG = slang as Record<string, string>;
const URL_RE = /(https?:\/\/\S+|www\.\S+)/gu;
const REPEAT_RE = /(.)\1{2,}/gu;
const TOKEN_RE = /[a-z0-9]+|[☀-➿\u{1F300}-\u{1FAFF}]/gu;

export function normalize(text: string): string {
  if (typeof text !== "string") return "";
  let t = text.normalize("NFKC").toLowerCase();
  t = t.replace(URL_RE, " ");
  t = t.replace(REPEAT_RE, "$1$1");
  return t;
}

export function tokens(text: string, useSlang = true): string[] {
  const raw = normalize(text).match(TOKEN_RE) ?? [];
  if (!useSlang) return raw;
  const out: string[] = [];
  for (const tok of raw) {
    const mapped = Object.prototype.hasOwnProperty.call(SLANG, tok) ? SLANG[tok] : tok;
    for (const part of mapped.split(/\s+/)) if (part) out.push(part);
  }
  return out;
}

export function wordNgrams(toks: string[], nMax = 2): string[] {
  const feats = [...toks];
  for (let n = 2; n <= nMax; n++) {
    for (let i = 0; i + n <= toks.length; i++) feats.push(toks.slice(i, i + n).join(" "));
  }
  return feats;
}

/** N-gram karakter per token (dihitung per code point, sama seperti Python). */
export function charNgramsOf(tok: string, nMin = 2, nMax = 5): string[] {
  const w = Array.from(" " + tok + " ");
  const L = w.length;
  const feats: string[] = [];
  for (let n = nMin; n <= nMax; n++) {
    if (n > L) break;
    for (let i = 0; i + n <= L; i++) feats.push(w.slice(i, i + n).join(""));
  }
  return feats;
}
