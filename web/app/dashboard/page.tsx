import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import Link from "next/link";
import {
  KartuAnotasi,
  KartuLabelKotor,
  KartuPembanding,
  KartuUjiTahan,
  type Anotasi,
  type LabelKotor,
  type Pembanding,
  type UjiTahan,
} from "@/components/BuktiTambahan";
import { BoardTable, MainTable, PerClassF1, ScoreVsTime, SpeedBars, type BoardRow, type MainModel } from "@/components/DashboardCharts";
import SiteHeader, { SiteFooter } from "@/components/SiteHeader";
import type { ModelInfo, ModelMeta } from "@/lib/model";
import { dec, nf } from "@/lib/fmt";

export const metadata: Metadata = {
  title: "Dashboard model · Suara Rakyat",
  description: "Perbandingan semua model sentimen ulasan aplikasi layanan publik: kecepatan, akurasi, presisi, dan waktu latih.",
};

type Comparison = Pick<ModelInfo, "id" | "name" | "features" | "tagline" | "metrics"> & {
  live: boolean;
  fit_seconds: number;
  fit_hardware: string;
  cpu_ms_per_review: number | null;
  size_mb: number | null;
};
type Site = { leaderboard: BoardRow[]; comparison: Comparison[]; label_noise: { oracle_macro_f1: number } };
type Speed = { cpu: string; measured: string; ms_per_review: Record<string, number>; ms_all_models: number };

function bacaOpsional<T>(berkas: string): T | null {
  return fs.existsSync(berkas) ? (JSON.parse(fs.readFileSync(berkas, "utf8")) as T) : null;
}

const FEATURE_ID: Record<string, string> = {
  word: "kata 1-2 gram",
  word_noslang: "kata, tanpa kamus slang",
  wordchar: "kata + karakter 2-5 gram",
  transformer: "subword transformer",
  "transformer+wordchar": "transformer + kata/karakter",
};

