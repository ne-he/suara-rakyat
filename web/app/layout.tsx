import type { Metadata, Viewport } from "next";
import { Big_Shoulders, JetBrains_Mono, Permanent_Marker, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const shoulders = Big_Shoulders({
  variable: "--font-shoulders",
  subsets: ["latin"],
  weight: ["700", "900"],
  adjustFontFallback: false,
});

const marker = Permanent_Marker({
  variable: "--font-marker",
  subsets: ["latin"],
  weight: "400",
});

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["400", "600"],
});

export const metadata: Metadata = {
  title: "Suara Rakyat · Baca nada ulasan aplikasi layanan publik",
  description:
    "617.722 ulasan warga untuk Mobile JKN, JMO, SatuSehat, MyPertamina, KAI Access, dan Info BMKG dibaca oleh tiga model sentimen. Tulis ulasanmu dan pilih modelnya.",
};

export const viewport: Viewport = {
  themeColor: "#ce1126",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="id"
      className={`${shoulders.variable} ${marker.variable} ${jakarta.variable} ${jetbrains.variable} antialiased`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
