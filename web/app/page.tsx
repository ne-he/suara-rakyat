import fs from "node:fs";
import path from "node:path";
import Analyzer from "@/components/Analyzer";

type PerClass = { precision: number; recall: number; f1: number; support: number };
type Metrics = {
  macro_f1: number;
  accuracy: number;
  weighted_f1: number;
  per_class: Record<"negative" | "neutral" | "positive", PerClass>;
  confusion: number[][];
};
type Report = {
  dataset: {
    raw_rows: number;
    exact_duplicates: number;
    unique_texts: number;
    label_counts_unique: Record<string, number>;
    split_counts: Record<string, Record<string, number>>;
    date_min: string;
    date_max: string;
    apps: Record<string, number>;
  };
  deploy: {
    name: string;
    features: string;
    metrics: {
      test: Metrics;
      val: Metrics;
      test_by_app: Record<string, number>;
      test_weighted_by_frequency: { macro_f1: number; accuracy: number };
      polarity_flip_rate: number;
      binary_neg_pos: { accuracy: number; macro_f1: number };
      label_noise_ceiling: {
        rows_in_those_keys: number;
        oracle_macro_f1_on_duplicated_rows: number;
        neutral_rows_whose_text_majority_is_not_neutral: number;
        example_mixed: Record<string, Record<string, number>>;
      };
    };
  };
  best_overall: string;
  leaderboard: {
    name: string;
    family: string;
    features: string;
    deployable: boolean;
    val_macro_f1: number;
    test_macro_f1: number;
    test_macro_f1_raw: number;
    test_accuracy: number;
    test_f1: Record<string, number>;
  }[];
};

const REPO_URL = "https://github.com/ne-he/suara-sentimen";

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
  word_noslang: "kata 1-2 gram, tanpa kamus slang",
  wordchar: "kata 1-2 gram + karakter 2-5 gram",
  transformer: "subword transformer",
};

const nf = new Intl.NumberFormat("id-ID");
const pct = (x: number, d = 1) => `${(x * 100).toFixed(d).replace(".", ",")}%`;
const dec = (x: number) => x.toFixed(3).replace(".", ",");

function loadReport(): Report {
  const file = path.join(process.cwd(), "model", "report.json");
  return JSON.parse(fs.readFileSync(file, "utf8")) as Report;
}

