import plotly.express as px
import streamlit as st


def render_trend_chart(df):
    valid_dates = df.dropna(subset=["waktu_pesanan_dibuat"]).copy()

    if valid_dates.empty:
        st.info("Tidak ada data bertanggal untuk grafik tren.")
        return

    monthly = (
        valid_dates.groupby(valid_dates["waktu_pesanan_dibuat"].dt.to_period("M"))
        .agg(
            pesanan=("order_id", "nunique"),
            pembayaran=("total_pembayaran", "sum"),
        )
        .reset_index()
    )
    monthly["bulan"] = monthly["waktu_pesanan_dibuat"].astype(str)

    fig = px.line(
        monthly,
        x="bulan",
        y="pembayaran",
        markers=True,
        labels={"bulan": "Bulan", "pembayaran": "Total Pembayaran"},
        title="Tren Total Pembayaran per Bulan",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=350)
    fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)


def render_category_chart(df):
    category = (
        df.groupby("product_categories")
        .agg(
            pesanan=("order_id", "nunique"),
            pembayaran=("total_pembayaran", "sum"),
        )
        .sort_values("pembayaran", ascending=False)
        .head(10)
        .reset_index()
    )

    if category.empty:
        st.info("Tidak ada kategori yang dapat divisualisasikan.")
        return

    fig = px.bar(
        category.sort_values("pembayaran"),
        x="pembayaran",
        y="product_categories",
        orientation="h",
        labels={
            "product_categories": "Kategori Produk",
            "pembayaran": "Total Pembayaran",
        },
        title="Top 10 Kategori berdasarkan Total Pembayaran",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=350)
    fig.update_xaxes(tickprefix="Rp ", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)


def render_province_chart(df):
    province = (
        df.groupby("provinsi")
        .agg(
            pesanan=("order_id", "nunique"),
            pembayaran=("total_pembayaran", "sum"),
        )
        .sort_values("pembayaran", ascending=False)
        .head(8)
        .reset_index()
    )

    if province.empty:
        return

    fig = px.bar(
        province.sort_values("pembayaran"),
        x="pembayaran",
        y="provinsi",
        orientation="h",
        title="8 Provinsi dengan Pembayaran Tertinggi",
        labels={"provinsi": "Provinsi", "pembayaran": "Total Pembayaran"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=330)
    fig.update_xaxes(tickprefix="Rp ", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)


def render_payment_chart(df):
    payment = (
        df.groupby("metode_pembayaran")
        .agg(
            pesanan=("order_id", "nunique"),
            pembayaran=("total_pembayaran", "sum"),
        )
        .sort_values("pesanan", ascending=False)
        .head(8)
        .reset_index()
    )

    if payment.empty:
        return

    fig = px.bar(
        payment.sort_values("pesanan"),
        x="pesanan",
        y="metode_pembayaran",
        orientation="h",
        title="Metode Pembayaran berdasarkan Jumlah Pesanan",
        labels={
            "metode_pembayaran": "Metode Pembayaran",
            "pesanan": "Jumlah Pesanan",
        },
    )
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=330)
    st.plotly_chart(fig, use_container_width=True)
