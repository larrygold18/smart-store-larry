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
P6 – BI Insights & Storytelling (OLAP Analysis)

This module builds on earlier Smart Store work by performing OLAP-style slicing, dicing, and drilldown to uncover actionable business insights using Python on Windows 11.

1. Business Goal

Goal:
Identify the top-selling product category and analyze how that category’s sales vary by state and by month, so the Smart Store can improve:

inventory planning

targeted marketing

seasonal sales forecasting

This goal focuses on a specific outcome:
➡ Which category should the business prioritize and how should it plan by geography and time?

2. Data Source

I used the prepared CSVs generated during Projects P3–P5:

sales_data_prepared_clean.csv

Includes: transactionid, productid, customerid, saleamount, SaleDate.1, statecode

products_data_prepared.csv

Includes: productid, productname, category

customers_data_prepared.csv

Includes: customer_id (renamed to customerid), country, signup_date

Columns Used in Analysis
Table	Columns	Purpose
Sales	saleamount, statecode, SaleDate.1	Metric + geography + time
Products	productid, category	Category dimension
Sales (derived)	Year, Month	Drilldown time hierarchy

All files stored in:

data/prepared/

3. Tools

Windows 11

Python 3 inside .venv

pandas — OLAP grouping, slicing, dicing, drilldown

matplotlib — visualizations

VS Code — execution and editing

Main script for OLAP logic:

olap/goal_top_category_by_state_month.py


Full documentation:

olap/OLAP.md

4. Workflow & OLAP Logic
4.1 Steps Performed

Loaded prepared CSVs.

Converted SaleDate.1 to datetime format.

Converted saleamount to numeric.

Merged sales + products to attach categories.

Added time hierarchy columns:

Year

Month

Built OLAP cube grouped by:

category × statecode × Year × Month


Computed:

SUM(saleamount) AS total_sales


Slice: Filtered cube to only the top category.

Dice: Broke down the top category by statecode.

Drilldown: Examined the monthly trend for the top category.

5. Results & Visualizations
Top Category

From the OLAP script:

➡️ Top Category: home

5.1 DICE Result — Top Category by State

Insight:
Certain states strongly drive Home-category sales.
These states are candidates for:

Additional inventory

Regional advertising

Localized promotions

5.2 DRILLDOWN — Monthly Trend for Top Category

Insight:
Sales for the top category vary significantly by month —
a seasonal pattern exists that can guide:

Ordering cycles

Discount timing

Holiday promotions

6. Suggested Business Action

Based on this analysis:

✔ Inventory Strategy

Prioritize stocking the Home category in the highest-performing states.

✔ Marketing Strategy

Deploy targeted campaigns in states with lower sales to increase awareness.

✔ Seasonal Planning

Use the monthly trend to determine which months need:

More inventory

More marketing spend

Or clearance activity

P6 – BI Insights & Storytelling (OLAP Analysis)

This module builds on earlier Smart Store work by performing OLAP-style slicing, dicing, and drilldown to uncover actionable business insights using Python on Windows 11.

1. Business Goal

Goal:
Identify the top-selling product category and analyze how that category’s sales vary by state and by month, so the Smart Store can improve:

inventory planning

targeted marketing

seasonal sales forecasting

This goal focuses on a specific outcome:
➡ Which category should the business prioritize and how should it plan by geography and time?

2. Data Source

I used the prepared CSVs generated during Projects P3–P5:

sales_data_prepared_clean.csv

Includes: transactionid, productid, customerid, saleamount, SaleDate.1, statecode

products_data_prepared.csv

Includes: productid, productname, category

customers_data_prepared.csv

Includes: customer_id (renamed to customerid), country, signup_date

Columns Used in Analysis
Table	Columns	Purpose
Sales	saleamount, statecode, SaleDate.1	Metric + geography + time
Products	productid, category	Category dimension
Sales (derived)	Year, Month	Drilldown time hierarchy

All files stored in:

data/prepared/

3. Tools

Windows 11

Python 3 inside .venv

pandas — OLAP grouping, slicing, dicing, drilldown

matplotlib — visualizations

VS Code — execution and editing

Main script for OLAP logic:

olap/goal_top_category_by_state_month.py


Full documentation:

olap/OLAP.md

4. Workflow & OLAP Logic
4.1 Steps Performed

Loaded prepared CSVs.

