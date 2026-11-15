# Meridian Health — Digitera Executive BI Suite

A six-page Streamlit pharmacy retail analytics application styled with the Digitera visual identity.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app starts immediately in **synthetic demo mode**. No credentials are required.

## Connect PostgreSQL

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL. Example:

```bash
# Windows PowerShell
$env:DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/meridian"

# macOS/Linux
export DATABASE_URL="postgresql+psycopg://username:password@localhost:5432/meridian"
streamlit run app.py
```

The database must contain these tables and the columns used by the app:

- `fact_sales`
- `fact_stock_log`
- `fact_prescriptions`
- `dim_products`
- `dim_stores`
- `dim_customers`
- `dim_categories`
- `dim_employees`

Use the schema in the supplied SQL as the source of truth. The app expects `discount_pct` as a fraction (e.g. `0.10` for 10%), consistent with the supplied SQL expressions.

## Data behavior and assumptions

- The financial measures follow the requested SQL logic:
  - Gross Revenue = `SUM(quantity * unit_price)`
  - Net Revenue = `SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0)))`
  - Total Cost = `SUM(quantity * cost_price)`
  - Net Profit = Net Revenue − Total Cost
  - Profit Margin = Net Profit / Net Revenue × 100
- Sales `unit_price` is used for transaction revenue; product `cost_price` is used for cost.
- The inventory turnover metric is explicitly a directional proxy (units sold divided by current stock), not a formal time-normalized COGS turnover.
- CLV is displayed as observed cumulative net revenue, not a predictive model.
- Cohort and funnel thresholds follow the uploaded SQL: repeat = 2+ orders; loyal = 5+ orders.
- The uploaded text inventory extract is a flattened/pivot-style report, not a complete `fact_stock_log` table. It is not silently loaded as normalized stock data. Load the normalized fact and dimension tables to use live database mode.
- Synthetic data is deterministic and intended for UI/logic demonstration only.

## Production deployment checklist

1. Configure secrets through the hosting platform; never commit credentials.
2. Use a least-privilege, read-only database account for analytics.
3. Add database indexes on date and foreign-key columns.
4. Validate source table names, key uniqueness, currency, timezone, and discount conventions.
5. Add row-level access controls if users must only see permitted regions/stores.
6. Add observability, automated tests, and deployment health checks before production use.
7. Do not expose customer-level identifiable or prescription-level patient details in shared dashboards.

## Included pages

1. Executive Overview
2. Sales Analysis
3. Customer Analysis (RFM, observed CLV, new/returning)
4. Product & Inventory Analysis
5. Store & Geographic Analysis
6. Customer Behavior Analysis
