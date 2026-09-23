// Tiga bukti tambahan di dashboard: label yang bertabrakan, uji tahan bahasa, dan pembanding
// dari penelitian lain. Semuanya tabel dan batang sederhana, jadi tidak perlu JavaScript di browser.

import { CLASS_HEX, dec, LABELS, LABEL_ID, nf, pct, type Label } from "@/lib/fmt";

export type LabelKotor = {
  min_kemunculan: number;
  teks_unik: number;
  teks_muncul_ulang: number;
  teks_label_bertabrakan: number;
  baris_di_teks_bertabrakan: number;
  contoh: { teks: string; n: number; negative: number; neutral: number; positive: number; bintang_rata: number }[];
};
export type UjiTahan = {
  catatan: string;
  n: number;
  model: { id: string; nama: string }[];
  akurasi: Record<string, number>;
  per_kategori: ({ kategori: string; n: number } & Record<string, number>)[];
  butir: { kategori: string; teks: string; label: Label; alasan: string; jawab: Record<string, Label> }[];
};
type Skor = { accuracy: number; precision_weighted: number; recall_weighted: number; f1_weighted: number; f1_macro: number; n_test?: number };
export type Pembanding = {
  sumber_paper: { sitasi: string; doi: string; setelan: string };
  kesepakatan_bintang_vader: { n: number; kappa: number; kecocokan: number; paper_kappa: number; paper_kecocokan: number };
  vader_di_test_kami: Skor;
  per_app: { app: string; paper_linearsvc: Record<string, number>; acak: Skor; kunci_teks: Skor }[];
  semua_app: { acak: Skor; kunci_teks: Skor };
};
export type Anotasi = {
  anotator: number;
  butir_disiapkan: number;
  butir_dipakai: number;
  butir_seri: number;
  butir_tidak_jelas: number;
  kappa_fleiss: number;
  kesepakatan_penuh: number;
  kappa_pasangan: { pasangan: string; kappa: number }[];
  banding: Record<string, { nama?: string; kappa?: number; accuracy?: number; macro_f1?: number; lawan_manusia?: { accuracy: number; macro_f1: number }; lawan_bintang?: { accuracy: number; macro_f1: number } }>;
};

const KATEGORI_ID: Record<string, string> = {
  typo: "Salah ketik",
  slang: "Bahasa gaul",
  negasi: "Kalimat bernegasi",
  sarkasme: "Sindiran",
  campuran: "Pujian campur keluhan",
  netral: "Pertanyaan dan saran",
  pendek: "Sangat pendek",
  emoji: "Emoji",
};
const APP_ID: Record<string, string> = {
  satusehat: "SatuSehat",
  BMKG: "Info BMKG",
  KAI: "KAI Access",
  pertamina: "MyPertamina",
  mobileJKN: "Mobile JKN",
  JMO: "JMO",
};
const TABEL = "w-full min-w-[34rem] text-left text-sm [&_td]:px-3 [&_td]:py-2 [&_th]:px-3 [&_th]:py-2 [&_tr]:border-b [&_tr]:border-garis";

function Pita({ row }: { row: Record<Label, number> }) {
  const total = LABELS.reduce((s, l) => s + row[l], 0) || 1;
  return (
    <span className="flex h-3 w-full overflow-hidden rounded-full border border-aspal/25" aria-hidden>
      {LABELS.map((l) => (
        <span key={l} style={{ width: `${((row[l] / total) * 100).toFixed(2)}%`, background: CLASS_HEX[l] }} />
      ))}
    </span>
  );
}

