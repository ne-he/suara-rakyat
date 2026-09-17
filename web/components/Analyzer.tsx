"use client";

import { useRef, useState } from "react";

type Label = "negative" | "neutral" | "positive";
type Result = {
  label: Label;
  probs: Record<Label, number>;
  tokens: { token: string; weight: number }[];
  empty: boolean;
  ms: number;
};

const LABEL_ID: Record<Label, string> = {
  negative: "Negatif",
  neutral: "Netral",
  positive: "Positif",
};

const COLOR: Record<Label, string> = {
  negative: "var(--neg)",
  neutral: "var(--neu)",
  positive: "var(--pos)",
};

const SAMPLES = [
  { app: "Mobile JKN", text: "Sudah 3 hari tidak bisa login, kode OTP tidak pernah masuk. Tolong diperbaiki." },
  { app: "KAI Access", text: "Pesan tiket mudik jadi gampang banget, tidak perlu antre di stasiun. Mantap!" },
  { app: "SatuSehat", text: "Aplikasinya lumayan, tapi sertifikat vaksin kadang lama munculnya." },
  { app: "MyPertamina", text: "ribet bgt harus scan QR segala, sinyal di SPBU aja susah" },
  { app: "JMO", text: "Cek saldo JHT sekarang cepat, tampilan juga lebih rapi dari versi lama." },
];

const MAX = 2000;

export default function Analyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stampKey, setStampKey] = useState(0);
  const areaRef = useRef<HTMLTextAreaElement>(null);

  async function analyze(value = text) {
    if (!value.trim()) {
      setError("Tulis atau tempel ulasannya dulu.");
      areaRef.current?.focus();
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Gagal membaca ulasan.");
      setResult(data as Result);
      setStampKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal membaca ulasan.");
    } finally {
      setLoading(false);
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

  return (
    <div className="relative">
      <div className="rounded-[18px] border border-ink/80 bg-card shadow-[6px_6px_0_0_var(--ink)]">
        <div className="flex items-center justify-between border-b border-ink/80 px-5 py-3 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-2">
          <span>Formulir baca ulasan</span>
          <span aria-hidden>No. {String(stampKey + 1).padStart(4, "0")}</span>
        </div>

        <form
          className="p-5"
          onSubmit={(e) => {
            e.preventDefault();
            analyze();
          }}
        >
          <label htmlFor="review" className="mb-2 block font-mono text-[11px] uppercase tracking-[0.14em] text-muted">
            Isi ulasan
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
            placeholder="Contoh: aplikasinya sering error pas mau daftar antrean, tolong diperbaiki"
            className="rule w-full resize-y rounded-lg border border-line bg-transparent px-3 py-2 text-[17px] leading-8 text-ink outline-none placeholder:text-muted/70 focus:border-ink"
          />
          <div className="mt-1 flex items-center justify-between text-xs text-muted">
            <span>{error ? <span className="font-medium text-neg">{error}</span> : "Ctrl + Enter untuk kirim"}</span>
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
                className="rounded-full border border-line bg-paper px-3 py-1.5 text-xs text-ink-2 transition hover:border-ink hover:text-ink"
              >
                Contoh {s.app}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-5 py-3.5 font-display text-lg font-bold text-paper transition hover:bg-signal disabled:opacity-60"
          >
            {loading ? "Membaca..." : "Baca nadanya"}
          </button>
        </form>
      </div>

      <div aria-live="polite">
        {result && (
          <section className="rise mt-6 rounded-[18px] border border-line bg-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">Hasil</p>
                <p className="mt-1 text-sm text-ink-2">
                  Keyakinan model {Math.round(result.probs[result.label] * 100)}%
                  <span className="text-muted"> · {result.ms} ms</span>
                </p>
              </div>
              <div
                key={stampKey}
                className="stamp select-none rounded-md border-[3px] px-4 py-1.5 font-display text-3xl font-extrabold uppercase tracking-wide"
                style={{ color: COLOR[result.label], borderColor: COLOR[result.label] }}
              >
                {LABEL_ID[result.label]}
              </div>
            </div>

            <div className="mt-5 space-y-2.5">
              {(Object.keys(LABEL_ID) as Label[]).map((l) => (
                <div key={l} className="grid grid-cols-[72px_1fr_48px] items-center gap-3 text-sm">
                  <span className="text-ink-2">{LABEL_ID[l]}</span>
                  <div className="h-3 overflow-hidden rounded-full bg-paper-2">
                    <div
                      className="bar-fill h-full rounded-full"
                      style={{ width: `${(result.probs[l] * 100).toFixed(1)}%`, background: COLOR[l] }}
                    />
                  </div>
                  <span className="text-right font-mono text-xs">{(result.probs[l] * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>

            {result.empty ? (
              <p className="mt-5 rounded-lg bg-paper-2 p-3 text-sm text-ink-2">
                Tidak ada kata yang dikenali model, jadi hasil ini cuma tebakan dari pola umum. Coba tulis ulasan yang lebih lengkap.
              </p>
            ) : (
              <div className="mt-6">
                <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">
                  Kata yang dibaca model (setelah dinormalisasi)
                </p>
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
                          background: toward
                            ? `color-mix(in srgb, ${COLOR[result.label]} ${Math.round(strength * 32)}%, transparent)`
                            : "transparent",
                          textDecoration: !toward && strength > 0.25 ? "line-through" : undefined,
                          textDecorationColor: "var(--muted)",
                          color: strength > 0.05 ? "var(--ink)" : "var(--muted)",
                        }}
                      >
                        {t.token}
                      </span>
                    );
                  })}
                </p>
                {topDrivers.length > 0 && (
                  <p className="mt-4 text-sm text-ink-2">
                    Paling mendorong ke <b style={{ color: COLOR[result.label] }}>{LABEL_ID[result.label].toLowerCase()}</b>:{" "}
                    {topDrivers.map((t) => `"${t.token}"`).join(", ")}
                  </p>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
