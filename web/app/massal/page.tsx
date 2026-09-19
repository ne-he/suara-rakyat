import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import BatchAnalyzer from "@/components/BatchAnalyzer";
import SiteHeader, { SiteFooter } from "@/components/SiteHeader";
import type { ModelMeta } from "@/lib/model";

export const metadata: Metadata = {
  title: "Cek banyak ulasan · Suara Rakyat",
  description: "Tempel atau unggah sampai 1.000 ulasan sekaligus, lihat porsi negatif, netral, positif, dan kata keluhan yang paling sering muncul.",
};

export default function Massal() {
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  return (
    <>
      <SiteHeader active="/massal" />
      <main className="px-5 py-12 sm:px-10 sm:py-16">
        <div className="mx-auto max-w-5xl">
          <p className="kicker text-merah">Cek massal</p>
          <h1 className="display mt-3 text-6xl sm:text-8xl">
            Seribu suara,
            <br />
            <span className="text-merah">sekali baca.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-aspal-2">
            Tempel ulasan satu per baris atau unggah file CSV. Web akan menghitung porsi nadanya, menandai kata yang paling sering mendorong ke
            negatif, lalu menyiapkan file hasil untuk diunduh.
          </p>
          <div className="mt-10">
            <BatchAnalyzer models={meta.models.map((m) => ({ id: m.id, name: m.name }))} defaultId={meta.default_model} />
          </div>
        </div>
      </main>
      <SiteFooter version={meta.version} />
    </>
  );
}
