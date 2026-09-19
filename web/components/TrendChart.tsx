"use client";

import { useMemo, useRef, useState } from "react";
import { ChartFooter, TABLE_CLASS, Tooltip } from "@/components/ChartTools";
import { APP_NAME, CLASS_HEX, INK, nf, pct } from "@/lib/fmt";
import { useWidth } from "@/lib/useWidth";

export type TrendRow = { period: string; n: number; negative: number; neutral: number; positive: number };
export type TrendData = { min_rows_per_period: number; apps: Record<string, TrendRow[]>; total_rows: number };

const FONT = "Plus Jakarta Sans, Arial, sans-serif";
const VOLUME = "#8a8072";

function allQuarters(rows: TrendRow[]): TrendRow[] {
  // isi kuartal yang kosong supaya jarak waktu di sumbu x jujur
  const key = (p: string) => {
    const [y, q] = p.split("-K").map(Number);
    return y * 4 + (q - 1);
  };
  const byKey = new Map(rows.map((r) => [key(r.period), r]));
  const keys = rows.map((r) => key(r.period));
  const out: TrendRow[] = [];
  for (let k = Math.min(...keys); k <= Math.max(...keys); k++) {
    out.push(byKey.get(k) ?? { period: `${Math.floor(k / 4)}-K${(k % 4) + 1}`, n: 0, negative: 0, neutral: 0, positive: 0 });
  }
  return out;
}

