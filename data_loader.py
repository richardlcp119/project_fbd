import numpy as np
import pandas as pd
import streamlit as st


NUMERIC_COLUMNS = [
    "total_qty",
    "total_weight_gr",
    "total_returned_qty",
    "total_diskon",
    "ongkos_kirim_dibayar_oleh_pembeli",
    "estimasi_potongan_biaya_pengiriman",
    "total_pembayaran",
    "perkiraan_ongkos_kirim",
]


@st.cache_data
def load_data(data_file):
    if not data_file.exists():
        st.error(
            "File data_clean.csv tidak ditemukan. "
            "Letakkan file CSV di folder yang sama dengan app.py."
        )
        st.stop()

    df = pd.read_csv(data_file)

    if "waktu_pesanan_dibuat" in df.columns:
        df["waktu_pesanan_dibuat"] = pd.to_datetime(
            df["waktu_pesanan_dibuat"], errors="coerce"
        )

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    if "status_pesanan" in df.columns:
        status_raw = df["status_pesanan"].fillna("").astype(str)
        df["status_group"] = np.select(
            [
                status_raw.str.contains(r"^Batal", case=False, regex=True),
                status_raw.eq("Selesai"),
            ],
            ["Batal", "Selesai"],
            default="Dalam Proses",
        )
    else:
        df["status_group"] = "Tidak Diketahui"

    if "waktu_pesanan_dibuat" in df.columns:
        df["tanggal"] = df["waktu_pesanan_dibuat"].dt.date
        df["bulan"] = df["waktu_pesanan_dibuat"].dt.to_period("M").astype(str)
        df["jam"] = df["waktu_pesanan_dibuat"].dt.hour

    return df
