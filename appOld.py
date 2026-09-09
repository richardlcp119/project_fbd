import streamlit as st

from config import DATA_FILE
from data_loader import load_data
from filters import render_sidebar_filters, apply_filters
from metrics import calculate_kpis
from charts import (
    render_trend_chart,
    render_category_chart,
    render_province_chart,
    render_payment_chart,
)
from ui import (
    inject_css,
    render_header,
    render_kpi_section,
    render_interpretation,
    render_recommendations,
    render_data_preview,
)

st.set_page_config(
    page_title="Big Data Sales Insight Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

df = load_data(DATA_FILE)

render_header()

filters = render_sidebar_filters(df)
filtered = apply_filters(df, filters)

kpis = calculate_kpis(filtered)
render_kpi_section(kpis, len(filtered))

st.markdown('<div class="section-title">Grafik Tren / Perbandingan</div>', unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    render_trend_chart(filtered)
with right:
    render_category_chart(filtered)

col_a, col_b = st.columns(2)
with col_a:
    render_province_chart(filtered)
with col_b:
    render_payment_chart(filtered)

render_interpretation(filtered, kpis)
render_recommendations(filtered, kpis)
render_data_preview(filtered)

st.markdown("---")
st.caption("Fundamental Big Data • Project 1 — Big Data Exploration & Data Insight")
