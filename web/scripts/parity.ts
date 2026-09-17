// Uji paritas: prediksi web (TypeScript) harus sama dengan prediksi Python.
// Sampel dibuat oleh ml/scripts/05_export_web.py. Jalankan: npm run parity

import fs from "node:fs";
import path from "node:path";
import { predict } from "../lib/model";

type Sample = { text: string; label: string; probs: number[] };

const samples = JSON.parse(
  fs.readFileSync(path.join(__dirname, "parity_samples.json"), "utf8"),
) as Sample[];

let labelMismatch = 0;
let maxDiff = 0;
const bad: string[] = [];
const t0 = performance.now();
for (const s of samples) {
  const p = predict(s.text);
  const got = [p.probs.negative, p.probs.neutral, p.probs.positive];
  const diff = Math.max(...got.map((g, i) => Math.abs(g - s.probs[i])));
  maxDiff = Math.max(maxDiff, diff);
  if (p.label !== s.label || diff > 1e-3) {
    labelMismatch += p.label !== s.label ? 1 : 0;
    if (bad.length < 10) bad.push(`${JSON.stringify(s.text)} py=${s.label} ${s.probs} ts=${p.label} ${got}`);
  }
}
const ms = (performance.now() - t0) / samples.length;
console.log(`samples=${samples.length} label_mismatch=${labelMismatch} max_prob_diff=${maxDiff.toExponential(2)} avg_ms=${ms.toFixed(3)}`);
bad.forEach((b) => console.log("  " + b));
if (labelMismatch > 0 || maxDiff > 1e-3) process.exit(1);
