import os
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

# ---------- Memuat dan Membersihkan Data ----------
DATA_FILE = "data_clean.csv"

# Inisialisasi DataFrame global
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    # Normalisasi tanggal
    df["waktu_pesanan_dibuat"] = pd.to_datetime(df["waktu_pesanan_dibuat"], errors="coerce")
    
    # Normalisasi kolom numerik
    numeric_cols = [
        "total_qty", "total_weight_gr", "total_returned_qty", "total_diskon",
        "ongkos_kirim_dibayar_oleh_pembeli", "estimasi_potongan_biaya_pengiriman",
        "total_pembayaran", "perkiraan_ongkos_kirim"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            
    # Pengelompokan status pesanan
    status_raw = df["status_pesanan"].fillna("").astype(str)
    df["status_group"] = np.select(
        [
            status_raw.str.contains(r"^Batal", case=False, regex=True),
            status_raw.eq("Selesai"),
        ],
        ["Batal", "Selesai"],
        default="Dalam Proses"
    )
else:
    df = pd.DataFrame()

# Fungsi format Rupiah
def rupiah(value):
    try:
        return "Rp {:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return "Rp 0"

@app.route('/')
def index():
    if df.empty:
        return "File data_clean.csv tidak ditemukan atau kosong. Pastikan file ada di direktori yang sama dengan app1.py"

    # ==========================================
    # 1. Menghitung KPI (Data Keseluruhan)
    # ==========================================
    orders = df["order_id"].nunique() if "order_id" in df.columns else 0
    revenue = df["total_pembayaran"].sum() if "total_pembayaran" in df.columns else 0
    avg_order_value = revenue / orders if orders else 0
    cancel_rate = (df["status_group"].eq("Batal").mean() * 100) if len(df) else 0
    returned_qty = df["total_returned_qty"].sum() if "total_returned_qty" in df.columns else 0
    total_qty = df["total_qty"].sum() if "total_qty" in df.columns else 0
    return_rate = (returned_qty / total_qty * 100) if total_qty else 0

    kpi_data = {
        "orders": f"{orders:,}".replace(",", "."),
        "revenue": rupiah(revenue),
        "avg_order": rupiah(avg_order_value),
        "cancel_rate": "{:.1f}%".format(cancel_rate),
        "return_rate": "{:.1f}%".format(return_rate)
    }

    # ==========================================
    # 2. Menyiapkan Opsi untuk Dropdown Filter
    # ==========================================
    def get_options(col_name):
        if col_name in df.columns:
            return sorted(df[col_name].dropna().astype(str).unique().tolist())
        return []

    filters = {
        "categories": get_options("product_categories"),
        "provinces": get_options("provinsi"),
        "statuses": get_options("status_group"),
        "payments": get_options("metode_pembayaran")
    }

    # ==========================================
    # 3. Menyiapkan Data Grafik (Chart.js)
    # ==========================================
    # A. Tren Pembayaran per Bulan
    valid_dates = df.dropna(subset=["waktu_pesanan_dibuat"]).copy()
    if not valid_dates.empty:
        monthly = valid_dates.groupby(valid_dates["waktu_pesanan_dibuat"].dt.to_period("M"))["total_pembayaran"].sum().reset_index()
        trend_labels = monthly["waktu_pesanan_dibuat"].astype(str).tolist()
        trend_data = monthly["total_pembayaran"].tolist()
    else:
        trend_labels, trend_data = [], []

    # B. Top 10 Kategori by Revenue
    cat = df.groupby("product_categories")["total_pembayaran"].sum().sort_values(ascending=False).head(10)
    
    # C. Top 8 Provinsi by Revenue
    prov = df.groupby("provinsi")["total_pembayaran"].sum().sort_values(ascending=False).head(8)
    
    # D. Metode Pembayaran by Jumlah Pesanan
    pay = df.groupby("metode_pembayaran")["order_id"].nunique().sort_values(ascending=False).head(8)

    charts = {
        "trend": {"labels": trend_labels, "data": trend_data},
        "category": {"labels": cat.index.tolist(), "data": cat.values.tolist()},
        "province": {"labels": prov.index.tolist(), "data": prov.values.tolist()},
        "payment": {"labels": pay.index.tolist(), "data": pay.values.tolist()}
    }

    return render_template('dashboard.html', kpi=kpi_data, filters=filters, charts=charts)

if __name__ == '__main__':
    app.run(debug=True)