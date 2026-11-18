# Meridian Health – Executive BI Suite

<p align="center">
  <strong>Healthcare Business Intelligence & Analytics Dashboard</strong>
  <br>
  Built with Streamlit, Python, Pandas, Plotly, and PostgreSQL
</p>

---

## Overview

**Meridian Health – Executive BI Suite** is an interactive Business Intelligence (BI) dashboard designed to help healthcare retail businesses monitor performance, understand customer behavior, analyze sales, and make data-driven decisions.

Developed with the **Digitera** visual identity, the application provides a centralized analytics environment for exploring business performance through interactive visualizations, KPIs, and analytical reports.

The dashboard supports PostgreSQL integration and includes a synthetic data mode, allowing users to explore its features without requiring a live database.

## Key Features

- Interactive executive dashboard with business KPIs.
- Sales and revenue performance analysis.
- Customer segmentation using RFM analysis.
- Customer lifetime value (CLV) estimation.
- Product and inventory performance monitoring.
- Store and geographic performance analysis.
- Customer behavior, retention, and cohort analysis.
- Interactive charts and visualizations.
- Global filters for date, region, store, and product category.
- PostgreSQL database integration.
- Synthetic demo data for testing and demonstration.
- Responsive, branded interface based on Digitera's visual identity.

## Dashboard Modules

### 1. Executive Overview

Provides a high-level summary of the organization's business performance.

**Key metrics:**
- Gross Sales
- Net Revenue
- Total Profit
- Profit Margin
- Total Orders
- Average Order Value

**Visualizations:**
- Monthly revenue and profit trends.
- Top-performing products.
- Top-performing stores.
- Executive performance summary.

### 2. Sales Analysis

Analyzes sales performance across different business dimensions.

**Features:**
- Daily and monthly sales trends.
- Revenue analysis by region.
- Store performance comparison.
- Payment method distribution.
- Product category analysis.
- Sales and profitability comparisons.

### 3. Customer Analysis

Provides insights into customer value, purchasing patterns, and segmentation.

**Features:**
- RFM (Recency, Frequency, Monetary) analysis.
- Customer segmentation.
- Customer lifetime value estimation.
- New versus returning customer analysis.
- Customer purchasing behavior.

**RFM methodology:**
- Recency: How recently a customer made a purchase.
- Frequency: How frequently a customer purchases.
- Monetary: How much a customer spends.

### 4. Product & Inventory Analysis

Monitors product performance and inventory conditions.

**Features:**
- Inventory valuation.
- Product stock monitoring.
- Expiry risk analysis.
- Reorder recommendations.
- Product turnover analysis.
- Profitability versus inventory performance.

### 5. Store & Geographic Analysis

Evaluates performance across stores and geographic regions.

**Features:**
- Geographic store distribution.
- Store-level performance comparison.
- Regional revenue analysis.
- Store performance scorecards.
- Comparative performance visualizations.

### 6. Customer Behavior Analysis

Explores customer journeys, retention, and purchasing patterns.

**Features:**
- Customer cohort analysis.
- Conversion analysis.
- First-time versus repeat purchasing.
- Customer loyalty funnel.
- Time-to-return analysis.
- Retention and purchasing behavior insights.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations |
| Plotly | Interactive visualizations |
| SQLAlchemy | Database connectivity |
| PostgreSQL | Relational database |
| Psycopg | PostgreSQL driver |
| Git & GitHub | Version control and source code management |
| Streamlit Community Cloud | Application deployment |

## Project Structure

```text
meridian_health_digitera/
│
├── app.py
│   └── Main Streamlit application
│
├── requirements.txt
│   └── Python dependencies
│
├── README.md
│   └── Project documentation
│
└── .gitignore
    └── Files excluded from version control
```

## Installation and Setup

### Prerequisites

Make sure the following tools are installed:

