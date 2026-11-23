# AI Service — Sistem Pencatatan Transaksi & Inventaris Pintar Toko Listrik Bina Harja (A26-CS300)

Repositori/modul ini berisi layanan **Gen AI** dan *preprocessing* awal untuk proyek Capstone **Asah 2026** (ID Tim: `A26-CS300`) pada UMKM ritel **Toko Listrik Bina Harja**[cite: 2, 18, 23].

## Anggota Tim & Peran
- **Gen AI (PJ Minggu 1 & Minggu 3):** Zayyana Maulida (`ae466b6x1823`)[cite: 2, 17]
- **Gen AI (PJ Minggu 2):** Najib Alfa Rojaya (`ae466b6y1321`)[cite: 2, 17]
- **Full-Stack (Express.js & Vite/React):** Tutur Pryambadha (`fs179b6y1739`)[cite: 2, 17]
- **Data Science:** Az-Zahrawani (`ds466b6x0304`) & Muhammad Sidiq Fathurochman (`ds005b6y1268`)[cite: 2, 17]

## Permasalahan & Peran Model AI
Toko Listrik Bina Harja sebelumnya mencatat transaksi harian dan mutasi stok secara manual menggunakan buku catatan, sehingga memakan waktu, rawan salah hitung, dan menyulitkan pemantauan stok maupun perencanaan restok secara cepat[cite: 4, 17].

Peran modul **AI** dalam solusi ini meliputi:
1. **Smart Text-to-Transaction:** Mengekstrak entitas transaksi (produk alat listrik kanonikal, `product_id`, kuantitas, harga satuan/subtotal, dan metode pembayaran seperti `Tunai` atau `QRIS`) dari teks catatan kasir tidak terstruktur agar tampil sebagai draf yang diperiksa sebelum disimpan.
2. **Penanganan Input Kurang Lengkap & Out-of-Scope Guardrails:** Mendeteksi input transaksi yang kurang lengkap (misalnya nama barang tanpa jumlah) agar dilengkapi pengguna, serta menolak secara sopan input atau pertanyaan yang berada di luar konteks usaha toko listrik[cite: 6, 13, 15, 17].
3. **Asisten Katalog & Integrasi Lanjutan (Minggu 3):** Menyediakan fitur tanya jawab katalog/produk berbasis RAG, *prompt* terstruktur, penanganan *fallback* saat kuota API/latensi bermasalah, serta dokumentasi Swagger/OpenAPI[cite: 13, 17].

## Sumber Data & Katalog Produk
Data yang digunakan pada tahap pengembangan ini merupakan **dataset baseline/simulasi** (bukan data transaksi riil milik UMKM) untuk menjaga privasi dan mengatasi ketiadaan catatan digital historis UMKM[cite: 4, 8, 18]:
- **Dataset Rujukan Publik (Kaggle):** [Retail Store Inventory Forecasting Dataset](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset/data) — disaring ke satu toko (`Store ID = S001`) dengan 731 hari pencatatan (`2022-01-01` s.d. `2024-01-01`) dan atribut eksternal lintas-cabang yang tidak relevan dikeluarkan[cite: 18].
- **Daftar Produk UMKM (20 SKU):** Master katalog 20 produk alat listrik (`P0001`–`P0020`) meliputi kategori *Lampu*, *Kabel*, *Saklar*, *MCB*, *Solder*, *Baterai*, *Stop Kontak*, *Steker*, *Antenna*, *Fitting Lampu*, dan *Remote* beserta `Product Name`, `Brand`, `Product Type`, `Category`, `Purchase Price`, dan `Price`[cite: 18].
- **Dataset Gabungan (`bina_harja_dataset.csv`):** Hasil penggabungan (*left join* berdasarkan `Product ID`) yang disiapkan bersama tim Data Science sebanyak **14.620 baris** dan **13 kolom** sebagai kontrak skema awal sebelum digantikan data riil UMKM pada tahap produksi[cite: 18].

## Struktur Folder
```text
capstone-project/
├── data/
│   ├── bina_harja_dataset.csv
│   └── processed/
│       └── catalog_master.json
├── src/
│   ├── preprocess.py
│   └── main.py
├── requirements.txt
├── API_CONTRACT.md
└── README.md
```

## Cara Menjalankan di Lokal
1. Aktifkan *virtual environment*:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```[cite: 20, 21]
2. Instal dependensi:
   ```powershell
   pip install -r requirements.txt
   ```[cite: 21]
3. Jalankan *preprocessing* katalog awal:
   ```powershell
   python src\preprocess.py
   ```[cite: 22, 23]
4. Jalankan server FastAPI lokal:
   ```powershell
   uvicorn src.main:app --reload --port 8000
   ```[cite: 23]
5. Buka dokumentasi Swagger interaktif di `http://127.0.0.1:8000/docs`[cite: 23].