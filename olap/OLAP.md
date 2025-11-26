# P6 – BI Insights and Storytelling (OLAP Analysis)

## 1. Business Goal

**Goal:** Identify the **top-selling product category** and understand how its sales vary by **state** and **month**, so the Smart Store can focus marketing and inventory on the best-performing areas.

- Actionable use:
  - Prioritize inventory for the top category in high-performing states.
  - Run targeted promotions in states where the top category is weaker.

---

## 2. Data Source

I used the **prepared CSV data** from my `data/prepared` folder:

- `sales_data_prepared_clean.csv` (or `sales_data_prepared.csv`)
  - `productid`
  - `customerid`
  - `saleamount`
  - `saledate` / `SaleDate.1`
  - `statecode`
- `products_data_prepared.csv`
  - `productid`
  - `productname`
  - `category`
- `customers_data_prepared.csv`
  - `customerid`
  - `country`
  - `signup_date`

These files were created in earlier projects (P3–P5) and represent the cleaned and modeled sales data.

---

## 3. Tools

- **Python 3** (inside `.venv`)
- **pandas** for OLAP-style grouping and aggregations
- **matplotlib** for charts
- Editor: **VS Code** on **Windows 11**

Main script:

- `olap/goal_top_category_by_state_month.py`

---

## 4. Workflow & OLAP Logic

### 4.1 Dimensions and Metrics

- **Dimensions**
  - `category` (from products)
  - `statecode` (from sales)
  - `Year`, `Month` (derived from sale date)

- **Metric**
  - `saleamount` – numeric measure of sales

- **Aggregations**
  - `SUM(saleamount)` → `total_sales`

### 4.2 Processing Steps

1. Load prepared sales, products, and customers data.
2. Parse the sale date column to a proper DateTime.
3. Merge sales with products (and customers) on `productid` and `customerid`.
4. Add time hierarchy columns:
   - `Year`
   - `Month` (YYYY-MM)
5. Build an OLAP-style cube with:

   ```text
   GROUP BY category, statecode, Year, Month
   AGGREGATE SUM(saleamount) AS total_sales
