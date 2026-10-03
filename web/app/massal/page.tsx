import type { Metadata } from "next";
import BatchAnalyzer from "@/components/BatchAnalyzer";
import SiteHeader, { SiteFooter } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Cek banyak ulasan · Suara Rakyat",
  description: "Tempel atau unggah sampai 1.000 ulasan sekaligus, lihat porsi negatif, netral, positif, dan kata keluhan yang paling sering muncul.",
};

export default function Massal() {
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
            Cocok untuk yang punya banyak ulasan, misalnya pengelola layanan atau peneliti. Tempel ulasan satu per baris atau unggah file CSV. Web
            menghitung porsi nadanya, menandai kata keluhan yang paling sering muncul, lalu menyiapkan file hasil untuk diunduh.
          </p>
          <ol className="mt-6 grid gap-3 text-sm sm:grid-cols-3">
            {["Masukkan ulasan: tempel teks, unggah CSV, atau pakai 200 ulasan contoh.", "Tekan Baca semua.", "Lihat ringkasannya, saring per nada, lalu unduh hasil CSV."].map(
              (t, i) => (
                <li key={t} className="flex gap-3 rounded-xl border-2 border-aspal/20 bg-white/60 p-3">
                  <span className="display text-3xl text-merah">{i + 1}</span>
                  <span className="text-aspal-2">{t}</span>
                </li>
              ),
            )}
          </ol>
          <div className="mt-10">
            <BatchAnalyzer />
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
