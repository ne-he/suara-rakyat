import { loadModels, predictOne } from "@/lib/model";
import { clientIp, limited, tooMany } from "@/lib/ratelimit";

export const runtime = "nodejs";

const MAX_TEXTS = 1000;
const MAX_CHARS = 2000;
const MAX_BODY_BYTES = 2_500_000;
const TOP_WORDS = 12;
type Label = "negative" | "neutral" | "positive";

// Cek banyak ulasan sekaligus. Teks tidak disimpan dan tidak dicatat, hanya dihitung lalu dibalas.
export async function POST(request: Request) {
  if (limited("batch", clientIp(request), 10)) return tooMany();

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) return Response.json({ error: "Data terlalu besar. Maksimal 1.000 ulasan per kiriman." }, { status: 413 });

  let body: { texts?: unknown; model?: unknown };
  try {
    const parsed: unknown = JSON.parse(raw);
    body = parsed && typeof parsed === "object" ? (parsed as typeof body) : {};
  } catch {
    return Response.json({ error: 'Format harus JSON: {"texts": ["..."], "model": "svm"}' }, { status: 400 });
  }
  const { meta } = loadModels();
  const model = typeof body.model === "string" ? body.model : meta.default_model;
  if (!meta.models.some((m) => m.id === model)) return Response.json({ error: "Model tidak dikenal." }, { status: 400 });
  if (!Array.isArray(body.texts) || body.texts.length === 0) return Response.json({ error: "Belum ada ulasan yang dikirim." }, { status: 400 });
  if (body.texts.length > MAX_TEXTS) return Response.json({ error: `Maksimal ${MAX_TEXTS} ulasan per kiriman.` }, { status: 400 });
  if (!body.texts.every((t) => typeof t === "string")) return Response.json({ error: "Setiap ulasan harus berupa teks." }, { status: 400 });

  const texts = (body.texts as string[]).map((t) => t.slice(0, MAX_CHARS));
  const t0 = performance.now();
  const counts: Record<Label, number> = { negative: 0, neutral: 0, positive: 0 };
  // kata penentu per label: jumlah dorongan kata ke label hasil, plus berapa ulasan yang memuatnya
  const words: Record<Label, Map<string, { score: number; docs: number }>> = { negative: new Map(), neutral: new Map(), positive: new Map() };
  const items = texts.map((text) => {
    if (!text.trim()) return { label: null, confidence: null };
    const p = predictOne(text, model);
    counts[p.label] += 1;
    const seen = new Set<string>();
    for (const t of p.tokens) {
      if (t.weight <= 0 || t.token.length < 3 || /^\d+$/.test(t.token)) continue;
      const e = words[p.label].get(t.token) ?? { score: 0, docs: 0 };
      e.score += t.weight;
      if (!seen.has(t.token)) {
        e.docs += 1;
        seen.add(t.token);
      }
      words[p.label].set(t.token, e);
    }
    return { label: p.label, confidence: Math.round(p.probs[p.label] * 1000) / 1000 };
  });
  const top = Object.fromEntries(
    (Object.keys(words) as Label[]).map((l) => [
      l,
      [...words[l].entries()]
        .filter(([, e]) => e.docs >= 2 || counts[l] < 20)
        .sort((a, b) => b[1].score - a[1].score)
        .slice(0, TOP_WORDS)
        .map(([token, e]) => ({ token, score: Math.round(e.score * 100) / 100, docs: e.docs })),
    ]),
  );
  return Response.json({ model, n: texts.length, counts, items, top, ms: Math.round(performance.now() - t0) });
}
