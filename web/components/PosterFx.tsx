"use client";

import { useEffect } from "react";

// Titik sorot kartu .poster mengikuti kursor. Satu listener untuk seluruh halaman, hanya untuk mouse.
export default function PosterFx() {
  useEffect(() => {
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    let raf = 0;
    let last: PointerEvent | null = null;
    const apply = () => {
      raf = 0;
      const el = last?.target instanceof Element ? (last.target.closest(".poster") as HTMLElement | null) : null;
      if (!el || !last) return;
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", `${Math.round(last.clientX - r.left)}px`);
      el.style.setProperty("--my", `${Math.round(last.clientY - r.top)}px`);
    };
    const onMove = (e: PointerEvent) => {
      last = e;
      if (!raf) raf = requestAnimationFrame(apply);
    };
    document.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      document.removeEventListener("pointermove", onMove);
      cancelAnimationFrame(raf);
    };
  }, []);
  return null;
}
