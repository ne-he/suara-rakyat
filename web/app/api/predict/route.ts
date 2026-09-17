import { loadModels, predictAll } from "@/lib/model";

export const runtime = "nodejs";

const MAX_CHARS = 2000;
const MAX_BODY_BYTES = 8_000;
const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 60;

// Pembatas laju sederhana per instance serverless (best effort, bukan pengganti WAF).
const hits = new Map<string, { count: number; start: number }>();

function limited(ip: string): boolean {
  const now = Date.now();
  const h = hits.get(ip);
  if (!h || now - h.start > WINDOW_MS) {
    hits.set(ip, { count: 1, start: now });
    if (hits.size > 5000) hits.clear();
    return false;
  }
  h.count += 1;
  return h.count > MAX_PER_WINDOW;
}

export async function POST(request: Request) {
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "anon";
  if (limited(ip)) {
    return Response.json({ error: "Terlalu banyak permintaan, coba lagi sebentar." }, { status: 429 });
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) {
    return Response.json({ error: "Permintaan terlalu besar." }, { status: 413 });
  }

  let text: unknown;
  try {
    const body: unknown = JSON.parse(raw);
    text = body && typeof body === "object" ? (body as { text?: unknown }).text : undefined;
  } catch {
    return Response.json({ error: "Format harus JSON: {\"text\": \"...\"}" }, { status: 400 });
  }
  if (typeof text !== "string" || text.trim().length === 0) {
    return Response.json({ error: "Tulis ulasannya dulu." }, { status: 400 });
  }
  if (text.length > MAX_CHARS) {
    return Response.json({ error: `Ulasan maksimal ${MAX_CHARS} karakter.` }, { status: 400 });
  }

  const { meta } = loadModels(); // muat bobot sekali per instance, tidak ikut dihitung waktu prediksi
  const t0 = performance.now();
  const results = predictAll(text);
  const ms = performance.now() - t0;
  return Response.json({ default: meta.default_model, results, ms: Math.round(ms * 100) / 100 });
}
