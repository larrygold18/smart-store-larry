"""
P7 Custom BI Project - Smart Store Larry

Business Goal:
Identify the most profitable (category, country) combination in the latest year
and analyze its monthly trend.

This script:
- Loads prepared sales, customer, and product data
- Converts all required fields to numeric / datetime
- Computes net sales using saleamount and discountpct
- Slices to most recent year
- Dices by category + country
- Finds the top-performing pair
- Creates three visuals:
    1. Net sales by category (latest year)
    2. Net sales for top category by country
    3. Monthly trend for the top category/country
- Saves all results to:  olap/figures/
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -------------------------------------------------------------------
# File paths (Windows-friendly)
# -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "prepared"
OUT = ROOT / "olap" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

sales_path = DATA / "sales_data_prepared.csv"
customers_path = DATA / "customers_data_prepared.csv"
products_path = DATA / "products_data_prepared.csv"

# -------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------
print("Loading data...")

sales = pd.read_csv(sales_path)
customers = pd.read_csv(customers_path)
products = pd.read_csv(products_path)

# -------------------------------------------------------------------
# Clean and prepare data
# -------------------------------------------------------------------

# Normalize column names
sales.columns = [c.lower() for c in sales.columns]
customers.columns = [c.lower() for c in customers.columns]
products.columns = [c.lower() for c in products.columns]

# Convert saleamount / discountpct to numeric
sales["saleamount"] = pd.to_numeric(sales["saleamount"], errors="coerce").fillna(0)
sales["discountpct"] = pd.to_numeric(sales.get("discountpct", 0), errors="coerce").fillna(0)

# Compute net sales
sales["net_sales"] = sales["saleamount"] * (1 - sales["discountpct"] / 100.0)

# Parse datetime column
if "saledate" in sales.columns:
    sales["saledate"] = pd.to_datetime(sales["saledate"], errors="coerce")
else:
    raise KeyError("Your sales CSV must include a 'saledate' column.")

# Extract year & month
sales["year"] = sales["saledate"].dt.year
sales["month"] = sales["saledate"].dt.to_period("M").astype(str)

# Merge with products and customers
sales = sales.merge(products[["productid", "category"]], on="productid", how="left")
sales = sales.merge(
    customers[["customer_id", "country"]], left_on="customerid", right_on="customer_id", how="left"
)

# -------------------------------------------------------------------
# Slice: latest year only
# -------------------------------------------------------------------
latest_year = int(sales["year"].max())
df_year = sales[sales["year"] == latest_year].copy()

print(f"\nLatest Year Detected: {latest_year}")
print(f"Rows in latest year: {len(df_year):,}")

# -------------------------------------------------------------------
# Slice: totals by category
# -------------------------------------------------------------------
category_totals = (
    df_year.groupby("category", as_index=False)["net_sales"]
    .sum()
    .sort_values("net_sales", ascending=False)
)

top_category = category_totals.iloc[0]["category"]
print(f"\nTop Category: {top_category}")

# -------------------------------------------------------------------
# Dice: within top category, compare countries
# -------------------------------------------------------------------
df_top_category = df_year[df_year["category"] == top_category]

country_totals = (
    df_top_category.groupby("country", as_index=False)["net_sales"]
    .sum()
    .sort_values("net_sales", ascending=False)
)

top_country = country_totals.iloc[0]["country"]
print(f"Top Country for this category: {top_country}")

# -------------------------------------------------------------------
# Drilldown: monthly trend for (top category, top country)
# -------------------------------------------------------------------
df_top_pair = df_top_category[df_top_category["country"] == top_country]

monthly_trend = df_top_pair.groupby("month", as_index=False)["net_sales"].sum().sort_values("month")

# -------------------------------------------------------------------
# VISUAL 1 — Category totals (bar chart)
# -------------------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.bar(category_totals["category"], category_totals["net_sales"])
plt.title(f"Total Net Sales by Category ({latest_year})")
plt.xlabel("Category")
plt.ylabel("Net Sales")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUT / "p7_sales_by_category.png")
plt.close()

# -------------------------------------------------------------------
# VISUAL 2 — Country totals for top category
# -------------------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.bar(country_totals["country"], country_totals["net_sales"], color="teal")
plt.title(f"Net Sales for Top Category '{top_category}' by Country ({latest_year})")
plt.xlabel("Country")
plt.ylabel("Net Sales")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUT / "p7_top_category_by_country.png")
plt.close()

# -------------------------------------------------------------------
# VISUAL 3 — Monthly trend for the top combination
# -------------------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.plot(monthly_trend["month"], monthly_trend["net_sales"], marker="o", color="purple")
plt.title(f"Monthly Trend - {top_category} in {top_country} ({latest_year})")
plt.xlabel("Month")
plt.ylabel("Net Sales")
plt.xticks(rotation=45)
plt.grid(alpha=0.4)
plt.tight_layout()
plt.savefig(OUT / "p7_monthly_trend.png")
plt.close()

# -------------------------------------------------------------------
# Done
# -------------------------------------------------------------------
print("\nP7 analysis complete! Files saved to: olap/figures/")
print("Files generated:")
print(" - p7_sales_by_category.png")
print(" - p7_top_category_by_country.png")
print(" - p7_monthly_trend.png")
