# Big Data Exploration & Data Insight Dashboard

Versi modular dari dashboard Python + Streamlit.

## Struktur

```text
Big_Data_Dashboard_Modular/
├── app.py
├── config.py
├── data_loader.py
├── filters.py
├── metrics.py
├── charts.py
├── ui.py
├── data_clean.csv
├── requirements.txt
└── README.md
```

## Fungsi tiap file

- `app.py` → entry point dashboard.
- `config.py` → lokasi file data.
- `data_loader.py` → membaca dan membersihkan CSV.
- `filters.py` → filter sidebar dan filtering data.
- `metrics.py` → perhitungan KPI.
- `charts.py` → visualisasi Plotly.
- `ui.py` → CSS, header, KPI, interpretasi, rekomendasi, dan preview data.

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka `http://localhost:8501`.
