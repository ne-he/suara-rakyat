import type { NextConfig } from "next";

// File bobot model dibaca lewat fs saat runtime, jadi wajib ikut dibundel ke fungsi serverless.
// Hanya model bawaan (Linear SVM) yang dibawa. Bobot LR dan NB di folder model cuma dipakai skrip uji.
const MODEL_FILES = ["./model/meta.json", "./model/vocab_word.txt", "./model/vocab_char.txt", "./model/idf.f32", "./model/coef_svm.f32"];
const MODEL_LAIN = ["./model/coef_logreg.f32", "./model/coef_nb.f32"];

const nextConfig: NextConfig = {
  outputFileTracingIncludes: {
    "/api/predict": MODEL_FILES,
    "/api/predict-batch": MODEL_FILES,
  },
  outputFileTracingExcludes: {
    "/api/predict": MODEL_LAIN,
    "/api/predict-batch": MODEL_LAIN,
  },
  poweredByHeader: false,
  // Pintasan saat presentasi di komputer kelas. Tidak ditautkan dari menu, hanya tautan lihat saja (view) di Canva.
  async redirects() {
    return [
      { source: "/presentasi", destination: "https://www.canva.com/design/DAHXD6OaoFY/aT3THzQRSzqnMxq1Nt76lg/view", permanent: false },
      { source: "/poster", destination: "https://www.canva.com/design/DAHXDY2yA_I/GXDv3-DdJlHK_iWla7_93Q/view", permanent: false },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data:",
              "font-src 'self'",
              "connect-src 'self'",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
