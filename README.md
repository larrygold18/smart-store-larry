## P4: Data Warehouse (SQLite)

**Design**: Star schema
- **Fact**: `sale(sale_id, transaction_id, sale_date, customer_id, product_id, store_id, campaign_id, sale_amount, discount_pct, state_code)`
- **Dims**:
  - `customer(customer_id, name, country, signup_date, loyalty_points, preferred_contact)`
  - `product(product_id, product_name, category, unit_price, current_discount_pct, supplier)`

**ETL output**: `data/dw/smart_sales.db`
**Row counts** (from script): customers=190, products=100, sales=1890 (110 sale rows dropped for missing FKs)
**Data quality rules**:
- FK integrity (`sale.customer_id` → `customer.customer_id`; `sale.product_id` → `product.product_id`)
- `sale_amount` must be non-null and ≥ 0
- Dates stored as ISO `YYYY-MM-DD` TEXT (SQLite)

![DW Screenshot](docs/images/p4_dw_screenshot.png)
# Smart Store BI Reporting – Project P5
Smart Store BI Reporting – Project P5

Author: Sandra Otubushin
Operating System: Windows 11
Tool Used: Power BI Desktop (Windows implementation)

📘 Project Overview

This project continues from P4, where I built a SQLite data warehouse for the Smart Store dataset.
For P5, I loaded the warehouse tables into Power BI Desktop and performed OLAP reporting operations:

Slice (single-dimensional filter)

Dice (multi-dimensional filter)

Drilldown (hierarchical date exploration)

Interactive visualization

Star schema modeling

Because Windows blocked direct SQLite ODBC installation, I exported all warehouse tables to CSV and imported them into Power BI.

📊 Data Sources Used

The following tables were imported from the P4 data warehouse:

customers_data_prepared.csv

products_data_prepared.csv

sales_data_prepared_clean.csv
(cleaned version with corrected dates and numeric saleamount values)

🧩 Data Model (Star Schema)

The fact table sales_data_prepared_clean connects to two dimension tables:

customers_data_prepared       products_data_prepared
          \                           /
           \                         /
            --> sales_data_prepared_clean <--


Relationships:

customers_data_prepared.customer_id → sales_data_prepared_clean.customerid

products_data_prepared.productid → sales_data_prepared_clean.productid

📸 Insert Model View Screenshot Here
🔍 OLAP Operations
1️⃣ Slice Operation

Dimension Used: Product Category
Field: products_data_prepared[category]
Why:
Slicing allows analysis along a single dimension. Filtering by category shows how sales vary across product categories.

Visualization:

Slicer: Product Category

Bar Chart: Sum of saleamount by productname
2️⃣ Dice Operation

Dimensions Used:

Product Category

State Code

Fields:

products_data_prepared[category]

sales_data_prepared_clean[statecode]

Why:
Dicing uses two dimensions together. This reveals patterns such as which states perform best for a given category.

Visualization:

Two slicers: Category + StateCode

Column chart filtered by both slicers

📸 Insert DICE Screenshot Here
3️⃣ Drilldown Operation

Hierarchy Used: SaleDate hierarchy

Year

Quarter

Month

Day

Field: SaleDate.1 (cleaned date column)

Why:
Drilldowns allow deeper exploration of trends over time.
This shows how sales unfold annually, quarterly, and monthly.

Visualization:

Column or Line Chart

X-axis: Date hierarchy

Y-axis: Sum of saleamount

Drilldown enabled (⬇⬇ icon)
