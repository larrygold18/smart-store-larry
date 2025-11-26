import pandas as pd
import sqlite3
from pathlib import Path

# --- paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
DW_PATH = PROJECT_ROOT / "data" / "dw" / "smart_sales.db"
DW_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- schema ---
SCHEMA_SQL = """
DROP VIEW  IF EXISTS v_sales_by_region_and_category;
DROP TABLE IF EXISTS sale;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS product;

CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    country TEXT,
    signup_date TEXT,
    loyalty_points INTEGER,
    preferred_contact TEXT
);

CREATE TABLE product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    unit_price REAL,
    current_discount_pct REAL,
    supplier TEXT
);

CREATE TABLE sale (
    sale_id INTEGER PRIMARY KEY,
    transaction_id INTEGER,
    sale_date TEXT,
    customer_id INTEGER,
    product_id INTEGER,
    store_id INTEGER,
    campaign_id INTEGER,
    sale_amount REAL,
    discount_pct REAL,
    state_code TEXT,
    FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
    FOREIGN KEY (product_id)  REFERENCES product (product_id)
);

CREATE INDEX IF NOT EXISTS ix_sale_customer_id ON sale(customer_id);
CREATE INDEX IF NOT EXISTS ix_sale_product_id  ON sale(product_id);
CREATE INDEX IF NOT EXISTS ix_sale_date        ON sale(sale_date);

CREATE VIEW v_sales_by_region_and_category AS
SELECT
    c.country AS region,
    p.category,
    COUNT(s.sale_id) AS orders,
    SUM(s.sale_amount) AS revenue
FROM sale s
JOIN customer c ON c.customer_id = s.customer_id
JOIN product  p ON p.product_id  = s.product_id
GROUP BY c.country, p.category;
"""


# --- DB helpers ---
def connect_db():
    conn = sqlite3.connect(DW_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def create_schema(conn):
    conn.executescript(SCHEMA_SQL)


# --- CSV loader ---
def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(r"[ \-]+", "_", regex=True)
    return df


def load_csvs():
    customers = pd.read_csv(PREPARED_DIR / "customers_data_prepared.csv")
    products = pd.read_csv(PREPARED_DIR / "products_data_prepared.csv")
    sales = pd.read_csv(PREPARED_DIR / "sales_data_prepared.csv")

    customers = _normalize_cols(customers)
    products = _normalize_cols(products)
    sales = _normalize_cols(sales)

    # Rename to match schema
    products = products.rename(
        columns={
            "productid": "product_id",
            "productname": "product_name",
            "currentdiscountpct": "current_discount_pct",
        }
    )
    sales = sales.rename(
        columns={
            "transactionid": "transaction_id",
            "saledate": "sale_date",
            "customerid": "customer_id",
            "productid": "product_id",
            "storeid": "store_id",
            "campaignid": "campaign_id",
            "saleamount": "sale_amount",
            "discountpct": "discount_pct",
            "statecode": "state_code",
        }
    )

    # Normalize data
    if "signup_date" in customers:
        customers["signup_date"] = pd.to_datetime(
            customers["signup_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    if "sale_date" in sales:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )
    if "sale_amount" in sales:
        sales["sale_amount"] = pd.to_numeric(sales["sale_amount"], errors="coerce")

    for df in (customers, products, sales):
        for col in ("unnamed_0", "unnamed:_0"):
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

    return customers, products, sales


# --- validation helpers ---
def filter_sales_with_valid_fks(sales, customers, products):
    """Keep only sales with customer_id and product_id existing in dim tables."""
    cust_ids = set(customers["customer_id"].dropna().astype(int))
    prod_ids = set(products["product_id"].dropna().astype(int))
    s = sales.copy()
    for col in ("customer_id", "product_id"):
        if col in s.columns:
            s[col] = pd.to_numeric(s[col], errors="coerce")
    valid_mask = s["customer_id"].isin(cust_ids) & s["product_id"].isin(prod_ids)
    kept = s.loc[valid_mask].copy()
    rejects = s.loc[~valid_mask].copy()
    dropped = len(s) - len(kept)
    if dropped > 0:
        print(
            f"[WARN] Dropped {dropped} sale rows with missing customer/product keys (kept {len(kept)} / {len(s)})."
        )
    return kept, rejects


def safe_insert(conn, table, df, cols):
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{table}: expected a pandas.DataFrame, got {type(df).__name__}")
    use = [c for c in cols if c in df.columns]
    if not use:
        raise ValueError(f"{table}: no matching columns found. CSV columns: {df.columns.tolist()}")
    df.loc[:, use].to_sql(table, conn, if_exists="append", index=False)


def insert_all(conn, customers, products, sales):
    # dims
    safe_insert(
        conn,
        "customer",
        customers,
        ["customer_id", "name", "country", "signup_date", "loyalty_points", "preferred_contact"],
    )
    safe_insert(
        conn,
        "product",
        products,
        [
            "product_id",
            "product_name",
            "category",
            "unit_price",
            "current_discount_pct",
            "supplier",
        ],
    )

    # facts
    sales_clean, rejects_fk = filter_sales_with_valid_fks(sales, customers, products)
    amt_bad_mask = (sales_clean["sale_amount"].isna()) | (sales_clean["sale_amount"] < 0)
    rejects_amt = sales_clean.loc[amt_bad_mask].copy()
    sales_final = sales_clean.loc[~amt_bad_mask].copy()

    # save rejects
    if not rejects_fk.empty:
        rejects_fk.to_sql("rejects_sale_fk", conn, if_exists="replace", index=False)
    if not rejects_amt.empty:
        rejects_amt.to_sql("rejects_sale_amount", conn, if_exists="replace", index=False)

    # insert fact
    safe_insert(
        conn,
        "sale",
        sales_final,
        [
            "sale_id",
            "transaction_id",
            "sale_date",
            "customer_id",
            "product_id",
            "store_id",
            "campaign_id",
            "sale_amount",
            "discount_pct",
            "state_code",
        ],
    )


def quality_checks(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM customer")
    customers_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM product")
    products_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sale")
    sales_cnt = cur.fetchone()[0]
    cur.execute(
        """SELECT COUNT(*) FROM sale s LEFT JOIN customer c ON c.customer_id=s.customer_id WHERE c.customer_id IS NULL"""
    )
    orphan_customers = cur.fetchone()[0]
    cur.execute(
        """SELECT COUNT(*) FROM sale s LEFT JOIN product p ON p.product_id=s.product_id WHERE p.product_id IS NULL"""
    )
    orphan_products = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sale WHERE sale_amount IS NULL OR sale_amount < 0")
    bad_amounts = cur.fetchone()[0]
    return {
        "customers": customers_cnt,
        "products": products_cnt,
        "sales": sales_cnt,
        "orphan_customers": orphan_customers,
        "orphan_products": orphan_products,
        "bad_amounts": bad_amounts,
    }


# --- main ---
def main():
    conn = connect_db()
    try:
        with conn:
            create_schema(conn)
            customers, products, sales = load_csvs()
            insert_all(conn, customers, products, sales)
        checks = quality_checks(conn)
        print("=== DATA WAREHOUSE LOAD COMPLETE ===")
        for k, v in checks.items():
            print(f"{k}: {v}")
        conn.execute("ANALYZE;")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
