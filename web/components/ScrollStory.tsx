"use client";

// Cerita scroll: canvas menempel di layar, posisi scroll menentukan gambar.
// Mode frame  : kalau public/frames/manifest.json ada (hasil tools/frames), frame video digambar sesuai scroll.
// Mode kode   : kalau belum ada frame, adegan kerumunan + balon suara digambar langsung dengan canvas.
// Semua pembaruan per frame lewat ref (tanpa re-render React) supaya tidak ngelag.

import { useEffect, useRef } from "react";

export type FramesManifest = {
  fps: number;
  scenes: { id: string; variants: Record<"d" | "m", { width: number; height: number; frames: number; mb: number }> }[];
};

export type Chapter = { kicker: string; title: string; body: string; cta?: { label: string; href: string } };

type Props = {
  manifest: FramesManifest | null;
  chapters: Chapter[];
  shares: { negative: number; neutral: number; positive: number };
};

const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (a: number, b: number, x: number) => {
  const t = clamp((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

function mulberry(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function mixHex(a: string, b: string, t: number) {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `rgb(${pa.map((v, i) => Math.round(lerp(v, pb[i], t))).join(",")})`;
}

/* ---------------- mode frame ---------------- */

class FrameStore {
  images: (HTMLImageElement | null)[][];
  loaded = 0;
  total = 0;
  private queue: [number, number][] = [];
  private active = 0;
  private stopped = false;

  constructor(
    private manifest: FramesManifest,
    private variant: "d" | "m",
    private onLoad: () => void,
  ) {
    this.images = manifest.scenes.map((s) => new Array(s.variants[variant].frames).fill(null));
    this.total = this.images.reduce((a, s) => a + s.length, 0);
    // urutan progresif: frame jarang dulu (cerita langsung bisa di-scroll), lalu makin rapat
    const seen = new Set<string>();
    for (const stride of [24, 12, 6, 3, 1]) {
      manifest.scenes.forEach((s, si) => {
        const n = s.variants[variant].frames;
        for (let i = 0; i < n; i += stride) {
          const key = `${si}:${i}`;
          if (!seen.has(key)) {
            seen.add(key);
            this.queue.push([si, i]);
          }
        }
      });
    }
  }

  url(si: number, i: number) {
    return `/frames/${this.manifest.scenes[si].id}/${this.variant}/${String(i + 1).padStart(4, "0")}.webp`;
  }

  start() {
    for (let k = 0; k < 6; k++) this.pump();
  }

  stop() {
    this.stopped = true;
  }

  private pump() {
    if (this.stopped) return;
    const next = this.queue.shift();
    if (!next) return;
    this.active++;
    const [si, i] = next;
    const img = new Image();
    img.decoding = "async";
    img.src = this.url(si, i);
    const done = () => {
      this.active--;
      this.pump();
    };
    img
      .decode()
      .then(() => {
        this.images[si][i] = img;
        this.loaded++;
        this.onLoad();
      })
      .catch(() => undefined)
      .finally(done);
  }

  nearest(si: number, i: number): HTMLImageElement | null {
    const arr = this.images[si];
    if (!arr) return null;
    for (let d = 0; d < arr.length; d++) {
      if (arr[i - d]) return arr[i - d];
      if (arr[i + d]) return arr[i + d];
    }
    return null;
  }
}

/* ---------------- mode kode ---------------- */

type World = {
  w: number;
  h: number;
  buildings: { x: number; w: number; h: number; windows: [number, number][] }[];
  people: { x: number; row: number; r: number; tone: string }[];
  signs: { x: number; row: number; w: number; h: number; style: number; phase: number }[];
  flags: { x: number; pole: number; phase: number; size: number }[];
  bubbles: { cls: number; ox: number; oy: number; sx: number; sy: number; lx: number; bx: number; delay: number; size: number; phase: number }[];
  counts: number[];
};

const ROWS = [0.78, 0.88, 1.0];
const TONES = ["#3b2a22", "#4a3528", "#2e211b", "#57402f", "#241915"];
const CLASS_COLOR = ["#b0151f", "#c98a05", "#1c7a4c"];

function buildWorld(w: number, h: number, shares: number[]): World {
  const rnd = mulberry(20260917);
  const narrow = w < 640;
  const k = Math.min(1, w / 1100);
  const buildings: World["buildings"] = [];
  for (let x = -20; x < w + 40; ) {
    const bw = (34 + rnd() * 70) * Math.max(0.55, k);
    const bh = h * (narrow ? 0.06 + rnd() * 0.14 : 0.08 + rnd() * 0.2);
    const windows: [number, number][] = [];
    for (let k = 0; k < 6; k++) if (rnd() < 0.5) windows.push([rnd(), rnd()]);
    buildings.push({ x, w: bw, h: bh, windows });
    x += bw + rnd() * 6;
  }
  const people: World["people"] = [];
  ROWS.forEach((_, row) => {
    const scale = (0.72 + row * 0.16) * (narrow ? 1.25 : 1);
    for (let x = -10; x < w + 20; x += (22 + rnd() * 16) * scale) {
      people.push({ x, row, r: (8 + rnd() * 2.5) * scale, tone: TONES[Math.floor(rnd() * TONES.length)] });
    }
  });
  const signs: World["signs"] = [];
  const nSigns = Math.max(5, Math.round(w / 110));
  for (let k = 0; k < nSigns; k++) {
    const row = Math.floor(rnd() * 3);
    const scale = (0.72 + row * 0.16) * (narrow ? 1.2 : 1);
    signs.push({ x: rnd() * w, row, w: (54 + rnd() * 50) * scale, h: (36 + rnd() * 22) * scale, style: Math.floor(rnd() * 3), phase: rnd() * 6.28 });
  }
  signs.sort((a, b) => a.row - b.row);
  const flags: World["flags"] = [];
  const nFlags = Math.max(3, Math.round(w / 260));
  for (let k = 0; k < nFlags; k++) flags.push({ x: (k + 0.3 + rnd() * 0.4) * (w / nFlags), pole: h * (0.2 + rnd() * 0.1), phase: rnd() * 6.28, size: 0.8 + rnd() * 0.5 });

  const total = w < 640 ? 90 : 150;
  const counts = shares.map((s) => Math.round(s * total));
  const bubbles: World["bubbles"] = [];
  const rank = [0, 0, 0];
  for (let c = 0; c < 3; c++) {
    for (let k = 0; k < counts[c]; k++) {
      const row = Math.floor(rnd() * 3);
      bubbles.push({
        cls: c,
        ox: rnd() * w,
        oy: h * ROWS[row] - 30,
        sx: w * (0.08 + rnd() * 0.84),
        sy: h * (narrow ? 0.5 + rnd() * 0.22 : 0.1 + rnd() * 0.34),
        lx: 0,
        bx: 0,
        delay: rnd() * 0.12,
        size: 7 + rnd() * 5,
        phase: rnd() * 6.28,
      });
    }
  }
  // posisi jalur (menyebar) dan batang (rapat, panjang sebanding jumlah kelas)
  const laneW = w * 0.84;
  const step = Math.min(18, (w * 0.7) / Math.max(...counts));
  bubbles.forEach((b) => {
    const r = rank[b.cls]++;
    b.lx = w * 0.08 + (laneW * (r + 0.5)) / counts[b.cls];
    b.bx = w * 0.1 + r * step;
  });
  return { w, h, buildings, people, signs, flags, bubbles, counts };
}

function layer(w: number, h: number, dpr: number) {
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.round(w * dpr));
  c.height = Math.max(1, Math.round(h * dpr));
  const x = c.getContext("2d")!;
  x.setTransform(dpr, 0, 0, dpr, 0, 0);
  return [c, x] as const;
}

/**
 * Penggambar adegan kode dengan cache: langit (resolusi 1/4), gedung siang/malam, dan tiap baris
 * kerumunan dirender sekali. Per frame cuma menempel lapisan lalu menggambar papan, bendera, balon.
 */
class WorldRenderer {
  private sky: HTMLCanvasElement;
  private skyCtx: CanvasRenderingContext2D;
  private skyKey = -1;
  private cityDay: HTMLCanvasElement;
  private cityNight: HTMLCanvasElement;
  private rows: HTMLCanvasElement[] = [];
  private rowTop: number[] = [];
  private cityTop: number;
  private palette: string[][];

  constructor(
    private W: World,
    dpr: number,
  ) {
    const { w, h } = W;
    [this.sky, this.skyCtx] = layer(Math.ceil(w / 4), Math.ceil(h / 4), 1);
    this.cityTop = h * 0.66 - Math.max(...W.buildings.map((b) => b.h)) - 4;
    const cityH = h - this.cityTop;
    const drawCity = (color: string, lights: number) => {
      const [c, x] = layer(w, cityH, dpr);
      x.fillStyle = color;
      for (const b of W.buildings) x.fillRect(b.x, h * 0.66 - b.h - this.cityTop, b.w, cityH);
      x.fillStyle = `rgba(255,220,150,${lights})`;
      for (const b of W.buildings)
        for (const [u, v] of b.windows) x.fillRect(b.x + 6 + u * (b.w - 16), h * 0.66 - b.h - this.cityTop + 10 + v * (b.h - 24), 4, 5);
      return c;
    };
    this.cityDay = drawCity("#8a5a4a", 0.15);
    this.cityNight = drawCity("#1e1626", 0.7);
    ROWS.forEach((ry, row) => {
      const top = h * ry - 90;
      const layerH = h - top + 60;
      const [c, x] = layer(w, layerH, dpr);
      const shade = row === 0 ? 0.25 : row === 1 ? 0.12 : 0;
      for (const person of W.people) {
        if (person.row !== row) continue;
        x.fillStyle = shade ? mixHex(person.tone, "#1a1020", shade) : person.tone;
        const r = person.r;
        const y = h * ry - top;
        x.beginPath();
        x.arc(person.x, y - r * 3.1, r, 0, Math.PI * 2);
        x.moveTo(person.x - r * 2, layerH);
        x.lineTo(person.x - r * 1.9, y - r * 1.2);
        x.quadraticCurveTo(person.x, y - r * 2.4, person.x + r * 1.9, y - r * 1.2);
        x.lineTo(person.x + r * 2, layerH);
        x.fill();
      }
      this.rows.push(c);
      this.rowTop.push(top);
    });
    // 3 kelas x 33 langkah warna (putih ke warna kelas)
    this.palette = CLASS_COLOR.map((c) => Array.from({ length: 33 }, (_, i) => mixHex("#fffaf0", c, i / 32)));
  }

  draw(ctx: CanvasRenderingContext2D, p: number, time: number, monoFont: string) {
    const { W } = this;
    const { w, h } = W;
    const dusk = smooth(0.2, 0.95, p);

    const key = Math.round(dusk * 64);
    if (key !== this.skyKey) {
      this.skyKey = key;
      const d = key / 64;
      const sw = this.sky.width;
      const sh = this.sky.height;
      const s = this.skyCtx;
      const sky = s.createLinearGradient(0, 0, 0, sh);
      sky.addColorStop(0, mixHex("#f2b35b", "#2b1d3a", d));
      sky.addColorStop(0.55, mixHex("#f6d59a", "#a8433f", d));
      sky.addColorStop(1, mixHex("#f9e7c4", "#e0703f", d));
      s.fillStyle = sky;
      s.fillRect(0, 0, sw, sh);
      const sunY = sh * lerp(0.3, 0.62, d);
      const glow = s.createRadialGradient(sw * 0.7, sunY, 0, sw * 0.7, sunY, sh * 0.42);
      glow.addColorStop(0, "rgba(255,244,214,0.95)");
      glow.addColorStop(0.18, "rgba(255,214,150,0.55)");
      glow.addColorStop(1, "rgba(255,200,140,0)");
      s.fillStyle = glow;
      s.fillRect(0, 0, sw, sh);
    }
    ctx.drawImage(this.sky, 0, 0, w, h);

    const lift = p * h * 0.1;
    const cityY = this.cityTop + lift * 0.5;
    const cityH = h - this.cityTop;
    if (dusk < 0.999) ctx.drawImage(this.cityDay, 0, cityY, w, cityH);
    if (dusk > 0.001) {
      ctx.globalAlpha = dusk;
      ctx.drawImage(this.cityNight, 0, cityY, w, cityH);
      ctx.globalAlpha = 1;
    }

    // bendera merah putih berkibar
    const seg = 8;
    for (const f of W.flags) {
      const px = f.x;
      const top = h * 0.78 + lift - f.pole;
      ctx.fillStyle = "#1a1512";
      ctx.fillRect(px - 1, top, 2, f.pole + 4);
      const fw = 58 * f.size;
      const fh = 38 * f.size;
      for (const [color, y0, y1] of [
        ["#ce1126", 0, 0.5],
        ["#fbfaf5", 0.5, 1],
      ] as const) {
        ctx.fillStyle = color;
        ctx.beginPath();
        for (let i = 0; i <= seg; i++) ctx.lineTo(px + (fw * i) / seg, top + fh * y0 + Math.sin(time * 3 + f.phase + i * 0.7) * 3.2 * (i / seg));
        for (let i = seg; i >= 0; i--) ctx.lineTo(px + (fw * i) / seg, top + fh * y1 + Math.sin(time * 3 + f.phase + i * 0.7) * 3.2 * (i / seg));
        ctx.fill();
      }
    }

    // papan karton lalu kerumunan, baris belakang dulu
    for (let row = 0; row < 3; row++) {
      const shift = lift * (0.6 + row * 0.2);
      const y = h * ROWS[row] + shift;
      const scale = (0.72 + row * 0.16) * (w < 640 ? 1.2 : 1);
      for (const s of W.signs) {
        if (s.row !== row) continue;
        const sy = y - s.h - 46 * scale + Math.sin(time * 1.6 + s.phase) * 3;
        ctx.fillStyle = "#1a1512";
        ctx.fillRect(s.x + s.w / 2 - 1.5, sy + s.h, 3, 50);
        ctx.fillRect(s.x - 2, sy - 2, s.w + 4, s.h + 4);
        ctx.fillStyle = s.style === 1 ? "#fbfaf5" : "#d4ae72";
        ctx.fillRect(s.x, sy, s.w, s.h);
        ctx.fillStyle = s.style === 2 ? "#ce1126" : "#1a1512";
        ctx.fillRect(s.x + s.w * 0.14, sy + s.h * 0.3, s.w * 0.72, s.h * 0.12);
        ctx.fillRect(s.x + s.w * 0.14, sy + s.h * 0.56, s.w * 0.5, s.h * 0.12);
      }
      const img = this.rows[row];
      ctx.drawImage(img, 0, this.rowTop[row] + shift, w, (img.height * w) / img.width);
    }

    // balon suara: dikelompokkan per (kelas, tingkat transparansi) supaya sedikit panggilan fill
    const sort = smooth(0.52, 0.76, p);
    const bar = smooth(0.8, 0.96, p);
    const laneY = w < 640 ? [h * 0.63, h * 0.7, h * 0.77] : [h * 0.12, h * 0.21, h * 0.3];
    const colorIdx = Math.round(sort * 32);
    for (let cls = 0; cls < 3; cls++) {
      for (let level = 1; level <= 8; level++) {
        let any = false;
        for (const b of W.bubbles) {
          if (b.cls !== cls) continue;
          const up = smooth(0.14 + b.delay, 0.42 + b.delay, p);
          if (up <= 0.001 || Math.ceil(Math.min(1, up * 1.4) * 8) !== level) continue;
          if (!any) {
            ctx.beginPath();
            any = true;
          }
          const wob = Math.sin(time * 2 + b.phase) * 6 * (1 - sort);
          const x = lerp(lerp(lerp(b.ox, b.sx, up) + wob, b.lx, sort), b.bx, bar);
          const yy = lerp(lerp(b.oy + lift, b.sy, up), laneY[cls], sort);
          const size = b.size * (1 - bar * 0.25);
          ctx.roundRect(x - size, yy - size * 0.72, size * 2, size * 1.44, size * 0.5);
          ctx.moveTo(x - size * 0.3, yy + size * 0.7);
          ctx.lineTo(x - size * 0.75, yy + size * 1.25);
          ctx.lineTo(x + size * 0.15, yy + size * 0.7);
        }
        if (any) {
          ctx.globalAlpha = level / 8;
          ctx.fillStyle = this.palette[cls][colorIdx];
          ctx.fill();
        }
      }
    }
    ctx.globalAlpha = 1;

    if (bar > 0.05) {
      const names = ["NEGATIF", "NETRAL", "POSITIF"];
      const total = W.counts.reduce((a, c) => a + c, 0);
      ctx.globalAlpha = bar;
      ctx.fillStyle = "#fffaf0";
      ctx.font = `600 ${w < 640 ? 10 : 12}px ${monoFont}`;
      ctx.textBaseline = "middle";
      names.forEach((n, c) => ctx.fillText(`${n} ${((W.counts[c] / total) * 100).toFixed(0)}%`, w * 0.1, laneY[c] - 20));
      ctx.globalAlpha = 1;
    }
  }
}

/* ---------------- komponen ---------------- */

export default function ScrollStory({ manifest, chapters, shares }: Props) {
  const sectionRef = useRef<HTMLElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRefs = useRef<(HTMLDivElement | null)[]>([]);
  const railRef = useRef<HTMLDivElement>(null);
  const counterRef = useRef<HTMLSpanElement>(null);
  const loadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const canvas = canvasRef.current;
    if (!section || !canvas) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const monoFont = getComputedStyle(document.documentElement).getPropertyValue("--font-jetbrains") || "monospace";
    const N = chapters.length;
    let target = 0;
    let current = 0;
    let last = performance.now();
    let raf = 0;
    let visible = true;
    let dirty = true;
    let lastKey = "";
    let renderer: WorldRenderer | null = null;
    let cssW = 0;
    let cssH = 0;

    const variant: "d" | "m" = window.innerWidth < 820 ? "m" : "d";
    const store = manifest && manifest.scenes.length ? new FrameStore(manifest, variant, () => {
      dirty = true;
      kick();
    }) : null;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      cssW = canvas!.clientWidth;
      cssH = canvas!.clientHeight;
      canvas!.width = Math.round(cssW * dpr);
      canvas!.height = Math.round(cssH * dpr);
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (!store) renderer = new WorldRenderer(buildWorld(cssW, cssH, [shares.negative, shares.neutral, shares.positive]), dpr);
      dirty = true;
      lastKey = "";
      kick();
    }

    function measure() {
      const r = section!.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      target = total > 0 ? clamp(-r.top / total) : 0;
    }

    function drawCover(img: HTMLImageElement, alpha: number) {
      const iw = img.naturalWidth;
      const ih = img.naturalHeight;
      const s = Math.max(cssW / iw, cssH / ih);
      const dw = iw * s;
      const dh = ih * s;
      ctx!.globalAlpha = alpha;
      ctx!.drawImage(img, (cssW - dw) / 2, (cssH - dh) / 2, dw, dh);
      ctx!.globalAlpha = 1;
    }

    function drawFrames(p: number) {
      const scenes = manifest!.scenes;
      const S = scenes.length;
      const g = clamp(p) * S;
      const s = clamp(Math.floor(g), 0, S - 1);
      const t = p >= 1 ? 1 : clamp(g - s);
      const count = scenes[s].variants[variant].frames;
      const fi = Math.round(t * (count - 1));
      const fade = 0.12;
      const a = s < S - 1 && t > 1 - fade ? Math.round(((t - (1 - fade)) / fade) * 20) / 20 : 0;
      const key = `${s}:${fi}:${a}`;
      if (key === lastKey && !dirty) return;
      const img = store!.nearest(s, fi);
      if (!img) return;
      drawCover(img, 1);
      if (a > 0) {
        const nxt = store!.nearest(s + 1, 0);
        if (nxt) drawCover(nxt, a);
      }
      lastKey = key;
      dirty = false;
    }

    function updateOverlays(p: number) {
      const g = p * N;
      overlayRefs.current.forEach((el, i) => {
        if (!el) return;
        const u = g - i;
        let o = smooth(-0.05, 0.16, u) * (1 - smooth(0.8, 1.0, u));
        if (i === 0 && u < 0.5) o = 1 - smooth(0.8, 1.0, u);
        if (i === N - 1 && u > 0.5) o = smooth(-0.05, 0.16, u);
        el.style.opacity = o.toFixed(3);
        el.style.transform = `translate3d(0, ${((1 - o) * 24).toFixed(1)}px, 0)`;
        el.style.visibility = o < 0.01 ? "hidden" : "visible";
      });
      if (railRef.current) railRef.current.style.transform = `scaleY(${p.toFixed(4)})`;
      if (counterRef.current) counterRef.current.textContent = `${String(Math.min(N, Math.floor(g) + 1)).padStart(2, "0")} / ${String(N).padStart(2, "0")}`;
      if (loadRef.current && store) {
        const pct = Math.round((store.loaded / store.total) * 100);
        loadRef.current.textContent = pct < 100 ? `memuat adegan ${pct}%` : "";
      }
    }

    function frame(now: number) {
      raf = 0;
      // timestamp rAF bisa sedikit lebih awal dari performance.now() saat kick, jadi dijepit ke >= 0
      const dt = clamp((now - last) / 1000, 0, 0.1);
      last = Math.max(last, now);
      const k = reduce ? 1 : 1 - Math.exp(-dt * 10);
      current = clamp(current + (target - current) * k);
      if (Math.abs(target - current) < 0.0004) current = target;
      if (store) drawFrames(current);
      else if (renderer) renderer.draw(ctx!, current, reduce ? 0 : now / 1000, monoFont);
      updateOverlays(current);
      const animating = current !== target || (!store && !reduce) || dirty;
      if (visible && animating) raf = requestAnimationFrame(frame);
    }

    function kick() {
      if (!raf && visible) {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      }
    }

    const onScroll = () => {
      measure();
      kick();
    };
    const io = new IntersectionObserver((entries) => {
      visible = entries[0]?.isIntersecting ?? true;
      if (visible) kick();
    });
    io.observe(section);
    const ro = new ResizeObserver(() => {
      measure();
      resize();
    });
    ro.observe(canvas);
    window.addEventListener("scroll", onScroll, { passive: true });
    measure();
    current = target;
    resize();
    store?.start();

    return () => {
      window.removeEventListener("scroll", onScroll);
      io.disconnect();
      ro.disconnect();
      store?.stop();
      if (raf) cancelAnimationFrame(raf);
    };
  }, [manifest, chapters.length, shares.negative, shares.neutral, shares.positive]);

  return (
    <section ref={sectionRef} className="relative" style={{ height: `${chapters.length * 100 + 40}vh` }} aria-label="Cerita suara rakyat">
      <div className="sticky top-0 h-[100svh] w-full overflow-hidden bg-aspal">
        <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,rgba(20,18,16,0.82)_0%,rgba(20,18,16,0.45)_34%,rgba(20,18,16,0)_58%)] sm:bg-[linear-gradient(to_right,rgba(20,18,16,0.82)_0%,rgba(20,18,16,0.45)_42%,rgba(20,18,16,0)_68%)]" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 hidden h-1/3 bg-[linear-gradient(to_top,rgba(20,18,16,0.55),rgba(20,18,16,0))] sm:block" />

        {chapters.map((c, i) => (
          <div
            key={c.title}
            ref={(el) => {
              overlayRefs.current[i] = el;
            }}
            className="absolute inset-x-0 top-0 px-5 pt-[15svh] will-change-[opacity,transform] sm:bottom-0 sm:top-auto sm:px-10 sm:pb-[12svh] sm:pt-0"
            style={{ opacity: i === 0 ? 1 : 0, visibility: i === 0 ? "visible" : "hidden" }}
          >
            <div className="mx-auto max-w-6xl">
              <p className="kicker text-putih/80">{c.kicker}</p>
              <h2 className="display mt-3 max-w-4xl text-[13vw] text-putih sm:text-[11vw] lg:text-[128px]">
                {c.title}
              </h2>
              <p className="mt-4 max-w-xl text-lg leading-relaxed text-putih/90 sm:text-xl">{c.body}</p>
              {c.cta && (
                <a
                  href={c.cta.href}
                  className="mt-6 inline-flex items-center gap-2 rounded-full bg-merah px-6 py-3 font-semibold text-putih shadow-[4px_4px_0_#141210] transition hover:bg-merah-tua"
                >
                  {c.cta.label}
                </a>
              )}
            </div>
          </div>
        ))}

        <div className="pointer-events-none absolute right-4 top-1/2 flex -translate-y-1/2 flex-col items-center gap-3 sm:right-8">
          <span ref={counterRef} className="kicker text-putih/80 [writing-mode:vertical-rl]">
            01 / {String(chapters.length).padStart(2, "0")}
          </span>
          <div className="h-32 w-[3px] overflow-hidden rounded-full bg-putih/25">
            <div ref={railRef} className="h-full w-full origin-top bg-merah" style={{ transform: "scaleY(0)" }} />
          </div>
        </div>
        <div ref={loadRef} className="kicker pointer-events-none absolute left-5 top-20 text-putih/70 sm:left-10" />
      </div>
    </section>
  );
}
