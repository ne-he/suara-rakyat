// Label sekumpulan teks dengan 3 model web, lewat kode yang persis sama dengan API.
// Dipakai skrip Python (uji tahan bahasa, lembar anotasi) supaya hasilnya identik dengan yang dilihat pengunjung.
// Jalankan: npx tsx scripts/label-file.ts masuk.json keluar.json
// masuk.json berisi array teks. keluar.json berisi array { svm, logreg, nb } dengan label dan peluang.

import fs from "node:fs";
import { predictAll } from "../lib/model";

const [, , inFile, outFile] = process.argv;
if (!inFile || !outFile) {
  console.error("pakai: tsx scripts/label-file.ts masuk.json keluar.json");
  process.exit(1);
}

const texts = JSON.parse(fs.readFileSync(inFile, "utf8")) as string[];
const out = texts.map((t) => {
  const all = predictAll(t);
  return Object.fromEntries(Object.entries(all).map(([id, p]) => [id, { label: p.label, probs: p.probs, empty: p.empty }]));
});
fs.writeFileSync(outFile, JSON.stringify(out));
console.log(`${texts.length} teks dilabeli`);
