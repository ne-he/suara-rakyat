"use client";

import { useRef, useState } from "react";
import { unduhKartu } from "@/lib/kartu";

type Label = "negative" | "neutral" | "positive";
type Prediction = {
  model: string;
  label: Label;
  probs: Record<Label, number>;
  tokens: { token: string; weight: number }[];
  empty: boolean;
  explained?: boolean;
};
type ApiResult = { default: string; results: Record<string, Prediction>; ms: number };

export type ModelCard = {
  id: string;
  name: string;
  features: string;
  tagline: string;
  macroF1: number;
  accuracy: number;
  remote?: boolean;
};

const LABEL_ID: Record<Label, string> = { negative: "Negatif", neutral: "Netral", positive: "Positif" };
const COLOR: Record<Label, string> = { negative: "var(--neg)", neutral: "var(--neu)", positive: "var(--pos)" };

const SAMPLES = [
  { app: "Mobile JKN", text: "Sudah 3 hari tidak bisa login, kode OTP tidak pernah masuk. Tolong diperbaiki." },
  { app: "KAI Access", text: "Pesan tiket mudik jadi gampang banget, tidak perlu antre di stasiun. Mantap!" },
  { app: "SatuSehat", text: "Aplikasinya lumayan, tapi sertifikat vaksin kadang lama munculnya." },
  { app: "MyPertamina", text: "ribet bgt harus scan QR segala, sinyal di SPBU aja susah" },
  { app: "JMO", text: "Cek saldo JHT sekarang cepat, tampilan juga lebih rapi dari versi lama." },
];

const MAX = 2000;
const dec = (x: number) => x.toFixed(3).replace(".", ",");

