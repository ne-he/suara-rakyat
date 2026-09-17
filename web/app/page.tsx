import fs from "node:fs";
import path from "node:path";
import Analyzer, { type ModelCard } from "@/components/Analyzer";
import ModelEvidence, { type Evidence } from "@/components/ModelEvidence";
import ScrollStory, { type Chapter, type FramesManifest } from "@/components/ScrollStory";
import type { ModelMeta } from "@/lib/model";

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
    val_macro_f1: number;
    test_macro_f1: number;
    test_macro_f1_raw: number;
    test_accuracy: number;
    test_f1: Record<string, number>;
  }[];
};

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
};

const nf = new Intl.NumberFormat("id-ID");
const pct = (x: number, d = 1) => `${(x * 100).toFixed(d).replace(".", ",")}%`;
const dec = (x: number) => x.toFixed(3).replace(".", ",");

function loadFrames(): FramesManifest | null {
  const file = path.join(process.cwd(), "public", "frames", "manifest.json");
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as FramesManifest) : null;
}

export default function Home() {
  const site = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "site.json"), "utf8")) as Site;
  const meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), "model", "meta.json"), "utf8")) as ModelMeta;
  const frames = loadFrames();
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

  const chapters: Chapter[] = [
    {
      kicker: "Projek AOL Software Engineering",
      title: "Suara Rakyat",
      body: `${nf.format(d.raw_rows)} ulasan warga untuk enam aplikasi layanan publik. Scroll pelan-pelan.`,
    },
    {
      kicker: "Ulasan adalah suara",
      title: "Bintang satu punya cerita",
      body: "OTP tidak masuk, antrean hilang, saldo tidak muncul. Warga menuliskannya di kolom ulasan, satu per satu.",
    },
    {
      kicker: "Dibaca mesin",
      title: "Negatif, netral, positif",
      body: `Tiga model belajar dari ${nf.format(d.unique_texts)} ulasan unik untuk membaca nada setiap suara.`,
    },
    {
      kicker: "Giliranmu",
      title: "Sekarang kamu bersuara",
      body: "Tulis ulasanmu, pilih model pembacanya, lalu lihat kata mana yang paling menentukan.",
      cta: { label: "Tulis suaramu", href: "#coba" },
    },
  ];

  const cards: ModelCard[] = meta.models.map((m) => ({
    id: m.id,
    name: m.name,
    features: m.features,
    tagline: m.tagline,
    macroF1: m.metrics.test.macro_f1,
    accuracy: m.metrics.test.accuracy,
  }));
  const evidence: Evidence[] = meta.models.map((m) => ({
    id: m.id,
    name: m.name,
    features: m.features,
    fitSeconds: m.fit_seconds,
    valF1: m.metrics.val_macro_f1,
    testF1: m.metrics.test.macro_f1,
    testF1Raw: m.metrics.test_macro_f1_raw,
    accuracy: m.metrics.test.accuracy,
    flipRate: m.metrics.polarity_flip_rate,
    binaryAccuracy: m.metrics.binary_neg_pos_accuracy,
    perClass: m.metrics.test.per_class,
    confusion: m.metrics.test.confusion,
    byApp: m.metrics.test_by_app,
  }));

  return (
    <main>
      <a href="#coba" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-putih focus:px-3 focus:py-2">
        Langsung ke formulir
      </a>

      <div className="relative">
        <header className="absolute inset-x-0 top-0 z-20 px-5 pt-5 sm:px-10">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <a href="#" className="display flex items-center gap-2 text-2xl text-putih">
              <span className="inline-block h-5 w-7 border border-putih/80 bg-[linear-gradient(to_bottom,var(--merah)_50%,#fff_50%)]" aria-hidden />
              Suara Rakyat
            </a>
            <nav className="flex gap-4 text-sm text-putih/90 sm:gap-6">
              <a href="#coba" className="hover:text-white">Coba</a>
              <a href="#bukti" className="hover:text-white">Bukti</a>
              <a href="#tim" className="hidden hover:text-white sm:inline">Tim</a>
              <a href={REPO_URL} target="_blank" rel="noreferrer" className="hover:text-white">
                Kode
              </a>
            </nav>
          </div>
        </header>
        <ScrollStory manifest={frames} chapters={chapters} shares={shares} />
      </div>

      <div className="bendera" />

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
            <Analyzer models={cards} defaultId={meta.default_model} />
          </div>
        </div>
      </section>

      <section id="bukti" className="border-t-2 border-aspal bg-kertas px-5 py-16 sm:px-10 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr]">
            <div>
              <p className="kicker text-merah">Bukti, bukan klaim</p>
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
            <div className="karton self-start rounded-sm p-6">
              <p className="marker text-2xl text-merah-tua">Kenapa tidak 0,9?</p>
              <p className="mt-3 text-sm leading-relaxed text-aspal">
                Label diambil dari bintang, dan bintang sering tidak cocok dengan isi. Teks &quot;mantap&quot; saja diberi bintang negatif{" "}
                {nf.format(site.label_noise.mantap.negative ?? 0)} kali. Di {nf.format(site.label_noise.rows_in_duplicated_texts)} ulasan yang
                teksnya muncul berulang, tebakan sempurna pun cuma mencapai macro-F1 <b>{dec(site.label_noise.oracle_macro_f1)}</b>.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-aspal">
                Model terbaik kami mencapai <b>{dec(best.metrics.test.macro_f1)}</b> dan hanya membalik negatif jadi positif (atau sebaliknya) di{" "}
                <b>{pct(best.metrics.polarity_flip_rate)}</b> ulasan.
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
              Model dipilih dari skor validation, bukan test, supaya angka test tetap jujur. Semua dilatih di {nf.format(trainN)} ulasan. Geser bias
              menyesuaikan ambang kelas di validation agar kelas netral tidak tenggelam.
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
                    <tr key={m.name} className={`border-b border-garis last:border-0 ${m.web_id ? "bg-merah/5" : ""}`}>
                      <td className="px-4 py-2.5">
                        <span className="font-semibold">{m.family}</span>
                        {m.web_id && (
                          <span className="ml-2 rounded-full bg-merah px-2 py-0.5 font-mono text-[10px] uppercase text-putih">ada di web</span>
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
              { n: "03", h: "Adu model", p: `${families.join(", ")}, plus gabungannya. Pemenang dipilih dari skor validation.` },
              { n: "04", h: "Jalan di web", p: "Bobot tiga model diekspor dan dihitung langsung di server web tanpa GPU. Hasilnya diuji identik dengan versi Python." },
            ].map((s) => (
              <div key={s.n} className="rounded-xl border-2 border-putih/20 p-6">
                <span className="font-mono text-sm text-merah">{s.n}</span>
                <h3 className="display mt-2 text-4xl">{s.h}</h3>
                <p className="mt-2 text-sm leading-relaxed text-putih/75">{s.p}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border-2 border-putih/20 p-6">
              <h3 className="display text-4xl">Batasan</h3>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-putih/80">
                <li>
                  <b className="text-putih">Label berasal dari bintang.</b> Bintang 1-2 dianggap negatif, 3 netral, 4-5 positif. Kadang orang menulis
                  keluhan tapi memberi bintang 5.
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
            <div className="rounded-xl border-2 border-putih/20 p-6">
              <h3 className="display text-4xl">Sumber data</h3>
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
          <h2 className="display mt-3 text-6xl sm:text-7xl">Yang bersuara di balik layar</h2>
          <div className="mt-10 flex flex-wrap gap-5">
            {TEAM.map((name, i) => (
              <div key={name} className="karton rounded-sm px-6 py-5" style={{ transform: `rotate(${[-3, 2, -1.5, 3, -2][i % 5]}deg)` }}>
                <span className="marker text-3xl text-aspal">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="bendera" />
      <footer className="px-5 py-6 text-xs text-abu sm:px-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:justify-between">
          <span>Suara Rakyat {meta.version} · projek AOL Software Engineering</span>
          <span>Hasil model bukan penilaian resmi instansi mana pun.</span>
        </div>
      </footer>
    </main>
  );
}