- Python 3.12 recommended
- Git
- Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/meridian-health-digitera.git
```

Navigate to the project directory:

```bash
cd meridian-health-digitera
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

## Database Configuration

The application supports connecting to a PostgreSQL database through the `DATABASE_URL` environment variable.

### Database Connection

Set the following environment variable:

```text
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE
```

Replace the placeholders with your actual database credentials.

For Streamlit Community Cloud, configure the connection through the application's **Secrets** settings:

```toml
DATABASE_URL = "postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE"
```

Never commit database credentials or secret configuration files to GitHub.

### Expected Database Schema

The application is designed around a dimensional data model containing fact and dimension tables.

**Fact tables:**

- `fact_sales`
- `fact_stock_log`
- `fact_prescriptions`

**Dimension tables:**

- `dim_products`
- `dim_stores`
- `dim_customers`
- `dim_categories`
- `dim_employees`

The live database must contain the expected columns, relationships, and compatible data types used by the application.

Refer to the application code and your database implementation when preparing the production schema.

### Synthetic Data Mode

If PostgreSQL is not configured or the database cannot be accessed, the application uses synthetic demonstration data.

This allows users to explore the dashboard without connecting to a production database.

**Note:** Synthetic data is illustrative and should not be interpreted as actual Meridian Health business performance.

---

## Business Metrics and Calculations

The dashboard uses the following financial calculations:

| Metric | Calculation |
|---|---|
| Gross Sales | Quantity × Unit Price |
| Net Revenue | Gross Sales × (1 − Discount Percentage) |
| Cost of Goods Sold | Quantity × Product Cost Price |
| Profit | Net Revenue − Cost of Goods Sold |
| Profit Margin | (Profit / Net Revenue) × 100 |
| Average Order Value | Net Revenue / Number of Orders |

Additional analytical methodologies include:

- RFM customer segmentation.
- Cohort-based customer retention analysis.
- Customer purchasing frequency.
- Inventory valuation and expiry monitoring.
- Product and store performance comparisons.

**Analytical assumptions:** Customer lifetime value is represented by an observed revenue-based estimate, not a predictive lifetime value model. Inventory turnover is a directional analytical measure and should be validated against the organization's accounting and inventory policies.

---

## Deployment

The application can be deployed using **Streamlit Community Cloud**.

### Deployment Steps

1. Upload the project to a GitHub repository.
2. Visit [Streamlit Community Cloud](https://share.streamlit.io/).
3. Sign in using GitHub.
4. Select **Create app**.
5. Choose the Meridian Health repository.
6. Select the `main` branch.
7. Set the main file path to `app.py`.
8. Click **Deploy**.

After successful deployment, Streamlit provides a public application URL.

For PostgreSQL integration, configure `DATABASE_URL` through Streamlit's Secrets settings.

---

## Future Enhancements

Potential future improvements include:

- Predictive sales forecasting.
- Advanced customer churn prediction.
- Machine learning-based customer segmentation.
- Automated inventory replenishment recommendations.
- Advanced customer lifetime value prediction.
- Role-based access control.
- Automated reporting and scheduled report generation.
- Real-time business performance monitoring.
- Integration with additional healthcare management systems.

## Important Notes

- Synthetic data is intended for demonstration and development.
- Real database integration requires a compatible PostgreSQL schema.
- Geographic visualizations should use verified store coordinates for production.
- Production deployment should use secure database credentials and read-only database access where possible.
- Personal and sensitive healthcare information must be protected through appropriate access controls and privacy safeguards.

---

## Project Information

**Project:** Meridian Health – Executive BI Suite  
**Brand Identity:** Digitera  
**Application Type:** Business Intelligence & Data Analytics Dashboard  
**Framework:** Streamlit  
**Database:** PostgreSQL (optional)  
**Deployment Platform:** Streamlit Community Cloud

---

<p align="center">
  <strong>Meridian Health – Turning Business Data into Actionable Insights.</strong>
