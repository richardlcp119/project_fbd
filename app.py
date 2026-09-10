import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

# MENGGUNAKAN FILE SESUAI LAPORAN (Tingkat Pesanan)
DATA_FILE = "data_pesanan_bersih.csv"

# Fungsi standardisasi format Bulan (YYYY-MM) dari periode_analisis
def parse_periode(val):
    if pd.isna(val):
        return np.nan
    val_str = str(val).strip().split(' ')[0] 
    if '/' in val_str:
        # Menangani format M/D/YYYY
        parts = val_str.split('/')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[0].zfill(2)}" 
    elif '-' in val_str:
        # Menangani format YYYY-MM
        parts = val_str.split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1].zfill(2)}"
    return np.nan

# LOAD DATA & PREPROCESSING
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    # Hanya gunakan periode_analisis sebagai patokan waktu yang valid
    if "periode_analisis" in df.columns:
        df["periode_bersih"] = df["periode_analisis"].apply(parse_periode)
    else:
        df["periode_bersih"] = pd.NaT

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
        return f"File {DATA_FILE} tidak ditemukan atau kosong."

    cat_filter = request.args.get('category', '')
    prov_filter = request.args.get('province', '')
    start_month = request.args.get('start_month', '')
    end_month = request.args.get('end_month', '')

    filtered_df = df.copy()

    # Filter Provinsi
    if prov_filter and "Provinsi" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Provinsi'] == prov_filter]
    
    # Filter Multi-Kategori
    if cat_filter and "kategori_dalam_pesanan" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['kategori_dalam_pesanan'].str.contains(cat_filter, na=False, regex=False)]
        
    # Filter Rentang Waktu (HANYA BULAN & TAHUN)
    if start_month and "periode_bersih" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["periode_bersih"] >= start_month]
    if end_month and "periode_bersih" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["periode_bersih"] <= end_month]

    df_selesai = filtered_df[filtered_df["status_kelompok"] == "Selesai"] if "status_kelompok" in filtered_df.columns else pd.DataFrame()

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

    def get_cat_options():
        if "kategori_dalam_pesanan" in df.columns:
            all_cats = df["kategori_dalam_pesanan"].dropna().str.split(r'\s*\|\s*').explode()
            return sorted(all_cats.unique().tolist())
        return []

    def get_options(col_name):
        if col_name in df.columns:
            return sorted(df[col_name].dropna().astype(str).unique().tolist())
        return []

    # Ambil nilai minimum dan maksimum bulan untuk batas input di frontend
    if not df["periode_bersih"].dropna().empty:
        min_month = df["periode_bersih"].dropna().min()
        max_month = df["periode_bersih"].dropna().max()
    else:
        min_month, max_month = '', ''

    filters = {
        "categories": get_cat_options(),
        "provinces": get_options("Provinsi"),
        "min_month": min_month,
        "max_month": max_month
    }

    # AGREGASI DATA GRAFIK
    
    # 1. Tren Pembayaran & Jumlah Pesanan Bulanan
    valid_df = df_selesai.copy().dropna(subset=["periode_bersih"])
    
    if not valid_df.empty:
        monthly = valid_df.groupby("periode_bersih").agg({
            "total_pembayaran_rp": "sum",
            "order_id": "nunique"
        }).reset_index()
        
        monthly = monthly.sort_values("periode_bersih")
        
        trend_labels = monthly["periode_bersih"].tolist()
        trend_revenue = monthly["total_pembayaran_rp"].tolist()
        trend_orders = monthly["order_id"].tolist()
    else:
        trend_labels, trend_revenue, trend_orders = [], [], []

    # 2. Kategori Produk Top 10
    if not df_selesai.empty and "kategori_dalam_pesanan" in df_selesai.columns:
        cat_df = df_selesai.copy()
        cat_df['kategori_split'] = cat_df['kategori_dalam_pesanan'].str.split(r'\s*\|\s*')
        cat_df = cat_df.explode('kategori_split')
        cat = cat_df.groupby("kategori_split")["order_id"].nunique().sort_values(ascending=False).head(10)
    else:
        cat = pd.Series()

    # 3. Provinsi Top 10
    prov = df_selesai.groupby("Provinsi")["total_pembayaran_rp"].sum().sort_values(ascending=False).head(10) if "Provinsi" in df_selesai.columns else pd.Series()
    
    # 4. Metode Pembayaran
    pay = filtered_df.groupby("Metode Pembayaran")["order_id"].nunique().sort_values(ascending=False).head(10) if "Metode Pembayaran" in filtered_df.columns else pd.Series()
    
    # 5. Opsi Pengiriman
    ship = filtered_df.groupby("Opsi Pengiriman")["order_id"].nunique().sort_values(ascending=False).head(10) if "Opsi Pengiriman" in filtered_df.columns else pd.Series()

    # 6. Status Pesanan (Keseluruhan)
    status = filtered_df.groupby("status_kelompok")["order_id"].nunique().sort_values(ascending=False) if "status_kelompok" in filtered_df.columns else pd.Series()

    # 7. Alasan Pembatalan
    df_batal = filtered_df[filtered_df["status_kelompok"] == "Batal"] if "status_kelompok" in filtered_df.columns else pd.DataFrame()

    if "alasan_pembatalan_analisis" in df_batal.columns:
        cancel = df_batal.groupby("alasan_pembatalan_analisis")["order_id"].nunique().sort_values(ascending=False).head(5)
        # Memotong string teks yang panjang, hanya mengambil inti alasan setelah "Alasan:"
        cancel.index = cancel.index.astype(str).str.split('Alasan:').str[-1].str.strip()
    else:
        cancel = pd.Series()

    charts = {
        "trend": {"labels": trend_labels, "revenue": trend_revenue, "orders": trend_orders},
        "category": {"labels": cat.index.tolist(), "data": cat.values.tolist()},
        "province": {"labels": prov.index.tolist(), "data": prov.values.tolist()},
        "payment": {"labels": pay.index.tolist(), "data": pay.values.tolist()},
        "shipping": {"labels": ship.index.tolist(), "data": ship.values.tolist()},
        "status": {"labels": status.index.tolist(), "data": status.values.tolist()},
        "cancel": {"labels": cancel.index.tolist(), "data": cancel.values.tolist()}
    }

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