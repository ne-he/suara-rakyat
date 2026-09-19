"use client";

import { useRef, useState } from "react";
import { ChartFooter, TABLE_CLASS, Tooltip } from "@/components/ChartTools";
import { downloadCsv } from "@/lib/download";
import { dec, duration, EMPHASIS, INK, LABEL_ID, LABELS, ms, nf, pct, type Label } from "@/lib/fmt";
import { useWidth } from "@/lib/useWidth";

export type MainModel = {
  id: string;
  name: string;
  status: "web" | "server" | "pembanding";
  macroF1: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: Record<Label, number>;
  msPerReview: number | null;
  speedNote: string;
  fitSeconds: number | null;
  fitNote: string;
};
export type BoardRow = {
  name: string;
  family: string;
  features: string;
  web_id: string | null;
  comparison: boolean;
  val_macro_f1: number;
  test_macro_f1: number;
  test_macro_f1_raw?: number;
  test_accuracy: number;
  fit_seconds: number | null;
};

const FONT = "Plus Jakarta Sans, Arial, sans-serif";
const STATUS_ID = { web: "jalan di web", server: "server terpisah", pembanding: "hanya skor" };
const colorOf = (r: { features: string; web_id?: string | null }) =>
  r.features.startsWith("transformer") ? EMPHASIS.transformer : r.web_id ? EMPHASIS.web : EMPHASIS.other;

function roundedBar(x: number, y: number, w: number, h: number) {
  // ujung data membulat 4px, pangkal di sumbu tetap siku
  const r = Math.min(4, w / 2, h / 2);
  return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
}

function Legend({ items }: { items: { color: string; label: string }[] }) {
  return (
    <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-aspal-2">
      {items.map((it) => (
        <span key={it.label} className="inline-flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: it.color }} aria-hidden />
          {it.label}
        </span>
      ))}
    </div>
  );
}

