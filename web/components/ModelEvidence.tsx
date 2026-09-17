"use client";

import { useState } from "react";

type Label = "negative" | "neutral" | "positive";
export type Evidence = {
  id: string;
  name: string;
  features: string;
  live: boolean; // false = model pembanding, skornya ada tapi belum jalan di web
  note?: string;
  fitSeconds: number | null;
  fitHardware: string;
  msPerReview: number | null;
  speedHardware: string;
  valF1: number;
  testF1: number;
  testF1Raw: number;
  accuracy: number;
  flipRate: number;
  binaryAccuracy: number;
  perClass: Record<Label, { precision: number; recall: number; f1: number; support: number }>;
  confusion: number[][];
  byApp: Record<string, number>;
};

const LABELS: Label[] = ["negative", "neutral", "positive"];
const LABEL_ID: Record<Label, string> = { negative: "Negatif", neutral: "Netral", positive: "Positif" };
const COLOR: Record<Label, string> = { negative: "var(--neg)", neutral: "var(--neu)", positive: "var(--pos)" };
const APP_NAME: Record<string, string> = {
  JMO: "JMO",
  satusehat: "SatuSehat",
  mobileJKN: "Mobile JKN",
  pertamina: "MyPertamina",
  KAI: "KAI Access",
  BMKG: "Info BMKG",
};
const nf = new Intl.NumberFormat("id-ID");
const pct = (x: number, d = 1) => `${(x * 100).toFixed(d).replace(".", ",")}%`;
const dec = (x: number) => x.toFixed(3).replace(".", ",");
const ms = (x: number) => `${x.toFixed(x < 1 ? 2 : 1).replace(".", ",")} ms`;
const duration = (s: number) => (s < 1 ? "< 1 dtk" : s < 120 ? `${Math.round(s)} dtk` : `${Math.round(s / 60)} mnt`);

