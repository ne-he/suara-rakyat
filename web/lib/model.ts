// Inferensi 3 model linear TF-IDF (kata + karakter) hasil export ml/scripts/05_export_web.py.
// Rumus fitur sama dengan ml/suara_ml/features.py:
//   tf = 1 + ln(count), x = tf * idf, dinormalisasi L2 per blok (kata, karakter).
// Skor kelas = W x + b + bias, probabilitas = softmax(skor / T).
// Fitur dihitung sekali, lalu dipakai semua model. Model kata (Naive Bayes) cuma membaca blok kata.

import fs from "node:fs";
import path from "node:path";
import { charNgramsOf, tokens, wordNgrams } from "./textnorm";

export type Label = "negative" | "neutral" | "positive";

export type ModelInfo = {
  id: string;
  run: string;
  name: string;
  features: string;
  tagline: string;
  n_cols: number;
  intercept: number[];
  bias: number[];
  temperature: number;
  fit_seconds: number;
  metrics: {
    val_macro_f1: number;
    test_macro_f1_raw: number;
    polarity_flip_rate: number;
    binary_neg_pos_accuracy: number;
    binary_neg_pos_macro_f1: number;
    test_by_app: Record<string, number>;
    test: {
      macro_f1: number;
      accuracy: number;
      weighted_f1: number;
      per_class: Record<Label, { precision: number; recall: number; f1: number; support: number }>;
      confusion: number[][];
    };
  };
};

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
  default_model: string;
  models: ModelInfo[];
};

export type TokenContribution = { token: string; weight: number };

export type Prediction = {
  model: string;
  label: Label;
  probs: Record<Label, number>;
  tokens: TokenContribution[];
  empty: boolean;
};

type Loaded = {
  meta: ModelMeta;
  wordIndex: Map<string, number>;
  charIndex: Map<string, number>;
  idf: Float32Array;
  coef: Map<string, Float32Array>; // [kelas * n_cols], baris per kelas
};

let cached: Loaded | null = null;

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

export function loadModels(dir = path.join(process.cwd(), "model")): Loaded {
  if (cached) return cached;
  const meta = JSON.parse(fs.readFileSync(path.join(dir, "meta.json"), "utf8")) as ModelMeta;
  const nFeat = meta.n_word + meta.n_char;
  const wordIndex = readVocab(path.join(dir, "vocab_word.txt"), meta.n_word);
  const charIndex = readVocab(path.join(dir, "vocab_char.txt"), meta.n_char);
  const idf = readFloat32(path.join(dir, "idf.f32"));
  if (idf.length !== nFeat) throw new Error("ukuran idf tidak cocok dengan meta.json");
  const coef = new Map<string, Float32Array>();
  for (const m of meta.models) {
    const w = readFloat32(path.join(dir, `coef_${m.id}.f32`));
    if (w.length !== m.n_cols * meta.labels.length) throw new Error(`ukuran coef_${m.id} tidak cocok`);
    coef.set(m.id, w);
  }
  cached = { meta, wordIndex, charIndex, idf, coef };
  return cached;
}

export function modelIds(): string[] {
  return loadModels().meta.models.map((m) => m.id);
}

type Entry = { idx: number; value: number; owners: number[] };
type Feat = { term: string; owners: number[] };

/** Vektor TF-IDF satu blok. owners = indeks token asal tiap fitur (untuk atribusi). */
function block(feats: Feat[], index: Map<string, number>, idf: Float32Array, offset: number): Entry[] {
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

function featurize(text: string) {
  const { meta, wordIndex, charIndex, idf } = loadModels();
  const toks = tokens(text, meta.config.use_slang);
  const grams = wordNgrams(toks, meta.config.word_ngram_max);
  // wordNgrams mengurutkan unigram dulu lalu n-gram, jadi pemilik token bisa direkonstruksi
  const wordFeats: Feat[] = [];
  let g = 0;
  for (let i = 0; i < toks.length; i++) wordFeats.push({ term: grams[g++], owners: [i] });
  for (let n = 2; n <= meta.config.word_ngram_max; n++) {
    for (let i = 0; i + n <= toks.length; i++) {
      wordFeats.push({ term: grams[g++], owners: Array.from({ length: n }, (_, k) => i + k) });
    }
  }
  const entries = block(wordFeats, wordIndex, idf, 0);
  if (meta.config.use_char) {
    const charFeats: Feat[] = [];
    toks.forEach((t, i) => {
      for (const c of charNgramsOf(t, meta.config.char_min, meta.config.char_max)) charFeats.push({ term: c, owners: [i] });
    });
    entries.push(...block(charFeats, charIndex, idf, meta.n_word));
  }
  return { toks, entries };
}

function run(info: ModelInfo, w: Float32Array, toks: string[], entries: Entry[], labels: Label[]): Prediction {
  const K = labels.length;
  const nCols = info.n_cols;
  const used = entries.filter((e) => e.idx < nCols);
  const scores = info.intercept.map((b, k) => b + info.bias[k]);
  for (const e of used) for (let k = 0; k < K; k++) scores[k] += w[k * nCols + e.idx] * e.value;

  const T = info.temperature;
  const mx = Math.max(...scores.map((s) => s / T));
  const exps = scores.map((s) => Math.exp(s / T - mx));
  const z = exps.reduce((a, b) => a + b, 0);
  const p = exps.map((e) => e / z);
  const best = p.indexOf(Math.max(...p));

  // Atribusi: dorongan fitur ke kelas terpilih dibanding rata-rata kelas lain, dibagi ke token pemiliknya
  const contrib = new Array<number>(toks.length).fill(0);
  for (const e of used) {
    let others = 0;
    for (let k = 0; k < K; k++) if (k !== best) others += w[k * nCols + e.idx];
    const push = (w[best * nCols + e.idx] - others / (K - 1)) * e.value;
    for (const o of e.owners) contrib[o] += push / e.owners.length;
  }

  return {
    model: info.id,
    label: labels[best],
    probs: Object.fromEntries(labels.map((l, k) => [l, p[k]])) as Record<Label, number>,
    tokens: toks.map((token, i) => ({ token, weight: contrib[i] })),
    empty: used.length === 0,
  };
}

/** Prediksi satu model saja (dipakai uji kecepatan per model). */
export function predictOne(text: string, id: string): Prediction {
  const { meta, coef } = loadModels();
  const info = meta.models.find((m) => m.id === id);
  if (!info) throw new Error(`model ${id} tidak ada`);
  const { toks, entries } = featurize(text);
  return run(info, coef.get(id)!, toks, entries, meta.labels);
}

/** Prediksi semua model sekaligus (fitur dihitung sekali). */
export function predictAll(text: string): Record<string, Prediction> {
  const { meta, coef } = loadModels();
  const { toks, entries } = featurize(text);
  const out: Record<string, Prediction> = {};
  for (const info of meta.models) out[info.id] = run(info, coef.get(info.id)!, toks, entries, meta.labels);
  return out;
}
