"use client";

import { useRef, useState } from "react";
import { unduhKartu } from "@/lib/kartu";

type Label = "negative" | "neutral" | "positive";
type Hasil = {
  label: Label;
  probs: Record<Label, number>;
  tokens: { token: string; weight: number }[];
  empty: boolean;
};

const LABEL_ID: Record<Label, string> = { negative: "Negatif", neutral: "Netral", positive: "Positif" };
const COLOR: Record<Label, string> = { negative: "var(--neg)", neutral: "var(--neu)", positive: "var(--pos)" };
const ARTI: Record<Label, string> = {
  negative: "Ulasan ini terbaca sebagai keluhan atau rasa kecewa.",
  neutral: "Ulasan ini terbaca biasa saja: campuran pujian dan keluhan, pertanyaan, atau saran.",
  positive: "Ulasan ini terbaca sebagai pujian atau rasa puas.",
};

const SAMPLES = [
  { app: "Mobile JKN", text: "Sudah 3 hari tidak bisa login, kode OTP tidak pernah masuk. Tolong diperbaiki." },
  { app: "KAI Access", text: "Pesan tiket mudik jadi gampang banget, tidak perlu antre di stasiun. Mantap!" },
  { app: "SatuSehat", text: "Aplikasinya lumayan, tapi sertifikat vaksin kadang lama munculnya." },
  { app: "MyPertamina", text: "ribet bgt harus scan QR segala, sinyal di SPBU aja susah" },
  { app: "JMO", text: "Cek saldo JHT sekarang cepat, tampilan juga lebih rapi dari versi lama." },
];

const MAX = 2000;

function yakin(p: number): { kata: string; catatan?: string } {
  if (p >= 0.8) return { kata: "Mesin yakin" };
  if (p >= 0.6) return { kata: "Mesin cukup yakin" };
  return { kata: "Mesin ragu-ragu", catatan: "Ulasan campuran, sindiran, atau ulasan yang sangat pendek sering terbaca kurang tepat. Coba tulis lebih jelas." };
}

