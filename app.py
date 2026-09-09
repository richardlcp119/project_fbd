import os
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Big Data Sales Insight Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme / small CSS ----------
st.markdown("""
<style>
    .main { background: #f6faf7; }
    .block-container { padding-top: 1.2rem; }
    .dashboard-title { color: #087443; font-size: 2.25rem; font-weight: 800; margin-bottom: 0.15rem; }
    .dashboard-subtitle { color: #4d6358; margin-bottom: 1.2rem; }
    .section-title { color: #087443; font-size: 1.2rem; font-weight: 750; margin: 0.8rem 0 0.5rem; }
    .insight-box { border-left: 5px solid #20a464; background: white; padding: 1rem 1.1rem; border-radius: 0 12px 12px 0; box-shadow: 0 2px 10px rgba(0,0,0,.04); }
    .recommendation-box { border-left: 5px solid #f1b72b; background: #fffdf5; padding: 1rem 1.1rem; border-radius: 0 12px 12px 0; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #dcebe3; padding: 0.8rem; border-radius: 13px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
DATA_FILE = "data_clean.csv"
if not os.path.exists(DATA_FILE):
    alt = "/mnt/data/data_clean.csv"
    if os.path.exists(alt):
        DATA_FILE = alt
    else:
        st.error("File data_clean.csv tidak ditemukan. Letakkan file CSV di folder yang sama dengan aplikasi.")
        st.stop()

df = pd.read_csv(DATA_FILE)

# Normalize date
df["waktu_pesanan_dibuat"] = pd.to_datetime(df["waktu_pesanan_dibuat"], errors="coerce")

# Clean numeric columns
numeric_cols = [
    "total_qty", "total_weight_gr", "total_returned_qty", "total_diskon",
    "ongkos_kirim_dibayar_oleh_pembeli", "estimasi_potongan_biaya_pengiriman",
    "total_pembayaran", "perkiraan_ongkos_kirim"
]
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# Group detailed order statuses into readable business groups
status_raw = df["status_pesanan"].fillna("").astype(str)
df["status_group"] = np.select(
    [
        status_raw.str.contains(r"^Batal", case=False, regex=True),
        status_raw.eq("Selesai"),
    ],
    ["Batal", "Selesai"],
    default="Dalam Proses"
)

df["tanggal"] = df["waktu_pesanan_dibuat"].dt.date
df["bulan"] = df["waktu_pesanan_dibuat"].dt.to_period("M").astype(str)
df["jam"] = df["waktu_pesanan_dibuat"].dt.hour

# ---------- Helper ----------
def rupiah(value):
    try:
        return "Rp {:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return "Rp 0"

def pct(value):
    return "{:.1f}%".format(float(value))

# ---------- Header ----------
st.markdown('<div class="dashboard-title">📊 Big Data Exploration & Data Insight</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dashboard-subtitle">Dashboard eksplorasi data transaksi untuk melihat performa penjualan, '
    'perilaku pesanan, distribusi kategori, dan peluang pengambilan keputusan.</div>',
    unsafe_allow_html=True
)

# ---------- Sidebar filters ----------
st.sidebar.header("🔎 Filter Data")

min_date = df["waktu_pesanan_dibuat"].min()
max_date = df["waktu_pesanan_dibuat"].max()

if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input(
        "Rentang tanggal",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )
else:
    date_range = None

def multi_filter(label, col):
    options = sorted(df[col].dropna().astype(str).unique().tolist())
    return st.sidebar.multiselect(label, options, default=[])

selected_categories = multi_filter("Kategori produk", "product_categories")
selected_provinces = multi_filter("Provinsi", "provinsi")
selected_status = multi_filter("Status pesanan", "status_group")
selected_payment = multi_filter("Metode pembayaran", "metode_pembayaran")

filtered = df.copy()

# Date filter only applies to rows with valid dates.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        filtered["waktu_pesanan_dibuat"].isna()
        | (
            (filtered["waktu_pesanan_dibuat"].dt.date >= start)
            & (filtered["waktu_pesanan_dibuat"].dt.date <= end)
        )
    ]

if selected_categories:
    filtered = filtered[filtered["product_categories"].astype(str).isin(selected_categories)]
if selected_provinces:
    filtered = filtered[filtered["provinsi"].astype(str).isin(selected_provinces)]
if selected_status:
    filtered = filtered[filtered["status_group"].isin(selected_status)]
if selected_payment:
    filtered = filtered[filtered["metode_pembayaran"].astype(str).isin(selected_payment)]

# ---------- KPI utama ----------
orders = filtered["order_id"].nunique()
revenue = filtered["total_pembayaran"].sum()
avg_order_value = revenue / orders if orders else 0
cancel_rate = (filtered["status_group"].eq("Batal").mean() * 100) if len(filtered) else 0
returned_qty = filtered["total_returned_qty"].sum()
total_qty = filtered["total_qty"].sum()
return_rate = (returned_qty / total_qty * 100) if total_qty else 0

st.markdown('<div class="section-title">KPI Utama</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Pesanan", f"{orders:,}".replace(",", "."))
c2.metric("Total Pembayaran", rupiah(revenue))
c3.metric("Rata-rata / Pesanan", rupiah(avg_order_value))
c4.metric("Tingkat Pembatalan", pct(cancel_rate))
c5.metric("Tingkat Retur Qty", pct(return_rate))

st.caption(f"Menampilkan {len(filtered):,} baris data setelah filter.".replace(",", "."))

# ---------- Trend + comparison ----------
st.markdown('<div class="section-title">Grafik Tren / Perbandingan</div>', unsafe_allow_html=True)
left, right = st.columns(2)

valid_dates = filtered.dropna(subset=["waktu_pesanan_dibuat"]).copy()

with left:
    if len(valid_dates):
        monthly = (
            valid_dates.groupby(valid_dates["waktu_pesanan_dibuat"].dt.to_period("M"))
            .agg(pesanan=("order_id", "nunique"), pembayaran=("total_pembayaran", "sum"))
            .reset_index()
        )
        monthly["bulan"] = monthly["waktu_pesanan_dibuat"].astype(str)
        fig = px.line(
            monthly, x="bulan", y="pembayaran", markers=True,
            labels={"bulan": "Bulan", "pembayaran": "Total Pembayaran"},
            title="Tren Total Pembayaran per Bulan"
        )
        fig.update_layout(margin=dict(l=10,r=10,t=55,b=10), height=350)
        fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data bertanggal untuk grafik tren.")

with right:
    cat = (
        filtered.groupby("product_categories")
        .agg(pesanan=("order_id", "nunique"), pembayaran=("total_pembayaran", "sum"))
        .sort_values("pembayaran", ascending=False)
        .head(10)
        .reset_index()
    )
    if len(cat):
        fig2 = px.bar(
            cat.sort_values("pembayaran"),
            x="pembayaran", y="product_categories", orientation="h",
            labels={"product_categories":"Kategori Produk", "pembayaran":"Total Pembayaran"},
            title="Top 10 Kategori berdasarkan Total Pembayaran"
        )
        fig2.update_layout(margin=dict(l=10,r=10,t=55,b=10), height=350)
        fig2.update_xaxes(tickprefix="Rp ", separatethousands=True)
        st.plotly_chart(fig2, use_container_width=True)

# ---------- Additional comparison ----------
col_a, col_b = st.columns(2)
with col_a:
    prov = (
        filtered.groupby("provinsi")
        .agg(pesanan=("order_id","nunique"), pembayaran=("total_pembayaran","sum"))
        .sort_values("pembayaran", ascending=False)
        .head(8)
        .reset_index()
    )
    if len(prov):
        fig3 = px.bar(
            prov.sort_values("pembayaran"),
            x="pembayaran", y="provinsi", orientation="h",
            title="8 Provinsi dengan Pembayaran Tertinggi",
            labels={"provinsi":"Provinsi","pembayaran":"Total Pembayaran"}
        )
        fig3.update_layout(margin=dict(l=10,r=10,t=55,b=10), height=330)
        fig3.update_xaxes(tickprefix="Rp ", separatethousands=True)
        st.plotly_chart(fig3, use_container_width=True)

with col_b:
    pay = (
        filtered.groupby("metode_pembayaran")
        .agg(pesanan=("order_id","nunique"), pembayaran=("total_pembayaran","sum"))
        .sort_values("pesanan", ascending=False)
        .head(8)
        .reset_index()
    )
    if len(pay):
        fig4 = px.bar(
            pay.sort_values("pesanan"),
            x="pesanan", y="metode_pembayaran", orientation="h",
            title="Metode Pembayaran berdasarkan Jumlah Pesanan",
            labels={"metode_pembayaran":"Metode Pembayaran","pesanan":"Jumlah Pesanan"}
        )
        fig4.update_layout(margin=dict(l=10,r=10,t=55,b=10), height=330)
        st.plotly_chart(fig4, use_container_width=True)

# ---------- Interpretation ----------
top_cat = filtered.groupby("product_categories")["total_pembayaran"].sum().sort_values(ascending=False)
top_prov = filtered.groupby("provinsi")["total_pembayaran"].sum().sort_values(ascending=False)

cat_text = f'Kategori dengan kontribusi pembayaran terbesar adalah <b>{top_cat.index[0]}</b> dengan total {rupiah(top_cat.iloc[0])}.' if len(top_cat) else "Belum ada kategori yang dapat dianalisis."
prov_text = f'Provinsi dengan pembayaran tertinggi adalah <b>{top_prov.index[0]}</b> dengan total {rupiah(top_prov.iloc[0])}.' if len(top_prov) else "Belum ada provinsi yang dapat dianalisis."

interpretation = (
    f"Data terfilter menghasilkan <b>{orders:,}</b> pesanan dengan total pembayaran "
    f"<b>{rupiah(revenue)}</b> dan rata-rata nilai pesanan <b>{rupiah(avg_order_value)}</b>. "
    f"Tingkat pembatalan berada di <b>{pct(cancel_rate)}</b>, sedangkan tingkat retur berdasarkan kuantitas "
    f"sebesar <b>{pct(return_rate)}</b>. {cat_text} {prov_text}"
).replace(",", ".")

st.markdown('<div class="section-title">Interpretasi Singkat</div>', unsafe_allow_html=True)
st.markdown(f'<div class="insight-box">{interpretation}</div>', unsafe_allow_html=True)

# ---------- Recommendations ----------
recs = []
if cancel_rate >= 10:
    recs.append("Prioritaskan analisis alasan pembatalan dan evaluasi proses pembayaran/pengiriman karena proporsi pembatalan relatif tinggi.")
else:
    recs.append("Pertahankan proses fulfillment yang ada sambil memantau alasan pembatalan pada kategori atau wilayah tertentu.")
if len(top_cat):
    recs.append(f"Fokuskan stok dan promosi pada kategori <b>{top_cat.index[0]}</b>, tetapi cek margin sebelum meningkatkan persediaan secara agresif.")
if len(top_prov):
    recs.append(f"Optimalkan kampanye dan ongkos kirim di <b>{top_prov.index[0]}</b> karena wilayah tersebut memberikan kontribusi pembayaran terbesar.")
recs.append("Gunakan filter kategori, provinsi, dan metode pembayaran secara berkala untuk menemukan segmen yang mengalami penurunan performa.")

st.markdown('<div class="section-title">Rekomendasi Awal</div>', unsafe_allow_html=True)
st.markdown('<div class="recommendation-box">' + "<br><br>".join(f"• {x}" for x in recs) + '</div>', unsafe_allow_html=True)

# ---------- Data preview ----------
with st.expander("Lihat data terfilter"):
    show_cols = [c for c in [
        "order_id","product_categories","status_group","metode_pembayaran",
        "kota_kabupaten","provinsi","total_qty","total_pembayaran","total_diskon",
        "total_returned_qty","waktu_pesanan_dibuat"
    ] if c in filtered.columns]
    st.dataframe(filtered[show_cols], use_container_width=True, height=420)

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download data terfilter (CSV)",
        data=csv_bytes,
        file_name="data_terfilter.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Fundamental Big Data • Project 1 — Big Data Exploration & Data Insight")
