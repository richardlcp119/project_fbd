# Big Data Exploration Dashboard

Dashboard web dibuat dengan Python + Streamlit berdasarkan data `data_clean.csv`.

## Isi dashboard
- KPI utama: total pesanan, total pembayaran, rata-rata nilai pesanan, tingkat pembatalan, tingkat retur kuantitas.
- Grafik tren total pembayaran per bulan.
- Perbandingan kategori produk, provinsi, dan metode pembayaran.
- Filter tanggal, kategori, provinsi, status pesanan, dan metode pembayaran.
- Interpretasi singkat otomatis.
- Rekomendasi awal otomatis.
- Preview dan download data terfilter.

## Cara menjalankan

1. Install Python 3.10+.
2. Buka terminal pada folder proyek.
3. Install library:

```bash
pip install -r requirements.txt
```

4. Jalankan:

```bash
streamlit run app.py
```

5. Buka alamat yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Struktur

```text
big_data_dashboard/
├── app.py
├── data_clean.csv
├── requirements.txt
└── README.md
```
