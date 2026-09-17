// Potong video scene jadi urutan frame WebP untuk scroll story di web.
//
// Pakai:
//   1. Taruh video di folder vid/ (root repo) dengan nama scene1.mp4, scene2.mp4, ... (urut cerita).
//      Nama scene-1.mp4 juga diterima. Folder lain: set env MEDIA=path.
//   2. Atur potongan dan porsi scroll di tools/frames/scenes.json (opsional).
//   3. cd tools/frames && npm install && npm run frames
// Hasil: web/public/frames/sceneN/{d,m}/0001.webp + web/public/frames/manifest.json
//   d = desktop (lebar 1280), m = HP (lebar 640). Web otomatis memakai frame ini setelah build ulang.
// Opsi env: FPS (default 12), QD (kualitas desktop, 62), QM (kualitas HP, 58)

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ffmpeg from "ffmpeg-static";

const here = path.dirname(fileURLToPath(import.meta.url));
const mediaDir = path.resolve(process.env.MEDIA ?? path.join(here, "../../vid"));
const outRoot = path.resolve(here, "../../web/public/frames");
const configFile = path.join(here, "scenes.json");
const config = fs.existsSync(configFile) ? JSON.parse(fs.readFileSync(configFile, "utf8")) : {};
const FPS = Number(process.env.FPS ?? 12);
const VARIANTS = [
  { key: "d", width: 1280, quality: Number(process.env.QD ?? 62) },
  { key: "m", width: 640, quality: Number(process.env.QM ?? 58) },
];

function run(args) {
  const r = spawnSync(ffmpeg, args, { encoding: "utf8" });
  if (r.status !== 0) throw new Error(`ffmpeg gagal:\n${r.stderr.slice(-1500)}`);
  return r.stderr;
}

function probe(file) {
  const r = spawnSync(ffmpeg, ["-hide_banner", "-i", file], { encoding: "utf8" });
  const size = r.stderr.match(/Video:.*?(\d{2,5})x(\d{2,5})/);
  const dur = r.stderr.match(/Duration: (\d+):(\d+):([\d.]+)/);
  if (!size || !dur) throw new Error(`tidak bisa membaca video ${file}`);
  return { w: Number(size[1]), h: Number(size[2]), seconds: Number(dur[1]) * 3600 + Number(dur[2]) * 60 + Number(dur[3]) };
}

const videos = fs.existsSync(mediaDir)
  ? fs
      .readdirSync(mediaDir)
      .filter((f) => /^scene-?\d+\.(mp4|webm|mov)$/i.test(f))
      .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))
  : [];

if (videos.length === 0) {
  console.error(`Tidak ada video. Taruh scene1.mp4, scene2.mp4, ... di ${mediaDir}`);
  process.exit(1);
}

fs.rmSync(outRoot, { recursive: true, force: true });
const manifest = { fps: FPS, generated: new Date().toISOString(), scenes: [] };

for (const file of videos) {
  const id = `scene${file.match(/\d+/)[0]}`;
  const cfg = config[id] ?? {};
  const src = path.join(mediaDir, file);
  const { w, h, seconds } = probe(src);
  const start = Number(cfg.start ?? 0);
  const end = cfg.end == null ? seconds : Math.min(seconds, Number(cfg.end));
  const scene = { id, weight: Number(cfg.weight ?? 1), source: { file, seconds: +seconds.toFixed(2), start, end }, variants: {} };
  for (const v of VARIANTS) {
    const dir = path.join(outRoot, id, v.key);
    fs.mkdirSync(dir, { recursive: true });
    const height = Math.round((h * v.width) / w / 2) * 2;
    run([
      "-hide_banner", "-y", "-ss", String(start), "-to", String(end), "-i", src,
      "-vf", `fps=${FPS},scale=${v.width}:${height}:flags=lanczos`,
      "-an", "-c:v", "libwebp", "-quality", String(v.quality), "-compression_level", "5",
      "-f", "image2", path.join(dir, "%04d.webp"),
    ]);
    const names = fs.readdirSync(dir).filter((f) => f.endsWith(".webp"));
    const bytes = names.reduce((s, f) => s + fs.statSync(path.join(dir, f)).size, 0);
    scene.variants[v.key] = { width: v.width, height, frames: names.length, mb: Math.round(bytes / 1e5) / 10 };
    console.log(`${id}/${v.key}: ${names.length} frame (${start}s sampai ${end.toFixed(2)}s), ${v.width}x${height}, ${scene.variants[v.key].mb} MB`);
  }
  manifest.scenes.push(scene);
}

fs.writeFileSync(path.join(outRoot, "manifest.json"), JSON.stringify(manifest, null, 2));
const total = (k) => manifest.scenes.reduce((s, sc) => s + sc.variants[k].mb, 0).toFixed(1);
console.log(`total desktop ${total("d")} MB, HP ${total("m")} MB`);
console.log(`manifest: ${path.join(outRoot, "manifest.json")}`);
