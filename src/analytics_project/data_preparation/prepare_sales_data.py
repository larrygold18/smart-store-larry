import pandas as pd
import numpy as np

from ..utils.logger import get_logger
from .. import settings

log = get_logger("prepare_sales")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
        .str.lower()
        .str.strip("_")
    )
    return df


def remove_outliers_iqr(df: pd.DataFrame, k: float | None = None) -> pd.DataFrame:
    if k is None:
        k = settings.OUTLIER_IQR_K
    for col in df.select_dtypes(include=["number"]).columns:
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
    raw_path = settings.SALES_RAW
    out_path = settings.SALES_PREP
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    df = standardize_columns(df)

    # Parse dates (best guess column names)
    for c in [c for c in df.columns if "date" in c or c in {"order_date", "sale_date"}]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # Numeric conversions
    for c in ["quantity", "unit_price", "discount", "total"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Business rules
    if "quantity" in df.columns:
        df.loc[df["quantity"] <= 0, "quantity"] = pd.NA
    if {"quantity", "unit_price", "total"}.issubset(df.columns):
        calc_total = df["quantity"] * df["unit_price"]
        delta = (df["total"] - calc_total).abs()
        thr = 10 * delta.median(skipna=True)
        df.loc[delta > thr, "total"] = pd.NA  # mark insane mismatches

    # Dedupe on transaction id if present
    subset = [c for c in ["sale_id", "order_id"] if c in df.columns] or None
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    log.info(f"Drop duplicates on {subset or 'all cols'}: {before} -> {len(df)}")

    # Remove numeric outliers
    df = remove_outliers_iqr(df)

    df = df.dropna(how="all")
    df.to_csv(out_path, index=False)
    log.info(f"Wrote {out_path}")

    print(f"Sales raw count: {raw_count}")
    print(f"Sales prepared count: {len(df)}")


if __name__ == "__main__":
    main()
