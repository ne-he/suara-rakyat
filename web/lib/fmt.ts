// Format angka gaya Indonesia dan nama tampilan yang dipakai banyak komponen.

export type Label = "negative" | "neutral" | "positive";

export const LABELS: Label[] = ["negative", "neutral", "positive"];
export const LABEL_ID: Record<Label, string> = { negative: "Negatif", neutral: "Netral", positive: "Positif" };
// warna literal (bukan var CSS) supaya grafik yang diunduh sebagai SVG/PNG tetap berwarna
export const CLASS_HEX: Record<Label, string> = { negative: "#b0151f", neutral: "#c98a05", positive: "#1c7a4c" };
export const INK = { primary: "#141210", secondary: "#2a2622", muted: "#6f675c", grid: "#e4dccb", surface: "#ffffff" };
export const EMPHASIS = { transformer: "#ce1126", web: "#2b5f9e", other: "#b5ab9c" };

export const APP_NAME: Record<string, string> = {
  JMO: "JMO",
  satusehat: "SatuSehat",
  mobileJKN: "Mobile JKN",
  pertamina: "MyPertamina",
  KAI: "KAI Access",
  BMKG: "Info BMKG",
};

export const nf = new Intl.NumberFormat("id-ID");
export const pct = (x: number, d = 1) => `${(x * 100).toFixed(d).replace(".", ",")}%`;
export const dec = (x: number, d = 3) => x.toFixed(d).replace(".", ",");
export const ms = (x: number) => `${x.toFixed(x < 1 ? 2 : 1).replace(".", ",")} ms`;
export const duration = (s: number) => (s < 1 ? "< 1 dtk" : s < 120 ? `${Math.round(s)} dtk` : `${Math.round(s / 60)} mnt`);
