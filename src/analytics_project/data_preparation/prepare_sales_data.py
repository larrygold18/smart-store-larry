# src/analytics_project/data_preparation/prepare_sales_data.py
import pandas as pd
from ..utils.logger import get_logger
from .. import settings
from analytics_project.data_scrubber import DataScrubber

log = get_logger("prepare_sales")


def main() -> None:
    """Clean and prepare the sales data for ETL."""
    raw_path = settings.SALES_RAW
    out_path = settings.SALES_PREP
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading raw file: {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    scrub = DataScrubber()

    # 1️⃣ Map raw headers to canonical names (exactly matches your screenshot)
    mapping = {
        "transactionid": "transaction_id",
        "saledate": "order_date",
        "customerid": "customer_id",
        "productid": "product_id",
        "storeid": "store_id",
        "campaignid": "campaign_id",
        "saleamount": "sale_amount",
        "discountpct": "discount_pct",
        "statecode": "state_code",
    }

    # 2️⃣ Standardize columns
    df = scrub.standardize_columns(df, mapping=mapping)
    # print("Sales columns after standardize:", list(df.columns))  # TEMP debug

    # 3️⃣ Clean strings and normalize state codes
    df = scrub.trim_whitespace(df)
    if "state_code" in df.columns:
        df["state_code"] = df["state_code"].astype(str).str.strip().str.upper()

    # 4️⃣ Convert types
    if "order_date" in df.columns:
        df = scrub.to_datetime(df, ["order_date"])
    if "sale_amount" in df.columns:
        df = scrub.to_numeric(df, ["sale_amount"])
    if "discount_pct" in df.columns:
        df = scrub.to_numeric(df, ["discount_pct"])

    # 5️⃣ Drop empties & duplicates
    df = scrub.drop_empty_rows(df)
    df = scrub.drop_duplicates(df)

    # 6️⃣ Fill missing values
    fill_plan = {}
    if "discount_pct" in df.columns:
        fill_plan["discount_pct"] = {"method": "constant", "value": 0}
    if "state_code" in df.columns:
        fill_plan["state_code"] = {"method": "mode"}
    if fill_plan:
        df = scrub.fill_missing(df, fill_plan)

    # 7️⃣ (Optional) Outlier handling
    if "sale_amount" in df.columns:
        df = scrub.remove_outliers_iqr(df, ["sale_amount"], factor=1.5)

    # 8️⃣ Derived metrics (optional)
    if "discount_pct" in df.columns and "sale_amount" in df.columns:
        df["net_sale_amount"] = df["sale_amount"] * (1 - (df["discount_pct"].fillna(0) / 100))

    # 9️⃣ Schema validation
    required = {
        "transaction_id": "string",
        "order_date": "datetime64[ns]",
        "customer_id": "string",
        "product_id": "string",
        "store_id": "string",
        "campaign_id": "string",
        "sale_amount": "float64",
        "discount_pct": "float64",
        "state_code": "string",
        "net_sale_amount": "float64",
    }
    required_subset = {k: v for k, v in required.items() if k in df.columns}
    if required_subset:
        scrub.validate_schema(df, required_subset)

    # 🔟 Write cleaned data
    df.to_csv(out_path, index=False)
    log.info(f"Wrote cleaned file to {out_path}")
    print(f"Sales raw count: {raw_count}")
    print(f"Sales prepared count: {len(df)}")


if __name__ == "__main__":
    main()
