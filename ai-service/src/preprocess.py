import json
import re
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATASET_PATH = BASE_DIR / "data" / "bina_harja_dataset.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CATALOG_OUTPUT_PATH = PROCESSED_DIR / "catalog_master.json"


def normalize_text(text: str) -> str:
    """Membersihkan teks input kasir maupun nama produk menjadi lowercase standar."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\.\-\(\)\+]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def build_product_catalog(csv_path: Path = RAW_DATASET_PATH) -> list[dict]:
    """Mengekstrak dan membersihkan master 20 SKU produk dari bina_harja_dataset.csv."""
    df = pd.read_csv(csv_path)

    required_cols = [
        "Product ID",
        "Product Name",
        "Brand",
        "Product Type",
        "Category",
        "Purchase Price",
        "Price",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan pada dataset: {missing}")

    # Ambil 20 SKU unik dan bersihkan spasi berlebih
    catalog_df = (
        df[required_cols]
        .drop_duplicates(subset=["Product ID"])
        .sort_values("Product ID")
        .copy()
    )

    for col in ["Product ID", "Product Name", "Brand", "Product Type", "Category"]:
        catalog_df[col] = catalog_df[col].astype(str).str.strip()

    # Validasi nilai harga
    catalog_df = catalog_df[
        (catalog_df["Price"] > 0) & (catalog_df["Purchase Price"] >= 0)
    ]

    catalog_records = []
    for _, row in catalog_df.iterrows():
        canonical_name = row["Product Name"]
        brand = row["Brand"]
        product_type = row["Product Type"]
        category = row["Category"]

        # Susun keyword pencarian dasar untuk membantu entity matching / prompting AI
        aliases = list(
            {
                normalize_text(canonical_name),
                normalize_text(f"{brand} {product_type}"),
                normalize_text(f"{category} {brand}"),
                normalize_text(f"{category} {product_type}"),
            }
        )

        catalog_records.append(
            {
                "product_id": row["Product ID"],
                "canonical_name": canonical_name,
                "brand": brand,
                "product_type": product_type,
                "category": category,
                "purchase_price": int(row["Purchase Price"]),
                "price": int(row["Price"]),
                "normalized_name": normalize_text(canonical_name),
                "aliases": aliases,
            }
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_records, f, ensure_ascii=False, indent=2)

    return catalog_records


if __name__ == "__main__":
    catalog = build_product_catalog()
    print(f"Preprocessing selesai: {len(catalog)} produk berhasil disimpan ke {CATALOG_OUTPUT_PATH}")