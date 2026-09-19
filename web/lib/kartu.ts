// Kartu hasil untuk dibagikan: digambar di canvas lalu diunduh sebagai PNG. Semua di browser.

import { downloadBlob } from "./download";
import { CLASS_HEX, LABEL_ID, LABELS, type Label } from "./fmt";

const W = 1080;
const H = 1350;
const KERTAS = "#efe7d6";
const ASPAL = "#141210";
const MERAH = "#ce1126";

function fam(name: string, fallback: string): string {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v ? `${v}, ${fallback}` : fallback;
}

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const w of words) {
    const next = line ? `${line} ${w}` : w;
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line);
      line = w;
      if (lines.length === maxLines) break;
    } else line = next;
  }
  if (lines.length < maxLines && line) lines.push(line);
  if (lines.length === maxLines) {
    const last = lines[maxLines - 1];
    if (words.join(" ").length > lines.join(" ").length) lines[maxLines - 1] = `${last.slice(0, -2)}...`;
  }
  return lines;
}

export async function unduhKartu(opts: {
  label: Label;
  probs: Record<Label, number>;
  modelName: string;
  text?: string;
  drivers: string[];
}) {
  await document.fonts.ready;
  const display = fam("--font-shoulders", "Impact, sans-serif");
  const sans = fam("--font-jakarta", "Arial, sans-serif");
  const marker = fam("--font-marker", "Comic Sans MS, cursive");
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;
  const warna = CLASS_HEX[opts.label];

  ctx.fillStyle = KERTAS;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = MERAH;
  ctx.fillRect(0, 0, W, 96);
  ctx.fillStyle = "#ffffff";
  ctx.font = `900 54px ${display}`;
  ctx.textBaseline = "middle";
  ctx.fillText("SUARA RAKYAT", 56, 52);
  ctx.font = `500 26px ${sans}`;
  ctx.textAlign = "right";
  ctx.fillText("suara-rakyat-xi.vercel.app", W - 56, 54);
  ctx.textAlign = "left";

  ctx.fillStyle = "#6f675c";
  ctx.font = `600 26px ${sans}`;
  ctx.fillText(`DIBACA OLEH ${opts.modelName.toUpperCase()}`, 56, 168);

  // stempel hasil
  ctx.save();
  ctx.translate(56, 230);
  ctx.rotate((-3 * Math.PI) / 180);
  ctx.font = `900 150px ${display}`;
  const teks = LABEL_ID[opts.label].toUpperCase();
  const lebar = ctx.measureText(teks).width;
  ctx.strokeStyle = warna;
  ctx.lineWidth = 8;
  ctx.strokeRect(0, 0, lebar + 64, 190);
  ctx.fillStyle = warna;
  ctx.fillText(teks, 32, 104);
  ctx.restore();

  ctx.fillStyle = ASPAL;
  ctx.font = `700 36px ${sans}`;
  ctx.fillText(`Keyakinan ${Math.round(opts.probs[opts.label] * 100)}%`, 56, 500);

  // batang peluang tiap kelas
  let y = 560;
  for (const l of LABELS) {
    ctx.fillStyle = "#6f675c";
    ctx.font = `500 26px ${sans}`;
    ctx.fillText(LABEL_ID[l], 56, y + 22);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(220, y + 6, 700, 32);
    ctx.fillStyle = CLASS_HEX[l];
    ctx.fillRect(220, y + 6, Math.max(4, 700 * opts.probs[l]), 32);
    ctx.fillStyle = ASPAL;
    ctx.font = `600 24px ${sans}`;
    ctx.textAlign = "right";
    ctx.fillText(`${(opts.probs[l] * 100).toFixed(1).replace(".", ",")}%`, W - 56, y + 24);
    ctx.textAlign = "left";
    y += 58;
  }

  let bawah = 860;
  if (opts.text) {
    ctx.font = `400 40px ${marker}`;
    const lines = wrap(ctx, `"${opts.text}"`, W - 180, 6);
    const tinggi = 60 + lines.length * 46;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(56, 780, W - 112, tinggi);
    ctx.strokeStyle = ASPAL;
    ctx.lineWidth = 4;
    ctx.strokeRect(56, 780, W - 112, tinggi);
    ctx.fillStyle = ASPAL;
    ctx.font = `400 40px ${marker}`;
    lines.forEach((l, i) => ctx.fillText(l, 88, 836 + i * 46));
    bawah = 780 + tinggi + 56;
  }

  if (opts.drivers.length) {
    ctx.fillStyle = "#6f675c";
    ctx.font = `500 26px ${sans}`;
    ctx.fillText(`Kata penentu: ${opts.drivers.slice(0, 4).join(", ")}`, 56, bawah);
  }

  ctx.fillStyle = MERAH;
  ctx.fillRect(0, H - 90, W, 8);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, H - 82, W, 8);
  ctx.fillStyle = "#6f675c";
  ctx.font = `500 24px ${sans}`;
  ctx.fillText("Model sentimen ulasan aplikasi layanan publik, projek AOL Software Engineering.", 56, H - 48);
  ctx.fillText("Hasil model, bukan penilaian resmi instansi mana pun.", 56, H - 20);

  const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/png"));
  if (blob) downloadBlob(blob, `suara-rakyat-${opts.label}.png`);
}
