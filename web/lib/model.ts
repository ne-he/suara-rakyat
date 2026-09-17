// Inferensi model linear TF-IDF (kata + karakter) hasil export ml/scripts/05_export_web.py.
// Rumus fitur sama dengan ml/suara_ml/features.py:
//   tf = 1 + ln(count), x = tf * idf, dinormalisasi L2 per blok (kata, karakter).
// Skor kelas = W x + b + bias, probabilitas = softmax(skor / T).

import fs from "node:fs";
import path from "node:path";
import { charNgramsOf, tokens, wordNgrams } from "./textnorm";

export type Label = "negative" | "neutral" | "positive";

export type ModelMeta = {
  version: string;
  labels: Label[];
  config: {
    use_slang: boolean;
    word_ngram_max: number;
    use_char: boolean;
    char_min: number;
    char_max: number;
  };
  n_word: number;
  n_char: number;
  intercept: number[];
  bias: number[];
  temperature: number;
  source_run: string;
  metrics: Record<string, unknown>;
};

export type TokenContribution = { token: string; weight: number };

export type Prediction = {
  label: Label;
  probs: Record<Label, number>;
  tokens: TokenContribution[];
  empty: boolean;
};

type Model = {
  meta: ModelMeta;
  wordIndex: Map<string, number>;
  charIndex: Map<string, number>;
  idf: Float32Array;
  coef: Float32Array; // [kelas * nFitur], baris per kelas
};

let cached: Model | null = null;

function readFloat32(file: string): Float32Array {
  const buf = fs.readFileSync(file);
  const copy = new ArrayBuffer(buf.byteLength);
  new Uint8Array(copy).set(buf);
  return new Float32Array(copy);
}

function readVocab(file: string, expected: number): Map<string, number> {
  // token tidak pernah berisi \r, jadi aman menerima file LF maupun CRLF
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);
  if (lines.length && lines[lines.length - 1] === "") lines.pop();
  if (lines.length !== expected) {
    throw new Error(`vocab ${path.basename(file)}: ${lines.length} baris, harusnya ${expected}`);
  }
  const m = new Map<string, number>();
  lines.forEach((t, i) => m.set(t, i));
  return m;
}

export function loadModel(dir = path.join(process.cwd(), "model")): Model {
  if (cached) return cached;
  const meta = JSON.parse(fs.readFileSync(path.join(dir, "meta.json"), "utf8")) as ModelMeta;
  const nFeat = meta.n_word + meta.n_char;
  const wordIndex = readVocab(path.join(dir, "vocab_word.txt"), meta.n_word);
  const charIndex = meta.config.use_char
    ? readVocab(path.join(dir, "vocab_char.txt"), meta.n_char)
    : new Map<string, number>();
  const idf = readFloat32(path.join(dir, "idf.f32"));
  const coef = readFloat32(path.join(dir, "coef.f32"));
  if (idf.length !== nFeat || coef.length !== nFeat * meta.labels.length) {
    throw new Error("ukuran idf/coef tidak cocok dengan meta.json");
  }
  cached = { meta, wordIndex, charIndex, idf, coef };
  return cached;
}

type Entry = { idx: number; value: number; owners: number[] };

/** Hitung vektor TF-IDF satu blok. owners = indeks token asal tiap fitur (untuk atribusi). */
function block(
  feats: { term: string; owners: number[] }[],
  index: Map<string, number>,
  idf: Float32Array,
  offset: number,
): Entry[] {
  const counts = new Map<number, { count: number; owners: Set<number> }>();
  for (const f of feats) {
    const i = index.get(f.term);
    if (i === undefined) continue;
    const e = counts.get(i) ?? { count: 0, owners: new Set<number>() };
    e.count += 1;
    f.owners.forEach((o) => e.owners.add(o));
    counts.set(i, e);
  }
  const entries: Entry[] = [];
  let norm = 0;
  for (const [i, e] of counts) {
    const v = (1 + Math.log(e.count)) * idf[offset + i];
    norm += v * v;
    entries.push({ idx: offset + i, value: v, owners: [...e.owners] });
  }
  norm = Math.sqrt(norm);
  if (norm > 0) for (const e of entries) e.value /= norm;
  return entries;
}

export function predict(text: string): Prediction {
  const { meta, wordIndex, charIndex, idf, coef } = loadModel();
  const K = meta.labels.length;
  const nFeat = meta.n_word + meta.n_char;
  const toks = tokens(text, meta.config.use_slang);

  const wordFeats: { term: string; owners: number[] }[] = [];
  const grams = wordNgrams(toks, meta.config.word_ngram_max);
  // wordNgrams mengurutkan unigram dulu lalu n-gram; rekonstruksi pemilik token
  let g = 0;
  for (let i = 0; i < toks.length; i++) wordFeats.push({ term: grams[g++], owners: [i] });
  for (let n = 2; n <= meta.config.word_ngram_max; n++) {
    for (let i = 0; i + n <= toks.length; i++) {
      wordFeats.push({ term: grams[g++], owners: Array.from({ length: n }, (_, k) => i + k) });
    }
  }
  const entries = block(wordFeats, wordIndex, idf, 0);

  if (meta.config.use_char) {
    const charFeats: { term: string; owners: number[] }[] = [];
    toks.forEach((t, i) => {
      for (const c of charNgramsOf(t, meta.config.char_min, meta.config.char_max)) {
        charFeats.push({ term: c, owners: [i] });
      }
    });
    entries.push(...block(charFeats, charIndex, idf, meta.n_word));
  }

  const scores = meta.intercept.map((b, k) => b + meta.bias[k]);
  for (const e of entries) {
    for (let k = 0; k < K; k++) scores[k] += coef[k * nFeat + e.idx] * e.value;
  }
  const T = meta.temperature;
  const mx = Math.max(...scores.map((s) => s / T));
  const exps = scores.map((s) => Math.exp(s / T - mx));
  const z = exps.reduce((a, b) => a + b, 0);
  const p = exps.map((e) => e / z);
  const best = p.indexOf(Math.max(...p));

  // Atribusi: dorongan tiap fitur ke kelas terpilih dibanding rata-rata kelas lain,
  // dibagi rata ke token pemiliknya.
  const contrib = new Array<number>(toks.length).fill(0);
  for (const e of entries) {
    let others = 0;
    for (let k = 0; k < K; k++) if (k !== best) others += coef[k * nFeat + e.idx];
    const push = (coef[best * nFeat + e.idx] - others / (K - 1)) * e.value;
    for (const o of e.owners) contrib[o] += push / e.owners.length;
  }

  const probs = Object.fromEntries(meta.labels.map((l, k) => [l, p[k]])) as Record<Label, number>;
  return {
    label: meta.labels[best],
    probs,
    tokens: toks.map((token, i) => ({ token, weight: contrib[i] })),
    empty: entries.length === 0,
  };
}
