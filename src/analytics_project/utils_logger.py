import pandas as pd
import sqlite3
from pathlib import Path

# --- paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
DW_PATH = PROJECT_ROOT / "data" / "dw" / "smart_sales.db"
DW_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- schema (drop+recreate so it always matches CSVs) ---
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
    category TEXT
);

CREATE TABLE sale (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    sale_amount REAL,
    sale_date TEXT,
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


def connect_db():
    conn = sqlite3.connect(DW_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def create_schema(conn):
    conn.executescript(SCHEMA_SQL)


def load_csvs():
    customers = pd.read_csv(PREPARED_DIR / "customers_data_prepared.csv")
    products = pd.read_csv(PREPARED_DIR / "products_data_prepared.csv")
    sales = pd.read_csv(PREPARED_DIR / "sales_data_prepared.csv")

    # normalize typical columns
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

    # drop stray index columns if present
    for df in (customers, products, sales):
        if "Unnamed: 0" in df.columns:
            df.drop(columns=["Unnamed: 0"], inplace=True)

    return customers, products, sales


def safe_insert(conn, table, df, cols):
    use = [c for c in cols if c in df.columns]
    df.loc[:, use].to_sql(table, conn, if_exists="append", index=False)


def insert_all(conn, customers, products, sales):
    safe_insert(
        conn,
        "customer",
        customers,
        ["customer_id", "name", "country", "signup_date", "loyalty_points", "preferred_contact"],
    )
    safe_insert(conn, "product", products, ["product_id", "product_name", "category"])
    safe_insert(
        conn, "sale", sales, ["sale_id", "customer_id", "product_id", "sale_amount", "sale_date"]
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
    return dict(
        customers=customers_cnt,
        products=products_cnt,
        sales=sales_cnt,
        orphan_customers=orphan_customers,
        orphan_products=orphan_products,
        bad_amounts=bad_amounts,
    )


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
