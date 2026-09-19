"use client";

import { useMemo, useRef, useState } from "react";
import { parseCsv } from "@/lib/csv";
import { downloadCsv } from "@/lib/download";
import { CLASS_HEX, INK, LABEL_ID, LABELS, nf, pct, type Label } from "@/lib/fmt";
import { useWidth } from "@/lib/useWidth";

type ModelOpt = { id: string; name: string };
type Item = { label: Label | null; confidence: number | null };
type Result = {
  model: string;
  n: number;
  counts: Record<Label, number>;
  items: Item[];
  top: Record<Label, { token: string; score: number; docs: number }[]>;
  ms: number;
};

const MAX_TEXTS = 1000;
const TEXT_HINTS = ["ulasan", "review", "content", "text", "teks", "komentar", "isi"];
const STAR_HINTS = ["bintang", "score", "rating", "star", "nilai"];

function starLabel(v: string): Label | null {
  const s = Number(String(v).replace(",", "."));
  if (!Number.isFinite(s) || s < 1 || s > 5) return null;
  return s <= 2 ? "negative" : s < 4 ? "neutral" : "positive";
}

export default function BatchAnalyzer({ models, defaultId }: { models: ModelOpt[]; defaultId: string }) {
  const [mode, setMode] = useState<"tempel" | "csv">("tempel");
  const [pasted, setPasted] = useState("");
  const [table, setTable] = useState<string[][] | null>(null);
  const [fileName, setFileName] = useState("");
  const [hasHeader, setHasHeader] = useState(true);
  const [textCol, setTextCol] = useState(0);
  const [starCol, setStarCol] = useState(-1);
  const [model, setModel] = useState(defaultId);
  const [result, setResult] = useState<Result | null>(null);
  const [sent, setSent] = useState<{ texts: string[]; stars: (Label | null)[]; rows: string[][]; header: string[] } | null>(null);
  const [filter, setFilter] = useState<Label | "all">("all");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const header = table && hasHeader ? table[0] : table?.[0]?.map((_, i) => `Kolom ${i + 1}`) ?? [];
  const body = table ? (hasHeader ? table.slice(1) : table) : [];

  function loadTable(text: string, name: string) {
    const rows = parseCsv(text);
    if (rows.length === 0) {
      setError("File kosong atau bukan CSV.");
      return;
    }
    const head = rows[0].map((c) => c.trim().toLowerCase());
    const looksHeader = head.some((h) => TEXT_HINTS.includes(h) || STAR_HINTS.includes(h));
    setTable(rows);
    setFileName(name);
    setHasHeader(looksHeader);
    const t = head.findIndex((h) => TEXT_HINTS.includes(h));
    // tanpa petunjuk nama kolom: pilih kolom dengan teks rata-rata terpanjang
    const avgLen = rows[0].map((_, i) => rows.slice(0, 50).reduce((s, r) => s + (r[i]?.length ?? 0), 0));
    setTextCol(t >= 0 ? t : avgLen.indexOf(Math.max(...avgLen)));
    setStarCol(looksHeader ? head.findIndex((h) => STAR_HINTS.includes(h)) : -1);
    setMode("csv");
    setResult(null);
    setError(null);
  }

  async function run() {
    let texts: string[];
    let stars: (Label | null)[] = [];
    let rows: string[][];
    let head: string[];
    if (mode === "tempel") {
      texts = pasted.split(/\r?\n/).map((t) => t.trim()).filter(Boolean);
      rows = texts.map((t) => [t]);
      head = ["ulasan"];
    } else {
      rows = body.filter((r) => (r[textCol] ?? "").trim());
      texts = rows.map((r) => r[textCol].trim());
      stars = starCol >= 0 ? rows.map((r) => starLabel(r[starCol] ?? "")) : [];
      head = header;
    }
    if (texts.length === 0) {
      setError(mode === "tempel" ? "Tempel minimal satu ulasan, satu ulasan per baris." : "Kolom ulasan yang dipilih kosong.");
      return;
    }
    if (texts.length > MAX_TEXTS) {
      setError(`Ada ${nf.format(texts.length)} ulasan. Maksimal ${nf.format(MAX_TEXTS)} per kiriman, jadi hanya ${nf.format(MAX_TEXTS)} pertama yang dibaca.`);
      texts = texts.slice(0, MAX_TEXTS);
      rows = rows.slice(0, MAX_TEXTS);
      stars = stars.slice(0, MAX_TEXTS);
    } else setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/predict-batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texts, model }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Gagal membaca ulasan.");
      setResult(json as Result);
      setSent({ texts, stars, rows, header: head });
      setFilter("all");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal membaca ulasan.");
    } finally {
      setLoading(false);
    }
  }

  const agreement = useMemo(() => {
    if (!result || !sent || sent.stars.length === 0) return null;
    let n = 0;
    let same = 0;
    sent.stars.forEach((s, i) => {
      const p = result.items[i]?.label;
      if (!s || !p) return;
      n += 1;
      if (s === p) same += 1;
    });
    return n ? { n, share: same / n } : null;
  }, [result, sent]);

  const total = result ? LABELS.reduce((s, l) => s + result.counts[l], 0) : 0;
  const shown = result && sent ? sent.texts.map((t, i) => ({ t, i, it: result.items[i] })).filter((x) => filter === "all" || x.it.label === filter) : [];

  return (
    <div className="space-y-8">
      <div className="poster rounded-xl border-2 border-aspal bg-white p-5 sm:p-6">
        <p className="kicker kicker-garis text-abu">1. Masukkan ulasan</p>
        <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Cara memasukkan ulasan">
          {(
            [
              ["tempel", "Tempel teks"],
              ["csv", "Unggah CSV"],
            ] as const
          ).map(([k, l]) => (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={mode === k}
              onClick={() => setMode(k)}
              className={`rounded-full border-2 px-4 py-1.5 text-sm transition ${mode === k ? "border-aspal bg-aspal text-putih" : "border-aspal/25 hover:border-aspal"}`}
            >
              {l}
            </button>
          ))}
          <button
            type="button"
            onClick={async () => {
              const res = await fetch("/contoh/ulasan-contoh.csv");
              loadTable(await res.text(), "ulasan-contoh.csv");
            }}
            className="rounded-full border-2 border-dashed border-merah/60 px-4 py-1.5 text-sm text-merah-tua transition hover:border-merah hover:bg-merah/5"
          >
            Pakai 200 ulasan contoh
          </button>
        </div>

        {mode === "tempel" ? (
          <div className="mt-4">
            <label htmlFor="massal" className="text-sm text-aspal-2">
              Satu ulasan per baris.
            </label>
            <textarea
              id="massal"
              value={pasted}
              onChange={(e) => setPasted(e.target.value)}
              rows={8}
              placeholder={"otp tidak masuk dari kemarin\ntampilan baru lebih rapi, mantap\nlumayan tapi sering logout sendiri"}
              className="mt-2 w-full resize-y rounded-lg border-2 border-aspal/40 bg-putih/60 px-3 py-2 font-mono text-sm outline-none focus:border-aspal focus:bg-white"
            />
            <p className="text-xs text-abu">{nf.format(pasted.split(/\r?\n/).filter((t) => t.trim()).length)} ulasan</p>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.txt,text/csv"
                className="sr-only"
                id="berkas"
                onChange={async (e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  if (f.size > 5_000_000) {
                    setError("File lebih dari 5 MB. Potong dulu jadi maksimal 1.000 ulasan.");
                    return;
                  }
                  loadTable(await f.text(), f.name);
                  e.target.value = "";
                }}
              />
              <label htmlFor="berkas" className="cursor-pointer rounded-sm bg-aspal px-4 py-2 text-sm text-putih shadow-[3px_3px_0_var(--merah)] transition hover:-translate-y-0.5">
                Pilih file CSV
              </label>
              <span className="text-sm text-abu">{fileName ? `${fileName}: ${nf.format(body.length)} baris` : "Belum ada file. File dibaca di browsermu."}</span>
            </div>
            {table && (
              <div className="grid gap-3 sm:grid-cols-3">
                <label className="text-sm">
                  <span className="block text-xs text-abu">Kolom ulasan</span>
                  <select value={textCol} onChange={(e) => setTextCol(Number(e.target.value))} className="mt-1 w-full rounded-md border-2 border-aspal/30 bg-white px-2 py-1.5">
                    {header.map((h, i) => (
                      <option key={i} value={i}>
                        {h || `Kolom ${i + 1}`}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  <span className="block text-xs text-abu">Kolom bintang (opsional)</span>
                  <select value={starCol} onChange={(e) => setStarCol(Number(e.target.value))} className="mt-1 w-full rounded-md border-2 border-aspal/30 bg-white px-2 py-1.5">
                    <option value={-1}>Tidak ada</option>
                    {header.map((h, i) => (
                      <option key={i} value={i}>
                        {h || `Kolom ${i + 1}`}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex items-center gap-2 self-end pb-2 text-sm">
                  <input type="checkbox" checked={hasHeader} onChange={(e) => setHasHeader(e.target.checked)} className="h-4 w-4 accent-[var(--merah)]" />
                  Baris pertama judul kolom
                </label>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="poster rounded-xl border-2 border-aspal bg-white p-5 sm:p-6">
        <p className="kicker kicker-garis text-abu">2. Pilih model lalu baca</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {models.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-pressed={model === m.id}
              onClick={() => setModel(m.id)}
              className={`display rounded-full border-2 px-4 py-1.5 text-lg transition duration-300 hover:-translate-y-0.5 ${
                model === m.id ? "border-aspal bg-merah text-putih shadow-[3px_3px_0_var(--aspal)]" : "border-aspal/30 bg-white hover:border-aspal"
              }`}
            >
              {m.name}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="display mt-5 w-full rounded-sm bg-merah px-5 py-3 text-3xl text-putih shadow-[4px_4px_0_var(--aspal)] transition hover:bg-merah-tua active:translate-x-[2px] active:translate-y-[2px] active:shadow-[2px_2px_0_var(--aspal)] disabled:opacity-60 sm:w-auto sm:px-10"
        >
          {loading ? "Membaca..." : "Baca semua"}
        </button>
        {error && <p className="mt-3 text-sm font-semibold text-neg">{error}</p>}
        <p className="mt-3 text-xs text-abu">
          Maksimal 1.000 ulasan per kiriman, ulasan lebih dari 2.000 karakter dipotong. Teks dikirim ke server untuk dihitung lalu dibuang, tidak disimpan.
          Jangan unggah data pribadi seperti nama lengkap, NIK, atau nomor HP.
        </p>
      </div>

      {result && sent && (
        <div className="rise space-y-6" aria-live="polite">
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            <Stat k="Ulasan dibaca" v={nf.format(total)} s={`${result.ms} ms di server`} />
            {LABELS.map((l) => (
              <Stat key={l} k={LABEL_ID[l]} v={total ? pct(result.counts[l] / total) : "0%"} s={`${nf.format(result.counts[l])} ulasan`} dot={CLASS_HEX[l]} />
            ))}
          </div>

          <div className="poster rounded-xl border-2 border-aspal bg-white p-5 sm:p-6">
            <p className="kicker kicker-garis text-abu">Komposisi nada</p>
            <StackBar counts={result.counts} />
            {agreement && (
              <p className="mt-3 text-sm text-aspal-2">
                Cocok dengan label dari bintang di <b className="text-aspal">{pct(agreement.share)}</b> dari {nf.format(agreement.n)} ulasan yang punya bintang.
              </p>
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {(["negative", "positive"] as Label[]).map((l) => (
              <div key={l} className="poster rounded-xl border-2 border-aspal bg-white p-5">
                <p className="kicker kicker-garis text-abu">Kata paling mendorong ke {LABEL_ID[l].toLowerCase()}</p>
                {result.top[l].length === 0 ? (
                  <p className="mt-3 text-sm text-abu">Belum ada ulasan {LABEL_ID[l].toLowerCase()}.</p>
                ) : (
                  <ol className="mt-4 space-y-2">
                    {result.top[l].map((w, i) => (
                      <li key={w.token} className="group grid grid-cols-[1.5rem_1fr_auto] items-center gap-2 text-sm">
                        <span className="font-mono text-xs text-abu">{i + 1}</span>
                        <span className="relative">
                          <span
                            className="absolute inset-y-0 left-0 rounded-sm opacity-15 transition-opacity duration-300 group-hover:opacity-30"
                            style={{ width: `${((w.score / result.top[l][0].score) * 100).toFixed(1)}%`, background: CLASS_HEX[l] }}
                            aria-hidden
                          />
                          <span className="relative px-1.5 font-semibold">{w.token}</span>
                        </span>
                        <span className="font-mono text-xs text-abu">{nf.format(w.docs)} ulasan</span>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            ))}
          </div>

          <div className="rounded-xl border-2 border-aspal bg-white">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-aspal p-4">
              <div className="flex flex-wrap gap-2">
                {(["all", ...LABELS] as const).map((f) => (
                  <button
                    key={f}
                    type="button"
                    aria-pressed={filter === f}
                    onClick={() => setFilter(f)}
                    className={`rounded-full border px-3 py-1 text-xs transition ${filter === f ? "border-aspal bg-aspal text-putih" : "border-aspal/30 hover:border-aspal"}`}
                  >
                    {f === "all" ? `Semua (${nf.format(total)})` : `${LABEL_ID[f]} (${nf.format(result.counts[f])})`}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => {
                  const extra = ["prediksi", "keyakinan", "model"];
                  const rows = sent.rows.map((r, i) => [...r, result.items[i]?.label ? LABEL_ID[result.items[i].label!] : "", result.items[i]?.confidence ?? "", result.model]);
                  downloadCsv([[...sent.header, ...extra], ...rows], `hasil-suara-rakyat-${result.model}.csv`);
                }}
                className="rounded-sm bg-aspal px-4 py-2 text-sm text-putih shadow-[3px_3px_0_var(--merah)] transition hover:-translate-y-0.5"
              >
                Unduh hasil CSV
              </button>
            </div>
            <div className="max-h-[28rem] overflow-auto">
              <table className="w-full text-left text-sm">
                <thead className="kicker sticky top-0 bg-kertas text-abu">
                  <tr>
                    <th className="px-4 py-2">#</th>
                    <th className="px-4 py-2">Ulasan</th>
                    <th className="px-4 py-2">Hasil</th>
                    <th className="px-4 py-2 text-right">Yakin</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.slice(0, 300).map(({ t, i, it }) => (
                    <tr key={i} className="baris border-b border-garis last:border-0">
                      <td className="px-4 py-2 align-top font-mono text-xs text-abu">{i + 1}</td>
                      <td className="px-4 py-2 align-top">{t.length > 180 ? `${t.slice(0, 180)}...` : t}</td>
                      <td className="whitespace-nowrap px-4 py-2 align-top">
                        {it.label && (
                          <span className="inline-flex items-center gap-1.5">
                            <span className="h-2.5 w-2.5 rounded-full" style={{ background: CLASS_HEX[it.label] }} aria-hidden />
                            {LABEL_ID[it.label]}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-right align-top font-mono text-xs">{it.confidence != null ? pct(it.confidence, 0) : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {shown.length > 300 && <p className="p-4 text-xs text-abu">Menampilkan 300 baris pertama. Semua baris ada di file CSV hasil.</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ k, v, s, dot }: { k: string; v: string; s: string; dot?: string }) {
  return (
    <div className="poster rounded-xl border-2 border-aspal bg-white p-4">
      <p className="kicker kicker-garis flex items-center gap-2 text-abu">
        {dot && <span className="h-2.5 w-2.5 rounded-full" style={{ background: dot }} aria-hidden />}
        {k}
      </p>
      <p className="display mt-3 text-4xl sm:text-5xl">
        <span className="angka">{v}</span>
      </p>
      <p className="mt-1 text-xs text-abu">{s}</p>
    </div>
  );
}

function StackBar({ counts }: { counts: Record<Label, number> }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const total = LABELS.reduce((s, l) => s + counts[l], 0) || 1;
  const H = 36;
  const gapPx = 2;
  const parts = LABELS.filter((l) => counts[l] > 0);
  const usable = width - gapPx * (parts.length - 1);
  const widths = parts.map((l) => (counts[l] / total) * usable);
  const offsets = widths.map((_, i) => widths.slice(0, i).reduce((s, w) => s + w, 0) + gapPx * i);
  return (
    <div ref={ref} className="mt-4">
      <svg viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label="Komposisi negatif, netral, positif">
        {parts.map((l, i) => {
          const x = offsets[i];
          const w = widths[i];
          const r = Math.min(4, w / 2);
          const first = i === 0;
          const lastPart = i === parts.length - 1;
          const d = `M${x + (first ? r : 0)},0H${x + w - (lastPart ? r : 0)}${lastPart ? `Q${x + w},0 ${x + w},${r}V${H - r}Q${x + w},${H} ${x + w - r},${H}` : `V${H}`}H${x + (first ? r : 0)}${first ? `Q${x},${H} ${x},${H - r}V${r}Q${x},0 ${x + r},0` : `V0`}Z`;
          return (
            <g key={l}>
              <path d={d} fill={CLASS_HEX[l]} />
              {w > 54 && (
                <text
                  x={x + w / 2}
                  y={H / 2 + 4}
                  textAnchor="middle"
                  fontSize={12}
                  fontWeight={600}
                  fill={l === "neutral" ? INK.primary : INK.surface}
                  fontFamily="Plus Jakarta Sans, Arial, sans-serif"
                >
                  {pct(counts[l] / total, 0)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm">
        {LABELS.map((l) => (
          <span key={l} className="inline-flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm" style={{ background: CLASS_HEX[l] }} aria-hidden />
            {LABEL_ID[l]} {pct(counts[l] / total)}
          </span>
        ))}
      </div>
    </div>
  );
}
