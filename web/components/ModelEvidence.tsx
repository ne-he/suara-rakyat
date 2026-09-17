"use client";

import { useState } from "react";

type Label = "negative" | "neutral" | "positive";
export type Evidence = {
  id: string;
  name: string;
  features: string;
  fitSeconds: number;
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

export default function ModelEvidence({ models }: { models: Evidence[] }) {
  const [active, setActive] = useState(models[0].id);
  const m = models.find((x) => x.id === active) ?? models[0];

  return (
    <div>
      <div role="tablist" aria-label="Pilih model" className="flex flex-wrap gap-2">
        {models.map((x) => (
          <button
            key={x.id}
            role="tab"
            aria-selected={x.id === active}
            onClick={() => setActive(x.id)}
            className={`display rounded-full border-2 px-5 py-2 text-xl transition ${
              x.id === active ? "border-aspal bg-merah text-putih shadow-[3px_3px_0_var(--aspal)]" : "border-aspal/30 bg-white hover:border-aspal"
            }`}
          >
            {x.name}
          </button>
        ))}
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { k: "Macro-F1 test", v: dec(m.testF1), s: `tanpa geser bias ${dec(m.testF1Raw)}` },
          { k: "Akurasi test", v: pct(m.accuracy), s: `val macro-F1 ${dec(m.valF1)}` },
          { k: "Polaritas terbalik", v: pct(m.flipRate), s: "negatif jadi positif atau sebaliknya" },
          { k: "Waktu latih", v: m.fitSeconds < 1 ? "< 1 dtk" : `${Math.round(m.fitSeconds)} dtk`, s: `fitur ${m.features}` },
        ].map((c) => (
          <div key={c.k} className="rounded-xl border-2 border-aspal bg-white p-4">
            <p className="kicker text-abu">{c.k}</p>
            <p className="display mt-2 text-5xl">{c.v}</p>
            <p className="mt-1 text-xs text-abu">{c.s}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker text-abu">Per kelas</p>
          <div className="mt-4 space-y-4">
            {LABELS.map((l) => (
              <div key={l}>
                <div className="flex items-baseline justify-between">
                  <span className="font-semibold" style={{ color: COLOR[l] }}>
                    {LABEL_ID[l]}
                  </span>
                  <span className="font-mono text-sm">F1 {dec(m.perClass[l].f1)}</span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-kertas">
                  <div className="bar-fill h-full rounded-full" style={{ width: `${(m.perClass[l].f1 * 100).toFixed(1)}%`, background: COLOR[l] }} />
                </div>
                <p className="mt-1 text-xs text-abu">
                  presisi {pct(m.perClass[l].precision)} · recall {pct(m.perClass[l].recall)} · {nf.format(m.perClass[l].support)} ulasan
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker text-abu">Matriks kebingungan</p>
          <div className="mt-4 grid grid-cols-[60px_repeat(3,1fr)] gap-1 text-center text-xs">
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
                  return (
                    <div
                      key={`${row}${j}`}
                      className="flex aspect-square flex-col items-center justify-center rounded-md"
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
          <p className="mt-3 text-xs text-abu">Baris = label asli, kolom = prediksi.</p>
        </div>

        <div className="rounded-xl border-2 border-aspal bg-white p-5">
          <p className="kicker text-abu">Macro-F1 per aplikasi</p>
          <div className="mt-4 space-y-2.5">
            {Object.entries(m.byApp)
              .sort((a, b) => b[1] - a[1])
              .map(([app, f1]) => (
                <div key={app}>
                  <div className="flex justify-between text-sm">
                    <span>{APP_NAME[app] ?? app}</span>
                    <span className="font-mono">{dec(f1)}</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-kertas">
                    <div className="bar-fill h-full rounded-full bg-aspal" style={{ width: `${(f1 * 100).toFixed(1)}%` }} />
                  </div>
                </div>
              ))}
          </div>
          <p className="mt-4 text-xs text-abu">
            Akurasi kalau netral dikesampingkan: <b className="text-aspal">{pct(m.binaryAccuracy)}</b>. Info BMKG dan KAI Access datanya sedikit, jadi
            skornya paling goyah.
          </p>
        </div>
      </div>
    </div>
  );
}
