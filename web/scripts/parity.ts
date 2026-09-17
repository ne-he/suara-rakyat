// Uji paritas: prediksi web (TypeScript) untuk tiap model harus sama dengan prediksi Python.
// Sampel dibuat oleh ml/scripts/05_export_web.py. Jalankan: npm run parity

import fs from "node:fs";
import path from "node:path";
import { predictAll } from "../lib/model";

type Sample = { text: string; probs: Record<string, number[]> };

const samples = JSON.parse(fs.readFileSync(path.join(__dirname, "parity_samples.json"), "utf8")) as Sample[];
const LABELS = ["negative", "neutral", "positive"] as const;

const stats: Record<string, { mismatch: number; maxDiff: number }> = {};
const bad: string[] = [];
const t0 = performance.now();
for (const s of samples) {
  const all = predictAll(s.text);
  for (const [id, expected] of Object.entries(s.probs)) {
    const p = all[id];
    if (!p) throw new Error(`model ${id} tidak ada di web`);
    const got = LABELS.map((l) => p.probs[l]);
    const diff = Math.max(...got.map((g, i) => Math.abs(g - expected[i])));
    const expLabel = LABELS[expected.indexOf(Math.max(...expected))];
    const st = (stats[id] ??= { mismatch: 0, maxDiff: 0 });
    st.maxDiff = Math.max(st.maxDiff, diff);
    if (p.label !== expLabel) st.mismatch += 1;
    if ((p.label !== expLabel || diff > 1e-3) && bad.length < 10) {
      bad.push(`[${id}] ${JSON.stringify(s.text)} py=${expected} ts=${got}`);
    }
  }
}
const ms = (performance.now() - t0) / samples.length;
let failed = false;
for (const [id, st] of Object.entries(stats)) {
  console.log(`${id}: samples=${samples.length} label_mismatch=${st.mismatch} max_prob_diff=${st.maxDiff.toExponential(2)}`);
  if (st.mismatch > 0 || st.maxDiff > 1e-3) failed = true;
}
console.log(`avg_ms_all_models=${ms.toFixed(3)}`);
bad.forEach((b) => console.log("  " + b));
if (failed) process.exit(1);
