import type { CSSProperties } from "react";
import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import Analyzer, { type ModelCard } from "@/components/Analyzer";
import ModelEvidence, { type Evidence } from "@/components/ModelEvidence";
import PosterFx from "@/components/PosterFx";
import { SiteFooter } from "@/components/SiteHeader";
import SuaraTicker, { type TickerItem } from "@/components/SuaraTicker";
import TrendChart, { type TrendData } from "@/components/TrendChart";
import ScrollStory, { type Chapter, type FramesManifest } from "@/components/ScrollStory";
import type { ModelInfo, ModelMeta } from "@/lib/model";

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
  label_noise: {
    rows_in_duplicated_texts: number;
    oracle_macro_f1: number;
    neutral_not_majority: number;
    mantap: Record<string, number>;
  };
  leaderboard: {
    name: string;
    family: string;
    features: string;
    web_id: string | null;
    comparison: boolean;
    val_macro_f1: number;
    test_macro_f1: number;
    test_macro_f1_raw: number;
    test_accuracy: number;
    test_f1: Record<string, number>;
  }[];
  comparison: (Pick<ModelInfo, "id" | "name" | "features" | "tagline" | "metrics"> & {
    live: boolean;
    fit_seconds: number;
    fit_hardware: string;
    cpu_ms_per_review: number | null;
    size_mb: number | null;
  })[];
};

type Speed = { cpu: string; ms_per_review: Record<string, number> };
type Extras = { ticker: TickerItem[]; trend: TrendData };

const REPO_URL = "https://github.com/ne-he/suara-rakyat";
const TEAM = ["Nehemiah", "Marcel", "Wilson", "Hans", "Daniel"];

const APP_NAME: Record<string, string> = {
  JMO: "JMO",
  satusehat: "SatuSehat",
  mobileJKN: "Mobile JKN",
  pertamina: "MyPertamina",
  KAI: "KAI Access",
  BMKG: "Info BMKG",
};
const FEATURE_ID: Record<string, string> = {
  word: "kata 1-2 gram",
  word_noslang: "kata, tanpa kamus slang",
  wordchar: "kata + karakter 2-5 gram",
  transformer: "subword transformer",
  "transformer+wordchar": "transformer + kata/karakter",
};

const nf = new Intl.NumberFormat("id-ID");
const pct = (x: number, d = 1) => `${(x * 100).toFixed(d).replace(".", ",")}%`;
const dec = (x: number) => x.toFixed(3).replace(".", ",");

function loadExtras(): Extras | null {
  const file = path.join(process.cwd(), "data", "extras.json");
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as Extras) : null;
}

function loadSpeed(): Speed | null {
  const file = path.join(process.cwd(), "data", "speed.json");
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as Speed) : null;
}

function loadFrames(): FramesManifest | null {
  const file = path.join(process.cwd(), "public", "frames", "manifest.json");
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as FramesManifest) : null;
}

