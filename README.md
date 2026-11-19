# Meridian Health | Executive BI & Pharmacy Retail Analytics Suite

An end-to-end **Pharmacy & Health Retail Business Intelligence Solution** combining a **PostgreSQL Star Schema analytical warehouse** (`sql/`) with a **6-page interactive Streamlit Executive BI Dashboard** (`app.py`). Designed to track multi-store sales performance, profit margins, discount leakage, customer retention cohorts, pharmacist workload, and batch-level inventory expiration risks.

---

## Table of Contents
1. [Executive Highlights & Key Findings](#1-executive-highlights--key-findings)
2. [Repository & Data Architecture](#2-repository--data-architecture)
3. [Financial & KPI Definitions](#3-financial--kpi-definitions)
4. [Analytical Classifications & Methodology](#4-analytical-classifications--methodology)
   - [RFM Customer Segmentation](#41-rfm-customer-segmentation-7-tier-model)
   - [Customer Lifecycle & Time-to-Return](#42-customer-lifecycle--time-to-return-classification)
   - [Inventory Shelf-Life & Reorder Risk](#43-inventory-shelf-life--reorder-risk-classification)
   - [Store & Pharmacist Operational Efficiency](#44-store--pharmacist-operational-efficiency)
5. [Streamlit Dashboard Pages](#5-streamlit-dashboard-pages)
6. [How to Run Locally](#6-how-to-run-locally)

---

## 1. Executive Highlights & Key Findings
Across **9,900 transactions**, **23,790 units sold**, **10,000 prescriptions**, and **10,000 inventory batch logs** (`Oct 2024 – Dec 2025`):

* **Top-Line & Profitability:** Generated **$3,615,051.91** in gross revenue and **$3,158,944.05** in net revenue after an average discount of **12.58%**, delivering **$1,109,265.45** in net profit (**35.12%** overall profit margin) and a **$319.09** net Average Order Value (AOV).
* **Payment & Regional Drivers:** **Credit Card** leads net revenue share (**33.25%**, $1.05M), followed by **Debit Card** (**28.54%**), **Cash** (**21.75%**), and **Online** (**16.45%**). Regionally, **East** leads net revenue (**27.09%**, $855.8k) with the highest AOV (**$342.18**).
* **Margin Dispersion Across Stores:** **Precision Meds** leads net revenue (**$314.3k**), while three locations (*Wellness Corner*, *CuraMax Superstore*, and *MediHealth Downtown*) exhibit noticeably lower gross margins (~20% vs. ~40%+ at top stores) due to product mix and discounting.
* **Inventory & Expiry Exposure:** **1,605** out of 10,000 tracked batches carry shelf-life warnings (`Short Shelf Life`, `Expired on Receipt`, `High Risk - Monitor`, or `Critical Danger`), and **1,635** batches are flagged below reorder level.

---

## 2. Repository & Data Architecture

```text
meridian-health-bi/
├── app1.py                                          # 6-page Streamlit Executive BI Dashboard
├── data/                                            # Star Schema CSV tables (dim_* and fact_*)
├── sql/
│   ├── 01_schema_and_base_views.sql                 # Table standardization & enriched analytical views
│   ├── 02_executive_overview_kpis.sql               # Page 1: Executive KPIs, monthly/yearly profit & top entities
│   ├── 03_sales_and_discount_analysis.sql           # Page 2: Gross vs. net revenue, payment mix, region & category discounts
│   ├── 04_customer_rfm_and_clv_analysis.sql         # Page 3: RFM quintile segmentation, CLV proxy & new vs. returning
│   ├── 05_product_and_inventory_risk_analysis.sql   # Page 4: Stock valuation, expiry risk, reorder alerts & turnover
│   ├── 06_store_and_pharmacist_workload_analysis.sql  # Page 5: Store scorecard, prescriptions/pharmacist & labor cost/Rx
│   └── 07_customer_cohort_funnel_and_retention.sql  # Page 6: Acquisition cohorts, conversion funnel & time-to-return
└── README.md
```

### Star Schema Model
* **Fact Tables:** `fact_sales` (9,900 rows), `fact_prescriptions` (10,000 rows), `fact_stock_log` (10,000 rows)
* **Dimension Tables:** `dim_products` (5,000 SKUs), `dim_categories` (9 categories), `dim_stores` (12 branches across 5 regions), `dim_customers` (1,555 profiles), `dim_employees` (120 staff), `dim_suppliers` (5 suppliers)

---

## 3. Financial & KPI Definitions

All SQL queries and Streamlit views adhere to a single financial calculation standard:

| Metric | Formula | Business Definition |
| :--- | :--- | :--- |
| **Gross Revenue** | $\text{Quantity} \times \text{Unit Price}$ | Total pre-discount retail sales value. |
| **Discount Value** | $\text{Gross Revenue} \times \text{Discount \%}$ | Total promotional/loyalty discount leakage. |
| **Net Revenue** | $\text{Gross Revenue} \times (1 - \text{Discount}\%)$ | Realized top-line revenue after discounts. |
| **Total Cost (COGS)** | $\text{Quantity} \times \text{Cost Price}$ | Direct wholesale acquisition cost of units sold. |
| **Net Profit** | $\text{Net Revenue} - \text{Total Cost}$ | Gross operating profit after discounts and COGS. |
| **Profit Margin (%)** | $\left(\frac{\text{Net Profit}}{\text{Net Revenue}}\right) \times 100$ | Percentage of net revenue retained as profit. |
| **Net AOV** | $\frac{\text{Net Revenue}}{\text{Distinct Orders}}$ | Average net spend per completed transaction (`sale_id`). |
| **Observed CLV Proxy** | $\frac{\text{Customer Net Revenue}}{\text{Unique Customers}}$ | Cumulative realized net spend per customer over the dataset window. |

---

## 4. Analytical Classifications & Methodology

### 4.1 RFM Customer Segmentation (7-Tier Model)
Customers are scored from **1 to 5** using quintiles (`NTILE(5)`) across three behavioral dimensions relative to the dataset's latest transaction date (`max_date`):
* **Recency ($R$):** Days since last purchase (`max_date - last_purchase`), scored inversely so recent buyers receive `5`.
* **Frequency ($F$):** Distinct order count (`COUNT(DISTINCT sale_id)`), scored `1` (lowest) to `5` (highest).
* **Monetary ($M$):** Total net spend, scored `1` (lowest) to `5` (highest).

| RFM Segment | Rule Criteria | Recommended Action |
| :--- | :--- | :--- |
| **Champions** | $R \ge 4 \text{ and } F \ge 4 \text{ and } M \ge 4$ | Reward with VIP perks, early access, and referral incentives. |
| **Loyal Customers** | $R \ge 3 \text{ and } F \ge 4$ | Upsell higher-margin wellness/supplement bundles. |
| **Potential Loyalists** | $R \ge 4 \text{ and } F \ge 2$ | Offer membership tier upgrades to lock in repeat habits. |
| **New Customers** | $R \ge 4 \text{ and } F = 1$ | Trigger post-purchase onboarding and second-order coupons. |
| **At Risk** | $R \le 2 \text{ and } F \ge 3$ | Launch personalized win-back campaigns before churn occurs. |
| **Hibernating** | $R \le 2 \text{ and } F = 2$ | Re-engage with targeted seasonal or prescription reminders. |
| **Lost Customers** | All remaining combinations ($R \le 2, F = 1$) | Exclude from high-cost campaigns; test low-cost reactivation. |

---

### 4.2 Customer Lifecycle & Time-to-Return Classification
* **New vs. Returning Orders:** A transaction is classified as **New** when `sale_date` equals the customer's minimum purchase date (`first_date`); all subsequent purchases are classified as **Returning**.
* **Purchase Funnel & Loyalty Tiers:**
  * **One-Time Customers:** `total_orders = 1`
  * **Repeat Customers:** `total_orders >= 2` (or `2–4` orders in lifecycle breakdowns)
  * **Loyal Customers:** `total_orders >= 5`
* **Time-to-Return Intervals:** Measures the exact day gap (`second_purchase - first_purchase`) between a customer's 1st and 2nd order, grouped into 5 behavioral windows: `Within 7 Days`, `8–30 Days`, `31–60 Days`, `61–90 Days`, and `90+ Days`.

---

### 4.3 Inventory Shelf-Life & Reorder Risk Classification
Batch records in `fact_stock_log` are evaluated along two operational risk axes:

| Risk Dimension | Classification / Flag | Definition & Operational Trigger |
| :--- | :--- | :--- |
| **Shelf-Life Status** | `Expired on Receipt` | Batch arrived past its expiration date (`days_left < 0`); immediate quarantine/vendor claim. |
| **Shelf-Life Status** | `Critical Danger` | Expires within **0–30 days**; prioritize immediate markdown or return-to-vendor. |
| **Shelf-Life Status** | `High Risk - Monitor` | Elevated spoilage risk requiring active pharmacist rotation (FEFO). |
| **Shelf-Life Status** | `Short Shelf Life` | Expires within **31–90 days**; flag for promotional bundling. |
| **Shelf-Life Status** | `Safe` | Healthy remaining shelf life (`> 90 days`). |
| **Replenishment Flag** | `is_below_reorder_level` | Triggered when `quantity < reorder_level`; surfaces in the live Reorder Alert table. |
| **Turnover Proxy** | $\frac{\text{Units Sold}}{\text{Current Stock Units}}$ | Directional velocity ratio comparing historical unit demand against on-hand stock. |

---

### 4.4 Store & Pharmacist Operational Efficiency
To evaluate clinical workload alongside retail profitability (`06_store_and_pharmacist_workload_analysis.sql`), each branch is benchmarked on:
* **Prescriptions per Pharmacist:** $\frac{\text{Total Prescriptions}}{\text{Licensed Pharmacists (`is_pharmacist = TRUE`)}}$ — measures clinical dispensing load and staffing bottlenecks.
* **Labor Cost per Prescription:** $\frac{\text{Total Store Payroll}}{\text{Total Prescriptions}}$ — measures payroll efficiency relative to pharmacy dispensing volume.

---

## 5. Streamlit Dashboard Pages

1. **Executive Overview:** Top-line KPI cards with prior-period delta comparison, monthly cost-vs-profit stacked composition chart, top 10 categories & stores, and an automated health summary.
2. **Sales Analysis:** Monthly/Daily gross revenue decomposition (Net Revenue + Discount Leakage), Region → Store treemap, payment method donut & AOV table, and Category Revenue vs. Average Discount bubble chart.
3. **Customer Analysis:** 7-segment RFM distribution & revenue treemap, observed CLV box plots across loyalty tiers (`Platinum`, `Gold`, `Silver`, `Others`), and New vs. Returning revenue trends.
4. **Product & Inventory Analysis:** Stock valuation at cost & retail, critical/expired batch KPIs, interactive below-reorder alert table, and Product Margin % vs. Turnover Proxy matrix.
5. **Store & Geographic Analysis:** Interactive geo scatter map, Region → City → Store sunburst, full store financial & clinical scorecard, and a multi-metric radar benchmark chart.
6. **Customer Behavior Analysis:** Monthly acquisition cohort heatmap, repeat conversion by region and first payment method, 3-stage customer conversion funnel, and time-to-return distribution.

---

## 6. How to Run Locally

1. **Clone the repository & install dependencies:**
   ```bash
   git clone https://github.com/<your-username>/meridian-health-bi.git
   cd meridian-health-bi
   pip install streamlit pandas numpy plotly sqlalchemy psycopg2-binary
   ```
2. **Configure your data source (choose one):**
   * **CSV Mode (Default):** Place the 9 CSV tables inside `./data/` (or set `MERIDIAN_DATA_DIR=/path/to/csvs`).
   * **PostgreSQL Mode:** Execute `sql/01_schema_and_base_views.sql` on your database and set `DATABASE_URL="postgresql://user:password@localhost:5432/meridian_db"`.
   * **Demo Mode:** Set `USE_SYNTHETIC_DATA=true` to run with built-in reproducible synthetic data.
3. **Launch the BI Suite:**
   ```bash
   streamlit run app1.py
   ```
