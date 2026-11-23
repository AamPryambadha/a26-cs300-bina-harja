openapi: 3.0.3
info:
  title: API Contract - Toko Listrik Bina Harja (A26-CS300)
  description: >
    Dokumen kesepakatan REST API antara Frontend (Vite/React), Backend (Express.js),
    dan AI Service (FastAPI) untuk Sistem Pencatatan Transaksi dan Inventaris Pintar
    Toko Listrik Bina Harja.
  version: 1.0.0

servers:
  - url: http://localhost:5000/api/v1
    description: Backend Local Development (Express.js)
  - url: https://api.binaharja-capstone.example.com/api/v1
    description: Backend Production (Free Tier Hosting)

tags:
  - name: Products
    description: Manajemen inventaris dan stok produk alat listrik
  - name: Transactions
    description: Pencatatan transaksi kasir dan pemotongan stok otomatis
  - name: Smart AI
    description: Proxy Backend ke layanan AI (Smart Text-to-Transaction)
  - name: Dashboard
    description: Analitik omzet, laba harian, produk terlaris, dan peringatan restok

paths:
  /products:
    get:
      tags: [Products]
      summary: Ambil daftar produk inventaris
      parameters:
        - name: search
          in: query
          schema: { type: string }
          description: Pencarian berdasarkan nama atau SKU produk
        - name: category
          in: query
          schema: { type: string }
          description: Filter kategori (Lampu, Kabel, Saklar, MCB, dll.)
        - name: low_stock_only
          in: query
          schema: { type: boolean, default: false }
      responses:
        '200':
          description: Daftar produk berhasil diambil
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, example: success }
                  data:
                    type: array
                    items: { $ref: '#/components/schemas/Product' }
    post:
      tags: [Products]
      summary: Tambah produk baru
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ProductCreateRequest' }
      responses:
        '201':
          description: Produk berhasil ditambahkan
        '400':
          $ref: '#/components/responses/ValidationError'
        '409':
          description: SKU sudah terdaftar

  /products/{id}/restock:
    patch:
      tags: [Products]
      summary: Tambah stok barang masuk (Restock)
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [quantity_added]
              properties:
                quantity_added: { type: integer, minimum: 1, example: 15 }
                notes: { type: string, example: "Restok dari distributor" }
      responses:
        '200':
          description: Stok berhasil ditambahkan
        '400':
          $ref: '#/components/responses/ValidationError'
        '404':
          $ref: '#/components/responses/NotFoundError'

  /transactions:
    get:
      tags: [Transactions]
      summary: Ambil riwayat transaksi penjualan
      parameters:
        - name: start_date
          in: query
          schema: { type: string, format: date, example: "2026-11-01" }
        - name: end_date
          in: query
          schema: { type: string, format: date, example: "2026-11-23" }
        - name: payment_method
          in: query
          schema: { type: string, enum: [TUNAI, QRIS] }
      responses:
        '200':
          description: Daftar riwayat transaksi
    post:
      tags: [Transactions]
      summary: Simpan transaksi kasir & kurangi stok otomatis
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/TransactionCreateRequest' }
      responses:
        '201':
          description: Transaksi tersimpan dan stok diperbarui
        '400':
          $ref: '#/components/responses/ValidationError'
        '409':
          description: Stok tidak mencukupi (mencegah stok minus)
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ErrorResponse' }

  /ai/parse-transaction:
    post:
      tags: [Smart AI]
      summary: Ekstrak draf transaksi dari teks bebas (Smart Text-to-Transaction)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [raw_text]
              properties:
                raw_text:
                  type: string
                  minLength: 3
                  maxLength: 300
                  example: "jual 2 kabel NYM dan 5 saklar, bayar QRIS"
      responses:
        '200':
          description: Draf ekstraksi siap dikonfirmasi pengguna
        '422':
          description: Input kurang lengkap atau di luar konteks toko listrik
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ErrorResponse' }
        '429':
          description: Rate limit AI tercapai (gunakan fallback form manual)
        '502':
          description: Layanan AI sedang tidak tersedia (gunakan fallback form manual)

  /dashboard/summary:
    get:
      tags: [Dashboard]
      summary: Ringkasan KPI omzet dan laba harian
      parameters:
        - name: date
          in: query
          schema: { type: string, format: date, example: "2026-11-23" }
      responses:
        '200':
          description: Ringkasan KPI (mengembalikan 0 jika belum ada transaksi)

  /dashboard/restock-alerts:
    get:
      tags: [Dashboard]
      summary: Daftar produk stok menipis dan rekomendasi restok
      responses:
        '200':
          description: Daftar produk dengan stok di bawah atau sama dengan threshold

components:
  schemas:
    Product:
      type: object
      properties:
        id: { type: integer, example: 1 }
        sku: { type: string, example: "LMP-LED-12W" }
        name: { type: string, example: "Lampu LED 12W" }
        category: { type: string, example: "Lampu" }
        unit: { type: string, example: "pcs" }
        cost_price: { type: integer, example: 22000 }
        selling_price: { type: integer, example: 32000 }
        stock: { type: integer, example: 20 }
        min_stock_threshold: { type: integer, example: 5 }
        warranty_months: { type: integer, nullable: true, example: 12 }

    ProductCreateRequest:
      type: object
      required: [sku, name, category, unit, cost_price, selling_price, stock, min_stock_threshold]
      properties:
        sku: { type: string, example: "LMP-LED-12W" }
        name: { type: string, example: "Lampu LED 12W" }
        category: { type: string, example: "Lampu" }
        unit: { type: string, example: "pcs" }
        cost_price: { type: integer, minimum: 0, example: 22000 }
        selling_price: { type: integer, minimum: 0, example: 32000 }
        stock: { type: integer, minimum: 0, example: 20 }
        min_stock_threshold: { type: integer, minimum: 0, example: 5 }
        warranty_months: { type: integer, minimum: 0, nullable: true, example: 12 }

    TransactionCreateRequest:
      type: object
      required: [payment_method, items]
      properties:
        payment_method: { type: string, enum: [TUNAI, QRIS] }
        source: { type: string, enum: [MANUAL, AI_SMART_TEXT], default: MANUAL }
        ai_log_id: { type: string, nullable: true }
        notes: { type: string, nullable: true }
        items:
          type: array
          minItems: 1
          items:
            type: object
            required: [product_id, quantity]
            properties:
              product_id: { type: integer, example: 1 }
              quantity: { type: integer, minimum: 1, example: 3 }
              unit_price:
                type: integer
                minimum: 0
                nullable: true
                description: Opsional untuk harga nego; jika kosong memakai harga jual default.

    ErrorResponse:
      type: object
      properties:
        status: { type: string, example: error }
        error_code: { type: string, example: VALIDATION_ERROR }
        message: { type: string, example: "Jumlah barang wajib diisi." }
        details:
          type: array
          items:
            type: object
            properties:
              field: { type: string }
              reason: { type: string }
        fallback_action: { type: string, nullable: true, example: "SWITCH_TO_MANUAL_FORM" }

  responses:
    ValidationError:
      description: Input tidak valid (Joi Schema Validation)
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorResponse' }
    NotFoundError:
      description: Data tidak ditemukan
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorResponse' }