import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

DATA_FILE = "data_clean.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    if "waktu_pesanan" in df.columns:
        df["waktu_pesanan_dibuat"] = pd.to_datetime(df["waktu_pesanan"], errors="coerce")
    else:
        df["waktu_pesanan_dibuat"] = pd.NaT

    numeric_cols = [
        "jumlah_item_tercatat", "berat_pesanan_gr", "jumlah_retur", 
        "diskon_nilai_asli", "ongkir_pembeli_nilai_asli", 
        "estimasi_ongkir_nilai_asli", "total_pembayaran_rp"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            
    if "status_kelompok" not in df.columns and "Status Pesanan" in df.columns:
        status_raw = df["Status Pesanan"].fillna("").astype(str)
        df["status_kelompok"] = np.select(
            [status_raw.str.contains(r"^Batal", case=False, regex=True), status_raw.eq("Selesai")],
            ["Batal", "Selesai"],
            default="Dalam Proses"
        )
else:
    df = pd.DataFrame()

def rupiah(value):
    try:
        return "Rp {:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return "Rp 0"

@app.route('/')
def index():
    if df.empty:
        return "File data_clean.csv tidak ditemukan atau kosong."

    cat_filter = request.args.get('category', '')
    prov_filter = request.args.get('province', '')
    stat_filter = request.args.get('status', '')
    pay_filter = request.args.get('payment', '')

    filtered_df = df.copy()

    # Terapkan filter dari dropdown (kecuali filter kategori karena multi-value)
    if prov_filter and "Provinsi" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Provinsi'] == prov_filter]
    if stat_filter and "status_kelompok" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status_kelompok'] == stat_filter]
    if pay_filter and "Metode Pembayaran" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Metode Pembayaran'] == pay_filter]
    
    # Filter multi-kategori (memeriksa string mengandung kategori)
    if cat_filter and "kategori_dalam_pesanan" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['kategori_dalam_pesanan'].str.contains(cat_filter, na=False, regex=False)]

    # Pisahkan dataset khusus Selesai untuk metrik keuangan
    df_selesai = filtered_df[filtered_df["status_kelompok"] == "Selesai"] if "status_kelompok" in filtered_df.columns else pd.DataFrame()

    # Hitung KPI Sesuai Laporan
    orders = filtered_df["order_id"].nunique() if "order_id" in filtered_df.columns else 0
    orders_selesai = df_selesai["order_id"].nunique() if "order_id" in df_selesai.columns else 0
    revenue_selesai = df_selesai["total_pembayaran_rp"].sum() if "total_pembayaran_rp" in df_selesai.columns else 0
    avg_order_value = revenue_selesai / orders_selesai if orders_selesai else 0
    
    cancel_rate = 0
    if "status_kelompok" in filtered_df.columns and len(filtered_df) > 0:
        cancel_rate = (filtered_df["status_kelompok"].eq("Batal").mean() * 100)

    kpi_data = {
        "orders": f"{orders:,}".replace(",", "."),
        "orders_selesai": f"{orders_selesai:,}".replace(",", "."),
        "revenue": rupiah(revenue_selesai),
        "avg_order": rupiah(avg_order_value),
        "cancel_rate": "{:.1f}%".format(cancel_rate)
    }

    # Opsi Filter Khusus Kategori (Harus di-explode agar muncul rapi di opsi tunggal)
    def get_cat_options():
        if "kategori_dalam_pesanan" in df.columns:
            all_cats = df["kategori_dalam_pesanan"].dropna().str.split(r'\s*\|\s*').explode()
            return sorted(all_cats.unique().tolist())
        return []

    def get_options(col_name):
        if col_name in df.columns:
            return sorted(df[col_name].dropna().astype(str).unique().tolist())
        return []

    filters = {
        "categories": get_cat_options(),
        "provinces": get_options("Provinsi"),
        "statuses": get_options("status_kelompok"),
        "payments": get_options("Metode Pembayaran")
    }

    # Visualisasi 1: Tren Pembayaran (Hanya Pesanan Selesai)
    valid_dates = df_selesai.dropna(subset=["waktu_pesanan_dibuat"]).copy()
    if not valid_dates.empty:
        monthly = valid_dates.groupby(valid_dates["waktu_pesanan_dibuat"].dt.to_period("M"))["total_pembayaran_rp"].sum().reset_index()
        trend_labels = monthly["waktu_pesanan_dibuat"].astype(str).tolist()
        trend_data = monthly["total_pembayaran_rp"].tolist()
    else:
        trend_labels, trend_data = [], []

    # Visualisasi 2: Kategori Teratas berdasar Frekuensi (Di-explode & Selesai)
    if not df_selesai.empty and "kategori_dalam_pesanan" in df_selesai.columns:
        cat_df = df_selesai.copy()
        cat_df['kategori_split'] = cat_df['kategori_dalam_pesanan'].str.split(r'\s*\|\s*')
        cat_df = cat_df.explode('kategori_split')
        cat = cat_df.groupby("kategori_split")["order_id"].nunique().sort_values(ascending=False).head(10)
    else:
        cat = pd.Series()

    # Visualisasi 3: Provinsi berdasar Pendapatan (Selesai)
    prov = df_selesai.groupby("Provinsi")["total_pembayaran_rp"].sum().sort_values(ascending=False).head(10) if "Provinsi" in df_selesai.columns else pd.Series()
    
    # Visualisasi 4: Metode Pembayaran (Semua Status)
    pay = filtered_df.groupby("Metode Pembayaran")["order_id"].nunique().sort_values(ascending=False).head(10) if "Metode Pembayaran" in filtered_df.columns else pd.Series()

    charts = {
        "trend": {"labels": trend_labels, "data": trend_data},
        "category": {"labels": cat.index.tolist(), "data": cat.values.tolist()},
        "province": {"labels": prov.index.tolist(), "data": prov.values.tolist()},
        "payment": {"labels": pay.index.tolist(), "data": pay.values.tolist()}
    }

    # Interpretasi (Disesuaikan agar teks kategori menghasilkan format angka/pesanan, bukan rupiah)
    top_cat_name = cat.index[0] if not cat.empty else "Belum ada data"
    top_cat_val = f"{cat.iloc[0]:,}".replace(",", ".") if not cat.empty else "0"
    
    top_prov_name = prov.index[0] if not prov.empty else "Belum ada data"
    top_prov_val = rupiah(prov.iloc[0]) if not prov.empty else "Rp 0"

    if cancel_rate >= 10:
        rec_text = "Prioritaskan analisis alasan pembatalan dan evaluasi proses karena proporsi pembatalan relatif tinggi (di atas 10%)."
        rec_color = "var(--ios-red)"
    else:
        rec_text = "Pertahankan proses fulfillment yang ada. Tingkat pembatalan masih dalam batas aman."
        rec_color = "var(--ios-green)"

    insights = {
        "top_category": top_cat_name,
        "top_category_val": top_cat_val,
        "top_province": top_prov_name,
        "top_province_val": top_prov_val,
        "recommendation": rec_text,
        "rec_color": rec_color
    }

    return render_template('dashboard.html', kpi=kpi_data, filters=filters, charts=charts, insights=insights)

if __name__ == '__main__':
    app.run(debug=True)