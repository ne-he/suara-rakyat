// Uji kecepatan baca per ulasan untuk tiap model web (CPU, satu ulasan per panggilan, seperti di API).
// Teks diambil dari sampel paritas (3.000 ulasan validation). Jalankan: npm run bench
// Hasil ditulis ke data/speed.json dan ditampilkan di panel bukti.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadModels, predictAll, predictOne } from "../lib/model";

type Sample = { text: string };
const texts = (JSON.parse(fs.readFileSync(path.join(__dirname, "parity_samples.json"), "utf8")) as Sample[])
  .map((s) => s.text)
  .filter((t) => t.trim().length > 0);

const ROUNDS = 3;
const { meta } = loadModels();

function timeIt(fn: (t: string) => unknown): number {
  for (const t of texts.slice(0, 300)) fn(t); // pemanasan JIT
  const perRound: number[] = [];
  for (let r = 0; r < ROUNDS; r++) {
    const t0 = performance.now();
    for (const t of texts) fn(t);
    perRound.push((performance.now() - t0) / texts.length);
  }
  return Math.min(...perRound); // ronde tercepat, paling sedikit gangguan proses lain
}

const out = {
  measured: new Date().toISOString().slice(0, 10),
  cpu: os.cpus()[0]?.model.trim() ?? "?",
  node: process.version,
  n_texts: texts.length,
  ms_per_review: Object.fromEntries(meta.models.map((m) => [m.id, +timeIt((t) => predictOne(t, m.id)).toFixed(3)])),
  ms_all_models: +timeIt(predictAll).toFixed(3),
};
fs.mkdirSync(path.join(__dirname, "..", "data"), { recursive: true });
fs.writeFileSync(path.join(__dirname, "..", "data", "speed.json"), JSON.stringify(out, null, 2) + "\n");
console.log(out);
