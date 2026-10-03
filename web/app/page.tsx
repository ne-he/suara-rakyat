import type { CSSProperties } from "react";
import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import Analyzer from "@/components/Analyzer";
import type { DataAplikasi } from "@/components/DashboardAplikasi";
import PosterFx from "@/components/PosterFx";
import { SiteFooter } from "@/components/SiteHeader";
import SuaraTicker, { type TickerItem } from "@/components/SuaraTicker";
import ScrollStory, { type Chapter, type FramesManifest } from "@/components/ScrollStory";
import type { ModelMeta } from "@/lib/model";
import { CLASS_HEX } from "@/lib/fmt";

type Site = {
  dataset: {
    raw_rows: number;
    exact_duplicates: number;
    unique_texts: number;
    label_counts_unique: Record<"negative" | "neutral" | "positive", number>;
    split_counts: Record<string, Record<string, number>>;
    date_min: string;
    date_max: string;
    apps: Record<string, number>;
  };
};

type Extras = { ticker: TickerItem[] };

const TEAM = ["Nehemiah", "Marcel", "Wilson", "Hans", "Daniel"];

const APP_NAME: Record<string, string> = {
  JMO: "JMO",
  satusehat: "SatuSehat",
  mobileJKN: "Mobile JKN",
  pertamina: "MyPertamina",
  KAI: "KAI Access",
  BMKG: "Info BMKG",
};

const nf = new Intl.NumberFormat("id-ID");
const pct = (x: number, d = 0) => `${(x * 100).toFixed(d).replace(".", ",")}%`;

function loadJson<T>(file: string): T | null {
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as T) : null;
}

const LANGKAH = [
  { n: "1", h: "Tulis ulasan", p: "Ketik atau tempel ulasan tentang aplikasi layanan publik. Boleh pakai singkatan. Atau klik salah satu contoh." },
  { n: "2", h: "Tekan Baca nadanya", p: "Mesin membaca ulasanmu dalam sekejap. Tidak perlu daftar, dan teksnya tidak disimpan." },
  { n: "3", h: "Lihat hasilnya", p: "Nadanya negatif, netral, atau positif, seberapa yakin mesinnya, dan kata mana yang paling menentukan." },
];

