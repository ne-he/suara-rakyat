"use client";

import { useMemo, useRef, useState } from "react";
import { ChartFooter, TABLE_CLASS } from "@/components/ChartTools";
import { parseCsv } from "@/lib/csv";
import { downloadCsv } from "@/lib/download";
import { EMPHASIS, INK, nf } from "@/lib/fmt";
import { useWidth } from "@/lib/useWidth";

// System Usability Scale (Brooke, 1996), diterjemahkan tim. Butir ganjil pernyataan positif, genap negatif.
const ITEMS = [
  "Saya rasa saya akan sering memakai web ini.",
  "Menurut saya web ini rumit tanpa alasan yang jelas.",
  "Menurut saya web ini mudah dipakai.",
  "Saya rasa saya butuh bantuan orang yang paham teknis untuk bisa memakai web ini.",
  "Menurut saya fitur-fitur di web ini terhubung dengan baik.",
  "Menurut saya ada terlalu banyak hal yang tidak konsisten di web ini.",
  "Saya bayangkan kebanyakan orang bisa cepat belajar memakai web ini.",
  "Menurut saya web ini merepotkan untuk dipakai.",
  "Saya merasa percaya diri saat memakai web ini.",
  "Saya perlu belajar banyak hal dulu sebelum bisa memakai web ini.",
];
const SHORT = ["Ingin sering pakai", "Tidak rumit", "Mudah dipakai", "Tanpa bantuan teknis", "Fitur terhubung", "Konsisten", "Cepat dipelajari", "Tidak merepotkan", "Percaya diri", "Tanpa banyak belajar"];
const SCALE = ["Sangat tidak setuju", "Tidak setuju", "Netral", "Setuju", "Sangat setuju"];
const TASKS = [
  "Tulis satu ulasan di halaman depan lalu tekan Suarakan.",
  "Ganti model pembaca dan bandingkan hasilnya.",
  "Buka Dashboard dan temukan model dengan skor tertinggi.",
  "Di halaman Massal, baca 200 ulasan contoh lalu unduh hasilnya.",
];
const BENCHMARK = 68; // rata-rata skor SUS yang umum dipakai sebagai patokan

const itemScore = (i: number, v: number) => (i % 2 === 0 ? v - 1 : 5 - v);
const susScore = (answers: number[]) => answers.reduce((s, v, i) => s + itemScore(i, v), 0) * 2.5;

export default function SusForm() {
  const [tab, setTab] = useState<"isi" | "rekap">("isi");
  return (
    <div>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Mode kuesioner">
        {(
          [
            ["isi", "Isi kuesioner"],
            ["rekap", "Rekap tim"],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            type="button"
            role="tab"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={`display rounded-full border-2 px-5 py-2 text-xl transition duration-300 hover:-translate-y-0.5 ${
              tab === k ? "border-aspal bg-merah text-putih shadow-[3px_3px_0_var(--aspal)]" : "border-aspal/30 bg-white hover:border-aspal"
            }`}
          >
            {l}
          </button>
        ))}
      </div>
      <div className="mt-6">{tab === "isi" ? <Isi /> : <Rekap />}</div>
    </div>
  );
}

