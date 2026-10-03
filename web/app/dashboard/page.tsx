import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import Link from "next/link";
import DashboardAplikasi, { type DataAplikasi } from "@/components/DashboardAplikasi";
import SiteHeader, { SiteFooter } from "@/components/SiteHeader";
import type { TrendData } from "@/components/TrendChart";
import { nf } from "@/lib/fmt";

export const metadata: Metadata = {
  title: "Dashboard aplikasi · Suara Rakyat",
  description: "Ringkasan ulasan warga untuk enam aplikasi layanan publik: porsi keluhan, hal yang paling sering dikeluhkan dan dipuji, dan tren per kuartal.",
};

// path ditulis lengkap (bukan dari variabel) supaya Turbopack tidak ikut menyertakan seluruh proyek
export default function Dashboard() {
  const data = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "aplikasi.json"), "utf8")) as DataAplikasi;
  const extrasFile = path.join(process.cwd(), "data", "extras.json");
  const trend = fs.existsSync(extrasFile) ? (JSON.parse(fs.readFileSync(extrasFile, "utf8")) as { trend: TrendData }).trend : null;

  return (
    <>
      <SiteHeader active="/dashboard" />
      <main className="px-5 py-12 sm:px-10 sm:py-16">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Dashboard aplikasi</p>
          <h1 className="display mt-3 text-6xl sm:text-8xl">
            Enam aplikasi,
            <br />
            <span className="text-merah">satu papan keluhan.</span>
          </h1>
          <p className="mt-5 max-w-3xl text-lg text-aspal-2">
            Ringkasan {nf.format(data.ulasan)} ulasan warga di Google Play, ditulis antara {data.mulai.slice(0, 4)} dan {data.akhir.slice(0, 4)}. Nada di
            halaman ini dihitung dari bintang yang diberikan penulisnya, jadi bukan tebakan mesin.
          </p>
          <div className="karton mt-6 max-w-3xl rounded-sm p-4 text-sm leading-relaxed text-aspal">
            Ulasan baru, keluhan di media sosial, atau kotak saran biasanya tidak punya bintang. Untuk teks seperti itu, pakai{" "}
            <Link href="/#coba" className="font-semibold underline decoration-merah underline-offset-2">
              pembaca satu ulasan
            </Link>{" "}
            atau{" "}
            <Link href="/massal" className="font-semibold underline decoration-merah underline-offset-2">
              cek massal
            </Link>
            .
          </div>
          <div className="mt-12">
            <DashboardAplikasi data={data} trend={trend} />
          </div>
          <p className="mt-12 max-w-3xl text-xs text-abu">
            Sumber: dataset IGAR v3 (Isnan dan Pardamean, 2025), lisensi CC BY 4.0. Daftar keluhan dan pujian dipilih otomatis dengan membandingkan
            seberapa sering tiap kata muncul di ulasan bintang rendah dan bintang tinggi aplikasi yang sama. Kata perasaan umum seperti jelek atau
            mantap sengaja tidak dihitung supaya yang tampil adalah hal yang dibicarakan. Contoh ulasan sudah disamarkan dari angka panjang dan alamat
            surel.
          </p>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