export default function Home() {
  const site = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "site.json"), "utf8")) as Site;
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  const frames = loadFrames();
  const speed = loadSpeed();
  const extras = loadExtras();
  // model besar hanya muncul kalau alamat servernya sudah diisi di env (INDOBERT_URL)
  const remoteReady = Boolean(process.env.INDOBERT_URL);
  const d = site.dataset;
  const trainN = Object.values(d.split_counts.train).reduce((a, b) => a + b, 0);
  const testN = Object.values(d.split_counts.test).reduce((a, b) => a + b, 0);
  const shares = {
    negative: d.label_counts_unique.negative / d.unique_texts,
    neutral: d.label_counts_unique.neutral / d.unique_texts,
    positive: d.label_counts_unique.positive / d.unique_texts,
  };
  const board = [...site.leaderboard].sort((a, b) => b.val_macro_f1 - a.val_macro_f1);
  const families = [...new Set(board.map((m) => m.family))].filter((f) => f !== "Baseline mayoritas" && f !== "Gabungan skor");
  const best = meta.models.find((m) => m.id === meta.default_model) ?? meta.models[0];
  const top = site.comparison[0];

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
      body: `Model dilatih dengan ${nf.format(trainN)} ulasan unik untuk menebak nada tiap ulasan baru.`,
    },
    {
      kicker: "Giliranmu",
      title: "Sekarang kamu bersuara",
      body: "Tulis ulasanmu dan pilih modelnya. Web akan menandai kata yang paling menentukan hasilnya.",
      cta: { label: "Tulis suaramu", href: "#coba" },
    },
  ];

  const remoteModel = site.comparison.find((m) => m.live);
  const remoteCard: ModelCard | undefined =
    remoteReady && remoteModel
      ? {
          id: remoteModel.id,
          name: remoteModel.name,
          features: remoteModel.features,
          tagline: "Paling akurat. Jalan di server terpisah, jadi jawabannya lebih lama, apalagi kalau servernya baru bangun.",
          macroF1: remoteModel.metrics.test.macro_f1,
          accuracy: remoteModel.metrics.test.accuracy,
          remote: true,
        }
      : undefined;
  const cards: ModelCard[] = meta.models.map((m) => ({
    id: m.id,
    name: m.name,
    features: m.features,
    tagline: m.tagline,
    macroF1: m.metrics.test.macro_f1,
    accuracy: m.metrics.test.accuracy,
  }));
  const toEvidence = (m: Pick<ModelInfo, "id" | "name" | "features" | "metrics">) => ({
    id: m.id,
    name: m.name,
    features: m.features,
    valF1: m.metrics.val_macro_f1,
    testF1: m.metrics.test.macro_f1,
    testF1Raw: m.metrics.test_macro_f1_raw,
    accuracy: m.metrics.test.accuracy,
    flipRate: m.metrics.polarity_flip_rate,
    binaryAccuracy: m.metrics.binary_neg_pos_accuracy,
    perClass: m.metrics.test.per_class,
    confusion: m.metrics.test.confusion,
    byApp: m.metrics.test_by_app,
  });
  const evidence: Evidence[] = [
    ...meta.models.map((m) => ({
      ...toEvidence(m),
      live: true,
      fitSeconds: m.fit_seconds,
      fitHardware: "CPU laptop",
      msPerReview: speed?.ms_per_review[m.id] ?? null,
      speedHardware: "CPU laptop",
    })),
    ...site.comparison.map((m) => ({
      ...toEvidence(m),
      live: false,
      note: m.live
        ? `${m.name} jalan di server terpisah (folder indobert-api), bukan di server web ini. Ukurannya ${String(m.size_mb ?? "?").replace(".", ",")} MB dan butuh sekitar ${String(m.cpu_ms_per_review ?? "?").replace(".", ",")} ms per ulasan di CPU laptop, sekitar 95 kali lebih lambat dari model linear.${remoteReady ? " Sudah bisa dicoba di formulir atas." : " Belum dinyalakan di web ini."}`
        : `${m.name} versi penuh (${String(m.size_mb ?? "?").replace(".", ",")} MB) butuh GPU untuk cepat, jadi dipakai sebagai pembanding di laporan saja. Versi ringannya ada di baris berikutnya.`,
      fitSeconds: m.fit_seconds,
      fitHardware: m.fit_hardware,
      msPerReview: m.cpu_ms_per_review,
      speedHardware: m.live ? "CPU laptop, ONNX int8" : "belum diukur",
    })),
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
              <a href="/kuesioner" className="hidden hover:text-white sm:inline">Kuesioner</a>
              <a href={REPO_URL} target="_blank" rel="noreferrer" className="hidden hover:text-white sm:inline">
                Kode
              </a>
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
            <span className="text-merah">Pilih pembacanya.</span>
          </h2>
          <p className="mt-5 max-w-2xl text-lg text-aspal-2">
            Tiga model membaca ulasan yang sama sekaligus. Pilih salah satu untuk lihat alasannya, atau bandingkan ketiganya di bawah hasil.
          </p>
          <div className="mt-10">
            <Analyzer models={cards} defaultId={meta.default_model} remote={remoteCard} />
          </div>
        </div>
      </section>

      {extras && (
        <section id="tren" className="border-t-2 border-aspal px-5 py-16 sm:px-10 sm:py-20">
          <div className="mx-auto max-w-6xl">
            <p className="kicker text-merah">Tren keluhan</p>
            <h2 className="display mt-3 text-6xl sm:text-7xl">Naik turunnya keluhan warga</h2>
            <p className="mt-5 max-w-3xl text-lg text-aspal-2">
              Porsi ulasan bintang 1 dan 2 tiap kuartal, dihitung dari {nf.format(extras.trend.total_rows)} ulasan mentah. Ini label asli dari bintang,
              jadi bukan hasil tebakan model.
            </p>
            <div className="poster mt-8 rounded-xl border-2 border-aspal bg-white p-4 sm:p-6">
              <TrendChart data={extras.trend} defaultApp="pertamina" />
            </div>
          </div>
        </section>
      )}

      <section id="bukti" className="border-t-2 border-aspal bg-kertas px-5 py-16 sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr]">
            <div>
              <p className="kicker text-merah">Hasil uji</p>
              <h2 className="display mt-3 text-6xl sm:text-7xl">Diuji di {nf.format(testN)} ulasan yang belum pernah dilihat.</h2>
              <p className="mt-5 leading-relaxed text-aspal-2">
                Dari {nf.format(d.raw_rows)} ulasan mentah, {nf.format(d.exact_duplicates)} ternyata duplikat persis, kebanyakan &quot;mantap&quot;
                dan &quot;bagus&quot;. Duplikat digabung dulu, lalu teks yang sama selalu masuk kelompok yang sama. Jadi skor di sini tidak
                menggelembung karena model sekadar hafal.
              </p>
              <p className="mt-4 leading-relaxed text-aspal-2">
                Metrik utama <b className="text-aspal">macro-F1</b>: rata-rata F1 tiga kelas dengan bobot sama, supaya kelas netral yang cuma{" "}
                {pct(shares.neutral)} data tetap dihitung adil.
              </p>
            </div>
            <div className="karton karton-angkat self-start rounded-sm p-6">
              <p className="marker text-2xl text-merah-tua">Kenapa tidak 0,9?</p>
              <p className="mt-3 text-sm leading-relaxed text-aspal">
                Label diambil dari bintang, dan bintang sering tidak cocok dengan isi. Teks &quot;mantap&quot; saja diberi bintang negatif{" "}
                {nf.format(site.label_noise.mantap.negative ?? 0)} kali. Di {nf.format(site.label_noise.rows_in_duplicated_texts)} ulasan yang
                teksnya muncul berulang, tebakan terbaik yang mungkin dari teks saja cuma mencapai macro-F1{" "}
                <b>{dec(site.label_noise.oracle_macro_f1)}</b>. Batas itu khusus untuk kelompok tersebut, bukan untuk seluruh data test.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-aspal">
                {top ? (
                  <>
                    Skor tertinggi kami <b>{dec(top.metrics.test.macro_f1)}</b> dari {top.name}. Model di formulir atas ({best.name}) mencapai{" "}
                    <b>{dec(best.metrics.test.macro_f1)}</b> dan membalik negatif jadi positif (atau sebaliknya) di{" "}
                    <b>{pct(best.metrics.polarity_flip_rate)}</b> ulasan.
                  </>
                ) : (
                  <>
                    Model terbaik kami mencapai <b>{dec(best.metrics.test.macro_f1)}</b> dan membalik negatif jadi positif (atau sebaliknya) di{" "}
                    <b>{pct(best.metrics.polarity_flip_rate)}</b> ulasan.
                  </>
                )}
              </p>
            </div>
          </div>

          <div className="mt-14">
            <ModelEvidence models={evidence} />
          </div>

          <div className="mt-16">
            <p className="kicker text-merah">Papan perbandingan</p>
            <h3 className="display mt-3 text-5xl">{board.length} konfigurasi diadu di data yang sama</h3>
            <p className="mt-3 max-w-3xl text-aspal-2">
              Urutan ditentukan skor validation. Angka test baru dihitung sesudahnya, jadi tidak ikut memengaruhi pilihan. Semua dilatih di{" "}
              {nf.format(trainN)} ulasan. Geser bias mengatur ambang tiap kelas di validation supaya kelas netral tetap tertebak.
            </p>
            <div className="mt-6 overflow-x-auto rounded-xl border-2 border-aspal bg-white">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="kicker border-b-2 border-aspal text-abu">
                  <tr>
                    <th className="px-4 py-3">Model</th>
                    <th className="px-4 py-3">Fitur</th>
                    <th className="px-4 py-3 text-right">Val F1</th>
                    <th className="px-4 py-3 text-right">Test F1</th>
                    <th className="px-4 py-3 text-right">Tanpa geser bias</th>
                    <th className="px-4 py-3 text-right">F1 netral</th>
                    <th className="px-4 py-3 text-right">Akurasi</th>
                  </tr>
                </thead>
                <tbody>
                  {board.map((m) => (
                    <tr key={m.name} className={`baris border-b border-garis last:border-0 ${m.web_id ? "bg-merah/5" : ""}`}>
                      <td className="px-4 py-2.5">
                        <span className="font-semibold">{m.family}</span>
                        {m.web_id && (
                          <span className="ml-2 rounded-full bg-merah px-2 py-0.5 font-mono text-[10px] uppercase text-putih">ada di web</span>
                        )}
                        {m.comparison && (
                          <span className="ml-2 rounded-full bg-aspal px-2 py-0.5 font-mono text-[10px] uppercase text-putih">pembanding</span>
                        )}
                        <span className="block font-mono text-[11px] text-abu">{m.name}</span>
                      </td>
                      <td className="px-4 py-2.5 text-aspal-2">{FEATURE_ID[m.features] ?? m.features}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{dec(m.val_macro_f1)}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{dec(m.test_macro_f1)}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-abu">{dec(m.test_macro_f1_raw)}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{dec(m.test_f1.neutral)}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{pct(m.test_accuracy)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section id="cara" className="border-t-2 border-aspal bg-aspal px-5 py-16 text-putih sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Cara kerja</p>
          <h2 className="display mt-3 text-6xl sm:text-7xl">Dari kolom ulasan ke web</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { n: "01", h: "Kumpulkan", p: `${nf.format(d.raw_rows)} ulasan Google Play dari 6 aplikasi pemerintah, ${d.date_min.slice(0, 4)} sampai ${d.date_max.slice(0, 4)} (dataset IGAR).` },
              { n: "02", h: "Bersihkan", p: "Huruf kecil, URL dibuang, huruf berulang dipangkas, singkatan seperti gak, bgt, udh dibakukan. Duplikat digabung." },
              { n: "03", h: "Adu model", p: `${families.join(", ")}, plus gabungannya. Urutan diambil dari skor validation.` },
              { n: "04", h: "Jalan di web", p: "Bobot tiga model linear diekspor dan dihitung di server web tanpa GPU. Hasilnya dicek sama dengan versi Python di 3.018 teks." },
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

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <div className="poster poster-gelap rounded-xl border-2 border-putih/20 p-6">
              <h3 className="display text-4xl">
                <span className="angka">Batasan</span>
              </h3>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-putih/80">
                <li>
                  <b className="text-putih">Bukan suara seluruh rakyat.</b> Yang terbaca di sini hanya warga yang memakai Android, membuka Play
                  Store, lalu menyempatkan diri menulis. Orang yang sedang kesal atau sangat puas lebih sering menulis daripada yang biasa saja, dan
                  ulasan dari iOS maupun media sosial tidak ikut terhitung. Anggap ini satu sinyal publik, bukan hasil survei warga.
                </li>
                <li>
                  <b className="text-putih">Label berasal dari bintang.</b> Bintang 1-2 dianggap negatif, 3 netral, 4-5 positif. Kadang orang menulis
                  keluhan tapi memberi bintang 5.{" "}
                  <Link href="/dashboard#label" className="underline decoration-merah underline-offset-2">
                    Contohnya ada di dashboard
                  </Link>
                  .
                </li>
                <li>
                  <b className="text-putih">Netral paling sulit.</b> Ulasan bintang 3 sering berisi pujian dan keluhan sekaligus.
                </li>
                <li>
                  <b className="text-putih">Sarkasme dan konteks panjang</b> bisa terbaca salah karena model membaca pola kata, bukan maksud.
                </li>
                <li>
                  <b className="text-putih">Teks yang kamu kirim tidak disimpan.</b> Prediksi dihitung lalu langsung dibalas.
                </li>
              </ul>
            </div>
            <div className="poster poster-gelap rounded-xl border-2 border-putih/20 p-6">
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
              <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                {Object.entries(d.apps).map(([app, n]) => (
                  <div key={app} className="flex justify-between border-b border-putih/15 pb-1">
                    <span>{APP_NAME[app] ?? app}</span>
                    <span className="font-mono text-putih/70">{nf.format(n)}</span>
                  </div>
                ))}
              </div>
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

      <SiteFooter version={meta.version} />
    </main>
  );
}