// path ditulis lengkap (bukan dari variabel) supaya Turbopack tidak ikut menyertakan seluruh proyek
export default function Dashboard() {
  const site = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "site.json"), "utf8")) as Site;
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  const speed = bacaOpsional<Speed>(path.join(process.cwd(), "data", "speed.json"));
  const labelKotor = bacaOpsional<LabelKotor>(path.join(process.cwd(), "data", "label.json"));
  const uji = bacaOpsional<UjiTahan>(path.join(process.cwd(), "data", "uji.json"));
  const pembanding = bacaOpsional<Pembanding>(path.join(process.cwd(), "data", "pembanding.json"));
  const anotasi = bacaOpsional<Anotasi>(path.join(process.cwd(), "data", "anotasi.json"));

  const macro = (m: { metrics: ModelInfo["metrics"] }, k: "precision" | "recall") =>
    (["negative", "neutral", "positive"] as const).reduce((s, l) => s + m.metrics.test.per_class[l][k], 0) / 3;

  const models: MainModel[] = [
    ...meta.models.map((m) => ({
      id: m.id,
      name: m.name,
      status: "web" as const,
      macroF1: m.metrics.test.macro_f1,
      accuracy: m.metrics.test.accuracy,
      precision: macro(m, "precision"),
      recall: macro(m, "recall"),
      f1: {
        negative: m.metrics.test.per_class.negative.f1,
        neutral: m.metrics.test.per_class.neutral.f1,
        positive: m.metrics.test.per_class.positive.f1,
      },
      msPerReview: speed?.ms_per_review[m.id] ?? null,
      speedNote: "TypeScript di server web, CPU laptop",
      fitSeconds: m.fit_seconds,
      fitNote: "scikit-learn, CPU laptop",
    })),
    ...site.comparison.map((c) => ({
      id: c.id,
      name: c.name,
      status: (c.live ? "server" : "pembanding") as MainModel["status"],
      macroF1: c.metrics.test.macro_f1,
      accuracy: c.metrics.test.accuracy,
      precision: macro(c, "precision"),
      recall: macro(c, "recall"),
      f1: {
        negative: c.metrics.test.per_class.negative.f1,
        neutral: c.metrics.test.per_class.neutral.f1,
        positive: c.metrics.test.per_class.positive.f1,
      },
      msPerReview: c.cpu_ms_per_review,
      speedNote: c.live ? "onnxruntime int8, CPU laptop" : "belum diukur, versi penuh butuh GPU",
      fitSeconds: c.fit_seconds,
      fitNote: c.fit_hardware,
    })),
  ];
  const board = [...site.leaderboard].sort((a, b) => b.val_macro_f1 - a.val_macro_f1);
  const deploy = meta.models.find((m) => m.id === meta.default_model) ?? meta.models[0];
  const juara = models.reduce((a, b) => (b.macroF1 > a.macroF1 ? b : a));

  return (
    <>
      <SiteHeader active="/dashboard" />
      <main className="px-5 py-12 sm:px-10 sm:py-16">
        <div className="mx-auto max-w-6xl">
          <p className="kicker text-merah">Dashboard model</p>
          <h1 className="display mt-3 text-6xl sm:text-8xl">
            Semua model,
            <br />
            <span className="text-merah">satu papan.</span>
          </h1>
          <p className="mt-5 max-w-3xl text-lg text-aspal-2">
            {board.length} konfigurasi diadu di data yang sama. Halaman ini memakai angka yang sama persis dengan laporan, jadi tabel dan grafiknya
            bisa langsung diambil untuk bab Hasil.
          </p>
          <nav aria-label="Loncat ke bagian" className="mt-5 flex flex-wrap gap-2 text-sm">
            {[
              { href: "#label", teks: "Label kotor", ada: !!labelKotor },
              { href: "#uji", teks: "Uji tahan bahasa", ada: !!uji },
              { href: "#pembanding", teks: "Pembanding penelitian lain", ada: !!pembanding },
              { href: "#anotasi", teks: "Dibaca ulang manusia", ada: !!anotasi },
            ]
              .filter((x) => x.ada)
              .map((x) => (
                <a
                  key={x.href}
                  href={x.href}
                  className="rounded-full border-2 border-aspal/30 px-4 py-1 transition duration-300 hover:-translate-y-0.5 hover:border-aspal hover:bg-white"
                >
                  {x.teks}
                </a>
              ))}
          </nav>

          <section className="mt-12">
            <h2 className="display text-4xl">Model utama</h2>
            <p className="mt-2 max-w-3xl text-sm text-aspal-2">
              Skor tertinggi dipegang <b className="text-aspal">{juara.name}</b>. Kecepatan baca diukur di laptop yang sama
              {speed ? ` (${speed.cpu}, ${nf.format(speed.ms_all_models)} ms untuk tiga model linear sekaligus)` : ""}. Presisi dan recall adalah
              rata-rata tiga kelas.
            </p>
            <div className="mt-5">
              <MainTable models={models} />
            </div>
          </section>

          <section className="mt-14">
            <h2 className="display text-4xl">Skor dibanding waktu latih</h2>
            <p className="mt-2 max-w-3xl text-sm text-aspal-2">
              Sumbu datar memakai skala log. Naik sedikit di skor sering berarti waktu latih berlipat.
            </p>
            <div className="poster mt-5 rounded-xl border-2 border-aspal bg-white p-4 sm:p-5">
              <ScoreVsTime rows={board} />
            </div>
          </section>

          <section className="mt-14 grid gap-6 lg:grid-cols-2">
            <div>
              <h2 className="display text-4xl">F1 per kelas</h2>
              <p className="mt-2 text-sm text-aspal-2">Kelas netral yang paling sulit untuk semua model.</p>
              <div className="poster mt-5 rounded-xl border-2 border-aspal bg-white p-4 sm:p-5">
                <PerClassF1 models={models} />
              </div>
            </div>
            <div>
              <h2 className="display text-4xl">Kecepatan baca</h2>
              <p className="mt-2 text-sm text-aspal-2">Satu ulasan per panggilan, CPU laptop yang sama.</p>
              <div className="poster mt-5 rounded-xl border-2 border-aspal bg-white p-4 sm:p-5">
                <SpeedBars models={models} />
              </div>
            </div>
          </section>

          {labelKotor && (
            <section id="label" className="mt-14 scroll-mt-20">
              <h2 className="display text-4xl">Seberapa kotor labelnya</h2>
              <p className="mt-2 max-w-3xl text-sm text-aspal-2">
                Label di dataset ini berasal dari bintang, bukan dari orang yang membaca teksnya. Teks yang sama persis bisa mendapat bintang 1 dari
                satu orang dan bintang 5 dari orang lain. Di baris ulasan yang teksnya kembar, tebakan sempurna dari teks saja hanya sampai macro-F1{" "}
                {dec(site.label_noise.oracle_macro_f1)}. Angka model di halaman ini harus dibaca dengan batas itu.
              </p>
              <div className="mt-5">
                <KartuLabelKotor d={labelKotor} />
              </div>
            </section>
          )}

          {uji && (
            <section id="uji" className="mt-14 scroll-mt-20">
              <h2 className="display text-4xl">Uji tahan bahasa</h2>
              <p className="mt-2 max-w-3xl text-sm text-aspal-2">
                Skor rata-rata menyembunyikan kelemahan yang khas bahasa sehari-hari. {uji.n} kalimat disusun tim untuk menguji salah ketik, bahasa
                gaul, kalimat bernegasi, sindiran, pujian yang bercampur keluhan, pertanyaan netral, ulasan sangat pendek, dan emoji. Kalimat dan
                label acuannya buatan tim, bukan dari dataset, jadi ini uji tambahan, bukan tolok ukur resmi.
              </p>
              <div className="mt-5">
                <KartuUjiTahan d={uji} />
              </div>
            </section>
          )}

          {pembanding && (
            <section id="pembanding" className="mt-14 scroll-mt-20">
              <h2 className="display text-4xl">Pembanding dari penelitian lain</h2>
              <p className="mt-2 max-w-3xl text-sm text-aspal-2">
                Paper resmi dataset ini melaporkan akurasi 0,81 sampai 0,92 per aplikasi. Angka itu jauh di atas macro-F1 kami, dan alasannya ada
                dua. Pertama, skor tertimbang dikuasai kelas besar, sedangkan macro-F1 memberi bobot sama ke kelas netral yang hanya 7 persen data.
                Kedua, paper tidak menyebut cara memisah data, dan kalau ulasan kembar dibiarkan tersebar acak, teks yang sama bisa muncul di latih
                dan uji sekaligus. Kolom replikasi memakai setelan paper, kolom split kami memakai kunci teks yang anti bocor.
              </p>
              <div className="mt-5">
                <KartuPembanding
                  d={pembanding}
                  kami={{
                    macroF1: deploy.metrics.test.macro_f1,
                    f1Weighted: deploy.metrics.test.weighted_f1,
                    accuracy: deploy.metrics.test.accuracy,
                  }}
                />
              </div>
            </section>
          )}

          {anotasi && (
            <section id="anotasi" className="mt-14 scroll-mt-20">
              <h2 className="display text-4xl">Dibaca ulang manusia</h2>
              <p className="mt-2 max-w-3xl text-sm text-aspal-2">
                Pembuat dataset menulis sendiri bahwa tiap ulasan hanya punya satu penilai, yaitu penulisnya lewat bintang. Tim membaca ulang{" "}
                {nf.format(anotasi.butir_disiapkan)} ulasan test tanpa melihat bintangnya, supaya terlihat seberapa sering pembaca manusia sepakat
                dan seberapa jauh bintang dari pembacaan manusia.
              </p>
              <div className="mt-5">
                <KartuAnotasi d={anotasi} />
              </div>
            </section>
          )}

          <section className="mt-14">
            <h2 className="display text-4xl">Papan perbandingan lengkap</h2>
            <p className="mt-2 max-w-3xl text-sm text-aspal-2">
              Urutan ditentukan skor validation. Angka test baru dihitung sesudahnya. Matriks kebingungan tiap model yang jalan di web ada di{" "}
              <Link href="/#bukti" className="underline decoration-merah underline-offset-2">
                bagian bukti halaman depan
              </Link>
              .
            </p>
            <div className="mt-5">
              <BoardTable rows={board} featureId={FEATURE_ID} />
            </div>
          </section>
        </div>
      </main>
      <SiteFooter version={meta.version} />
    </>
  );
}
