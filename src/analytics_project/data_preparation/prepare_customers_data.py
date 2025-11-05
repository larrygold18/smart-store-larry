import pandas as pd
import numpy as np

from ..utils.logger import get_logger
from .. import settings

log = get_logger("prepare_customers")


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
    raw_path = settings.CUSTOMERS_RAW
    out_path = settings.CUSTOMERS_PREP
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    df = standardize_columns(df)

    # Basic typing rules (adjust if your columns differ)
    if "customer_id" in df.columns:
        df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
        df.loc[(df["age"] < 0) | (df["age"] > 120), "age"] = pd.NA

    # Clean strings
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip()

    # Dedupe using keys if present
    key_subset = [c for c in ["customer_id", "email"] if c in df.columns] or None
    before = len(df)
    df = df.drop_duplicates(subset=key_subset, keep="first")
    log.info(f"Drop duplicates on {key_subset or 'all cols'}: {before} -> {len(df)}")

    # Remove gross numeric outliers
    df = remove_outliers_iqr(df)

    # Finalize
    df = df.dropna(how="all")
    df.to_csv(out_path, index=False)
    log.info(f"Wrote {out_path}")

    print(f"Customers raw count: {raw_count}")
    print(f"Customers prepared count: {len(df)}")


if __name__ == "__main__":
    main()