export default function Home() {
  const r = loadReport();
  const t = r.deploy.metrics.test;
  const testN = Object.values(r.dataset.split_counts.test).reduce((a, b) => a + b, 0);
  const trainN = Object.values(r.dataset.split_counts.train).reduce((a, b) => a + b, 0);
  const board = [...r.leaderboard].sort((a, b) => b.val_macro_f1 - a.val_macro_f1);
  const families = [...new Set(board.map((m) => m.family))].filter((f) => f !== "Baseline mayoritas" && f !== "Gabungan skor");
  const labels = ["negative", "neutral", "positive"] as const;
  const labelId = { negative: "Negatif", neutral: "Netral", positive: "Positif" };
  const colorOf = { negative: "var(--neg)", neutral: "var(--neu)", positive: "var(--pos)" };

  return (
    <main className="mx-auto w-full max-w-6xl px-4 sm:px-8">
      <header className="flex items-center justify-between border-b border-ink py-4">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-2xl font-extrabold tracking-tight">SUARA</span>
          <span className="hidden font-mono text-[11px] uppercase tracking-[0.14em] text-muted sm:inline">
            v1 · model sentimen ulasan
          </span>
        </div>
        <nav className="flex gap-5 text-sm text-ink-2">
          <a href="#bukti" className="hover:text-signal">Bukti</a>
          <a href="#cara" className="hover:text-signal">Cara kerja</a>
          {REPO_URL && (
            <a href={REPO_URL} className="hover:text-signal" target="_blank" rel="noreferrer">
              Kode
            </a>
          )}
        </nav>
      </header>

      <section className="grid gap-10 py-10 lg:grid-cols-[1.05fr_1fr] lg:gap-14 lg:py-16">
        <div className="rise">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">
            Untuk warga, bukan cuma untuk instansi
          </p>
          <h1 className="mt-4 font-display text-[44px] font-extrabold leading-[0.95] tracking-tight sm:text-[64px] lg:text-[76px]">
            Keluhanmu dibaca.
            <br />
            <span className="text-signal">Bukan cuma bintangnya.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-2">
            Tempel ulasan aplikasi layanan publik. Model yang belajar dari{" "}
            <b className="text-ink">{nf.format(r.dataset.unique_texts)} ulasan unik</b> Mobile JKN, JMO, SatuSehat,
            MyPertamina, KAI Access, dan Info BMKG akan membaca nadanya, lalu menunjukkan kata mana yang paling
            berpengaruh.
          </p>
          <dl className="mt-8 grid max-w-xl grid-cols-3 gap-px overflow-hidden rounded-xl border border-ink bg-ink">
            {[
              { k: "Macro-F1 test", v: dec(t.macro_f1) },
              { k: "Akurasi test", v: pct(t.accuracy) },
              { k: "Ulasan uji", v: nf.format(testN) },
            ].map((m) => (
              <div key={m.k} className="bg-card px-4 py-3">
                <dt className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">{m.k}</dt>
                <dd className="mt-1 font-display text-2xl font-bold">{m.v}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="rise [animation-delay:120ms]">
          <Analyzer />
        </div>
      </section>

      <section id="bukti" className="border-t border-ink py-14">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">Bukti, bukan klaim</p>
            <h2 className="mt-3 font-display text-4xl font-extrabold leading-none tracking-tight">
              Diuji di {nf.format(testN)} ulasan yang tidak pernah dilihat model.
            </h2>
            <p className="mt-5 leading-relaxed text-ink-2">
              Dari {nf.format(r.dataset.raw_rows)} ulasan mentah, {nf.format(r.dataset.exact_duplicates)} ternyata
              duplikat persis (kebanyakan &quot;mantap&quot; dan &quot;bagus&quot;). Duplikat dibuang dulu, lalu teks yang sama selalu
              masuk kelompok yang sama. Jadi skor di sini tidak menggelembung karena model sekadar hafal.
            </p>
            <p className="mt-4 leading-relaxed text-ink-2">
              Metrik utama <b className="text-ink">macro-F1</b>: rata-rata F1 tiga kelas dengan bobot sama, supaya kelas
              netral yang cuma {pct(r.dataset.label_counts_unique.neutral / r.dataset.unique_texts)} data tetap dihitung
              adil.
            </p>
            <div className="mt-6 rounded-[18px] border-2 border-ink bg-card p-5">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-signal">Kenapa angkanya tidak 0,9?</p>
              <p className="mt-2 text-sm leading-relaxed text-ink-2">
                Label diambil dari bintang, dan bintang sering tidak cocok dengan isi. Teks &quot;mantap&quot; saja diberi bintang
                negatif {nf.format(r.deploy.metrics.label_noise_ceiling.example_mixed.mantap?.negative ?? 0)} kali. Di{" "}
                {nf.format(r.deploy.metrics.label_noise_ceiling.rows_in_those_keys)} ulasan yang teksnya muncul berulang,
                tebakan sempurna pun cuma mencapai macro-F1{" "}
                <b className="text-ink">{dec(r.deploy.metrics.label_noise_ceiling.oracle_macro_f1_on_duplicated_rows)}</b>.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-ink-2">
                Yang paling penting buat warga: model hanya membalik negatif jadi positif (atau sebaliknya) di{" "}
                <b className="text-ink">{pct(r.deploy.metrics.polarity_flip_rate)}</b> ulasan. Kalau netral dikesampingkan,
                akurasinya <b className="text-ink">{pct(r.deploy.metrics.binary_neg_pos.accuracy)}</b>.
              </p>
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-[18px] border border-line bg-card p-5">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">Per kelas (test)</p>
              <div className="mt-4 space-y-4">
                {labels.map((l) => (
                  <div key={l}>
                    <div className="flex items-baseline justify-between">
                      <span className="font-medium" style={{ color: colorOf[l] }}>
                        {labelId[l]}
                      </span>
                      <span className="font-mono text-sm">F1 {dec(t.per_class[l].f1)}</span>
                    </div>
                    <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-paper-2">
                      <div className="h-full rounded-full" style={{ width: `${(t.per_class[l].f1 * 100).toFixed(1)}%`, background: colorOf[l] }} />
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      presisi {pct(t.per_class[l].precision)} · recall {pct(t.per_class[l].recall)} ·{" "}
                      {nf.format(t.per_class[l].support)} ulasan
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[18px] border border-line bg-card p-5">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">Matriks kebingungan (test)</p>
              <div className="mt-4 grid grid-cols-[64px_repeat(3,1fr)] gap-1 text-center text-xs">
                <span />
                {labels.map((l) => (
                  <span key={l} className="pb-1 text-muted">
                    {labelId[l]}
                  </span>
                ))}
                {labels.map((row, i) => {
                  const total = t.confusion[i].reduce((a, b) => a + b, 0);
                  return [
                    <span key={`h${row}`} className="flex items-center justify-end pr-1 text-muted">
                      {labelId[row]}
                    </span>,
                    ...t.confusion[i].map((v, j) => {
                      const share = v / total;
                      return (
                        <div
                          key={`${row}${j}`}
                          className="flex aspect-square flex-col items-center justify-center rounded-md"
                          style={{
                            background: `color-mix(in srgb, ${i === j ? colorOf[row] : "var(--ink)"} ${Math.round(share * 70)}%, var(--paper-2))`,
                            color: share > 0.45 ? "var(--paper)" : "var(--ink)",
                          }}
                        >
                          <span className="font-mono text-sm font-semibold">{pct(share, 0)}</span>
                          <span className="font-mono text-[10px] opacity-80">{nf.format(v)}</span>
                        </div>
                      );
                    }),
                  ];
                })}
              </div>
              <p className="mt-3 text-xs text-muted">Baris = label asli, kolom = prediksi.</p>
            </div>

            <div className="rounded-[18px] border border-line bg-card p-5 sm:col-span-2">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">Macro-F1 test per aplikasi</p>
              <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
                {Object.entries(r.deploy.metrics.test_by_app)
                  .sort((a, b) => b[1] - a[1])
                  .map(([app, f1]) => (
                    <div key={app} className="flex items-baseline justify-between border-b border-line pb-1.5">
                      <span className="text-sm">{APP_NAME[app] ?? app}</span>
                      <span className="font-mono text-sm">{dec(f1)}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-14">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">Papan perbandingan</p>
          <h3 className="mt-3 font-display text-3xl font-extrabold tracking-tight">
            {board.length} konfigurasi model diadu di data yang sama.
          </h3>
          <p className="mt-3 max-w-3xl text-ink-2">
            Model dipilih dari skor validation, bukan test, supaya angka test tetap jujur. Semua dilatih di{" "}
            {nf.format(trainN)} ulasan train. &quot;Geser bias&quot; menyesuaikan ambang kelas di validation agar kelas netral tidak
            tenggelam.
          </p>
          <div className="mt-6 overflow-x-auto rounded-[18px] border border-ink bg-card">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-ink font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
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
                {board.map((m) => {
                  const isDeploy = m.name === r.deploy.name;
                  return (
                    <tr key={m.name} className={`border-b border-line last:border-0 ${isDeploy ? "bg-paper-2" : ""}`}>
                      <td className="px-4 py-2.5">
                        <span className="font-medium">{m.family}</span>
                        {isDeploy && (
                          <span className="ml-2 rounded-full bg-signal px-2 py-0.5 font-mono text-[10px] uppercase text-paper">
                            dipakai web
                          </span>
                        )}
                        <span className="block font-mono text-[11px] text-muted">{m.name}</span>
                      </td>
                      <td className="px-4 py-2.5 text-ink-2">{FEATURE_ID[m.features] ?? m.features}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{dec(m.val_macro_f1)}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{dec(m.test_macro_f1)}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-muted">{dec(m.test_macro_f1_raw)}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{dec(m.test_f1.neutral)}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{pct(m.test_accuracy)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section id="cara" className="border-t border-ink py-14">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">Cara kerja</p>
        <div className="mt-6 grid gap-px overflow-hidden rounded-[18px] border border-ink bg-ink sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              n: "01",
              h: "Kumpulkan",
              p: `${nf.format(r.dataset.raw_rows)} ulasan Google Play dari 6 aplikasi pemerintah, ${r.dataset.date_min.slice(0, 4)} sampai ${r.dataset.date_max.slice(0, 4)} (dataset IGAR).`,
            },
            {
              n: "02",
              h: "Bersihkan",
              p: "Huruf kecil, URL dibuang, huruf berulang dipangkas, singkatan seperti gak, bgt, udh dibakukan. Duplikat digabung.",
            },
            {
              n: "03",
              h: "Adu model",
              p: `${families.join(", ")}, plus gabungannya. Pemenang dipilih dari skor validation.`,
            },
            {
              n: "04",
              h: "Jalan di web",
              p: "Bobot model diekspor dan dihitung langsung di server web, tanpa GPU. Hasilnya diuji identik dengan versi Python.",
            },
          ].map((s) => (
            <div key={s.n} className="bg-card p-6">
              <span className="font-mono text-sm text-signal">{s.n}</span>
              <h3 className="mt-2 font-display text-2xl font-bold">{s.h}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-2">{s.p}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <div className="rounded-[18px] border border-line bg-card p-6">
            <h3 className="font-display text-2xl font-bold">Batasan yang perlu kamu tahu</h3>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-ink-2">
              <li>
                <b className="text-ink">Label berasal dari bintang.</b> Bintang 1-2 dianggap negatif, 3 netral, 4-5 positif. Kadang
                orang menulis keluhan tapi memberi bintang 5, jadi labelnya sendiri tidak sempurna.
              </li>
              <li>
                <b className="text-ink">Netral paling sulit.</b> Ulasan bintang 3 sering berisi pujian dan keluhan sekaligus.
              </li>
              <li>
                <b className="text-ink">Sarkasme dan konteks panjang</b> bisa terbaca salah karena model membaca pola kata, bukan
                maksud.
              </li>
              <li>
                <b className="text-ink">Teks yang kamu kirim tidak disimpan.</b> Prediksi dihitung lalu langsung dibalas.
              </li>
            </ul>
          </div>
          <div className="rounded-[18px] border border-line bg-card p-6">
            <h3 className="font-display text-2xl font-bold">Sumber data</h3>
            <p className="mt-4 text-sm leading-relaxed text-ink-2">
              Isnan, M. dan Pardamean, B. (2025). <i>IGAR: Indonesian Government App Review Dataset</i>. Mendeley Data, V3.{" "}
              <a className="underline decoration-signal underline-offset-2" href="https://doi.org/10.17632/7zryc6k76z.3" target="_blank" rel="noreferrer">
                doi:10.17632/7zryc6k76z.3
              </a>
              . Lisensi CC BY 4.0. Data diolah ulang (duplikat digabung, teks dinormalisasi) untuk projek ini.
            </p>
            <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              {Object.entries(r.dataset.apps).map(([app, n]) => (
                <div key={app} className="flex justify-between border-b border-line pb-1">
                  <span>{APP_NAME[app] ?? app}</span>
                  <span className="font-mono text-ink-2">{nf.format(n)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <footer className="flex flex-col gap-2 border-t border-ink py-6 text-xs text-muted sm:flex-row sm:justify-between">
        <span>SUARA v1 · projek AOL Software Engineering</span>
        <span>Hasil model bukan penilaian resmi instansi mana pun.</span>
      </footer>
    </main>
  );
}
