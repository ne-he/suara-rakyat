"use client";

import { useState, type ReactNode, type RefObject } from "react";
import { downloadPng, downloadSvg } from "@/lib/download";

/** Tombol unduh PNG/SVG untuk satu grafik, plus tabel pengganti yang bisa dibuka. */
export function ChartFooter({
  svgRef,
  filename,
  table,
}: {
  svgRef: RefObject<SVGSVGElement | null>;
  filename: string;
  table: ReactNode;
}) {
  const [busy, setBusy] = useState(false);
  return (
    <div className="mt-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <button
          type="button"
          disabled={busy}
          onClick={async () => {
            if (!svgRef.current) return;
            setBusy(true);
            try {
              await downloadPng(svgRef.current, `${filename}.png`);
            } finally {
              setBusy(false);
            }
          }}
          className="rounded-full border border-aspal/40 bg-white px-3 py-1 transition hover:-translate-y-0.5 hover:border-aspal disabled:opacity-50"
        >
          Unduh PNG
        </button>
        <button
          type="button"
          onClick={() => svgRef.current && downloadSvg(svgRef.current, `${filename}.svg`)}
          className="rounded-full border border-aspal/40 bg-white px-3 py-1 transition hover:-translate-y-0.5 hover:border-aspal"
        >
          Unduh SVG
        </button>
      </div>
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer text-xs text-abu hover:text-aspal">Lihat sebagai tabel</summary>
        <div className="mt-2 max-h-72 overflow-auto rounded-lg border border-garis bg-white">{table}</div>
      </details>
    </div>
  );
}

export function Tooltip({ x, y, width, children }: { x: number; y: number; width: number; children: ReactNode }) {
  const left = Math.min(Math.max(x, 90), width - 90);
  return (
    <div
      className="pointer-events-none absolute z-10 w-44 -translate-x-1/2 -translate-y-full rounded-lg border-2 border-aspal bg-white px-3 py-2 text-xs shadow-[3px_3px_0_var(--aspal)]"
      style={{ left, top: y - 10 }}
      role="status"
    >
      {children}
    </div>
  );
}

export const TABLE_CLASS = "w-full text-left text-xs [&_td]:px-3 [&_td]:py-1.5 [&_th]:px-3 [&_th]:py-2 [&_thead]:sticky [&_thead]:top-0 [&_thead]:bg-kertas [&_tr]:border-b [&_tr]:border-garis";
