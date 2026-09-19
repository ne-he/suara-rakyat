import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import SiteHeader, { SiteFooter } from "@/components/SiteHeader";
import SusForm from "@/components/SusForm";
import type { ModelMeta } from "@/lib/model";

export const metadata: Metadata = {
  title: "Kuesioner SUS · Suara Rakyat",
  description: "Kuesioner System Usability Scale untuk menilai web Suara Rakyat, plus alat rekap jawaban tim.",
};

export default function Kuesioner() {
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  return (
    <>
      <SiteHeader active="/kuesioner" />
      <main className="px-5 py-12 sm:px-10 sm:py-16">
        <div className="mx-auto max-w-5xl">
          <p className="kicker text-merah">Evaluasi pengguna</p>
          <h1 className="display mt-3 text-6xl sm:text-8xl">
            Menurutmu
            <br />
            <span className="text-merah">web ini gimana?</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-aspal-2">
            Sepuluh pernyataan System Usability Scale (Brooke, 1996), diterjemahkan tim. Isinya cepat, sekitar dua menit. Jawaban dihitung di
            browsermu dan tidak dikirim ke mana pun.
          </p>
          <div className="mt-10">
            <SusForm />
          </div>
          <p className="mt-10 max-w-3xl text-xs text-abu">
            Rumus skor: pernyataan ganjil dihitung nilai dikurangi 1, pernyataan genap dihitung 5 dikurangi nilai, semuanya dijumlahkan lalu dikali
            2,5. Hasilnya 0 sampai 100. Patokan rata-rata 68 yang dipakai di sini berasal dari rangkuman studi SUS dan perlu dicek lagi sumbernya
            sebelum masuk laporan.
          </p>
        </div>
      </main>
      <SiteFooter version={meta.version} />
    </>
  );
}
