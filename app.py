import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

# ---------- Memuat dan Membersihkan Data ----------
DATA_FILE = "data_clean.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    # Normalisasi tanggal (menggunakan kolom baru: 'waktu_pesanan')
    if "waktu_pesanan" in df.columns:
        df["waktu_pesanan_dibuat"] = pd.to_datetime(df["waktu_pesanan"], errors="coerce")
    else:
        df["waktu_pesanan_dibuat"] = pd.NaT

    # Normalisasi kolom numerik sesuai dataset baru
    numeric_cols = [
        "jumlah_item_tercatat", "berat_pesanan_gr", "jumlah_retur", 
        "diskon_nilai_asli", "ongkir_pembeli_nilai_asli", 
        "estimasi_ongkir_nilai_asli", "total_pembayaran_rp"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            
    # Menggunakan status kelompok bawaan dari dataset baru jika ada
    if "status_kelompok" not in df.columns and "Status Pesanan" in df.columns:
        status_raw = df["Status Pesanan"].fillna("").astype(str)
        df["status_kelompok"] = np.select(
            [status_raw.str.contains(r"^Batal", case=False, regex=True), status_raw.eq("Selesai")],
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
        return "File data_clean.csv tidak ditemukan atau kosong."

    # ----- 1. Tangkap Parameter Filter -----
    cat_filter = request.args.get('category', '')
    prov_filter = request.args.get('province', '')
    stat_filter = request.args.get('status', '')
    pay_filter = request.args.get('payment', '')

    filtered_df = df.copy()

    # Filter berdasarkan kolom baru
    if cat_filter and "kategori_dalam_pesanan" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['kategori_dalam_pesanan'] == cat_filter]
    if prov_filter and "Provinsi" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Provinsi'] == prov_filter]
    if stat_filter and "status_kelompok" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status_kelompok'] == stat_filter]
    if pay_filter and "Metode Pembayaran" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Metode Pembayaran'] == pay_filter]

    # ----- 2. Hitung KPI -----
    orders = filtered_df["order_id"].nunique() if "order_id" in filtered_df.columns else 0
    revenue = filtered_df["total_pembayaran_rp"].sum() if "total_pembayaran_rp" in filtered_df.columns else 0
    avg_order_value = revenue / orders if orders else 0
    
    cancel_rate = 0
    if "status_kelompok" in filtered_df.columns and len(filtered_df) > 0:
        cancel_rate = (filtered_df["status_kelompok"].eq("Batal").mean() * 100)

    returned_qty = filtered_df["jumlah_retur"].sum() if "jumlah_retur" in filtered_df.columns else 0
    total_qty = filtered_df["jumlah_item_tercatat"].sum() if "jumlah_item_tercatat" in filtered_df.columns else 0
    return_rate = (returned_qty / total_qty * 100) if total_qty else 0

    kpi_data = {
        "orders": f"{orders:,}".replace(",", "."),
        "revenue": rupiah(revenue),
        "avg_order": rupiah(avg_order_value),
        "cancel_rate": "{:.1f}%".format(cancel_rate),
        "return_rate": "{:.1f}%".format(return_rate)
    }

    # ----- 3. Opsi Dropdown Filter -----
    def get_options(col_name):
        if col_name in df.columns:
            return sorted(df[col_name].dropna().astype(str).unique().tolist())
        return []

    filters = {
        "categories": get_options("kategori_dalam_pesanan"),
        "provinces": get_options("Provinsi"),
        "statuses": get_options("status_kelompok"),
        "payments": get_options("Metode Pembayaran")
    }

    # ----- 4. Data Grafik -----
    valid_dates = filtered_df.dropna(subset=["waktu_pesanan_dibuat"]).copy()
    if not valid_dates.empty:
        monthly = valid_dates.groupby(valid_dates["waktu_pesanan_dibuat"].dt.to_period("M"))["total_pembayaran_rp"].sum().reset_index()
        trend_labels = monthly["waktu_pesanan_dibuat"].astype(str).tolist()
        trend_data = monthly["total_pembayaran_rp"].tolist()
    else:
        trend_labels, trend_data = [], []

    cat = filtered_df.groupby("kategori_dalam_pesanan")["total_pembayaran_rp"].sum().sort_values(ascending=False).head(10) if "kategori_dalam_pesanan" in filtered_df.columns else pd.Series()
    prov = filtered_df.groupby("Provinsi")["total_pembayaran_rp"].sum().sort_values(ascending=False).head(8) if "Provinsi" in filtered_df.columns else pd.Series()
    pay = filtered_df.groupby("Metode Pembayaran")["order_id"].nunique().sort_values(ascending=False).head(8) if "Metode Pembayaran" in filtered_df.columns else pd.Series()

    charts = {
        "trend": {"labels": trend_labels, "data": trend_data},
        "category": {"labels": cat.index.tolist(), "data": cat.values.tolist()},
        "province": {"labels": prov.index.tolist(), "data": prov.values.tolist()},
        "payment": {"labels": pay.index.tolist(), "data": pay.values.tolist()}
    }

    # ----- 5. Interpretasi & Rekomendasi -----
    top_cat_name = cat.index[0] if not cat.empty else "Belum ada data"
    top_cat_val = rupiah(cat.iloc[0]) if not cat.empty else "Rp 0"
    
    top_prov_name = prov.index[0] if not prov.empty else "Belum ada data"

    if cancel_rate >= 10:
        rec_text = "Prioritaskan analisis alasan pembatalan dan evaluasi proses karena proporsi pembatalan relatif tinggi (di atas 10% detik)."
        rec_color = "var(--ios-red)"
    else:
        rec_text = "Pertahankan proses fulfillment yang ada. Tingkat pembatalan masih dalam batas aman."
        rec_color = "var(--ios-green)"

    insights = {
        "top_category": top_cat_name,
        "top_category_val": top_cat_val,
        "top_province": top_prov_name,
        "recommendation": rec_text,
        "rec_color": rec_color
    }

    return render_template('dashboard.html', kpi=kpi_data, filters=filters, charts=charts, insights=insights)

if __name__ == '__main__':
    app.run(debug=True)