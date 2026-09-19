import { clientIp, limited, tooMany } from "@/lib/ratelimit";

export const runtime = "nodejs";
// server gratis bisa sedang tidur, bangunnya bisa sampai sekitar satu menit
export const maxDuration = 60;

const MAX_CHARS = 2000;
const LABELS = ["negative", "neutral", "positive"];

// Jembatan ke server IndoBERTweet (folder indobert-api). Alamat dan kuncinya hanya ada di server
// (INDOBERT_URL, INDOBERT_KEY), jadi browser tidak pernah tahu dan tidak bisa memanggilnya langsung.
export async function POST(request: Request) {
  const base = process.env.INDOBERT_URL;
  if (!base) return Response.json({ error: "IndoBERT belum dipasang di server ini.", code: "off" }, { status: 503 });
  if (limited("indobert", clientIp(request), 20)) return tooMany();

  const raw = await request.text();
  if (raw.length > 8_000) return Response.json({ error: "Permintaan terlalu besar." }, { status: 413 });
  let text: unknown;
  try {
    const body: unknown = JSON.parse(raw);
    text = body && typeof body === "object" ? (body as { text?: unknown }).text : undefined;
  } catch {
    return Response.json({ error: 'Format harus JSON: {"text": "..."}' }, { status: 400 });
  }
  if (typeof text !== "string" || !text.trim()) return Response.json({ error: "Tulis ulasannya dulu." }, { status: 400 });
  if (text.length > MAX_CHARS) return Response.json({ error: `Ulasan maksimal ${MAX_CHARS} karakter.` }, { status: 400 });

  const t0 = Date.now();
  try {
    const res = await fetch(`${base.replace(/\/$/, "")}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(process.env.INDOBERT_KEY ? { "x-suara-key": process.env.INDOBERT_KEY } : {}) },
      body: JSON.stringify({ text }),
      signal: AbortSignal.timeout(55_000),
      cache: "no-store",
    });
    if (!res.ok) return Response.json({ error: `Server IndoBERT membalas ${res.status}.`, code: "upstream" }, { status: 502 });
    const data = (await res.json()) as { label?: string; probs?: Record<string, number>; tokens?: unknown };
    if (!data.label || !LABELS.includes(data.label) || !data.probs || !Array.isArray(data.tokens)) {
      return Response.json({ error: "Balasan server IndoBERT tidak dikenali.", code: "upstream" }, { status: 502 });
    }
    return Response.json({ ...data, wait_ms: Date.now() - t0 });
  } catch (e) {
    const timeout = e instanceof Error && e.name === "TimeoutError";
    return Response.json(
      { error: timeout ? "Server IndoBERT terlalu lama membalas, mungkin sedang bangun. Coba lagi sebentar." : "Server IndoBERT tidak bisa dihubungi.", code: timeout ? "timeout" : "down" },
      { status: 504 },
    );
  }
}
