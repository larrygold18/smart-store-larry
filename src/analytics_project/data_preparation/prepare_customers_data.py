# src/analytics_project/data_preparation/prepare_customers_data.py
import pandas as pd
from ..utils.logger import get_logger
from .. import settings
from analytics_project.data_scrubber import DataScrubber

log = get_logger("prepare_customers")


def main() -> None:
    """Clean and prepare the customers data for ETL."""
    raw_path = settings.CUSTOMERS_RAW
    out_path = settings.CUSTOMERS_PREP
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading raw file: {raw_path}")
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    scrub = DataScrubber()

    # 1) Map YOUR raw headers -> canonical names (matches your screenshot)
    mapping = {
        "customerid": "customer_id",
        "name": "name",
        "region": "country",
        "joindate": "signup_date",
        "loyaltypointspts": "loyalty_points",
        "preferredcontact": "preferred_contact",
    }

    # 2) Standardize columns & force critical aliases (bullet-proof)
    df = scrub.standardize_columns(df, mapping=mapping)
    # print("Customers columns after standardize:", list(df.columns))  # TEMP debug

    # Force canonical names even if the scrubber didn't apply mapping
    rename_map = {
        "customerid": "customer_id",
        "region": "country",
        "joindate": "signup_date",
        "loyaltypointspts": "loyalty_points",
        "preferredcontact": "preferred_contact",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    # print("Columns after forced rename:", list(df.columns))  # TEMP
    # print(df.dtypes)  # TEMP: verify types before casting

    # If mapping missed (case/spacing quirks), hard-rename the essentials
    for old, new in [
        ("region", "country"),
        ("joindate", "signup_date"),
        ("loyaltypointspts", "loyalty_points"),
    ]:
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    # 3) Strings / categories
    df = scrub.trim_whitespace(df)
    cols_to_norm = [c for c in ["country", "preferred_contact"] if c in df.columns]
    if cols_to_norm:
        df = scrub.normalize_categories(df, cols_to_norm, case="lower")
    else:
        print("WARNING: no 'country' or 'preferred_contact' column found; skipping normalization")

    # 4) Types (guarded)
    if "signup_date" in df.columns:
        df = scrub.to_datetime(df, ["signup_date"])
    else:
        print("WARNING: no 'signup_date' column found; skipping date parsing")

    if "loyalty_points" in df.columns:
        df = scrub.to_numeric(df, ["loyalty_points"])
    else:
        print("WARNING: no 'loyalty_points' column found; skipping numeric cast")

    # --- sanity check AFTER types (TEMP: remove later) ---
    # print("AFTER TYPES dtypes:")
    # try:
    # print(df[["signup_date", "loyalty_points"]].dtypes)
    # xcept KeyError:
    # If either column doesn't exist, show what's there
    # print("Available columns:", list(df.columns))

    # Optional safety assertions (will raise if types are wrong)
    if "signup_date" in df.columns:
        assert pd.api.types.is_datetime64_any_dtype(df["signup_date"]), (
            "signup_date is not datetime"
        )
    if "loyalty_points" in df.columns:
        assert pd.api.types.is_float_dtype(df["loyalty_points"]), "loyalty_points is not float"

    # 5) Drop empties & duplicates
    df = scrub.drop_empty_rows(df)
    df = scrub.drop_duplicates(df)

    # 6) Fill missing values
    fill_plan = {}
    if "country" in df.columns:
        fill_plan["country"] = {"method": "mode"}
    if "preferred_contact" in df.columns:
        fill_plan["preferred_contact"] = {"method": "mode"}
    if "loyalty_points" in df.columns:
        fill_plan["loyalty_points"] = {"method": "constant", "value": 0}
    if fill_plan:
        df = scrub.fill_missing(df, fill_plan)

    # 7) (Optional) outliers
    if "loyalty_points" in df.columns:
        df = scrub.remove_outliers_iqr(df, ["loyalty_points"], factor=1.5)

    # 8) Validate schema (only for columns that exist)
    required = {
        "customer_id": "string",
        "name": "string",
        "country": "string",
        "signup_date": "datetime64[ns]",
        "loyalty_points": "float64",
        "preferred_contact": "string",
    }
    required_subset = {k: v for k, v in required.items() if k in df.columns}
    if required_subset:
        scrub.validate_schema(df, required_subset)

    # 9) Write
    df.to_csv(out_path, index=False)
    log.info(f"Wrote cleaned file to {out_path}")
    print(f"Customers raw count: {raw_count}")
    print(f"Customers prepared count: {len(df)}")


if __name__ == "__main__":
    main()