export default function Home() {
  // path ditulis lengkap (bukan dari variabel) supaya Turbopack tidak ikut menyertakan seluruh proyek
  const site = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "site.json"), "utf8")) as Site;
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  const frames = loadJson<FramesManifest>(path.join(process.cwd(), "public", "frames", "manifest.json"));
  const extras = loadJson<Extras>(path.join(process.cwd(), "data", "extras.json"));
  const aplikasi = loadJson<DataAplikasi>(path.join(process.cwd(), "data", "aplikasi.json"));
  const d = site.dataset;
  const trainN = Object.values(d.split_counts.train).reduce((a, b) => a + b, 0);
  const testN = Object.values(d.split_counts.test).reduce((a, b) => a + b, 0);
  const shares = {
    negative: d.label_counts_unique.negative / d.unique_texts,
    neutral: d.label_counts_unique.neutral / d.unique_texts,
    positive: d.label_counts_unique.positive / d.unique_texts,
  };
  const model = meta.models.find((m) => m.id === meta.default_model) ?? meta.models[0];
  const tepat = Math.round(model.metrics.test.accuracy * 100);
  const netral = model.metrics.test.per_class.neutral;

  const chapters: Chapter[] = [
    {
      kicker: "Projek AOL Software Engineering",
      title: "Suara Rakyat",
      body: `${nf.format(d.raw_rows)} ulasan warga untuk enam aplikasi layanan publik. Scroll pelan-pelan.`,
    },
    {
      kicker: "Dari kolom ulasan",
      title: "Bintang satu punya cerita",
      body: "Kode OTP tidak kunjung masuk, saldo JHT tidak muncul. Keluhan seperti ini ditulis warga di Play Store setiap hari.",
    },
    {
      kicker: "Dibaca mesin",
      title: "Negatif, netral, positif",
      body: `Mesin belajar dari ${nf.format(trainN)} ulasan berbintang untuk menebak nada tiap ulasan baru.`,
    },
    {
      kicker: "Giliranmu",
      title: "Sekarang kamu bersuara",
      body: "Tulis ulasanmu. Web akan membaca nadanya dan menandai kata yang paling menentukan.",
      cta: { label: "Tulis suaramu", href: "#coba" },
    },
  ];

  return (
    <main>
      <PosterFx />
      <a href="#coba" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-putih focus:px-3 focus:py-2">
        Langsung ke formulir
      </a>

      <div className="relative">
        <header className="absolute inset-x-0 top-0 z-20 px-5 pt-5 sm:px-10">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <a href="#" className="display flex shrink-0 items-center gap-2 text-2xl text-putih">
              <span className="inline-block h-5 w-7 border border-putih/80 bg-[linear-gradient(to_bottom,var(--merah)_50%,#fff_50%)]" aria-hidden />
              <span className="hidden sm:inline">Suara Rakyat</span>
              <span className="sm:hidden">SR</span>
            </a>
            <nav className="flex gap-3 text-xs text-putih/90 sm:gap-6 sm:text-sm">
              <a href="#coba" className="hover:text-white">Coba</a>
              <a href="/massal" className="hover:text-white">Massal</a>
              <a href="/dashboard" className="hover:text-white">Dashboard</a>
              <a href="/kuesioner" className="hover:text-white">Kuesioner</a>
            </nav>
          </div>
        </header>
        <ScrollStory manifest={frames} chapters={chapters} shares={shares} />
      </div>

      {extras && <SuaraTicker items={extras.ticker} />}

      <section id="coba" className="scroll-mt-4 px-5 py-16 sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Coba sekarang</p>
          <h2 className="display mt-3 text-6xl sm:text-8xl">
            Tulis suaramu.
            <br />
            <span className="text-merah">Lihat nadanya.</span>
          </h2>
          <ol className="mt-8 grid gap-3 sm:grid-cols-3" aria-label="Cara pakai">
            {LANGKAH.map((l) => (
              <li key={l.n} className="flex gap-4 rounded-xl border-2 border-aspal/20 bg-white/60 p-4">
                <span className="display text-5xl leading-none text-merah">{l.n}</span>
                <span>
                  <span className="block font-semibold text-aspal">{l.h}</span>
                  <span className="mt-1 block text-sm leading-snug text-aspal-2">{l.p}</span>
                </span>
              </li>
            ))}
          </ol>
          <div className="mt-10">
            <Analyzer />
          </div>
          <p className="mt-8 text-sm text-aspal-2">
            Punya banyak ulasan sekaligus?{" "}
            <Link href="/massal" className="font-semibold underline decoration-merah underline-offset-2">
              Pakai cek massal
            </Link>
            , bisa sampai 1.000 ulasan dari file CSV.
          </p>
        </div>
      </section>

      {aplikasi && (
        <section id="aplikasi" className="border-t-2 border-aspal bg-kertas px-5 py-16 sm:px-10 sm:py-20">
          <div className="mx-auto max-w-6xl">
            <p className="kicker text-merah">Dashboard aplikasi</p>
            <h2 className="display mt-3 text-6xl sm:text-7xl">Porsi keluhan tiap aplikasi</h2>
            <p className="mt-5 max-w-3xl text-lg text-aspal-2">
              Dari {nf.format(aplikasi.ulasan)} ulasan, berapa yang bernada negatif (bintang 1 dan 2). Buka dashboard untuk melihat apa yang paling
              sering dikeluhkan di tiap aplikasi dan kapan keluhannya memuncak.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {[...aplikasi.apps]
                .sort((a, b) => b.porsi.negative - a.porsi.negative)
                .map((a) => (
                  <Link
                    key={a.id}
                    href="/dashboard"
                    className="poster rounded-xl border-2 border-aspal bg-white p-4 transition hover:-translate-y-0.5"
                  >
                    <span className="block text-sm font-semibold text-aspal">{a.nama}</span>
                    <span className="display mt-2 block text-4xl" style={{ color: CLASS_HEX.negative }}>
                      {pct(a.porsi.negative)}
                    </span>
                    <span className="block text-xs text-abu">negatif dari {nf.format(a.ulasan)}</span>
                  </Link>
                ))}
            </div>
            <Link
              href="/dashboard"
              className="display mt-8 inline-block rounded-sm bg-aspal px-6 py-3 text-2xl text-putih shadow-[4px_4px_0_var(--merah)] transition hover:-translate-y-0.5"
            >
              Buka dashboard
            </Link>
          </div>
        </section>
      )}

      <section id="cara" className="border-t-2 border-aspal bg-aspal px-5 py-16 text-putih sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Cara kerja</p>
          <h2 className="display mt-3 text-6xl sm:text-7xl">Dari kolom ulasan ke web</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { n: "01", h: "Kumpulkan", p: `${nf.format(d.raw_rows)} ulasan Google Play dari 6 aplikasi layanan publik, ${d.date_min.slice(0, 4)} sampai ${d.date_max.slice(0, 4)}.` },
              { n: "02", h: "Bersihkan", p: "Huruf dikecilkan, tautan dibuang, singkatan seperti gak, bgt, udh dibakukan, dan ulasan yang sama persis digabung." },
              { n: "03", h: "Belajar", p: `Mesin mempelajari kata mana yang sering muncul di ulasan bintang rendah, sedang, dan tinggi dari ${nf.format(trainN)} contoh.` },
              { n: "04", h: "Membaca", p: "Ulasan baru diubah menjadi angka, lalu nadanya ditebak dalam waktu kurang dari satu milidetik." },
            ].map((s) => (
              <div key={s.n} className="poster poster-gelap rounded-xl border-2 border-putih/20 p-6">
                <span className="font-mono text-sm text-merah">{s.n}</span>
                <h3 className="display mt-2 text-4xl">
                  <span className="angka">{s.h}</span>
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-putih/75">{s.p}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid gap-4 lg:grid-cols-3">
            <div className="poster poster-gelap rounded-xl border-2 border-putih/20 p-6">
              <h3 className="display text-4xl">
                <span className="angka">Seberapa tepat?</span>
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-putih/80">
                Mesin diuji dengan {nf.format(testN)} ulasan yang belum pernah dilihatnya. Dari setiap 100 ulasan, sekitar <b className="text-putih">{tepat}</b>{" "}
                terbaca sama dengan bintang yang diberikan penulisnya.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-putih/80">
                Yang paling sulit adalah ulasan netral (bintang 3): hanya sekitar {Math.round(netral.recall * 100)} dari 100 yang tertebak netral, karena
                isinya sering campuran pujian dan keluhan.
              </p>
            </div>
            <div className="poster poster-gelap rounded-xl border-2 border-putih/20 p-6 lg:col-span-2">
              <h3 className="display text-4xl">
                <span className="angka">Batasan</span>
              </h3>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-putih/80">
                <li>
                  <b className="text-putih">Bukan suara seluruh rakyat.</b> Yang terbaca hanya warga yang memakai Android, membuka Play Store, lalu
                  menyempatkan diri menulis. Orang yang sedang kesal atau sangat puas lebih sering menulis, dan ulasan dari iOS maupun media sosial
                  tidak ikut terhitung. Anggap ini satu sinyal publik, bukan hasil survei warga.
                </li>
                <li>
                  <b className="text-putih">Mesin belajar dari bintang.</b> Bintang 1-2 dianggap negatif, 3 netral, 4-5 positif. Kadang orang menulis
                  keluhan tapi memberi bintang 5, jadi mesin ikut belajar dari contoh yang keliru.
                </li>
                <li>
                  <b className="text-putih">Sindiran dan ulasan campuran</b> bisa terbaca salah karena mesin membaca pola kata, bukan maksud.
                </li>
                <li>
                  <b className="text-putih">Teks yang kamu kirim tidak disimpan.</b> Nadanya dihitung lalu langsung dibalas.
                </li>
              </ul>
            </div>
          </div>

          <div className="poster poster-gelap mt-4 rounded-xl border-2 border-putih/20 p-6">
            <h3 className="display text-4xl">
              <span className="angka">Sumber data</span>
            </h3>
            <p className="mt-4 text-sm leading-relaxed text-putih/80">
              Isnan, M. dan Pardamean, B. (2025). <i>IGAR: Indonesian Government App Review Dataset</i>. Mendeley Data, V3.{" "}
              <a className="underline decoration-merah underline-offset-2" href="https://doi.org/10.17632/7zryc6k76z.3" target="_blank" rel="noreferrer">
                doi:10.17632/7zryc6k76z.3
              </a>
              . Lisensi CC BY 4.0. Data diolah ulang (duplikat digabung, teks dinormalisasi).
            </p>
            <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
              {Object.entries(d.apps).map(([app, n]) => (
                <div key={app} className="flex justify-between border-b border-putih/15 pb-1">
                  <span>{APP_NAME[app] ?? app}</span>
                  <span className="font-mono text-putih/70">{nf.format(n)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="tim" className="border-t-2 border-aspal px-5 py-16 sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Tim</p>
          <h2 className="display mt-3 text-6xl sm:text-7xl">Tim pembuat</h2>
          <div className="mt-10 flex flex-wrap gap-5">
            {TEAM.map((name, i) => (
              <div key={name} className="karton karton-angkat rounded-sm px-6 py-5" style={{ "--r": `${[-3, 2, -1.5, 3, -2][i % 5]}deg` } as CSSProperties}>
                <span className="marker text-3xl text-aspal">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