export default function Analyzer({ models, defaultId, remote }: { models: ModelCard[]; defaultId: string; remote?: ModelCard }) {
  const all = remote ? [...models, remote] : models;
  const [text, setText] = useState("");
  const [selected, setSelected] = useState(defaultId);
  const [data, setData] = useState<ApiResult | null>(null);
  const [jauh, setJauh] = useState<{ state: "idle" | "loading" | "ok" | "error"; result?: Prediction; error?: string }>({ state: "idle" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stampKey, setStampKey] = useState(0);
  const [sertakanTeks, setSertakanTeks] = useState(true);
  const [dikirim, setDikirim] = useState("");
  const areaRef = useRef<HTMLTextAreaElement>(null);
  const jalan = useRef(0);

  async function analyze(value = text) {
    if (!value.trim()) {
      setError("Tulis atau tempel suaramu dulu.");
      areaRef.current?.focus();
      return;
    }
    const tiket = ++jalan.current;
    setLoading(true);
    setError(null);
    setDikirim(value);
    if (remote) {
      setJauh({ state: "loading" });
      // model besar dipanggil terpisah supaya tiga model cepat tetap tampil duluan
      fetch("/api/predict-indobert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      })
        .then(async (res) => {
          const json = await res.json();
          if (tiket !== jalan.current) return;
          if (!res.ok) setJauh({ state: "error", error: json.error ?? "Server IndoBERT tidak menjawab." });
          else setJauh({ state: "ok", result: { ...json, model: remote.id } as Prediction });
        })
        .catch(() => tiket === jalan.current && setJauh({ state: "error", error: "Server IndoBERT tidak bisa dihubungi." }));
    }
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Gagal membaca ulasan.");
      if (tiket !== jalan.current) return;
      setData(json as ApiResult);
      setStampKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal membaca ulasan.");
    } finally {
      setLoading(false);
    }
  }

  function pick(id: string) {
    setSelected(id);
    if (data) setStampKey((k) => k + 1);
  }

  const hasil: Record<string, Prediction> = { ...(data?.results ?? {}), ...(jauh.state === "ok" && jauh.result ? { [remote!.id]: jauh.result } : {}) };
  const result = hasil[selected] ?? null;
  const menungguJauh = remote?.id === selected && jauh.state === "loading";
  const gagalJauh = remote?.id === selected && jauh.state === "error";
  const maxAbs = result ? Math.max(1e-9, ...result.tokens.map((t) => Math.abs(t.weight))) : 1;
  const topDrivers = result
    ? [...result.tokens]
        .filter((t) => t.weight > 0)
        .sort((a, b) => b.weight - a.weight)
        .filter((t, i, arr) => arr.findIndex((x) => x.token === t.token) === i)
        .slice(0, 4)
    : [];
  const labels = Object.values(hasil).map((r) => r.label);
  const agree = labels.length > 1 && new Set(labels).size === 1;

  return (
    <div className="grid gap-8 lg:grid-cols-[1.05fr_1fr]">
      <div>
        <fieldset>
          <legend className="kicker text-abu">1. Pilih model pembaca</legend>
          <div className={`mt-3 grid gap-3 ${remote ? "sm:grid-cols-2" : "sm:grid-cols-3"}`}>
            {all.map((m, i) => {
              const on = m.id === selected;
              return (
                <label
                  key={m.id}
                  className={`poster cursor-pointer rounded-xl border-2 p-4 ${
                    on ? "border-aspal bg-aspal text-putih shadow-[4px_4px_0_var(--merah)]" : "border-aspal/25 bg-white hover:border-aspal"
                  }`}
                >
                  <input type="radio" name="model" value={m.id} checked={on} onChange={() => pick(m.id)} className="sr-only" />
                  {(i === 0 || m.remote) && (
                    <span className="absolute -top-2.5 right-3 rounded-full bg-merah px-2 py-0.5 font-mono text-[10px] uppercase text-putih">
                      {m.remote ? "server terpisah" : "terbaik di web"}
                    </span>
                  )}
                  <span className="display block text-2xl">
                    <span className="angka">{m.name}</span>
                  </span>
                  <span className={`mt-1 block text-xs ${on ? "text-putih/70" : "text-abu"}`}>fitur {m.features}</span>
                  <span className={`mt-3 block text-sm leading-snug ${on ? "text-putih/90" : "text-aspal-2"}`}>{m.tagline}</span>
                  <span className="mt-3 flex gap-4 font-mono text-xs">
                    <span>F1 {dec(m.macroF1)}</span>
                    <span>akurasi {(m.accuracy * 100).toFixed(1).replace(".", ",")}%</span>
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <form
          className="karton mt-8 rounded-sm p-5 sm:p-6"
          onSubmit={(e) => {
            e.preventDefault();
            analyze();
          }}
        >
          <label htmlFor="review" className="kicker block text-aspal">
            2. Tulis suaramu
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
            <span>{error ? <span className="font-semibold text-neg">{error}</span> : "Ctrl + Enter untuk kirim"}</span>
            <span className="font-mono">
              {text.length}/{MAX}
            </span>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
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
            {loading ? "Membaca..." : "Suarakan"}
          </button>
        </form>
      </div>

      <div aria-live="polite" className="lg:pt-8">
        {!result && !menungguJauh && !gagalJauh && (
          <div className="flex h-full min-h-64 flex-col justify-center rounded-xl border-2 border-dashed border-aspal/25 p-6 text-center">
            <p className="display text-4xl text-aspal/30">Hasil muncul di sini</p>
            <p className="mt-2 text-sm text-abu">Pilih model, tulis ulasan, lalu tekan Suarakan.</p>
          </div>
        )}
        {(menungguJauh || gagalJauh) && (
          <div className="mb-4 rounded-xl border-2 border-dashed border-aspal/40 bg-putih p-5">
            <p className="kicker text-abu">{remote?.name}</p>
            <p className="mt-2 text-sm text-aspal-2">
              {menungguJauh
                ? "Sedang dibaca di server terpisah. Kalau servernya baru bangun, ini bisa sampai satu menit."
                : `${jauh.error} Model lain di atas tetap bisa dipakai.`}
            </p>
            {menungguJauh && <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-kertas"><div className="jalan h-full w-1/3 rounded-full bg-merah" /></div>}
          </div>
        )}
        {result && (
          <section className="rise rounded-xl border-2 border-aspal bg-white p-5 shadow-[6px_6px_0_var(--aspal)]">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="kicker text-abu">Dibaca oleh {all.find((m) => m.id === selected)?.name}</p>
                <p className="mt-1 text-sm text-aspal-2">
                  Keyakinan {Math.round(result.probs[result.label] * 100)}%
                  {data && <span className="text-abu"> · {models.length} model cepat dalam {data.ms} ms</span>}
                </p>
              </div>
              <div
                key={stampKey}
                className="stamp display select-none rounded-sm border-[3px] px-4 pb-1 pt-1.5 text-4xl"
                style={{ color: COLOR[result.label], borderColor: COLOR[result.label] }}
              >
                {LABEL_ID[result.label]}
              </div>
            </div>

            <div className="mt-5 space-y-2.5">
              {(Object.keys(LABEL_ID) as Label[]).map((l) => (
                <div key={l} className="grid grid-cols-[72px_1fr_52px] items-center gap-3 text-sm">
                  <span className="text-aspal-2">{LABEL_ID[l]}</span>
                  <div className="h-3 overflow-hidden rounded-full bg-kertas">
                    <div className="bar-fill h-full rounded-full" style={{ width: `${(result.probs[l] * 100).toFixed(1)}%`, background: COLOR[l] }} />
                  </div>
                  <span className="text-right font-mono text-xs">{(result.probs[l] * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>

            {result.empty ? (
              <p className="mt-5 rounded-lg bg-kertas p-3 text-sm text-aspal-2">
                Tidak ada kata yang dikenali model, jadi hasil ini cuma tebakan dari pola umum. Coba tulis ulasan yang lebih lengkap.
              </p>
            ) : (
              <div className="mt-6">
                <p className="kicker text-abu">Kata yang dibaca model (setelah dinormalisasi)</p>
                <p className="mt-2 flex flex-wrap gap-x-1.5 gap-y-2 text-[15px] leading-7">
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
                {result.explained === false && <p className="mt-2 text-xs text-abu">Ulasan ini terlalu panjang untuk dihitung kata penentunya di server.</p>}
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center gap-3 border-t-2 border-dashed border-aspal/20 pt-4">
              <button
                type="button"
                onClick={() =>
                  unduhKartu({
                    label: result.label,
                    probs: result.probs,
                    modelName: all.find((m) => m.id === selected)?.name ?? selected,
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

            <div className="mt-4 border-t-2 border-dashed border-aspal/20 pt-4">
              <p className="kicker text-abu">{agree ? "Semua model sepakat" : "Model tidak sepakat"}</p>
              <div className={`mt-3 grid gap-2 ${all.length > 3 ? "grid-cols-2" : "grid-cols-3"}`}>
                {all.map((m) => {
                  const r = hasil[m.id];
                  const on = m.id === selected;
                  const nunggu = m.remote && jauh.state === "loading";
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => pick(m.id)}
                      className={`rounded-lg border-2 p-2.5 text-left transition duration-300 hover:-translate-y-0.5 ${on ? "border-aspal bg-kertas" : "border-transparent bg-kertas/60 hover:border-aspal/40"}`}
                    >
                      <span className="block truncate text-[11px] text-abu">{m.name}</span>
                      <span className="display block text-xl" style={{ color: r ? COLOR[r.label] : "var(--abu)" }}>
                        {r ? LABEL_ID[r.label] : nunggu ? "menunggu" : "tidak ada"}
                      </span>
                      <span className="font-mono text-[11px]">{r ? `${Math.round(r.probs[r.label] * 100)}%` : ""}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
