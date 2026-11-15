# Meridian Health Data Analytics

An interactive pharmacy analytics dashboard built with **Python, Streamlit, PostgreSQL, Pandas and Plotly**.

## Dashboard sections

- Executive Overview: revenue, profit (when cost data is available), orders and customer KPIs.
- Sales Analysis: product category and payment-method performance.
- Customer Analysis: RFM segmentation.
- Product & Inventory: product catalog and stock-condition records.
- Store & Geographic Analysis: store-level performance.
- Cohort Analysis: attribute-based cohorts by geography, product category, store, customer type and payment method. These are not limited to time-based cohorts.
- Data Quality: missing values, distinct values and duplicate-row checks.

## Project structure

```text
data/
  raw/                 # Original CSV files
  processed/           # Cleaned/consolidated CSV files
streamlit_app/
  app.py
  utils/
    data_loader.py
    analytics.py
requirements.txt
.streamlit/
  secrets.toml.example
```

## 1. Install and run locally

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

## 2. CSV files

Place your CSV files in `data/raw/`. The loader recognizes these names:

- `sales_group1_storesA.csv`
- `sales_group2_storesB.csv`
- `sales_group3_storesC.csv`
- `customers_master.csv`
- `products_catalog.csv`
- `stores.csv`
- `stock_condition_log.csv`
- `employees.csv`
- `prescriptions_log.csv`
- `categories.csv`
- `suppliers.csv`

A consolidated `fact_sales.csv`, `sales_cleaned.csv` or `cleaned_sales.csv` in `data/processed/` is preferred over combining the three sales-group files.

## 3. PostgreSQL connection

The default PostgreSQL table mapping is in `streamlit_app/utils/data_loader.py`. Update `DEFAULT_TABLES` or override table names in `.streamlit/secrets.toml`.

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and enter your database URL. Keep the real `secrets.toml` private; it is ignored by Git.

The default fact table name is `fact_sales`. The customer, product and store dimension table names are assumptions and may need to be changed to match your actual database.

The recommended source mode tries PostgreSQL first for each dataset and falls back to its CSV equivalent if a table cannot be loaded. CSV files are not appended to PostgreSQL results, which avoids accidental double-counting of the same transactions.

For deployment, use a hosted PostgreSQL database reachable from Streamlit Community Cloud. A local database on your laptop is not reachable by the cloud app.

## 4. Expected sales fields

The sales fact table/CSV should contain as many of these fields as possible:

- `sale_id`
- `customer_id`
- `store_id`
- `employee_id`
- `product_id`
- `sale_date`
- `quantity`
- `unit_price`
- `discount_pct`
- `payment_method`

Revenue is calculated as:

`quantity * unit_price * (1 - discount_rate)`

`discount_pct` can be stored as either a decimal (0.10) or percentage (10). If a `revenue` column already exists, it is used instead.

Profit is calculated only when a unit cost / `cost_price` or `cost_amount` is available. The dashboard does not invent missing cost data.

## 5. Important schema note

This starter is designed around the known Meridian Health sales fields. The exact names and relationships of your dimension and inventory tables still need to be checked against your PostgreSQL schema. Adjust table mappings and aliases before relying on every dashboard page.

## 6. Deploy

1. Push this repository to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app and select this repository.
4. Set the main file path to `meridian_streamlit_dashboard/streamlit_app/app.py` when the repository root is selected.
5. Add your PostgreSQL connection details under the app's **Secrets** settings.
6. Deploy.

Do not commit customer-identifiable, confidential or otherwise restricted source data. Confirm you have permission to publish any dataset.

## Limitations

- Some charts appear only when the required columns exist.
- The inventory page currently displays available stock-condition records; inventory KPIs require confirmation of the stock log's fields and business definitions.
- The cohort page implements attribute-based cohorts (region/city, product category, store, customer type and payment method), not only monthly cohorts.
- Funnel analysis is not fabricated from sales transactions. It requires defined funnel stages or event data.
