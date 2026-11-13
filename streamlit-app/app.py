"""Suara Rakyat v5: dashboard pemantauan ulasan aplikasi layanan publik.

Tampilan saja. Pengambilan ulasan ada di suara/scraper.py, klasifikasi di suara/classifier.py,
ringkasan di suara/analysis.py. Jalankan: streamlit run app.py
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from suara.analysis import LABEL_ID, ReviewAnalysis
from suara.apps import APPS
from suara.classifier import LABELS, SentimentClassifier
from suara.scraper import MAX_FETCH, WIB, AppNotFound, ReviewScraper

OTHER = "Aplikasi lain (isi application ID)"
COLORS = {"Negatif": "#c0392b", "Netral": "#8a8f98", "Positif": "#2e8b57"}
APP_ID_RE = re.compile(r"^[A-Za-z][\w]*(\.[\w]+)+$")

st.set_page_config(page_title="Suara Rakyat: Pantau Ulasan", page_icon="📣", layout="wide")


@st.cache_resource(show_spinner="Memuat model...")
def load_classifier() -> SentimentClassifier:
    return SentimentClassifier()


def parse_app_id(raw: str) -> str:
    """Terima application ID atau tautan Google Play utuh (ambil bagian setelah id=)."""
    m = re.search(r"[?&]id=([\w.]+)", raw)
    return (m.group(1) if m else raw).strip()


def ribuan(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def run_search(app_id: str, start: date, end: date) -> None:
    scraper = ReviewScraper()
    with st.status("Mengambil ulasan dari Google Play...", expanded=True) as status:
        try:
            info = scraper.app_info(app_id)
        except AppNotFound:
            status.update(label="Aplikasi tidak ditemukan", state="error")
            st.error(f"Application ID `{app_id}` tidak ditemukan di Google Play Indonesia. Cek lagi ejaannya.")
            return
        except Exception:
            status.update(label="Google Play tidak bisa dihubungi", state="error")
            st.error("Google Play tidak bisa dihubungi saat ini. Coba lagi beberapa menit lagi.")
            return
        st.write(f"**{info['title']}** oleh {info['developer']}")

        start_dt = datetime.combine(start, datetime.min.time(), WIB)
        end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), WIB)
        bar = st.progress(0.0, text="Mengambil halaman pertama...")

        def on_progress(fetched: int, oldest: datetime | None) -> None:
            covered = (end_dt - oldest) / (end_dt - start_dt) if oldest else 0.0
            frac = min(1.0, max(0.0, covered, fetched / MAX_FETCH))
            tgl = oldest.strftime("%d/%m/%Y") if oldest else "-"
            bar.progress(frac, text=f"{ribuan(fetched)} ulasan diambil, sudah sampai tanggal {tgl}")

        res = scraper.fetch(app_id, start, end, on_progress)
        st.write(f"Membaca nada {ribuan(len(res.reviews))} ulasan...")
        preds = load_classifier().predict_many(res.reviews["content"].tolist())
        status.update(label="Selesai", state="complete", expanded=False)

    st.session_state["hasil"] = {
        "info": info,
        "app_id": app_id,
        "start": start,
        "end": end,
        "res": res,
        "analysis": ReviewAnalysis(res.reviews, preds),
        "taken_at": datetime.now(WIB),
    }


def show_dashboard(h: dict) -> None:
    a: ReviewAnalysis = h["analysis"]
    res = h["res"]
    st.subheader(h["info"]["title"])
    st.caption(
        f"{h['info']['developer']} · `{h['app_id']}` · ulasan {h['start']:%d/%m/%Y} sampai {h['end']:%d/%m/%Y} · "
        f"diambil {h['taken_at']:%d/%m/%Y %H:%M} WIB"
    )
    if res.hit_limit:
        st.warning(
            f"Pencarian dibatasi {ribuan(res.fetched)} ulasan terbaru. Ulasan tertua yang terambil bertanggal "
            f"{res.oldest_seen:%d/%m/%Y}, jadi ulasan sebelum tanggal itu belum terbaca. Persempit rentang tanggal "
            "supaya semua ulasan masuk."
        )
    if a.df.empty:
        st.info(
            "Tidak ada ulasan di rentang tanggal ini. Kalau rentangnya baru saja dan aplikasinya ramai, "
            "bisa jadi Google Play sedang menolak permintaan. Coba lagi beberapa menit lagi."
        )
        return

    counts = a.counts()
    total = sum(counts.values())
    cols = st.columns(4)
    cols[0].metric("Ulasan dibaca", ribuan(total))
    if a.unreadable():
        cols[0].caption(f"{a.unreadable()} ulasan tidak terbaca (tanpa kata yang dikenali)")
    for col, lab in zip(cols[1:], LABELS):
        col.metric(LABEL_ID[lab], pct(counts[lab] / total) if total else "0%")
        col.caption(f"{ribuan(counts[lab])} ulasan")
    agree = a.star_agreement()
    if agree is not None:
        st.caption(
            f"Nada hasil model sama dengan nada dari bintang pada {pct(agree)} ulasan. "
            "Bintang hanya pembanding, karena isi tulisan tidak selalu sejalan dengan bintangnya."
        )

    trend = a.trend()
    weekly = a.is_weekly()
    trend["label"] = trend["periode"].dt.strftime("%d/%m/%y" if weekly else "%d/%m")
    order = trend.sort_values("periode")["label"].unique().tolist()
    scale = alt.Scale(domain=list(COLORS), range=list(COLORS.values()))
    chart = (
        alt.Chart(trend)
        .mark_bar()
        .encode(
            x=alt.X("label:O", sort=order, title="Minggu mulai tanggal" if weekly else "Tanggal", axis=alt.Axis(labelAngle=-45 if len(order) > 14 else 0)),
            y=alt.Y("jumlah:Q", title="Jumlah ulasan"),
            color=alt.Color("nada:N", scale=scale, legend=alt.Legend(title=None, orient="top")),
            order=alt.Order("nada:N", sort="ascending"),
            tooltip=[alt.Tooltip("label:O", title="Periode"), "nada:N", "jumlah:Q"],
        )
        .properties(height=280)
    )
    st.markdown("#### Tren nada ulasan")
    st.altair_chart(chart, width="stretch")

    st.markdown("#### Kata yang paling menentukan")
    c1, c2 = st.columns(2)
    for col, lab in ((c1, "negative"), (c2, "positive")):
        words = a.top_words(lab)
        col.markdown(f"**Mendorong ke {LABEL_ID[lab].lower()}**")
        if words.empty:
            col.caption("Belum ada ulasan dengan nada ini.")
            continue
        bars = (
            alt.Chart(words)
            .mark_bar(color=COLORS[LABEL_ID[lab]])
            .encode(
                x=alt.X("skor:Q", title="Seberapa kuat mendorong", axis=alt.Axis(labels=False)),
                y=alt.Y("kata:N", sort="-x", title=None),
                tooltip=["kata:N", alt.Tooltip("ulasan:Q", title="Muncul di ulasan")],
            )
            .properties(height=28 * len(words))
        )
        col.altair_chart(bars, width="stretch")

    st.markdown("#### Daftar ulasan")
    f1, f2 = st.columns([3, 2])
    pilihan = f1.segmented_control("Nada", ["Negatif", "Netral", "Positif", "Semua"], default="Negatif")
    urut = f2.selectbox("Urutkan", ["Terbaru", "Paling banyak disukai", "Keyakinan tertinggi"])
    label = None if pilihan in (None, "Semua") else {v: k for k, v in LABEL_ID.items()}[pilihan]
    tabel = a.table(label)
    if urut == "Paling banyak disukai":
        tabel = tabel.sort_values("disukai", ascending=False)
    elif urut == "Keyakinan tertinggi":
        tabel = tabel.sort_values("keyakinan", ascending=False)
    tabel = tabel.assign(keyakinan=(tabel["keyakinan"] * 100).round().astype("Int64"))
    st.caption(f"{ribuan(len(tabel))} ulasan")
    st.dataframe(
        tabel,
        hide_index=True,
        width="stretch",
        height=420,
        column_config={
            "tanggal": st.column_config.TextColumn("Tanggal", width="small"),
            "bintang": st.column_config.NumberColumn("Bintang", format="%d ⭐", width="small"),
            "nada": st.column_config.TextColumn("Nada", width="small"),
            "keyakinan": st.column_config.NumberColumn("Keyakinan", format="%d%%", width="small"),
            "disukai": st.column_config.NumberColumn("Disukai", help="Jumlah pengguna yang menandai ulasan ini membantu", width="small"),
            "dibalas": st.column_config.TextColumn("Dibalas", help="Sudah dibalas pengembang aplikasi atau belum", width="small"),
            "ulasan": st.column_config.TextColumn("Ulasan", width="large"),
        },
    )
    st.download_button(
        "Unduh semua hasil (CSV)",
        a.to_csv(),
        file_name=f"suara-rakyat_{h['app_id']}_{h['start']:%Y%m%d}-{h['end']:%Y%m%d}.csv",
        mime="text/csv",
    )


st.title("📣 Suara Rakyat")
st.markdown(
    "Dashboard pemantauan ulasan aplikasi layanan publik. Pilih aplikasi dan rentang tanggal, "
    "sistem mengambil ulasannya dari Google Play lalu membaca nadanya: **negatif**, **netral**, atau **positif**."
)

today = datetime.now(WIB).date()
c1, c2, c3 = st.columns([2, 1, 1])
pilih = c1.selectbox("Aplikasi", [*APPS, OTHER])
start = c2.date_input("Start date", value=today - timedelta(days=6), max_value=today, format="DD/MM/YYYY")
end = c3.date_input("End date", value=today, max_value=today, format="DD/MM/YYYY")
raw_id = ""
if pilih == OTHER:
    raw_id = st.text_input(
        "Application ID",
        placeholder="contoh: com.bpjstku",
        help="Bagian setelah id= di alamat Google Play aplikasinya. Boleh juga tempel alamat lengkapnya.",
    )

if st.button("Ambil dan baca ulasan", type="primary"):
    app_id = APPS.get(pilih) or parse_app_id(raw_id)
    if start > end:
        st.error("Start date harus sama dengan atau sebelum end date.")
    elif not APP_ID_RE.match(app_id):
        st.error("Isi application ID yang valid, misalnya `com.bpjstku`.")
    else:
        run_search(app_id, start, end)

if "hasil" in st.session_state:
    show_dashboard(st.session_state["hasil"])

with st.expander("Cara kerja dan batasan"):
    st.markdown(
        f"""
- Ulasan diambil dari Google Play Indonesia lewat library `google-play-scraper`, paling banyak {ribuan(MAX_FETCH)} ulasan terbaru per pencarian.
- Nada dibaca oleh model **Linear SVM** yang dilatih dari 617.722 ulasan dataset IGAR (2012 sampai 2023). Di data uji, macro-F1 0,668 dan akurasi 82,7%.
- Model membaca pola kata, bukan maksud. Sarkasme dan kalimat yang mencampur pujian dan keluhan bisa terbaca salah. Kelas netral paling sulit dibaca.
- Model dilatih dari ulasan sampai 2023, jadi istilah atau fitur aplikasi yang baru muncul sesudahnya bisa belum dikenali.
- Nama dan foto pengulas tidak diambil. Deret angka panjang (misalnya NIK atau nomor HP) dan email disamarkan. Hasil tidak disimpan di server dan hilang saat halaman ditutup.
"""
    )
