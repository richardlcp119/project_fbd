import pandas as pd
import streamlit as st


def _multiselect(label, df, column):
    if column not in df.columns:
        return []
    options = sorted(df[column].dropna().astype(str).unique().tolist())
    return st.sidebar.multiselect(label, options, default=[])


def render_sidebar_filters(df):
    st.sidebar.header("🔎 Filter Data")

    min_date = df["waktu_pesanan_dibuat"].min()
    max_date = df["waktu_pesanan_dibuat"].max()

    date_range = None
    if pd.notna(min_date) and pd.notna(max_date):
        date_range = st.sidebar.date_input(
            "Rentang tanggal",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )

    return {
        "date_range": date_range,
        "categories": _multiselect("Kategori produk", df, "product_categories"),
        "provinces": _multiselect("Provinsi", df, "provinsi"),
        "status": _multiselect("Status pesanan", df, "status_group"),
        "payment": _multiselect("Metode pembayaran", df, "metode_pembayaran"),
    }


def apply_filters(df, filters):
    filtered = df.copy()

    date_range = filters.get("date_range")
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        valid_date = filtered["waktu_pesanan_dibuat"].isna()
        valid_date |= (
            (filtered["waktu_pesanan_dibuat"].dt.date >= start)
            & (filtered["waktu_pesanan_dibuat"].dt.date <= end)
        )
        filtered = filtered[valid_date]

    if filters.get("categories"):
        filtered = filtered[
            filtered["product_categories"].astype(str).isin(filters["categories"])
        ]

    if filters.get("provinces"):
        filtered = filtered[
            filtered["provinsi"].astype(str).isin(filters["provinces"])
        ]

    if filters.get("status"):
        filtered = filtered[filtered["status_group"].isin(filters["status"])]

    if filters.get("payment"):
        filtered = filtered[
            filtered["metode_pembayaran"].astype(str).isin(filters["payment"])
        ]

    return filtered
