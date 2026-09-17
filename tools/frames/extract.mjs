// Potong video scene jadi urutan frame WebP untuk scroll story di web.
//
// Pakai:
//   1. Taruh video di tools/frames/media/ dengan nama scene-1.mp4, scene-2.mp4, scene-3.mp4 (urut cerita)
//   2. cd tools/frames && npm install && npm run frames
// Hasil: web/public/frames/scene-N/{d,m}/0001.webp + web/public/frames/manifest.json
//   d = desktop (lebar 1280), m = HP (lebar 640). Web otomatis memakai frame ini kalau manifest ada.
// Opsi env: FPS (default 12), QD (kualitas desktop, 68), QM (kualitas HP, 62)

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ffmpeg from "ffmpeg-static";

const here = path.dirname(fileURLToPath(import.meta.url));
const mediaDir = path.join(here, "media");
const outRoot = path.resolve(here, "../../web/public/frames");
const FPS = Number(process.env.FPS ?? 12);
const VARIANTS = [
  { key: "d", width: 1280, quality: Number(process.env.QD ?? 68) },
  { key: "m", width: 640, quality: Number(process.env.QM ?? 62) },
];

function run(args) {
  const r = spawnSync(ffmpeg, args, { encoding: "utf8" });
  if (r.status !== 0) throw new Error(`ffmpeg gagal:\n${r.stderr.slice(-1500)}`);
  return r.stderr;
}

function probeSize(file) {
  const r = spawnSync(ffmpeg, ["-hide_banner", "-i", file], { encoding: "utf8" });
  const m = r.stderr.match(/Video:.*?(\d{2,5})x(\d{2,5})/);
  if (!m) throw new Error(`tidak bisa membaca ukuran video ${file}`);
  return { w: Number(m[1]), h: Number(m[2]) };
}

const videos = fs.existsSync(mediaDir)
  ? fs
      .readdirSync(mediaDir)
      .filter((f) => /^scene-\d+\.(mp4|webm|mov)$/i.test(f))
      .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))
  : [];

if (videos.length === 0) {
  console.error(`Tidak ada video. Taruh scene-1.mp4, scene-2.mp4, ... di ${mediaDir}`);
  process.exit(1);
}

fs.rmSync(outRoot, { recursive: true, force: true });
const manifest = { fps: FPS, generated: new Date().toISOString(), scenes: [] };

for (const file of videos) {
  const id = path.parse(file).name;
  const src = path.join(mediaDir, file);
  const { w, h } = probeSize(src);
  const scene = { id, variants: {} };
  for (const v of VARIANTS) {
    const dir = path.join(outRoot, id, v.key);
    fs.mkdirSync(dir, { recursive: true });
    const height = Math.round((h * v.width) / w / 2) * 2;
    run([
      "-hide_banner", "-y", "-i", src,
      "-vf", `fps=${FPS},scale=${v.width}:${height}:flags=lanczos`,
      "-an", "-c:v", "libwebp", "-quality", String(v.quality), "-compression_level", "4",
      "-f", "image2", path.join(dir, "%04d.webp"),
    ]);
    const frames = fs.readdirSync(dir).filter((f) => f.endsWith(".webp")).length;
    const bytes = fs.readdirSync(dir).reduce((s, f) => s + fs.statSync(path.join(dir, f)).size, 0);
    scene.variants[v.key] = { width: v.width, height, frames, mb: Math.round(bytes / 1e5) / 10 };
    console.log(`${id}/${v.key}: ${frames} frame, ${v.width}x${height}, ${scene.variants[v.key].mb} MB`);
  }
  manifest.scenes.push(scene);
}

fs.writeFileSync(path.join(outRoot, "manifest.json"), JSON.stringify(manifest, null, 2));
console.log(`manifest: ${path.join(outRoot, "manifest.json")}`);
