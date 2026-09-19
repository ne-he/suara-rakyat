"use client";

import { useEffect, useRef, useState } from "react";
import { APP_NAME, CLASS_HEX, type Label } from "@/lib/fmt";

export type TickerItem = { text: string; label: Label; app: string; stars: number };

// Pita ulasan asli yang berjalan pelan. Daftar digandakan supaya putarannya menyambung tanpa jeda.
// Animasi dimatikan saat pita keluar layar, kalau tidak scroll cerita di atasnya ikut tersendat.
export default function SuaraTicker({ items }: { items: TickerItem[] }) {
  const ref = useRef<HTMLElement>(null);
  const [tampak, setTampak] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver((entries) => setTampak(entries[0].isIntersecting), { rootMargin: "120px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const row = (hidden: boolean) =>
    items.map((it, i) => (
      <li key={`${hidden ? "b" : "a"}${i}`} aria-hidden={hidden || undefined} className="flex shrink-0 items-center gap-3 px-6">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: CLASS_HEX[it.label] }} aria-hidden />
        <span className="font-mono text-[11px] uppercase tracking-wider text-putih/60">
          {APP_NAME[it.app] ?? it.app} · {"★".repeat(it.stars)}
          <span className="text-putih/25">{"★".repeat(5 - it.stars)}</span>
          <span className="sr-only"> bintang {it.stars}</span>
        </span>
        <span className="whitespace-nowrap text-sm text-putih/90">&ldquo;{it.text}&rdquo;</span>
      </li>
    ));

  return (
    <section
      ref={ref}
      aria-label="Contoh ulasan asli dari dataset"
      className="pita group relative overflow-hidden border-y-2 border-aspal bg-aspal py-3 [contain:layout_paint]"
    >
      <ul className={`flex w-max ${tampak ? "pita-jalan" : ""}`}>
        {row(false)}
        {row(true)}
      </ul>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-aspal" aria-hidden />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-aspal" aria-hidden />
    </section>
  );
}