export function ScoreVsTime({ rows }: { rows: BoardRow[] }) {
  const pts = rows.filter((r) => r.fit_seconds != null && !r.name.startsWith("dummy"));
  const [ref, width] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const M = { l: 52, r: 20, t: 16, b: 40 };
  const H = 340;
  const xs = pts.map((p) => Math.log10(Math.max(0.1, p.fit_seconds!)));
  const ys = pts.map((p) => p.test_macro_f1);
  const x0 = -1;
  const x1 = Math.ceil(Math.max(...xs));
  const y0 = Math.floor((Math.min(...ys) - 0.005) * 100) / 100;
  const y1 = Math.ceil((Math.max(...ys) + 0.005) * 100) / 100;
  const X = (v: number) => M.l + ((v - x0) / (x1 - x0)) * (width - M.l - M.r);
  const Y = (v: number) => M.t + (1 - (v - y0) / (y1 - y0)) * (H - M.t - M.b);
  const yTicks: number[] = [];
  for (let v = y0; v <= y1 + 1e-9; v += 0.01) yTicks.push(Math.round(v * 100) / 100);
  const xTicks = [0.1, 1, 10, 100, 1000, 10000].filter((t) => Math.log10(t) >= x0 && Math.log10(t) <= x1);
  const highlight = pts.map((p) => p.features.startsWith("transformer") || !!p.web_id);
  // urutan gambar: abu dulu, sorotan paling atas
  const order = pts.map((_, i) => i).sort((a, b) => Number(highlight[a]) - Number(highlight[b]));

  return (
    <div>
      <div
        ref={ref}
        className="relative"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const box = e.currentTarget.getBoundingClientRect();
          const mx = e.clientX - box.left;
          const my = e.clientY - box.top;
          let best = -1;
          let bd = 28 * 28;
          pts.forEach((_, i) => {
            const d = (X(xs[i]) - mx) ** 2 + (Y(ys[i]) - my) ** 2;
            if (d < bd) {
              bd = d;
              best = i;
            }
          });
          setHover(best >= 0 ? best : null);
        }}
      >
        <svg ref={svgRef} viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label="Macro-F1 test dibanding waktu latih untuk semua konfigurasi">
          <rect width={width} height={H} fill={INK.surface} />
          {yTicks.map((v) => (
            <g key={`y${v}`}>
              <line x1={M.l} x2={width - M.r} y1={Y(v)} y2={Y(v)} stroke={INK.grid} strokeWidth={1} />
              <text x={M.l - 8} y={Y(v) + 4} textAnchor="end" fontFamily={FONT} fontSize={11} fill={INK.muted}>
                {dec(v, 2)}
              </text>
            </g>
          ))}
          {xTicks.map((t) => (
            <text key={`x${t}`} x={X(Math.log10(t))} y={H - M.b + 18} textAnchor="middle" fontFamily={FONT} fontSize={11} fill={INK.muted}>
              {t < 1 ? "0,1 dtk" : t < 60 ? `${t} dtk` : t < 3600 ? `${Math.round(t / 60)} mnt` : `${Math.round(t / 3600)} jam`}
            </text>
          ))}
          <text x={width - M.r} y={H - 6} textAnchor="end" fontFamily={FONT} fontSize={11} fill={INK.muted}>
            waktu latih (skala log)
          </text>
          <text x={M.l} y={M.t - 4} fontFamily={FONT} fontSize={11} fill={INK.muted}>
            macro-F1 test
          </text>
          {order.map((i) => (
            <circle
              key={pts[i].name}
              cx={X(xs[i])}
              cy={Y(ys[i])}
              r={hover === i ? 7 : highlight[i] ? 6 : 4.5}
              fill={colorOf(pts[i])}
              stroke={INK.surface}
              strokeWidth={2}
            />
          ))}
          {pts.map((p, i) => {
            if (!highlight[i]) return null;
            const right = X(xs[i]) < width - 150;
            const below = p.name.endsWith("_int8");
            return (
              <text
                key={`l${p.name}`}
                x={X(xs[i]) + (right ? 10 : -10)}
                y={Y(ys[i]) + (below ? 16 : -8)}
                textAnchor={right ? "start" : "end"}
                fontFamily={FONT}
                fontSize={11}
                fontWeight={600}
                fill={INK.primary}
              >
                {p.web_id ? p.family : below ? "IndoBERTweet int8" : p.name.startsWith("indo") ? "IndoBERTweet" : p.family}
              </text>
            );
          })}
        </svg>
        {hover !== null && (
          <Tooltip x={X(xs[hover])} y={Y(ys[hover])} width={width}>
            <p className="font-semibold">{pts[hover].family}</p>
            <p className="font-mono text-[10px] text-abu">{pts[hover].name}</p>
            <p>macro-F1 test {dec(ys[hover])}</p>
            <p>latih {duration(pts[hover].fit_seconds!)}</p>
          </Tooltip>
        )}
      </div>
      <Legend
        items={[
          { color: EMPHASIS.transformer, label: "Transformer (IndoBERTweet)" },
          { color: EMPHASIS.web, label: "Model di web" },
          { color: EMPHASIS.other, label: "Konfigurasi lain" },
        ]}
      />
      <p className="mt-1 text-xs text-abu">Model linear dilatih di CPU laptop, IndoBERTweet di GPU T4 Colab. Gabungan skor tidak punya waktu latih sendiri, jadi tidak digambar.</p>
      <ChartFooter
        svgRef={svgRef}
        filename="skor-vs-waktu-latih"
        table={
          <table className={TABLE_CLASS}>
            <thead>
              <tr>
                <th>Model</th>
                <th className="text-right">Macro-F1 test</th>
                <th className="text-right">Waktu latih</th>
              </tr>
            </thead>
            <tbody>
              {pts.map((p) => (
                <tr key={p.name}>
                  <td>
                    {p.family} <span className="font-mono text-abu">{p.name}</span>
                  </td>
                  <td className="text-right font-mono">{dec(p.test_macro_f1)}</td>
                  <td className="text-right font-mono">{nf.format(p.fit_seconds!)} dtk</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}

export function PerClassF1({ models }: { models: MainModel[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const narrow = width < 640;
  const labelW = 150;
  const barH = 16;
  const rowH = 26;
  const panelH = 30 + rowH * models.length;
  const cols = narrow ? 1 : 3;
  const panelW = cols === 1 ? width : (width - 24 * 2) / 3;
  const H = (narrow ? 3 : 1) * (panelH + 12) + 10;
  const color = (m: MainModel) => (m.status === "web" ? EMPHASIS.web : EMPHASIS.transformer);

  return (
    <div ref={ref}>
      <svg ref={svgRef} viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label="F1 per kelas untuk model utama">
        <rect width={width} height={H} fill={INK.surface} />
        {LABELS.map((l, p) => {
          const ox = cols === 1 ? 0 : p * (panelW + 24);
          const oy = cols === 1 ? p * (panelH + 12) : 0;
          const lw = cols === 1 ? labelW : 0;
          const plotW = panelW - lw - 44;
          return (
            <g key={l} transform={`translate(${ox},${oy})`}>
              <text x={0} y={16} fontFamily={FONT} fontSize={13} fontWeight={600} fill={INK.primary}>
                F1 {LABEL_ID[l].toLowerCase()}
              </text>
              {models.map((m, i) => {
                const y = 30 + i * rowH;
                const w = Math.max(2, m.f1[l] * plotW);
                return (
                  <g key={m.id}>
                    {cols === 1 ? (
                      <text x={lw - 8} y={y + 12} textAnchor="end" fontFamily={FONT} fontSize={11} fill={INK.secondary}>
                        {m.name}
                      </text>
                    ) : null}
                    <path d={roundedBar(lw, y, w, barH)} fill={color(m)} />
                    <text x={lw + w + 6} y={y + 12} fontFamily={FONT} fontSize={11} fill={INK.primary}>
                      {dec(m.f1[l])}
                      {cols !== 1 ? ` ${m.name}` : ""}
                    </text>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <Legend
        items={[
          { color: EMPHASIS.transformer, label: "IndoBERTweet" },
          { color: EMPHASIS.web, label: "Model di web" },
        ]}
      />
      <ChartFooter
        svgRef={svgRef}
        filename="f1-per-kelas"
        table={
          <table className={TABLE_CLASS}>
            <thead>
              <tr>
                <th>Model</th>
                {LABELS.map((l) => (
                  <th key={l} className="text-right">
                    F1 {LABEL_ID[l].toLowerCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id}>
                  <td>{m.name}</td>
                  {LABELS.map((l) => (
                    <td key={l} className="text-right font-mono">
                      {dec(m.f1[l])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}

export function SpeedBars({ models }: { models: MainModel[] }) {
  const rows = models.filter((m) => m.msPerReview != null);
  const [ref, width] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const labelW = Math.min(170, width * 0.4);
  const rowH = 34;
  const H = 20 + rowH * rows.length + 30;
  const lo = -1;
  const hi = 2;
  const plotW = width - labelW - 70;
  const X = (v: number) => ((Math.log10(v) - lo) / (hi - lo)) * plotW;
  return (
    <div ref={ref}>
      <svg ref={svgRef} viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label="Waktu baca per ulasan di CPU laptop">
        <rect width={width} height={H} fill={INK.surface} />
        {[0.1, 1, 10, 100].map((t) => (
          <g key={t}>
            <line x1={labelW + X(t)} x2={labelW + X(t)} y1={14} y2={H - 26} stroke={INK.grid} strokeWidth={1} />
            <text x={labelW + X(t)} y={H - 8} textAnchor="middle" fontFamily={FONT} fontSize={11} fill={INK.muted}>
              {String(t).replace(".", ",")} ms
            </text>
          </g>
        ))}
        {rows.map((m, i) => {
          const y = 20 + i * rowH;
          const w = Math.max(2, X(m.msPerReview!));
          return (
            <g key={m.id}>
              <text x={labelW - 8} y={y + 12} textAnchor="end" fontFamily={FONT} fontSize={12} fill={INK.secondary}>
                {m.name}
              </text>
              <path d={roundedBar(labelW, y, w, 16)} fill={m.status === "web" ? EMPHASIS.web : EMPHASIS.transformer} />
              <text x={labelW + w + 6} y={y + 12} fontFamily={FONT} fontSize={11} fontWeight={600} fill={INK.primary}>
                {ms(m.msPerReview!)}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="mt-1 text-xs text-abu">Satu ulasan per panggilan di CPU laptop yang sama. Skala log: tiap garis 10 kali lebih lambat.</p>
      <ChartFooter
        svgRef={svgRef}
        filename="kecepatan-baca"
        table={
          <table className={TABLE_CLASS}>
            <thead>
              <tr>
                <th>Model</th>
                <th className="text-right">Per ulasan</th>
                <th>Catatan</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.id}>
                  <td>{m.name}</td>
                  <td className="text-right font-mono">{ms(m.msPerReview!)}</td>
                  <td>{m.speedNote}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}

export function StatusBadge({ status }: { status: MainModel["status"] }) {
  const cls = status === "web" ? "bg-merah text-putih" : status === "server" ? "bg-aspal text-putih" : "border border-aspal/40 text-aspal";
  return <span className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 font-mono text-[10px] uppercase ${cls}`}>{STATUS_ID[status]}</span>;
}

export function MainTable({ models }: { models: MainModel[] }) {
  return (
    <div>
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="kicker border-b-2 border-aspal text-abu">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Macro-F1</th>
              <th className="px-4 py-3 text-right">Akurasi</th>
              <th className="px-4 py-3 text-right">Presisi</th>
              <th className="px-4 py-3 text-right">Recall</th>
              <th className="px-4 py-3 text-right">F1 netral</th>
              <th className="px-4 py-3 text-right">Baca / ulasan</th>
              <th className="px-4 py-3 text-right">Latih</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id} className="baris border-b border-garis last:border-0">
                <td className="px-4 py-2.5 font-semibold">{m.name}</td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={m.status} />
                </td>
                <td className="px-4 py-2.5 text-right font-mono font-semibold">{dec(m.macroF1)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{pct(m.accuracy)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{pct(m.precision)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{pct(m.recall)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{dec(m.f1.neutral)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{m.msPerReview == null ? "-" : ms(m.msPerReview)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{m.fitSeconds == null ? "-" : duration(m.fitSeconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <UnduhTabel
        nama="ringkasan-model"
        rows={[
          ["model", "status", "macro_f1_test", "akurasi", "presisi_makro", "recall_makro", "f1_negatif", "f1_netral", "f1_positif", "ms_per_ulasan", "catatan_kecepatan", "detik_latih", "catatan_latih"],
          ...models.map((m) => [
            m.name,
            STATUS_ID[m.status],
            m.macroF1,
            m.accuracy,
            m.precision,
            m.recall,
            m.f1.negative,
            m.f1.neutral,
            m.f1.positive,
            m.msPerReview ?? "",
            m.speedNote,
            m.fitSeconds ?? "",
            m.fitNote,
          ]),
        ]}
      />
    </div>
  );
}

export function BoardTable({ rows, featureId }: { rows: BoardRow[]; featureId: Record<string, string> }) {
  return (
    <div>
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="kicker border-b-2 border-aspal text-abu">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Fitur</th>
              <th className="px-4 py-3 text-right">Val F1</th>
              <th className="px-4 py-3 text-right">Test F1</th>
              <th className="px-4 py-3 text-right">Akurasi</th>
              <th className="px-4 py-3 text-right">Latih</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className={`baris border-b border-garis last:border-0 ${r.web_id ? "bg-merah/5" : ""}`}>
                <td className="px-4 py-2.5">
                  <span className="font-semibold">{r.family}</span>
                  <span className="block font-mono text-[11px] text-abu">{r.name}</span>
                </td>
                <td className="px-4 py-2.5 text-aspal-2">{featureId[r.features] ?? r.features}</td>
                <td className="px-4 py-2.5 text-right font-mono">{dec(r.val_macro_f1)}</td>
                <td className="px-4 py-2.5 text-right font-mono font-semibold">{dec(r.test_macro_f1)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{pct(r.test_accuracy)}</td>
                <td className="px-4 py-2.5 text-right font-mono">{r.fit_seconds == null ? "-" : duration(r.fit_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <UnduhTabel
        nama="papan-perbandingan"
        rows={[
          ["model", "keluarga", "fitur", "val_macro_f1", "test_macro_f1", "test_macro_f1_tanpa_geser_bias", "akurasi", "detik_latih", "di_web"],
          ...rows.map((r) => [r.name, r.family, r.features, r.val_macro_f1, r.test_macro_f1, r.test_macro_f1_raw ?? "", r.test_accuracy, r.fit_seconds ?? "", r.web_id ? "ya" : "tidak"]),
        ]}
      />
    </div>
  );
}

function UnduhTabel({ nama, rows }: { nama: string; rows: (string | number)[][] }) {
  return (
    <button
      type="button"
      onClick={() => downloadCsv(rows, `${nama}.csv`)}
      className="mt-3 rounded-full border border-aspal/40 bg-white px-3 py-1 text-xs transition hover:-translate-y-0.5 hover:border-aspal"
    >
      Unduh tabel CSV
    </button>
  );
}
