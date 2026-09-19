import { loadModels, predictAll } from "@/lib/model";
import { clientIp, limited, tooMany } from "@/lib/ratelimit";

export const runtime = "nodejs";

const MAX_CHARS = 2000;
const MAX_BODY_BYTES = 8_000;
const MAX_PER_MINUTE = 60;

export async function POST(request: Request) {
  if (limited("predict", clientIp(request), MAX_PER_MINUTE)) return tooMany();

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
