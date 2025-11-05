import pandas as pd
import os

print("✅ Running explore_data.py ...")

# Files to explore
files = ["customers_data.csv", "products_data.csv", "sales_data.csv"]

for file in files:
    path = f"data/raw/{file}"
    print(f"\nChecking: {path} -> Exists? {os.path.exists(path)}")

    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        continue

    df = pd.read_csv(path)
    print(f"\n--- {file} ---")
    print(df.head())  # show first 5 rows
    print("\nSummary statistics:")
    print(df.describe(include='all').T)