export default function ModelEvidence({ models }: { models: Evidence[] }) {
  const [active, setActive] = useState(models[0].id);
  const [cell, setCell] = useState<[number, number] | null>(null);
  const m = models.find((x) => x.id === active) ?? models[0];
  const macroPrecision = LABELS.reduce((s, l) => s + m.perClass[l].precision, 0) / LABELS.length;
  const totalTest = LABELS.reduce((s, l) => s + m.perClass[l].support, 0);

  let caption = "Baris = label asli, kolom = tebakan model. Arahkan kursor ke kotak untuk membaca artinya.";
  if (cell) {
    const [i, j] = cell;
    const v = m.confusion[i][j];
    const share = v / m.confusion[i].reduce((a, b) => a + b, 0);
    caption =
      i === j
        ? `${pct(share)} ulasan ${LABEL_ID[LABELS[i]].toLowerCase()} ditebak benar (${nf.format(v)} ulasan).`
        : `${pct(share)} ulasan ${LABEL_ID[LABELS[i]].toLowerCase()} malah ditebak ${LABEL_ID[LABELS[j]].toLowerCase()} (${nf.format(v)} ulasan).`;
  }

  const stats = [
    { k: "Macro-F1 test", v: dec(m.testF1), s: `tanpa geser bias ${dec(m.testF1Raw)} · val ${dec(m.valF1)}` },
    { k: "Akurasi", v: pct(m.accuracy), s: `tanpa kelas netral ${pct(m.binaryAccuracy)}` },
    { k: "Presisi", v: pct(macroPrecision), s: "rata-rata tiga kelas" },
    { k: "Kecepatan baca", v: m.msPerReview == null ? "?" : ms(m.msPerReview), s: `per ulasan, ${m.speedHardware}` },
    { k: "Waktu latih", v: m.fitSeconds == null ? "?" : duration(m.fitSeconds), s: `dilatih di ${m.fitHardware}` },
    { k: "Polaritas terbalik", v: pct(m.flipRate), s: "negatif jadi positif atau sebaliknya" },
  ];

  return (
    <div>
      <div role="tablist" aria-label="Pilih model" className="flex flex-wrap gap-2">
        {models.map((x) => {
          const on = x.id === active;
          return (
            <button
              key={x.id}
              role="tab"
              aria-selected={on}
              onClick={() => {
                setActive(x.id);
                setCell(null);
              }}
              className={`display flex items-center gap-2 rounded-full border-2 px-5 py-2 text-xl transition duration-300 hover:-translate-y-0.5 ${
                on
                  ? "border-aspal bg-merah text-putih shadow-[3px_3px_0_var(--aspal)]"
                  : "border-aspal/30 bg-white hover:border-aspal hover:shadow-[3px_3px_0_var(--aspal)]"
              }`}
            >
              {x.name}
              {!x.live && (
                <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] normal-case tracking-normal ${on ? "bg-putih text-merah" : "bg-aspal text-putih"}`}>
                  pembanding
                </span>
              )}
            </button>
          );
        })}
      </div>

      {m.note && (
        <p className="rise mt-4 max-w-3xl rounded-lg border-2 border-dashed border-aspal/40 bg-putih px-4 py-3 text-sm text-aspal-2" key={m.id}>
          {m.note}
        </p>
      )}

      <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
        {stats.map((c) => (
          <div key={c.k} className="poster rounded-xl border-2 border-aspal bg-white p-4 sm:p-5">
            <p className="kicker kicker-garis text-abu">{c.k}</p>
            <p className="display mt-3 text-4xl sm:text-5xl">
              <span className="angka">{c.v}</span>
            </p>
            <p className="mt-1.5 text-xs text-abu">{c.s}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="poster flex flex-col rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker kicker-garis self-start text-abu">Per kelas</p>
          <div className="mt-5 space-y-4">
            {LABELS.map((l) => (
              <div key={l} className="group">
                <div className="flex items-baseline justify-between">
                  <span className="font-semibold transition-transform duration-300 group-hover:translate-x-1" style={{ color: COLOR[l] }}>
                    {LABEL_ID[l]}
                  </span>
                  <span className="font-mono text-sm">F1 {dec(m.perClass[l].f1)}</span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-kertas transition-[height] duration-300 group-hover:h-3">
                  <div className="bar-fill h-full rounded-full" style={{ width: `${(m.perClass[l].f1 * 100).toFixed(1)}%`, background: COLOR[l] }} />
                </div>
                <p className="mt-1 text-xs text-abu">
                  presisi {pct(m.perClass[l].precision)} · recall {pct(m.perClass[l].recall)} · {nf.format(m.perClass[l].support)} ulasan
                </p>
              </div>
            ))}
          </div>
          <div className="mt-auto pt-6">
            <p className="text-xs text-abu">Komposisi {nf.format(totalTest)} ulasan test</p>
            <div className="mt-2 flex h-6 overflow-hidden rounded-md border-2 border-aspal">
              {LABELS.map((l) => (
                <div
                  key={l}
                  className="flex items-center justify-center font-mono text-[10px] text-putih"
                  style={{ width: `${((m.perClass[l].support / totalTest) * 100).toFixed(2)}%`, background: COLOR[l] }}
                  title={`${LABEL_ID[l]} ${pct(m.perClass[l].support / totalTest)}`}
                >
                  {m.perClass[l].support / totalTest > 0.1 ? pct(m.perClass[l].support / totalTest, 0) : ""}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="poster rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker kicker-garis text-abu">Matriks kebingungan</p>
          <div className="mt-5 grid grid-cols-[60px_repeat(3,1fr)] gap-1 text-center text-xs" onMouseLeave={() => setCell(null)}>
            <span />
            {LABELS.map((l) => (
              <span key={l} className="pb-1 text-abu">
                {LABEL_ID[l]}
              </span>
            ))}
            {LABELS.map((row, i) => {
              const total = m.confusion[i].reduce((a, b) => a + b, 0);
              return [
                <span key={`h${row}`} className="flex items-center justify-end pr-1 text-abu">
                  {LABEL_ID[row]}
                </span>,
                ...m.confusion[i].map((v, j) => {
                  const share = v / total;
                  const on = cell?.[0] === i && cell?.[1] === j;
                  return (
                    <div
                      key={`${row}${j}`}
                      tabIndex={0}
                      aria-label={`Label ${LABEL_ID[row]}, ditebak ${LABEL_ID[LABELS[j]]}: ${pct(share)}, ${nf.format(v)} ulasan`}
                      onMouseEnter={() => setCell([i, j])}
                      onFocus={() => setCell([i, j])}
                      onBlur={() => setCell(null)}
                      className={`sel relative flex aspect-square cursor-default flex-col items-center justify-center rounded-md ${on ? "ring-2 ring-aspal" : ""}`}
                      style={{
                        background: `color-mix(in srgb, ${i === j ? COLOR[row] : "var(--aspal)"} ${Math.round(share * 75)}%, var(--kertas))`,
                        color: share > 0.45 ? "var(--putih)" : "var(--aspal)",
                      }}
                    >
                      <span className="font-mono text-sm font-semibold">{pct(share, 0)}</span>
                      <span className="font-mono text-[10px] opacity-80">{nf.format(v)}</span>
                    </div>
                  );
                }),
              ];
            })}
          </div>
          <p className="mt-3 min-h-10 text-xs text-abu" aria-live="polite">
            {caption}
          </p>
        </div>

        <div className="poster rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker kicker-garis text-abu">Macro-F1 per aplikasi</p>
          <div className="mt-5 space-y-2.5">
            {Object.entries(m.byApp)
              .sort((a, b) => b[1] - a[1])
              .map(([app, f1]) => (
                <div key={app} className="group">
                  <div className="flex justify-between text-sm">
                    <span className="transition-transform duration-300 group-hover:translate-x-1">{APP_NAME[app] ?? app}</span>
                    <span className="font-mono transition-colors duration-300 group-hover:text-merah">{dec(f1)}</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-kertas transition-[height] duration-300 group-hover:h-2.5">
                    <div
                      className="bar-fill h-full rounded-full bg-aspal transition-colors duration-300 group-hover:bg-merah"
                      style={{ width: `${(f1 * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
          <p className="mt-4 text-xs text-abu">Info BMKG dan KAI Access datanya sedikit, jadi skor keduanya paling goyah.</p>
        </div>
      </div>
    </div>
  );
}
