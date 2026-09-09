import streamlit as st


def rupiah(value):
    try:
        return "Rp {:,.0f}".format(float(value)).replace(",", ".")
    except Exception:
        return "Rp 0"


def pct(value):
    return "{:.1f}%".format(float(value))


def inject_css():
    st.markdown(
        '''
        <style>
            .main { background: #f6faf7; }
            .block-container { padding-top: 1.2rem; }
            .dashboard-title {
                color: #087443;
                font-size: 2.25rem;
                font-weight: 800;
                margin-bottom: 0.15rem;
            }
            .dashboard-subtitle {
                color: #4d6358;
                margin-bottom: 1.2rem;
            }
            .section-title {
                color: #087443;
                font-size: 1.2rem;
                font-weight: 750;
                margin: 0.8rem 0 0.5rem;
            }
            .insight-box {
                border-left: 5px solid #20a464;
                background: white;
                padding: 1rem 1.1rem;
                border-radius: 0 12px 12px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,.04);
            }
            .recommendation-box {
                border-left: 5px solid #f1b72b;
                background: #fffdf5;
                padding: 1rem 1.1rem;
                border-radius: 0 12px 12px 0;
            }
            div[data-testid="stMetric"] {
                background: white;
                border: 1px solid #dcebe3;
                padding: 0.8rem;
                border-radius: 13px;
                box-shadow: 0 2px 8px rgba(0,0,0,.04);
            }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        '<div class="dashboard-title">📊 Big Data Exploration & Data Insight</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Dashboard eksplorasi data transaksi untuk melihat performa penjualan, "
        "perilaku pesanan, distribusi kategori, dan peluang pengambilan keputusan."
        "</div>",
        unsafe_allow_html=True,
    )


def render_kpi_section(kpis, filtered_rows):
    st.markdown('<div class="section-title">KPI Utama</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Pesanan", f"{kpis['orders']:,}".replace(",", "."))
    c2.metric("Total Pembayaran", rupiah(kpis["revenue"]))
    c3.metric("Rata-rata / Pesanan", rupiah(kpis["avg_order_value"]))
    c4.metric("Tingkat Pembatalan", pct(kpis["cancel_rate"]))
    c5.metric("Tingkat Retur Qty", pct(kpis["return_rate"]))

    st.caption(
        f"Menampilkan {filtered_rows:,} baris data setelah filter.".replace(",", ".")
    )


def render_interpretation(df, kpis):
    top_cat = (
        df.groupby("product_categories")["total_pembayaran"]
        .sum()
        .sort_values(ascending=False)
    )
    top_prov = (
        df.groupby("provinsi")["total_pembayaran"]
        .sum()
        .sort_values(ascending=False)
    )

    cat_text = (
        f"Kategori dengan kontribusi pembayaran terbesar adalah "
        f"<b>{top_cat.index[0]}</b> dengan total {rupiah(top_cat.iloc[0])}."
        if len(top_cat)
        else "Belum ada kategori yang dapat dianalisis."
    )

    prov_text = (
        f"Provinsi dengan pembayaran tertinggi adalah "
        f"<b>{top_prov.index[0]}</b> dengan total {rupiah(top_prov.iloc[0])}."
        if len(top_prov)
        else "Belum ada provinsi yang dapat dianalisis."
    )

    interpretation = (
        f"Data terfilter menghasilkan <b>{kpis['orders']:,}</b> pesanan "
        f"dengan total pembayaran <b>{rupiah(kpis['revenue'])}</b> dan "
        f"rata-rata nilai pesanan <b>{rupiah(kpis['avg_order_value'])}</b>. "
        f"Tingkat pembatalan berada di <b>{pct(kpis['cancel_rate'])}</b>, "
        f"sedangkan tingkat retur berdasarkan kuantitas sebesar "
        f"<b>{pct(kpis['return_rate'])}</b>. {cat_text} {prov_text}"
    ).replace(",", ".")

    st.markdown('<div class="section-title">Interpretasi Singkat</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="insight-box">{interpretation}</div>',
        unsafe_allow_html=True,
    )


def render_recommendations(df, kpis):
    top_cat = (
        df.groupby("product_categories")["total_pembayaran"]
        .sum()
        .sort_values(ascending=False)
    )
    top_prov = (
        df.groupby("provinsi")["total_pembayaran"]
        .sum()
        .sort_values(ascending=False)
    )

    recs = []

    if kpis["cancel_rate"] >= 10:
        recs.append(
            "Prioritaskan analisis alasan pembatalan dan evaluasi proses "
            "pembayaran/pengiriman karena proporsi pembatalan relatif tinggi."
        )
    else:
        recs.append(
            "Pertahankan proses fulfillment yang ada sambil memantau alasan "
            "pembatalan pada kategori atau wilayah tertentu."
        )

    if len(top_cat):
        recs.append(
            f"Fokuskan stok dan promosi pada kategori <b>{top_cat.index[0]}</b>, "
            "tetapi cek margin sebelum meningkatkan persediaan secara agresif."
        )

    if len(top_prov):
        recs.append(
            f"Optimalkan kampanye dan ongkos kirim di <b>{top_prov.index[0]}</b> "
            "karena wilayah tersebut memberikan kontribusi pembayaran terbesar."
        )

    recs.append(
        "Gunakan filter kategori, provinsi, dan metode pembayaran secara berkala "
        "untuk menemukan segmen yang mengalami penurunan performa."
    )

    st.markdown('<div class="section-title">Rekomendasi Awal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="recommendation-box">'
        + "<br><br>".join(f"• {text}" for text in recs)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_data_preview(df):
    with st.expander("Lihat data terfilter"):
        show_cols = [
            column for column in [
                "order_id",
                "product_categories",
                "status_group",
                "metode_pembayaran",
                "kota_kabupaten",
                "provinsi",
                "total_qty",
                "total_pembayaran",
                "total_diskon",
                "total_returned_qty",
                "waktu_pesanan_dibuat",
            ] if column in df.columns
        ]

        st.dataframe(df[show_cols], use_container_width=True, height=420)

        st.download_button(
            "⬇️ Download data terfilter (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="data_terfilter.csv",
            mime="text/csv",
        )