export default function Analyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<Hasil | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stampKey, setStampKey] = useState(0);
  const [sertakanTeks, setSertakanTeks] = useState(true);
  const [dikirim, setDikirim] = useState("");
  const areaRef = useRef<HTMLTextAreaElement>(null);
  const jalan = useRef(0);

  async function analyze(value = text) {
    if (!value.trim()) {
      setError("Tulis atau tempel ulasanmu dulu.");
      areaRef.current?.focus();
      return;
    }
    const tiket = ++jalan.current;
    setLoading(true);
    setError(null);
    setDikirim(value);
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Gagal membaca ulasan.");
      if (tiket !== jalan.current) return;
      setResult(json as Hasil);
      setStampKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal membaca ulasan.");
    } finally {
      if (tiket === jalan.current) setLoading(false);
    }
  }

  const maxAbs = result ? Math.max(1e-9, ...result.tokens.map((t) => Math.abs(t.weight))) : 1;
  const topDrivers = result
    ? [...result.tokens]
        .filter((t) => t.weight > 0)
        .sort((a, b) => b.weight - a.weight)
        .filter((t, i, arr) => arr.findIndex((x) => x.token === t.token) === i)
        .slice(0, 4)
    : [];
  const p = result ? result.probs[result.label] : 0;
  const y = yakin(p);

  return (
    <div className="grid gap-8 lg:grid-cols-[1.05fr_1fr]">
      <form
        className="karton self-start rounded-sm p-5 sm:p-6"
        onSubmit={(e) => {
          e.preventDefault();
          analyze();
        }}
      >
        <label htmlFor="review" className="kicker block text-aspal">
          Tulis atau tempel ulasan
        </label>
        <textarea
          id="review"
          ref={areaRef}
          value={text}
          maxLength={MAX}
          rows={5}
          onChange={(e) => {
            setText(e.target.value);
            if (error) setError(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) analyze();
          }}
          placeholder="contoh: aplikasinya sering error pas mau daftar antrean, tolong diperbaiki"
          className="marker mt-3 w-full resize-y rounded-sm border-2 border-aspal/70 bg-white/70 px-3 py-2 text-[19px] leading-8 text-aspal outline-none placeholder:text-aspal/40 focus:border-aspal focus:bg-white"
        />
        <div className="mt-1 flex items-center justify-between text-xs text-aspal/70">
          <span>{error ? <span role="alert" className="font-semibold text-neg">{error}</span> : "Boleh pakai singkatan dan bahasa sehari-hari."}</span>
          <span className="font-mono">
            {text.length}/{MAX}
          </span>
        </div>
        <p className="mt-4 text-xs text-aspal/70">Belum ada ide? Klik salah satu contoh:</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s.app}
              type="button"
              onClick={() => {
                setText(s.text);
                analyze(s.text);
              }}
              className="rounded-full border border-aspal/40 bg-putih/80 px-3 py-1.5 text-xs text-aspal transition duration-300 hover:-translate-y-0.5 hover:border-aspal hover:bg-putih hover:shadow-[2px_2px_0_var(--aspal)]"
            >
              Contoh {s.app}
            </button>
          ))}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="display mt-5 w-full rounded-sm bg-merah px-5 py-3.5 text-3xl text-putih shadow-[4px_4px_0_var(--aspal)] transition hover:bg-merah-tua active:translate-x-[2px] active:translate-y-[2px] active:shadow-[2px_2px_0_var(--aspal)] disabled:opacity-60"
        >
          {loading ? "Membaca..." : "Baca nadanya"}
        </button>
        <p className="mt-2 text-center text-xs text-aspal/60">atau tekan Ctrl + Enter</p>
      </form>

      <div aria-live="polite">
        {!result && (
          <div className="flex h-full min-h-64 flex-col justify-center rounded-xl border-2 border-dashed border-aspal/25 p-6 text-center">
            <p className="display text-4xl text-aspal/30">Hasil muncul di sini</p>
            <p className="mt-2 text-sm text-abu">Tulis ulasan lalu tekan Baca nadanya.</p>
          </div>
        )}
        {result?.empty && (
          <section className="rise rounded-xl border-2 border-dashed border-aspal/40 bg-white p-6" aria-label="Hasil baca" data-hasil="kosong">
            <p className="display text-4xl text-abu">Tidak terbaca</p>
            <p className="mt-3 text-sm leading-relaxed text-aspal-2">
              Tidak ada kata yang dikenali, jadi nadanya tidak ditebak. Coba tulis ulasan dalam bahasa Indonesia yang lebih lengkap, misalnya apa yang
              terjadi saat memakai aplikasinya.
            </p>
          </section>
        )}
        {result && !result.empty && (
          <section className="rise rounded-xl border-2 border-aspal bg-white p-5 shadow-[6px_6px_0_var(--aspal)]" aria-label="Hasil baca">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="max-w-[16rem]">
                <p className="kicker text-abu">Nada ulasan</p>
                <p className="mt-1 text-sm leading-snug text-aspal-2">{ARTI[result.label]}</p>
              </div>
              <div
                key={stampKey}
                data-hasil={result.label}
                className="stamp display select-none rounded-sm border-[3px] px-4 pb-1 pt-1.5 text-4xl"
                style={{ color: COLOR[result.label], borderColor: COLOR[result.label] }}
              >
                {LABEL_ID[result.label]}
              </div>
            </div>

            <p className="mt-4 text-sm">
              <b>{y.kata}</b> <span className="text-abu">({Math.round(p * 100)}%)</span>
            </p>
            {y.catatan && <p className="mt-1 rounded-lg bg-kertas p-2.5 text-xs text-aspal-2">{y.catatan}</p>}

            <div className="mt-4 space-y-2.5">
              {(Object.keys(LABEL_ID) as Label[]).map((l) => (
                <div key={l} className="grid grid-cols-[72px_1fr_52px] items-center gap-3 text-sm">
                  <span className="text-aspal-2">{LABEL_ID[l]}</span>
                  <div className="h-3 overflow-hidden rounded-full bg-kertas">
                    <div className="bar-fill h-full rounded-full" style={{ width: `${(result.probs[l] * 100).toFixed(1)}%`, background: COLOR[l] }} />
                  </div>
                  <span className="text-right font-mono text-xs">{(result.probs[l] * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>

            <div className="mt-6">
              <p className="kicker text-abu">Kata yang menentukan hasil</p>
              <p className="mt-1 text-xs text-abu">Makin tebal warnanya, makin besar pengaruhnya. Kata yang dicoret menahan hasil ini.</p>
              <p className="mt-2 flex flex-wrap gap-x-1.5 gap-y-2 text-[15px] leading-7" data-kata>
                {result.tokens.map((t, i) => {
                  const strength = Math.min(1, Math.abs(t.weight) / maxAbs);
                  const toward = t.weight > 0;
                  return (
                    <span
                      key={i}
                      title={toward ? `Mendorong ke ${LABEL_ID[result.label]}` : `Menahan ${LABEL_ID[result.label]}`}
                      className="rounded px-1"
                      style={{
                        background: toward ? `color-mix(in srgb, ${COLOR[result.label]} ${Math.round(strength * 34)}%, transparent)` : "transparent",
                        textDecoration: !toward && strength > 0.25 ? "line-through" : undefined,
                        color: strength > 0.05 ? "var(--aspal)" : "var(--abu)",
                      }}
                    >
                      {t.token}
                    </span>
                  );
                })}
              </p>
              {topDrivers.length > 0 && (
                <p className="mt-4 text-sm text-aspal-2">
                  Paling mendorong ke <b style={{ color: COLOR[result.label] }}>{LABEL_ID[result.label].toLowerCase()}</b>:{" "}
                  {topDrivers.map((t) => `"${t.token}"`).join(", ")}
                </p>
              )}
              <p className="mt-2 text-xs text-abu">Singkatan seperti gk, bgt, udh sudah diubah ke bentuk bakunya sebelum dibaca.</p>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3 border-t-2 border-dashed border-aspal/20 pt-4">
              <button
                type="button"
                onClick={() =>
                  unduhKartu({
                    label: result.label,
                    probs: result.probs,
                    text: sertakanTeks ? dikirim : undefined,
                    drivers: topDrivers.map((t) => t.token),
                  })
                }
                className="rounded-sm bg-aspal px-4 py-2 text-sm text-putih shadow-[3px_3px_0_var(--merah)] transition hover:-translate-y-0.5"
              >
                Unduh kartu hasil
              </button>
              <label className="flex items-center gap-2 text-xs text-abu">
                <input type="checkbox" checked={sertakanTeks} onChange={(e) => setSertakanTeks(e.target.checked)} className="h-4 w-4 accent-[var(--merah)]" />
                sertakan teks ulasan di kartu
              </label>
            </div>
            <p className="mt-4 text-xs text-abu">Ini tebakan mesin, bukan penilaian resmi. Sindiran dan ulasan campuran paling sering keliru.</p>
          </section>
        )}
      </div>
    </div>
  );
}