export function KartuLabelKotor({ d }: { d: LabelKotor }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { a: nf.format(d.teks_label_bertabrakan), b: "teks yang sama mendapat lebih dari satu label bintang" },
          { a: nf.format(d.baris_di_teks_bertabrakan), b: "ulasan berada di dalam teks-teks itu" },
          { a: nf.format(d.min_kemunculan), b: "kali kemunculan minimal untuk masuk daftar di bawah" },
        ].map((k) => (
          <div key={k.b} className="karton-angkat karton rounded-sm p-4">
            <p className="display text-4xl text-merah-tua">{k.a}</p>
            <p className="mt-1 text-sm text-aspal-2">{k.b}</p>
          </div>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className={TABEL}>
          <caption className="sr-only">Contoh teks ulasan yang sama dengan label bintang berbeda</caption>
          <thead className="bg-kertas">
            <tr>
              <th scope="col">Teks ulasan</th>
              <th scope="col" className="text-right">Muncul</th>
              <th scope="col" className="min-w-[9rem]">Sebaran label</th>
              <th scope="col" className="text-right">Negatif</th>
              <th scope="col" className="text-right">Netral</th>
              <th scope="col" className="text-right">Positif</th>
              <th scope="col" className="text-right">Bintang</th>
            </tr>
          </thead>
          <tbody>
            {d.contoh.map((c) => (
              <tr key={c.teks} className="sel">
                <td className="max-w-[16rem] truncate" title={c.teks}>{c.teks}</td>
                <td className="text-right font-mono">{nf.format(c.n)}</td>
                <td><Pita row={c} /></td>
                <td className="text-right font-mono">{nf.format(c.negative)}</td>
                <td className="text-right font-mono">{nf.format(c.neutral)}</td>
                <td className="text-right font-mono">{nf.format(c.positive)}</td>
                <td className="text-right font-mono">{dec(c.bintang_rata, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-aspal-2">
        {LABELS.map((l) => (
          <span key={l} className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: CLASS_HEX[l] }} aria-hidden />
            {LABEL_ID[l]}
          </span>
        ))}
      </div>
    </div>
  );
}

export function KartuUjiTahan({ d }: { d: UjiTahan }) {
  const terbaik = (row: Record<string, number>) => Math.max(...d.model.map((m) => row[m.id] ?? 0));
  return (
    <div className="space-y-5">
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className={TABEL}>
          <caption className="sr-only">Akurasi tiap model per kategori kalimat uji</caption>
          <thead className="bg-kertas">
            <tr>
              <th scope="col">Kategori</th>
              <th scope="col" className="text-right">Kalimat</th>
              {d.model.map((m) => (
                <th key={m.id} scope="col" className="text-right">{m.nama}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {d.per_kategori.map((k) => {
              const top = terbaik(k);
              return (
                <tr key={k.kategori} className="sel">
                  <td>{KATEGORI_ID[k.kategori] ?? k.kategori}</td>
                  <td className="text-right font-mono">{k.n}</td>
                  {d.model.map((m) => (
                    <td key={m.id} className={`text-right font-mono ${k[m.id] === top ? "font-bold text-merah-tua" : ""}`}>{pct(k[m.id] as number, 0)}</td>
                  ))}
                </tr>
              );
            })}
            <tr className="bg-kertas font-medium">
              <td>Semua kalimat</td>
              <td className="text-right font-mono">{d.n}</td>
              {d.model.map((m) => (
                <td key={m.id} className="text-right font-mono">{pct(d.akurasi[m.id], 1)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer text-xs text-abu hover:text-aspal">Lihat {d.n} kalimat ujinya</summary>
        <div className="mt-2 max-h-96 overflow-auto rounded-lg border border-garis bg-white">
          <table className={TABEL}>
            <thead className="sticky top-0 bg-kertas">
              <tr>
                <th scope="col">Kalimat</th>
                <th scope="col">Kategori</th>
                <th scope="col">Acuan</th>
                {d.model.map((m) => (
                  <th key={m.id} scope="col">{m.nama}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {d.butir.map((b) => (
                <tr key={b.teks}>
                  <td className="max-w-[20rem]">{b.teks}</td>
                  <td className="text-xs text-aspal-2">{KATEGORI_ID[b.kategori] ?? b.kategori}</td>
                  <td className="text-xs">{LABEL_ID[b.label]}</td>
                  {d.model.map((m) => (
                    <td key={m.id} className="text-xs" style={{ color: b.jawab[m.id] === b.label ? undefined : CLASS_HEX.negative }}>
                      {LABEL_ID[b.jawab[m.id]]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export function KartuPembanding({ d, kami }: { d: Pembanding; kami: { macroF1: number; f1Weighted: number; accuracy: number } }) {
  const k = d.kesepakatan_bintang_vader;
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { a: dec(k.kappa, 4), b: `kappa bintang lawan VADER di ${nf.format(k.n)} ulasan. Paper menulis ${dec(k.paper_kappa, 2)}` },
          { a: pct(k.kecocokan, 2), b: `label bintang dan VADER sama. Paper menulis ${pct(k.paper_kecocokan, 2)}` },
          { a: dec(d.vader_di_test_kami.f1_macro), b: "macro-F1 VADER kalau dipakai sebagai model di data test kami" },
        ].map((x) => (
          <div key={x.b} className="karton-angkat karton rounded-sm p-4">
            <p className="display text-4xl text-merah-tua">{x.a}</p>
            <p className="mt-1 text-sm text-aspal-2">{x.b}</p>
          </div>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className={TABEL}>
          <caption className="sr-only">Baseline paper IGAR dan replikasinya di dua cara memisah data</caption>
          <thead className="bg-kertas">
            <tr>
              <th scope="col">Aplikasi</th>
              <th scope="col" className="text-right">Paper: akurasi</th>
              <th scope="col" className="text-right">Paper: F1</th>
              <th scope="col" className="text-right">Replikasi acak: akurasi</th>
              <th scope="col" className="text-right">Replikasi acak: F1 tertimbang</th>
              <th scope="col" className="text-right">Split kami: F1 tertimbang</th>
              <th scope="col" className="text-right">Split kami: macro-F1</th>
            </tr>
          </thead>
          <tbody>
            {d.per_app.map((r) => (
              <tr key={r.app} className="sel">
                <td>{APP_ID[r.app] ?? r.app}</td>
                <td className="text-right font-mono">{dec(r.paper_linearsvc.accuracy, 2)}</td>
                <td className="text-right font-mono">{dec(r.paper_linearsvc.f1, 2)}</td>
                <td className="text-right font-mono">{dec(r.acak.accuracy, 2)}</td>
                <td className="text-right font-mono">{dec(r.acak.f1_weighted, 2)}</td>
                <td className="text-right font-mono">{dec(r.kunci_teks.f1_weighted, 2)}</td>
                <td className="text-right font-mono">{dec(r.kunci_teks.f1_macro, 2)}</td>
              </tr>
            ))}
            <tr className="bg-kertas font-medium">
              <td>Semua aplikasi</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right font-mono">{dec(d.semua_app.acak.accuracy, 2)}</td>
              <td className="text-right font-mono">{dec(d.semua_app.acak.f1_weighted, 2)}</td>
              <td className="text-right font-mono">{dec(d.semua_app.kunci_teks.f1_weighted, 2)}</td>
              <td className="text-right font-mono">{dec(d.semua_app.kunci_teks.f1_macro, 2)}</td>
            </tr>
            <tr className="bg-kertas font-medium">
              <td>Model web kami</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right text-aspal-2">tidak ada</td>
              <td className="text-right font-mono">{dec(kami.f1Weighted, 2)}</td>
              <td className="text-right font-mono">{dec(kami.macroF1, 2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-xs text-aspal-2">
        Baris paper diambil dari Tabel 9 (LinearSVC, teks Indonesia) di {d.sumber_paper.sitasi} doi:{d.sumber_paper.doi}. {d.sumber_paper.setelan}
      </p>
    </div>
  );
}

export function KartuAnotasi({ d }: { d: Anotasi }) {
  const model = Object.entries(d.banding).filter(([id]) => id !== "bintang");
  const bintang = d.banding.bintang;
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { a: dec(d.kappa_fleiss, 2), b: `kappa Fleiss antar ${d.anotator} pembaca di ${nf.format(d.butir_dipakai)} ulasan` },
          { a: pct(d.kesepakatan_penuh, 0), b: "ulasan yang dinilai sama persis oleh semua pembaca" },
          { a: dec(bintang?.kappa ?? 0, 2), b: "kappa label bintang lawan label pembaca" },
        ].map((x) => (
          <div key={x.b} className="karton-angkat karton rounded-sm p-4">
            <p className="display text-4xl text-merah-tua">{x.a}</p>
            <p className="mt-1 text-sm text-aspal-2">{x.b}</p>
          </div>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border-2 border-aspal bg-white">
        <table className={TABEL}>
          <caption className="sr-only">Skor tiap model terhadap label pembaca manusia dan label bintang</caption>
          <thead className="bg-kertas">
            <tr>
              <th scope="col">Model</th>
              <th scope="col" className="text-right">Macro-F1 lawan pembaca</th>
              <th scope="col" className="text-right">Macro-F1 lawan bintang</th>
            </tr>
          </thead>
          <tbody>
            {model.map(([id, m]) => (
              <tr key={id} className="sel">
                <td>{m.nama ?? id}</td>
                <td className="text-right font-mono">{dec(m.lawan_manusia?.macro_f1 ?? 0)}</td>
                <td className="text-right font-mono">{dec(m.lawan_bintang?.macro_f1 ?? 0)}</td>
              </tr>
            ))}
            <tr className="bg-kertas font-medium">
              <td>Label bintang</td>
              <td className="text-right font-mono">{dec(bintang?.macro_f1 ?? 0)}</td>
              <td className="text-right text-aspal-2">acuan</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-xs text-aspal-2">
        {nf.format(d.butir_disiapkan)} ulasan disiapkan, {nf.format(d.butir_seri)} dibuang karena suara pembaca seri dan{" "}
        {nf.format(d.butir_tidak_jelas)} dinilai tidak jelas. Contoh diambil seimbang per kelas bintang, jadi angka di tabel ini tidak sebanding
        dengan skor di seluruh data test.
      </p>
    </div>
  );
}
