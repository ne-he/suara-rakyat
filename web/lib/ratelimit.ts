// Pembatas laju sederhana per instance serverless (best effort, bukan pengganti WAF).
// Tiap route punya ember sendiri, jadi cek massal tidak menghabiskan jatah formulir biasa.

const buckets = new Map<string, Map<string, { count: number; start: number }>>();

export function clientIp(request: Request): string {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "anon";
}

export function limited(bucket: string, ip: string, maxPerWindow: number, windowMs = 60_000): boolean {
  const hits = buckets.get(bucket) ?? new Map<string, { count: number; start: number }>();
  buckets.set(bucket, hits);
  const now = Date.now();
  const h = hits.get(ip);
  if (!h || now - h.start > windowMs) {
    hits.set(ip, { count: 1, start: now });
    if (hits.size > 5000) hits.clear();
    return false;
  }
  h.count += 1;
  return h.count > maxPerWindow;
}

export const tooMany = () => Response.json({ error: "Terlalu banyak permintaan, coba lagi sebentar." }, { status: 429 });
