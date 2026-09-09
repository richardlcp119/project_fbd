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
            .stApp { background: #f6faf7; }
            .block-container { padding-top: 1.1rem; padding-bottom: 2rem; }

            .dashboard-title {
                color: #087443;
                font-size: clamp(1.8rem, 3vw, 2.45rem);
                line-height: 1.15;
                font-weight: 800;
                margin-bottom: 0.25rem;
                letter-spacing: -0.02em;
            }

            .dashboard-subtitle {
                color: #4d6358;
                font-size: 1rem;
                line-height: 1.55;
                margin-bottom: 1.25rem;
                max-width: 1100px;
            }

            .section-title {
                color: #087443;
                font-size: 1.18rem;
                line-height: 1.25;
                font-weight: 750;
                margin: 0.75rem 0 0.55rem;
            }

            /* KPI cards dibuat dengan HTML sendiri agar nilai panjang tidak terpotong
               oleh komponen st.metric. */
            .kpi-card {
                min-height: 112px;
                background: #ffffff;
                border: 1px solid #dcebe3;
                border-radius: 14px;
                padding: 0.9rem 1rem;
                box-shadow: 0 3px 12px rgba(0,0,0,.045);
                display: flex;
                flex-direction: column;
                justify-content: center;
                overflow: hidden;
            }

            .kpi-label {
                color: #555b67;
                font-size: 0.92rem;
                line-height: 1.25;
                margin-bottom: 0.5rem;
                white-space: normal;
            }

            .kpi-value {
                color: #303542;
                font-size: clamp(1.35rem, 2vw, 1.85rem);
                line-height: 1.12;
                font-weight: 650;
                letter-spacing: -0.02em;
                white-space: normal;
                overflow-wrap: anywhere;
            }

            .kpi-green { border-top: 4px solid #20a464; }
            .kpi-blue { border-top: 4px solid #2d5be3; }
            .kpi-red { border-top: 4px solid #d62f2f; }
            .kpi-yellow { border-top: 4px solid #f1b72b; }

            .insight-box {
                border-left: 5px solid #20a464;
                background: white;
                padding: 1rem 1.1rem;
                border-radius: 0 12px 12px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,.04);
                line-height: 1.6;
            }

            .recommendation-box {
                border-left: 5px solid #f1b72b;
                background: #fffdf5;
                padding: 1rem 1.1rem;
                border-radius: 0 12px 12px 0;
                line-height: 1.55;
            }

            /* Sidebar lebih padat dan bersih. */
            section[data-testid="stSidebar"] {
                background: #eef1f5;
            }

            section[data-testid="stSidebar"] .block-container {
                padding-top: 1.35rem;
                padding-left: 1.15rem;
                padding-right: 1.15rem;
            }

            section[data-testid="stSidebar"] h2 {
                color: #343846;
                font-size: 1.35rem;
                margin-bottom: 0.8rem;
            }

            section[data-testid="stSidebar"] [data-baseweb="select"] > div,
            section[data-testid="stSidebar"] [data-baseweb="input"] > div {
                border-radius: 11px;
            }

            /* Expander dibuat lebih konsisten dengan kartu dashboard. */
            div[data-testid="stExpander"] {
                border: 1px solid #d8dce3;
                border-radius: 12px;
                background: #ffffff;
                overflow: hidden;
            }

            div[data-testid="stExpander"] summary {
                padding: 0.85rem 1rem;
            }

            @media (max-width: 900px) {
                .kpi-card { min-height: 100px; }
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


def _kpi_card(label, value, style):
    return (
        f'<div class="kpi-card {style}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        '</div>'
    )


def render_kpi_section(kpis, filtered_rows):
    st.markdown('<div class="section-title">KPI Utama</div>', unsafe_allow_html=True)

    cards = [
        ("Total Pesanan", f"{kpis['orders']:,}".replace(",", "."), "kpi-green"),
        ("Total Pembayaran", rupiah(kpis["revenue"]), "kpi-blue"),
        ("Rata-rata / Pesanan", rupiah(kpis["avg_order_value"]), "kpi-blue"),
        ("Tingkat Pembatalan", pct(kpis["cancel_rate"]), "kpi-red"),
        ("Tingkat Retur Qty", pct(kpis["return_rate"]), "kpi-yellow"),
    ]

    columns = st.columns(5)
    for column, (label, value, style) in zip(columns, cards):
        with column:
            st.markdown(_kpi_card(label, value, style), unsafe_allow_html=True)

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
            use_container_width=False,
        )
