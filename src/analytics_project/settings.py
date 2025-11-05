from pathlib import Path

# run scripts from the repo root (C:\Repos\smart-store-larry)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PREPARED_DIR = DATA_DIR / "prepared"
LOG_DIR = PROJECT_ROOT / "logs"

# files
CUSTOMERS_RAW = RAW_DIR / "customers_data.csv"
PRODUCTS_RAW = RAW_DIR / "products_data.csv"
SALES_RAW = RAW_DIR / "sales_data.csv"

CUSTOMERS_PREP = PREPARED_DIR / "customers_data_prepared.csv"
PRODUCTS_PREP = PREPARED_DIR / "products_data_prepared.csv"
SALES_PREP = PREPARED_DIR / "sales_data_prepared.csv"

# outlier knob (raise to 3.0 if trimming too much)
OUTLIER_IQR_K = 1.5
