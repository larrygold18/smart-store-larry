import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- PATHS ----------
DATA = Path("data/prepared")
OUT = Path("olap/figures")
OUT.mkdir(parents=True, exist_ok=True)

# ---------- LOAD DATA ----------
clean_path = DATA / "sales_data_prepared_clean.csv"
raw_path = DATA / "sales_data_prepared.csv"

if clean_path.exists():
    sales = pd.read_csv(clean_path)
else:
    sales = pd.read_csv(raw_path)

products = pd.read_csv(DATA / "products_data_prepared.csv")
customers = pd.read_csv(DATA / "customers_data_prepared.csv")

# some projects have "customer_id", some "customerid"
if "customer_id" in customers.columns and "customerid" not in customers.columns:
    customers = customers.rename(columns={"customer_id": "customerid"})

# ---------- CLEAN & PREPARE ----------
# choose the best date column
if "SaleDate.1" in sales.columns:
    date_col = "SaleDate.1"
elif "saledate" in sales.columns:
    date_col = "saledate"
else:
    raise ValueError("Could not find a usable date column in sales_data_prepared.")

sales[date_col] = pd.to_datetime(sales[date_col], errors="coerce")

if "saleamount" not in sales.columns:
    raise ValueError("Could not find 'saleamount' column in sales data.")

sales["saleamount"] = pd.to_numeric(sales["saleamount"], errors="coerce")

# drop bad rows
sales = sales.dropna(subset=[date_col, "saleamount"])

# ---------- MERGE FACT + DIMENSIONS ----------
df = sales.merge(products, on="productid", how="left")

if "customerid" in sales.columns and "customerid" in customers.columns:
    df = df.merge(
        customers[["customerid", "country", "signup_date"]],
        on="customerid",
        how="left",
    )

# build time hierarchy
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# ---------- BUILD OLAP CUBE ----------
cube = (
    df.groupby(["category", "statecode", "Year", "Month"], as_index=False)["saleamount"]
    .sum()
    .rename(columns={"saleamount": "total_sales"})
)

cube.to_csv(OUT / "cube_category_state_year_month.csv", index=False)

# ---------- BUSINESS GOAL: find top category ----------
total_by_cat = cube.groupby("category")["total_sales"].sum().sort_values(ascending=False)
top_category = total_by_cat.index[0]

print("\nTop Category:", top_category)

# ---------- SLICE: only that category ----------
slice_df = cube[cube["category"] == top_category]

# ---------- DICE: category x state ----------
dice = (
    slice_df.groupby("statecode", as_index=False)["total_sales"]
    .sum()
    .sort_values("total_sales", ascending=False)
)
dice.to_csv(OUT / "dice_top_category_by_state.csv", index=False)

# ---------- DRILLDOWN: monthly trend ----------
drill = slice_df.groupby("Month", as_index=False)["total_sales"].sum().sort_values("Month")

# ---------- VISUAL 1: Dice (bar chart by state) ----------
plt.figure(figsize=(10, 5))
plt.bar(dice["statecode"], dice["total_sales"])
plt.title(f"Total Sales for Top Category '{top_category}' by State")
plt.xlabel("State Code")
plt.ylabel("Total Sales")
plt.tight_layout()
plt.savefig(OUT / "dice_top_category_by_state.png")
plt.close()

# ---------- VISUAL 2: Drilldown (line chart by month) ----------
plt.figure(figsize=(12, 5))
plt.plot(drill["Month"], drill["total_sales"], marker="o")
plt.title(f"Monthly Sales Trend for Top Category '{top_category}'")
plt.xlabel("Month")
plt.ylabel("Total Sales")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUT / "drilldown_monthly_trend.png")
plt.close()

print("\nAnalysis complete. Charts saved to olap/figures/")