Converted SaleDate.1 to datetime format.

Converted saleamount to numeric.

Merged sales + products to attach categories.

Added time hierarchy columns:

Year

Month

Built OLAP cube grouped by:

category × statecode × Year × Month


Computed:

SUM(saleamount) AS total_sales


Slice: Filtered cube to only the top category.

Dice: Broke down the top category by statecode.

Drilldown: Examined the monthly trend for the top category.

5. Results & Visualizations
Top Category

From the OLAP script:

➡️ Top Category: home

5.1 DICE Result — Top Category by State

Insight:
Certain states strongly drive Home-category sales.
These states are candidates for:

Additional inventory

Regional advertising

Localized promotions

5.2 DRILLDOWN — Monthly Trend for Top Category

Insight:
Sales for the top category vary significantly by month —
a seasonal pattern exists that can guide:

Ordering cycles

Discount timing

Holiday promotions

6. Suggested Business Action

Based on this analysis:

✔ Inventory Strategy

Prioritize stocking the Home category in the highest-performing states.

✔ Marketing Strategy

Deploy targeted campaigns in states with lower sales to increase awareness.

✔ Seasonal Planning

Use the monthly trend to determine which months need:

More inventory

More marketing spend

Or clearance activity

P6 – BI Insights & Storytelling (OLAP Analysis)

This module builds on earlier Smart Store work by performing OLAP-style slicing, dicing, and drilldown to uncover actionable business insights using Python on Windows 11.

1. Business Goal

Goal:
Identify the top-selling product category and analyze how that category’s sales vary by state and by month, so the Smart Store can improve:

inventory planning

targeted marketing

seasonal sales forecasting

This goal focuses on a specific outcome:
➡ Which category should the business prioritize and how should it plan by geography and time?

2. Data Source

I used the prepared CSVs generated during Projects P3–P5:

sales_data_prepared_clean.csv

Includes: transactionid, productid, customerid, saleamount, SaleDate.1, statecode

products_data_prepared.csv

Includes: productid, productname, category

customers_data_prepared.csv

Includes: customer_id (renamed to customerid), country, signup_date

Columns Used in Analysis
Table	Columns	Purpose
Sales	saleamount, statecode, SaleDate.1	Metric + geography + time
Products	productid, category	Category dimension
Sales (derived)	Year, Month	Drilldown time hierarchy

All files stored in:

data/prepared/

3. Tools

Windows 11

Python 3 inside .venv

pandas — OLAP grouping, slicing, dicing, drilldown

matplotlib — visualizations

VS Code — execution and editing

Main script for OLAP logic:

olap/goal_top_category_by_state_month.py


Full documentation:

olap/OLAP.md

4. Workflow & OLAP Logic
4.1 Steps Performed

Loaded prepared CSVs.

Converted SaleDate.1 to datetime format.

Converted saleamount to numeric.

Merged sales + products to attach categories.

Added time hierarchy columns:

Year

Month

Built OLAP cube grouped by:

category × statecode × Year × Month


Computed:

SUM(saleamount) AS total_sales


Slice: Filtered cube to only the top category.

Dice: Broke down the top category by statecode.

Drilldown: Examined the monthly trend for the top category.

5. Results & Visualizations
Top Category

From the OLAP script:

➡️ Top Category: home

5.1 DICE Result — Top Category by State

Insight:
Certain states strongly drive Home-category sales.
These states are candidates for:

Additional inventory

Regional advertising

Localized promotions

5.2 DRILLDOWN — Monthly Trend for Top Category

Insight:
Sales for the top category vary significantly by month —
a seasonal pattern exists that can guide:

Ordering cycles

Discount timing

Holiday promotions

6. Suggested Business Action

Based on this analysis:

✔ Inventory Strategy

Prioritize stocking the Home category in the highest-performing states.

✔ Marketing Strategy

Deploy targeted campaigns in states with lower sales to increase awareness.

✔ Seasonal Planning

Use the monthly trend to determine which months need:

More inventory

More marketing spend

Or clearance activity

7. Challenges and Solutions
Challenge	Solution
Misformatted sale dates	Used pd.to_datetime with error coercion and dropped invalid rows
saleamount stored as text	Converted with pd.to_numeric
Date column names inconsistent (saledate, SaleDate.1)	Added column detection logic in script
Multiple joins required	Standardized customerid naming and merged on productid
