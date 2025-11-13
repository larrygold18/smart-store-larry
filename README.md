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

**Screenshots**
![DW screenshot](docs/p4_dw_screenshot.png)
