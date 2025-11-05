# src/analytics_project/data_preparation/prepare_products_data.py
import pandas as pd
import numpy as np
from typing import Iterable

# bring in the logger adapter and settings file
from ..utils.logger import get_logger
from .. import settings
from analytics_project.data_scrubber import DataScrubber

# initialize a logger specific to this script
log = get_logger("prepare_products")
print("DEBUG logger type:", type(log))


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """(Legacy helper) Standardize column names to snake_case."""
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
    """(Legacy helper) Remove numeric outliers using the IQR rule."""
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
    raw_path = settings.PRODUCTS_RAW  # e.g., Path("data/raw/products_data.csv")
    out_path = settings.PRODUCTS_PREP  # e.g., Path("data/prepared/products_prepared.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading raw file: {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    # 0) reusable scrubber
    scrub = DataScrubber()

    # 1) map raw headers -> desired names (LEFT must match your CSV exactly)
    mapping = {
        "Unit Price": "unit_price",
        "UnitPrice": "unit_price",
        "Price": "unit_price",
        # "Product ID": "product_id",
        # "Product Name": "product_name",
        # "Category": "category",
    }

    # 1) columns & strings
    df = scrub.standardize_columns(df, mapping=mapping)  # -> snake_case headers
    print("Columns after standardize:", list(df.columns))  # TEMP: remove later
    df = scrub.trim_whitespace(df)
    df = scrub.normalize_categories(df, ["category"], case="lower")  # optional

    # 2) types
    df = scrub.to_numeric(df, ["unit_price"])

    # 3) dedupe & empties
    df = scrub.drop_empty_rows(df)
    df = scrub.drop_duplicates(df)

    # 4) missing values
    df = scrub.fill_missing(df, {"category": {"method": "mode"}})

    # 5) (optional) outliers
    df = scrub.remove_outliers_iqr(df, ["unit_price"], factor=1.5)

    # 6) schema (only include columns that really exist)
    required = {
        "unit_price": "float64",
    }
    scrub.validate_schema(df, required)

    # 7) write
    df.to_csv(out_path, index=False)
    log.info(f"Wrote cleaned file to {out_path}")
    print(f"Products raw count: {raw_count}")
    print(f"Products prepared count: {len(df)}")


if __name__ == "__main__":
    main()
