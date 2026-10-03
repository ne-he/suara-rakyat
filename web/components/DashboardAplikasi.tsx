"use client";

import { useRef, useState } from "react";
import TrendChart, { type TrendData } from "@/components/TrendChart";
import { CLASS_HEX, LABEL_ID, LABELS, nf, pct, type Label } from "@/lib/fmt";

export type Istilah = { teks: string; ulasan: number; porsi: number };
export type Aplikasi = {
  id: string;
  nama: string;
  pengelola: string;
  ulasan: number;
  mulai: string;
  akhir: string;
  rata_bintang: number;
  porsi: Record<Label, number>;
  keluhan: Istilah[];
  pujian: Istilah[];
  contoh: { teks: string; label: Label; bintang: number }[];
};
export type DataAplikasi = { ulasan: number; mulai: string; akhir: string; porsi: Record<Label, number>; apps: Aplikasi[] };

const BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const tgl = (iso: string) => `${BULAN[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
const koma = (x: number, d = 2) => x.toFixed(d).replace(".", ",");

export default function DashboardAplikasi({ data, trend }: { data: DataAplikasi; trend: TrendData | null }) {
  const urut = [...data.apps].sort((a, b) => b.porsi.negative - a.porsi.negative);
  const [pilih, setPilih] = useState(urut[0].id);
  const detailRef = useRef<HTMLDivElement>(null);
  const app = data.apps.find((a) => a.id === pilih)!;

  function buka(id: string, gulir: boolean) {
    setPilih(id);
    if (gulir) detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="space-y-14">
      <section aria-labelledby="ringkas">
        <h2 id="ringkas" className="display text-4xl sm:text-5xl">
          Mana yang paling banyak dikeluhkan?
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-aspal-2">
          Diurutkan dari porsi ulasan negatif terbesar. Klik salah satu aplikasi untuk melihat apa yang paling sering dikeluhkan dan dipuji.
        </p>
        <div className="poster mt-5 rounded-xl border-2 border-aspal bg-white p-4 sm:p-6">
          <ul className="space-y-4">
            {urut.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  onClick={() => buka(a.id, true)}
                  aria-pressed={a.id === pilih}
                  className={`group block w-full rounded-lg p-2 text-left transition hover:bg-kertas ${a.id === pilih ? "bg-kertas" : ""}`}
                >
                  <span className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
                    <span className="font-semibold text-aspal">{a.nama}</span>
                    <span className="text-xs text-abu">
                      {nf.format(a.ulasan)} ulasan · rata-rata {koma(a.rata_bintang, 1)} bintang
                    </span>
                  </span>
                  <span className="mt-2 flex h-6 w-full overflow-hidden rounded-md" aria-label={LABELS.map((l) => `${LABEL_ID[l]} ${pct(a.porsi[l])}`).join(", ")}>
                    {LABELS.map((l) => (
                      <span
                        key={l}
                        className="flex items-center justify-center text-[11px] font-semibold"
                        style={{ width: `${a.porsi[l] * 100}%`, background: CLASS_HEX[l], color: l === "neutral" ? "#141210" : "#fff" }}
                      >
                        {a.porsi[l] >= 0.09 ? pct(a.porsi[l], 0) : ""}
                      </span>
                    ))}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 border-t border-garis pt-3 text-xs text-aspal-2">
            {LABELS.map((l) => (
              <span key={l} className="inline-flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm" style={{ background: CLASS_HEX[l] }} aria-hidden />
                {LABEL_ID[l]} {l === "negative" ? "(bintang 1-2)" : l === "neutral" ? "(bintang 3)" : "(bintang 4-5)"}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section ref={detailRef} aria-labelledby="detail" className="scroll-mt-20">
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Pilih aplikasi">
          {data.apps.map((a) => (
            <button
              key={a.id}
              type="button"
              role="radio"
              aria-checked={a.id === pilih}
              onClick={() => buka(a.id, false)}
              className={`rounded-full border-2 px-4 py-1.5 text-sm transition duration-300 hover:-translate-y-0.5 ${
                a.id === pilih ? "border-aspal bg-aspal text-putih" : "border-aspal/25 bg-white hover:border-aspal"
              }`}
            >
              {a.nama}
            </button>
          ))}
        </div>

        <h2 id="detail" className="display mt-6 text-5xl sm:text-6xl">
          {app.nama}
        </h2>
        <p className="mt-1 text-sm text-abu">
          Aplikasi {app.pengelola}. Ulasan dari {tgl(app.mulai)} sampai {tgl(app.akhir)}.
        </p>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          <Stat k="Ulasan" v={nf.format(app.ulasan)} s="dari Google Play" />
          <Stat k="Rata-rata bintang" v={koma(app.rata_bintang)} s="dari 5" />
          <Stat k="Negatif" v={pct(app.porsi.negative)} s={`${nf.format(Math.round(app.ulasan * app.porsi.negative))} ulasan`} dot={CLASS_HEX.negative} />
          <Stat k="Positif" v={pct(app.porsi.positive)} s={`${nf.format(Math.round(app.ulasan * app.porsi.positive))} ulasan`} dot={CLASS_HEX.positive} />
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Daftar
            judul="Paling sering dikeluhkan"
            ket="Kata yang jauh lebih sering muncul di ulasan negatif daripada di ulasan positif aplikasi ini."
            isi={app.keluhan}
            label="negative"
            kosong={`Ulasan negatif ${app.nama} terlalu sedikit untuk dirangkum.`}
          />
          <Daftar
            judul="Paling sering dipuji"
            ket="Kata yang jauh lebih sering muncul di ulasan positif daripada di ulasan negatif aplikasi ini."
            isi={app.pujian}
            label="positive"
            kosong={`Ulasan positif ${app.nama} terlalu sedikit untuk dirangkum.`}
          />
        </div>

        {app.contoh.length > 0 && (
          <div className="mt-6">
            <p className="kicker kicker-garis text-abu">Contoh ulasan asli</p>
            <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {app.contoh.map((c) => (
                <li key={c.teks} className="rounded-xl border-2 border-aspal/15 bg-white p-4">
                  <span className="inline-flex items-center gap-2 text-xs font-semibold" style={{ color: CLASS_HEX[c.label] }}>
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: CLASS_HEX[c.label] }} aria-hidden />
                    {LABEL_ID[c.label]} · {c.bintang} bintang
                  </span>
                  <p className="marker mt-2 text-lg leading-snug text-aspal">&ldquo;{c.teks}&rdquo;</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {trend?.apps[app.id] && (
          <div className="mt-8">
            <p className="kicker kicker-garis text-abu">Naik turunnya keluhan per tiga bulan</p>
            <div className="poster mt-4 rounded-xl border-2 border-aspal bg-white p-4 sm:p-6">
              <TrendChart data={trend} defaultApp={app.id} app={app.id} />
            </div>
          </div>
        )}
      </section>
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

function Daftar({ judul, ket, isi, label, kosong }: { judul: string; ket: string; isi: Istilah[]; label: Label; kosong: string }) {
  const puncak = Math.max(...isi.map((x) => x.porsi), 1e-9);
  return (
    <div className="poster rounded-xl border-2 border-aspal bg-white p-5">
      <p className="kicker kicker-garis text-abu">{judul}</p>
      <p className="mt-2 text-xs text-abu">{ket}</p>
      {isi.length < 3 ? (
        <p className="mt-4 text-sm text-abu">{kosong}</p>
      ) : (
        <ol className="mt-4 space-y-2">
          {isi.map((w, i) => (
            <li key={w.teks} className="grid grid-cols-[1.5rem_1fr_auto] items-center gap-2 text-sm">
              <span className="font-mono text-xs text-abu">{i + 1}</span>
              <span className="relative">
                <span className="absolute inset-y-0 left-0 rounded-sm opacity-15" style={{ width: `${((w.porsi / puncak) * 100).toFixed(1)}%`, background: CLASS_HEX[label] }} aria-hidden />
                <span className="relative px-1.5 font-semibold">{w.teks}</span>
              </span>
              <span className="text-right font-mono text-xs text-abu">{nf.format(w.ulasan)} ulasan</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
