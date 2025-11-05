# 🧩 Module 3 — Data Preparation for ETL

This module completes the data preparation pipeline for the Smart Store project.
Using a reusable **DataScrubber** class, all raw data tables were standardized, cleaned, validated, and saved into `data/prepared/` for future ETL and BI analysis.

---

## ⚙️ Tools & Environment
- **Python 3.12**
- **pandas** for data processing
- **Visual Studio Code** on **Windows 11**
- **Custom DataScrubber class** for reusable cleaning functions
- **uv** for environment management
- **Git / GitHub** for version control

---

## 🧠 Objective
Prepare all three raw datasets (`customers`, `products`, `sales`) for loading into a centralized data warehouse.
Steps include:
1. Standardize column names (snake_case)
2. Trim whitespace and normalize text
3. Convert datatypes (`datetime`, numeric)
4. Remove duplicates and empty rows
5. Fill missing values with mode or constants
6. Optionally remove outliers using IQR
7. Validate schema and export cleaned data

---

## 🧹 Final Row Counts

| Dataset   | Raw Count | Prepared Count |
|------------|-----------|----------------|
| Customers  | 201       | 190            |
| Products   | 100       | 100            |
| Sales      | 2001      | 2001           |

---

## 🧾 Example Commands (Windows / PowerShell)

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Run data prep scripts
uv run python -m analytics_project.data_preparation.prepare_customers_data
uv run python -m analytics_project.data_preparation.prepare_products_data
uv run python -m analytics_project.data_preparation.prepare_sales_data