function Isi() {
  const [answers, setAnswers] = useState<(number | null)[]>(Array(10).fill(null));
  const [done, setDone] = useState(false);
  const [copied, setCopied] = useState(false);
  const filled = answers.filter((a) => a !== null).length;
  const score = done ? susScore(answers as number[]) : null;

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (filled === 10) setDone(true);
        }}
      >
        {ITEMS.map((q, i) => (
          <fieldset key={i} className="poster rounded-xl border-2 border-aspal bg-white p-4">
            <legend className="sr-only">Pernyataan {i + 1}</legend>
            <p className="font-medium">
              <span className="mr-2 font-mono text-sm text-merah">{String(i + 1).padStart(2, "0")}</span>
              {q}
            </p>
            <div className="mt-3 grid grid-cols-5 gap-1.5">
              {SCALE.map((s, k) => {
                const v = k + 1;
                const on = answers[i] === v;
                return (
                  <label
                    key={v}
                    className={`flex cursor-pointer flex-col items-center gap-1 rounded-lg border-2 px-1 py-2 text-center transition ${
                      on ? "border-aspal bg-aspal text-putih" : "border-aspal/15 hover:border-aspal/60"
                    }`}
                  >
                    <input
                      type="radio"
                      name={`q${i}`}
                      value={v}
                      checked={on}
                      disabled={done}
                      onChange={() => setAnswers((a) => a.map((x, j) => (j === i ? v : x)))}
                      className="sr-only"
                    />
                    <span className="display text-2xl">{v}</span>
                    <span className="hidden text-[10px] leading-tight sm:block">{s}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        ))}
        <p className="text-xs text-abu sm:hidden">1 = sangat tidak setuju, 5 = sangat setuju.</p>
        {!done && (
          <button
            type="submit"
            disabled={filled < 10}
            className="display w-full rounded-sm bg-merah px-5 py-3 text-3xl text-putih shadow-[4px_4px_0_var(--aspal)] transition hover:bg-merah-tua disabled:opacity-50"
          >
            {filled < 10 ? `Terisi ${filled} dari 10` : "Hitung skor"}
          </button>
        )}
      </form>

      <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start">
        <div className="karton rounded-sm p-5">
          <p className="marker text-xl text-merah-tua">Sebelum mengisi</p>
          <p className="mt-2 text-sm">Coba dulu tugas ini di web:</p>
          <ol className="mt-2 list-decimal space-y-1.5 pl-5 text-sm">
            {TASKS.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ol>
        </div>
        {done && score !== null && (
          <div className="rise rounded-xl border-2 border-aspal bg-white p-5 shadow-[6px_6px_0_var(--aspal)]" aria-live="polite">
            <p className="kicker text-abu">Skor SUS kamu</p>
            <p className="display mt-2 text-7xl">{nf.format(score)}</p>
            <p className="mt-2 text-sm text-aspal-2">
              {score >= BENCHMARK ? "Di atas" : "Di bawah"} patokan rata-rata umum {BENCHMARK}. Skala 0 sampai 100.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={async () => {
                  await navigator.clipboard.writeText((answers as number[]).join("\t"));
                  setCopied(true);
                }}
                className="rounded-sm bg-aspal px-3 py-2 text-sm text-putih transition hover:-translate-y-0.5"
              >
                {copied ? "Tersalin" : "Salin jawaban"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setAnswers(Array(10).fill(null));
                  setDone(false);
                  setCopied(false);
                }}
                className="rounded-sm border-2 border-aspal px-3 py-2 text-sm transition hover:-translate-y-0.5"
              >
                Isi ulang
              </button>
            </div>
            <p className="mt-3 text-xs text-abu">
              Jawaban tidak disimpan di server. Tempel hasil salinan ke spreadsheet tim (satu baris per orang), lalu rekap di tab Rekap tim.
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}

function Rekap() {
  const [raw, setRaw] = useState("");
  const parsed = useMemo(() => {
    const rows = raw.trim() ? parseCsv(raw) : [];
    const ok: number[][] = [];
    let skipped = 0;
    for (const r of rows) {
      const nums = r.map((c) => c.trim()).filter((c) => /^[1-5]$/.test(c)).map(Number);
      if (nums.length >= 10) ok.push(nums.slice(0, 10));
      else skipped += 1;
    }
    return { ok, skipped };
  }, [raw]);

  const scores = parsed.ok.map(susScore);
  const n = scores.length;
  const mean = n ? scores.reduce((a, b) => a + b, 0) / n : 0;
  const sd = n > 1 ? Math.sqrt(scores.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1)) : 0;
  const sorted = [...scores].sort((a, b) => a - b);
  const median = n ? (n % 2 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2) : 0;
  const itemMeans = Array.from({ length: 10 }, (_, i) => (n ? parsed.ok.reduce((s, r) => s + itemScore(i, r[i]), 0) / n : 0));
  const f1 = (x: number) => x.toFixed(1).replace(".", ",");

  return (
    <div className="space-y-6">
      <div className="poster rounded-xl border-2 border-aspal bg-white p-5">
        <label htmlFor="rekap" className="kicker kicker-garis text-abu">
          Tempel jawaban
        </label>
        <p className="mt-3 text-sm text-aspal-2">
          Satu baris per responden berisi 10 angka 1 sampai 5 sesuai urutan pernyataan. Bisa langsung disalin dari Google Sheets atau hasil ekspor Google
          Form. Kolom lain seperti waktu isi akan dilewati.
        </p>
        <textarea
          id="rekap"
          rows={7}
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          placeholder={"4\t2\t5\t1\t4\t2\t5\t1\t4\t2\n5\t1\t4\t2\t4\t1\t5\t2\t5\t1"}
          className="mt-3 w-full rounded-lg border-2 border-aspal/40 bg-putih/60 px-3 py-2 font-mono text-sm outline-none focus:border-aspal focus:bg-white"
        />
        <p className="text-xs text-abu">
          {nf.format(n)} responden terbaca{parsed.skipped ? `, ${nf.format(parsed.skipped)} baris dilewati (misalnya baris judul)` : ""}.
        </p>
      </div>

      {n > 0 && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            {[
              { k: "Rata-rata SUS", v: f1(mean), s: `patokan umum ${BENCHMARK}` },
              { k: "Median", v: f1(median), s: `min ${f1(sorted[0])} · maks ${f1(sorted[n - 1])}` },
              { k: "Simpangan baku", v: n > 1 ? f1(sd) : "-", s: n > 1 ? `95%: ${f1(mean - (1.96 * sd) / Math.sqrt(n))} sampai ${f1(mean + (1.96 * sd) / Math.sqrt(n))}` : "butuh 2 responden" },
              { k: `Di atas ${BENCHMARK}`, v: `${Math.round((scores.filter((s) => s >= BENCHMARK).length / n) * 100)}%`, s: `${nf.format(n)} responden` },
            ].map((c) => (
              <div key={c.k} className="poster rounded-xl border-2 border-aspal bg-white p-4">
                <p className="kicker kicker-garis text-abu">{c.k}</p>
                <p className="display mt-3 text-4xl sm:text-5xl">
                  <span className="angka">{c.v}</span>
                </p>
                <p className="mt-1 text-xs text-abu">{c.s}</p>
              </div>
            ))}
          </div>
          <div className="rounded-xl border-2 border-aspal bg-white p-5">
            <p className="kicker text-abu">Skor per butir</p>
            <ItemBars means={itemMeans} n={n} />
          </div>
          <button
            type="button"
            onClick={() =>
              downloadCsv(
                [["responden", ...ITEMS.map((_, i) => `B${i + 1}`), "skor_sus"], ...parsed.ok.map((r, i) => [i + 1, ...r, susScore(r)])],
                "rekap-sus.csv",
              )
            }
            className="rounded-sm bg-aspal px-4 py-2 text-sm text-putih shadow-[3px_3px_0_var(--merah)] transition hover:-translate-y-0.5"
          >
            Unduh rekap CSV
          </button>
        </>
      )}
    </div>
  );
}

function ItemBars({ means, n }: { means: number[]; n: number }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const labelW = Math.min(170, width * 0.42);
  const rowH = 30;
  const top = 24;
  const H = top + rowH * 10 + 26;
  const plotW = width - labelW - 44;
  const x = (v: number) => labelW + (v / 4) * plotW;
  const FONT = "Plus Jakarta Sans, Arial, sans-serif";
  return (
    <div ref={ref} className="mt-3">
      <svg ref={svgRef} viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label="Rata-rata skor tiap butir SUS">
        <rect width={width} height={H} fill={INK.surface} />
        <text x={0} y={14} fontFamily={FONT} fontSize={12} fill={INK.muted}>
          Rata-rata skor butir, 0 sampai 4, makin tinggi makin baik ({n} responden)
        </text>
        {[0, 1, 2, 3, 4].map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={top} y2={top + rowH * 10} stroke={INK.grid} strokeWidth={1} />
            <text x={x(v)} y={H - 8} textAnchor="middle" fontFamily={FONT} fontSize={11} fill={INK.muted}>
              {v}
            </text>
          </g>
        ))}
        {means.map((m, i) => {
          const y = top + rowH * i + (rowH - 16) / 2;
          const w = x(m) - labelW;
          const r = Math.min(4, w / 2);
          return (
            <g key={i}>
              <text x={labelW - 8} y={y + 12} textAnchor="end" fontFamily={FONT} fontSize={12} fill={INK.secondary}>
                {i + 1}. {SHORT[i]}
              </text>
              {w > 0 && <path d={`M${labelW},${y}H${labelW + w - r}Q${labelW + w},${y} ${labelW + w},${y + r}V${y + 16 - r}Q${labelW + w},${y + 16} ${labelW + w - r},${y + 16}H${labelW}Z`} fill={EMPHASIS.web} />}
              <text x={labelW + w + 6} y={y + 12} fontFamily={FONT} fontSize={11} fill={INK.primary}>
                {m.toFixed(1).replace(".", ",")}
              </text>
            </g>
          );
        })}
      </svg>
      <ChartFooter
        svgRef={svgRef}
        filename="sus-per-butir"
        table={
          <table className={TABLE_CLASS}>
            <thead>
              <tr>
                <th>Butir</th>
                <th>Pernyataan</th>
                <th className="text-right">Skor 0-4</th>
              </tr>
            </thead>
            <tbody>
              {means.map((m, i) => (
                <tr key={i}>
                  <td className="font-mono">{i + 1}</td>
                  <td>{ITEMS[i]}</td>
                  <td className="text-right font-mono">{m.toFixed(2).replace(".", ",")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}
