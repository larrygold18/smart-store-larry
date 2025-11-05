# src/analytics_project/data_preparation/prepare_products_data.py
import pandas as pd
import numpy as np
from typing import Iterable

# bring in the logger adapter and settings file
from ..utils.logger import get_logger
from .. import settings

# initialize a logger specific to this script
log = get_logger("prepare_products")
print("DEBUG logger type:", type(log))


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names: lowercase, replace spaces and symbols with underscores,
    and remove leading/trailing underscores.
    """
    df.columns = (
        df.columns.str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
        .str.lower()
        .str.strip("_")
    )
    return df


def remove_outliers_iqr(
    df: pd.DataFrame, cols: Iterable[str] | None = None, k: float | None = None
) -> pd.DataFrame:
    """
    Remove numeric outliers using the IQR rule.
    Any row with a numeric value outside [Q1 - k*IQR, Q3 + k*IQR] is dropped.
    """
    if k is None:
        k = settings.OUTLIER_IQR_K
    if cols is None:
        cols = df.select_dtypes(include=["number"]).columns

    for col in cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lo, hi = q1 - k * iqr, q3 + k * iqr
        before = len(df)
        df = df[(df[col].between(lo, hi)) | df[col].isna()]
        if before != len(df):
            log.info(f"Outlier trim on {col}: {before} -> {len(df)}")
    return df


def main() -> None:
    """Read raw product data, clean it, and save the prepared dataset."""
    raw_path = settings.PRODUCTS_RAW
    out_path = settings.PRODUCTS_PREP
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading raw file: {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    # --- 1. standardize column names ---
    df = standardize_columns(df)

    # --- 2. enforce data types ---
    if "product_id" in df.columns:
        df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce").astype("Int64")

    # --- 3. clean up text fields ---
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # --- 4. business rules ---
    for price_col in [
        c for c in df.columns if c in {"price", "unit_price", "list_price"} or "price" in c
    ]:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
        df.loc[df[price_col] <= 0, price_col] = pd.NA

    for col in [c for c in df.columns if c in {"cost", "weight", "stock"}]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- 5. remove duplicates ---
    subset = [c for c in ("product_id", "sku") if c in df.columns]
    if not subset:
        fallback = [c for c in ("product_name", "brand", "category", "model") if c in df.columns]
        subset = fallback if len(fallback) >= 2 else None

    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    log.info(f"Drop duplicates on {subset or 'all columns'}: {before} -> {len(df)}")

    # --- 6. remove numeric outliers ---
    df = remove_outliers_iqr(df)

    # --- 7. finalize and save ---
    df = df.dropna(how="all")
    df.to_csv(out_path, index=False)
    log.info(f"Wrote cleaned file to {out_path}")

    print(f"Products raw count: {raw_count}")
    print(f"Products prepared count: {len(df)}")


if __name__ == "__main__":
    main()