export default function TrendChart({ data, defaultApp }: { data: TrendData; defaultApp: string }) {
  const apps = Object.keys(data.apps);
  const [app, setApp] = useState(defaultApp);
  const [hover, setHover] = useState<number | null>(null);
  const [wrapRef, width] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const min = data.min_rows_per_period;
  const rows = useMemo(() => allQuarters(data.apps[app]), [data, app]);

  const M = { l: 44, r: 16, t: 20 };
  const lineH = 190;
  const gap = 46;
  const volH = 80;
  const H = M.t + lineH + gap + volH + 30;
  const plotW = width - M.l - M.r;
  const band = plotW / rows.length;
  const cx = (i: number) => M.l + band * (i + 0.5);
  const yNeg = (v: number) => M.t + lineH * (1 - v);
  const maxN = Math.max(...rows.map((r) => r.n));
  const volTop = M.t + lineH + gap;
  const yVol = (n: number) => volTop + volH * (1 - n / maxN);
  const valid = rows.map((r) => r.n >= min);
  const share = rows.map((r) => (r.n ? r.negative / r.n : 0));

  // garis putus di kuartal yang ulasannya terlalu sedikit
  let path = "";
  rows.forEach((_, i) => {
    if (!valid[i]) return;
    path += `${i > 0 && valid[i - 1] ? "L" : "M"}${cx(i).toFixed(1)},${yNeg(share[i]).toFixed(1)}`;
  });
  const validIdx = rows.map((_, i) => i).filter((i) => valid[i]);
  const peak = validIdx.reduce((a, b) => (share[b] > share[a] ? b : a), validIdx[0]);
  const last = validIdx[validIdx.length - 1];
  const barW = Math.min(24, Math.max(3, band - 2));
  const everyYear = band * 4 < 34 ? 2 : 1;

  const h = hover !== null ? rows[hover] : null;

  return (
    <div>
      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Pilih aplikasi">
        {apps.map((a) => (
          <button
            key={a}
            type="button"
            role="radio"
            aria-checked={a === app}
            onClick={() => {
              setApp(a);
              setHover(null);
            }}
            className={`rounded-full border-2 px-3 py-1 text-sm transition duration-300 hover:-translate-y-0.5 ${
              a === app ? "border-aspal bg-aspal text-putih" : "border-aspal/25 bg-white hover:border-aspal"
            }`}
          >
            {APP_NAME[a] ?? a}
          </button>
        ))}
      </div>

      <p className="mt-4 text-sm text-aspal-2">
        Kuartal dengan porsi ulasan negatif tertinggi di {APP_NAME[app]}: <b className="text-aspal">{rows[peak].period}</b>, {pct(share[peak])} dari{" "}
        {nf.format(rows[peak].n)} ulasan. Kuartal terakhir di data: <b className="text-aspal">{rows[last].period}</b>, {pct(share[last])}.
      </p>

      <div ref={wrapRef} className="relative mt-4" onMouseLeave={() => setHover(null)}>
        <svg ref={svgRef} viewBox={`0 0 ${width} ${H}`} width={width} height={H} role="img" aria-label={`Porsi ulasan negatif per kuartal untuk ${APP_NAME[app]}`}>
          <rect x={0} y={0} width={width} height={H} fill={INK.surface} />
          <text x={M.l} y={12} fontFamily={FONT} fontSize={12} fill={INK.muted}>
            Porsi ulasan bintang 1-2 (negatif) per kuartal, {APP_NAME[app]}
          </text>
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <g key={v}>
              <line x1={M.l} x2={width - M.r} y1={yNeg(v)} y2={yNeg(v)} stroke={INK.grid} strokeWidth={1} />
              <text x={M.l - 8} y={yNeg(v) + 4} textAnchor="end" fontFamily={FONT} fontSize={11} fill={INK.muted}>
                {Math.round(v * 100)}%
              </text>
            </g>
          ))}
          {hover !== null && <line x1={cx(hover)} x2={cx(hover)} y1={M.t} y2={volTop + volH} stroke={INK.muted} strokeWidth={1} />}
          <path d={path} fill="none" stroke={CLASS_HEX.negative} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
          {rows.map((r, i) =>
            valid[i] && (i === peak || i === last || i === hover || !valid[i - 1] || !valid[i + 1]) ? (
              <circle key={r.period} cx={cx(i)} cy={yNeg(share[i])} r={4} fill={CLASS_HEX.negative} stroke={INK.surface} strokeWidth={2} />
            ) : null,
          )}
          {[peak, last].filter((v, i, a) => a.indexOf(v) === i).map((i) => (
            <text
              key={`lbl${i}`}
              x={Math.min(cx(i), width - M.r - 4)}
              y={yNeg(share[i]) - 10}
              textAnchor={cx(i) > width - 60 ? "end" : "middle"}
              fontFamily={FONT}
              fontSize={11}
              fontWeight={600}
              fill={INK.primary}
            >
              {pct(share[i], 0)}
            </text>
          ))}

          <text x={M.l} y={volTop - 10} fontFamily={FONT} fontSize={12} fill={INK.muted}>
            Jumlah ulasan per kuartal (puncak {nf.format(maxN)})
          </text>
          <line x1={M.l} x2={width - M.r} y1={volTop + volH} y2={volTop + volH} stroke={INK.grid} strokeWidth={1} />
          {rows.map((r, i) => {
            if (!r.n) return null;
            const y = yVol(r.n);
            const hgt = volTop + volH - y;
            const rad = Math.min(4, barW / 2, hgt);
            const x = cx(i) - barW / 2;
            return (
              <path
                key={`v${r.period}`}
                d={`M${x},${volTop + volH}V${y + rad}Q${x},${y} ${x + rad},${y}H${x + barW - rad}Q${x + barW},${y} ${x + barW},${y + rad}V${volTop + volH}Z`}
                fill={VOLUME}
                opacity={valid[i] ? 1 : 0.4}
              />
            );
          })}
          {rows.map((r, i) =>
            r.period.endsWith("K1") && Number(r.period.slice(0, 4)) % everyYear === 0 ? (
              <text key={`x${r.period}`} x={cx(i) - band / 2} y={volTop + volH + 18} fontFamily={FONT} fontSize={11} fill={INK.muted}>
                {r.period.slice(0, 4)}
              </text>
            ) : null,
          )}
          {rows.map((r, i) => (
            <rect
              key={`hit${r.period}`}
              x={cx(i) - band / 2}
              y={M.t}
              width={band}
              height={volTop + volH - M.t}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
              onClick={() => setHover(i)}
            />
          ))}
        </svg>
        {h && hover !== null && (
          <Tooltip x={cx(hover)} y={valid[hover] ? yNeg(share[hover]) : volTop} width={width}>
            <p className="font-semibold">{h.period}</p>
            {h.n >= min ? (
              <>
                <p>Negatif {pct(h.negative / h.n)}</p>
                <p>Netral {pct(h.neutral / h.n)}</p>
                <p>Positif {pct(h.positive / h.n)}</p>
              </>
            ) : (
              <p className="text-abu">Ulasan terlalu sedikit untuk dihitung persennya</p>
            )}
            <p className="text-abu">{nf.format(h.n)} ulasan</p>
          </Tooltip>
        )}
      </div>
      <p className="mt-1 text-xs text-abu">
        Label dari bintang, bukan tebakan model. Kuartal dengan kurang dari {min} ulasan tidak dihitung persennya (batang pudar).
      </p>
      <ChartFooter
        svgRef={svgRef}
        filename={`tren-keluhan-${app}`}
        table={
          <table className={TABLE_CLASS}>
            <thead>
              <tr>
                <th>Kuartal</th>
                <th className="text-right">Ulasan</th>
                <th className="text-right">Negatif</th>
                <th className="text-right">Netral</th>
                <th className="text-right">Positif</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {rows.map((r) => (
                <tr key={r.period}>
                  <td>{r.period}</td>
                  <td className="text-right">{nf.format(r.n)}</td>
                  <td className="text-right">{r.n ? pct(r.negative / r.n) : "-"}</td>
                  <td className="text-right">{r.n ? pct(r.neutral / r.n) : "-"}</td>
                  <td className="text-right">{r.n ? pct(r.positive / r.n) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}
