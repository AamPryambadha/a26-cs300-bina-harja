from contextlib import asynccontextmanager
from typing import Literal, Optional
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.preprocess import CATALOG_OUTPUT_PATH, build_product_catalog, normalize_text
import json

CATALOG_CACHE: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global CATALOG_CACHE
    if not CATALOG_OUTPUT_PATH.exists():
        CATALOG_CACHE = build_product_catalog()
    else:
        with open(CATALOG_OUTPUT_PATH, "r", encoding="utf-8") as f:
            CATALOG_CACHE = json.load(f)
    yield


app = FastAPI(
    title="Toko Listrik Bina Harja - AI Service (A26-CS300)",
    version="0.1.0",
    description="REST API layanan Smart Text-to-Transaction dan Asisten Katalog Alat Listrik.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StoreContext(BaseModel):
    merchant_name: str = "Toko Listrik Bina Harja"
    allowed_payment_methods: list[str] = ["Tunai", "QRIS"]


class ParseTransactionRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, examples=["jual 2 Philip LED 3W dan 5 Broco Plafon, bayar QRIS"])
    store_context: Optional[StoreContext] = Field(default_factory=StoreContext)


class ParsedItem(BaseModel):
    raw_item_text: str
    product_id: str
    canonical_product_name: str
    category: str
    quantity: Optional[int]
    unit_price: int
    subtotal: Optional[int]
    confidence: float


class TransactionData(BaseModel):
    transaction_type: Literal["sale"] = "sale"
    payment_method: Optional[str] = None
    items: list[ParsedItem] = []
    total_amount: Optional[int] = None


class ParseTransactionResponse(BaseModel):
    status: Literal["parsed", "incomplete", "out_of_scope"]
    is_complete: bool
    needs_confirmation: bool
    message: str
    data: Optional[TransactionData] = None
    missing_fields: list[str] = []
    fallback_to_manual: bool = False


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "bina-harja-ai-service",
        "catalog_items_loaded": len(CATALOG_CACHE),
    }


@app.get("/api/v1/ai/catalog")
def get_canonical_catalog():
    return {"total": len(CATALOG_CACHE), "items": CATALOG_CACHE}


@app.post("/api/v1/ai/parse-transaction", response_model=ParseTransactionResponse)
def parse_transaction(payload: ParseTransactionRequest):
    clean_text = normalize_text(payload.raw_text)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Input raw_text tidak boleh kosong.")

    # Deteksi metode pembayaran sederhana untuk baseline v0.1
    payment_method = None
    if "qris" in clean_text:
        payment_method = "QRIS"
    elif "tunai" in clean_text or "cash" in clean_text:
        payment_method = "Tunai"

    # Pencocokan baseline ke 20 katalog kanonikal
    matched_items: list[ParsedItem] = []
    missing_fields: list[str] = []

    for product in CATALOG_CACHE:
        for alias in product["aliases"]:
            if alias and alias in clean_text:
                qty_match = re.search(rf"(\d+)\s+(?:pcs|unit|buah|meter|roll)?\s*{re.escape(alias)}", clean_text)
                qty = int(qty_match.group(1)) if qty_match else None
                subtotal = qty * product["price"] if qty is not None else None

                if qty is None:
                    missing_fields.append(f"items[{len(matched_items)}].quantity")

                matched_items.append(
                    ParsedItem(
                        raw_item_text=f"{qty} {alias}".strip() if qty else alias,
                        product_id=product["product_id"],
                        canonical_product_name=product["canonical_name"],
                        category=product["category"],
                        quantity=qty,
                        unit_price=product["price"],
                        subtotal=subtotal,
                        confidence=0.90 if qty is not None else 0.75,
                    )
                )
                break

    if not matched_items:
        return ParseTransactionResponse(
            status="out_of_scope",
            is_complete=False,
            needs_confirmation=False,
            message="Maaf, produk tidak dikenali dalam katalog Toko Listrik Bina Harja atau input di luar konteks transaksi.",
            data=None,
            missing_fields=[],
            fallback_to_manual=True,
        )

    if missing_fields:
        return ParseTransactionResponse(
            status="incomplete",
            is_complete=False,
            needs_confirmation=True,
            message="Jumlah barang belum lengkap. Mohon lengkapi kuantitas sebelum transaksi disimpan.",
            data=TransactionData(
                payment_method=payment_method,
                items=matched_items,
                total_amount=None,
            ),
            missing_fields=missing_fields,
            fallback_to_manual=True,
        )

    total_amount = sum(item.subtotal or 0 for item in matched_items)
    return ParseTransactionResponse(
        status="parsed",
        is_complete=True,
        needs_confirmation=True,
        message="Berhasil mengekstrak draf transaksi. Silakan periksa sebelum disimpan.",
        data=TransactionData(
            payment_method=payment_method,
            items=matched_items,
            total_amount=total_amount,
        ),
        missing_fields=[],
        fallback_to_manual=False,
    )