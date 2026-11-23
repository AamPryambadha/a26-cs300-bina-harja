# API Contract — AI Service (A26-CS300: Toko Listrik Bina Harja)

Dokumen ini menjadi kesepakatan format komunikasi antara **AI Service (FastAPI)**, **Backend (Express.js)**, **Frontend (Vite/React)**, dan **Data Science** pada proyek **A26-CS300**.

## 1. Informasi Dasar
- **Base URL (Lokal):** `http://127.0.0.1:8000`
- **Swagger / OpenAPI Docs:** `http://127.0.0.1:8000/docs`
- **Format Request & Response:** `application/json` (UTF-8)

## 2. Aturan Umum
- Seluruh *key* JSON menggunakan format `snake_case`.
- `product_id` (`P0001`–`P0020`) dan `canonical_product_name` mengacu pada katalog master produk Toko Listrik Bina Harja (`data/processed/catalog_master.json`).
- Mutasi pengurangan stok persisten, pencatatan transaksi final ke database, serta validasi stok tidak minus ditangani oleh **Backend (Express.js)** setelah pengguna mengonfirmasi draf transaksi.
- Jika layanan AI mengalami gangguan, latensi tinggi, atau *out of scope*, respons menyertakan `fallback_to_manual: true` agar kasir tetap dapat input manual.

## 3. Endpoint

### 3.1 `GET /health`
Memeriksa status aktif layanan AI dan jumlah item katalog yang termuat.

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "service": "bina-harja-ai-service",
  "catalog_items_loaded": 20
}
```

### 3.2 `GET /api/v1/ai/catalog`
Mengambil daftar katalog kanonikal produk alat listrik Toko Listrik Bina Harja (`P0001`–`P0020`).

**Response (`200 OK`):**
```json
{
  "total": 20,
  "items": [
    {
      "product_id": "P0001",
      "canonical_name": "Philip LED 3W",
      "brand": "Philip",
      "product_type": "LED 3W",
      "category": "Lampu",
      "purchase_price": 22150,
      "price": 32500,
      "normalized_name": "philip led 3w",
      "aliases": [
        "philip led 3w",
        "lampu philip",
        "lampu led 3w"
      ]
    }
  ]
}
```

### 3.3 `POST /api/v1/ai/parse-transaction`
Mengekstrak teks catatan kasir menjadi draf transaksi terstruktur, mendeteksi data yang kurang lengkap, atau menolak input di luar konteks usaha.

**Request Body (`application/json`):**
```json
{
  "raw_text": "jual 2 Philip LED 3W dan 5 Broco Plafon, bayar QRIS",
  "store_context": {
    "merchant_name": "Toko Listrik Bina Harja",
    "allowed_payment_methods": ["Tunai", "QRIS"]
  }
}
```

**Response — Berhasil & Lengkap (`200 OK`, `status: "parsed"`):**
```json
{
  "status": "parsed",
  "is_complete": true,
  "needs_confirmation": true,
  "message": "Berhasil mengekstrak draf transaksi. Silakan periksa sebelum disimpan.",
  "data": {
    "transaction_type": "sale",
    "payment_method": "QRIS",
    "items": [
      {
        "raw_item_text": "2 philip led 3w",
        "product_id": "P0001",
        "canonical_product_name": "Philip LED 3W",
        "category": "Lampu",
        "quantity": 2,
        "unit_price": 32500,
        "subtotal": 65000,
        "confidence": 0.9
      },
      {
        "raw_item_text": "5 broco plafon",
        "product_id": "P0019",
        "canonical_product_name": "Broco Plafon",
        "category": "Fitting Lampu",
        "quantity": 5,
        "unit_price": 15000,
        "subtotal": 75000,
        "confidence": 0.9
      }
    ],
    "total_amount": 140000
  },
  "missing_fields": [],
  "fallback_to_manual": false
}
```

**Response — Informasi Kurang Lengkap (`200 OK`, `status: "incomplete"`):**
```json
{
  "status": "incomplete",
  "is_complete": false,
  "needs_confirmation": true,
  "message": "Jumlah barang belum lengkap. Mohon lengkapi kuantitas sebelum transaksi disimpan.",
  "data": {
    "transaction_type": "sale",
    "payment_method": null,
    "items": [
      {
        "raw_item_text": "saklar",
        "product_id": "P0008",
        "canonical_product_name": "Bright-G Saklar Tanam 1",
        "category": "Saklar",
        "quantity": null,
        "unit_price": 10000,
        "subtotal": null,
        "confidence": 0.75
      }
    ],
    "total_amount": null
  },
  "missing_fields": ["items[0].quantity"],
  "fallback_to_manual": true
}
```

**Response — Di Luar Konteks Usaha (`200 OK`, `status: "out_of_scope"`):**
```json
{
  "status": "out_of_scope",
  "is_complete": false,
  "needs_confirmation": false,
  "message": "Maaf, produk tidak dikenali dalam katalog Toko Listrik Bina Harja atau input di luar konteks transaksi.",
  "data": null,
  "missing_fields": [],
  "fallback_to_manual": true
}
```

## 4. Kode Status & Error Handling
- `200 OK`: Request diproses dan menghasilkan status domain (`parsed`, `incomplete`, atau `out_of_scope`).
- `400 Bad Request`: `raw_text` kosong atau payload JSON tidak valid.
- `422 Unprocessable Entity`: Gagal validasi tipe/skema request.
- `429 Too Many Requests` / `500` / `503`: Batas kuota API atau gangguan layanan AI; Backend/Frontend mengarahkan pengguna ke form kasir manual.